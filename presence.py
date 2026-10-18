# -*- coding: utf-8 -*-
"""Status online (v1.6.6). last_seen zapisywany przy zalogowanych żądaniach, najwyżej raz na 60 s.
Online = widziany ≤ 2 min temu; „Aktywna/y X min temu” do 1 h; później nic.
Widoczność (Prywatność → „Kto widzi, że jestem online”): all / close (domyślnie, tylko bliscy znajomi) / nobody.
API nigdy nie oddaje surowego znacznika czasu – tylko {"on": true} albo {"min": X}; zablokowani nie widzą nic."""
import threading, time
import store
THROTTLE, ONLINE_S, MAX_S = 60, 120, 3600
VIS = ("all", "close", "nobody")
DEFAULT_VIS = "close"
_lock = threading.Lock()
_mem = {}   # uid -> last_seen (pamięć procesu; zapis do magazynu co 60 s)

def touch(uid, now=None):
    if not uid: return
    now = int(now or time.time())
    if now - _mem.get(uid, 0) < THROTTLE: return
    with _lock:
        _mem[uid] = now
        store.put("ls:" + uid, now)

def last_seen(uid):
    t = _mem.get(uid)
    if t is None:
        t = int(store.get("ls:" + uid, 0) or 0); _mem[uid] = t
    return t

def vis(uid):
    try:
        import userprof; v = (userprof._P().get(uid) or {}).get("online_vis")
    except Exception: v = None
    return v if v in VIS else DEFAULT_VIS

def set_vis(uid, v):
    if v not in VIS: raise ValueError("bad visibility")
    import userprof
    with userprof._lock:
        P = userprof._P(); r = P.setdefault(uid, {}); r["online_vis"] = v; store.put("user_profiles", P)
    return v

def _fr(uid):
    import inbox; return inbox._fr(uid)

def can_see(viewer, target):
    """Serwerowa bramka: czy viewer może zobaczyć status target."""
    if not viewer or not target: return False   # niezalogowani nigdy nie widzą statusu
    if viewer == target: return True
    ft, fv = _fr(target), _fr(viewer)
    if viewer in ft["blocked"] or target in fv["blocked"]: return False
    v = vis(target)
    if v == "nobody": return False
    if v == "all": return True
    return viewer in ft["friends"] and viewer in (ft.get("close") or {})

def status(viewer, target, now=None):
    """None (nic nie pokazujemy) albo {"on": True} / {"min": X} (1–60)."""
    if not can_see(viewer, target): return None
    t = last_seen(target)
    if not t: return None
    d = int(now or time.time()) - t
    if d <= ONLINE_S: return {"on": True}
    if d <= MAX_S: return {"min": max(1, d // 60)}
    return None

def online_flag(viewer, target):
    s = status(viewer, target); return bool(s and s.get("on"))

def delete(uid):
    _mem.pop(uid, None)
    store.put("ls:" + uid, 0)
