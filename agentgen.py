# -*- coding: utf-8 -*-
"""Generator agentek z OPISU (v1.6.6, t429u/t430u). Bez przesyłania zdjęć przez zwykłych użytkowników.
Kroki: 1 Opis → 2 Warianty (AI, kilka próbek) → 3 Wybór (1–4) → 4 Sprawdzenie (nsfw_filter + moderacja, tylko wybrane) → 5 Profil gotowy.
Uczciwość: prawdziwa generacja wymaga dostawcy AI (LUNA_IMAGE_API_URL / LUNA_IMAGE_API_KEY, wideo: LUNA_VIDEO_API_URL / KEY).
Bez klucza zadanie czeka w kolejce z jasnym komunikatem – nigdy nie podstawiamy gotowych zdjęć Luny jako „wygenerowanych”.
Kontrakt dostawcy obrazów: POST {prompt, negative, n, max_px} → {"images": ["<base64 JPEG/PNG>", ...]}.
Kontrakt dostawcy wideo:   POST {prompt, image (base64 twarzy agentki), n, seconds, height} → {"videos": ["<base64 MP4>", ...]}.
Agentki na podstawie zdjęć PRAWDZIWEJ osoby: tylko ścieżka admina przy potwierdzonej współpracy (umowa + zgoda), flaga na agentce."""
import base64, hashlib, json, os, re, secrets, threading, time, urllib.request
import store, plans, quality, imgsafe, social

N_IMG, N_VID, PICK_MAX = 4, 3, 4
DESC_LEN, NAME_LEN = 200, 24
SRC_TTL = 30 * 86400
_lock = threading.Lock()

def _o(pl, en, es, de, uk, pro=False):
    d = {"pl": pl, "en": en, "es": es, "de": de, "uk": uk}
    if pro: d["pro"] = True   # opcja dla Pro/Ultra (i partnerek)
    return d
