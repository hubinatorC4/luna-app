"""Poleć Lunę (v1.4.9): gdy osoba, która założyła konto z linku polecającego, zrobi PIERWSZY prawdziwy zakup (plan lub strój),
OBIE osoby dostają 7 dni Premium. Limit: 10 nagród polecającego w miesiącu (czas polski). Konta oznaczone przez antybota – bez nagrody.
Program można wyłączyć w panelu właściciela (referral_cfg.enabled). Bez nagród za polubienia/obserwacje. Tylko prawdziwe dane."""
import datetime, secrets, threading, time
import store, accounts, antibot

DAYS = 7; CAP = 10
_lock = threading.Lock()
ALPH = "abcdefghjkmnpqrstuvwxyz23456789"

def _month(ts=None):
    try:
        from zoneinfo import ZoneInfo; d = datetime.datetime.fromtimestamp(ts or time.time(), ZoneInfo("Europe/Warsaw"))
    except Exception: d = datetime.datetime.utcfromtimestamp(ts or time.time())
    return d.strftime("%Y-%m")

def _refs(): return store.get("referrals", {}) or {}
def enabled(): return bool((store.get("referral_cfg", {}) or {}).get("enabled", True))
def set_enabled(on):
    c = store.get("referral_cfg", {}) or {}; c["enabled"] = bool(on); c["changed"] = int(time.time()); store.put("referral_cfg", c); return enabled()

def code(uid):
    """Stały kod polecający konta (tworzony przy pierwszym użyciu)."""
    with accounts._lock:
        a = accounts._accts(); u = a.get(uid)
        if not u: raise KeyError("not found")
        if not u.get("ref"):
            used = {x.get("ref") for x in a.values()}
            c = "".join(secrets.choice(ALPH) for _ in range(7))
            while c in used: c = "".join(secrets.choice(ALPH) for _ in range(7))
            u["ref"] = c; store.put("accounts", a)
        return u["ref"]

def _owner(c):
    c = str(c or "").strip().lower()[:12]
    if not c: return None
    return next((u["uid"] for u in accounts._accts().values() if u.get("ref") == c), None)

def on_signup(new_uid, ref_code, ak_new=None):
    """Zapisuje polecenie (status pending). Nagroda dopiero po potwierdzeniu e-maila."""
    if not enabled(): return None
    rid = _owner(ref_code)
    if not rid or rid == new_uid: return None
    with _lock:
        R = _refs()
        if any(r["referee"] == new_uid for r in R.values()): return None
        k = secrets.token_hex(6)
        R[k] = {"id": k, "referrer": rid, "referee": new_uid, "created": int(time.time()), "status": "pending", "reason": "", "rewarded_at": 0, "ak": ak_new or ""}
        store.put("referrals", R)
    return k

def _grant(uid, days):
    with accounts._lock:
        a = accounts._accts(); u = a.get(uid)
        if not u: return False
        now = time.time(); ps = u.get("pass") or {}
        if ps.get("until", 0) > now and ps.get("plan") in ("premium", "pro"):
            ps["until"] = int(ps["until"] + days * 86400); ps.setdefault("ref_days", 0); ps["ref_days"] += days
        else:
            ps = {"plan": "premium", "until": int(now + days * 86400), "granted_at": int(now), "by": "polecenie", "reminded": [], "ref_days": days}
        u["pass"] = ps; store.put("accounts", a); return True

def on_verified(uid):
    """Potwierdzenie e-maila poleconej osoby – tylko odnotowanie (nagroda po pierwszym zakupie)."""
    with _lock:
        R = _refs(); r = next((x for x in R.values() if x["referee"] == uid and x["status"] == "pending"), None)
        if not r: return None
        r["verified"] = True; store.put("referrals", R); return r["status"]

def on_purchase(uid):
    """Pierwszy opłacony zakup poleconej osoby → po 7 dni Premium dla obu stron (jeśli program włączony)."""
    if not uid: return None
    with _lock:
        R = _refs(); r = next((x for x in R.values() if x["referee"] == uid and x["status"] == "pending"), None)
        if not r: return None
        if not enabled(): return None   # wyłączony: polecenie czeka; nagroda tylko, gdy program działa
        if r.get("ak") and antibot.hidden(r["ak"]): r["status"] = "rejected"; r["reason"] = "konto oznaczone jako podejrzane"
        else:
            m = _month(); n = sum(1 for x in R.values() if x["referrer"] == r["referrer"] and x["status"] == "rewarded" and _month(x["rewarded_at"]) == m)
            if n >= CAP: r["status"] = "capped"; r["reason"] = f"limit {CAP} nagród w miesiącu"
            elif _grant(r["referrer"], DAYS):
                _grant(uid, DAYS); r["status"] = "rewarded"; r["rewarded_at"] = int(time.time()); r["both"] = True
        store.put("referrals", R); return r["status"]

def mine(uid, base=""):
    R = [r for r in _refs().values() if r["referrer"] == uid]; m = _month()
    month = sum(1 for r in R if r["status"] == "rewarded" and _month(r["rewarded_at"]) == m)
    if not enabled(): return {"enabled": False}
    c = code(uid)
    return {"enabled": True, "rule": "first_purchase_both", "code": c, "link": f"{base}/?ref={c}", "days_per_referral": DAYS, "cap_month": CAP, "rewarded_month": month,
            "rewarded_total": sum(1 for r in R if r["status"] == "rewarded"), "pending": sum(1 for r in R if r["status"] == "pending"),
            "days_earned": DAYS * sum(1 for r in R if r["status"] == "rewarded"), **badge(R)}

BADGES = ((10, "gold"), (3, "amb"), (1, "seed"))
def badge(R):
    """Odznaka „Zaproś znajomych” – tylko z prawdziwych liczb: osoby z linku z potwierdzonym e-mailem (bez odrzuconych przez antybota)."""
    ok = sum(1 for r in R if (r.get("verified") or r["status"] == "rewarded") and r["status"] != "rejected")
    b = next((k for n, k in BADGES if ok >= n), None)
    nxt = next((n for n, k in reversed(BADGES) if ok < n), None)
    return {"joined": len(R), "confirmed": ok, "badge": b, "badge_next": nxt}

def admin_list():
    A = accounts._accts(); nick = lambda uid: (A.get(uid) or {}).get("name") or ("konto " + uid[:4]) if uid in A else "usunięte konto"
    out = [{"id": r["id"], "referrer": nick(r["referrer"]), "referee": nick(r["referee"]), "created": r["created"], "status": r["status"], "reason": r["reason"],
            "rewarded_at": r["rewarded_at"], "referee_verified": bool((A.get(r["referee"]) or {}).get("verified"))} for r in _refs().values()]
    out.sort(key=lambda x: -x["created"])
    st = {}
    for r in out: st[r["status"]] = st.get(r["status"], 0) + 1
    return {"items": out[:500], "stats": st, "days": DAYS, "cap": CAP, "enabled": enabled()}

def forget(uid):
    """Usunięcie konta: usuwamy powiązania polecające tej osoby (dane osobowe), zachowując anonimowe liczby nagród."""
    with _lock:
        R = _refs(); ch = False
        for r in R.values():
            if r["referee"] == uid: r["referee"] = "x"; ch = True
            if r["referrer"] == uid: r["referrer"] = "x"; ch = True
        if ch: store.put("referrals", R)
