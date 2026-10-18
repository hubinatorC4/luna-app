# -*- coding: utf-8 -*-
"""Uczciwa promocja (E3): obrazki do udostępniania (OG 1200×630) agentek i bitew, metadane OG dla linków
z bitew/rankingu/profili oraz krótkie linki (/casting, /zapros). Tylko prawdziwe dane: imiona agentek AI, prawdziwe
wyniki zakończonych bitew. Nigdy dane właściciela ani prawdziwych osób. Bez sztucznych liczników."""
import base64, html, io, os, re, threading, time
from collections import OrderedDict
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
FONT = os.path.join(ROOT, "ogfonts", "Nunito-VariableFont_wght.ttf")
W, H = 1200, 630
BG = (11, 7, 5); CREAM = (245, 240, 232); GREEN = (61, 220, 132); PINK = (255, 105, 180); ORANGE = (255, 159, 67); MUTED = (190, 178, 168)
HOST = "luna-voice-coach.onrender.com"

T = {
 "pl": {"vote": "Głosuj na moją agentkę!", "battle": "Bitwa agentek AI", "live": "Trwa głosowanie", "result": "Wynik bitwy", "winner": "Zwycięża", "draw": "Remis",
        "ai": "Agentka AI", "rules": "1 konto = 1 głos · tylko prawdziwe głosy", "pts": "pkt", "wins": "wygrane", "profile": "Profil agentki AI",
        "cta_a": "Zobacz profil i zagłosuj", "luna": "Luna – trenerka głosu AI", "rank": "Ranking bitew"},
 "en": {"vote": "Vote for my agent!", "battle": "AI agent battle", "live": "Voting is open", "result": "Battle result", "winner": "Winner", "draw": "Draw",
        "ai": "AI agent", "rules": "1 account = 1 vote · real votes only", "pts": "pts", "wins": "wins", "profile": "AI agent profile",
        "cta_a": "See the profile and vote", "luna": "Luna – AI voice coach", "rank": "Battle ranking"},
 "es": {"vote": "¡Vota por mi agente!", "battle": "Batalla de agentes IA", "live": "Votación abierta", "result": "Resultado", "winner": "Gana", "draw": "Empate",
        "ai": "Agente IA", "rules": "1 cuenta = 1 voto · solo votos reales", "pts": "pts", "wins": "victorias", "profile": "Perfil de agente IA",
        "cta_a": "Mira el perfil y vota", "luna": "Luna – entrenadora de voz IA", "rank": "Ranking de batallas"},
 "de": {"vote": "Stimm für meine Agentin!", "battle": "KI-Agentinnen-Battle", "live": "Abstimmung läuft", "result": "Ergebnis", "winner": "Siegerin", "draw": "Unentschieden",
        "ai": "KI-Agentin", "rules": "1 Konto = 1 Stimme · nur echte Stimmen", "pts": "Pkt.", "wins": "Siege", "profile": "Profil der KI-Agentin",
        "cta_a": "Profil ansehen und abstimmen", "luna": "Luna – KI-Stimmtrainerin", "rank": "Battle-Ranking"},
 "uk": {"vote": "Голосуй за мою агентку!", "battle": "Битва ШІ-агенток", "live": "Голосування триває", "result": "Результат битви", "winner": "Перемагає", "draw": "Нічия",
        "ai": "ШІ-агентка", "rules": "1 акаунт = 1 голос · лише справжні голоси", "pts": "балів", "wins": "перемог", "profile": "Профіль ШІ-агентки",
        "cta_a": "Переглянь профіль і проголосуй", "luna": "Луна – ШІ-тренерка голосу", "rank": "Рейтинг битв"},
}
def _t(lang): return T.get(lang if lang in T else "pl")

# ---------- źródła obrazów (tylko publiczne) ----------
def _load_src(src):
    """Bajty obrazu z publicznego adresu strony: plik statyczny, zdjęcie profilu lub zatwierdzona agentka z Bitew."""
    try:
        src = str(src or "")
        if src.startswith("data:image/"):
            return base64.b64decode(src.split(",", 1)[1])
        path = src.split("?", 1)[0]
        m = re.fullmatch(r"/api/agent/profile/img/([0-9a-f]{10})\.jpg", path)
        if m:
            import profiles
            i = profiles.own_img(m.group(1)); return base64.b64decode(i["b"]) if i else None
        m = re.fullmatch(r"/api/battles/img/([0-9a-f]{10})", path)
        if m:
            import battles
            d = battles.entry_img(m.group(1)); return base64.b64decode(d.split(",", 1)[1]) if d else None
        if path.startswith("/") and not path.startswith("/api/"):
            fp = os.path.realpath(os.path.join(STATIC, path.lstrip("/")))
            if fp.startswith(os.path.realpath(STATIC) + os.sep) and os.path.isfile(fp): return open(fp, "rb").read()
    except Exception:
        return None
    return None

