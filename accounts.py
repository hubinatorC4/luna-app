"""Konta użytkowników: e-mail + hasło (Argon2id), sesje w ciasteczku HttpOnly, CSRF, blokada po nieudanych logowaniach,
weryfikacja e-mail (gdy skonfigurowano dostawcę), eksport i usuwanie danych (RODO). Hasła i tokeny nigdy nie są logowane."""
import hashlib, re, secrets, threading, time
import store, age, testers, notify, security
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
    _ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
except Exception:  # awaryjnie scrypt ze stdlib
    _ph = None

SESSION_DAYS = 30
MAX_FAILS, LOCK_MIN = 5, 15
_lock = threading.Lock()
EMAIL_RE = notify.EMAIL_RE

def _h(s): return hashlib.sha256(s.encode()).hexdigest()

def hash_pw(pw):
    if _ph: return _ph.hash(pw)
    salt = secrets.token_bytes(16)
    return "scrypt$" + salt.hex() + "$" + hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1).hex()

def check_pw(stored, pw):
    if stored.startswith("scrypt$"):
        _, s, d = stored.split("$"); return secrets.compare_digest(hashlib.scrypt(pw.encode(), salt=bytes.fromhex(s), n=2**14, r=8, p=1).hex(), d)
    try: return _ph.verify(stored, pw)
    except Exception: return False

def _accts(): return store.get("accounts", {}) or {}
def _sess(): return store.get("sessions", {}) or {}

def _by_email(a, email):
    e = email.lower()
    return next((u for u in a.values() if u["email"].lower() == e), None)

def validate_pw(pw):
    if not isinstance(pw, str) or not (10 <= len(pw) <= 128): raise ValueError("Hasło musi mieć od 10 do 128 znaków.")
    if pw.lower() == pw or pw.upper() == pw or not re.search(r"\d", pw):
        raise ValueError("Hasło powinno zawierać małe i wielkie litery oraz cyfrę.")

def signup(d, base_url=""):
    email = str(d.get("email", "")).strip()[:254]; pw = d.get("password"); name = str(d.get("name", "")).strip()[:30]
    name = re.sub(r"[<>\x00-\x1f]", "", name)
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail.")
    validate_pw(pw)
    decl = age.check(d)  # Underage → grzeczna odmowa, nic nie zapisujemy
    if d.get("terms") is not True: raise ValueError("Zaakceptuj regulamin i informację o prywatności.")
    import userprof, social
    nick = social.nick_ok(d.get("nick") or name)  # tylko nick (bez imienia i nazwiska); wymagany, unikalny, moderowany
    if any(userprof._key(v.get("nick", "")) == userprof._key(nick) for v in userprof._P().values()): raise ValueError("Ten nick jest już zajęty – wybierz inny.")
    name = nick
    pwh = hash_pw(pw)
    with _lock:
        a = _accts()
        if _by_email(a, email): raise ValueError("Konto z tym adresem już istnieje – zaloguj się.")
        uid = secrets.token_hex(8); vt = secrets.token_urlsafe(24)
        a[uid] = {"uid": uid, "email": email, "pw": pwh, "name": name, "created": int(time.time()), "verified": False,
                  "vtok": _h(vt), "tester": "", "fails": 0, "lock": 0, "terms_at": int(time.time()), **decl}
        store.put("accounts", a)
    try: userprof.set_nick(uid, nick)
    except ValueError: pass
    sent = False
    if notify.email_enabled() and base_url:
        link = f"{base_url}/api/account/verify?token={vt}"
        try:
            notify._send_email(email, "Luna – potwierdź adres e-mail", f"Kliknij, aby potwierdzić konto w Lunie: {link}",
                               f"<p>Kliknij, aby potwierdzić konto w Lunie:</p><p><a href=\"{link}\">Potwierdzam adres</a></p>")
            sent = True
        except Exception: sent = False
    return uid, sent

def verify(tok):
    th = _h(str(tok or ""))
    with _lock:
        a = _accts()
        for u in a.values():
            if u.get("vtok") and secrets.compare_digest(u["vtok"], th):
                u["verified"] = True; u["vtok"] = ""; store.put("accounts", a); return u["uid"]
    return False

class TotpRequired(Exception):
    """Hasło poprawne, ale konto ma włączone 2FA – potrzebny 6-cyfrowy kod z aplikacji."""

