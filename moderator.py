"""Panel admina (strona + aplikacja) – konto właściciela z rolą admin, 2FA (TOTP) na urządzenie, przełączniki systemu
(tryb serwisowy 503 + Retry-After), przełączniki funkcji, wspólna kolejka moderacji, użytkownicy, treści, komunikaty,
prawdziwe statystyki i dziennik audytu. Tożsamość publiczna zawsze: „Moderator” / „Zespół Luny” – nigdy prawdziwe dane."""
import hashlib, hmac, html, io, json, os, re, secrets, threading, time, unicodedata
from urllib.parse import urlparse, parse_qs
import store, security

_lock = threading.RLock()
ROOT = os.path.dirname(os.path.abspath(__file__))
PANEL_DIR = os.path.join(ROOT, "modpanel")
MOD_NAME = "Zespół Luny · Moderator"
DEVICE_DAYS = 30
TOKEN_TTL = 30 * 60
REAUTH_GRACE = 5 * 60
# haki ustawiane przez server.py
MINT = None          # () -> token panelu producenta (X-Admin-Token), żeby działały istniejące /api/admin/*
TOTP_ENV = None      # () -> sekret TOTP z env (LUNA_ADMIN_TOTP_SECRET) albo ""

# ---------- konto właściciela (rola admin po stronie serwera) ----------
def admin_nick(): return unicodedata.normalize("NFC", os.getenv("LUNA_ADMIN_NICK", "").strip())[:24]
def _pw_hash():
    h = os.getenv("LUNA_ADMIN_PASSWORD_HASH", "").strip()
    return h if h.startswith("$argon2") else ""
def configured(): return bool(admin_nick() and _pw_hash())

