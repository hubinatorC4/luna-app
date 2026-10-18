"""Deklaracja pełnoletności (18+). To wyłącznie oświadczenie użytkownika – nie weryfikujemy wieku ani konta bankowego."""
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
    """Zwraca dict z danymi deklaracji albo rzuca ValueError/Underage."""
    dob = str(d.get("dob", "")).strip()
    if age_of(dob) < 18: raise Underage(UNDER_MSG)
    if d.get("adult") is not True: raise ValueError("Zaznacz oświadczenie o pełnoletności i posiadaniu własnego konta bankowego.")
    return {"dob": dob, "adult": True, "adult_text": ADULT_TEXT, "adult_at": int(time.time())}

def declare(vid, d, name=""):
    if not re.fullmatch(r"[0-9a-f]{16,32}", str(vid or "")): raise ValueError("bad id")
    rec = check(d); rec.update({"vid": vid, "name": str(name or "").strip()[:40], "source": str(d.get("source", "app"))[:12]})
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
        out.append({"vid": v["vid"], "name": v.get("name", ""), "age": age_of(v["dob"]), "adult": v["adult"], "at": v["adult_at"], "source": v.get("source", "app")})
    return sorted(out, key=lambda x: -x["at"])
