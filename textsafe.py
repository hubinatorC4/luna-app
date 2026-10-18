# -*- coding: utf-8 -*-
"""Filtr tekstu (t479u): treści seksualne i seksualizacja nieletnich w 5 językach strony (PL/EN/ES/DE/UK).

  check_text(t)   – wpisy, komentarze, czaty, bio, nicki (przez social.check_text / social.nick_ok): blokuje treści seksualne
                    i każde połączenie „nieletni + seks”.
  check_prompt(t) – opisy i imiona w GENERATORZE agentek (ostrzej): do tego skąpe/prześwitujące stroje, „sexy”, nieletni,
                    dziecięcy wygląd i wiek < 21. Odmowa PRZED wysłaniem do dostawcy AI.

Normalizacja utrudnia obejścia: małe litery, bez polskich/obcych znaków diakrytycznych, cyfry/znaki jak litery (s3x, p0rn, n@ked),
cyrylica podobna do łaciny, emoji i kropki wstawione w środek słowa (p.o.r.n). Żaden filtr słów nie jest pełny – ostatecznie decyduje moderator."""
import re, unicodedata

SEXUAL = {   # początki słów (dopasowanie od początku wyrazu)
 "pl": "porn seks seksu seksem seksie seksting sex sexu nago nagi nagie naga nagą nagich nagiej nagim nagosc nagusk rozbieran rozbierz rozebran striptiz erotyk erotycz masturb orgazm onani genitali penis penisa wagin cipk cycki cyck sutek sutki sutkow fiut kutas ruchan bzykan obciag xxx nsfw hentai nudes nudesy",
 "en": "porn porno sex sexual sexting nude nudes nudity naked topless striptease stripper erotic erotica masturbat orgasm genital penis vagina pussy tits titties boobs nipple nipples blowjob handjob cumshot horny xxx nsfw hentai onlyfans fansly camgirl dickpic",
 "es": "porno sexo sexual desnud tetas pezon pezones pene vagina masturb orgasmo erotic erótic follar mamada cachond",
 "de": "porno sex sexuell nackt nacktbild erotik erotisch masturb orgasmus penis vagina titten nippel muschi fick",
 "uk": "порн секс сексуал гола голий голі голого оголен роздяг еротик мастурб оргазм пеніс вагін сиськ цицьк сосок соски мінет",
}
MINOR = {
 "pl": "dziecko dzieci dziecie dziecię dziecinn dziewczynk chlopczyk chłopczyk nieletni nastolat malolat małolat podlotek gimnazjalist uczennic uczniak lolit loli shota",
 "en": "child children childlike kid kids kiddie minor minors underage preteen teen teens teenage teenager schoolgirl schoolboy loli lolita shota toddler infant baby_face little_girl young_girl jailbait",
 "es": "niña niño niñas niños infantil menor menores adolescente colegiala chiquilla",
 "de": "kind kinder kindlich minderjährig teenager schülerin schulmädchen",
 "uk": "дитин діти дитяч неповнолітн підліт школярк школяр малолітн",
}
REVEALING = {   # tylko generator: strój ma być skromny, w pełni zakrywający
 "pl": "bielizn majtk majtecz stanik biustonosz stringi bikini kostium_kapielowy stroj_kapielowy przezroczyst przeswit prześwit dekolt seksown sexy uwodzicielsk prowokacyjn zmyslow zmysłow fetysz lateks negliz negliż polnag półnag rozebran skap skąp mikro_spodnicz kuse",
 "en": "lingerie underwear panties bra bralette thong gstring bikini swimsuit swimwear bathing_suit see_through seethrough sheer transparent cleavage sexy seductive provocative sensual sultry fetish latex bdsm bondage kinky boudoir negligee pinup pin_up playboy undress undressed undressing half_naked braless lowcut low_cut revealing skimpy wet_shirt bare_skin bare_chest shirtless",
 "es": "lencería lenceria ropa_interior bragas sujetador tanga bikini bañador banador traje_de_baño transparente escote sexy seductora provocativa sensual fetiche látex latex desnuda semidesnuda",
 "de": "dessous unterwäsche unterwasche höschen hoschen bh tanga bikini badeanzug durchsichtig transparent ausschnitt sexy verführerisch verfuhrerisch aufreizend sinnlich fetisch latex oben_ohne halbnackt",
 "uk": "білизн трусик бюстгальтер ліфчик стрінг бікіні купальник прозор декольте сексуальн спокуслив провокативн чуттєв фетиш латекс напівгол",
}
SQUASH = ("porn", "hentai", "nsfw", "nudes", "naked", "topless", "lolita", "onlyfans", "striptiz", "striptease", "nacktbild")
AGE = re.compile(r"(?<!\d)(\d{1,2})\s*-?\s*(?:lat\w*|l\b|years?\b|yrs?\b|yo\b|y/o|anos\b|años\b|jahr\w*|рок\w*|літ\w*)", re.I)
AGE2 = re.compile(r"(?:\bage[ds]?|\bwiek\w*|\bedad|\balter|\bвік\w*)\s*:?\s*(\d{1,2})(?!\d)", re.I)