# ---------- rysowanie ----------
def _font(size, weight=800):
    from PIL import ImageFont
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

def _bg():
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new("RGB", (W, H), BG)
    g = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(g)
    d.ellipse((-200, 120, 520, 840), fill=(20, 70, 44)); d.ellipse((700, -250, 1450, 450), fill=(80, 22, 60)); d.ellipse((420, 380, 900, 900), fill=(70, 40, 12))
    return Image.blend(im, g.filter(ImageFilter.GaussianBlur(120)), 0.9)

def _portrait(raw, w, h, radius=30, ring=None):
    """Kadr portretowy (od góry, by nie ucinać twarzy) z zaokrągleniem i opcjonalną poświatą."""
    from PIL import Image, ImageDraw, ImageOps
    try: im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception: im = None
    if im is None:
        im = Image.new("RGB", (w, h), (40, 30, 28))
    else:
        im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.2))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    return out

def _glow_frame(base, box, color, radius=34, width=5):
    from PIL import Image, ImageDraw, ImageFilter
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), radius=radius, outline=color + (200,), width=14)
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(base).rounded_rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), radius=radius, outline=color + (255,), width=width)

def _fit_text(d, text, maxw, size, weight=800, min_size=22):
    while size > min_size:
        f = _font(size, weight)
        if d.textlength(text, font=f) <= maxw: return f, text
        size -= 2
    f = _font(min_size, weight); t = text
    while t and d.textlength(t + "…", font=f) > maxw: t = t[:-1]
    return f, (t + "…") if t != text else t

def _center(d, cx, y, text, font, fill):
    d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)

def _pill(d, cx, y, text, font, fg, bg, pad=22, h=None):
    tw = d.textlength(text, font=font); h = h or font.size + 22
    d.rounded_rectangle((cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + h), radius=h // 2, fill=bg)
    d.text((cx - tw / 2, y + (h - font.size) / 2 - font.size * 0.12), text, font=font, fill=fg)

def _footer(d, t):
    f = _font(24, 700)
    txt = f"{t['luna']}  ·  {HOST}"
    _center(d, W / 2, H - 46, txt, f, MUTED)

def _jpeg(im):
    b = io.BytesIO(); im.convert("RGB").save(b, "JPEG", quality=86, optimize=True, progressive=True); return b.getvalue()

def render_battle(a, b, lang="pl", result=None, own_vote=False):
    """a/b: {"name","img","partner"}; result: None (trwa) albo {"winner":"a"|"b"|None,"pa":..,"pb":..}."""
    from PIL import ImageDraw
    t = _t(lang); im = _bg().convert("RGBA"); d = ImageDraw.Draw(im)
    pw, ph = 330, 400; ya = 122; xa, xb = 120, W - 120 - pw
    for side, c, x in (("a", a, xa), ("b", b, xb)):
        win = result and result.get("winner") == side
        col = PINK if c.get("partner") else (ORANGE if win else GREEN)
        _glow_frame(im, (x, ya, x + pw, ya + ph), col)
        p = _portrait(_load_src(c.get("img")) or b"", pw, ph)
        if result and result.get("winner") and not win:
            from PIL import ImageEnhance
            p = ImageEnhance.Brightness(p).enhance(0.55)
        im.alpha_composite(p, (x, ya))
        d = ImageDraw.Draw(im)
        fn, nm = _fit_text(d, c.get("name") or "?", pw - 20, 40, 900)
        d.rounded_rectangle((x + 12, ya + ph - 74, x + pw - 12, ya + ph - 12), radius=24, fill=(11, 7, 5, 215))
        _center(d, x + pw / 2, ya + ph - 68, nm, fn, CREAM)
        _pill(d, x + 70, ya + 14, t["ai"], _font(20, 800), BG, CREAM, pad=14, h=34)
        if result and result.get("winner") == side:
            _pill(d, x + pw / 2, ya - 22, t["winner"], _font(26, 900), BG, ORANGE, pad=24, h=44)
        if result and result.get("p" + side) is not None:
            pv = str(result["p" + side]); pv = pv.replace(",", ".") if lang == "en" else pv.replace(".", ",")
            _center(d, x + pw / 2, ya + ph + 4, f"{pv}%", _font(34, 900), ORANGE if result.get("winner") == side else CREAM)
    # ostra świecąca linia pośrodku + VS
    from PIL import Image, ImageFilter
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.line((W / 2 + 40, 80, W / 2 - 40, 560), fill=GREEN + (230,), width=10)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im); d.line((W / 2 + 40, 80, W / 2 - 40, 560), fill=(230, 255, 240), width=3)
    d.ellipse((W / 2 - 56, 266, W / 2 + 56, 378), fill=BG, outline=GREEN, width=4)
    _center(d, W / 2, 288, "VS", _font(52, 900), CREAM)
    head = t["result"] if result else (t["vote"] if own_vote else t["battle"])
    fh, hh = _fit_text(d, head, 560, 44, 900)
    _center(d, W / 2, 22, hh, fh, GREEN if not result else ORANGE)
    draw = bool(result and not result.get("winner"))
    fs = _font(24, 800); ss = t["draw"] + " · " + t["rules"] if draw else t["rules"]
    _pill(d, W / 2, 78, ss, fs, CREAM, (11, 7, 5), pad=20, h=36)
    _footer(d, t)
    return _jpeg(im)

