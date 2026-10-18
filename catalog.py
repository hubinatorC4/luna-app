# -*- coding: utf-8 -*-
"""Katalog postaci (agentów), strojów, póz, sylwetek i planów – sterowany danymi (data/catalog.json)."""
import json, os, re, threading, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
DATA = os.path.join(ROOT, "data")
UPLOADS = os.path.join(DATA, "uploads")
FILE = os.path.join(DATA, "catalog.json")
PLACEHOLDER = "/catalog/luna/outfit_koronkowa.jpg"
PLAN_IDS = ["darmowy", "podstawowa", "premium", "pro"]
KINDS = ("outfits", "poses", "bodies")
TONE_IDS = ("rzeczowa", "ciepla", "zalotna", "motywujaca")

def _o(i, name, plan, img=None):
    return {"id": i, "name": name, "plan": plan, "image": img or ""}

DEFAULT = {
    "plans": [
        {"id": "darmowy", "name": "Darmowy", "price": "", "period": "",
         "features": ["Około 5 minut rozmowy z Luną dziennie", "Test głosu i próbki barwy", "Oglądanie Luna Live (bez zadawania pytań)", "1 strój awatara"]},
        {"id": "podstawowa", "name": "Podstawowa", "price": "", "period": "",
         "features": ["Wszystko z planu Darmowy, oraz:", "Rozmowa z Luną bez dziennego limitu", "Pytania do Luny w Luna Live", "Barwa głosu: presety i suwaki", "2 stroje awatara i hologram"]},
        {"id": "premium", "name": "Premium", "price": "", "period": "",
         "features": ["Wszystko z planu Podstawowa, oraz:", "Trening własnej agentki AI: imię, słowo wybudzające, ton, długość odpowiedzi", "Styl agentki: kolor pierścienia i własny obraz AI", "4 stroje awatara", "Profil agentki: opis i do 4 zdjęć AI", "Wyróżniony nick: szmaragdowy, pogrubiony"]},
        {"id": "pro", "name": "Pro / Ultra", "price": "", "period": "",
         "features": ["Wszystko z planów Podstawowa i Premium, oraz:", "Pełny trening agentki AI: także poza i sylwetka (wzrost, budowa)", "Wszystkie stroje (6)", "Profil agentki: do 12 zdjęć AI i przypięte ulubione", "Nick z gradientem i odznaką PRO"]},
    ],
    "agents": [{
        "id": "luna", "name": "Luna", "wake_word": "Luna", "plan": "podstawowa", "tone": "ciepla",
        "persona": "", "description": "Ciepła trenerka głosu z hiszpańskim temperamentem.",
        "voice": {"voice": "pl-PL-ZofiaNeural", "pitch": -2.6, "rate": -8, "warmth": 4.5, "volume": -27, "spanish": True},
        "outfits": [_o("koronkowa", "Koronkowa sukienka", "darmowy"), _o("sweter", "Sweter (na co dzień)", "podstawowa"),
                    _o("wieczorowa", "Suknia wieczorowa", "premium"), _o("biznes", "Marynarka (biznes)", "premium"),
                    _o("letnia", "Letnia sukienka", "pro"), _o("koktajlowa", "Sukienka koktajlowa", "pro")],
        "poses": [_o("prosto", "Na wprost", "pro"), _o("polobrot", "Półobrót", "pro"),
                  _o("zamyslona", "Zamyślona", "pro"), _o("siedzaca", "Siedząca", "pro")],
        "bodies": [_o("drobna", "Drobna, szczupła", "pro"), _o("srednia", "Średni wzrost", "pro"),
                   _o("wysoka", "Wysoka, szczupła", "pro"), _o("pelniejsza", "Średni wzrost, pełniejsza", "pro")],
    }],
}
_lock = threading.Lock()

def _s(v, n=200): return str(v if v is not None else "").strip()[:n]
def _num(v, lo, hi, d):
    try: return max(lo, min(hi, float(v)))
    except Exception: return d
def _img(v):
    v = _s(v, 300)
    return v if re.fullmatch(r"/(catalog|uploads)/[\w\-./]+\.(jpg|jpeg|png|webp)", v or "") and ".." not in v else ""
def _id(v, fallback):
    v = re.sub(r"[^a-z0-9_\-]", "", _s(v, 40).lower())
    return v or fallback

def auto_image(agent_id, kind, item_id):
    """Plik dostarczony w repo: static/catalog/<agent>/<outfit|pose|body>_<id>.jpg"""
    pref = {"outfits": "outfit", "poses": "pose", "bodies": "body"}[kind]
    rel = f"/catalog/{agent_id}/{pref}_{item_id}.jpg"
    return rel if os.path.exists(os.path.join(STATIC, rel.lstrip("/"))) else ""

