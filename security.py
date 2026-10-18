"""Nagłówki bezpieczeństwa, ochrona CSRF/Origin, dziennik audytu panelu, redakcja logów."""
import hashlib, re, threading, time
import store

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "media-src 'self' data: blob:; connect-src 'self'; font-src 'self' data:; worker-src 'self'; manifest-src 'self'; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
HEADERS = {
    "Content-Security-Policy": CSP,
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "microphone=(self), camera=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
}
SECRET_Q = re.compile(r"((?:token|t|code|key|secret|password|sid|csrf)=)[^&\s]+", re.I)

def redact(s):
    """Usuwa wartości tokenów/haseł z linii logu."""
    return SECRET_Q.sub(r"\1***", str(s))

def origin_ok(headers, host_hint=None):
    """Odrzuca żądania POST z obcego Origin (ochrona CSRF dla API). Brak nagłówka = klient nie-przeglądarkowy (cron, curl)."""
    o = headers.get("Origin")
    if not o: return True
    host = headers.get("X-Forwarded-Host") or headers.get("Host") or host_hint or ""
    return re.sub(r"^https?://", "", o).rstrip("/") == host

def ip_hash(ip):
    return hashlib.sha256(("luna-audit" + str(ip)).encode()).hexdigest()[:12]

_alock = threading.Lock()
def audit(action, ip="", detail=""):
    """Dziennik audytu panelu producenta (bez kodów, haseł i tokenów)."""
    with _alock:
        log = store.get("audit", []) or []
        log.append({"t": int(time.time()), "ip": ip_hash(ip), "action": str(action)[:60], "detail": redact(str(detail))[:200]})
        store.put("audit", log[-500:])

def audit_list(n=200):
    return list(reversed((store.get("audit", []) or [])[-n:]))
