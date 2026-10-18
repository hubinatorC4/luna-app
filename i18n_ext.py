"""Pakiet językowy (v1.7 i18n-pack): ~30 dodatkowych języków na bazie tłumaczenia przez angielski (pivot).

Jak to działa:
 • Źródło prawdy dla tekstów to dalej polskie oryginały + istniejące tłumaczenia EN/ES/DE/UK (i18n/*.json, słowniki w JS i w <script id="i18n">).
 • Dla języka X spoza bazowej piątki serwer składa stronę jak dla „en”, a słownik static/lang/X.json (klucz = angielski tekst, wartość = X)
   podmienia teksty: po stronie serwera (pary pl→X zbudowane z par pl→en) i w przeglądarce (static/i18n-ext.js – napisy tworzone przez JS).
 • Brak tłumaczenia danego napisu → angielski (nigdy pusty klucz).
 • Polska wersja regulaminu i polityki prywatności jest jedyną wiążącą; tłumaczenia prawne to szkic maszynowy z oznaczeniem DRAFT.
Właściciel serwisu występuje wyłącznie jako Hubinator❤️ (bez prawdziwych danych osobowych)."""
import json, os, re
R = os.path.dirname(os.path.abspath(__file__))
BASE = ("pl", "en", "es", "de", "uk")
# kod wewnętrzny: (BCP 47, nazwa natywna, nazwa polska, grupa, kierunek, poziom)
META = {
 "pl": ("pl", "Polski", "polski", "eu-c", "ltr", 0), "en": ("en", "English", "angielski", "eu-w", "ltr", 0),
 "es": ("es", "Español", "hiszpański", "eu-w", "ltr", 0), "de": ("de", "Deutsch", "niemiecki", "eu-w", "ltr", 0),
 "uk": ("uk", "Українська", "ukraiński", "eu-e", "ltr", 0),
 "fr": ("fr", "Français", "francuski", "eu-w", "ltr", 1), "it": ("it", "Italiano", "włoski", "eu-w", "ltr", 1),
 "pt": ("pt-PT", "Português (Portugal)", "portugalski (Portugalia)", "eu-w", "ltr", 2), "pt-br": ("pt-BR", "Português (Brasil)", "portugalski (Brazylia)", "am", "ltr", 1),
 "nl": ("nl", "Nederlands", "niderlandzki", "eu-w", "ltr", 1), "cs": ("cs", "Čeština", "czeski", "eu-c", "ltr", 1),
 "sk": ("sk", "Slovenčina", "słowacki", "eu-c", "ltr", 2), "ro": ("ro", "Română", "rumuński", "eu-c", "ltr", 1),
 "hu": ("hu", "Magyar", "węgierski", "eu-c", "ltr", 2), "sv": ("sv", "Svenska", "szwedzki", "eu-n", "ltr", 2),
 "no": ("nb", "Norsk (bokmål)", "norweski", "eu-n", "ltr", 2), "da": ("da", "Dansk", "duński", "eu-n", "ltr", 2),
 "fi": ("fi", "Suomi", "fiński", "eu-n", "ltr", 2), "el": ("el", "Ελληνικά", "grecki", "eu-s", "ltr", 2),
 "bg": ("bg", "Български", "bułgarski", "eu-s", "ltr", 2), "hr": ("hr", "Hrvatski", "chorwacki", "eu-s", "ltr", 2),
 "sr": ("sr-Cyrl", "Српски", "serbski", "eu-s", "ltr", 2), "lt": ("lt", "Lietuvių", "litewski", "eu-n", "ltr", 2),
 "lv": ("lv", "Latviešu", "łotewski", "eu-n", "ltr", 2), "et": ("et", "Eesti", "estoński", "eu-n", "ltr", 2),
 "tr": ("tr", "Türkçe", "turecki", "me", "ltr", 1), "ru": ("ru", "Русский", "rosyjski", "eu-e", "ltr", 2),
 "ar": ("ar", "العربية", "arabski", "me", "rtl", 1), "he": ("he", "עברית", "hebrajski", "me", "rtl", 2),
 "hi": ("hi", "हिन्दी", "hindi", "as", "ltr", 1), "id": ("id", "Bahasa Indonesia", "indonezyjski", "as", "ltr", 1),
 "vi": ("vi", "Tiếng Việt", "wietnamski", "as", "ltr", 2), "th": ("th", "ไทย", "tajski", "as", "ltr", 2),
 "ja": ("ja", "日本語", "japoński", "as", "ltr", 1), "ko": ("ko", "한국어", "koreański", "as", "ltr", 1),
 "zh": ("zh-Hans", "简体中文", "chiński (uproszczony)", "as", "ltr", 1),
}
EXT = tuple(k for k in META if k not in BASE)
# Rosyjski: wcześniejsza decyzja właściciela – ru/be → angielski. Pakiet ru jest przygotowany, ale włącza go dopiero LUNA_LANG_RU=1.
def enabled():
    off = {x.strip() for x in (os.getenv("LUNA_LANGS_OFF") or "").split(",") if x.strip()}
    if os.getenv("LUNA_LANG_RU") != "1": off.add("ru")
    return tuple(k for k in EXT if k not in off)
