"""Butik Luny: baza strojów (3 linie × 150), wydawanie partiami, ceny per waluta (ukryte publicznie, dopóki „Pokaż ceny” jest wyłączone).
Źródło startowe: data/catalog_outfits.json (w repo); zmiany moderatora w magazynie store (Postgres, gdy jest DATABASE_URL)."""
import json, os, re, threading, time
import store

SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "catalog_outfits.json")
LIMITS = {"usd": (1.0, 99.99), "eur": (0.99, 100.0), "pln": (3.99, 429.99)}  # min 1 USD, max 100 EUR
TIERS = ("free", "podstawowa", "premium", "pro")
STATUSES = ("planned", "released", "hidden")
_lock = threading.Lock(); _cache = {"items": None, "lines": None}

def _seed():
    d = json.load(open(SEED, encoding="utf-8"))
    return d["lines"], d["items"]

def _load():
    if _cache["items"] is None:
        lines, seed = _seed()
        saved = store.get("butik_items", None)
        its = saved if isinstance(saved, list) and saved else seed
        rd = {i["id"]: i["release_date"] for i in seed if i.get("release_date")}
        for i in its:
            if i["id"] in rd and not i.get("release_date"): i["release_date"] = rd[i["id"]]
        _cache["lines"] = lines; _cache["items"] = its
    return _cache["items"]

def _save(items):
    _cache["items"] = items; store.put("butik_items", items)

def lines(): _load(); return _cache["lines"]

def check_price(p):
    out = {}
    for cur, (lo, hi) in LIMITS.items():
        v = str((p or {}).get(cur, "")).replace(",", ".").strip()
        try: f = round(float(v), 2)
        except ValueError: raise ValueError(f"Podaj cenę {cur.upper()}.")
        if not (lo <= f <= hi): raise ValueError(f"Cena {cur.upper()} musi być w przedziale {lo:.2f}–{hi:.2f} (min. 1 USD, maks. 100 EUR).")
        out[cur] = f
    return out

def item(id_): return next((i for i in _load() if i["id"] == id_), None)

def _today():
    import datetime
    try:
        from zoneinfo import ZoneInfo; return datetime.datetime.now(ZoneInfo("Europe/Warsaw")).date().isoformat()
    except Exception: return datetime.datetime.utcnow().date().isoformat()

def eff_status(i):
    """Pozycja zaplanowana z datą premiery (release_date) staje się dostępna automatycznie od tego dnia (czas polski)."""
    if i.get("status") == "planned" and i.get("release_date") and i["release_date"] <= _today(): return "released"
    return i.get("status")

def tier_plan(t): return "darmowy" if t == "free" else t

def ranges(items=None):
    r = {}
    for i in items or _load():
        x = r.setdefault(i["line"], {c: [1e9, 0] for c in LIMITS})
        for c in LIMITS: x[c][0] = min(x[c][0], i["price"][c]); x[c][1] = max(x[c][1], i["price"][c])
    return r

def public(show_prices=False):
    its = [i for i in _load() if eff_status(i) == "released" or (i["status"] == "planned" and i.get("release_date"))]
    keep = ("id", "name", "name_en", "line", "collection", "category", "colors", "material", "description", "tier", "rarity", "image", "release_version", "release_date")
    out = [{k: i.get(k) for k in keep} | ({"price": i["price"]} if show_prices else {}) | ({"upcoming": True} if eff_status(i) != "released" else {}) for i in its]
    planned = {}
    for i in _load():
        if eff_status(i) == "planned": planned[i["line"]] = planned.get(i["line"], 0) + 1
    res = {"lines": lines(), "items": out, "planned": planned, "prices_visible": bool(show_prices)}
    if show_prices: res["ranges"] = ranges()
    return res

def admin_list(f=None):
    f = f or {}; q = str(f.get("q", "")).lower().strip()
    its = [i for i in _load() if (not f.get("line") or i["line"] == f["line"]) and (not f.get("status") or i["status"] == f["status"])
           and (not f.get("category") or i["category"] == f["category"]) and (not q or q in (i["name"] + " " + i["name_en"] + " " + i["id"]).lower())]
    off = max(0, int(f.get("offset", 0) or 0)); lim = max(1, min(200, int(f.get("limit", 50) or 50)))
    st = {}
    for i in _load(): st[i["status"]] = st.get(i["status"], 0) + 1
    return {"total": len(its), "items": its[off:off + lim], "stats": st, "ranges": ranges(), "lines": lines(), "limits": LIMITS}

def update(id_, d):
    with _lock:
        its = list(_load()); it = next((i for i in its if i["id"] == id_), None)
        if not it: raise KeyError("not found")
        if "price" in d: it["price"] = check_price(d["price"])
        if d.get("tier") in TIERS: it["tier"] = d["tier"]
        if d.get("status") in STATUSES:
            it["status"] = d["status"]
            if d["status"] != "released": it["release_version"] = None
        if "image" in d:
            img = str(d["image"] or "")
            if img and not re.fullmatch(r"/(uploads|catalog/[\w-]+)/[\w\-.]+\.(jpg|png|webp)", img): raise ValueError("Nieprawidłowy obraz.")
            it["image"] = img
        for k in ("name", "name_en", "description"):
            if k in d and str(d[k]).strip(): it[k] = re.sub(r"[<>]", "", str(d[k]).strip())[:200 if k != "description" else 500]
        _save(its); return it

def release_next(n, version, line=None, ids=None):
    """Oznacza kolejne n zaplanowanych pozycji jako wydane w wersji `version`."""
    n = max(1, min(100, int(n or 10))); version = re.sub(r"[^\w.\-]", "", str(version or ""))[:12] or "next"
    with _lock:
        its = list(_load()); done = []
        for i in its:
            if len(done) >= n: break
            if i["status"] != "planned": continue
            if ids and i["id"] not in ids: continue
            if line and i["line"] != line: continue
            i["status"] = "released"; i["release_version"] = version; done.append(i["id"])
        _save(its); return done

def reset():
    with _lock: _save(_seed()[1])
