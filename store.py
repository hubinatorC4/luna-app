"""Trwały magazyn klucz–wartość.

Postgres, gdy jest DATABASE_URL (Render: wewnętrzny adres bazy „luna-db”), a bez niego plik data/kv.json (tylko do pracy lokalnej –
na darmowym Renderze dysk jest ulotny i znika przy każdym wdrożeniu).

Postgres:
- tabele zakładane idempotentnie przy starcie (migracje w SCHEMA, numer wersji w luna_schema, blokada doradcza – dwie instancje naraz nie migrują);
- pula połączeń (wielokrotnego użytku) i ponowienie po zerwanym połączeniu;
- krótka pamięć podręczna (3 s, zapis-przez): mniej zapytań, każdy zapis od razu do bazy;
- błąd odczytu z bazy = wyjątek StoreError (nigdy „pusty słownik”, który potem nadpisałby dane);
- jednorazowe przeniesienie danych z plików (data/kv.json, config.json, catalog.json, czat na żywo) i z poprzedniej instancji (handover);
- codzienna kopia logiczna w tabeli luna_backups (7 ostatnich dni) – chroni przed błędem aplikacji, NIE przed utratą samej bazy.
"""
import copy, gzip, hashlib, hmac, json, os, queue, secrets, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
FILE = os.path.join(DATA, "kv.json")
URL = os.getenv("DATABASE_URL", "").strip()
_lock = threading.Lock()
_mem = None
BACKEND = "file"
ERROR = ""
CACHE_MAX = 256 * 1024                       # większe wartości (zdjęcia AI w base64) nie siedzą w pamięci
NOCACHE = ("agimg:", "upl:")
CACHE_TTL = float(os.getenv("LUNA_CACHE_TTL", "3"))   # krótko: przy wdrożeniu przez chwilę działają dwie instancje naraz
BACKUP_SKIP = ("agimg:", "upl:")             # kopia dzienna bez ciężkich plików graficznych
BACKUP_KEEP = 7

class StoreError(RuntimeError):
    pass

SCHEMA = [
    (1, ["CREATE TABLE IF NOT EXISTS luna_kv (k TEXT PRIMARY KEY, v JSONB NOT NULL, updated TIMESTAMPTZ DEFAULT now())"]),
    (2, ["CREATE TABLE IF NOT EXISTS luna_meta (k TEXT PRIMARY KEY, v JSONB NOT NULL, updated TIMESTAMPTZ DEFAULT now())",
         "CREATE TABLE IF NOT EXISTS luna_backups (day DATE PRIMARY KEY, created TIMESTAMPTZ NOT NULL DEFAULT now(), n_keys INT NOT NULL, size_bytes INT NOT NULL, data BYTEA NOT NULL)",
         "CREATE INDEX IF NOT EXISTS luna_kv_updated ON luna_kv (updated)"]),
]

# ---------- pula połączeń ----------
_pool = queue.LifoQueue()
_pool_n = [0]
POOL_MAX = 8

def _connect():
    import psycopg
    c = psycopg.connect(URL, connect_timeout=10, autocommit=True)
    return c

def _getconn():
    try:
        c = _pool.get_nowait()
        if not c.closed: return c
    except queue.Empty:
        pass
    with _lock:
        new = _pool_n[0] < POOL_MAX
        if new: _pool_n[0] += 1
    if new:
        try: return _connect()
        except Exception:
            with _lock: _pool_n[0] -= 1
            raise
    return _pool.get(timeout=15)

def _putconn(c, bad=False):
    if bad or c.closed:
        try: c.close()
        except Exception: pass
        with _lock: _pool_n[0] -= 1
        return
    _pool.put(c)

def _run(fn):
    """fn(conn) z ponowieniem raz po zerwanym połączeniu."""
    import psycopg
    for attempt in (0, 1):
        c = _getconn()
        try:
            r = fn(c); _putconn(c); return r
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            _putconn(c, bad=True)
            if attempt: raise StoreError("baza niedostępna: " + type(e).__name__)
        except Exception:
            _putconn(c, bad=True); raise

def _migrate_schema():
    def f(c):
        c.execute("SELECT pg_advisory_lock(726173)")
        try:
            c.execute("CREATE TABLE IF NOT EXISTS luna_schema (version INT PRIMARY KEY, applied TIMESTAMPTZ DEFAULT now())")
            done = {r[0] for r in c.execute("SELECT version FROM luna_schema").fetchall()}
            for ver, stmts in SCHEMA:
                if ver in done: continue
                for s in stmts: c.execute(s)
                c.execute("INSERT INTO luna_schema (version) VALUES (%s) ON CONFLICT DO NOTHING", (ver,))
            return max([v for v, _ in SCHEMA])
        finally:
            c.execute("SELECT pg_advisory_unlock(726173)")
    return _run(f)

