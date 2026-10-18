"""Plany po stronie serwera: darmowy < podstawowa < premium < pro. Plan wynika z konta (tester → Premium; płatności – wkrótce).
Limity planu Darmowy ustawiane w panelu (CFG['free'])."""
import datetime, hashlib, threading
RANK = {"darmowy": 0, "podstawowa": 1, "premium": 2, "pro": 3}
NAMES = {"darmowy": "Darmowy", "podstawowa": "Podstawowa", "premium": "Premium", "pro": "Pro / Ultra"}
_use, _lock = {}, threading.Lock()

def has(plan, need): return RANK.get(plan, 0) >= RANK.get(need, 0)

def _day(): return datetime.date.today().isoformat()

def used(key):
    with _lock: return _use.get((_day(), key), 0.0)

def add(keys, secs):
    with _lock:
        d = _day()
        for k in list(_use):
            if k[0] != d: _use.pop(k, None)
        for k in keys: _use[(d, k)] = _use.get((d, k), 0.0) + secs

def keys_for(uid, vid, ip):
    """Klucze limitu: konto, urządzenie i (luźniej) IP – utrudnia obchodzenie limitu przez czyszczenie danych."""
    k = []
    if uid: k.append("u:" + uid)
    if vid: k.append("v:" + vid)
    k.append("i:" + hashlib.sha256(("lim" + ip).encode()).hexdigest()[:16])
    return k

def chat_allowed(keys, minutes):
    lim = minutes * 60
    for k in keys:
        f = 3 if k.startswith("i:") else 1  # IP współdzielone (np. sieć domowa) – większy zapas
        if used(k) >= lim * f: return False
    return True

def speech_secs(q, a):
    return len(str(q).split()) / 2.3 + len(str(a).split()) / 2.3