def render_agent(name, img, lang="pl", stats=None, partner=False, official=False):
    from PIL import ImageDraw
    t = _t(lang); im = _bg().convert("RGBA")
    pw, ph = 390, 520; x, y = 90, 50
    _glow_frame(im, (x, y, x + pw, y + ph), PINK if partner else GREEN)
    im.alpha_composite(_portrait(_load_src(img) or b"", pw, ph), (x, y))
    d = ImageDraw.Draw(im); cx = 840
    _pill(d, cx, 92, t["ai"] + (" · Luna" if official else ""), _font(28, 800), BG, CREAM, pad=26, h=50)
    fn, nm = _fit_text(d, name or "?", 600, 92, 900)
    _center(d, cx, 170, nm, fn, CREAM)
    line = []
    if stats:
        if stats.get("pts"): line.append(f"{stats['pts']} {t['pts']}")
        if stats.get("wins"): line.append(f"{stats['wins']} {t['wins']}")
        if stats.get("pos") and stats.get("pts"): line.append(f"#{stats['pos']} {t['rank']}")
    if line:
        f2, l2 = _fit_text(d, " · ".join(line), 600, 38, 800); _center(d, cx, 300, l2, f2, ORANGE)
    _center(d, cx, 370 if line else 320, t["profile"], _font(32, 700), MUTED)
    _pill(d, cx, 440, t["cta_a"], _font(32, 900), BG, GREEN, pad=34, h=66)
    _footer(d, t)
    return _jpeg(im)

# ---------- pamięć podręczna ----------
_cache, _lock = OrderedDict(), threading.Lock()
def _cached(key, fn, ttl=900):
    now = time.time()
    with _lock:
        v = _cache.get(key)
        if v and now - v[0] < ttl: _cache.move_to_end(key); return v[1]
    b = fn()
    with _lock:
        _cache[key] = (now, b)
        while len(_cache) > 80: _cache.popitem(last=False)
    return b

# ---------- dane (tylko publiczne) ----------
def battle_data(bid):
    """Trwająca bitwa (bez liczby głosów – zmienia się) albo zakończona z prawdziwym wynikiem."""
    import battles
    if not re.fullmatch(r"[0-9a-f]{10}", str(bid or "")): return None
    st = battles._state()
    b = battles._find(st, bid)
    pm = {}
    try:
        E = {e["id"]: e["uid"] for e in battles._entries()}
        import partners
        pm = {k: partners.is_partner(v) for k, v in E.items()}
    except Exception: pass
    c = lambda x: {"id": x.get("id"), "name": x.get("name"), "img": x.get("img"), "partner": bool(pm.get(x.get("id")))}
    if b: return {"id": bid, "a": c(b["a"]), "b": c(b["b"]), "live": True, "scene": b.get("scene"), "ver": "live"}
    s = battles.summary(bid)
    if s: return {"id": bid, "a": c(s["a"]), "b": c(s["b"]), "live": False, "scene": s.get("scene"),
                  "result": {"winner": s["winner"] if s.get("reason") == "end" else None, "pa": s.get("pa"), "pb": s.get("pb")}, "ver": "end"}
    return None