P_ = True
OPTS = {
 # --- Sylwetka ---
 "body": {"slim": _o("szczupła", "slim build", "delgada", "schlank", "струнка"), "athletic": _o("wysportowana", "athletic build", "atlética", "sportlich", "атлетична"),
          "average": _o("przeciętna", "average build", "media", "durchschnittlich", "середня"), "petite": _o("drobna", "petite build", "menuda", "zierlich", "мініатюрна"),
          "curvy": _o("krągła", "curvy build", "con curvas", "kurvig", "з формами"), "plus": _o("plus size", "plus-size build", "talla grande", "Plus Size", "плюс-сайз")},
 # --- Twarz ---
 "eyes": {"brown": _o("brązowe", "brown", "marrones", "braun", "карі"), "blue": _o("niebieskie", "blue", "azules", "blau", "блакитні"),
          "green": _o("zielone", "green", "verdes", "grün", "зелені"), "hazel": _o("piwne", "hazel", "avellana", "haselnuss", "горіхові"),
          "grey": _o("szare", "grey", "grises", "grau", "сірі"), "amber": _o("bursztynowe", "amber", "ámbar", "bernsteinfarben", "бурштинові", P_)},
 "eyeshape": {"almond": _o("migdałowe", "almond-shaped", "almendrados", "mandelförmig", "мигдалеподібні"), "round": _o("okrągłe", "round", "redondos", "rund", "круглі"),
              "hooded": _o("z opadającą powieką", "hooded", "encapotados", "mit Schlupflid", "з нависаючою повікою"), "upturned": _o("lekko uniesione", "upturned", "rasgados hacia arriba", "nach oben geneigt", "трохи підняті"),
              "monolid": _o("bez fałdu powieki", "monolid", "monopárpado", "Monolid", "без складки повіки")},
 "skin": {"fair": _o("bardzo jasna", "fair", "muy clara", "sehr hell", "дуже світла"), "light": _o("jasna", "light", "clara", "hell", "світла"),
          "medium": _o("średnia", "medium", "media", "mittel", "середня"), "olive": _o("oliwkowa", "olive", "oliva", "oliv", "оливкова"),
          "tan": _o("śniada", "tan", "morena", "gebräunt", "смаглява"), "deep": _o("ciemna", "deep brown", "oscura", "dunkel", "темна")},
 "face": {"oval": _o("owalna", "oval", "ovalada", "oval", "овальне"), "round": _o("okrągła", "round", "redonda", "rund", "кругле"),
          "heart": _o("w kształcie serca", "heart-shaped", "de corazón", "herzförmig", "у формі серця"), "square": _o("kwadratowa", "square jaw", "cuadrada", "eckig", "квадратне"),
          "long": _o("pociągła", "long", "alargada", "länglich", "видовжене", P_)},
 "features": {"freckles": _o("piegi", "freckles", "pecas", "Sommersprossen", "веснянки"), "dimples": _o("dołeczki", "dimples", "hoyuelos", "Grübchen", "ямочки"),
              "mole": _o("pieprzyk", "beauty mark", "lunar", "Muttermal", "родимка"), "glasses": _o("okulary", "glasses", "gafas", "Brille", "окуляри"),
              "gap": _o("przerwa między zębami", "tooth gap", "diastema", "Zahnlücke", "щілинка між зубами", P_)},
 "makeup": {"natural": _o("naturalny", "natural makeup", "natural", "natürlich", "природний"), "none": _o("bez makijażu", "no makeup", "sin maquillaje", "ungeschminkt", "без макіяжу"),
            "soft": _o("delikatny glam", "soft glam makeup", "glam suave", "dezenter Glam", "легкий глем"), "bold": _o("wyraziste usta", "bold lipstick", "labios intensos", "kräftige Lippen", "яскраві губи"),
            "artistic": _o("artystyczny", "artistic makeup", "artístico", "künstlerisch", "артистичний", P_)},
 # --- Włosy ---
 "hair": {"brown": _o("brązowe", "brown", "castaño", "braun", "каштанове"), "blond": _o("blond", "blonde", "rubio", "blond", "біляве"),
          "black": _o("czarne", "black", "negro", "schwarz", "чорне"), "red": _o("rude", "red", "pelirrojo", "rot", "руде"),
          "silver": _o("srebrne", "silver", "plateado", "silbern", "срібне"), "pastel": _o("pastelowe", "pastel", "pastel", "pastell", "пастельне"),
          "ombre": _o("ombre", "ombre", "ombré", "Ombré", "омбре", P_)},
 "hairlen": {"long": _o("długie", "long", "largo", "lang", "довге"), "shoulder": _o("do ramion", "shoulder-length", "media melena", "schulterlang", "до плечей"),
             "short": _o("krótkie", "short", "corto", "kurz", "коротке"), "vlong": _o("bardzo długie", "very long", "muy largo", "sehr lang", "дуже довге")},
 "hairstyle": {"wavy": _o("fale", "wavy", "ondulado", "wellig", "хвилясте"), "straight": _o("proste", "straight", "liso", "glatt", "пряме"),
               "curly": _o("loki", "curly", "rizado", "lockig", "кучеряве"), "ponytail": _o("kucyk", "ponytail", "coleta", "Pferdeschwanz", "хвіст"),
               "bun": _o("kok", "bun", "moño", "Dutt", "гулька"), "braid": _o("warkocz", "braid", "trenza", "Zopf", "коса"),
               "bob": _o("bob", "bob cut", "bob", "Bob", "боб"), "pixie": _o("pixie", "pixie cut", "pixie", "Pixie", "піксі"),
               "afro": _o("afro", "afro", "afro", "Afro", "афро"), "locs": _o("dredy", "locs", "rastas", "Locs", "локси")},
 # --- Wiek (wygląd) – zawsze dorosła ---
 "agelook": {"20": _o("20+", "in her twenties (adult)", "20+", "20+", "20+"), "30": _o("30+", "in her thirties", "30+", "30+", "30+"),
             "40": _o("40+", "in her forties", "40+", "40+", "40+"), "50": _o("50+", "in her fifties", "50+", "50+", "50+")},
 # --- Styl ---
 "style": {"elegant": _o("elegancki", "elegant", "elegante", "elegant", "елегантний"), "casual": _o("swobodny", "casual", "informal", "lässig", "повсякденний"),
           "business": _o("biznesowy", "business", "de negocios", "business", "діловий"), "sporty": _o("sportowy", "sporty", "deportivo", "sportlich", "спортивний"),
           "street": _o("streetwear", "streetwear", "urbano", "Streetwear", "стрітвір"), "boho": _o("boho", "boho", "boho", "boho", "бохо"),
           "gala": _o("gala", "black-tie gala", "de gala", "Gala", "гала"), "retro": _o("retro", "retro", "retro", "retro", "ретро"),
           "minimal": _o("minimalizm", "minimalist", "minimalista", "minimalistisch", "мінімалізм", P_), "future": _o("futurystyczny", "futuristic", "futurista", "futuristisch", "футуристичний", P_),
           "cottage": _o("cottagecore", "cottagecore", "cottagecore", "Cottagecore", "котеджкор", P_), "avant": _o("awangarda", "avant-garde", "vanguardista", "Avantgarde", "авангард", P_)},
 "outfit": {"sweater": _o("sweter z golfem", "turtleneck sweater", "jersey de cuello alto", "Rollkragenpullover", "светр з горлом"),
            "blazer": _o("marynarka i spodnie", "blazer and trousers", "americana y pantalón", "Blazer und Hose", "жакет і штани"),
            "maxi": _o("sukienka maxi z rękawem", "long-sleeve maxi dress", "vestido largo con manga", "Maxikleid mit Ärmeln", "сукня максі з рукавами"),
            "jumpsuit": _o("kombinezon", "jumpsuit", "mono", "Jumpsuit", "комбінезон"), "coat": _o("płaszcz", "coat", "abrigo", "Mantel", "пальто"),
            "tracksuit": _o("dres", "tracksuit", "chándal", "Trainingsanzug", "спортивний костюм"), "hoodie": _o("bluza z kapturem", "hoodie and jeans", "sudadera y vaqueros", "Hoodie und Jeans", "худі й джинси"),
            "gown": _o("suknia wieczorowa z rękawem", "long-sleeve evening gown", "vestido de noche con manga", "Abendkleid mit Ärmeln", "вечірня сукня з рукавами"),
            "suit": _o("garnitur damski", "tailored suit", "traje a medida", "Hosenanzug", "жіночий костюм", P_), "kimono": _o("płaszcz-kimono", "kimono-style coat", "abrigo kimono", "Kimono-Mantel", "пальто-кімоно", P_)},
 "acc": {"earrings": _o("kolczyki", "earrings", "pendientes", "Ohrringe", "сережки"), "scarf": _o("szal", "scarf", "bufanda", "Schal", "шарф"),
         "watch": _o("zegarek", "watch", "reloj", "Armbanduhr", "годинник"), "hat": _o("kapelusz", "hat", "sombrero", "Hut", "капелюх"),
         "headphones": _o("słuchawki", "headphones", "auriculares", "Kopfhörer", "навушники"), "mic": _o("mikrofon", "microphone", "micrófono", "Mikrofon", "мікрофон"),
         "beret": _o("beret", "beret", "boina", "Baskenmütze", "берет", P_), "necklace": _o("naszyjnik", "statement necklace", "collar llamativo", "Statement-Kette", "кольє", P_)},
 # --- Charakter ---
 "personality": {"witty": _o("dowcipna", "witty", "ingeniosa", "witzig", "дотепна"), "warm": _o("ciepła", "warm", "cálida", "herzlich", "тепла"),
                 "cheerful": _o("pogodna", "cheerful", "alegre", "fröhlich", "життєрадісна"), "calm": _o("spokojna", "calm", "tranquila", "ruhig", "спокійна"),
                 "energetic": _o("energiczna", "energetic", "enérgica", "energisch", "енергійна"), "factual": _o("rzeczowa", "matter-of-fact", "directa", "sachlich", "по суті")},
 "voice": {"warm": _o("ciepły", "warm", "cálida", "warm", "теплий"), "soft": _o("miękki", "soft", "suave", "sanft", "м'який"),
           "bright": _o("jasny", "bright", "brillante", "hell", "дзвінкий"), "low": _o("niski", "low", "grave", "tief", "низький"),
           "crisp": _o("wyraźny", "crisp", "nítida", "klar", "чіткий"), "husky": _o("lekko zachrypnięty", "slightly husky", "algo ronca", "leicht rauchig", "трохи хрипкуватий", P_)},
 "pose": {"portrait": _o("portret", "head-and-shoulders portrait", "retrato", "Porträt", "портрет"), "wave": _o("macha na powitanie", "waving hello", "saludando", "winkt", "махає"),
          "mic": _o("z mikrofonem", "holding a microphone", "con micrófono", "mit Mikrofon", "з мікрофоном"), "arms": _o("ręce skrzyżowane", "arms crossed confidently", "brazos cruzados", "verschränkte Arme", "схрещені руки"),
          "sitting": _o("siedzi", "sitting relaxed", "sentada", "sitzend", "сидить"), "walking": _o("w ruchu", "walking", "caminando", "gehend", "у русі", P_)},
 "mood": {"smile": _o("uśmiech", "warm smile", "sonrisa", "Lächeln", "усмішка"), "confident": _o("pewna siebie", "confident", "segura", "selbstbewusst", "впевнена"),
          "calm": _o("spokój", "calm", "serena", "gelassen", "спокій"), "playful": _o("figlarna", "playful", "juguetona", "verspielt", "грайлива"),
          "focused": _o("skupiona", "focused", "concentrada", "konzentriert", "зосереджена")},
 "scene": {"studio": _o("studio", "soft studio backdrop", "estudio", "Studio", "студія"), "city": _o("miasto", "city street", "ciudad", "Stadt", "місто"),
           "cafe": _o("kawiarnia", "cozy café", "cafetería", "Café", "кав'ярня"), "stage": _o("scena", "stage with spotlight", "escenario", "Bühne", "сцена"),
           "park": _o("park", "green park", "parque", "Park", "парк"), "office": _o("biuro", "modern office", "oficina", "Büro", "офіс"),
           "library": _o("biblioteka", "library", "biblioteca", "Bibliothek", "бібліотека", P_), "nightcity": _o("nocne miasto", "city lights at night", "ciudad de noche", "Stadt bei Nacht", "нічне місто", P_)},
 "spec": {"diction": _o("dykcja", "diction", "dicción", "Aussprache", "дикція"), "public": _o("wystąpienia", "public speaking", "hablar en público", "Reden halten", "виступи"),
          "confidence": _o("pewność siebie", "confidence", "seguridad", "Selbstsicherheit", "впевненість"), "breath": _o("oddech", "breathing", "respiración", "Atmung", "дихання"),
          "tempo": _o("tempo mowy", "speech pace", "ritmo del habla", "Sprechtempo", "темп мовлення"), "emotion": _o("emocje w głosie", "emotion in voice", "emoción en la voz", "Gefühl in der Stimme", "емоції в голосі")},
}
MULTI = {"features": 3, "acc": 3, "spec": 3}   # pola wielokrotnego wyboru (maks.)
# sekcje panelu (zwijane); w każdej opcjonalny krótki tekst własny
SECTIONS = [("body", ["height", "body"]), ("face", ["eyes", "eyeshape", "skin", "face", "features", "makeup"]), ("hair", ["hair", "hairlen", "hairstyle"]),
            ("age", ["agelook"]), ("style", ["style", "outfit", "acc"]), ("char", ["personality", "voice", "pose", "mood", "scene", "spec"])]
