# -*- coding: utf-8 -*-
"""Składa pakiet językowy: cache tłumaczeń maszynowych (tools/i18n_pack/cache/*.json albo /workspace/i18n_work/cache) + glosariusz
→ static/lang/<kod>.json (przeglądarka) i i18n/ext/<kod>.json (tylko serwer) + i18n/catalog/coverage.json.
Kontrola jakości: zgubione placeholdery / znaczniki HTML, śmieci MT (obce pismo, powtórzenia), brak prawdziwego imienia właściciela.
Napis z błędem → zostaje angielski (bezpieczniej niż zepsute zdanie)."""
import json, os, re, sys, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, R)
import glossary, i18n_ext
CACHE = os.getenv("I18N_CACHE", "/workspace/i18n_work/cache")
SRC = json.load(open(os.path.join(R, "i18n", "catalog", "source_en.json"), encoding="utf-8"))
LEG = ("json:privacy", "json:regulamin", "html:regulamin", "html:privacy", "py:tools/build_legal", "py:tools/build_battle_rules", "html:zasady")
CODE = re.compile(r"[{;]\s*[a-z-]+\s*:\s*[^\s]|=>|function\s*\(|\bvar\b|document\.|querySelector|^\.[a-z]")
PH = re.compile(r"\{[\w.]*\}|\$\{[^}]*\}|%[sd]")
JUNK = re.compile(r"^\s*\[\s*['\"]|^\s*`|\$\{[^}]*[^\w.}][^}]*\}")   # fragmenty kodu JS złapane przez ekstraktor
FORBIDDEN = re.compile(r"Szumsk|Hubert\b", re.I)
NSFW = re.compile(r"勃起|性交|セックス|ポルノ|裸|乳首|陰茎|膣|섹스|포르노|성기|알몸|色情|阴茎|阴道|裸体|порн|секс\b|голая|пенис|эрекц|πορν|σεξ|पोर्न|सेक्स|ล่อนจ้อน|เซ็กส์|โป๊|إباح|جنس|קס\b|פורנו|\bporn|\bsex[eo]?\b|\bnud[eoi]|\bnaken|\bnackt|\berek|\berecc|\bpenis|\bvagin|\bpornô|\bseks\b|\bsexo\b", re.I)   # prawdziwe dane właściciela – nigdy w tłumaczeniach
NONLATIN = {"el", "bg", "sr", "ru", "ar", "he", "hi", "th", "ja", "ko", "zh", "uk"}
SCRIPT = {"el": r"[\u0370-\u03ff]", "bg": r"[\u0400-\u04ff]", "sr": r"[\u0400-\u04ff]", "ru": r"[\u0400-\u04ff]", "ar": r"[\u0600-\u06ff]", "he": r"[\u0590-\u05ff]",
          "hi": r"[\u0900-\u097f]", "th": r"[\u0e00-\u0e7f]", "ja": r"[\u3040-\u30ff\u4e00-\u9fff]", "ko": r"[\uac00-\ud7af]", "zh": r"[\u4e00-\u9fff]"}
