"""Tłumaczenia danych z API (plany, harmonogram Luna Live) dla EN/ES/DE/UK. Brak tłumaczenia = oryginał po polsku."""
import re
from urllib.parse import urlparse, parse_qs
LANGS = ("en", "es", "de", "uk")

def req_lang(query, headers):
    """Język z ?lang= albo z adresu strony, która wywołała API (Referer, ta sama domena)."""
    lg = parse_qs(query).get("lang", [""])[0][:2]
    if not lg:
        try: lg = parse_qs(urlparse(headers.get("Referer", "")).query).get("lang", [""])[0][:2]
        except Exception: lg = ""
    return lg if lg in LANGS else ""

# [pl, en, es, de, uk]
_T = [
 ["Darmowy", "Free", "Gratis", "Kostenlos", "Безкоштовний"],
 ["Podstawowa", "Basic", "Básica", "Basis", "Базовий"],
 ["Około 5 minut rozmowy z Luną dziennie", "About 5 minutes of talking to Luna a day", "Unos 5 minutos de conversación con Luna al día", "Etwa 5 Minuten Gespräch mit Luna pro Tag", "Близько 5 хвилин розмови з Луною на день"],
 ["Test głosu i próbki barwy", "Voice test and timbre samples", "Prueba de voz y muestras de timbre", "Stimmtest und Klangproben", "Тест голосу та зразки тембру"],
 ["Oglądanie Luna Live (bez zadawania pytań)", "Watching Luna Live (without asking questions)", "Ver Luna Live (sin hacer preguntas)", "Luna Live ansehen (ohne Fragen)", "Перегляд Luna Live (без запитань)"],
 ["1 strój awatara", "1 avatar outfit", "1 conjunto de avatar", "1 Avatar-Outfit", "1 вбрання аватара"],
 ["Wszystko z planu Darmowy, oraz:", "Everything in Free, plus:", "Todo lo del plan Gratis, y además:", "Alles aus Kostenlos, plus:", "Усе з плану Безкоштовний, а також:"],
 ["Rozmowa z Luną bez dziennego limitu", "Talk to Luna with no daily limit", "Conversación con Luna sin límite diario", "Gespräch mit Luna ohne Tageslimit", "Розмова з Луною без денного ліміту"],
 ["Pytania do Luny w Luna Live", "Questions to Luna in Luna Live", "Preguntas a Luna en Luna Live", "Fragen an Luna in Luna Live", "Запитання до Луни в Luna Live"],
 ["Barwa głosu: presety i suwaki", "Voice tone: presets and sliders", "Timbre de voz: ajustes y controles", "Stimmklang: Presets und Regler", "Тембр голосу: пресети й повзунки"],
 ["2 stroje awatara i hologram", "2 avatar outfits and hologram", "2 conjuntos de avatar y holograma", "2 Avatar-Outfits und Hologramm", "2 вбрання аватара й голограма"],
 ["Wszystko z planu Podstawowa, oraz:", "Everything in Basic, plus:", "Todo lo del plan Básica, y además:", "Alles aus Basis, plus:", "Усе з плану Базовий, а також:"],
 ["4 stroje awatara", "4 avatar outfits", "4 conjuntos de avatar", "4 Avatar-Outfits", "4 вбрання аватара"],
 ["Stwórz własną asystentkę: imię, słowo wybudzające, ton, długość odpowiedzi", "Create your own assistant: name, wake word, tone, reply length", "Crea tu propia asistente: nombre, palabra de activación, tono, longitud de respuesta", "Eigene Assistentin: Name, Aktivierungswort, Ton, Antwortlänge", "Створіть власну асистентку: ім’я, слово активації, тон, довжина відповіді"],
 ["Własny kolor pierścienia i własny obraz awatara", "Your own ring colour and avatar image", "Color de anillo y avatar propios", "Eigene Ringfarbe und eigenes Avatarbild", "Власний колір кільця й власне зображення аватара"],
 ["Wszystko z planów Podstawowa i Premium, oraz:", "Everything in Basic and Premium, plus:", "Todo lo de Básica y Premium, y además:", "Alles aus Basis und Premium, plus:", "Усе з планів Базовий і Premium, а також:"],
 ["Wszystkie stroje (6)", "All outfits (6)", "Todos los conjuntos (6)", "Alle Outfits (6)", "Усі вбрання (6)"],
 ["Zmiana pozy awatara", "Change the avatar’s pose", "Cambiar la pose del avatar", "Avatar-Pose ändern", "Зміна пози аватара"],
 ["Wybór sylwetki (wzrost, budowa)", "Choose the figure (height, build)", "Elegir la silueta (altura, complexión)", "Figur wählen (Größe, Statur)", "Вибір статури (зріст, будова)"],
 ["Dodatkowe postacie z katalogu", "Extra characters from the catalogue", "Personajes extra del catálogo", "Zusätzliche Figuren aus dem Katalog", "Додаткові персонажі з каталогу"],
 ["za darmo – wystarczy konto", "free – just create an account", "gratis: solo necesitas una cuenta", "kostenlos – Konto genügt", "безкоштовно – достатньо акаунта"],
 ["30 dni, bez automatycznego odnawiania", "30 days, no automatic renewal", "30 días, sin renovación automática", "30 Tage, keine automatische Verlängerung", "30 днів, без автоматичного продовження"],
 ["Co tydzień: pytania z czatu, łamaniec językowy tygodnia, ćwiczenia oddechowe i wyzwania głosowe.", "Every week: questions from the chat, the tongue twister of the week, breathing exercises and voice challenges.", "Cada semana: preguntas del chat, el trabalenguas de la semana, ejercicios de respiración y retos de voz.", "Jede Woche: Fragen aus dem Chat, der Zungenbrecher der Woche, Atemübungen und Stimm-Challenges.", "Щотижня: запитання з чату, скоромовка тижня, дихальні вправи й голосові челенджі."],
 ["Luna – asystentka AI (postać wygenerowana sztucznie)", "Luna – AI assistant (artificially generated character)", "Luna: asistente de IA (personaje generado artificialmente)", "Luna – KI-Assistentin (künstlich erzeugte Figur)", "Луна – ШІ-асистентка (штучно згенерований персонаж)"],
 ["Trening własnej agentki AI: imię, słowo wybudzające, ton, długość odpowiedzi", "Train your own AI agent: name, wake word, tone, reply length", "Entrena tu propia agente de IA: nombre, palabra de activación, tono, longitud de respuesta", "Training deiner eigenen KI-Agentin: Name, Aktivierungswort, Ton, Antwortlänge", "Тренування власної ШІ-агентки: ім’я, слово активації, тон, довжина відповіді"],
 ["Styl agentki: kolor pierścienia i własny obraz AI", "Agent style: ring colour and your own AI image", "Estilo de la agente: color del anillo e imagen de IA propia", "Stil der Agentin: Ringfarbe und eigenes KI-Bild", "Стиль агентки: колір кільця й власне ШІ-зображення"],
 ["Pełny trening agentki AI: także poza i sylwetka (wzrost, budowa)", "Full AI agent training: also pose and figure (height, build)", "Entrenamiento completo de la agente de IA: también pose y silueta (altura, complexión)", "Volles Training der KI-Agentin: auch Pose und Figur (Größe, Statur)", "Повне тренування ШІ-агентки: також поза й статура (зріст, будова)"],
 ["Czas odpowiedzi na każde pytanie zależy od dostępności osób w biurze, ale nie będzie dłuższy niż 30 dni.", "We reply as soon as someone is available – always within 30 days.", "Respondemos en cuanto haya alguien disponible, siempre en menos de 30 días.", "Wir antworten, sobald jemand verfügbar ist – immer innerhalb von 30 Tagen.", "Відповідаємо, щойно хтось буде на зв’язку, – завжди протягом 30 днів."],
 ["Ciepła trenerka głosu z hiszpańskim temperamentem.", "A warm voice coach with a Spanish temperament.", "Una cálida entrenadora de voz con temperamento español.", "Eine warmherzige Stimmtrainerin mit spanischem Temperament.", "Тепла тренерка голосу з іспанським темпераментом."],
 ["Koronkowa sukienka", "Lace dress", "Vestido de encaje", "Spitzenkleid", "Мереживна сукня"],
 ["Sweter (na co dzień)", "Jumper (everyday)", "Jersey (diario)", "Pullover (Alltag)", "Светр (на щодень)"],
 ["Suknia wieczorowa", "Evening gown", "Vestido de noche", "Abendkleid", "Вечірня сукня"],
 ["Marynarka (biznes)", "Blazer (business)", "Americana (negocios)", "Blazer (Business)", "Жакет (діловий)"],
 ["Letnia sukienka", "Summer dress", "Vestido de verano", "Sommerkleid", "Літня сукня"],
 ["Sukienka koktajlowa", "Cocktail dress", "Vestido de cóctel", "Cocktailkleid", "Коктейльна сукня"],
 ["Na wprost", "Facing forward", "De frente", "Frontal", "Анфас"],
 ["Półobrót", "Half turn", "Medio giro", "Halbe Drehung", "Напівоберт"],
 ["Zamyślona", "Thoughtful", "Pensativa", "Nachdenklich", "Замислена"],
 ["Siedząca", "Seated", "Sentada", "Sitzend", "Сидячи"],
 ["Drobna, szczupła", "Petite, slim", "Menuda, delgada", "Zierlich, schlank", "Мініатюрна, струнка"],
 ["Średni wzrost", "Average height", "Estatura media", "Mittelgroß", "Середній зріст"],
 ["Wysoka, szczupła", "Tall, slim", "Alta, delgada", "Groß, schlank", "Висока, струнка"],
 ["Średni wzrost, pełniejsza", "Average height, fuller figure", "Estatura media, más curvilínea", "Mittelgroß, kurvig", "Середній зріст, пишніша"],
]
_M = {l: {r[0]: r[i + 1] for r in _T} for i, l in enumerate(LANGS)}
DAYS = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
        "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        "uk": ["понеділок", "вівторок", "середа", "четвер", "пʼятниця", "субота", "неділя"]}
