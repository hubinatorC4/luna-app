"""„Dołącz do projektu Luna” – zgłoszenia trafiają do skrzynki głównego moderatora. Honeypot + limit czasu + rate limit."""
import re, secrets, threading, time
import store, age
from notify import EMAIL_RE
ROLES = ("projektant/ka", "grafik/czka", "programista/ka", "lektor/ka", "twórca treści", "tłumacz/ka", "marketing", "twarz AI", "inne")
CONSENT = ("Wyrażam zgodę na przetwarzanie moich danych (imię, e-mail, treść zgłoszenia, link do portfolio) w celu odpowiedzi "
           "na zgłoszenie do projektu Luna. Zgodę mogę wycofać w każdej chwili, pisząc w czacie z twórcą.")
_lock = threading.Lock()
def _all(): return store.get("join_msgs", []) or []

def submit(d, ip_hash=""):
    if str(d.get("website", "")).strip(): raise PermissionError("spam")          # honeypot
    try:
        if time.time() * 1000 - float(d.get("t0", 0)) < 3000: raise PermissionError("spam")  # wysłane za szybko
    except (TypeError, ValueError): raise PermissionError("spam")
    name = re.sub(r"[<>\x00-\x1f]", "", str(d.get("name", "")).strip())[:60]
    email = str(d.get("email", "")).strip()[:254]
    role = d.get("role") if d.get("role") in ROLES else None
    other = re.sub(r"[<>\x00-\x1f]", "", str(d.get("role_other", "")).strip())[:60]
    msg = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(d.get("message", "")).strip())[:1500]
    link = str(d.get("portfolio", "")).strip()[:300]
    if not name: raise ValueError("Podaj imię.")
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail.")
    if not role: raise ValueError("Wybierz rolę.")
    if role == "inne" and not other: raise ValueError("Napisz, jaka to rola.")
    if len(msg) < 10: raise ValueError("Napisz kilka słów o sobie (min. 10 znaków).")
    if link and not re.fullmatch(r"https?://[^\s<>\"']{3,300}", link): raise ValueError("Link do portfolio musi zaczynać się od https://")
    h = d.get("height")
    height = None
    if h not in (None, ""):
        try: height = int(h)
        except (TypeError, ValueError): raise ValueError("Wzrost podaj w centymetrach (np. 168).")
        if not 120 <= height <= 220: raise ValueError("Wzrost podaj w centymetrach (120–220).")
    decl = age.check(d)
    if d.get("consent") is not True: raise ValueError("Zaznacz zgodę na przetwarzanie danych.")
    if role == "twarz AI" and d.get("img_consent") is not True: raise ValueError("Zaznacz oświadczenie dotyczące wizerunku (art. 81).")
    rec = {"id": secrets.token_hex(6), "t": int(time.time()), "name": name, "email": email, "role": role, "role_other": other,
           "message": msg, "portfolio": link, "height": height, "kind": "twarz" if role == "twarz AI" else "projekt", "consent": CONSENT, "read": False, "ip": ip_hash, **decl}
    with _lock:
        a = _all(); a.append(rec); store.put("join_msgs", a[-1000:])
    return rec

def unread(): return sum(1 for m in _all() if not m.get("read"))
def admin_list(): return list(reversed(_all()))
def mark(id_, read=True, delete=False):
    with _lock:
        a = _all()
        if delete: a = [m for m in a if m["id"] != id_]
        else:
            for m in a:
                if m["id"] == id_: m["read"] = bool(read)
        store.put("join_msgs", a)