def login(email, pw, totp=None):
    """Zwraca uid lub rzuca ValueError/PermissionError (blokada)/TotpRequired (2FA)."""
    email = str(email or "").strip()[:254]; now = time.time()
    with _lock:
        a = _accts(); u = _by_email(a, email)
        if u and u.get("lock", 0) > now: raise PermissionError(f"Za dużo nieudanych prób. Konto zablokowane na {LOCK_MIN} minut.")
    ok = bool(u) and isinstance(pw, str) and len(pw) <= 128 and check_pw(u["pw"], pw)
    if not u: hash_pw("dummy-password-1A")  # wyrównanie czasu odpowiedzi
    with _lock:
        a = _accts(); u2 = _by_email(a, email)
        if not ok:
            if u2:
                u2["fails"] = u2.get("fails", 0) + 1
                if u2["fails"] >= MAX_FAILS: u2["lock"] = int(now + LOCK_MIN * 60); u2["fails"] = 0
                store.put("accounts", a)
            raise ValueError("Nieprawidłowy e-mail lub hasło.")
        if u2.get("totp"):
            if not totp:
                raise TotpRequired("Podaj 6-cyfrowy kod z aplikacji uwierzytelniającej.")
            if not security.totp_ok(u2["totp"], totp, "u:" + u2["uid"]):
                u2["fails"] = u2.get("fails", 0) + 1
                if u2["fails"] >= MAX_FAILS: u2["lock"] = int(now + LOCK_MIN * 60); u2["fails"] = 0
                store.put("accounts", a)
                raise ValueError("Nieprawidłowy kod 2FA.")
        u2["fails"] = 0; u2["lock"] = 0; u2["last_login"] = int(now)
        if _ph and not u2["pw"].startswith("scrypt$") and _ph.check_needs_rehash(u2["pw"]): u2["pw"] = hash_pw(pw)
        store.put("accounts", a); return u2["uid"]

def new_session(uid):
    sid = secrets.token_urlsafe(32); csrf = secrets.token_urlsafe(24); now = time.time()
    with _lock:
        s = {k: v for k, v in _sess().items() if v["exp"] > now}
        s[_h(sid)] = {"uid": uid, "exp": int(now + SESSION_DAYS * 86400), "csrf": csrf}
        store.put("sessions", s)
    return sid, csrf

def session(sid):
    if not sid or len(sid) > 100: return None
    v = _sess().get(_h(sid))
    if not v or v["exp"] < time.time(): return None
    u = _accts().get(v["uid"])
    return (u, v["csrf"]) if u else None

def end_session(sid):
    with _lock:
        s = _sess(); s.pop(_h(sid or ""), None); store.put("sessions", s)

def end_all_sessions(uid):
    """„Wyloguj ze wszystkich urządzeń” – usuwa każdą sesję konta. Zwraca liczbę zakończonych sesji."""
    with _lock:
        s = _sess(); keep = {k: v for k, v in s.items() if v.get("uid") != uid}
        n = len(s) - len(keep); store.put("sessions", keep); return n

# ---------- Opcjonalne 2FA (TOTP) dla użytkowników ----------
def totp_setup(uid):
    """Tworzy nowy (jeszcze nieaktywny) sekret; aktywuje go dopiero poprawny kod w totp_enable."""
    sec = security.totp_new_secret()
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u: raise ValueError("Nie ma takiego konta.")
        u["totp_pending"] = sec; store.put("accounts", a)
    return {"secret": sec, "uri": security.totp_uri(sec, (u.get("name") or "konto") + " · Luna")}

def totp_enable(uid, code):
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u or not u.get("totp_pending"): raise ValueError("Najpierw wygeneruj klucz 2FA.")
        if not security.totp_ok(u["totp_pending"], code, "u:" + uid): raise ValueError("Nieprawidłowy kod – sprawdź czas w telefonie i spróbuj ponownie.")
        u["totp"] = u.pop("totp_pending"); u["totp_at"] = int(time.time()); store.put("accounts", a)
    return True

def totp_disable(uid, pw, code):
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u or not u.get("totp"): raise ValueError("2FA nie jest włączone.")
    if not check_pw(u["pw"], str(pw or "")): raise ValueError("Nieprawidłowe hasło.")
    if not security.totp_ok(u["totp"], code, "u:" + uid): raise ValueError("Nieprawidłowy kod 2FA.")
    with _lock:
        a = _accts(); a[uid].pop("totp", None); a[uid].pop("totp_pending", None); store.put("accounts", a)
    return True

RANK = {"darmowy": 0, "podstawowa": 1, "premium": 2, "pro": 3}
PASS_DAYS = 30

def plan(u):
    """Najwyższy aktywny dostęp: miesięczny karnet (30 dni, bez odnawiania) albo Premium testera."""
    # Cennik v2: plan Podstawowa jest darmowy dla każdego konta; płatne są tylko Premium i Pro (30 dni, bez odnawiania).
    now = time.time(); best = {"plan": "podstawowa", "until": 0, "ring": None, "source": "account"}
    ps = u.get("pass") or {}
    if ps.get("until", 0) > now and ps.get("plan") in RANK: best = {"plan": ps["plan"], "until": ps["until"], "ring": None, "source": "pass"}
    st = testers.status(u.get("tester")) if u.get("tester") else {}
    if st.get("granted"):
        if RANK["premium"] > RANK[best["plan"]]: best = {"plan": "premium", "until": st["until"], "ring": st["ring"], "source": "tester"}
        else: best["ring"] = st["ring"]
    return best