ALL = BASE + EXT
OGL = {"fr": "fr_FR", "it": "it_IT", "pt": "pt_PT", "pt-br": "pt_BR", "nl": "nl_NL", "cs": "cs_CZ", "sk": "sk_SK", "ro": "ro_RO", "hu": "hu_HU", "sv": "sv_SE",
       "no": "nb_NO", "da": "da_DK", "fi": "fi_FI", "el": "el_GR", "bg": "bg_BG", "hr": "hr_HR", "sr": "sr_RS", "lt": "lt_LT", "lv": "lv_LV", "et": "et_EE",
       "tr": "tr_TR", "ru": "ru_RU", "ar": "ar_AR", "he": "he_IL", "hi": "hi_IN", "id": "id_ID", "vi": "vi_VN", "th": "th_TH", "ja": "ja_JP", "ko": "ko_KR", "zh": "zh_CN"}

def is_ext(lang): return lang in EXT and lang in enabled()
def norm(code):
    """Dowolny tag (fr-CA, pt_BR, zh-Hans-CN, nb, nn, iw…) → kod wewnętrzny albo ''."""
    c = str(code or "").strip().lower().replace("_", "-")
    if not c: return ""
    if c in ("pt-br",) or c.startswith("pt-br"): return "pt-br" if "pt-br" in enabled() else ""
    if c.startswith("zh"):
        return "zh" if ("zh" in enabled() and not re.search(r"hant|-tw|-hk|-mo", c)) else ""
    p = c.split("-")[0]
    p = {"nb": "no", "nn": "no", "iw": "he", "in": "id"}.get(p, p)
    if p in BASE: return p
    return p if p in EXT and p in enabled() else ""
def bcp(lang): return META.get(lang, (lang,))[0]
def direction(lang): return META.get(lang, ("", "", "", "", "ltr"))[4]

_D = {}
def dic(lang):
    """Słownik EN→X (static/lang/X.json: {"t": {en: x}, "p": [[wzorzec, x]], "meta": {...}})."""
    if lang not in _D:
        try: _D[lang] = json.load(open(os.path.join(R, "static", "lang", lang + ".json"), encoding="utf-8"))
        except (OSError, ValueError): _D[lang] = {"t": {}, "p": []}
        try: _D[lang]["t"].update(json.load(open(os.path.join(R, "i18n", "ext", lang + ".json"), encoding="utf-8")))   # tylko po stronie serwera
        except (OSError, ValueError): pass
    return _D[lang]
def tr(en, lang):
    if not isinstance(en, str) or not en: return en
    T = dic(lang)["t"]
    if en in T: return T[en]
    k = re.sub(r"\s+", " ", en).strip()
    if k in T:
        lead = en[:len(en) - len(en.lstrip())]; trail = en[len(en.rstrip()):]
        return lead + T[k] + trail
    return en