def agent_data(pid, lang="pl", owner_plan=None):
    import profiles, battles
    r = profiles._P().get(pid) if pid != "luna" else None
    v = profiles.view(pid, lang, None, None, owner_plan if r else None)
    if not v: return None
    img = (v["photos"][0]["url"] if v["photos"] else "/catalog/luna/outfit_sweter.jpg") if pid != "luna" else "/catalog/luna/outfit_sweter.jpg"
    if v.get("pinned"):
        pu = next((p["url"] for p in v["photos"] if p["ref"] == v["pinned"]), None); img = pu or img
    bs = v.get("battles") or {}
    st = {"pts": bs.get("pts", 0), "wins": bs.get("wins", 0), "pos": bs.get("pos")} if isinstance(bs, dict) else None
    return {"id": pid, "name": v["name"], "img": img, "stats": st, "partner": bool(v.get("partner")), "official": bool(v.get("official"))}

def bt_agent_data(eid):
    import battles
    p = battles.profile(eid) if re.fullmatch(r"[0-9a-f]{10}|luna", str(eid or "")) else None
    if not p: return None
    return {"id": eid, "name": p["name"], "img": p["img"], "stats": {"pts": p["pts"], "wins": p["wins"], "pos": p["pos"]}, "official": bool(p.get("official")), "partner": False}

# ---------- trasy HTTP ----------
REDIRECTS = {
    "/casting": "/twarz.html?" + urlencode({"utm_source": "video", "utm_medium": "social", "utm_campaign": "casting"}),
    "/zapros": "/app#konto",
    "/glosuj": "/bitwy.html?" + urlencode({"utm_source": "share", "utm_medium": "link", "utm_campaign": "glosuj"}),
}

def _send(h, code, body, ctype, cache="public, max-age=600"):
    h.send_response(code); h.send_header("Content-Type", ctype); h.send_header("Content-Length", str(len(body)))
    if cache: h.send_header("Cache-Control", cache)
    h.end_headers(); h.wfile.write(body)

def handle_get(h, u, owner_plan=None):
    """Zwraca True, gdy żądanie obsłużone: /og/battle/<bid>.jpg, /og/agent/<pid>.jpg, /og/bt/<eid>.jpg, krótkie linki."""
    p = u.path.rstrip("/") or "/"
    if p in REDIRECTS:
        loc = REDIRECTS[p]
        if u.query and "#" not in loc: loc += ("&" if "?" in loc else "?") + u.query
        h.send_response(302); h.send_header("Location", loc); h.send_header("Content-Length", "0"); h.end_headers(); return True
    m = re.fullmatch(r"/og/(battle|agent|bt)/([0-9a-z]{4,12})\.jpg", u.path)
    if not m: return False
    from urllib.parse import parse_qs
    q = parse_qs(u.query); lang = (q.get("lang") or ["pl"])[0][:2]; lang = lang if lang in T else "pl"
    own = (q.get("v") or [""])[0] == "1"
    kind, ident = m.groups()
    try:
        if kind == "battle":
            bd = battle_data(ident)
            if not bd: _send(h, 404, b"not found", "text/plain", None); return True
            body = _cached(("b", ident, lang, own, bd["ver"]), lambda: render_battle(bd["a"], bd["b"], lang, bd.get("result"), own))
        elif kind == "bt":
            ad = bt_agent_data(ident)
            if not ad: _send(h, 404, b"not found", "text/plain", None); return True
            body = _cached(("t", ident, lang, ad["stats"]["pts"]), lambda: render_agent(ad["name"], ad["img"], lang, ad["stats"], ad["partner"], ad["official"]))
        else:
            ad = agent_data(ident, lang, owner_plan(ident) if owner_plan else None)
            if not ad: _send(h, 404, b"not found", "text/plain", None); return True
            body = _cached(("a", ident, lang, ad["name"], ad["img"], (ad["stats"] or {}).get("pts")), lambda: render_agent(ad["name"], ad["img"], lang, ad["stats"], ad["partner"], ad["official"]))
    except Exception as e:
        import sys; sys.stderr.write("og error %s %s\n" % (type(e).__name__, e))
        _send(h, 500, b"error", "text/plain", None); return True
    _send(h, 200, body, "image/jpeg"); return True