PRO_FIELDS = {"eyeshape", "face"}   # całe pola tylko dla Pro/Ultra
HEIGHT = (150, 190)                 # cm; Premium co 5 cm, Pro/Ultra co 1 cm
AGE_FINE = (21, 59)                 # Pro/Ultra: dokładny wiek wyglądu (zawsze dorosła)
X_LEN = 60
POP_MIN = 30                        # od ilu anonimowych wyborów w polu ranking „Najpopularniejsze” zastępuje kolejność redakcyjną

EN_PROMPT = {"hair": "{} hair", "eyes": "{} eyes", "style": "{} style", "outfit": "wearing a modest {}"}
SAFE = ("original fictional adult woman (clearly over 21, never childlike), fully clothed modest outfit covering shoulders to knees (style, not nudity), "
        "non-suggestive friendly pose, friendly portrait, soft studio light, no logos or brands, does not resemble any real person, clearly an AI character")
# Stały negatywny prompt (t479u) – dodawany ZAWSZE przez serwer, użytkownik nie ma na niego wpływu.
NEG = ("nudity, nude, naked, topless, nipples, genitals, explicit, nsfw, porn, sexual, erotic, sexy, seductive, suggestive pose, provocative, "
       "lingerie, underwear, bra, panties, swimwear, bikini, cleavage, low-cut, see-through, sheer, transparent clothing, wet clothes, bare skin, "
       "bare chest, bare midriff, short skirt, fetish, latex, bdsm, minor, child, teen, teenager, schoolgirl, childlike face, young-looking, loli, "
       "logo, brand, celebrity, real person, lookalike, text, watermark")
