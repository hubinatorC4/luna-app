"""Trwały magazyn klucz–wartość. Postgres (DATABASE_URL), a bez niego plik data/kv.json (ulotny na darmowym Renderze)."""
import json, os, threading
ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "data", "kv.json")
URL = os.getenv("DATABASE_URL", "").strip()
_lock = threading.Lock()
_mem = None
BACKEND = "file"
if URL:
    try:
        import psycopg
        with psycopg.connect(URL, connect_timeout=10) as c:
            c.execute("CREATE TABLE IF NOT EXISTS luna_kv (k TEXT PRIMARY KEY, v JSONB NOT NULL, updated TIMESTAMPTZ DEFAULT now())")
        BACKEND = "postgres"
    except Exception as e:
        print("Postgres niedostępny, używam pliku:", repr(e)[:200])

def _file():
    global _mem
    if _mem is None:
        try: _mem = json.load(open(FILE, encoding="utf-8"))
        except Exception: _mem = {}
    return _mem

def get(k, default=None):
    if BACKEND == "postgres":
        try:
            import psycopg
            with psycopg.connect(URL, connect_timeout=10) as c:
                r = c.execute("SELECT v FROM luna_kv WHERE k=%s", (k,)).fetchone()
                return r[0] if r else default
        except Exception as e:
            print("kv get error", repr(e)[:200]); return default
    with _lock: return json.loads(json.dumps(_file().get(k, default)))

def put(k, v):
    if BACKEND == "postgres":
        import psycopg
        from psycopg.types.json import Jsonb
        with psycopg.connect(URL, connect_timeout=10) as c:
            c.execute("INSERT INTO luna_kv (k, v) VALUES (%s, %s) ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v, updated=now()", (k, Jsonb(v)))
        return
    with _lock:
        d = _file(); d[k] = v
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        json.dump(d, open(FILE + ".tmp", "w", encoding="utf-8"), ensure_ascii=False); os.replace(FILE + ".tmp", FILE)

def keys():
    """Lista kluczy magazynu (do migracji)."""
    if BACKEND == "postgres":
        import psycopg
        with psycopg.connect(URL, connect_timeout=10) as c:
            return [r[0] for r in c.execute("SELECT k FROM luna_kv").fetchall()]
    with _lock: return list(_file().keys())

def status():
    return {"backend": BACKEND, "persistent": BACKEND == "postgres"}