BRAND = re.compile(r"Luna Live|Luna|Hubinator❤️|BLIK|Stripe|Premium|Pro|Ultra|PRO|AI|IA|KI|TikTok|Instagram|YouTube|Android|WebP|AVIF|VAT|PLN|zł|OK|QR|ID|Miss|Bitwy|Butik|e-?mail|https?://\S+", re.I)
PT_PT = [(r"\busuári(a|o)s?\b", lambda m: "utilizador" + ("a" if m.group(1) == "a" else "") + ("es" if m.group(0).endswith("s") and m.group(1) == "o" else "s" if m.group(0).endswith("s") else "")),
         (r"\btela\b", "ecrã"), (r"\btelas\b", "ecrãs"), (r"\bcelular(es)?\b", "telemóvel"), (r"\barquivo\b", "ficheiro"), (r"\barquivos\b", "ficheiros"),
         (r"\bequipe\b", "equipa"), (r"\baplicativo\b", "aplicação"), (r"\bcontato\b", "contacto"), (r"\bcontatos\b", "contactos"), (r"\bregistro\b", "registo"),
         (r"\bsenha\b", "palavra-passe"), (r"\bsenhas\b", "palavras-passe"), (r"\bcâmera\b", "câmara"), (r"\bgerenciar\b", "gerir"), (r"\bsalvar\b", "guardar"),
         (r"\bexcluir\b", "eliminar"), (r"\bcompartilhar\b", "partilhar"), (r"\bcompartilhe\b", "partilhe"), (r"\bbaixar\b", "descarregar"), (r"\bcadastr", "regist"),
         (r"\bOriente Médio\b", "Médio Oriente"), (r"\bestá (\w+?)ndo\b", r"está a \1r"), (r"\bestou (\w+?)ndo\b", r"estou a \1r"), (r"\bestamos (\w+?)ndo\b", r"estamos a \1r")]
def pt_pt(x):
    for a, b in PT_PT: x = re.sub(a, b, x)
    return x
import unicodedata
ALLOWED = {"el": {"GREEK", "LATIN"}, "bg": {"CYRILLIC", "LATIN"}, "sr": {"CYRILLIC", "LATIN"}, "ru": {"CYRILLIC", "LATIN"}, "uk": {"CYRILLIC", "LATIN"},
           "ar": {"ARABIC", "LATIN"}, "he": {"HEBREW", "LATIN"}, "hi": {"DEVANAGARI", "LATIN"}, "th": {"THAI", "LATIN"},
           "ja": {"CJK", "HIRAGANA", "KATAKANA", "LATIN", "FULLWIDTH", "HALFWIDTH"}, "ko": {"HANGUL", "LATIN", "CJK", "FULLWIDTH"}, "zh": {"CJK", "LATIN", "FULLWIDTH"}}
def _scripts(x):
    out = set()
    for ch in x:
        if ch.isalpha():
            try: out.add(unicodedata.name(ch).split()[0])
            except ValueError: out.add("?")
    return out
def norm(s): return re.sub(r"\s+", " ", s).strip()
def check(en, x, lang):
    """Zwraca powód odrzucenia albo ''."""
    if not x or not x.strip(): return "pusty"
    if FORBIDDEN.search(x): return "dane-osobowe"
    if NSFW.search(x) and not NSFW.search(en): return "nsfw-śmieci"
    if sorted(PH.findall(en)) != sorted(PH.findall(x)): return "placeholder"
    if en.count("<") != x.count("<") or sorted(re.findall(r"</?(\w+)", en)) != sorted(re.findall(r"</?(\w+)", x)): return "html"
    if re.search(r"(\b\w+\b)(?:\W+\1\b){3,}", x) and not re.search(r"(\b\w+\b)(?:\W+\1\b){3,}", en): return "powtórzenia"
    core = BRAND.sub("", re.sub(r"<[^>]+>|&\w+;", "", x))
    if lang in SCRIPT and len(re.findall(r"[A-Za-z]", core)) > 12:
        lat = len(re.findall(r"[A-Za-z]", core)); nat = len(re.findall(SCRIPT[lang], core))
        if lat > nat * (1.2 if lang in ("ja", "zh") else 0.7): return "obce-pismo"
    if set(_scripts(x)) - set(_scripts(en)) - ALLOWED.get(lang, {"LATIN"}): return "obce-pismo"
    le, lx = len(norm(en)), len(norm(x))
    if le > 25 and (lx < le * (0.18 if lang in ("ja", "zh", "ko") else 0.35) or lx > le * 3.2): return "długość"
    return ""
def placeholders_to_pos(en, x):
    order = []
    for p in PH.findall(en):
        if p not in order: order.append(p)
    k, v = en, x
    for i, p in enumerate(order): k = k.replace(p, "{%d}" % i); v = v.replace(p, "{%d}" % i)
    return norm(k), norm(v)