def sanitize(c):
    c = c if isinstance(c, dict) else {}
    out = {"plans": [], "agents": []}
    plans = {p.get("id"): p for p in c.get("plans", []) if isinstance(p, dict)}
    for d in DEFAULT["plans"]:
        p = plans.get(d["id"], d)
        out["plans"].append({"id": d["id"], "name": _s(p.get("name"), 40) or d["name"], "price": _s(p.get("price"), 40),
                             "period": _s(p.get("period"), 40),
                             "features": [_s(f, 160) for f in (p.get("features") or [])[:12] if _s(f)],
                             "rev": int(p.get("rev") or 0) if str(p.get("rev") or 0).isdigit() else 0})
    seen = set()
    for i, a in enumerate((c.get("agents") or [])[:30]):
        if not isinstance(a, dict): continue
        aid = _id(a.get("id") or a.get("name"), f"agent{i}")
        if aid in seen: continue
        seen.add(aid)
        v = a.get("voice") if isinstance(a.get("voice"), dict) else {}
        ag = {"id": aid, "name": _s(a.get("name"), 30) or aid.title(), "wake_word": _s(a.get("wake_word"), 30) or _s(a.get("name"), 30) or aid,
              "plan": a.get("plan") if a.get("plan") in PLAN_IDS else "podstawowa",
              "tone": a.get("tone") if a.get("tone") in TONE_IDS else "ciepla",
              "persona": _s(a.get("persona"), 4000), "description": _s(a.get("description"), 300),
              "voice": {"voice": _s(v.get("voice"), 60) or "pl-PL-ZofiaNeural", "pitch": _num(v.get("pitch"), -6, 2, -2.6),
                        "rate": int(_num(v.get("rate"), -40, 30, -8)), "warmth": _num(v.get("warmth"), 0, 10, 4.5),
                        "volume": _num(v.get("volume"), -36, -16, -27), "spanish": bool(v.get("spanish", True))}}
        for k in KINDS:
            items, ids = [], set()
            for j, o in enumerate((a.get(k) or [])[:40]):
                if not isinstance(o, dict): continue
                oid = _id(o.get("id") or o.get("name"), f"{k[:-1]}{j}")
                if oid in ids: continue
                ids.add(oid)
                items.append({"id": oid, "name": _s(o.get("name"), 60) or oid, "plan": o.get("plan") if o.get("plan") in PLAN_IDS else "pro",
                              "image": _img(o.get("image"))})
            ag[k] = items
        out["agents"].append(ag)
    if not out["agents"]: return sanitize(copy.deepcopy(DEFAULT))
    return out

# v1.5.5: trening agentki AI tylko w planach płatnych – stare domyślne opisy planów zamieniamy na nowe
# (opisy zmienione ręcznie w panelu zostają bez zmian)
_OLD_V1 = {"premium": ["Wszystko z planu Podstawowa, oraz:", "4 stroje awatara", "Stwórz własną asystentkę: imię, słowo wybudzające, ton, długość odpowiedzi", "Własny kolor pierścienia i własny obraz awatara"], "pro": ["Wszystko z planów Podstawowa i Premium, oraz:", "Wszystkie stroje (6)", "Zmiana pozy awatara", "Wybór sylwetki (wzrost, budowa)", "Dodatkowe postacie z katalogu"]}
_OLD_V2 = {"premium": ["Wszystko z planu Podstawowa, oraz:", "Trening własnej agentki AI: imię, słowo wybudzające, ton, długość odpowiedzi", "Styl agentki: kolor pierścienia i własny obraz AI", "4 stroje awatara"], "pro": ["Wszystko z planów Podstawowa i Premium, oraz:", "Pełny trening agentki AI: także poza i sylwetka (wzrost, budowa)", "Wszystkie stroje (6)"]}
_NEW_FEATURES = {"premium": ["Wszystko z planu Podstawowa, oraz:", "Trening własnej agentki AI: imię, słowo wybudzające, ton, długość odpowiedzi", "Styl agentki: kolor pierścienia i własny obraz AI", "4 stroje awatara", "Profil agentki: opis i do 4 zdjęć AI", "Wyróżniony nick: szmaragdowy, pogrubiony"], "pro": ["Wszystko z planów Podstawowa i Premium, oraz:", "Pełny trening agentki AI: także poza i sylwetka (wzrost, budowa)", "Wszystkie stroje (6)", "Profil agentki: do 12 zdjęć AI i przypięte ulubione", "Nick z gradientem i odznaką PRO"]}

# Wersja opisów planów. Plany zapisane w data/catalog.json bez rev >= CAT_REV (czyli sprzed korekty spójności)
# pokazują opisy z kodu; zapis w panelu po tej zmianie ustawia rev i od tej chwili wygrywa wersja z panelu.
CAT_REV = 2
_STALE = re.compile(r"2160\s*px|dat[aęy] urodzenia|jednym klikni|wersj[aię] demonstracyjn", re.I)
_DEF_PLANS = {p["id"]: p for p in DEFAULT["plans"]}