if URL:
    try:
        SCHEMA_VERSION = _migrate_schema()
        BACKEND = "postgres"
    except Exception as e:
        ERROR = type(e).__name__
        print("Postgres niedostępny, używam pliku:", repr(e)[:200].replace(URL, "<DATABASE_URL>"), file=sys.stderr)

# ---------- pamięć podręczna ----------
_cache = {}   # k -> (czas, wartość)
def _cp(v): return json.loads(json.dumps(v)) if isinstance(v, (dict, list)) else v
def _cacheable(k, v):
    if k.startswith(NOCACHE): return False
    try: return len(json.dumps(v)) <= CACHE_MAX
    except Exception: return False

def _file():
    global _mem
    if _mem is None:
        try: _mem = json.load(open(FILE, encoding="utf-8"))
        except Exception: _mem = {}
    return _mem

def _file_save():
    os.makedirs(DATA, exist_ok=True)
    json.dump(_file(), open(FILE + ".tmp", "w", encoding="utf-8"), ensure_ascii=False); os.replace(FILE + ".tmp", FILE)

def get(k, default=None):
    if BACKEND == "postgres":
        e = _cache.get(k)
        if e and time.time() - e[0] < CACHE_TTL: v = e[1]
        else:
            r = _run(lambda c: c.execute("SELECT v FROM luna_kv WHERE k=%s", (k,)).fetchone())
            v = r[0] if r else None
            if _cacheable(k, v): _cache[k] = (time.time(), v)
        return default if v is None else _cp(v)
    with _lock: return json.loads(json.dumps(_file().get(k, default)))

def put(k, v):
    if BACKEND == "postgres":
        from psycopg.types.json import Jsonb
        if v is None:
            _run(lambda c: c.execute("DELETE FROM luna_kv WHERE k=%s", (k,)))
            _cache.pop(k, None); return
        v = _cp(v)
        _run(lambda c: c.execute("INSERT INTO luna_kv (k, v) VALUES (%s, %s) ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v, updated=now()", (k, Jsonb(v))))
        if _cacheable(k, v): _cache[k] = (time.time(), v)
        else: _cache.pop(k, None)
        return
    with _lock:
        d = _file()
        if v is None: d.pop(k, None)
        else: d[k] = v
        _file_save()

def delete(k): put(k, None)

def keys(prefix=""):
    """Lista kluczy magazynu (do migracji / kopii)."""
    if BACKEND == "postgres":
        return [r[0] for r in _run(lambda c: c.execute("SELECT k FROM luna_kv WHERE k LIKE %s", (prefix.replace("%", r"\%").replace("_", r"\_") + "%",)).fetchall())]
    with _lock: return [k for k in _file().keys() if k.startswith(prefix)]

def has(k):
    if BACKEND == "postgres":
        return bool(_run(lambda c: c.execute("SELECT 1 FROM luna_kv WHERE k=%s", (k,)).fetchone()))
    with _lock: return k in _file()

def meta_get(k, default=None):
    if BACKEND != "postgres": return get("_meta:" + k, default)
    r = _run(lambda c: c.execute("SELECT v FROM luna_meta WHERE k=%s", (k,)).fetchone())
    return r[0] if r else default

def meta_put(k, v):
    if BACKEND != "postgres": return put("_meta:" + k, v)
    from psycopg.types.json import Jsonb
    _run(lambda c: c.execute("INSERT INTO luna_meta (k, v) VALUES (%s, %s) ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v, updated=now()", (k, Jsonb(v))))

# ---------- zapis odroczony (czat na żywo, Luna Live – częste małe zmiany) ----------
_later = {}
def put_later(k, getter, delay=2.0):
    """Zapisze getter() pod k najpóźniej po `delay` s (łączy serię zmian w jeden zapis)."""
    with _lock: _later.setdefault(k, [getter, time.time() + delay])

def flush():
    with _lock: items = list(_later.items()); _later.clear()
    for k, (g, _t) in items:
        try: put(k, g())
        except Exception as e: print("store flush %s %s" % (k, type(e).__name__), file=sys.stderr)

def _flusher():
    while True:
        time.sleep(1)
        now = time.time()
        with _lock: due = [k for k, (_g, t) in _later.items() if t <= now]
        for k in due:
            with _lock: it = _later.pop(k, None)
            if it:
                try: put(k, it[0]())
                except Exception as e:
                    print("store flush %s %s" % (k, type(e).__name__), file=sys.stderr)
                    with _lock: _later.setdefault(k, [it[0], time.time() + 3])   # ponów za chwilę
