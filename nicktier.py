"""Styl nicku według planu – wyliczany na serwerze z konta (klient nie może go podrobić).
"" = Darmowy/Podstawowa (zwykły), "premium" = szmaragd, "pro" = gradient + odznaka PRO."""
import time, threading
import accounts
_c, _l = {}, threading.Lock()

def of_uid(uid):
    if not uid: return ""
    now = time.time()
    with _l:
        v = _c.get(uid)
        if v and v[1] > now: return v[0]
    u = accounts._accts().get(uid)
    p = accounts.plan(u)["plan"] if u else "darmowy"
    t = p if p in ("premium", "pro") else ""
    with _l:
        if len(_c) > 5000: _c.clear()
        _c[uid] = (t, now + 60)
    return t

def of_author(ak):
    ak = str(ak or "")
    return of_uid(ak[2:]) if ak.startswith("u:") else ""