# cyrylica podobna do łaciny (tylko w słowach mieszanych) i „leet”
_HOMO = str.maketrans({"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ѕ": "s", "к": "k", "т": "t", "м": "m", "н": "h", "в": "b"})
_LEET = str.maketrans("0134578@$!|", "oieastbasii")

def _fold(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower().replace("ł", "l"))
    return "".join(c for c in s if not unicodedata.combining(c))

def _norm(t):
    """Wersje tekstu do dopasowania: (słowa po normalizacji, tekst bez separatorów)."""
    s = _fold(t)
    words = []
    for w in re.findall(r"[\w@$!|]+", s):
        lat = sum(c.isascii() for c in w); cyr = sum("\u0400" <= c <= "\u04ff" for c in w)
        if lat and cyr: w = w.translate(_HOMO)              # słowo mieszane → łacina (p\u043ern)
        if any(c.isdigit() for c in w) and any(c.isalpha() for c in w) or re.search(r"[@$!|]", w): w = w.translate(_LEET)
        words.append(re.sub(r"(.)\1{2,}", r"\1\1", w))     # pooorn → poorn (dalej łapie się na początku „porn” po drugim kroku)
    s2 = " ".join(words)
    s2 = re.sub(r"\b(\w)\1+(\w)", r"\1\2", s2)
    # sklejanie tylko tam, gdzie ktoś rozdziela litery: „p.o.r.n”, „n a k e d”, „por-n” (nie skleja zwykłych słów obok siebie)
    sl = s.translate(_LEET)
    joined = re.sub(r"(?<=[^\W_])[.\-_*·•'\\/]+(?=[^\W_])", "", sl)
    runs = re.findall(r"(?:(?<![^\W_])[^\W_](?:[\W_]+|$)){3,}", sl)
    squash = " ".join([joined] + [re.sub(r"[\W_]", "", r) for r in runs])
    return s2, squash

def _terms(d):
    out = set()
    for l in d.values():
        for w in l.split(): out.add(_fold(w).replace("_", " "))
    return sorted(out, key=len, reverse=True)
_SEX, _MIN, _REV = _terms(SEXUAL), _terms(MINOR), _terms(REVEALING)
def _rx(terms, exact=("sex", "seks", "seksu", "sexu", "bh", "bra", "kind", "kid", "kids", "minor", "teen", "teens", "loli", "kuse", "fick", "pene", "nago", "nagi", "nagie", "naga", "nagim", "gola", "голий", "гола", "голі", "соски", "menor", "l")):
    parts = [re.escape(t) + (r"\b" if t in exact or len(t) <= 3 else "") for t in terms if t not in ("l",)]
    return re.compile(r"(?<![a-z\u0400-\u04ff])(?:" + "|".join(parts) + ")", re.I)
_RS, _RM, _RR = _rx(_SEX), _rx(_MIN), _rx(_REV)
_EMOJI_SEX = re.compile("[\U0001F346\U0001F351\U0001F4A6\U0001F51E]")   # 🍆 🍑 💦 🔞

