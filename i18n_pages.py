"""Tłumaczenie stron publicznych po stronie serwera (indeksowalne): i18n/<plik>.json = {lang: [[pl, tłumaczenie], ...]}.
Wpis z „<” – zamiana fragmentu HTML; wpis z „~” – zamiana podciągu; pozostałe – cały węzeł tekstowy lub wartość atrybutu.
Pliki JS z listy JS dostają ?lang=xx i podmianę napisów (strony publiczne i aplikacja /app)."""
import json, os, re
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")
PAGES = {"/promo.html": ["promo", "common"], "/live.html": ["live", "common"], "/regulamin.html": ["app_fix", "regulamin_bitwy", "regulamin_v143", "regulamin_v140", "regulamin", "common"],
         "/privacy.html": ["privacy_inbox", "privacy_v140", "privacy", "common", "app_fix"], "/o-lunie.html": ["app_fix", "olunie", "common"], "/galeria.html": ["common"], "/bitwy.html": ["common"], "/ranking.html": ["common"],
         "/index.html": ["app_index"],
         **{x: ["common"] for x in ("/scianka.html", "/butik.html", "/testerzy.html", "/dolacz.html", "/twarz.html", "/wesprzyj.html", "/problemy.html", "/agentka.html", "/agentki.html", "/skrzynka.html", "/znajomi.html", "/ustawienia.html")}}
PAGES.update({"/zaufanie.html": ["common"], "/zgloszenie.html": ["common"], "/zespol.html": ["common"]})
for _k in PAGES: PAGES[_k] = ["trust"] + PAGES[_k]   # link „Bezpieczeństwo i anonimowość” w stopce i karta na stronie/w aplikacji
PAGES["/regulamin.html"] = ["regulamin_v170"] + PAGES["/regulamin.html"]; PAGES["/privacy.html"] = ["privacy_v170"] + PAGES["/privacy.html"]
JS = {"portal.js": ["js_portal", "js_fix"], "legal.js": "js_fix", "live.js": "js_live", "testers.js": "js_testers", "push.js": "js_push",
      "app.js": "js_app", "account.js": ["js_account", "js_age"], "custom.js": "js_custom", "livechat.js": "js_livechat", "profile.js": "js_profile"}
JS_ON = ("/promo.html", "/live.html", "/index.html", "/testerzy.html", "/regulamin.html")
_c = {}
def _load(n):
    if n not in _c:
        try: _c[n] = json.load(open(os.path.join(D, n + ".json"), encoding="utf-8"))
        except (OSError, ValueError): _c[n] = {}
    return _c[n]
def _rules(names, lang):
    key = (tuple(names), lang)
    if key in _c: return _c[key]
    pairs = []
    for n in names: pairs += _load(n).get(lang, [])
    pairs.sort(key=lambda p: -len(p[0]))
    out = []
    for pl, tr in pairs:
        if pl == tr: continue
        if pl.startswith("~"): out.append(("raw", pl[1:], tr)); continue
        pat = r"\s+".join(re.escape(x) for x in pl.split())
        if "<" in pl: out.append(("html", re.compile(pat), tr))
        else: out.append(("text", re.compile(r"(>\s*)" + pat + r"(\s*<)"), re.compile(r'(\b(?:placeholder|aria-label|title|alt)=")' + pat + '"'), tr))
    _c[key] = out; return out
def apply(doc, path, lang):
    names = PAGES.get(path)
    if not lang or lang == "pl": return doc
    b = doc.find("<body")
    if names and b >= 0:
        head, body = doc[:b], doc[b:]
        for r in _rules(names, lang):
            if r[0] == "raw": body = body.replace(r[1], r[2])
            elif r[0] == "html": body = r[1].sub(lambda m, t=r[2]: t, body)
            else:
                body = r[1].sub(lambda m, t=r[3]: m.group(1) + t + m.group(2), body)
                body = r[2].sub(lambda m, t=r[3]: m.group(1) + t.replace('"', "&quot;") + '"', body)
        doc = head + body
    if path in JS_ON:
        doc = re.sub(r'(<script src="/?(' + "|".join(re.escape(k) for k in JS) + r')(\?[^"]*)?)"', lambda m: m.group(1) + ("&" if m.group(3) else "?") + "lang=" + lang + '"', doc)
    return doc
def js(name, src, lang):
    n = JS.get(name)
    if not n or not lang or lang == "pl": return src
    pairs = [x for k in (n if isinstance(n, list) else [n]) for x in _load(k).get(lang, [])]
    for pl, tr in sorted(pairs, key=lambda p: -len(p[0])): src = src.replace(pl, tr)
    return src
LEGAL_NOTE = {"en": "This translation is provided for convenience. The Polish version is legally binding.",
              "es": "Esta traducción se ofrece por comodidad. La versión polaca es la jurídicamente vinculante.",
              "de": "Diese Übersetzung dient der Orientierung. Rechtlich verbindlich ist die polnische Fassung.",
              "uk": "Цей переклад надано для зручності. Юридичну силу має польська версія."}
def legal_note(doc, path, lang):
    if path in ("/regulamin.html", "/privacy.html") and lang in LEGAL_NOTE:
        doc = re.sub(r"(</h1>)", r'\1<p class="hint legalnote">🌐 ' + LEGAL_NOTE[lang] + "</p>", doc, count=1)
    return doc
def library(lib, lang):
    """Biblioteka porad w danym języku (tłumaczenia z i18n/library.json); brak tłumaczenia = oryginał."""
    T = _load("library").get(lang) if lang and lang != "pl" else None
    if not T: return lib
    lv = {k: T["levels"].get(v, v) for k, v in lib["levels"].items()}
    cats = [dict(c, name=T["cats"].get(c["name"], (c["name"], c["desc"]))[0], desc=T["cats"].get(c["name"], (c["name"], c["desc"]))[1]) for c in lib["cats"]]
    items = []
    for it in lib["items"]:
        t = T["items"].get(it["id"])
        it = dict(it, level_name=lv.get(it["level"], it["level_name"]))
        if t: it.update(title=t[0], text=t[1])
        items.append(it)
    return {"cats": cats, "levels": lv, "items": items}
