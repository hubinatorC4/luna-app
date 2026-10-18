# -*- coding: utf-8 -*-
"""Katalog postaci (agentów), strojów, póz, sylwetek i planów – sterowany danymi (data/catalog.json)."""
import json, os, re, threading, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
DATA = os.path.join(ROOT, "data")
UPLOADS = os.path.join(DATA, "uploads")
FILE = os.path.join(DATA, "catalog.json")
PLACEHOLDER = "/catalog/luna/outfit_koronkowa.jpg"
PLAN_IDS = ["podstawowa", "premium", "pro"]
KINDS = ("outfits", "poses", "bodies")
TONE_IDS = ("rzeczowa", "ciepla", "zalotna", "motywujaca")

def _o(i, name, plan, img=None):
    return {"id": i, "name": name, "plan": plan, "image": img or ""}

DEFAULT = {
    "plans": [
        {"id": "podstawowa", "name": "Podstawowa", "price": "0 zł", "period": "na zawsze",
         "features": ["Rozmowa tekstowa i głosowa z Luną", "Słowo wybudzające „Luna”", "Barwa głosu: presety i suwaki", "2 stroje awatara"]},
        {"id": "premium", "name": "Premium", "price": "19,99 zł", "period": "miesięcznie",
         "features": ["Wszystko z planu Podstawowa, oraz:", "4 stroje awatara", "Stwórz własną asystentkę: imię, słowo wybudzające, ton, długość odpowiedzi", "Własny kolor pierścienia i własny obraz awatara"]},
        {"id": "pro", "name": "Pro / Ultra", "price": "39,99 zł", "period": "miesięcznie",
         "features": ["Wszystko z planów Podstawowa i Premium, oraz:", "Wszystkie stroje (6)", "Zmiana pozy awatara", "Wybór sylwetki (wzrost, budowa)", "Dodatkowe postacie z katalogu"]},
    ],
    "agents": [{
        "id": "luna", "name": "Luna", "wake_word": "Luna", "plan": "podstawowa", "tone": "ciepla",
        "persona": "", "description": "Ciepła trenerka głosu z hiszpańskim temperamentem.",
        "voice": {"voice": "pl-PL-ZofiaNeural", "pitch": -2.6, "rate": -8, "warmth": 4.5, "volume": -27, "spanish": True},
        "outfits": [_o("koronkowa", "Koronkowa sukienka", "podstawowa"), _o("sweter", "Sweter (na co dzień)", "podstawowa"),
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
                             "features": [_s(f, 160) for f in (p.get("features") or [])[:12] if _s(f)]})
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

def public(c):
    """Wersja dla klienta: uzupełnia obrazy (plik w repo → wgrany → zastępczy)."""
    c = copy.deepcopy(c)
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
    return c

def load():
    try:
        with open(FILE, encoding="utf-8") as f: return sanitize(json.load(f))
    except Exception:
        return sanitize(copy.deepcopy(DEFAULT))

def save(c):
    c = sanitize(c)
    with _lock:
        os.makedirs(DATA, exist_ok=True)
        with open(FILE + ".tmp", "w", encoding="utf-8") as f: json.dump(c, f, ensure_ascii=False, indent=1)
        os.replace(FILE + ".tmp", FILE)
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
    import secrets
    os.makedirs(UPLOADS, exist_ok=True)
    fn = secrets.token_hex(8) + (".jpg" if ext == ".jpeg" else ext)
    with open(os.path.join(UPLOADS, fn), "wb") as f: f.write(raw)
    return "/uploads/" + fn
