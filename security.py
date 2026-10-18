"""Nagłówki bezpieczeństwa, ochrona CSRF/Origin, prawdziwe IP klienta za Cloudflare/Renderem, TOTP (2FA),
sprawdzanie haseł z wycieków (HIBP k-anonymity), dziennik audytu panelu, redakcja logów."""
import base64, hashlib, hmac, os, re, secrets, struct, threading, time, urllib.request
import store

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "media-src 'self' data: blob:; connect-src 'self'; font-src 'self' data:; worker-src 'self'; manifest-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'")
# Cloudflare Turnstile (tylko gdy skonfigurowano klucze): skrypt i ramka z challenges.cloudflare.com
TS_HOST = "https://challenges.cloudflare.com"
def csp(turnstile=False, frame="'self'"):
    c = CSP.replace("frame-ancestors 'self'", "frame-ancestors " + frame)
    if turnstile:
        c = c.replace("script-src 'self'", "script-src 'self' " + TS_HOST).replace("connect-src 'self'", "connect-src 'self' " + TS_HOST) + "; frame-src " + TS_HOST
    return c
HEADERS = {
    "Content-Security-Policy": CSP,
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "microphone=(self), camera=(), geolocation=(), payment=(), usb=(), browsing-topics=(), magnetometer=(), gyroscope=(), accelerometer=(), display-capture=()",
    "X-Frame-Options": "SAMEORIGIN",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}
SECRET_Q = re.compile(r"((?:token|t|code|key|secret|password|sid|csrf)=)[^&\s]+", re.I)

def redact(s):
    """Usuwa wartości tokenów/haseł z linii logu."""
    return SECRET_Q.sub(r"\1***", str(s))

def origin_ok(headers, host_hint=None):
    """Odrzuca żądania POST z obcego Origin (ochrona CSRF dla API). Brak nagłówka = klient nie-przeglądarkowy (cron, curl)."""
    if (headers.get("Sec-Fetch-Site") or "") == "cross-site": return False  # przeglądarka: żądanie z obcej strony
    o = headers.get("Origin")
    if not o: return True
    host = headers.get("X-Forwarded-Host") or headers.get("Host") or host_hint or ""
    return re.sub(r"^https?://", "", o).rstrip("/") == host

IP_RE = re.compile(r"[0-9a-fA-F:.]{2,45}")
def client_ip(headers, peer=""):
    """Prawdziwe IP klienta. Render stoi za Cloudflare, który NADPISUJE CF-Connecting-IP / True-Client-IP;
    X-Forwarded-For jest tylko dopisywany, więc jego pierwszy element może podrobić klient (obejście limitów).
    Kolejność: True-Client-IP → CF-Connecting-IP → ostatni wpis X-Forwarded-For → adres gniazda."""
    for h in ("True-Client-IP", "CF-Connecting-IP"):
        v = (headers.get(h) or "").strip()
        if IP_RE.fullmatch(v): return v
    xf = [x.strip() for x in (headers.get("X-Forwarded-For") or "").split(",") if x.strip()]
    if xf and IP_RE.fullmatch(xf[-1]): return xf[-1]
    return str(peer or "")

_salt_cache = []
def _log_salt():
    """Sekretna sól do skrótów IP w logach (env LUNA_LOG_SALT albo losowa, trzymana w magazynie) – skrótu IPv4 nie da się odwrócić słownikiem."""
    if not _salt_cache:
        v = os.getenv("LUNA_LOG_SALT", "").strip()
        if not v:
            try:
                v = store.get("log_salt", "") or ""
                if not v: v = secrets.token_hex(16); store.put("log_salt", v)
            except Exception: v = secrets.token_hex(16)
        _salt_cache.append(v.encode())
    return _salt_cache[0]
def ip_hash(ip):
    return hmac.new(_log_salt(), str(ip).encode(), hashlib.sha256).hexdigest()[:12]

# ---------- TOTP (RFC 6238, 30 s, 6 cyfr) – darmowe 2FA zgodne z Google Authenticator / Aegis / 2FAS ----------
def totp_new_secret(): return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
def _totp_at(secret, step):
    key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    d = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    o = d[-1] & 15
    return "%06d" % ((struct.unpack(">I", d[o:o + 4])[0] & 0x7fffffff) % 1000000)
_used = {}
def totp_ok(secret, code, key="", window=1):
    """Sprawdza kod (±1 okno = ±30 s). Ten sam kod nie przejdzie drugi raz (ochrona przed powtórzeniem)."""
    code = re.sub(r"\s", "", str(code or ""))
    if not secret or not re.fullmatch(r"\d{6}", code): return False
    now = int(time.time() // 30)
    try:
        for w in range(-window, window + 1):
            if hmac.compare_digest(_totp_at(secret, now + w), code):
                k = (key or secret[:8], now + w)
                with _alock:
                    for x in [x for x in _used if x[1] < now - 3]: _used.pop(x, None)
                    if k in _used: return False
                    _used[k] = 1
                return True
    except Exception: return False
    return False
def totp_uri(secret, label, issuer="Luna"):
    from urllib.parse import quote
    return f"otpauth://totp/{quote(issuer)}:{quote(label)}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"

# ---------- Have I Been Pwned: Pwned Passwords (k-anonymity – wysyłamy tylko 5 pierwszych znaków SHA-1) ----------
def pwned_count(pw, timeout=4):
    """Ile razy hasło wystąpiło w wyciekach (0 = nie znaleziono lub usługa niedostępna – wtedy nie blokujemy)."""
    if os.getenv("LUNA_HIBP", "1") == "0": return 0
    h = hashlib.sha1(str(pw).encode("utf-8"), usedforsecurity=False).hexdigest().upper()  # nosec B324 – wymóg protokołu HIBP, nie do przechowywania
    try:
        req = urllib.request.Request("https://api.pwnedpasswords.com/range/" + h[:5], headers={"Add-Padding": "true", "User-Agent": "Luna-app-security"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310 – stały adres https
            for line in r.read().decode("utf-8", "ignore").splitlines():
                suf, _, n = line.partition(":")
                if suf.strip() == h[5:]: return int(n.strip() or 0)
    except Exception: return 0
    return 0

SECURITY_TXT = """Contact: {base}/app#live
Expires: {exp}
Preferred-Languages: pl, en
Canonical: {base}/.well-known/security.txt
Policy: {base}/regulamin.html
"""
def security_txt(base):
    exp = time.strftime("%Y-%m-%dT00:00:00Z", time.gmtime(time.time() + 300 * 86400))
    return SECURITY_TXT.format(base=base.rstrip("/"), exp=exp)

_alock = threading.Lock()
def audit(action, ip="", detail=""):
    """Dziennik audytu panelu producenta (bez kodów, haseł i tokenów)."""
    with _alock:
        log = store.get("audit", []) or []
        log.append({"t": int(time.time()), "ip": ip_hash(ip), "action": str(action)[:60], "detail": redact(str(detail))[:200]})
        store.put("audit", log[-500:])

def audit_list(n=200):
    return list(reversed((store.get("audit", []) or [])[-n:]))