# Najostrzejsze ustawienia bezpieczeństwa dostawcy AI – wysyłane ZAWSZE (bez przełącznika, także dla admina). Adapter dostawcy mapuje je
# na jego parametry (np. safety_tolerance=0 FLUX/BFL, enable_safety_checker=true fal/Replicate, moderation="auto" OpenAI, safe_mode=true).
# Uwaga: działają tylko u dostawcy, który je obsługuje – i tak każdy wynik przechodzi przez nasz filtr (upload_gate) przed pokazaniem.
PROVIDER_SAFETY = {"safety_level": "strictest", "safe_mode": True, "nsfw": False, "safety_tolerance": 0, "enable_safety_checker": True,
                   "disable_safety_checker": False, "moderation": "auto", "content_filter": "strict", "allow_adult": False, "person_generation": "allow_adult"}

def safe_body(prompt_text, extra):
    """Treść żądania do dostawcy: sprawdzony prompt + stały negatywny prompt + najostrzejsze ustawienia bezpieczeństwa (nie do nadpisania)."""
    import textsafe
    p = str(prompt_text or "")
    if SAFE not in p: p = p + ", " + SAFE
    textsafe.check_prompt(p.replace(SAFE, ""), "gen_final")   # ostatnia kontrola tuż przed wysłaniem (gdyby szkic ominął walidację)
    body = dict(extra); body.update({"prompt": p, "negative": NEG, "negative_prompt": NEG}); body.update(PROVIDER_SAFETY)
    return body

def _flagged(r, i):
    """Czy dostawca sam oznaczył i-ty wynik jako NSFW (has_nsfw_concepts / nsfw_content_detected / flagged / content_filter)."""
    for k in ("has_nsfw_concepts", "nsfw_content_detected", "nsfw", "flagged"):
        v = r.get(k)
        if isinstance(v, list) and i < len(v) and v[i]: return True
        if v is True: return True
    return False
# czarna lista opisu: treści seksualne, nieletni, marki, „jak <prawdziwa osoba>”
BLOCK = re.compile(r"(sex|seks|nag[aio]|nud|erot|porn|bielizn|lingerie|bikini|strip|topless|cycki|biust|boob|nsfw|fetysz|fetish|"
                   r"dziec|dziewczynk|nastolat|nieletn|teen|child|kid|loli|schoolgirl|uczennic|minor|"
                   r"\b(?:nike|adidas|gucci|chanel|louis ?vuitton|prada|dior|zara|h&m|apple|coca[- ]?cola|pepsi|supreme|balenciaga|versace)\b|"
                   r"wygl[aą]da(?:j[aą]c[aą])? jak|looks? like|look-?alike|sobowt[oó]r|doppelg|se parece a|sieht aus wie|схож[аи] на|"
                   r"celeb|influencer|gwiazd[ay] (?:filmu|tv)|aktork[ai]\b|piosenkark)", re.I)