WEEKLY = {"en": "Every {d}, {a}–{b} (Polish time)", "es": "Cada {d}, {a}–{b} (hora de Polonia)",
          "de": "Jeden {d}, {a}–{b} (polnische Zeit)", "uk": "Щотижня, {d}, {a}–{b} (за польським часом)"}
AT = {"en": "{d}, {dm} at {t}", "es": "{d}, {dm} a las {t}", "de": "{d}, {dm} um {t}", "uk": "{d}, {dm} о {t}"}
PL_DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]

def t(s, lang):
    return _M.get(lang, {}).get(s, s) if isinstance(s, str) else s

def catalog(pub, lang):
    if lang not in LANGS: return pub
    for p in pub.get("plans", []):
        p["name"] = t(p.get("name", ""), lang); p["pass"] = t(p.get("pass", ""), lang)
        p["features"] = [t(f, lang) for f in p.get("features", [])]
    return catalog_agents(pub, lang)

def sched(sc, lang):
    if lang not in LANGS or not isinstance(sc, dict): return sc
    sc = dict(sc); D = DAYS[lang]
    try:
        sc["day_name"] = D[sc["day"]]
        sc["weekly"] = WEEKLY[lang].format(d=D[sc["day"]], a=sc["time"], b=sc["end"])
        m = re.match(r"(\S+), (\d\d\.\d\d) o (\d\d:\d\d)$", sc.get("next_label", ""))
        if m and m.group(1) in PL_DAYS: sc["next_label"] = AT[lang].format(d=D[PL_DAYS.index(m.group(1))], dm=m.group(2), t=m.group(3))
    except Exception: pass
    sc["note"] = t(sc.get("note", ""), lang)
    return sc

def catalog_agents(pub, lang):
    if lang not in LANGS: return pub
    for a in pub.get("agents", []):
        a["description"] = t(a.get("description", ""), lang)
        for k in ("outfits", "poses", "bodies"):
            for o in a.get(k, []) or []:
                if isinstance(o, dict): o["name"] = t(o.get("name", ""), lang)
    return pub

def config(d, lang):
    if lang not in LANGS: return d
    d = dict(d); d["chat_notice"] = t(d.get("chat_notice", ""), lang)
    if isinstance(d.get("live"), dict): d["live"] = dict(d["live"], note=t(d["live"].get("note", ""), lang))
    return d
