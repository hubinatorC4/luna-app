"""QA pakietu językowego: render kluczowych stron w każdym języku (lokalny serwer), zrzuty, przepełnienie, brakujące klucze, RTL.
Użycie: python3 tools/i18n_pack/qa_shots.py http://127.0.0.1:8853 fr it ar …"""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1]; LANGS = sys.argv[2:]
OUT = "/workspace/shots/final_1910/jezyki"; os.makedirs(OUT, exist_ok=True)
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EN = {x["en"].strip() for x in json.load(open(os.path.join(R, "i18n/catalog/source_en.json")))}
PAGES = [("home", "/"), ("app", "/app"), ("bitwy", "/bitwy.html"), ("butik", "/butik.html"), ("regulamin", "/regulamin.html"), ("privacy", "/privacy.html"), ("testerzy", "/testerzy.html"), ("ustawienia", "/ustawienia.html")]
INIT = """try{localStorage.setItem('luna.age',JSON.stringify({adult:true,at:1760000000}));localStorage.setItem('luna.age18',JSON.stringify({yes:true,at:Date.now()}));
document.cookie='luna_age18=1; path=/';localStorage.setItem('luna.app.onb','1');localStorage.setItem('luna.seenVer','9.9.9');localStorage.setItem('luna.payNotice','1');}catch(e){}"""
PROBE = r"""(EN) => {
 const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
 const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n, pl = [], en = [], tot = 0;
 const ENS = new Set(EN);
 while ((n = tw.nextNode())){ const t = n.nodeValue.replace(/\s+/g, ' ').trim(); if (!t || !/\p{L}{2}/u.test(t) || !n.parentElement || !vis(n.parentElement) || n.parentElement.closest('script,style,.lpick,.lswitch,[lang=pl]')) continue;
   tot++; if (/[ąćęłńśźżĄĆĘŁŃŚŹŻ]/.test(t)) pl.push(t.slice(0, 60)); else if (ENS.has(t) && /[a-z]{3}/.test(t)) en.push(t.slice(0, 60)); }
 const over = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return vis(e) && r.width > 0 && (r.right > innerWidth + 2 || r.left < -2) && getComputedStyle(e).position !== 'fixed'; }).slice(0, 6).map(e => e.tagName + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : '') + ':' + (e.innerText || '').slice(0, 30));
 return {lang: document.documentElement.lang, dir: document.documentElement.dir, scrollW: document.documentElement.scrollWidth, w: innerWidth, tot, pl: pl.slice(0, 8), npl: pl.length, en: en.slice(0, 8), nen: en.length, over, title: document.title};
}"""
res = {}
with sync_playwright() as p:
    br = p.chromium.launch()
    for lang in LANGS:
        for vp, size in (("mobile", {"width": 390, "height": 844}),):
            ctx = br.new_context(viewport=size, device_scale_factor=2, is_mobile=True, has_touch=True, locale={"pt-br": "pt-BR", "zh": "zh-CN"}.get(lang, lang))
            ctx.add_init_script(INIT); pg = ctx.new_page()
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            for name, path in PAGES:
                try:
                    pg.goto(B + path + ("&" if "?" in path else "?") + "lang=" + lang, wait_until="networkidle", timeout=30000)
                except Exception as e:
                    errs.append("goto " + str(e)[:80])
                time.sleep(1.2)
                r = pg.evaluate(PROBE, list(EN))
                r["errors"] = errs[:]; errs.clear()
                f = f"{OUT}/{lang}_{name}_{vp}.png"; pg.screenshot(path=f, full_page=False)
                res[f"{lang}/{name}"] = r
                if name == "home":   # wybór języka z etykietą beta
                    try:
                        pg.click(".lpick-btn", timeout=4000); time.sleep(0.6); pg.screenshot(path=f"{OUT}/{lang}_picker_{vp}.png"); pg.keyboard.press("Escape")
                    except Exception as e: errs.append("picker " + str(e)[:60])
                print(lang, name, r["lang"], r["dir"], "tot", r["tot"], "pl", r["npl"], "en", r["nen"], "overflow", r["scrollW"] > r["w"] + 2, r["over"][:2], r["errors"][:2], flush=True)
            ctx.close()
    br.close()
p = os.path.join(OUT, "qa.json"); old = json.load(open(p)) if os.path.exists(p) else {}; old.update(res)
json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)
