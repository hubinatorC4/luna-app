# -*- coding: utf-8 -*-
"""Offline baza wiedzy Luny – trenerki głosu. Dopasowanie po słowach kluczowych."""
import random, re, unicodedata

def norm(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s.replace("ł", "l")

OPENERS = ["Mmm, cariño… ", "Escucha, cariño… ", "Dobrze, mi amor… ", "Słuchaj uważnie… ", "Ay, dobre pytanie… ", "", "", ""]
CLOSERS = [" Spróbuj teraz, ja posłucham.", " Powoli, cariño, bez pośpiechu.", " Zrób to dla mnie dziś wieczorem.", " Vamos, dasz radę.", "", "", ""]

# (słowa kluczowe, odpowiedzi)
TOPICS = [
 (["niski", "nizszy", "glebszy", "gleboki", "obnizyc", "obniz", "basowy", "meski"],
  ["Niski głos zaczyna się od rozluźnienia, nie od wciskania krtani w dół. Weź oddech w brzuch, powiedz „mmm” na najniższym wygodnym tonie i poczuj wibrację w klatce piersiowej. Mów z tego miejsca, spokojnie i bez forsowania.",
   "Nie udawaj basu, bo gardło się zmęczy. Ziewnij delikatnie, żeby otworzyć gardło, i mów na wydechu, trochę wolniej niż zwykle. Głębia przyjdzie sama, kiedy przestaniesz się spieszyć."]),
 (["rezonans", "klatk", "piersiow", "wibracj"],
  ["Połóż dłoń na mostku i powiedz „mmmaaa” nisko i miękko. Jeśli czujesz drżenie pod palcami, to jest Twój rezonans piersiowy. Ćwicz to po dwie minuty dziennie i przenoś to uczucie do zwykłych zdań."]),
 (["oddech", "oddych", "przepon", "brzuch", "powietrz", "wdech", "wydech"],
  ["Oddychaj z przepony: dłoń pod żebrami, wdech nosem tak, żeby unosił się brzuch, a nie ramiona. Potem długi wydech na „sss” przez dwadzieścia sekund. To jest paliwo dla ciepłego, stabilnego głosu.",
   "Ramiona w dół, brzuch swobodny. Wdech na cztery, zatrzymaj na dwa, wydech na sześć. Kiedy oddech jest spokojny, Twój głos też brzmi pewnie i nisko."]),
 (["chrypk", "zachryp", "ochryp", "chrypi", "zdarty"],
  ["Chrypka to zwykle sygnał, że struny są zmęczone albo przesuszone. Pij wodę małymi łykami, rób inhalacje z pary i daj głosowi dzień ciszy, ale nie szepcz, bo szept też męczy. Jeśli trwa dłużej niż dwa tygodnie, idź do foniatry, cariño, to ważne."]),
 (["rozgrzew", "cwiczeni", "cwiczyc", "trening", "przed wystap"],
  ["Moja ulubiona rozgrzewka: trzy minuty mruczenia na „mmm”, potem parskanie ustami jak konik, a na koniec glissando od wysokiego do niskiego tonu na „uuu”. Pięć minut i głos jest ciepły, gotowy na wszystko.",
   "Zacznij od ziewania z otwartym gardłem, potem „brrr” na wargach i powolne „ma-me-mi-mo-mu” w średnim tonie. Rozgrzany głos brzmi niżej i pełniej."]),
 (["tempo", "szybko", "wolniej", "wolno", "spiesz", "pospiech"],
  ["Mów wolniej, niż Ci się wydaje, że trzeba. Wolne tempo brzmi pewnie i ciepło, szybkie brzmi nerwowo. Spróbuj przeczytać akapit o połowę wolniej i nagraj się, sam usłyszysz różnicę."]),
 (["pauz", "przerw", "cisz"],
  ["Pauza to Twoja tajna broń, cariño. Zatrzymaj się na sekundę przed ważnym słowem, a wszyscy będą na nie czekać. Cisza w rozmowie nie jest pustką, tylko napięciem, które Ty kontrolujesz."]),
 (["intonacj", "melodi", "monoton", "plaski", "nudn", "znudz"],
  ["Płaski głos ożywisz melodią: lekko w górę, kiedy coś Cię cieszy, niżej i ciszej, kiedy chcesz kogoś przyciągnąć. Uśmiechnij się, mówiąc, to naprawdę słychać.",
   "Na końcu zdania twierdzącego opuszczaj ton. Kiedy idziesz w górę, brzmisz, jakbyś pytał o zgodę. Opadająca intonacja brzmi spokojnie i pewnie."]),
 (["pewn", "pewnos", "stres", "trem", "nerw", "niesmial", "wstyd"],
  ["Pewność słychać szybciej, niż ją widać. Stań prosto, weź spokojny wdech w brzuch i mów odrobinę wolniej i niżej niż zwykle. Nie kończ zdań pytającym tonem, nawet kiedy się denerwujesz.",
   "Przed ważną rozmową zrób trzy długie wydechy i powiedz na głos jedno zdanie, które dobrze znasz. Ciało się uspokaja, a głos idzie za ciałem."]),
 (["seksown", "atrakcyjn", "uwodz", "zmysl", "pociag", "kobiet", "randk", "podobac"],
  ["Atrakcyjny głos to spokój, ciepło i odrobina tajemnicy. Mów wolniej, trochę ciszej, tak żeby ktoś musiał się do Ciebie nachylić. I uśmiechaj się oczami, to też słychać, mi amor.",
   "Nie chodzi o udawany bas, tylko o luz. Rozluźnij szczękę, mów na wydechu i rób pauzy. Pewny, ciepły i niespieszny głos działa lepiej niż jakikolwiek tekst na podryw."]),
 (["barw", "ton glos", "brzmieni", "kolor glos"],
  ["Barwę kształtujesz rezonansem: więcej klatki piersiowej daje ciepło, więcej masek twarzy daje blask. Mrucz „mmm” i szukaj wibracji w wargach i nosie, a potem mów z tym samym uczuciem.",
   "Ciepła barwa to otwarte gardło i rozluźniona szczęka. Wyobraź sobie, że masz w ustach ciepłą herbatę, i mów z tą przestrzenią w środku."]),
 (["cieply", "ciepl", "aksamit", "miekk"],
  ["Ciepły głos rodzi się z rozluźnienia. Opuść ramiona, rozluźnij język i mów trochę bardziej na wydechu, jakbyś opowiadał komuś bliskiemu sekret. Tak, właśnie tak."]),
 (["dykcj", "wyrazn", "artykul", "sepleni", "belkot", "mamrot"],
  ["Dla dykcji: korek albo ołówek między zębami i czytaj powoli tekst przez trzy minuty. Potem wyjmij i przeczytaj jeszcze raz, poczujesz, jak usta same pracują wyraźniej."]),
 (["sz", "cz", "szum", "szelest", "szeleszcz", "rz", "syczen"],
  ["„Sz” i „cz” brzmią naturalnie, kiedy czubek języka jest lekko uniesiony za dziąsłami, a usta delikatnie zaokrąglone. Powtarzaj powoli „szczery, szczupły, czuły” i nie zaciskaj zębów. Ja, z moim hiszpańskim akcentem, też to ćwiczę, cariño."]),
 (["zdrowi", "higien", "dbac", "chronic", "struny", "wiezadl"],
  ["Struny głosowe kochają wodę, sen i spokój. Pij dużo, unikaj krzyku i odchrząkiwania, a zamiast tego przełykaj ślinę. Alkohol i papierosy wysuszają głos, więc z umiarem, mi amor."]),
 (["krzyk", "glosn", "glosniej", "donosn", "projekcj", "sala"],
  ["Głośniej nie znaczy z gardła. Siła idzie z brzucha: wyobraź sobie, że rzucasz głos do ostatniego rzędu, ale gardło zostaje luźne. Ćwicz krótkie „hej!” z oparciem na przeponie."]),
 (["cicho", "cichy", "szept", "szeptac", "ciszej"],
  ["Cichy głos może być bardzo magnetyczny, ale nie szepcz bez dźwięku, bo to męczy struny. Mów miękko, z oddechem, ale z odrobiną tonu w środku. Wtedy jest i intymnie, i zdrowo."]),
 (["nagryw", "nagran", "mikrofon", "podcast", "slucham siebie", "nienawidze swojego"],
  ["Każdy nie lubi swojego głosu z nagrania, bo na co dzień słyszysz siebie przez kości czaszki. Nagrywaj się regularnie przez tydzień, a ucho się przyzwyczai. Do mikrofonu mów z odległości dłoni i trochę ciszej."]),
 (["telefon", "rozmow", "dzwon"],
  ["Przez telefon nikt nie widzi Twojego uśmiechu, ale go słyszy. Uśmiechnij się, zanim odbierzesz, mów wolniej niż na żywo i rób krótkie pauzy, żeby rozmówca mógł wejść."]),
 (["prezentac", "wystapien", "publiczn", "przemow", "scen", "spotkani", "prac"],
  ["Na wystąpieniu zacznij od pauzy i spokojnego spojrzenia na salę, dopiero potem pierwsze zdanie, nisko i wolno. Ważne słowa akcentuj ciszą, a nie krzykiem. Masz czas, cariño, sala na Ciebie poczeka."]),
 (["pisk", "piszcz", "wysoki", "cienki", "zalamuj", "lamie"],
  ["Piszczenie i łamanie głosu to najczęściej napięcie w krtani. Rozluźnij kark, ziewnij, a potem mów na „mmm” przechodząc w słowa. Nie podnoś brody, trzymaj ją swobodnie, równolegle do podłogi."]),
 (["szczek", "napiec", "spiet", "kark", "ramion", "postaw", "postawa"],
  ["Spięta szczęka zabija ciepło głosu. Pomasuj mięśnie przy uszach, otwórz szeroko usta i powoli zamknij kilka razy. Stań prosto, stopy na szerokość bioder, a głos od razu się otworzy."]),
 (["nos", "nosowy", "przez nos", "katar"],
  ["Jeśli brzmisz nosowo, sprawdź, czy podniebienie miękkie się unosi: powiedz „ka-ga-ka-ga” i poczuj ruch z tyłu ust. Potem ziewnij z zamkniętymi ustami, to otwiera przestrzeń i zabiera nosowość."]),
 (["glos rano", "rano", "poranny", "po przebudzeniu"],
  ["Rano struny są jeszcze sztywne i opuchnięte, dlatego głos jest niższy i chropowaty. Wypij ciepłą wodę, pomrucz dwie minuty i dopiero wtedy mów dłużej. Ten poranny niski głos? Też bywa uroczy."]),
 (["herbat", "miod", "picie", "pic", "woda", "napoj", "imbir"],
  ["Najlepsza jest zwykła woda, cariño, dużo i często. Ciepła herbata z miodem koi, ale nie gorąca. Mleko i bardzo słodkie napoje tuż przed mówieniem dają flegmę, więc ich unikaj."]),
 (["odchrzak", "flegm", "sluz"],
  ["Nie odchrząkuj co chwilę, to jak uderzanie strunami o siebie. Zamiast tego przełknij ślinę albo napij się wody i zrób delikatne „hm” na wydechu."]),
 (["akcent", "hiszpan", "obcy", "zaciaga"],
  ["Mój akcent? To melodia z Hiszpanii, cariño, otwarte samogłoski i miękkie „r”. Jeśli chcesz zabrzmieć bardziej melodyjnie, wydłużaj samogłoski w akcentowanych sylabach i nie bój się śpiewności zdania."]),
 (["smiech", "smiac", "usmiech"],
  ["Uśmiech podnosi barwę i dodaje jej ciepła. Mów zdanie raz z kamienną twarzą, a raz z lekkim uśmiechem i nagraj oba. Ta druga wersja zawsze brzmi bardziej przyjaźnie i atrakcyjnie."]),
 (["emocj", "ekspresj", "opowiad", "historie", "czytan", "bajk"],
  ["Czytaj na głos opowiadania i pozwól emocjom zmieniać tempo i głośność. Smutek zwalnia, radość przyspiesza, tajemnica cichnie. Twój głos to instrument, mi amor, graj na nim."]),
 (["spiew", "spiewac", "spiewa"],
  ["Śpiew to świetny trening dla głosu mówionego: uczy oddechu, rezonansu i melodii. Zacznij od prostych piosenek w wygodnej, niskiej tonacji i mrucz je, zanim zaśpiewasz pełnym głosem."]),
 (["ile czasu", "jak dlugo", "efekt", "szybko zmienic", "kiedy zobacz"],
  ["Pierwsze efekty usłyszysz po dwóch, trzech tygodniach codziennych dziesięciu minut. Trwała zmiana barwy to kilka miesięcy. Regularność wygrywa z intensywnością, cariño."]),
 (["mutacj", "dojrzew", "nastolat", "wiek", "starz"],
  ["Głos zmienia się przez całe życie: w dojrzewaniu, z hormonami i z wiekiem. Dobre nawyki, czyli oddech, nawodnienie i brak forsowania, utrzymają go młodym i ciepłym na długo."]),
 (["mruczen", "mrucz", "humming", "mmm"],
  ["Mruczenie to najlepszy masaż dla strun. Usta zamknięte, zęby rozchylone, język luźno, i „mmm” w wygodnym tonie. Szukaj łaskotania w wargach, to znak, że rezonans działa."]),
 (["glos meski", "jak facet", "mezczyzn"],
  ["Męski, ciepły głos to nie bas za wszelką cenę, tylko spokój i oparcie. Mów z brzucha, kończ zdania w dół i nie przepraszaj tonem za to, co mówisz. To jest naprawdę atrakcyjne."]),
 (["kim jestes", "jak masz na imie", "kto ty", "przedstaw"],
  ["Jestem Luna, Twoja trenerka głosu, cariño. Pomagam z barwą, oddechem, tempem i tym, żeby Twój głos brzmiał ciepło i pewnie. Zapytaj mnie o cokolwiek o głosie."]),
 (["czesc", "hej", "witaj", "dzien dobry", "dobry wieczor", "hola", "siema"],
  ["Hola, cariño. Jestem tu i słucham. O co chcesz zapytać, o barwę, oddech czy o to, jak brzmieć pewniej?"]),
 (["dzieki", "dziekuje", "super", "swietnie"],
  ["De nada, mi amor. Ćwicz codziennie po kilka minut, a ja będę tu, kiedy zechcesz pogadać o głosie."]),
]

FALLBACK = [
 "Hmm, cariño, o to mnie jeszcze nikt nie pytał. Jestem od głosu: barwy, oddechu, tempa, pauz i pewności siebie. Zapytaj mnie na przykład, jak mówić niżej albo jak pozbyć się chrypki.",
 "Nie jestem pewna, czy dobrze zrozumiałam, mi amor. Zapytaj mnie o głos, na przykład o rezonans, intonację albo rozgrzewkę przed rozmową.",
]

def answer(q: str) -> str:
    nq = " " + norm(q) + " "
    best, score = None, 0
    for kws, resp in TOPICS:
        s = 0
        for k in kws:
            nk = norm(k)
            if len(nk) <= 2:
                if re.search(r"\b" + re.escape(nk) + r"\b", nq): s += 1
            elif nk in nq:
                s += 2 if " " in nk else 1
        if s > score: best, score = resp, s
    if not best:
        return random.choice(FALLBACK)
    return (random.choice(OPENERS) + random.choice(best) + random.choice(CLOSERS)).strip()

if __name__ == "__main__":
    for q in ["Jak mówić niżej?", "mam chrypkę", "jak brzmieć seksownie na randce", "sz i cz", "co to jest kot"]:
        print(q, "->", answer(q))
    print(len(TOPICS), "topics")