threading.Thread(target=_flusher, daemon=True).start()

def install_sigterm():
    """Render wysyła SIGTERM przy wdrożeniu – najpierw zapisujemy zaległe zmiany."""
    import signal
    def h(signum, frame):
        try: flush()
        finally: os._exit(0)
    try: signal.signal(signal.SIGTERM, h)
    except Exception: pass

# ---------- migawka (kopia / przeniesienie) ----------
def snapshot(skip=()):
    if BACKEND == "postgres":
        rows = _run(lambda c: c.execute("SELECT k, v FROM luna_kv").fetchall())
        return {k: v for k, v in rows if not (skip and k.startswith(tuple(skip)))}
    with _lock: return {k: v for k, v in json.loads(json.dumps(_file())).items() if not (skip and k.startswith(tuple(skip)))}

def import_missing(d, overwrite=()):
    """Dopisuje klucze, których nie ma w magazynie (nic nie nadpisuje, poza kluczami z `overwrite`). Zwraca liczbę dopisanych."""
    n = 0
    have = set(keys())
    for k, v in (d or {}).items():
        if not isinstance(k, str) or v is None or k.startswith("_meta:"): continue
        if k in have and k not in overwrite: continue
        put(k, v); n += 1
    return n

# ---------- jednorazowe przeniesienie danych z plików i z poprzedniej instancji ----------
def _handover_key():
    m = (os.getenv("LUNA_ADMIN_PASSWORD_HASH", "") + "|" + os.getenv("LUNA_ADMIN_CODE_HASH", "")).strip("|").strip()
    return hashlib.sha256(b"luna-kv-handover|" + m.encode()).digest() if len(m) >= 20 else b""

def handover_sign(ts, nonce):
    k = _handover_key()
    return hmac.new(k, ("%s|%s" % (ts, nonce)).encode(), hashlib.sha256).hexdigest() if k else ""

def handover_ok(ts, nonce, sig):
    """Tylko stara instancja bez bazy oddaje dane nowej (podpis z sekretu znanego obu instancjom, ważny 120 s)."""
    if BACKEND != "file" or not _handover_key(): return False
    try: ts = int(ts)
    except Exception: return False
    if abs(time.time() - ts) > 120 or not (16 <= len(str(nonce)) <= 64): return False
    return hmac.compare_digest(handover_sign(ts, nonce), str(sig or ""))

FILE_EXTRAS = {"config": "config.json", "catalog": "catalog.json", "livechat": "livechat.json", "liveroom": "liveroom.json"}

def handover_payload():
    """Wszystko, co stara instancja trzyma w plikach: magazyn kv + pliki konfiguracji/katalogu/czatu + wgrane pliki katalogu."""
    out = {"kv": snapshot(), "files": {}, "uploads": {}}
    for k, fn in FILE_EXTRAS.items():
        try: out["files"][k] = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        except Exception: pass
    up = os.path.join(DATA, "uploads"); tot = 0
    import base64
    for fn in (os.listdir(up) if os.path.isdir(up) else []):
        p = os.path.join(up, fn)
        try:
            b = open(p, "rb").read()
            if tot + len(b) > 40 * 1024 * 1024: break
            out["uploads"][fn] = base64.b64encode(b).decode(); tot += len(b)
        except Exception: pass
    return out

def _apply_payload(p, src):
    n = {"kv": 0, "files": 0, "uploads": 0}
    n["kv"] = import_missing(p.get("kv") or {})
    for k, v in (p.get("files") or {}).items():
        if k in FILE_EXTRAS and v and not has(k): put(k, v); n["files"] += 1
    for fn, b in (p.get("uploads") or {}).items():
        if isinstance(fn, str) and len(fn) < 40 and not has("upl:" + fn): put("upl:" + fn, {"b": b}); n["uploads"] += 1
    print("store: przeniesiono z %s: %s" % (src, n), flush=True)
    return n

def _from_files():
    p = {"kv": {}, "files": {}, "uploads": {}}
    try: p["kv"] = json.load(open(FILE, encoding="utf-8"))
    except Exception: pass
    for k, fn in FILE_EXTRAS.items():
        try: p["files"][k] = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        except Exception: pass
    return p