def pairs(en_pairs, lang):
    """[[pl, en], …] → [[pl, X], …] (brak X → en, czyli strona po angielsku zamiast po polsku)."""
    out = []
    for pl, en in en_pairs:
        if en.startswith("~"): out.append([pl, "~" + tr(en[1:], lang)] if pl.startswith("~") else [pl, tr(en[1:], lang)])
        else: out.append([pl, tr(en, lang)])
    return out

# Notka prawna – DRAFT + wiążąca wersja polska (po polsku i w danym języku)
LEGAL = {
 "fr": "Traduction automatique provisoire. Seule la version polonaise est juridiquement contraignante.",
 "it": "Bozza di traduzione automatica. Solo la versione polacca è giuridicamente vincolante.",
 "pt": "Rascunho de tradução automática. Apenas a versão polaca é juridicamente vinculativa.",
 "pt-br": "Rascunho de tradução automática. Somente a versão em polonês tem validade jurídica.",
 "nl": "Concept van een machinevertaling. Alleen de Poolse versie is juridisch bindend.",
 "cs": "Koncept strojového překladu. Právně závazná je pouze polská verze.",
 "sk": "Koncept strojového prekladu. Právne záväzná je iba poľská verzia.",
 "ro": "Ciornă de traducere automată. Doar versiunea în limba polonă este obligatorie din punct de vedere juridic.",
 "hu": "Gépi fordítás tervezete. Jogilag kizárólag a lengyel változat kötelező érvényű.",
 "sv": "Utkast till maskinöversättning. Endast den polska versionen är juridiskt bindande.",
 "no": "Utkast til maskinoversettelse. Bare den polske versjonen er juridisk bindende.",
 "da": "Udkast til maskinoversættelse. Kun den polske version er juridisk bindende.",
 "fi": "Konekäännöksen luonnos. Vain puolankielinen versio on oikeudellisesti sitova.",
 "el": "Πρόχειρη αυτόματη μετάφραση. Νομικά δεσμευτική είναι μόνο η πολωνική έκδοση.",
 "bg": "Чернова на машинен превод. Правно обвързваща е само полската версия.",
 "hr": "Nacrt strojnog prijevoda. Pravno je obvezujuća samo poljska verzija.",
 "sr": "Нацрт машинског превода. Правно обавезујућа је само пољска верзија.",
 "lt": "Mašininio vertimo juodraštis. Teisiškai privaloma tik lenkiška versija.",
 "lv": "Mašīntulkojuma melnraksts. Juridiski saistoša ir tikai poļu valodas versija.",
 "et": "Masintõlke mustand. Õiguslikult siduv on ainult poolakeelne versioon.",
 "tr": "Makine çevirisi taslağıdır. Yalnızca Lehçe sürüm hukuken bağlayıcıdır.",
 "ru": "Черновик машинного перевода. Юридическую силу имеет только польская версия.",
 "ar": "مسودة ترجمة آلية. النسخة البولندية وحدها هي الملزمة قانونيًا.",
 "he": "טיוטת תרגום מכונה. רק הגרסה הפולנית מחייבת מבחינה משפטית.",
 "hi": "मशीनी अनुवाद का मसौदा। केवल पोलिश संस्करण ही कानूनी रूप से बाध्यकारी है।",
 "id": "Draf terjemahan mesin. Hanya versi bahasa Polandia yang mengikat secara hukum.",
 "vi": "Bản nháp dịch máy. Chỉ phiên bản tiếng Ba Lan có giá trị pháp lý ràng buộc.",
 "th": "ร่างคำแปลด้วยเครื่อง มีเพียงฉบับภาษาโปแลนด์เท่านั้นที่มีผลผูกพันทางกฎหมาย",
 "ja": "機械翻訳の下書きです。法的拘束力を持つのはポーランド語版のみです。",
 "ko": "기계 번역 초안입니다. 법적 구속력은 폴란드어 원문에만 있습니다.",
 "zh": "机器翻译草稿。仅波兰语版本具有法律约束力。",
}
def legal_note(doc, path, lang):
    if path not in ("/regulamin.html", "/privacy.html") or not is_ext(lang): return doc
    pl_url = path   # bez ?lang → wersja polska
    note = (f'<p class="hint legalnote legaldraft" role="note"><b>DRAFT – wymaga weryfikacji</b> · 🌐 {LEGAL.get(lang, "")}<br>'
            f'<span lang="pl">Wersja polska jest jedyną wiążącą prawnie.</span> <a href="{pl_url}?lang=pl" lang="pl">Polski (wiążący) →</a></p>')
    return re.sub(r"(</h1>)", r"\1" + note.replace("\\", "\\\\"), doc, count=1)

