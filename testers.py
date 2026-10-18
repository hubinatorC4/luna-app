"""Rekrutacja testerów (maks. 50). Dane w magazynie store (Postgres, gdy ustawiony DATABASE_URL)."""
import csv, io, re, secrets, threading, time
import store, age
from notify import EMAIL_RE

LIMIT = 50
RINGS = {"fioletowa": "#8B5CF6", "niebieska": "#3B82F6"}
GRANT_DAYS = 60
CONSENT = ("Wyrażam zgodę na przetwarzanie moich danych (imię, e-mail, odpowiedzi z formularza) w celu rekrutacji i kontaktu "
           "w sprawie testów aplikacji Luna. Zgodę mogę wycofać w każdej chwili, pisząc w czacie z twórcą.")
_lock = threading.Lock()

def _all(): return store.get("testers", {}) or {}

def remaining():
    return max(0, LIMIT - len(_all()))

def signup(d, ip_hash=""):
    name = str(d.get("name", "")).strip()[:40]
    email = str(d.get("email", "")).strip()[:254]
    reason = str(d.get("reason", "")).strip()[:300]
    ring = d.get("ring") if d.get("ring") in RINGS else None
    android = d.get("android")
    if not name: raise ValueError("Podaj imię.")
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail.")
    if not ring: raise ValueError("Wybierz kolor obwódki.")
    if android not in (True, False): raise ValueError("Zaznacz, czy masz telefon z Androidem.")
    decl = age.check(d)  # 18+: data urodzenia i oświadczenie (Underage → grzeczna odmowa)
    if d.get("consent") is not True: raise ValueError("Zaznacz zgodę na przetwarzanie danych.")
    with _lock:
        t = _all()
        if any(v["email"].lower() == email.lower() for v in t.values()): raise ValueError("Ten adres e-mail jest już zgłoszony.")
        if len(t) >= LIMIT: raise OverflowError("Komplet! Wszystkie 50 miejsc dla testerów jest już zajętych.")
        code = secrets.token_hex(4).upper()
        while code in t: code = secrets.token_hex(4).upper()
        t[code] = {"code": code, "name": name, "email": email, "reason": reason, "ring": ring, "android": android,
                   "t": int(time.time()), "consent": CONSENT, "granted": False, "until": 0, "ip": ip_hash, **decl}
        store.put("testers", t)
        return code, LIMIT - len(t)

def status(code):
    v = _all().get(str(code or "").upper().strip())
    if not v: return {"found": False}
    active = v["granted"] and v["until"] > time.time()
    return {"found": True, "name": v["name"], "ring_choice": v["ring"], "granted": active, "until": v["until"] if active else 0,
            "ring": RINGS[v["ring"]] if active else None, "plan": "premium" if active else None}

def ring_for(code):
    s = status(code) if code else {}
    return s.get("ring") if s.get("granted") else None

def grant(code, on, ring=None):
    with _lock:
        t = _all(); v = t.get(code)
        if not v: raise KeyError("not found")
        if ring in RINGS: v["ring"] = ring
        v["granted"] = bool(on); v["until"] = int(time.time() + GRANT_DAYS * 86400) if on else 0
        store.put("testers", t); return v

def delete(code):
    with _lock:
        t = _all(); t.pop(code, None); store.put("testers", t)

def admin_list():
    out = []
    for v in sorted(_all().values(), key=lambda v: v["t"]):
        v = dict(v); v["age"] = age.age_of(v["dob"]) if v.get("dob") else None; out.append(v)
    return out

def csv_export():
    b = io.StringIO(); w = csv.writer(b, delimiter=";")
    w.writerow(["kod", "imię", "e-mail", "dlaczego", "obwódka", "android", "data zgłoszenia", "premium do", "zgoda", "data urodzenia", "oświadczenie 18+", "data oświadczenia"])
    for v in admin_list():
        w.writerow([v["code"], v["name"], v["email"], v["reason"], v["ring"], "tak" if v["android"] else "nie",
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(v["t"])), time.strftime("%Y-%m-%d", time.localtime(v["until"])) if v["granted"] else "", v["consent"], v.get("dob", ""), v.get("adult_text", "BRAK"), time.strftime("%Y-%m-%d %H:%M", time.localtime(v["adult_at"])) if v.get("adult_at") else ""])
    return "\ufeff" + b.getvalue()