def _from_previous():
    """Przy pierwszym starcie z bazą: poprzednia instancja (jeszcze obsługuje ruch podczas wdrożenia) oddaje swoje dane."""
    import urllib.request
    base = (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PUBLIC_URL") or "https://luna-voice-coach.onrender.com").rstrip("/")
    if not _handover_key(): return None, "no-key"
    ts, nonce = int(time.time()), secrets.token_hex(16)
    rq = urllib.request.Request(base + "/api/internal/kv-handover", headers={"X-Luna-Ts": str(ts), "X-Luna-Nonce": nonce, "X-Luna-Sig": handover_sign(ts, nonce), "User-Agent": "luna-handover"})
    try:
        with urllib.request.urlopen(rq, timeout=45) as r: return json.loads(r.read().decode("utf-8")), "ok"
    except urllib.error.HTTPError as e: return None, "http-%d" % e.code
    except Exception as e: return None, type(e).__name__

def first_start_migration():
    """Idempotentne: pliki lokalne zawsze dopisują brakujące klucze; handover tylko, dopóki się nie uda (maks. 5 prób)."""
    if BACKEND != "postgres": return {"backend": BACKEND}
    res = {}
    try: res["files"] = _apply_payload(_from_files(), "plików")
    except Exception as e: res["files"] = "error " + type(e).__name__
    st = meta_get("handover", {}) or {}
    if not st.get("done") and int(st.get("tries", 0)) < 5:
        p, why = _from_previous()
        st["tries"] = int(st.get("tries", 0)) + 1; st["last"] = why; st["t"] = int(time.time())
        if p is not None:
            try: st["counts"] = _apply_payload(p, "poprzedniej instancji"); st["done"] = True
            except Exception as e: st["last"] = "apply " + type(e).__name__
        elif why in ("http-404", "http-403", "no-key"): st["done"] = True   # poprzednia instancja już na bazie / brak sekretu – nie ma czego przenosić
        meta_put("handover", st)
    res["handover"] = st
    return res

# ---------- codzienna kopia logiczna (w tej samej bazie) ----------
def backup_now(day=None):
    if BACKEND != "postgres": return None
    import datetime as _dt
    day = day or _dt.date.today().isoformat()
    snap = snapshot(skip=BACKUP_SKIP)
    raw = gzip.compress(json.dumps(snap, ensure_ascii=False).encode("utf-8"), 6)
    def f(c):
        c.execute("INSERT INTO luna_backups (day, n_keys, size_bytes, data) VALUES (%s, %s, %s, %s) ON CONFLICT (day) DO UPDATE SET created=now(), n_keys=EXCLUDED.n_keys, size_bytes=EXCLUDED.size_bytes, data=EXCLUDED.data",
                  (day, len(snap), len(raw), raw))
        c.execute("DELETE FROM luna_backups WHERE day NOT IN (SELECT day FROM luna_backups ORDER BY day DESC LIMIT %s)", (BACKUP_KEEP,))
    _run(f)
    return {"day": day, "keys": len(snap), "bytes": len(raw)}

def backups():
    if BACKEND != "postgres": return []
    rows = _run(lambda c: c.execute("SELECT day, created, n_keys, size_bytes FROM luna_backups ORDER BY day DESC").fetchall())
    return [{"day": str(d), "t": int(cr.timestamp()), "keys": n, "bytes": s} for d, cr, n, s in rows]

def backup_data(day):
    if BACKEND != "postgres": return None
    r = _run(lambda c: c.execute("SELECT data FROM luna_backups WHERE day=%s", (day,)).fetchone())
    return gzip.decompress(bytes(r[0])) if r else None

def backup_tick():
    """Wołane co godzinę: jeśli dziś jeszcze nie było kopii – robi ją."""
    if BACKEND != "postgres": return None
    import datetime as _dt
    today = _dt.date.today().isoformat()
    b = backups()
    if b and b[0]["day"] == today: return None
    return backup_now(today)

def db_info():
    if BACKEND != "postgres": return {}
    def f(c):
        size = c.execute("SELECT pg_database_size(current_database())").fetchone()[0]
        n = c.execute("SELECT count(*) FROM luna_kv").fetchone()[0]
        return {"db_bytes": int(size), "keys": int(n)}
    try: return _run(f)
    except Exception: return {}

def status():
    s = {"backend": BACKEND, "persistent": BACKEND == "postgres"}
    if URL and BACKEND != "postgres": s["error"] = ERROR or "connect"
    return s

def ping():
    if BACKEND != "postgres": return None
    try: _run(lambda c: c.execute("SELECT 1").fetchone()); return True
    except Exception: return False

MIGRATION = {}
if BACKEND == "postgres" and os.getenv("LUNA_NO_HANDOVER") != "1":
    try: MIGRATION = first_start_migration()
    except Exception as e:
        MIGRATION = {"error": type(e).__name__}; print("store migration", type(e).__name__, file=sys.stderr)