FULLNAME = re.compile(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\b")

def engine_img(): return bool(os.getenv("LUNA_IMAGE_API_URL") and os.getenv("LUNA_IMAGE_API_KEY"))
def engine_vid(): return bool(os.getenv("LUNA_VIDEO_API_URL") and os.getenv("LUNA_VIDEO_API_KEY"))

def options(lang="pl", plan="premium"):
    pro = tier_of(plan) == "pro"; out = {}
    for k, d in OPTS.items():
        order, real = ranked(k)
        out[k] = {"items": [{"id": i, "label": d[i].get(lang) or d[i]["pl"], **({"pro": True} if d[i].get("pro") else {}),
                             **({"lock": True} if d[i].get("pro") and not pro else {})} for i in order],
                  "top": 3 if k not in ("agelook",) else 0, "real": real, "multi": MULTI.get(k, 0), "pro": k in PRO_FIELDS}
    return {"fields": out, "sections": [{"id": s_, "fields": f} for s_, f in SECTIONS], "tier": "pro" if pro else "basic",
            "height": {"min": HEIGHT[0], "max": HEIGHT[1], "step": 1 if pro else 5}, "age_fine": {"min": AGE_FINE[0], "max": AGE_FINE[1]} if pro else None, "x_len": X_LEN}

def clean_desc(t, n=None):
    n = n or DESC_LEN
    t = re.sub(r"[<>\x00-\x1f\x7f]", "", str(t or "")).strip()[:n]
    if not t: return ""
    if BLOCK.search(t): raise ValueError("Opis zawiera niedozwolone słowa (treści seksualne, nieletni, marki albo prawdziwe osoby). Opisz charakter i styl agentki. 💚")
    import textsafe
    textsafe.check_prompt(t, "gen_desc")   # 5 języków: seks, skąpe stroje, nieletni, wiek < 21 – odmowa przed generacją
    if FULLNAME.search(t): raise ValueError("Bez imion i nazwisk prawdziwych osób – agentka ma być oryginalna. 😉")
    social.check_text(t, n)
    return t

def _J(): return store.get("agent_gen", {}) or {}
def _put(J): store.put("agent_gen", J)

EN_FIELD = {"body": "{}", "eyes": "{} eyes", "eyeshape": "{} eyes", "skin": "{} skin tone", "face": "{} face", "makeup": "{}",
            "hair": "{} hair", "hairlen": "{} hair", "hairstyle": "{} hairstyle", "agelook": "adult woman {}", "style": "{} style",
            "outfit": "wearing a modest {}", "personality": "{} expression", "pose": "{}", "mood": "{} mood", "scene": "background: {}"}

def prompt(d):
    """Wszystkie wybory → jeden prompt (EN). Zawsze: dorosła, w pełni ubrana, oryginalna, oznaczona jako AI."""
    parts = []
    if d.get("age_fine"): parts.append(f"adult woman, looks about {d['age_fine']} years old")
    for k, f in EN_FIELD.items():
        if k == "agelook" and d.get("age_fine"): continue
        if d.get(k): parts.append(f.format(OPTS[k][d[k]]["en"]))
    if d.get("height"): parts.append(f"about {d['height']} cm tall")
    for k in ("features", "acc"):
        if d.get(k): parts.append(("with " if k == "features" else "accessories: ") + ", ".join(OPTS[k][x]["en"] for x in d[k]))
    for sec, txt in (d.get("x") or {}).items(): parts.append(f"{sec} details: {txt}")
    if d.get("desc"): parts.append("details: " + d["desc"])
    return ", ".join(parts + [SAFE])

def tier_of(plan):
    return "pro" if plans.has(plan, "pro") else "basic"

def _draft_in(d, plan="premium"):
    pro = tier_of(plan) == "pro"
    def need_pro(): raise PermissionError("To opcja dla Pro/Ultra – ale i bez niej Twoja agentka będzie świetna. 😉")
    out = {}
    for k in OPTS:
        if k in MULTI:
            v = [x for x in dict.fromkeys(d.get(k) or []) if isinstance(x, str)][:MULTI[k]]
            if any(x not in OPTS[k] for x in v): raise ValueError("Nieznana opcja.")
        else:
            v = str(d.get(k) or "")
            if v and v not in OPTS[k]: raise ValueError("Nieznana opcja.")
            if v and k in PRO_FIELDS and not pro: need_pro()
        if not pro and any(OPTS[k][x].get("pro") for x in (v if isinstance(v, list) else [v] if v else [])): need_pro()
        out[k] = v
    for k in ("hair", "outfit", "personality"):
        if not out[k]: raise ValueError("Wybierz kolor włosów, strój i charakter – resztę możesz pominąć (albo kliknij „Losuj”).")
    out["spec"] = out["spec"] or ["diction"]
    h = d.get("height")
    if h not in (None, "", 0):
        try: h = int(h)
        except Exception: raise ValueError("Wzrost podaj liczbą.")
        h = max(HEIGHT[0], min(HEIGHT[1], h))
        out["height"] = h if pro else int(round(h / 5.0) * 5)
    else: out["height"] = None
    af = d.get("age_fine")
    if af not in (None, "", 0):
        if not pro: need_pro()
        try: af = int(af)
        except Exception: raise ValueError("Wiek wyglądu podaj liczbą.")
        out["age_fine"] = max(AGE_FINE[0], min(AGE_FINE[1], af))   # nigdy poniżej 21 – zawsze dorosła
    else: out["age_fine"] = None
    X = {}
    for sec, _f in SECTIONS:
        t = (d.get("x") or {}).get(sec) if isinstance(d.get("x"), dict) else None
        if t: X[sec] = clean_desc(t, X_LEN)
    out["x"] = X
    out["desc"] = clean_desc(d.get("desc"))
    nm = re.sub(r"[<>\x00-\x1f]", "", str(d.get("name") or "")).strip()[:NAME_LEN]
    if nm:
        if re.fullmatch(r"\W*luna\W*", nm.lower()) or FULLNAME.search(nm) or BLOCK.search(nm): raise ValueError("Wybierz inne imię agentki.")
        import textsafe
        textsafe.check_prompt(nm, "gen_name")
        social.check_text(nm, NAME_LEN)
    out["name"] = nm
    return out

# ---------- 🔥 Najpopularniejsze: tylko zbiorcze, anonimowe liczniki wyborów (bez danych o osobach) ----------
def _count(dr):
    with _lock:
        C = store.get("agentgen_pop", {}) or {}
        for k in OPTS:
            v = dr.get(k)
            for x in (v if isinstance(v, list) else [v] if v else []):
                C.setdefault(k, {}); C[k][x] = int(C[k].get(x, 0)) + 1
        store.put("agentgen_pop", C)

def ranked(k):
    """(kolejność id, czy_z_danych). Przy małej liczbie wyborów – kolejność redakcyjna (bez udawanych liczb)."""
    C = (store.get("agentgen_pop", {}) or {}).get(k) or {}
    ids = list(OPTS[k])
    if sum(C.values()) < POP_MIN: return ids, False
    return sorted(ids, key=lambda i: (-int(C.get(i, 0)), ids.index(i))), True

def current(uid):
    J = _J(); js = [j for j in J.values() if j["uid"] == uid and j["kind"] == "img"]
    return max(js, key=lambda j: j["t"]) if js else None

def submit(uid, plan, d):
    """Krok 1→2: zapis opisu i zadanie wygenerowania wariantów (w planie). Zwraca (zadanie, None) albo (None, blokada planu)."""
    if not plans.has(plan, "premium"): return None, quality.lock("premium", "gen")
    dr = _draft_in(d, plan)
    cur = current(uid)
    if cur and cur["status"] in ("waiting", "generating", "checking"): raise ValueError("Poprzednie zadanie jeszcze trwa. 🙂")
    j = {"id": secrets.token_hex(6), "uid": uid, "kind": "img", "t": int(time.time()), "plan": plan, "px": quality.caps(plan)["gen_px"],
         "draft": dr, "prompt": safe_body(prompt(dr), {})["prompt"], "status": "waiting", "variants": [], "picked": [], "approved": [], "note": ""}
    with _lock: J = _J(); J[j["id"]] = j; _put(J)
    try: _count(dr)
    except Exception: pass
    _kick(j["id"])
    return view(j), None

def _call(url, key, body, timeout=120):
    rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(rq, timeout=timeout) as r: return json.loads(r.read().decode())

def _kick(jid):
    j = _J().get(jid)
    if not j: return
    if (j["kind"] == "img" and not engine_img()) or (j["kind"] == "vid" and not engine_vid()): return  # czeka w kolejce – uczciwie
    threading.Thread(target=_run, args=(jid,), daemon=True).start()

def _upd(jid, **kw):
    with _lock:
        J = _J(); j = J.get(jid)
        if j: j.update(kw); _put(J)
        return j

def _run(jid):
    j = _J().get(jid)
    if not j or j["status"] != "waiting": return
    ok, n, lim = quality.gen_take(j["uid"], j["plan"])
    if not ok: _upd(jid, note="limit"); return   # limit dzienny – zadanie poczeka do jutra
    _upd(jid, status="generating")
    try:
        if j["kind"] == "img":
            r = _call(os.getenv("LUNA_IMAGE_API_URL"), os.getenv("LUNA_IMAGE_API_KEY"), safe_body(j["prompt"], {"n": N_IMG, "max_px": j["px"]}))
            vs = []; drop = 0
            import upload_gate
            for i, b in enumerate((r.get("images") or [])[:N_IMG]):
                if _flagged(r, i): drop += 1; continue   # dostawca sam oznaczył wynik
                try:   # skan WYNIKU przed pokazaniem komukolwiek (także autorce): nagość lub „na granicy” = wariant usunięty
                    g = upload_gate.image(base64.b64decode(b), "agent_gen", max_px=j["px"], max_in=20 * 1024 * 1024, quality=2, review="block")
                except Exception: drop += 1; continue
                out, ext = g.bytes, g.ext
                if quality.is_user_photo(out): continue   # odcisk: zdjęcie z walla nigdy nie zostaje twarzą agentki
                vid = secrets.token_hex(6); store.put("agimg:" + vid, {"b": base64.b64encode(out).decode(), "ext": ext, "uid": j["uid"], "ai": True})
                vs.append(vid)
        else:
            face = store.get("agimg:" + j["face"], {}) or {}
            r = _call(os.getenv("LUNA_VIDEO_API_URL"), os.getenv("LUNA_VIDEO_API_KEY"), safe_body(j["prompt"], {"image": face.get("b", ""), "n": N_VID,
                                                                                         "seconds": j["secs"], "height": j["h"]}), timeout=600)
            import agentvideo, upload_gate
            os.makedirs(agentvideo.VDIR, exist_ok=True); vs = []; drop = 0
            for i, b in enumerate((r.get("videos") or [])[:N_VID]):
                if _flagged(r, i): drop += 1; continue
                vid = secrets.token_hex(6); p = os.path.join(agentvideo.VDIR, "g_" + vid + ".mp4"); open(p, "wb").write(base64.b64decode(b))
                try:   # każda próbka klatek (1/s, do 24) przez filtr nagości; „na granicy” też odpada
                    if upload_gate.video_file(p, "agent_vid") != "ok": raise ValueError("review")
                except Exception:
                    drop += 1
                    try: os.remove(p)
                    except Exception: pass
                    continue
                vs.append(vid)
        _upd(jid, status="variants" if vs else "failed", variants=vs, note="" if vs else ("nsfw" if drop else "empty"))
    except Exception as e:
        _upd(jid, status="waiting", note="retry")   # błąd dostawcy: zostaje w kolejce

def pick(uid, jid, ids):
    """Krok 3→4: wybrane warianty (1–4) idą do nsfw_filter + moderacji; pozostałe są usuwane."""
    J = _J(); j = J.get(jid)
    if not j or j["uid"] != uid or j["status"] != "variants": raise ValueError("Nie ma wariantów do wyboru.")
    ids = [i for i in dict.fromkeys(ids or []) if i in j["variants"]][:PICK_MAX if j["kind"] == "img" else 1]
    if not ids: raise ValueError("Wybierz co najmniej jeden wariant.")
    for v in j["variants"]:
        if v not in ids: _drop(j, v)
    verdict = {}
    for v in ids:
        verdict[v] = _nsfw(j, v)
    bad = [v for v, ok in verdict.items() if ok is False]
    for v in bad: _drop(j, v)
    keep = [v for v in ids if v not in bad]
    j2 = _upd(jid, picked=keep, variants=keep, status="checking" if keep else "rejected", note="nsfw" if bad else "")
    return view(j2)

def _nsfw(j, v):
    """Drugi skan przy wyborze (pierwszy był zaraz po generacji). Nagość, „na granicy”, błąd filtra = wariant odrzucony (fail-closed).
    Nawet „ok” i tak trafia do moderatora (None)."""
    try:
        import upload_gate, agentvideo
        if j["kind"] != "img":
            return None if upload_gate.video_file(os.path.join(agentvideo.VDIR, "g_" + v + ".mp4"), "agent_vid_pick") == "ok" else False
        raw = base64.b64decode((store.get("agimg:" + v) or {})["b"])
        upload_gate.image(raw, "agent_gen_pick", max_px=4096, max_in=20 * 1024 * 1024, review="block")
        return None
    except Exception: return False

def _drop(j, v):
    if j["kind"] == "img": store.put("agimg:" + v, None)
    else:
        try:
            import agentvideo; os.remove(os.path.join(agentvideo.VDIR, "g_" + v + ".mp4"))
        except Exception: pass

def moderate(jid, approve_ids, plan_of):
    """Krok 4→5 (moderator): zatwierdzone obrazy → agentka z automatycznym profilem; odrzucone są usuwane."""
    J = _J(); j = J.get(jid)
    if not j or j["status"] != "checking": raise ValueError("Brak zadania do sprawdzenia.")
    ok = [v for v in j["picked"] if v in (approve_ids or [])]
    for v in j["picked"]:
        if v not in ok: _drop(j, v)
    if not ok: _upd(jid, status="rejected", approved=[], note="mod"); return _J()[jid]
    if j["kind"] == "img":
        import profiles
        mark_approved(ok)
        pid = profiles.create_from_gen(j["uid"], plan_of(j["uid"]), j["draft"], ok)
        _upd(jid, status="done", approved=ok, pid=pid)
    else:
        _upd(jid, status="done", approved=ok)
    try:
        import inbox
        inbox.deliver(j["uid"], "important", title={"pl": "✨ Twoja agentka AI jest gotowa", "en": "✨ Your AI agent is ready", "es": "✨ Tu agente IA está lista",
                                                    "de": "✨ Deine KI-Agentin ist fertig", "uk": "✨ Ваша ШІ-агентка готова"} if j["kind"] == "img" else
                      {"pl": "🎬 Film agentki zatwierdzony", "en": "🎬 Agent video approved", "es": "🎬 Vídeo de la agente aprobado", "de": "🎬 Agentinnen-Video freigegeben", "uk": "🎬 Відео агентки схвалено"},
                      body={"pl": "Przeszła sprawdzenie i ma już profil. Pora na pierwszą bitwę? 😄", "en": "She passed the check and has a profile. First battle, maybe? 😄",
                            "es": "Pasó la revisión y ya tiene perfil. ¿Primera batalla? 😄", "de": "Sie hat die Prüfung bestanden und ein Profil. Erstes Battle? 😄",
                            "uk": "Вона пройшла перевірку й уже має профіль. Може, перший батл? 😄"}, link="/agentka.html?id=me", dedupe="ag:" + jid)
    except Exception: pass
    return _J()[jid]

def submit_video(uid, plan, pid_face):
    if not plans.has(plan, "premium"): return None, quality.lock("premium", "gen")
    import agentvideo
    L = agentvideo.limits(plan)
    cur = current(uid)
    if not cur or cur["status"] != "done" or not cur.get("approved"): raise ValueError("Najpierw stwórz agentkę (obraz musi przejść sprawdzenie).")
    if any(j["uid"] == uid and j["kind"] == "vid" and j["status"] in ("waiting", "generating", "checking") for j in _J().values()):
        raise ValueError("Film już się robi. Cierpliwości – dobre ujęcia lubią spokój. 🎬")
    j = {"id": secrets.token_hex(6), "uid": uid, "kind": "vid", "t": int(time.time()), "plan": plan, "secs": L["max_s"], "h": int(L["label"]),
         "face": cur["approved"][0], "prompt": cur["prompt"] + ", gentle natural movement, speaking calmly to camera", "status": "waiting", "variants": [], "picked": [], "approved": [], "note": ""}
    with _lock: J = _J(); J[j["id"]] = j; _put(J)
    _kick(j["id"]); return view(j), None

def view(j):
    if not j: return None
    u = (lambda v: f"/api/agent/gen/img/{v}.jpg") if j["kind"] == "img" else (lambda v: f"/api/agent/gen/vid/{v}.mp4")
    st = j["status"]
    step = {"waiting": 2, "generating": 2, "variants": 3, "checking": 4, "rejected": 1, "failed": 1, "done": 5}.get(st, 1)
    return {"id": j["id"], "kind": j["kind"], "status": st, "step": step, "note": j.get("note", ""), "t": j["t"],
            "variants": [{"id": v, "url": u(v)} for v in j["variants"]], "picked": j["picked"], "pid": j.get("pid"),
            "secs": j.get("secs"), "h": j.get("h"), "engine": engine_img() if j["kind"] == "img" else engine_vid(), "draft": j.get("draft")}

def state(uid):
    J = _J()
    vids = sorted([j for j in J.values() if j["uid"] == uid and j["kind"] == "vid"], key=lambda j: -j["t"])
    return {"img": view(current(uid)), "vid": view(vids[0]) if vids else None, "engine": {"img": engine_img(), "video": engine_vid()}}

def img_for(vid, viewer_uid):
    i = store.get("agimg:" + vid) or None
    if not i: return None
    if i.get("approved") or i.get("uid") == viewer_uid: return i
    return None

def mark_approved(vids):
    for v in vids:
        i = store.get("agimg:" + v)
        if i: i["approved"] = True; store.put("agimg:" + v, i)

def admin_list():
    return [dict(view(j), uid8=j["uid"][:8], prompt=j["prompt"]) for j in sorted(_J().values(), key=lambda j: -j["t"]) if j["status"] in ("checking", "waiting", "generating")][:100]

def delete_owner(uid):
    with _lock:
        J = _J()
        for k in [k for k, j in J.items() if j["uid"] == uid]:
            for v in J[k]["variants"] + J[k].get("approved", []): _drop(J[k], v)
            J.pop(k)
        _put(J)

def purge(now=None):
    """Porządki: zadania i niewybrane warianty starsze niż 30 dni są usuwane (oczekujące w kolejce też)."""
    now = now or time.time()
    with _lock:
        J = _J(); n = 0
        for k in [k for k, j in J.items() if j["status"] != "done" and now - j["t"] > SRC_TTL]:
            for v in J[k]["variants"]: _drop(J[k], v)
            J.pop(k); n += 1
        if n: _put(J)
    return n

def vid_path(v, viewer_uid):
    import agentvideo
    for j in _J().values():
        if j["kind"] == "vid" and v in j["variants"] + j.get("approved", []) and (j["uid"] == viewer_uid or v in j.get("approved", [])):
            p = os.path.join(agentvideo.VDIR, "g_" + v + ".mp4")
            return p if os.path.exists(p) else None
    return None

def tick():
    """Co minutę: zadania czekające w kolejce ruszają, gdy dostawca AI jest skonfigurowany (np. po dodaniu klucza)."""
    n = 0
    for j in list(_J().values()):
        if j["status"] == "waiting" and ((j["kind"] == "img" and engine_img()) or (j["kind"] == "vid" and engine_vid())):
            _kick(j["id"]); n += 1
    return n