def build(lang):
    src_lang = "pt-br" if lang == "pt" else lang
    f = os.path.join(CACHE, src_lang + ".json")
    C = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    G = dict(zip(glossary.K, glossary.G.get(lang, [])))
    client, server, pats = {}, {}, []
    st = collections.Counter(); bad = collections.Counter(); bad_ex = []
    leg_tot = leg_ok = 0
    for row in SRC:
        en = row["en"]
        if CODE.search(en) or JUNK.search(en): continue
        legal = all(o.startswith(LEG) for o in row["o"])
        en_q = en.replace("Hubert Szumski", "Hubinator❤️")
        x = G.get(en)
        src = "glosariusz" if x else "mt"
        if x is None:
            x = C.get(en_q)
            if x is not None and lang == "pt": x = pt_pt(x)
        st["all"] += 1; leg_tot += legal; st["ui_all"] += (not legal)
        if x is None: st["brak"] += 1; continue
        why = "" if src == "glosariusz" else check(en_q, x, lang)
        if why:
            bad[why] += 1
            if len(bad_ex) < 40: bad_ex.append([en[:120], x[:120], why])
            continue
        if norm(x) == norm(en) and re.search(r"[a-z]{3}", BRAND.sub("", en)): st["identyczne"] += 1
        st["ok"] += 1; st[src] += 1; leg_ok += legal; st["ui_ok"] += (not legal)
        x = x.replace("Hubinator❤️", "Hubinator❤️")
        page_only = all(o.startswith("json:") and not o.startswith("json:js_") for o in row["o"])
        tgt = server if (page_only or legal) else client
        tgt[norm(en)] = x if norm(en) == en else x.strip()
        if en != norm(en): server[en] = x
        if PH.search(en):
            k, v = placeholders_to_pos(en_q, x)
            pats.append([k, v])
    H = {k: v for k, v in client.items() if "<" in k}
    os.makedirs(os.path.join(R, "static", "lang"), exist_ok=True); os.makedirs(os.path.join(R, "i18n", "ext"), exist_ok=True)
    meta = {"lang": lang, "bcp": i18n_ext.bcp(lang), "dir": i18n_ext.direction(lang), "source": "MADLAD-400 3B (MT, lokalnie) + glosariusz ręczny", "status": "beta",
            "review": "glosariusz: ręcznie; reszta: szkic maszynowy – wymaga przeglądu native speakera"}
    json.dump({"meta": meta, "t": client, "h": H, "p": pats}, open(os.path.join(R, "static", "lang", lang + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump(server, open(os.path.join(R, "i18n", "ext", lang + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    cov = {"lang": lang, "name": i18n_ext.META[lang][1], "tier": i18n_ext.META[lang][5], "keys": st["all"], "ok": st["ok"], "pct": round(100 * st["ok"] / max(1, st["all"]), 1),
           "ui_keys": st["ui_all"], "ui_ok": st["ui_ok"], "ui_pct": round(100 * st["ui_ok"] / max(1, st["ui_all"]), 1), "legal_pct": round(100 * leg_ok / max(1, leg_tot), 1), "legal_policy": "EN (legal docs only in 5 reviewed languages)", "glossary": st["glosariusz"], "mt": st["mt"], "missing": st["brak"], "same_as_en": st["identyczne"],
           "rejected": dict(bad), "rejected_examples": bad_ex[:12], "phases": C.get("__phase__", [])}
    return cov
if __name__ == "__main__":
    langs = sys.argv[1:] or list(i18n_ext.EXT)
    out_p = os.path.join(R, "i18n", "catalog", "coverage.json")
    allc = json.load(open(out_p)) if os.path.exists(out_p) else {}
    for l in langs:
        c = build(l); allc[l] = c
        print(f"{l:6} UI {c['ui_pct']:5}% ({c['ui_ok']}/{c['ui_keys']})  all {c['pct']:5}%  ok={c['ok']}/{c['keys']} legal={c['legal_pct']}% rej={c['rejected']} brak={c['missing']}")
    json.dump(allc, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
