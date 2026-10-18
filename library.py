"""Biblioteka porad (portal): karty z tematów bazy wiedzy Luny + FAQ. Treść odpowiedzi pochodzi z knowledge.py."""
import re
import knowledge

CATS = [
    {"id": "barwa", "name": "Barwa", "icon": "🎚️", "desc": "Głębia, ciepło i rezonans głosu."},
    {"id": "oddech", "name": "Oddech", "icon": "🌬️", "desc": "Oddech przeponowy i spokojne podparcie."},
    {"id": "dykcja", "name": "Dykcja sz/cz", "icon": "👄", "desc": "Wyraźna wymowa, także „sz”, „cz” i „rz”."},
    {"id": "tempo", "name": "Tempo", "icon": "⏱️", "desc": "Spokojne tempo i świadome pauzy."},
    {"id": "pewnosc", "name": "Pewność siebie", "icon": "💪", "desc": "Trema, stres i zaufanie do własnego głosu."},
    {"id": "wystapienia", "name": "Wystąpienia", "icon": "🎤", "desc": "Prezentacje, rozmowy i opowiadanie historii."},
    {"id": "rozgrzewka", "name": "Rozgrzewka", "icon": "🔥", "desc": "Krótkie ćwiczenia przed mówieniem."},
    {"id": "zdrowie", "name": "Zdrowie głosu", "icon": "🩺", "desc": "Higiena głosu, chrypka i nawyki."},
]
LEVELS = {"p": "Początkujący", "s": "Średni", "z": "Zaawansowany"}
# indeks tematu w knowledge.TOPICS -> (tytuł, kategoria, poziom, data dodania)
META = {
    0: ("Jak mówić niższym głosem", "barwa", "s"), 1: ("Rezonans piersiowy w dwie minuty", "barwa", "s"),
    2: ("Oddech przeponowy krok po kroku", "oddech", "p"), 3: ("Chrypka – co robić", "zdrowie", "p"),
    4: ("Rozgrzewka głosu przed mówieniem", "rozgrzewka", "p"), 5: ("Mów wolniej – brzmisz pewniej", "tempo", "p"),
    6: ("Siła pauzy", "tempo", "s"), 7: ("Koniec z monotonią: intonacja", "wystapienia", "s"),
    8: ("Trema i pewność siebie", "pewnosc", "p"), 10: ("Barwa głosu – co ją tworzy", "barwa", "p"),
    11: ("Ciepły, miękki głos", "barwa", "p"), 12: ("Wyraźna dykcja", "dykcja", "p"),
    13: ("Dykcja: „sz”, „cz”, „rz”", "dykcja", "s"), 14: ("Higiena głosu na co dzień", "zdrowie", "p"),
    15: ("Donośny głos bez krzyku", "wystapienia", "z"), 16: ("Mów cicho, ale nie szeptem", "zdrowie", "s"),
    17: ("Nie lubisz swojego głosu z nagrania?", "pewnosc", "p"), 18: ("Głos w rozmowie telefonicznej", "wystapienia", "p"),
    19: ("Prezentacja i przemówienie", "wystapienia", "s"), 20: ("Gdy głos się łamie lub piszczy", "barwa", "z"),
    21: ("Rozluźnij szczękę i kark", "rozgrzewka", "p"), 22: ("Głos nosowy – jak go otworzyć", "barwa", "s"),
    23: ("Poranny głos", "rozgrzewka", "p"), 24: ("Co pić dla zdrowego głosu", "zdrowie", "p"),
    25: ("Zamiast odchrząkiwać", "zdrowie", "p"), 26: ("Akcent i naleciałości", "dykcja", "s"),
    27: ("Uśmiech słychać w głosie", "pewnosc", "p"), 28: ("Opowiadaj z emocją", "wystapienia", "s"),
    29: ("Śpiew a głos mówiony", "rozgrzewka", "s"), 30: ("Ile trwa zmiana głosu", "pewnosc", "p"),
    31: ("Głos a wiek", "zdrowie", "p"), 32: ("Ćwiczenie „mmm”", "rozgrzewka", "p"), 33: ("Niski głos bez forsowania", "barwa", "s"),
}
SECOND = {0: "Głębia bez udawania basu", 2: "Oddech 4–2–6", 4: "Szybka rozgrzewka w pięć minut", 7: "Melodia zdania w praktyce",
          8: "Stres przed rozmową – plan na minutę", 10: "Odkryj swoją naturalną barwę"}
FAQ = [
    ("Czy Luna jest prawdziwą osobą?", "Nie. Luna to sztucznie stworzona asystentka AI, a jej postać jest wygenerowana komputerowo. Mówi o tym w każdej rozmowie."),
    ("W jakiej przeglądarce Luna działa najlepiej?", "W Chrome na Androidzie i komputerze. Rozpoznawanie mowy zależy od przeglądarki; czat tekstowy i czytanie odpowiedzi działają szerzej."),
    ("Czy Luna słucha cały czas?", "Nie. Słowo „Luna” działa tylko wtedy, gdy aplikacja jest otwarta i masz włączone „Nasłuchiwanie”."),
    ("Czy Luna zastąpi foniatrę albo logopedę?", "Nie. Podpowiada ćwiczenia i dobre nawyki, ale przy długotrwałej chrypce lub bólu warto pójść do specjalisty."),
    ("Jak zainstalować Lunę na telefonie?", "Android: w Chrome stuknij menu ⋮ i wybierz „Zainstaluj aplikację”. iPhone: w Safari stuknij Udostępnij i „Do ekranu początkowego”."),
    ("Jak skontaktować się z twórcą?", "Użyj zakładki „Czat z twórcą”. Czas odpowiedzi na każde pytanie zależy od dostępności osób w biurze, ale nie będzie dłuższy niż 30 dni."),
]
THUMBS = ["/catalog/luna/outfit_koronkowa.jpg", "/catalog/luna/outfit_sweter.jpg", "/catalog/luna/outfit_wieczorowa.jpg",
          "/catalog/luna/outfit_biznes.jpg", "/catalog/luna/outfit_koktajlowa.jpg", "/catalog/luna/pose_polobrot.jpg",
          "/catalog/luna/pose_zamyslona.jpg", "/catalog/luna/pose_siedzaca.jpg"]

def _clean(t):
    return re.sub(r",?\s*cariño,?", "", t).replace("  ", " ").strip()

def secs(text):  # szacowany czas odsłuchu (lektor ok. 2,3 słowa na sekundę)
    return max(8, round(len(text.split()) / 2.3))

def build():
    items = []
    for i, (title, cat, lvl) in META.items():
        answers = knowledge.TOPICS[i][1]; kws = knowledge.TOPICS[i][0]
        for j, a in enumerate(answers[:2]):
            t = title if j == 0 else SECOND.get(i)
            if not t: continue
            a = _clean(a)
            items.append({"id": f"t{i}" + ("" if j == 0 else "b"), "kind": "porada", "title": t, "cat": cat, "level": lvl, "level_name": LEVELS[lvl],
                          "text": a, "secs": secs(a), "keywords": kws, "order": len(items), "new": j == 1,
                          "thumb": THUMBS[(i * 3 + j) % len(THUMBS)]})
    for k, (q, a) in enumerate(FAQ):
        items.append({"id": f"f{k}", "kind": "faq", "title": q, "cat": "faq", "level": "p", "level_name": LEVELS["p"], "text": a,
                      "secs": secs(a), "keywords": [], "order": len(items), "new": False, "thumb": "/avatar-512.jpg"})
    return {"cats": CATS, "levels": LEVELS, "items": items}

LIB = build()
