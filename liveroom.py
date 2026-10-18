"""Luna Live – transmisja na żywo: stan pokoju, widzowie (prawdziwe połączenia), czat, kolejka pytań, bieżąca odpowiedź z dźwiękiem."""
import json, os, threading, time
import livechat

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "data", "liveroom.json")
VIEWER_TTL = 15  # s – widz liczy się, jeśli odpytał serwer w ciągu ostatnich 15 s
lock = threading.Lock()
S = {"mode": "auto", "on": False, "topic": "", "started": 0, "auto": False, "seq": 0, "chat": [], "queue": [], "current": None, "banned": [], "history": []}
viewers = {}  # vid -> last seen
jobs = []       # zadania mowy dla Luny: {"kind","text","caption","title"}
greet = []      # pseudonimy do powitania
greeted = set() # vid już powitane w tej transmisji
cmd_last = {}   # vid -> czas ostatniej komendy

def _load():
    try:
        import store
        d = store.get("liveroom", None) if store.BACKEND == "postgres" else None
        if not isinstance(d, dict): d = json.load(open(FILE, encoding="utf-8"))
        S.update({k: d[k] for k in S if k in d})
    except Exception: pass
_load()

def _snap():
    with lock: return json.loads(json.dumps(S))

def save():
    try:
        import store
        if store.BACKEND == "postgres":
            store.put_later("liveroom", _snap); return
    except Exception: pass
    try:
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        json.dump(S, open(FILE + ".tmp", "w", encoding="utf-8"), ensure_ascii=False); os.replace(FILE + ".tmp", FILE)
    except Exception: pass

def now_ms(): return int(time.time() * 1000)

def nid():
    S["seq"] += 1; return S["seq"]

def touch(vid):
    t = time.time()
    with lock:
        if vid and livechat.VID_RE.fullmatch(vid): viewers[vid] = t
        for k in [k for k, v in viewers.items() if t - v > VIEWER_TTL]: viewers.pop(k, None)
        return len(viewers)

def public_state(since=0, mod=False):
    with lock:
        st = {"on": S["on"], "mode": S["mode"], "jobs": len(jobs), "topic": S["topic"], "started": S["started"], "now": now_ms(), "auto": S["auto"],
              "chat": [m for m in S["chat"] if m["id"] > since], "last_id": S["chat"][-1]["id"] if S["chat"] else 0,
              "ids": [m["id"] for m in S["chat"]][-200:], "current": S["current"], "history": S["history"][-5:],
              "queue_len": len([q for q in S["queue"] if q["status"] == "pending"])}
        if mod:
            st["queue"] = [q for q in S["queue"] if q["status"] == "pending"]
            st["banned"] = S["banned"]
        return st

def post(vid, name, avatar, text, ask, ring=None, tier=""):
    if not livechat.VID_RE.fullmatch(vid or ""): raise ValueError("bad id")
    text = livechat.clean_text(text, 300); name = livechat.clean_text(name, 40) or "Widz"
    if not text: raise ValueError("Wiadomość jest pusta.")
    with lock:
        if not S["on"]: raise PermissionError("Transmisja jest wyłączona.")
        if vid[:8] in S["banned"]: raise PermissionError("Nie możesz pisać na tym czacie.")
        m = {"id": nid(), "uid": vid[:8], "name": name, "avatar": livechat.clean_avatar(avatar), "text": text, "t": now_ms(), "ask": bool(ask)}
        if ring: m["ring"] = ring
        if tier in ("premium", "pro"): m["tier"] = tier
        S["chat"].append(m); S["chat"] = S["chat"][-200:]
        if ask:
            S["queue"].append({"id": m["id"], "uid": m["uid"], "name": name, "text": text, "t": m["t"], "status": "pending"})
            S["queue"] = S["queue"][-100:]
        save(); return m

def begin(topic=""):
    """Rozpoczęcie transmisji (ręcznie albo z harmonogramu)."""
    with lock:
        S.update(on=True, topic=livechat.clean_text(topic, 120) or S.get("topic", ""), started=now_ms(), chat=[], queue=[], current=None, history=[])
        jobs.clear(); greet.clear(); greeted.clear(); save()

def end():
    with lock:
        S.update(on=False, current=None); S["queue"] = []; jobs.clear(); greet.clear(); save()

def set_mode(m):
    with lock: S["mode"] = m if m in ("auto", "on", "off") else "auto"; save()

def set_topic(t):
    with lock: S["topic"] = livechat.clean_text(t, 120); save()

def add_job(job, front=False):
    with lock:
        if len(jobs) >= 6 and not front: return False
        jobs.insert(0, job) if front else jobs.append(job); return True

def pop_job():
    with lock: return jobs.pop(0) if jobs else None

def add_greet(vid, name):
    name = livechat.clean_text(name, 24)
    with lock:
        if not S["on"] or not name or vid in greeted or vid[:8] in S["banned"]: return
        greeted.add(vid); greet.append(name)

def take_greets():
    with lock:
        g = greet[:6]; del greet[:6]; return g

def cmd_ok(vid, gap=60):
    t = time.time()
    with lock:
        if t - cmd_last.get(vid, 0) < gap: return False
        cmd_last[vid] = t; return True

def set_current(cur):
    with lock:
        if S["current"]: S["history"] = (S["history"] + [S["current"]])[-20:]
        S["current"] = cur; save()

def take_question(qid):
    with lock:
        for q in S["queue"]:
            if q["id"] == qid and q["status"] == "pending":
                q["status"] = "answered"; save(); return dict(q)
    return None

def next_pending():
    with lock:
        for q in S["queue"]:
            if q["status"] == "pending": return q["id"]
    return None

def reject(qid):
    with lock:
        for q in S["queue"]:
            if q["id"] == qid: q["status"] = "rejected"
        save()

def delete_msg(mid):
    with lock:
        S["chat"] = [m for m in S["chat"] if m["id"] != mid]
        S["queue"] = [q for q in S["queue"] if q["id"] != mid]; save()

def ban(uid, on=True):
    uid = str(uid)[:8]
    with lock:
        if on and uid not in S["banned"]:
            S["banned"].append(uid)
            S["chat"] = [m for m in S["chat"] if m["uid"] != uid]
            S["queue"] = [q for q in S["queue"] if q["uid"] != uid]
        if not on and uid in S["banned"]: S["banned"].remove(uid)
        save()

def set_auto(v):
    with lock: S["auto"] = bool(v); save()

def busy():
    c = S["current"]
    return bool(c) and now_ms() < c["start"] + c["dur"] * 1000 + 2500