def public(c):
    """Wersja dla klienta: uzupełnia obrazy (plik w repo → wgrany → zastępczy)."""
    c = copy.deepcopy(c)
    for p in c.get("plans", []):
        if p.get("id") in _NEW_FEATURES and p.get("features") in (_OLD_V1.get(p["id"]), _OLD_V2.get(p["id"])): p["features"] = list(_NEW_FEATURES[p["id"]])
        p.pop("rev", None)
    for a in c["agents"]:
        for k in KINDS:
            for o in a[k]:
                img = o["image"] or auto_image(a["id"], k, o["id"])
                o["placeholder"] = not img
                o["image"] = img or (a["outfits"][0]["image"] if k != "outfits" and a["outfits"] and a["outfits"][0]["image"] else "") or auto_image(a["id"], "outfits", "koronkowa") or PLACEHOLDER
            for o in a[k]:
                if o["image"].endswith(".jpg") and os.path.exists(os.path.join(STATIC, o["image"].lstrip("/")[:-4] + "@2x.jpg")):
                    o["image2x"] = o["image"][:-4] + "@2x.jpg"
        a["avatar"] = next((o["image"] for o in a["outfits"] if not o["placeholder"]), a["outfits"][0]["image"] if a["outfits"] else PLACEHOLDER)
    for p in c.get("plans", []):  # ceny nie są publikowane (aplikacja w fazie testów)
        p.pop("price", None); p.pop("period", None)
    return c

def _migrate(c):
    """Zapisany katalog sprzed poprawek (rev < CAT_REV) albo z nieaktualną frazą nie przywraca starych opisów planów."""
    for p in c.get("plans", []):
        d = _DEF_PLANS.get(p.get("id"))
        if d and (int(p.get("rev") or 0) < CAT_REV or any(_STALE.search(f) for f in p.get("features") or [])):
            p["features"] = list(d["features"])
    return c

def load():
    try:   # Postgres (trwale), gdy jest DATABASE_URL; plik data/catalog.json tylko lokalnie
        import store
        sv = store.get("catalog", None) if store.BACKEND == "postgres" else None
        if isinstance(sv, dict) and sv: return _migrate(sanitize(sv))
    except Exception: pass
    try:
        with open(FILE, encoding="utf-8") as f: return _migrate(sanitize(json.load(f)))
    except Exception:
        return sanitize(copy.deepcopy(DEFAULT))

def save(c):
    c = sanitize(c)
    for p in c["plans"]: p["rev"] = CAT_REV
    with _lock:
        os.makedirs(DATA, exist_ok=True)
        with open(FILE + ".tmp", "w", encoding="utf-8") as f: json.dump(c, f, ensure_ascii=False, indent=1)
        os.replace(FILE + ".tmp", FILE)
    import store
    if store.BACKEND == "postgres": store.put("catalog", c)
    return c

def save_upload(name, raw):
    ext = os.path.splitext(name or "")[1].lower()
    sig = raw[:12]
    if ext == ".mp3":
        if len(raw) > 6 * 1024 * 1024: raise ValueError("Plik MP3 większy niż 6 MB")
        if not (sig.startswith(b"ID3") or sig[:1] == b"\xff"): raise ValueError("To nie jest prawidłowy plik MP3")
    else:
        if ext not in (".jpg", ".jpeg", ".png", ".webp"): raise ValueError("Dozwolone formaty: JPG, PNG, WEBP, MP3")
        if len(raw) > 4 * 1024 * 1024: raise ValueError("Plik większy niż 4 MB")
        if not (sig.startswith(b"\xff\xd8") or sig.startswith(b"\x89PNG") or (sig[:4] == b"RIFF" and sig[8:12] == b"WEBP")):
            raise ValueError("To nie jest prawidłowy obraz")
    import secrets, upload_gate
    os.makedirs(UPLOADS, exist_ok=True)
    if ext != ".mp3":   # filtr nagości obowiązuje też admina; „na granicy” = wybierz inne zdjęcie (nie ma kolejki dla plików publicznych)
        g = upload_gate.image(raw, "admin_upload", max_px=2048, max_in=4 * 1024 * 1024, quality=3, review="hold")
        raw, ext = g.bytes, "." + g.ext
    fn = secrets.token_hex(8) + (".jpg" if ext == ".jpeg" else ext)
    with open(os.path.join(UPLOADS, fn), "wb") as f: f.write(raw)
    import store, base64
    if store.BACKEND == "postgres": store.put("upl:" + fn, {"b": base64.b64encode(raw).decode()})   # przetrwa wdrożenie
    return "/uploads/" + fn

def read_upload(fn):
    """Plik wgrany przez admina: z dysku, a po wdrożeniu z bazy (i znów na dysk jako pamięć podręczna)."""
    p = os.path.join(UPLOADS, fn)
    if os.path.exists(p): return open(p, "rb").read()
    import store, base64
    r = store.get("upl:" + fn) if store.BACKEND == "postgres" else None
    if not r or not r.get("b"): return None
    raw = base64.b64decode(r["b"])
    try:
        os.makedirs(UPLOADS, exist_ok=True); open(p, "wb").write(raw)
    except Exception: pass
    return raw
