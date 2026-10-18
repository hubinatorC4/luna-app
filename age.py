"""Pełnoletność (18+).
• Strona, aplikacja i rejestracja: proste pytanie „Masz 18 lat?” Tak / Nie – samodeklaracja, zapisujemy tylko adult_confirmed + znacznik czasu.
• Formularze (testerzy, casting, Dołącz, Twarz AI): tylko „Masz 18 lat?” Tak / Nie – bez daty urodzenia; testerzy i casting dodatkowo weryfikacja u zewnętrznego dostawcy (verify18.py)."""
import datetime, re, threading, time
import store

ADULT_TEXT = "Oświadczam, że jestem osobą pełnoletnią (18+) i posiadam własne konto bankowe."
UNDER_MSG = ("Przepraszamy – Luna jest przeznaczona wyłącznie dla osób pełnoletnich (18+). "
             "Dziękujemy za zainteresowanie i zapraszamy, gdy skończysz 18 lat.")
_lock = threading.Lock()

class Underage(ValueError): pass

def age_of(dob):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(dob or "")): raise ValueError("Podaj datę urodzenia.")
    try: b = datetime.date.fromisoformat(dob)
    except ValueError: raise ValueError("Podaj poprawną datę urodzenia.")
    t = datetime.date.today()
    if b > t or b.year < 1900: raise ValueError("Podaj poprawną datę urodzenia.")
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))

def check(d):
    """Oświadczenie 18+ w formularzach (Dołącz, Twarz AI, tester w aplikacji) – BEZ daty urodzenia (nie zbieramy jej).
    Starsze klienty mogą jeszcze wysłać datę: nadal odmawiamy osobom < 18, ale daty nie zapisujemy."""
    if d.get("adult_confirmed") is False: raise Underage(UNDER_MSG)
    if d.get("dob") and age_of(str(d.get("dob")).strip()) < 18: raise Underage(UNDER_MSG)
    if d.get("adult") is not True and d.get("adult_confirmed") is not True: raise ValueError("Zaznacz oświadczenie o pełnoletności (18+).")
    return {"adult": True, "adult_text": ADULT_TEXT, "adult_at": int(time.time())}

CONFIRM_TEXT = "Masz 18 lat? – Tak"

def confirm(d):
    """Samodeklaracja „Masz 18 lat?” → Tak. Bez daty urodzenia. Zwraca pola do zapisania na koncie/urządzeniu."""
    if d.get("adult_confirmed") is not True and d.get("adult") is not True:
        raise ValueError("Potwierdź, że masz ukończone 18 lat.")
    if d.get("dob"):  # starsze wersje aplikacji wciąż wysyłają datę urodzenia – nadal odmawiamy osobom poniżej 18 lat
        if age_of(str(d.get("dob")).strip()) < 18: raise Underage(UNDER_MSG)
    now = int(time.time())
    return {"adult": True, "adult_at": now, "adult_text": CONFIRM_TEXT, "adult_confirmed": True, "adult_confirmed_at": now}

def declare(vid, d, name=""):
    if not re.fullmatch(r"[0-9a-f]{16,32}", str(vid or "")): raise ValueError("bad id")
    rec = confirm(d); rec.update({"vid": vid, "name": str(name or "").strip()[:40], "source": str(d.get("source", "app"))[:12]})
    with _lock:
        a = store.get("age_decl", {}) or {}
        a[vid] = rec; store.put("age_decl", a)
    return rec

def status(vid):
    v = (store.get("age_decl", {}) or {}).get(str(vid or ""))
    return {"declared": bool(v), "at": v["adult_at"] if v else 0}

def admin_list():
    out = []
    for v in (store.get("age_decl", {}) or {}).values():
        out.append({"vid": v["vid"], "name": v.get("name", ""), "age": age_of(v["dob"]) if v.get("dob") else None, "adult": v["adult"], "at": v["adult_at"], "source": v.get("source", "app")})
    return sorted(out, key=lambda x: -x["at"])