MSG = {
 "pl": ("Ten tekst zawiera treści seksualne – u Luny ich nie ma. Spróbuj inaczej. 💚",
        "Tego nie przepuścimy: treści łączące nieletnich i seksualność są zakazane i zgłaszane.",
        "Opis agentki: tylko dorosła (21+), w pełni ubrana, bez skąpych strojów i podtekstów. Opisz styl i charakter. 💚"),
 "en": ("This text contains sexual content – there's none of that at Luna. Please rephrase. 💚",
        "We won't allow this: content combining minors and sexuality is prohibited and reported.",
        "Agent description: adults only (21+), fully clothed, no revealing outfits or innuendo. Describe style and personality. 💚"),
 "es": ("Este texto tiene contenido sexual: en Luna no lo hay. Reformúlalo, por favor. 💚",
        "No lo permitimos: el contenido que mezcla menores y sexualidad está prohibido y se denuncia.",
        "Descripción de la agente: solo adulta (21+), totalmente vestida, sin ropa reveladora ni insinuaciones. Describe estilo y carácter. 💚"),
 "de": ("Dieser Text enthält sexuelle Inhalte – die gibt es bei Luna nicht. Bitte formuliere ihn um. 💚",
        "Das lassen wir nicht zu: Inhalte, die Minderjährige mit Sexualität verbinden, sind verboten und werden gemeldet.",
        "Agentin-Beschreibung: nur erwachsen (21+), vollständig bekleidet, keine knappen Outfits oder Anspielungen. Beschreibe Stil und Charakter. 💚"),
 "uk": ("Цей текст містить сексуальний зміст – у Луни такого немає. Перефразуйте, будь ласка. 💚",
        "Ми цього не пропустимо: поєднання неповнолітніх і сексуальності заборонене й повідомляється.",
        "Опис агентки: лише доросла (21+), повністю вдягнена, без відвертого одягу й натяків. Опишіть стиль і характер. 💚"),
}

class Refused(ValueError):
    def __init__(self, msg, kind, term=""):
        super().__init__(msg); self.kind = kind; self.term = term

def _lang():
    try:
        import nsfw_filter; return getattr(nsfw_filter._tl, "lang", "pl")
    except Exception: return "pl"

def _ages(raw):
    s = _fold(raw)
    return [int(m.group(1)) for m in list(AGE.finditer(s)) + list(AGE2.finditer(s))]

def scan(t, level="text"):
    """(rodzaj, termin) albo (None, ""). rodzaj: sexual | minor_sexual | prompt."""
    words, squash = _norm(t)
    sx = _RS.search(words) or next((x for x in SQUASH if re.search(r"(?<![a-z])" + x, squash)), None) or _EMOJI_SEX.search(str(t or ""))
    mn = _RM.search(words)
    young = any(a < 18 for a in _ages(t))
    if (mn or young) and (sx or (level == "prompt" and _RR.search(words))): return "minor_sexual", (mn.group(0) if mn else "age")
    if sx: return "sexual", sx if isinstance(sx, str) else sx.group(0)
    if level == "prompt":
        r = _RR.search(words)
        if r: return "prompt", r.group(0)
        if mn: return "prompt", mn.group(0)
        if any(a < 21 for a in _ages(t)): return "prompt", "age<21"
        if re.search(r"(?<![a-z])(young[- ]?looking|younger looking|baby[- ]?face|child[- ]?like|petite girl|little girl|mlodo wyglad|dziecinn|wyglada na nastolat)", words): return "prompt", "young-look"
    return None, ""

def _audit(kind, term, ctx):
    try:
        import security; security.audit("text_" + kind, "", f"ctx={str(ctx)[:20]} term={str(term)[:20]}")
    except Exception: pass

def check_text(t, ctx="text", lang=None):
    k, term = scan(t, "text")
    if not k: return t
    m = MSG.get((lang or _lang())[:2], MSG["pl"])
    if k == "minor_sexual": _audit(k, term, ctx); raise Refused(m[1], k, term)
    raise Refused(m[0], k, term)

def check_prompt(t, ctx="gen", lang=None):
    k, term = scan(t, "prompt")
    if not k: return t
    m = MSG.get((lang or _lang())[:2], MSG["pl"])
    _audit(k, term, ctx)
    raise Refused(m[1] if k == "minor_sexual" else m[2], k, term)
