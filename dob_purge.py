"""Jednorazowe (idempotentne) usunięcie zapisanych dat urodzenia ze wszystkich rekordów.
Od v1.6.x formularze i konta pytają tylko „Masz 18 lat?” (Tak/Nie) – daty urodzenia nie zbieramy i nie przechowujemy.
• Usuwa pola z datą urodzenia (dob, birthdate, date_of_birth, …) z każdego rekordu w magazynie (testerzy, Dołącz/Twarz AI,
  zespół, formularze 18+, konta, oświadczenia urządzeń i każdy inny klucz).
• Zachowuje potwierdzenie 18+. Jeśli rekord miał tylko datę, przed jej usunięciem ustawia adult_confirmed (True, gdy 18+),
  bez zapisywania samej daty.
• Do dziennika audytu trafia wyłącznie liczba oczyszczonych rekordów. Bezpiecznie uruchamiać przy każdym starcie."""
import datetime, json, re, time
import store

MARK = "mig_dob_purge"
FIELDS = {"dob", "birthdate", "birth_date", "birthday", "date_of_birth", "dateofbirth", "data_urodzenia", "urodziny", "born"}
_HINT = re.compile(r'"(?:' + "|".join(sorted(FIELDS)) + r')"\s*:', re.I)
KNOWN = ("testers", "join_msgs", "team_apps", "f18_apps", "accounts", "age_decl", "user_profiles")

def _is_adult(v):
    try:
        b = datetime.date.fromisoformat(str(v).strip()[:10]); t = datetime.date.today()
        return (t.year - b.year - ((t.month, t.day) < (b.month, b.day))) >= 18
    except Exception: return None

def _clean_rec(r):
    """Czyści jeden słownik (rekord). Zwraca True, gdy coś usunięto."""
    hit = [k for k in list(r.keys()) if str(k).lower() in FIELDS]
    if not hit: return False
    has_flag = r.get("adult") is True or r.get("adult_confirmed") is True or r.get("dob_declared") is True
    if not has_flag:
        a = None
        for k in hit:
            a = _is_adult(r.get(k))
            if a is not None: break
        if a is not None:
            r["adult_confirmed"] = bool(a)
            if a: r.setdefault("adult", True)
    elif r.get("adult") is True and "adult_confirmed" not in r:
        r["adult_confirmed"] = True
    for k in hit: r.pop(k, None)
    return True

def _walk(v):
    """Rekurencyjnie czyści dicty/listy; zwraca liczbę oczyszczonych rekordów."""
    n = 0
    if isinstance(v, dict):
        if _clean_rec(v): n += 1
        for x in v.values():
            if isinstance(x, (dict, list)): n += _walk(x)
    elif isinstance(v, list):
        for x in v:
            if isinstance(x, (dict, list)): n += _walk(x)
    return n

def clean_value(v):
    """Czyści przekazaną strukturę w miejscu (np. import kopii zapasowej). Zwraca liczbę oczyszczonych rekordów."""
    return _walk(v)

def _keys():
    ks = set(KNOWN)
    try: ks.update(store.keys())
    except Exception: pass
    return sorted(k for k in ks if k != MARK)

def run(audit=None):
    """Idempotentne: drugi przebieg nic nie zmienia (0 rekordów). Zwraca {"records": n, "keys": m}."""
    total, keys = 0, 0
    for k in _keys():
        v = store.get(k, None)
        if not isinstance(v, (dict, list)): continue
        try:
            if not _HINT.search(json.dumps(v, ensure_ascii=False)): continue
        except Exception: continue
        n = _walk(v)
        if n:
            store.put(k, v); total += n; keys += 1
    first = not (store.get(MARK, None) or {}).get("t")
    if first or total:
        store.put(MARK, {"v": 1, "t": int(time.time()), "records": total, "keys": keys})
        if audit:
            try: audit("dob_purge", "", "records=%d keys=%d" % (total, keys))
            except Exception: pass
    return {"records": total, "keys": keys}
