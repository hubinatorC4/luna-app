"""Anonimowe statystyki popularności (bez danych osobowych): dzienne liczniki zbiorcze.
Unikalność liczona skrótem (dzienna losowa sól + losowy identyfikator sesji + klucz) – sól jest kasowana po 2 dniach,
więc skrótów nie da się powiązać z osobą ani między dniami. Bez IP, bez ciasteczek śledzących, bez odcisku urządzenia.
Klucze: sec:<sekcja>, page:<ścieżka>, post:<id>:{v,u,click,share,like,dislike,cmt,lang:xx}, item:<id>:{v,u,cart,buy,rev_pln}."""
import datetime, hashlib, re, secrets, threading, time
import store
_lock = threading.Lock()
_buf = {}          # day -> {key: n}
_seen = {}         # day -> set(hash)
_tot = {}          # przyrosty sum całkowitych (publiczne liczniki wyświetleń)
_last = time.time()
KEEP_DAYS = 400
KEY_RE = re.compile(r"(sec|page|post|item|utm):[\w\-./]{1,60}(:[a-z_]{1,8}(:[a-z]{2})?)?")
BOT_UA = re.compile(r"(?i)bot|crawl|spider|slurp|headless|phantom|selenium|puppeteer|playwright|python|curl|wget|httpclient|okhttp|java/|go-http|axios|node-fetch|scrapy|lighthouse|preview|facebookexternalhit|embedly|monitor|uptime")
def today(): return (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).date().isoformat()
def is_bot(ua): return not ua or len(ua) < 20 or bool(BOT_UA.search(ua))
def _salt(day):
    S = _salt.cache
    if day not in S:
        s = store.get("stats_salt", {}) or {}
        if day not in s:
            s[day] = secrets.token_hex(16)
            for k in sorted(s)[:-2]: s.pop(k, None)
            store.put("stats_salt", s)
        S.clear(); S.update(s)
    return S[day]
_salt.cache = {}
def _seen_day(day):
    if day not in _seen:
        _seen.clear(); _seen[day] = set(store.get("stats_seen:" + day, []) or [])
    return _seen[day]
def add(key, n=1, day=None, total=False):
    if not KEY_RE.fullmatch(key): return
    day = day or today()
    with _lock:
        b = _buf.setdefault(day, {}); b[key] = b.get(key, 0) + n
        if total: _tot[key] = _tot.get(key, 0) + n
    maybe_flush()
def once(sid, key):
    """True, jeśli ta sesja jeszcze nie była liczona dla klucza dziś."""
    day = today()
    h = hashlib.sha256((_salt(day) + "|" + sid + "|" + key).encode()).hexdigest()[:12]
    with _lock:
        s = _seen_day(day)
        if h in s: return False
        if len(s) < 200000: s.add(h)
        return True
def view(sid, key, lang=None):
    """Wyświetlenie (raz na sesję dziennie). Dla postów również unikalni widzowie i język."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", sid or ""): return False
    if not once(sid, key): return False
    add(key + ":v", total=key.startswith("post:"))
    if key.startswith(("post:", "item:")):
        if once(sid + "#u", key.split(":")[0] + ":" + key.split(":")[1]): add(key + ":u")
        if lang in ("pl", "en", "es", "de", "uk") and key.startswith("post:"): add(key + ":lang:" + lang)
    return True
def flush():
    global _last
    with _lock:
        buf, tot = dict(_buf), dict(_tot); _buf.clear(); _tot.clear(); _last = time.time()
        seen = {d: list(s) for d, s in _seen.items()}
    try:
        for day, inc in buf.items():
            cur = store.get("stats_d:" + day, {}) or {}
            for k, n in inc.items(): cur[k] = cur.get(k, 0) + n
            store.put("stats_d:" + day, cur)
            idx = store.get("stats_days", []) or []
            if day not in idx:
                idx = sorted(set(idx + [day]))[-KEEP_DAYS:]; store.put("stats_days", idx)
        if tot:
            T = store.get("stats_tot", {}) or {}
            for k, n in tot.items(): T[k] = T.get(k, 0) + n
            store.put("stats_tot", T)
        for d, s in seen.items(): store.put("stats_seen:" + d, s)
    except Exception as e:
        print("stats flush error", type(e).__name__)
        with _lock:
            for day, inc in buf.items():
                b = _buf.setdefault(day, {})
                for k, n in inc.items(): b[k] = b.get(k, 0) + n
            for k, n in tot.items(): _tot[k] = _tot.get(k, 0) + n
def maybe_flush():
    if time.time() - _last > 20: threading.Thread(target=flush, daemon=True).start()
def totals():
    T = store.get("stats_tot", {}) or {}
    with _lock:
        for k, n in _tot.items(): T[k] = T.get(k, 0) + n
    return T
def post_views(pid, T=None): return (T if T is not None else totals()).get("post:" + pid + ":v", 0)
def range_days(days):
    t = datetime.date.fromisoformat(today())
    return [(t - datetime.timedelta(days=i)).isoformat() for i in range(days)][::-1]
def series(days):
    """{day: {key: n}} za ostatnie N dni (z niezapisanym buforem)."""
    out = {}
    with _lock: buf = {d: dict(v) for d, v in _buf.items()}
    idx = set(store.get("stats_days", []) or [])
    for d in range_days(days):
        cur = (store.get("stats_d:" + d, {}) or {}) if d in idx else {}
        for k, n in buf.get(d, {}).items(): cur[k] = cur.get(k, 0) + n
        out[d] = cur
    return out
def threadsafe_start():
    def loop():
        while True:
            time.sleep(20)
            try:
                if _buf or _tot: flush()
            except Exception: pass
    threading.Thread(target=loop, daemon=True).start()