_VS = dict.fromkeys(map(ord, "\ufe0f\ufe0e\u200d\u200b\u200c\u2060"), None)
def login_key(n):
    """Porównanie nicku przy logowaniu: NFC, bez selektorów wariantu (❤ = ❤️), bez spacji, bez wielkości liter."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", str(n or "")).translate(_VS)).casefold()

_HOMO = str.maketrans({"а": "a", "в": "b", "с": "c", "е": "e", "ё": "e", "һ": "h", "н": "h", "і": "i", "ї": "i", "ј": "j", "к": "k", "м": "m",
                       "о": "o", "р": "p", "т": "t", "у": "y", "х": "x", "ь": "b", "п": "n", "и": "u", "ս": "u", "ո": "n", "ı": "i", "ɩ": "i",
                       "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
                       "0": "o", "1": "i", "!": "i", "|": "i", "l": "i", "3": "e", "4": "a", "@": "a", "5": "s", "$": "s", "7": "t", "8": "b", "6": "b"})
def skeleton(n):
    s = unicodedata.normalize("NFKD", str(n or "")).casefold()
    s = "".join(c for c in s if not unicodedata.combining(c)).translate(_HOMO)
    return re.sub(r"[^a-z]", "", s)
_RES_RE = re.compile(r"h+u+b+i+n+a+t+o+r+")
def reserved(n):
    """Nick właściciela i podobne (homoglify, cyfry, wielkość liter) są zarezerwowane."""
    return bool(_RES_RE.search(skeleton(n)))

def _accts():
    import accounts; return accounts._accts()
def admin_uid():
    if not configured(): return ""
    return next((u["uid"] for u in _accts().values() if u.get("role") == "admin"), "")
# Role (elastycznie pod przyszły lżejszy „Panel moderatora” dla osób mianowanych przez admina – jeszcze NIEaktywne):
# admin = właściciel, pełna władza; moderator = przyszła rola z wąskim zestawem uprawnień. Dziś panel wpuszcza tylko admina.
ROLE_PERMS = {
    "admin": {"*"},
    "moderator": {"queue", "chat", "users.basic", "shop", "support"},   # szkic – do zatwierdzenia przez właściciela
}
ACTIVE_ROLES = ("admin",)   # dopisz "moderator", gdy właściciel zatwierdzi specyfikację
def role_of(u): return (u or {}).get("role") or ""
def can(u, perm):
    r = role_of(u)
    if r not in ACTIVE_ROLES or r not in ROLE_PERMS: return False
    if r == "admin" and not configured(): return False
    P = ROLE_PERMS[r]; return "*" in P or perm in P
def is_admin_user(u): return bool(u and role_of(u) == "admin" and configured())
def is_admin_uid(uid): return bool(uid) and uid == admin_uid()
def author_is_admin(ak): return bool(ak) and str(ak).startswith("u:") and is_admin_uid(str(ak)[2:])

BIO = ("Zaczęło się od jednej aplikacji i jednej szalonej myśli: a co, gdyby głos mógł zmieniać więcej? ⚡ Pilnuję, żeby Luna była miejscem "
       "z klasą, a najlepsze komentarze dostają ode mnie serduszko. Mustang w awatarze nie jest przypadkiem: wolny, uparty i zawsze do przodu. "
       "Wierzę, że wyjdzie z tego coś wielkiego.")
INTERESTS = ["Głos", "AI", "moda", "bitwy agentek"]
SHARE_LINK = "https://luna-voice-coach.onrender.com/?utm_source=profile&utm_medium=share&utm_campaign=polecam"
AVATAR = {"poster": "/mod-av/mustang-512.jpg", "webp": "/mod-av/mustang-512.webp", "webm": "/mod-av/mustang-512.webm", "mp4": "/mod-av/mustang-512.mp4"}

def ensure_admin():
    """Przy starcie: konto właściciela istnieje, ma rolę admin, hasło z LUNA_ADMIN_PASSWORD_HASH i zarezerwowany nick."""
    if not configured(): return None
    import accounts, userprof
    nick, h, now = admin_nick(), _pw_hash(), int(time.time())
    with accounts._lock:
        A = accounts._accts()
        u = next((x for x in A.values() if x.get("role") == "admin"), None)
        if not u:
            k = login_key(nick)
            u = next((x for x in A.values() if login_key(x.get("name")) == k), None)
        if not u:
            uid = secrets.token_hex(8)
            u = {"uid": uid, "email": "moderator@luna.invalid", "created": now, "tester": "", "fails": 0, "lock": 0}
            A[uid] = u
        u.update({"role": "admin", "pw": h, "name": nick, "verified": True, "adult": True, "adult_at": u.get("adult_at") or now,
                  "adult_confirmed": True, "adult_confirmed_at": u.get("adult_confirmed_at") or now, "terms_at": u.get("terms_at") or now})
        store.put("accounts", A)
        uid = u["uid"]
    with userprof._lock:
        P = userprof._P(); r = P.get(uid) or {}
        first = not r.get("mod_seeded")
        r["nick"] = nick
        if first:
            r.update({"bio": BIO, "interests": list(INTERESTS), "links": [SHARE_LINK], "show_links": True, "public": True, "show_bio": True, "show_interests": True, "mod_seeded": now})
        elif not r.get("links"): r["links"] = [SHARE_LINK]; r["show_links"] = True
        P[uid] = r; store.put("user_profiles", P)
    return uid

def find_admin_by_login(ident):
    """Logowanie nickiem tylko dla konta właściciela (zwykli użytkownicy logują się e-mailem)."""
    if not configured() or "@" in str(ident or ""): return None
    if login_key(ident) != login_key(admin_nick()): return None
    return next((u for u in _accts().values() if u.get("role") == "admin"), None)

# ---------- przełączniki systemu i funkcji ----------
FEATURES = {"register": "Rejestracja", "battles": "Bitwy", "generator": "Generator", "chat": "Czat / DM", "wall": "Wrzucanie na ścianę", "shop": "Butik i płatności"}
SCOPES = {"site": "Strona", "app": "Aplikacja", "system": "Cały system"}
_DEF = {"site": {"on": True}, "app": {"on": True}, "system": {"on": True}, "features": {k: True for k in FEATURES}, "msg": "", "until": 0}
_cache = {"t": 0, "v": None}
def switches(fresh=False):
    now = time.time()
    if fresh or _cache["v"] is None or now - _cache["t"] > 10:
        v = store.get("mod_switches", None) or {}
        S = json.loads(json.dumps(_DEF))
        for k in SCOPES:
            if isinstance(v.get(k), dict): S[k]["on"] = bool(v[k].get("on", True))
        S["features"].update({k: bool(x) for k, x in (v.get("features") or {}).items() if k in FEATURES})
        S["msg"] = str(v.get("msg") or "")[:300]; S["until"] = int(v.get("until") or 0)
        _cache.update(t=now, v=S)
    S = _cache["v"]
    if S["until"] and S["until"] < now and not all(S[k]["on"] for k in SCOPES):   # zaplanowany powrót: samo się włącza
        S2 = json.loads(json.dumps(S))
        for k in SCOPES: S2[k]["on"] = True
        S2["until"] = 0; _save_switches(S2); return S2
    return S
def _save_switches(S):
    store.put("mod_switches", S); _cache.update(t=time.time(), v=S)

APP_HDR = re.compile(r"lunamowijakjest", re.I)
def is_app(h, q):
    if (q.get("source") or [""])[0] in ("twa", "pwa") or (q.get("app") or [""])[0] == "1": return True
    if h._cookie("luna_app") == "1": return True
    if APP_HDR.search(h.headers.get("X-Requested-With") or ""): return True
    return (h.headers.get("Referer") or "").startswith("android-app://")

# ścieżki, które działają zawsze (panel, logowanie, admin, płatności – webhook, zdrowie)
ALWAYS = ("/api/mod/", "/api/admin/", "/api/account/login", "/api/account/me", "/api/account/logout", "/api/health", "/api/stripe/webhook",
          "/fonts/", "/mod-av/", "/favicon", "/robots.txt", "/.well-known/", "/soft.css", "/mod-ring.css", "/sec-client.js")
FEAT_POST = (("register", ("/api/account/signup",)), ("battles", ("/api/battles/",)),
             ("generator", ("/api/agent/generate", "/api/agent/video", "/api/agent/profile/own")),
             ("chat", ("/api/dm", "/api/battles/chat")), ("wall", ("/api/wall/post", "/api/wall/edit", "/api/me/avatar", "/api/avatar/upload")),
             ("shop", ("/api/pay/checkout", "/api/butik")))
FEAT_MSG = {"register": "Rejestracja ma chwilę przerwy – Luna ustawia krzesła dla nowych gości. Wróć za moment 💚",
            "battles": "Bitwy mają przerwę techniczną – agentki poprawiają szminkę przed kolejną rundą 💄",
            "generator": "Generator odpoczywa – pędzle się suszą. Spróbuj trochę później 🎨",
            "chat": "Czat ma krótką przerwę – Luna odkurza dymki. Zaraz wracamy 💬",
            "wall": "Wrzucanie na ścianę jest chwilowo wstrzymane – wieszamy nowe ramki 🖼️",
            "shop": "Butik jest chwilowo zamknięty – Luna liczy cekiny. Płatności wrócą wkrótce 🛍️"}
def feature_for(path):
    for f, ps in FEAT_POST:
        if any(path == p or path.startswith(p if p.endswith("/") else p + "/") or path == p for p in ps): return f
    return None

_pp = []
def panel_prefix():
    if _pp: return _pp[0]
    _pp.append(_panel_prefix()); return _pp[0]
def _panel_prefix():
    """Nieodgadywalna ścieżka panelu: LUNA_MOD_PATH albo HMAC sekretu (stała między restartami)."""
    v = re.sub(r"[^a-z0-9-]", "", os.getenv("LUNA_MOD_PATH", "").strip().lower())
    if len(v) >= 12: return "/" + v
    seed = (_pw_hash() or os.getenv("LUNA_ADMIN_CODE_HASH", "") or os.getenv("LUNA_ADMIN_CODE", "") or "")
    if not seed:
        seed = store.get("mod_seed", "") or ""
        if not seed: seed = secrets.token_hex(16); store.put("mod_seed", seed)
    return "/m-" + hmac.new(seed.encode(), b"luna-moderator-panel", hashlib.sha256).hexdigest()[:20]

def admin_bypass(h):
    """Właściciel zalogowany zwykłym kontem + zaufane urządzenie (po 2FA) widzi stronę także w trybie serwisowym."""
    try:
        a = h._acct()
        return bool(a and is_admin_user(a[0]) and device_ok(h, a[0]["uid"]))
    except Exception: return False

def gate(h, method):
    """Zwraca True, gdy żądanie zostało obsłużone (503). Wywoływane na początku do_GET/do_POST."""
    S = switches()
    down_any = not all(S[k]["on"] for k in SCOPES)
    feat_off = method == "POST" and not all(S["features"].values())
    u = urlparse(h.path); p = u.path
    if not down_any and not feat_off: return False
    pref = panel_prefix()
    if p == pref or p.startswith(pref + "/") or p.startswith(ALWAYS): return False
    if admin_bypass(h): return False
    q = parse_qs(u.query)
    if down_any:
        app = is_app(h, q)
        if not S["system"]["on"] or (app and not S["app"]["on"]) or (not app and not S["site"]["on"]):
            return maintenance(h, S, p)
    if feat_off:
        f = feature_for(p)
        if f and not S["features"].get(f, True):
            return h._json({"error": FEAT_MSG[f], "paused": f}, 503)
    return False

def maintenance(h, S, p):
    ra = max(60, min(86400, S["until"] - int(time.time()))) if S["until"] else 600
    if p.startswith("/api/"):
        h.send_response(503); h.send_header("Retry-After", str(ra))
        b = json.dumps({"error": "Luna poprawia makijaż, zaraz wracamy 💄", "maintenance": True, "retry_after": ra}, ensure_ascii=False).encode()
        h.send_header("Content-Type", "application/json; charset=utf-8"); h.send_header("Content-Length", str(len(b))); h.send_header("Cache-Control", "no-store")
        h.end_headers(); h.wfile.write(b); return True
    msg = html.escape(S["msg"] or "Dopracowujemy kilka rzeczy, żeby było jeszcze piękniej. Dziękujemy za cierpliwość 💚")
    when = ""
    if S["until"]:
        when = "<p class=w>Planowany powrót: <b>" + time.strftime("%d.%m.%Y, %H:%M", time.localtime(S["until"])) + "</b></p>"
    b = MAINT_HTML.replace("{MSG}", msg).replace("{WHEN}", when).encode()
    h.send_response(503); h.send_header("Retry-After", str(ra)); h.send_header("Content-Type", "text/html; charset=utf-8")
    h.send_header("Content-Length", str(len(b))); h.send_header("Cache-Control", "no-store"); h.send_header("X-Robots-Tag", "noindex")
    h.end_headers(); h.wfile.write(b); return True

MAINT_HTML = """<!doctype html><html lang=pl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<meta name=robots content=noindex><title>Luna – przerwa techniczna</title><link rel=stylesheet href="/soft.css">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 50% 30%,#2a1610,#0b0705 70%);color:#f6e9da;font-family:Nunito,system-ui,sans-serif;text-align:center;padding:24px}
.c{max-width:520px;background:rgba(255,255,255,.05);border:1px solid rgba(240,160,64,.25);border-radius:28px;padding:34px 26px;box-shadow:0 20px 60px rgba(0,0,0,.45)}
.e{font-size:64px;display:inline-block;animation:b 2.4s ease-in-out infinite}@keyframes b{50%{transform:translateY(-8px) rotate(-6deg)}}
@media (prefers-reduced-motion:reduce){.e{animation:none}}h1{font-family:"Playfair Display",serif;font-size:28px;margin:10px 0}
p{line-height:1.55;color:#e9d6c2}.w{color:#f0a040}.s{font-size:13px;opacity:.7;margin-top:18px}</style></head>
<body><main class=c><div class=e aria-hidden=true>💄</div><h1>Luna poprawia makijaż, zaraz wracamy</h1><p>{MSG}</p>{WHEN}
<p class=s>Luna is touching up her make-up – we'll be right back. · Kod 503, spokojnie: to tylko pudrowanie noska.</p></main></body></html>"""

# ---------- zaufane urządzenia (2FA raz na 30 dni) ----------
def _dh(t): return hashlib.sha256(("mdev:" + str(t)).encode()).hexdigest()
def device_ok(h, uid):
    t = h._cookie("luna_mdev")
    if not t or len(t) > 100: return False
    d = (store.get("mod_devices", {}) or {}).get(_dh(t))
    return bool(d and d.get("uid") == uid and d.get("exp", 0) > time.time())
def device_new(h, uid):
    t = secrets.token_urlsafe(32); now = int(time.time())
    with _lock:
        D = {k: v for k, v in (store.get("mod_devices", {}) or {}).items() if v.get("exp", 0) > now}
        D[_dh(t)] = {"uid": uid, "exp": now + DEVICE_DAYS * 86400, "t": now, "ua": (h.headers.get("User-Agent") or "")[:60]}
        store.put("mod_devices", D)
    h._cookies = getattr(h, "_cookies", []) + [f"luna_mdev={t}; Path=/; Max-Age={DEVICE_DAYS * 86400}; HttpOnly; Secure; SameSite=Strict"]
def device_forget(h, all_=False, uid=""):
    t = h._cookie("luna_mdev")
    with _lock:
        D = store.get("mod_devices", {}) or {}
        D = {k: v for k, v in D.items() if not (all_ and v.get("uid") == uid) and k != _dh(t)}
        store.put("mod_devices", D)
    h._cookies = getattr(h, "_cookies", []) + ["luna_mdev=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"]

def totp_secret(u):
    e = TOTP_ENV() if TOTP_ENV else ""
    return e or (u or {}).get("mod_totp", "")

# ---------- sesje panelu: token (X-Admin-Token) + CSRF na token ----------
_sess = {}   # token -> {"uid", "csrf", "exp", "reauth"}
def _mint(uid):
    tok = MINT(); now = time.time()
    with _lock:
        for k in [k for k, v in _sess.items() if v["exp"] < now]: _sess.pop(k, None)
        _sess[tok] = {"uid": uid, "csrf": secrets.token_urlsafe(24), "exp": now + TOKEN_TTL, "reauth": 0}
    return tok, _sess[tok]["csrf"]
def _ctx(h):
    """Pełna autoryzacja akcji panelu: konto admin + zaufane urządzenie + token + CSRF."""
    a = h._acct()
    if not a or not is_admin_user(a[0]): return None
    uid = a[0]["uid"]
    if not device_ok(h, uid): return None
    tok = h.headers.get("X-Admin-Token") or ""
    s = _sess.get(tok)
    if not s or s["uid"] != uid or s["exp"] < time.time(): return None
    if h.command == "POST" and not hmac.compare_digest(h.headers.get("X-CSRF-Token") or "", s["csrf"]): return None
    s["exp"] = time.time() + TOKEN_TTL
    return {"uid": uid, "u": a[0], "tok": tok, "s": s}
def _reauth(c, data):
    """Akcje krytyczne (wyłączniki, bany, masowe wiadomości) wymagają świeżego kodu 2FA (ważność 5 min)."""
    if time.time() - c["s"]["reauth"] < REAUTH_GRACE: return True
    if security.totp_ok(totp_secret(c["u"]), data.get("otp"), "mod-reauth:" + c["uid"]):
        c["s"]["reauth"] = time.time(); return True
    return False

# ---------- audyt ----------
def audit(h, action, target="", detail=""):
    with _lock:
        L = store.get("mod_audit", []) or []
        L.append({"t": int(time.time()), "who": "Moderator", "action": str(action)[:60], "target": str(target)[:80], "detail": security.redact(str(detail))[:240],
                  "ip": security.ip_hash(h._ip()) if h else ""})
        store.put("mod_audit", L[-2000:])
    try: security.audit("mod " + str(action), h._ip() if h else "", str(target)[:60])
    except Exception: pass

# ---------- wiadomość do użytkownika (Skrzynka) ----------
ACT_PL = {"warn": "Ostrzeżenie", "strike": "Poważne naruszenie (strike)", "temp_block": "Czasowa blokada", "ban": "Blokada konta", "unban": "Zdjęcie blokady",
          "remove": "Usunięcie treści", "approve": "Treść zaakceptowana", "unstrike": "Cofnięcie naruszenia"}
def notify_user(uid, action, reason, extra=""):
    if not uid: return
    try:
        import inbox
        body = f"{ACT_PL.get(action, action)}. Powód: {reason or 'naruszenie regulaminu'}. {extra}".strip()
        if action in ("warn", "strike", "temp_block", "ban"):
            body += " Zasada 3 poważnych naruszeń: po trzecim konto może zostać zablokowane na stałe. Możesz się odwołać w Pomocy."
        inbox.deliver(uid, "important", title="🛡️ Wiadomość od moderatora", body=body + "\n— " + MOD_NAME, link="/problemy.html")
    except Exception: pass

# ---------- strike'i: moduł reports (Zgłoś 🚩) gdy jest, inaczej zgodny zapis rp_acct ----------
def _rp():
    try:
        import reports; return reports
    except Exception: return None
MAX_STRIKES = 3
def standing(uid):
    r = _rp()
    if r: return r.standing(uid)
    a = store.get("rp_acct:" + uid, {}) or {}; now = time.time(); bu = int(a.get("block_until", 0) or 0)
    return {"strikes": len(a.get("strikes", [])), "max": MAX_STRIKES, "banned": bool(a.get("banned")), "block_until": bu if bu > now else 0, "warns": int(a.get("warns", 0)),
            "history": [{"t": x["t"], "action": x["action"], "cat": x.get("cat", "other")} for x in a.get("history", [])][-20:][::-1]}
def sanction(uid, action, days=7, reason=""):
    import social
    if action in ("unban",):
        r = _rp()
        if r: r.lift(uid)
        else:
            with _lock:
                a = store.get("rp_acct:" + uid, {}) or {}; a["banned"] = 0; a["block_until"] = 0
                a.setdefault("history", []).append({"t": int(time.time()), "action": "lift", "cat": "other"}); store.put("rp_acct:" + uid, a)
        with social._lock: B = social._bans(); B.discard("u:" + uid); store.put("social_bans", sorted(B))
        return standing(uid)
    if action == "unstrike":
        r = _rp()
        if r: return r.unstrike(uid)
        with _lock:
            a = store.get("rp_acct:" + uid, {}) or {}
            if a.get("strikes"): a["strikes"].pop()
            store.put("rp_acct:" + uid, a)
        return standing(uid)
    serious = action in ("strike", "temp_block", "ban")
    act = {"strike": "warn"}.get(action, action)
    r = _rp(); cid = "mod-" + secrets.token_hex(4)
    if r: r._sanction(uid, "u:" + uid, act, "other", serious, days, cid)
    else:
        now = int(time.time())
        with _lock:
            a = store.get("rp_acct:" + uid, {}) or {}; S = a.setdefault("strikes", [])
            if act == "warn": a["warns"] = int(a.get("warns", 0)) + 1
            if serious: S.append({"t": now, "cat": "other", "case": cid})
            if act == "temp_block": a["block_until"] = max(int(a.get("block_until", 0) or 0), now + max(1, min(int(days or 7), 90)) * 86400)
            final = act == "ban" or len(S) >= MAX_STRIKES
            if final: a["banned"] = now
            a.setdefault("history", []).append({"t": now, "action": "ban" if final else act, "cat": "other", "serious": serious, "case": cid})
            store.put("rp_acct:" + uid, a)
        if final:
            with social._lock: B = social._bans(); B.add("u:" + uid); store.put("social_bans", sorted(B))
    return standing(uid)
def blocked_msg(uid):
    """Blokada zapisu (gdy moduł reports jeszcze jej nie egzekwuje)."""
    if not uid or _rp(): return None
    st = standing(uid)
    if st["banned"]: return "Twoje konto jest zablokowane przez moderację. Możesz się odwołać w Pomocy."
    if st["block_until"]: return "Twoje konto ma czasową blokadę do " + time.strftime("%d.%m.%Y %H:%M", time.localtime(st["block_until"])) + "."
    return None

# ---------- statystyki (tylko prawdziwe liczby) ----------
def _midnight():
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        d = datetime.now(ZoneInfo("Europe/Warsaw")); return int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    except Exception: return int(time.time() // 86400 * 86400)
def stats():
    A = _accts(); m = _midnight(); out = {"users": len([u for u in A.values() if u.get("role") != "admin"]),
                                          "signups_today": sum(1 for u in A.values() if u.get("created", 0) >= m and u.get("role") != "admin")}
    try:
        import battles; out["active_battles"] = len(battles._all(battles.tick()))
    except Exception: out["active_battles"] = None
    try: out["open_reports"] = len(queue())
    except Exception: out["open_reports"] = None
    try:
        import tickets, support
        out["tickets"] = tickets.admin_list().get("new", 0) + sum(1 for s in support.admin_list() if not s.get("closed"))
    except Exception: out["tickets"] = None
    out["persistent"] = store.status()["persistent"]
    return out

# ---------- wspólna kolejka moderacji ----------
def _nick(uid):
    try:
        import userprof; return userprof.get(uid)["nick"] or "użytkownik"
    except Exception: return "użytkownik"
def _uid_ak(ak): return ak[2:] if str(ak or "").startswith("u:") else ""
def queue():
    import social, avatars, battles, agentvideo, inbox
    Q = []
    r = _rp()
    if r:
        try:
            for c in r.admin_list("open")["items"]:
                Q.append({"src": "case", "id": c["id"], "kind": "Zgłoszenie 🚩 · " + c["type"], "text": str(c.get("snap") or "")[:300], "t": c["u"],
                          "uid": "", "who": c.get("owner_short") or "gość", "n": c["n"], "acts": ["dismiss", "remove", "warn", "temp_block", "ban"]})
        except Exception: pass
    SA = social.admin_list()
    for p in SA["posts"]:
        Q.append({"src": "post", "id": p["id"], "kind": "Wpis na ścianie" + (" · zgłoszony" if p.get("reports") else " · czeka"), "text": p.get("text", "")[:300],
                  "img": p.get("img_url"), "t": p["t"], "uid": _uid_ak(p.get("author")), "ak": p.get("author"), "who": p.get("nick", ""), "n": p.get("reports", 0),
                  "acts": ["approve", "remove", "warn", "strike", "temp_block", "ban"]})
    for c in SA["comments"]:
        Q.append({"src": "cmt", "id": c["id"], "kind": "Komentarz" + (" · zgłoszony" if c.get("reports") else " · czeka"), "text": c.get("text", "")[:300],
                  "t": c["t"], "uid": _uid_ak(c.get("author")), "ak": c.get("author"), "who": c.get("nick", ""), "n": c.get("reports", 0),
                  "acts": ["approve", "remove", "warn", "strike", "temp_block", "ban"]})
    for a in avatars.admin_list():
        uid = a.get("uid", "")
        Q.append({"src": "avatar", "id": a.get("id", ""), "kind": "Awatar" + (" · zgłoszony" if a.get("kind") == "report" else " · nowy"), "text": a.get("reason", "") or "",
                  "img": a.get("img") or a.get("url"), "t": a.get("t", 0), "uid": "", "short": uid, "who": a.get("nick") or uid, "acts": ["approve", "remove", "ban"]})
    try:
        B = battles.admin_list()
        for e in B["entries"]:
            if e["status"] == "pending" or e.get("reports"):
                Q.append({"src": "battle", "id": e["id"], "kind": "Agentka do bitwy" + (" · zgłoszona" if e.get("reports") else " · czeka"), "text": e.get("name", ""),
                          "img": e.get("img"), "t": e.get("t", 0), "uid": e.get("uid", ""), "who": e.get("name", ""), "acts": ["approve", "remove", "warn", "strike", "ban"]})
        for m in B["chat_flagged"]:
            if not m.get("hidden"):
                Q.append({"src": "btchat", "id": str(m["id"]), "bid": m["bid"], "kind": "Czat bitwy · zgłoszony", "text": m.get("text", "")[:300], "t": m.get("t", 0),
                          "uid": _uid_ak(m.get("ak")), "ak": m.get("ak"), "who": m.get("nick", ""), "acts": ["approve", "remove", "ban"]})
    except Exception: pass
    for j in agentvideo.admin_list():
        if j["status"] == "review":
            Q.append({"src": "video", "id": j["id"], "kind": "Film agentki · scena do sprawdzenia", "text": str(j.get("custom") or j.get("scene") or ""), "t": j["t"],
                      "uid": "", "who": j.get("u", ""), "acts": ["approve", "remove"]})
    try:
        for d in inbox.admin_reports():
            if d["status"] in ("open", "new", None, ""):
                Q.append({"src": "dm", "id": d["id"], "kind": "Czat prywatny · zgłoszenie", "text": (d.get("message") or "") + " · powód: " + str(d.get("reason") or ""),
                          "t": d["t"], "uid": "", "who": d.get("reported", ""), "acts": ["dismiss", "remove", "ban"]})
    except Exception: pass
    try:
        import profiles
        rev = set(store.get("mod_reviewed", []) or [])
        for pid, pr in profiles._P().items():
            if pr.get("public") and not pr.get("hidden") and pid not in rev and pr.get("t", pr.get("created", time.time())) > time.time() - 14 * 86400:
                Q.append({"src": "agent", "id": pid, "kind": "Nowa agentka (profil)", "text": (pr.get("name", "") + " – " + pr.get("bio", ""))[:300], "t": pr.get("t", 0),
                          "uid": pr.get("uid", ""), "who": _nick(pr.get("uid", "")), "img": "/agentka.html?id=" + pid, "link": True, "acts": ["approve", "remove", "warn", "strike", "ban"]})
    except Exception: pass
    try:
        import forms18
        for f in forms18.admin_list():
            if f.get("kind") == "casting" and f.get("decision") in (None, "", "new"):
                Q.append({"src": "casting", "id": f["id"], "kind": "Casting · zgłoszenie", "text": str(f.get("nick") or f.get("alias") or "anonimowo") + " · weryfikacja: " + f.get("status", ""),
                          "t": f.get("t", 0), "uid": "", "who": str(f.get("nick") or "anonim"), "acts": ["approve", "remove"]})
    except Exception: pass
    for x in Q:
        if x.get("uid"): x["who"] = x.get("who") or _nick(x["uid"]); x["standing"] = standing(x["uid"])
        x.pop("ak", None) if not x.get("uid") else None
    return sorted(Q, key=lambda x: -(x.get("t") or 0))

def queue_act(h, d):
    import social, avatars, battles, agentvideo, inbox, userprof
    src, id_, act = str(d.get("src", "")), str(d.get("id", ""))[:80], str(d.get("action", ""))
    reason = re.sub(r"[<>\x00-\x1f]", "", str(d.get("reason") or ""))[:300]
    days = max(1, min(90, int(d.get("days") or 7)))
    uid = ""
    if src == "case":
        r = _rp()
        if not r: raise ValueError("Moduł zgłoszeń niedostępny.")
        r.decide(id_, act, days=days, note=reason); return {"ok": True}
    if src in ("post", "cmt"):
        L = social._posts() if src == "post" else store.get("comments", []) or []
        x = next((i for i in L if i["id"] == id_), None)
        if not x: raise KeyError(id_)
        uid = _uid_ak(x.get("author"))
        social.moderate(src, id_, "approve" if act == "approve" else "hide")
        try: inbox.on_moderation(src, x, "approve" if act == "approve" else "reject")
        except Exception: pass
    elif src == "avatar":
        short = str(d.get("short", ""))[:8]
        ou = userprof.uid_by_short(short)
        if id_.startswith("ua-") and ou: userprof.moderate_avatar(ou, act == "approve")
        if act == "approve": avatars.dismiss(id_)
        else: avatars.block(short, True); avatars.dismiss(id_)
        uid = ou or ""
    elif src == "battle":
        E = next((e for e in battles._entries() if e["id"] == id_), None)
        uid = (E or {}).get("uid", "")
        battles.admin_action({"action": "approve" if act == "approve" else "remove", "id": id_})
    elif src == "btchat":
        battles.admin_action({"action": "chat_restore" if act == "approve" else ("chat_ban" if act == "ban" else "chat_delete"), "bid": d.get("bid"), "mid": id_})
    elif src == "video":
        agentvideo.admin_action(id_, "approve" if act == "approve" else "reject")
    elif src == "dm":
        inbox.admin_report_act(id_, act if act in ("dismiss", "remove", "ban") else "dismiss")
    elif src == "agent":
        import profiles
        r = profiles._P().get(id_); uid = (r or {}).get("uid", "")
        if act != "approve": profiles.admin(id_, "hide")
        with _lock:
            R = set(store.get("mod_reviewed", []) or []); R.add(id_); store.put("mod_reviewed", sorted(R)[-5000:])
    elif src == "casting":
        import forms18
        forms18.decide(id_, "accepted" if act == "approve" else "rejected")
    else: raise ValueError("Nieznane źródło.")
    res = {"ok": True}
    if uid and act in ("warn", "strike", "temp_block", "ban"):
        res["standing"] = sanction(uid, act, days, reason)
    if uid and act in ("remove", "warn", "strike", "temp_block", "ban"):
        notify_user(uid, act, reason, "Dotyczy: " + {"post": "wpis na ścianie", "cmt": "komentarz", "avatar": "awatar", "battle": "agentka w bitwie", "agent": "profil agentki"}.get(src, "treść") + ".")
    return res

# ---------- użytkownicy ----------
def users(q=""):
    import accounts, userprof, partners
    k = login_key(q); out = []
    P = userprof._P()
    for u in sorted(_accts().values(), key=lambda x: -x.get("created", 0)):
        nick = (P.get(u["uid"]) or {}).get("nick") or u.get("name", "")
        if k and k not in login_key(nick): continue
        pl = accounts.plan(u)
        out.append({"uid": u["uid"], "nick": nick, "plan": pl["plan"], "until": pl["until"], "source": pl["source"], "created": u.get("created", 0),
                    "admin": u.get("role") == "admin", "partner": partners.is_partner(u["uid"]), "model": is_model_user(u), "adult": bool(u.get("adult_confirmed_at") or u.get("adult")), "standing": standing(u["uid"]),
                    "override": bool((u.get("pass") or {}).get("by") == "moderator-override")})
        if len(out) >= 60: break
    return out

def user_act(h, d):
    import accounts, partners
    uid = str(d.get("uid", ""))[:16]; act = str(d.get("action", ""))
    u = _accts().get(uid)
    if not u: raise KeyError(uid)
    if u.get("role") == "admin": raise ValueError("Konta admina nie da się tu zmieniać.")
    reason = re.sub(r"[<>\x00-\x1f]", "", str(d.get("reason") or ""))[:300]
    if act in ("warn", "strike", "temp_block", "ban", "unban", "unstrike"):
        st = sanction(uid, act, int(d.get("days") or 7), reason); notify_user(uid, act, reason); return {"standing": st}
    if act in ("model_on", "model_off"):
        return model_set(uid, act == "model_on", d.get("adult") is True, d.get("identity") is True, d.get("agreement") is True)
    if act in ("partner_on", "partner_off"):
        partners.admin_set(uid, act == "partner_on", True, None, "Moderator"); return {"partner": act == "partner_on"}
    if act == "plan":
        plan = str(d.get("plan", ""))
        with accounts._lock:
            A = accounts._accts(); x = A[uid]
            if plan == "none": x.pop("pass", None)
            elif plan in ("premium", "pro"):
                m = max(1, min(12, int(d.get("months") or 1)))
                x["pass"] = {"plan": plan, "until": int(time.time() + m * 30 * 86400), "granted_at": int(time.time()), "by": "moderator-override", "reminded": []}
            else: raise ValueError("Zły plan.")
            store.put("accounts", A)
        return {"plan": accounts.plan(_accts()[uid])}
    raise ValueError("Nieznana akcja.")

# ---------- treści ----------
def content(q=""):
    import social, profiles
    k = q.strip().lower(); out = []
    pins = set(store.get("wall_pinned", []) or [])
    for p in reversed(social._posts()):
        if p.get("status") == "deleted": continue
        if k and k not in (p.get("text", "") + " " + p.get("nick", "")).lower(): continue
        out.append({"type": "post", "id": p["id"], "title": p.get("nick", ""), "text": p.get("text", "")[:200], "hidden": p.get("status") in ("hidden", "rejected"),
                    "status": p.get("status"), "pinned": p["id"] in pins, "t": p.get("t", 0)})
        if len(out) >= 40: break
    for pid, r in profiles._P().items():
        if k and k not in (r.get("name", "") + " " + r.get("bio", "")).lower(): continue
        out.append({"type": "agent", "id": pid, "title": r.get("name", "Agentka"), "text": r.get("bio", "")[:200], "hidden": bool(r.get("hidden")), "public": bool(r.get("public")), "t": r.get("t", 0)})
        if len(out) >= 80: break
    return out
def content_act(h, d):
    import social, profiles
    typ, id_, act = d.get("type"), str(d.get("id", ""))[:40], d.get("action")
    if typ == "post":
        if act in ("hide", "unhide"): social.moderate("post", id_, "hide" if act == "hide" else "approve")
        elif act in ("pin", "unpin"):
            with _lock:
                Pn = [x for x in (store.get("wall_pinned", []) or []) if x != id_]
                if act == "pin": Pn.insert(0, id_)
                store.put("wall_pinned", Pn[:3])
        else: raise ValueError("bad action")
    elif typ == "agent":
        if act not in ("hide", "unhide"): raise ValueError("bad action")
        profiles.admin(id_, "hide" if act == "hide" else "show")
    else: raise ValueError("bad type")
    return {"ok": True}

# ---------- komunikat na stronie („Co nowego” / ogłoszenie) ----------
def announcement():
    a = store.get("mod_announce", {}) or {}
    return {"on": bool(a.get("on")), "text": str(a.get("text") or "")[:400], "title": str(a.get("title") or "Co nowego")[:60], "t": int(a.get("t") or 0)}
_ann_cache = {"t": 0, "v": None}
def announcement_cached():
    if time.time() - _ann_cache["t"] > 15 or _ann_cache["v"] is None: _ann_cache.update(t=time.time(), v=announcement())
    return _ann_cache["v"]

def inject(doc, h, path):
    """Wstrzykuje ogłoszenie (dla wszystkich) i link „🛡️ Panel admina” (tylko gdy serwer rozpozna konto admin)."""
    a = announcement_cached()
    add = '<link rel="stylesheet" href="/mod-ring.css?v=1.0">\n<script src="/mod-ring.js?v=1.0" defer></script>\n'
    if a["on"] and a["text"]:
        add += (f'<div class="luna-ann" role="status" data-t="{a["t"]}"><b>📣 {html.escape(a["title"])}</b> <span>{html.escape(a["text"])}</span>'
                '<button type="button" class="luna-ann-x" aria-label="Zamknij">×</button></div>\n')
    try:
        acc = h._acct()
        if acc and is_admin_user(acc[0]):
            add += f'<script src="{panel_prefix()}/link.js?v=1.0" defer></script>\n'
    except Exception: pass
    return doc.replace("</body>", add + "</body>", 1)

# ---------- HTTP ----------
def _send(h, code, ctype, b, extra=None):
    h.send_response(code); h.send_header("Content-Type", ctype); h.send_header("Content-Length", str(len(b)))
    h.send_header("Cache-Control", "no-store"); h.send_header("X-Robots-Tag", "noindex, nofollow")
    for k, v in (extra or {}).items(): h.send_header(k, v)
    h.end_headers(); h.wfile.write(b); return True

def handle_get(h, u):
    pref = panel_prefix(); p = u.path
    if p == pref or p.startswith(pref + "/"):
        sub = p[len(pref):] or "/"
        if sub == "/link.js":
            a = h._acct()
            if not a or not is_admin_user(a[0]): return _send(h, 404, "text/plain; charset=utf-8", b"not found")
            js = open(os.path.join(PANEL_DIR, "link.js"), encoding="utf-8").read().replace("__P__", pref)
            return _send(h, 200, "text/javascript; charset=utf-8", js.encode())
        files = {"/": ("index.html", "text/html; charset=utf-8"), "/app": ("index.html", "text/html; charset=utf-8"),
                 "/mod.js": ("mod.js", "text/javascript; charset=utf-8"), "/mod.css": ("mod.css", "text/css; charset=utf-8")}
        if sub not in files: return _send(h, 404, "text/plain; charset=utf-8", b"not found")
        fn, ct = files[sub]
        b = open(os.path.join(PANEL_DIR, fn), encoding="utf-8").read().replace("__P__", pref)
        if fn == "index.html": b = b.replace("__MODE__", "app" if sub == "/app" else "web")
        return _send(h, 200, ct, b.encode())
    if not p.startswith("/api/mod/") and p != "/api/me/look": return None
    if p == "/api/mod/public":
        S = switches(); return h._json({"features": S["features"], "announcement": announcement_cached()})
    if p == "/api/me/look":
        a = h._acct()
        if not a: return h._json({"login": True, "model": False})
        uid = a[0]["uid"]
        if not is_model_user(a[0]): return h._json({"model": False})
        out = {"model": True, "presets": look_presets(), "look": look_get(uid), "view": look_public(uid)}
        if (parse_qs(u.query).get("suggest") or [""])[0] == "1": out["suggest"] = look_suggest(uid)
        return h._json(out)
    if p == "/api/mod/state":
        return h._json(state(h))
    if p == "/api/mod/setup.svg":
        a = h._acct()
        if not a or not is_admin_user(a[0]) or not a[0].get("mod_totp_pending"): return _send(h, 404, "text/plain", b"not found")
        import segno
        u2 = security.totp_uri(a[0]["mod_totp_pending"], "Moderator", "Luna")
        b = io.BytesIO(); segno.make(u2, error="m").save(b, kind="svg", scale=6, border=2, dark="#0b0705", light="#ffffff", xmldecl=False)
        return _send(h, 200, "image/svg+xml", b.getvalue())
    c = _ctx(h)
    if not c: return h._json({"error": "unauthorized"}, 401)
    q = parse_qs(u.query); g = lambda k: (q.get(k) or [""])[0]
    if p == "/api/mod/overview":
        return h._json({"switches": switches(True), "features": FEATURES, "scopes": SCOPES, "stats": stats(), "announcement": announcement(),
                        "support": True, "persistent": store.status()["persistent"]})
    if p == "/api/mod/queue": return h._json({"items": queue()})
    if p == "/api/mod/users": return h._json({"items": users(g("q")[:30])})
    if p == "/api/mod/content": return h._json({"items": content(g("q")[:40])})
    if p == "/api/mod/audit": return h._json({"items": list(reversed((store.get("mod_audit", []) or [])[-300:]))})
    if p == "/api/mod/broadcasts":
        import inbox; return h._json({"items": inbox.admin_broadcasts()[:30]})
    return h._json({"error": "not found"}, 404)

def state(h):
    """Etap wejścia do panelu: login → setup (2FA pierwszy raz) → unlock (kod na nowym urządzeniu) → ok."""
    a = h._acct()
    if not a: return {"stage": "login"}
    u = a[0]
    if not is_admin_user(u): return {"stage": "denied"}
    if not totp_secret(u): return {"stage": "setup", "has_pending": bool(u.get("mod_totp_pending")), "persistent": store.status()["persistent"]}
    if not device_ok(h, u["uid"]): return {"stage": "unlock"}
    tok, csrf = _mint(u["uid"])
    return {"stage": "ok", "token": tok, "csrf": csrf, "name": MOD_NAME, "nick": admin_nick(), "prefix": panel_prefix(), "ttl": TOKEN_TTL}

_rl = {}
def _rate(key, n, per):
    now = time.time()
    with _lock:
        L = [t for t in _rl.get(key, []) if now - t < per]
        if len(L) >= n: _rl[key] = L; return False
        L.append(now); _rl[key] = L; return True

CRITICAL = ("switches", "broadcast")
def handle_post(h, u, data):
    p = u.path
    if p == "/api/me/look":
        a = h._acct()
        if not a: return h._json({"error": "Zaloguj się.", "login": True}, 401)
        if not h._csrf_ok(a[1]): return h._json({"error": "Odśwież stronę (CSRF)."}, 403)
        if not _rate("look:" + a[0]["uid"], 30, 60): return h._json({"error": "Za szybko – lustro też potrzebuje chwili 💄"}, 429)
        try: return h._json({"ok": True, "view": look_set(a[0]["uid"], data)})
        except PermissionError as e: return h._json({"error": str(e)}, 403)
        except ValueError as e: return h._json({"error": str(e)}, 400)
    if not p.startswith("/api/mod/"): return None
    ip = h._ip()
    if not _rate("m:" + ip, 90, 60): return h._json({"error": "Za szybko – odczekaj chwilę."}, 429)
    if p in ("/api/mod/setup/start", "/api/mod/setup/confirm", "/api/mod/unlock"):
        a = h._acct()
        if not a or not is_admin_user(a[0]): return h._json({"error": "unauthorized"}, 401)
        if not h._csrf_ok(a[1]): return h._json({"error": "Odśwież stronę (CSRF)."}, 403)
        if not _rate("m2fa:" + ip, 8, 300): return h._json({"error": "Za dużo prób – odczekaj 5 minut."}, 429)
        uid = a[0]["uid"]
        import accounts
        if p == "/api/mod/setup/start":
            if totp_secret(a[0]): return h._json({"error": "2FA jest już skonfigurowane."}, 400)
            with accounts._lock:
                A = accounts._accts(); A[uid]["mod_totp_pending"] = security.totp_new_secret(); store.put("accounts", A)
                sec = A[uid]["mod_totp_pending"]
            audit(h, "2fa_setup_start")
            return h._json({"ok": True, "secret": sec, "qr": "/api/mod/setup.svg?t=" + str(int(time.time()))})
        if p == "/api/mod/setup/confirm":
            if totp_secret(a[0]): return h._json({"error": "2FA jest już skonfigurowane."}, 400)
            pend = a[0].get("mod_totp_pending")
            if not pend or not security.totp_ok(pend, data.get("code"), "mod-setup:" + uid): return h._json({"error": "Nieprawidłowy kod – sprawdź czas w telefonie."}, 400)
            with accounts._lock:
                A = accounts._accts(); A[uid]["mod_totp"] = A[uid].pop("mod_totp_pending"); A[uid]["mod_totp_at"] = int(time.time()); store.put("accounts", A)
            device_new(h, uid); audit(h, "2fa_enabled")
            return h._json({"ok": True})
        sec = totp_secret(a[0])
        if not sec or not security.totp_ok(sec, data.get("code"), "mod-unlock:" + uid):
            audit(h, "unlock_fail"); return h._json({"error": "Nieprawidłowy kod 2FA."}, 400)
        device_new(h, uid); audit(h, "unlock_ok", "nowe urządzenie (30 dni)")
        return h._json({"ok": True})
    c = _ctx(h)
    if not c: return h._json({"error": "unauthorized"}, 401)
    if p == "/api/mod/lock":
        device_forget(h, bool(data.get("all")), c["uid"]); _sess.pop(c["tok"], None); audit(h, "lock", "wszystkie urządzenia" if data.get("all") else "to urządzenie")
        return h._json({"ok": True})
    act = p.rsplit("/", 1)[-1]
    crit = act in CRITICAL or (act in ("queue", "user") and data.get("action") in ("ban", "temp_block", "model_on", "model_off"))
    if crit:
        if not _rate("mc:" + c["uid"], 20, 600): return h._json({"error": "Za dużo akcji krytycznych – odczekaj chwilę."}, 429)
        if not _reauth(c, data): return h._json({"error": "Potwierdź kodem 2FA.", "reauth": True}, 403)
    try:
        if p == "/api/mod/switches":
            S = json.loads(json.dumps(switches(True)))
            for k in SCOPES:
                if k in (data.get("scopes") or {}): S[k]["on"] = bool(data["scopes"][k])
            for k, v in (data.get("features") or {}).items():
                if k in FEATURES: S["features"][k] = bool(v)
            if "msg" in data: S["msg"] = re.sub(r"[<>\x00-\x1f]", "", str(data.get("msg") or ""))[:300]
            if "until" in data:
                t = int(data.get("until") or 0); S["until"] = t if t > time.time() else 0
            _save_switches(S); audit(h, "switches", ", ".join([f"{k}={'ON' if S[k]['on'] else 'OFF'}" for k in SCOPES] + [f"{k}={'ON' if v else 'OFF'}" for k, v in S["features"].items()]))
            return h._json({"ok": True, "switches": S})
        if p == "/api/mod/queue":
            r = queue_act(h, data); audit(h, "queue " + str(data.get("action")), str(data.get("src")) + ":" + str(data.get("id"))[:40], data.get("reason", "")); return h._json(r)
        if p == "/api/mod/user":
            r = user_act(h, data); audit(h, "user " + str(data.get("action")), "u:" + str(data.get("uid"))[:8], data.get("reason") or data.get("plan") or ""); return h._json({"ok": True, **r})
        if p == "/api/mod/content":
            r = content_act(h, data); audit(h, "content " + str(data.get("action")), str(data.get("type")) + ":" + str(data.get("id"))[:20]); return h._json(r)
        if p == "/api/mod/announce":
            a = {"on": bool(data.get("on")), "title": re.sub(r"[<>\x00-\x1f]", "", str(data.get("title") or "Co nowego"))[:60],
                 "text": re.sub(r"[<>\x00-\x1f]", "", str(data.get("text") or ""))[:400], "t": int(time.time())}
            store.put("mod_announce", a); _ann_cache.update(t=0, v=None); audit(h, "announce", "ON" if a["on"] else "OFF", a["title"]); return h._json({"ok": True, "announcement": a})
        if p == "/api/mod/broadcast":
            import inbox
            b = inbox.broadcast(str(data.get("title") or ""), str(data.get("body") or "") + "\n— " + MOD_NAME, "important" if data.get("important") else "updates", "all", by="Moderator")
            audit(h, "broadcast", (b or {}).get("id", ""), str(data.get("title"))[:80]); return h._json({"ok": True, "id": (b or {}).get("id")})
    except KeyError: return h._json({"error": "Nie znaleziono."}, 404)
    except (ValueError, PermissionError) as e: return h._json({"error": str(e)}, 400)
    return h._json({"error": "not found"}, 404)

# ---------- 💗 Modelka Luny (rola nadawana TYLKO przez moderatora) + Wygląd profilu ----------
def is_model_user(u): return bool(u and (u.get("model") or {}).get("on"))
def is_model_uid(uid): return is_model_user(_accts().get(uid)) if uid else False
def model_set(uid, on, adult=False, identity=False, agreement=False):
    """Nadanie wymaga: potwierdzonych 18+, tożsamości (tylko flaga tak/nie + data + kto) i umowy współpracy. Dokumentów nie przechowujemy."""
    import accounts
    with accounts._lock:
        A = accounts._accts(); u = A.get(uid)
        if not u: raise KeyError(uid)
        if u.get("role") == "admin": raise ValueError("Admin nie potrzebuje tej roli 😉")
        if on:
            if not (adult and identity and agreement): raise ValueError("Zaznacz wszystkie trzy: 18+, tożsamość i umowa współpracy.")
            now = int(time.time())
            u["model"] = {"on": True, "adult": True, "identity": True, "identity_at": now, "agreement": True, "at": now, "by": "Moderator"}
        else:
            m = u.get("model") or {}; u["model"] = {"on": False, "revoked_at": int(time.time()), "by": "Moderator", "was": bool(m.get("on"))}
        store.put("accounts", A)
    return {"model": bool(on)}

def _lum(hx):
    hx = hx.lstrip("#"); c = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
# 10 palet (akcent) – kolory zastrzeżone (elektryczny niebieski moderatora #0A2BFF–#3D7BFF, różowy ramki modelki) są wykluczone
PALETTES = {"roza": ("Pudrowy róż", "#F7A1C4"), "wino": ("Wino", "#E0407A"), "zloto": ("Szampańskie złoto", "#E8C27A"), "miedz": ("Miedź", "#E07A30"),
            "szmaragd": ("Szmaragd", "#2EBD85"), "mieta": ("Mięta", "#7FE0C2"), "lawenda": ("Lawenda", "#B79CFF"), "sliwka": ("Śliwka", "#B86ADB"),
            "turkus": ("Turkus", "#26C6DA"), "perla": ("Perła", "#EDE6DD")}
BGS = {"noc": ("Noc", ["#0B0705"]), "grafit": ("Grafit", ["#16161A"]), "bordo": ("Bordo nocą", ["#2A0A14"]), "las": ("Leśna noc", ["#0A1F17"]),
       "zmierzch": ("Zmierzch", ["#1B0F2E", "#3A1430"]), "aksamit": ("Aksamit", ["#140A1E", "#2B0F2B"]), "ocean": ("Głębia oceanu", ["#04161F", "#0B2E3A"]),
       "brzask": ("Brzask", ["#2B1408", "#4A1F12"])}
FONTS = {"nunito": ("Nunito", "Nunito,system-ui,sans-serif"), "playfair": ("Playfair Display", "\"Playfair Display\",Georgia,serif"),
         "georgia": ("Georgia", "Georgia,\"Times New Roman\",serif"), "trebuchet": ("Trebuchet", "\"Trebuchet MS\",Tahoma,sans-serif"),
         "verdana": ("Verdana", "Verdana,Geneva,sans-serif"), "system": ("Systemowa", "system-ui,-apple-system,\"Segoe UI\",Roboto,sans-serif")}
FRAMES = {"modelka": "Różowa ramka modelki (domyślna)", "podwojna": "Podwójna", "perlowa": "Perłowa", "satyna": "Satynowa poświata"}
LOOK_DEF = {"palette": "roza", "bg": "noc", "font": "playfair", "frame": "modelka"}
def _text_for(bg):
    best = max(("#FFFFFF", "#F6E9DA", "#111111"), key=lambda t: min(contrast(t, c) for c in bg)); return best
def look_presets():
    out = {"palettes": [], "bgs": [], "fonts": [{"id": k, "name": v[0], "css": v[1]} for k, v in FONTS.items()], "frames": [{"id": k, "name": v} for k, v in FRAMES.items()]}
    for k, (n, c) in PALETTES.items(): out["palettes"].append({"id": k, "name": n, "color": c})
    for k, (n, cs) in BGS.items(): out["bgs"].append({"id": k, "name": n, "colors": cs, "text": _text_for(cs)})
    return out
def look_ok(lk):
    """WCAG AA: tekst ≥ 4,5:1 na każdym kolorze tła; akcent (przyciski, nick) ≥ 3:1 na tle."""
    cs = BGS[lk["bg"]][1]; tx = _text_for(cs); ac = PALETTES[lk["palette"]][1]
    return min(contrast(tx, c) for c in cs) >= 4.5 and min(contrast(ac, c) for c in cs) >= 3.0
def look_get(uid):
    import userprof
    r = (userprof._P().get(uid) or {}).get("look") or {}
    lk = {k: (r.get(k) if r.get(k) in D else LOOK_DEF[k]) for k, D in (("palette", PALETTES), ("bg", BGS), ("font", FONTS), ("frame", FRAMES))}
    return lk
def look_public(uid):
    """Wygląd do wyświetlenia – tylko dla zweryfikowanych modelek; reszta ma standardowy wygląd."""
    if not is_model_uid(uid): return None
    lk = look_get(uid); cs = BGS[lk["bg"]][1]
    return {**lk, "accent": PALETTES[lk["palette"]][1], "bgc": cs, "text": _text_for(cs), "font_css": FONTS[lk["font"]][1]}
def look_set(uid, d):
    if not is_model_uid(uid): raise PermissionError("Wygląd profilu to przywilej zweryfikowanych Modelek Luny 💗")
    lk = look_get(uid)
    for k, D in (("palette", PALETTES), ("bg", BGS), ("font", FONTS), ("frame", FRAMES)):
        v = d.get(k)
        if v is not None:
            if v not in D: raise ValueError("Tego wariantu nie ma w katalogu – wybierz z listy.")
            lk[k] = v
    if not look_ok(lk): raise ValueError("Za słaby kontrast – tekst byłby nieczytelny. Wybierz inne tło albo kolor.")
    import userprof
    with userprof._lock:
        P = userprof._P(); r = P.get(uid) or {}; r["look"] = lk; P[uid] = r; store.put("user_profiles", P)
    return look_public(uid)
def look_suggest(uid):
    """„Dopasuj do agentki”: dominujący kolor zdjęcia agentki → najbliższa paleta z katalogu."""
    import profiles, base64, colorsys
    pid, _r = profiles.mine(uid)
    im = profiles._imgs().get(pid) if pid else None
    if not im: return None
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(base64.b64decode(im["b"]))).convert("RGB").resize((64, 64))
        q = img.quantize(colors=6); pal = q.getpalette()[:18]; counts = sorted(q.getcolors(), reverse=True)
        best = None
        for n, idx in counts:
            r, g, b = pal[idx * 3:idx * 3 + 3]; h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if 0.15 < l < 0.9 and s > 0.2: best = (h, l, s); break
        if not best: return "perla"
        def dist(hx):
            hx = hx.lstrip("#"); h2, l2, s2 = colorsys.rgb_to_hls(*[int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)])
            dh = min(abs(best[0] - h2), 1 - abs(best[0] - h2)); return dh * 3 + abs(best[1] - l2) + abs(best[2] - s2) * .5
        return min(PALETTES, key=lambda k: dist(PALETTES[k][1]))
    except Exception: return None
