# -*- coding: utf-8 -*-
"""Jakość mediów i Generator agentek według planu – egzekwowane na serwerze (402 z nazwą planu).
Podstawowa/Darmowy: obrazy ≤ 854 px (dłuższy bok), wideo ≤ 480p, bez generatora.
Premium: ≤ 1280 px, wideo ≤ 720p, generator 20/dzień.  Pro / Ultra: ≤ 1920 px (źródła mają maks. 1920 px – nie powiększamy), wideo ≤ 1080p, generator 60/dzień."""
import base64, hashlib, threading, time
import store, plans, imgsafe

CAPS = {"darmowy": {"img": 854, "video": 480, "gen": 0, "gen_px": 0},
        "podstawowa": {"img": 854, "video": 480, "gen": 0, "gen_px": 0},
        "premium": {"img": 1280, "video": 720, "gen": 20, "gen_px": 1280},
        "pro": {"img": 1920, "video": 1080, "gen": 60, "gen_px": 1920}}
USER_PHOTO_PX = 854          # zdjęcia użytkownika na wallu: zawsze maks. 854 px
VIDEO_LEVELS = (480, 720, 1080)
NEED_FOR_VIDEO = {480: "darmowy", 720: "premium", 1080: "pro"}
WIDTHS = (480, 854, 1280, 1920)

def caps(plan): return dict(CAPS.get(plan, CAPS["darmowy"]))

def need_for_img(w):
    for p in ("darmowy", "premium", "pro"):
        if w <= CAPS[p]["img"]: return p
    return "pro"

def lock(need):
    return {"error": "plan_required", "need": need, "plan_name": plans.NAMES[need],
            "message": f"Ta jakość jest dostępna od planu {plans.NAMES[need]}."}

def check_video(plan, q):
    """None gdy wolno, inaczej treść odpowiedzi 402."""
    q = int(q)
    if q not in VIDEO_LEVELS: raise ValueError("Nieznana jakość.")
    return None if q <= caps(plan)["video"] else lock(NEED_FOR_VIDEO[q])

def check_img(plan, w):
    return None if w <= caps(plan)["img"] else lock(need_for_img(w))

# ---------- skalowanie obrazów przy wydawaniu (pamięć podręczna w RAM) ----------
_rc, _rl = {}, threading.Lock()
def scaled_dataurl(key, data_url, w):
    """data URL → bajty JPEG/PNG o dłuższym boku ≤ w (bez powiększania, bez metadanych)."""
    ck = (key, w)
    with _rl:
        if ck in _rc: return _rc[ck]
    head, _, b = str(data_url or "").partition(";base64,")
    raw = base64.b64decode(b)
    out, ext = imgsafe.reencode(raw, max_px=w, max_in=12 * 1024 * 1024, quality=3)
    res = (out, "image/png" if ext == "png" else "image/jpeg")
    with _rl:
        if len(_rc) > 300: _rc.clear()
        _rc[ck] = res
    return res

# ---------- Generator agentek: dzienne limity ----------
_gl = threading.Lock()
def _day(): return time.strftime("%Y-%m-%d", time.gmtime())
def gen_used(uid):
    g = (store.get("gen_count", {}) or {}).get(uid) or {}
    return g.get("n", 0) if g.get("d") == _day() else 0
def gen_take(uid, plan):
    lim = caps(plan)["gen"]
    with _gl:
        G = store.get("gen_count", {}) or {}
        g = G.get(uid) or {}
        n = g.get("n", 0) if g.get("d") == _day() else 0
        if n >= lim: return False, n, lim
        G[uid] = {"d": _day(), "n": n + 1}; store.put("gen_count", G)
        return True, n + 1, lim

# ---------- zdjęcia użytkownika nie mogą zostać twarzą agentki ----------
def user_photo_mark(raw_or_out):
    h = hashlib.sha256(raw_or_out).hexdigest()
    with _gl:
        S = store.get("user_photo_hashes", []) or []
        if h not in S: S.append(h); store.put("user_photo_hashes", S[-5000:])
def is_user_photo(raw):
    return hashlib.sha256(raw).hexdigest() in set(store.get("user_photo_hashes", []) or [])