CSS = '<link rel="stylesheet" href="/i18n-ext.css?v=1">'
_SCRIPT = re.compile(r'(<script\b[^>]*\bsrc="(/?[\w./-]+\.js))(\?[^"]*)?"')
NO_PIVOT = ("langswitch.js", "lg.js", "i18n-ext.js", "sec-client.js")
def _html_attrs(doc, attrs):
    """Atrybuty na <html> (CSP: script-src 'self' – bez skryptów inline, dane dla lg.js / i18n-ext.js idą w data-*)."""
    def f(m):
        a = m.group(1)
        for k in attrs: a = re.sub(r'\s' + re.escape(k) + r'="[^"]*"', "", a)
        return "<html" + a + "".join(f' {k}="{v}"' for k, v in attrs.items()) + ">"
    return re.sub(r"<html\b([^>]*)>", f, doc, count=1)
def finish(doc, path, lang):
    """Ostatni krok: lista języków dla lg.js; dla języków pakietu lang/dir, skrypty z ?lang=X (baza „en”), i18n-ext.js i czcionki."""
    langs = ",".join(BASE + enabled())
    if not is_ext(lang):
        doc = _html_attrs(doc, {"data-luna-langs": langs})
        return doc.replace("</head>", CSS + "\n</head>", 1) if "i18n-ext.css" not in doc else doc
    doc = _html_attrs(doc, {"lang": bcp(lang), "dir": direction(lang), "data-luna-base": "en", "data-luna-lang": lang, "data-luna-langs": langs})
    def sc(m):
        name = os.path.basename(m.group(2))
        if name in NO_PIVOT: return m.group(0)
        q = re.sub(r"([?&])lang=[\w-]+", r"\1", m.group(3) or "").rstrip("&?")
        return m.group(1) + (q + "&" if q else "?") + "lang=" + lang + '"'
    doc = _SCRIPT.sub(sc, doc)
    return doc.replace("</head>", CSS + '<script src="/i18n-ext.js?v=1"></script>\n</head>', 1)

# Przepisanie skryptu JS na bazę „en” (stare słowniki mają tylko pl/en/es/de/uk) – tłumaczenie na X robi i18n-ext.js w przeglądarce.
_PIV = [
 (re.compile(r"document\.documentElement\.lang\b"), "document.documentElement.dataset.lunaBase"),
 (re.compile(r"document\.documentElement\.getAttribute\(\s*['\"]lang['\"]\s*\)"), "document.documentElement.dataset.lunaBase"),
 (re.compile(r"localStorage\.getItem\(\s*['\"]luna\.lang['\"]\s*\)"), "'en'"),
 (re.compile(r"\.get\(\s*['\"]lang['\"]\s*\)"), r"\g<0>&&'en'"),
 (re.compile(r"navigator\.languages\b"), "['en']"),
 (re.compile(r"navigator\.language\b"), "'en'"),
]
def pivot_js(name, src):
    if name in NO_PIVOT: return src
    for rx, rep in _PIV: src = rx.sub(rep, src)
    return src
