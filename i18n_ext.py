"""Pakiet językowy (v1.7 i18n-pack): ~30 dodatkowych języków na bazie tłumaczenia przez angielski (pivot).

Jak to działa:
 • Źródło prawdy dla tekstów to dalej polskie oryginały + istniejące tłumaczenia EN/ES/DE/UK (i18n/*.json, słowniki w JS i w <script id="i18n">).
 • Dla języka X spoza bazowej piątki serwer składa stronę jak dla „en”, a słownik static/lang/X.json (klucz = angielski tekst, wartość = X)
   podmienia teksty: po stronie serwera (pary pl→X zbudowane z par pl→en) i w przeglądarce (static/i18n-ext.js – napisy tworzone przez JS).
 • Brak tłumaczenia danego napisu → angielski (nigdy pusty klucz).
 • Regulamin, polityka prywatności i zasady bitew: tylko 5 przejrzanych języków; w językach pakietu wersja angielska + notka (wiążąca wersja PL, EN referencyjna).
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

# Dokumenty prawne (regulamin, polityka prywatności, zasady bitew) są tylko w 5 przejrzanych językach (pl/en/es/de/uk).
# W językach pakietu strona jest renderowana po angielsku (bez tłumaczenia maszynowego – <main lang="en" data-no-i18n>),
# a nad treścią stoi krótka notka w języku użytkownika: brak wersji w tym języku, wiążąca jest wersja polska (PL), angielska (EN) – referencyjna.
LEGAL_PATHS = ("/regulamin.html", "/privacy.html", "/zasady-bitew.html")
LEGAL = {
 "fr": "Non disponible dans votre langue – affiché en anglais. Seule la version polonaise (PL) fait foi ; l’anglais (EN) sert de référence.",
 "it": "Non disponibile nella tua lingua – mostrato in inglese. Fa fede solo la versione polacca (PL); l’inglese (EN) è di riferimento.",
 "pt": "Não disponível no seu idioma – apresentado em inglês. Apenas a versão polaca (PL) é juridicamente vinculativa; o inglês (EN) serve de referência.",
 "pt-br": "Não disponível no seu idioma – exibido em inglês. Somente a versão em polonês (PL) tem validade jurídica; o inglês (EN) serve de referência.",
 "nl": "Niet beschikbaar in jouw taal – getoond in het Engels. Alleen de Poolse versie (PL) is juridisch bindend; het Engels (EN) dient als referentie.",
 "cs": "Není k dispozici ve vašem jazyce – zobrazeno v angličtině. Právně závazná je pouze polská verze (PL); angličtina (EN) slouží pro orientaci.",
 "sk": "Nie je dostupné vo vašom jazyku – zobrazené v angličtine. Právne záväzná je iba poľská verzia (PL); angličtina (EN) slúži na orientáciu.",
 "ro": "Indisponibil în limba ta – afișat în engleză. Doar versiunea în polonă (PL) are forță juridică; engleza (EN) este de referință.",
 "hu": "Az Ön nyelvén nem érhető el – angolul jelenik meg. Jogilag csak a lengyel változat (PL) kötelező; az angol (EN) tájékoztató jellegű.",
 "sv": "Inte tillgängligt på ditt språk – visas på engelska. Endast den polska versionen (PL) är juridiskt bindande; engelska (EN) är en referens.",
 "no": "Ikke tilgjengelig på ditt språk – vises på engelsk. Bare den polske versjonen (PL) er juridisk bindende; engelsk (EN) er til referanse.",
 "da": "Ikke tilgængelig på dit sprog – vises på engelsk. Kun den polske version (PL) er juridisk bindende; engelsk (EN) er til reference.",
 "fi": "Ei saatavilla kielelläsi – näytetään englanniksi. Vain puolankielinen versio (PL) on oikeudellisesti sitova; englanninkielinen (EN) on viitteellinen.",
 "el": "Δεν είναι διαθέσιμο στη γλώσσα σας – εμφανίζεται στα αγγλικά. Νομικά δεσμευτική είναι μόνο η πολωνική έκδοση (PL)· η αγγλική (EN) είναι για αναφορά.",
 "bg": "Не е налично на вашия език – показва се на английски. Правно обвързваща е само полската версия (PL); английската (EN) е за справка.",
 "hr": "Nije dostupno na vašem jeziku – prikazano na engleskom. Pravno je obvezujuća samo poljska verzija (PL); engleska (EN) služi kao referenca.",
 "sr": "Није доступно на вашем језику – приказано на енглеском. Правно обавезујућа је само пољска верзија (PL); енглеска (EN) служи као референца.",
 "lt": "Jūsų kalba neprieinama – rodoma anglų kalba. Teisiškai privaloma tik lenkiška versija (PL); angliška (EN) – informacinė.",
 "lv": "Nav pieejams jūsu valodā – parādīts angļu valodā. Juridiski saistoša ir tikai poļu versija (PL); angļu (EN) ir atsaucei.",
 "et": "Teie keeles pole saadaval – kuvatakse inglise keeles. Õiguslikult siduv on ainult poolakeelne versioon (PL); ingliskeelne (EN) on teadmiseks.",
 "tr": "Dilinizde mevcut değil – İngilizce gösteriliyor. Yalnızca Lehçe sürüm (PL) hukuken bağlayıcıdır; İngilizce (EN) bilgi amaçlıdır.",
 "ru": "Недоступно на вашем языке – показано на английском. Юридическую силу имеет только польская версия (PL); английская (EN) – справочная.",
 "ar": "غير متوفر بلغتك – معروض بالإنجليزية. النسخة البولندية (PL) وحدها الملزمة قانونيًا؛ والإنجليزية (EN) للاطلاع فقط.",
 "he": "לא זמין בשפה שלך – מוצג באנגלית. רק הגרסה הפולנית (PL) מחייבת מבחינה משפטית; האנגלית (EN) לעיון בלבד.",
 "hi": "आपकी भाषा में उपलब्ध नहीं है – अंग्रेज़ी में दिखाया गया है। केवल पोलिश संस्करण (PL) कानूनी रूप से बाध्यकारी है; अंग्रेज़ी (EN) केवल संदर्भ के लिए है।",
 "id": "Tidak tersedia dalam bahasa Anda – ditampilkan dalam bahasa Inggris. Hanya versi bahasa Polandia (PL) yang mengikat secara hukum; bahasa Inggris (EN) sebagai referensi.",
 "vi": "Chưa có bằng ngôn ngữ của bạn – hiển thị bằng tiếng Anh. Chỉ bản tiếng Ba Lan (PL) có giá trị pháp lý; bản tiếng Anh (EN) để tham khảo.",
 "th": "ยังไม่มีในภาษาของคุณ – แสดงเป็นภาษาอังกฤษ ฉบับภาษาโปแลนด์ (PL) เท่านั้นที่มีผลผูกพันทางกฎหมาย ส่วนภาษาอังกฤษ (EN) ใช้เพื่ออ้างอิง",
 "ja": "お使いの言語では提供されていないため、英語で表示しています。法的拘束力を持つのはポーランド語版（PL）のみで、英語版（EN）は参考訳です。",
 "ko": "사용 중인 언어로는 제공되지 않아 영어로 표시됩니다. 법적 구속력은 폴란드어판(PL)에만 있으며, 영어판(EN)은 참고용입니다.",
 "zh": "暂无您所用语言的版本，现以英文显示。仅波兰语版本（PL）具有法律约束力，英文版本（EN）仅供参考。",
}
def legal_render_lang(path, lang):
    """Język treści dokumentu prawnego: języki pakietu → „en” (przejrzana wersja), bazowa piątka bez zmian."""
    return "en" if is_ext(lang) and path in LEGAL_PATHS else lang
def legal_note(doc, path, lang):
    if path not in LEGAL_PATHS or not is_ext(lang): return doc
    note = (f'<p class="hint legalnote legalen" role="note" lang="{bcp(lang)}" dir="{direction(lang)}" data-no-i18n>🌐 {LEGAL.get(lang, "")} '
            f'<a href="{path}?lang=pl" lang="pl" hreflang="pl">Polski (PL) →</a> · <a href="{path}?lang=en" lang="en" hreflang="en">English (EN) →</a></p>')
    doc = re.sub(r"<main\b([^>]*)>", lambda m: "<main" + m.group(1) + ' lang="en" dir="ltr" data-no-i18n>', doc, count=1) if "<main" in doc else \
          re.sub(r"(<h1\b)", r'<div lang="en" dir="ltr" data-no-i18n>\1', doc, count=1).replace("</body>", "</div></body>", 1)
    return re.sub(r"(</h1>)", lambda m: m.group(1) + note, doc, count=1)

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