# ---------- metadane OG dla linków do udostępniania ----------
def _set_meta(doc, prop, val, name_attr="property"):
    val = html.escape(val, quote=True)
    pat = rf'<meta {name_attr}="{re.escape(prop)}" content="[^"]*">'
    if re.search(pat, doc): return re.sub(pat, f'<meta {name_attr}="{prop}" content="{val}">', doc, count=1)
    return doc.replace("</head>", f'<meta {name_attr}="{prop}" content="{val}">\n</head>', 1)

def _apply(doc, base, title, desc, img, alt):
    doc = _set_meta(doc, "og:title", title); doc = _set_meta(doc, "og:description", desc)
    doc = _set_meta(doc, "og:image", base + img); doc = _set_meta(doc, "og:image:width", "1200"); doc = _set_meta(doc, "og:image:height", "630")
    doc = _set_meta(doc, "og:image:alt", alt)
    doc = _set_meta(doc, "twitter:card", "summary_large_image", "name"); doc = _set_meta(doc, "twitter:title", title, "name")
    doc = _set_meta(doc, "twitter:description", desc, "name"); doc = _set_meta(doc, "twitter:image", base + img, "name")
    return doc

def _strip(x): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()
def faq_jsonld(doc):
    """FAQPage z pytań widocznych na stronie (<details><summary>…</summary><p>…</p>) – ten sam tekst, w języku strony."""
    import json
    body = doc.split("<body", 1)[-1]
    qa = [(_strip(a), _strip(b)) for a, b in re.findall(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>", body, re.S)]
    qa = [(a, b) for a, b in qa if 3 < len(a) < 300 and 3 < len(b) < 2000][:20]
    if len(qa) < 2: return ""
    d = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": a, "acceptedAnswer": {"@type": "Answer", "text": b}} for a, b in qa]}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>"

FAQ_PAGES = ("/o-lunie.html", "/promo.html", "/testerzy.html", "/twarz.html", "/butik.html")
def inject(doc, path, q, lang, base, owner_plan=None):
    """Podmienia og:image/og:title na kartę konkretnej bitwy lub agentki (link z przycisku Udostępnij); FAQPage z widocznych pytań."""
    l = lang or "pl"; t = _t(l)
    if path in FAQ_PAGES and '"FAQPage"' not in doc:
        try:
            j = faq_jsonld(doc)
            if j: doc = doc.replace("</head>", j + "\n</head>", 1)
        except Exception: pass
    try:
        if path == "/bitwy.html":
            bid = (q.get("b") or q.get("sum") or [""])[0]
            bd = battle_data(bid) if bid else None
            if bd:
                own = (q.get("v") or [""])[0] == "1"
                nm = f"{bd['a']['name']} vs {bd['b']['name']}"
                if bd["live"]:
                    title = f"{nm} – {t['vote'] if own else t['battle']}"; desc = f"{t['live']} · {t['rules']}"
                else:
                    r = bd["result"]; w = bd[r["winner"]]["name"] if r.get("winner") else None
                    title = f"{nm} – {t['result']}"; desc = (f"{t['winner']}: {w} · {r['pa']}% : {r['pb']}%" if w else t["draw"]) + f" · {t['rules']}"
                return _apply(doc, base, title, desc, f"/og/battle/{bid}.jpg?lang={l}" + ("&v=1" if own else ""), nm + " – " + t["ai"])
        if path == "/ranking.html":
            eid = (q.get("a") or [""])[0]
            ad = bt_agent_data(eid) if eid else None
            if ad:
                s = ad["stats"]; title = f"{ad['name']} · #{s['pos']} {t['rank']}" if s.get("pts") else f"{ad['name']} – {t['ai']} · {t['rank']}"
                desc = f"{s['pts']} {t['pts']} · {s['wins']} {t['wins']} · {t['rules']}"
                return _apply(doc, base, title, desc, f"/og/bt/{eid}.jpg?lang={l}", ad["name"] + " – " + t["ai"])
        if path == "/agentka.html":
            pid = (q.get("id") or ["luna"])[0][:12] or "luna"
            ad = agent_data(pid, l, owner_plan(pid) if owner_plan and pid != "luna" else None)
            if ad:
                doc = _set_meta(doc, "og:image", f"{base}/og/agent/{pid}.jpg?lang={l}")
                doc = _set_meta(doc, "twitter:image", f"{base}/og/agent/{pid}.jpg?lang={l}", "name")
                doc = _set_meta(doc, "og:image:width", "1200"); doc = _set_meta(doc, "og:image:height", "630")
                doc = _set_meta(doc, "og:image:alt", ad["name"] + " – " + t["ai"])
    except Exception:
        return doc
    return doc