def grant_pass(uid, plan_id, months=1, by="moderator"):
    """Moderator przyznaje/przedłuża miesięczny dostęp. Ten sam plan – przedłużenie od daty wygaśnięcia; inny – od teraz."""
    if plan_id not in ("podstawowa", "premium", "pro"): raise ValueError("Nieznany plan.")
    months = max(1, min(12, int(months or 1)))
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u: raise KeyError("not found")
        now = time.time(); ps = u.get("pass") or {}
        start = ps["until"] if ps.get("plan") == plan_id and ps.get("until", 0) > now else now
        u["pass"] = {"plan": plan_id, "until": int(start + months * PASS_DAYS * 86400), "granted_at": int(now), "by": by, "reminded": []}
        store.put("accounts", a); return u["pass"]

def grant_item(uid, ref):
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u: raise KeyError("not found")
        its = u.setdefault("items", [])
        if ref not in its: its.append(ref)
        store.put("accounts", a); return its

def revoke_pass(uid):
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u: raise KeyError("not found")
        u["pass"] = {}; store.put("accounts", a)

def expiring(days_lo, days_hi, tag):
    """Konta, którym dostęp wygasa w oknie (dni) i które nie dostały jeszcze przypomnienia `tag`. Oznacza jako wysłane."""
    now = time.time(); out = []
    with _lock:
        a = _accts(); ch = False
        for u in a.values():
            ps = u.get("pass") or {}
            if not ps.get("until"): continue
            left = (ps["until"] - now) / 86400
            if days_lo <= left < days_hi and tag not in ps.get("reminded", []):
                ps.setdefault("reminded", []).append(tag); out.append((u["uid"], ps["plan"], ps["until"])); ch = True
        if ch: store.put("accounts", a)
    return out

def public(u):
    return {"uid": u["uid"], "email": u["email"], "name": u["name"], "verified": u["verified"], "created": u["created"],
            "adult": bool(u.get("adult")), "adult_at": u.get("adult_at", 0), "tester": u.get("tester", ""), "items": u.get("items", []), **plan(u),
            "email_verification_available": notify.email_enabled(), "totp": bool(u.get("totp"))}

def link_tester(uid, code):
    code = str(code or "").strip().upper()[:12]
    if not testers.status(code).get("found"): raise ValueError("Nie znaleziono takiego kodu testera.")
    with _lock:
        a = _accts()
        if any(x.get("tester") == code and x["uid"] != uid for x in a.values()): raise ValueError("Ten kod jest już przypisany do innego konta.")
        a[uid]["tester"] = code; store.put("accounts", a); return a[uid]

def export(uid):
    u = dict(_accts().get(uid) or {})
    for k in ("pw", "vtok", "fails", "lock", "totp", "totp_pending"): u.pop(k, None)
    t = testers._all().get(u.get("tester", ""), None)
    if t: t = {k: v for k, v in t.items() if k != "ip"}
    return {"exported_at": int(time.time()), "account": u, "tester_application": t,
            "note": "Eksport danych konta Luna (RODO art. 15/20). Rozmowy z Luną i profil (imię, awatar) są przechowywane tylko na Twoim urządzeniu."}

def delete(uid, pw=None, check=True):
    """Usuwa konto i dane osobowe (e-mail, imię, hasło, sesje, zgłoszenie testera, zapis na e-maile). Jedno kliknięcie + potwierdzenie w UI."""
    with _lock:
        a = _accts(); u = a.get(uid)
        if not u: raise ValueError("Nie ma takiego konta.")
        if check and pw is not None and not check_pw(u["pw"], str(pw or "")): raise ValueError("Nieprawidłowe hasło.")
        a.pop(uid); store.put("accounts", a)
        s = {k: v for k, v in _sess().items() if v["uid"] != uid}; store.put("sessions", s)
    try:
        if u.get("tester"): testers.delete(u["tester"])
        es = store.get("email_subs", {}) or {}
        es2 = {k: v for k, v in es.items() if str(v.get("email", "")).lower() != str(u.get("email", "")).lower()}
        if len(es2) != len(es): store.put("email_subs", es2)
    except Exception: pass
    return True

def admin_list():
    return [{"uid": u["uid"], "email": u["email"], "name": u["name"], "verified": u["verified"], "created": u["created"],
             "adult": bool(u.get("adult")), "adult_at": u.get("adult_at", 0), "age": age.age_of(u["dob"]) if u.get("dob") else None,
             "plan": plan(u)["plan"], "until": plan(u)["until"], "source": plan(u)["source"], "locked": u.get("lock", 0) > time.time()} for u in sorted(_accts().values(), key=lambda x: -x["created"])]
