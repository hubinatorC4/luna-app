"""Czat na żywo („Napisz do twórcy”): rozmowy odwiedzających i skrzynka moderatora.
Przechowywanie: pamięć + data/livechat.json (na darmowym Renderze dysk jest ulotny)."""
import base64, json, os, re, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "data", "livechat.json")
VID_RE = re.compile(r"[0-9a-f]{16,32}")
MAX_TEXT, MAX_NAME, MAX_MSGS, MAX_CONVS = 2000, 40, 300, 1000
MAX_AVATAR = 24 * 1024  # bajty po zdekodowaniu
_lock = threading.Lock()
_rl = {}  # klucz -> lista znaczników czasu
_seq = [0]
CONVS = {}

def _load():
    global CONVS
    try:
        import store
        d = store.get("livechat", None) if store.BACKEND == "postgres" else None
        if not isinstance(d, dict): d = json.load(open(FILE, encoding="utf-8"))
        CONVS = d.get("convs", {}); _seq[0] = int(d.get("seq", 0))
    except Exception:
        CONVS = {}
_load()

def _snap():
    with _lock: return json.loads(json.dumps({"convs": CONVS, "seq": _seq[0]}))

def _save():
    try:
        import store
        if store.BACKEND == "postgres":   # trwale w Postgresie (zapis odroczony o 2 s – seria wiadomości = jeden zapis)
            store.put_later("livechat", _snap); return
    except Exception: pass
    try:
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        tmp = FILE + ".tmp"
        json.dump({"convs": CONVS, "seq": _seq[0]}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, FILE)
    except Exception:
        pass

def clean_text(s, n):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]", "", str(s or ""))
    return s.strip()[:n]

def clean_avatar(a):
    import imgsafe
    return imgsafe.safe_avatar_dataurl(a, MAX_AVATAR)

def rate_ok(key, per_min, per_day):
    now = time.time()
    with _lock:
        ts = [t for t in _rl.get(key, []) if now - t < 86400]
        if len([t for t in ts if now - t < 60]) >= per_min or len(ts) >= per_day:
            _rl[key] = ts; return False
        ts.append(now); _rl[key] = ts
        if len(_rl) > 20000:
            for k in list(_rl)[:5000]: _rl.pop(k, None)
        return True

def _msg(frm, text, name=""):
    _seq[0] += 1
    m = {"id": _seq[0], "from": frm, "text": text, "t": int(time.time() * 1000)}
    if name: m["name"] = name
    return m

def _view(c, since=0):
    return [m for m in c["msgs"] if m["id"] > since]

def visitor_send(vid, name, avatar, text, notice, ring=None, tier=""):
    if not VID_RE.fullmatch(vid or ""): raise ValueError("bad id")
    text = clean_text(text, MAX_TEXT); name = clean_text(name, MAX_NAME) or "Gość"
    if not text: raise ValueError("empty")
    with _lock:
        c = CONVS.get(vid)
        if not c:
            if len(CONVS) >= MAX_CONVS:
                old = sorted(CONVS.items(), key=lambda kv: kv[1]["updated"])[0][0]; CONVS.pop(old, None)
            c = CONVS[vid] = {"vid": vid, "created": int(time.time() * 1000), "msgs": [], "unread": 0, "visitor_unread": 0}
        c["name"] = name; c["avatar"] = clean_avatar(avatar); c["ring"] = ring; c["tier"] = tier if tier in ("premium", "pro") else ""
        first = not any(m["from"] == "visitor" for m in c["msgs"])
        c["msgs"].append(dict(_msg("visitor", text, name), tier=c["tier"]))
        if first and notice: c["msgs"].append(_msg("system", notice))
        c["msgs"] = c["msgs"][-MAX_MSGS:]
        c["unread"] += 1; c["updated"] = int(time.time() * 1000)
        _save()
        return list(c["msgs"])

def visitor_poll(vid, since=0, mark=True):
    if not VID_RE.fullmatch(vid or ""): raise ValueError("bad id")
    with _lock:
        c = CONVS.get(vid)
        if not c: return [], 0
        unread = c.get("visitor_unread", 0)
        if mark and unread: c["visitor_unread"] = 0; _save()
        return _view(c, since), unread

def inbox():
    with _lock:
        out = []
        for c in CONVS.values():
            last = next((m for m in reversed(c["msgs"]) if m["from"] != "system"), {})
            out.append({"vid": c["vid"], "name": c.get("name", "Gość"), "avatar": c.get("avatar", ""), "ring": c.get("ring"), "tier": c.get("tier", ""), "unread": c.get("unread", 0),
                        "updated": c.get("updated", 0), "count": len(c["msgs"]), "last": (last.get("text", "") or "")[:120], "last_from": last.get("from", "")})
        out.sort(key=lambda x: -x["updated"])
        return {"convs": out, "unread": sum(x["unread"] for x in out)}

def conv(vid, mark=True):
    with _lock:
        c = CONVS.get(vid)
        if not c: raise KeyError("not found")
        if mark and c.get("unread"): c["unread"] = 0; _save()
        return {"vid": vid, "name": c.get("name", "Gość"), "avatar": c.get("avatar", ""), "ring": c.get("ring"), "tier": c.get("tier", ""), "msgs": list(c["msgs"])}

def reply(vid, text):
    text = clean_text(text, MAX_TEXT)
    if not text: raise ValueError("empty")
    with _lock:
        c = CONVS.get(vid)
        if not c: raise KeyError("not found")
        c["msgs"].append(_msg("moderator", text)); c["msgs"] = c["msgs"][-MAX_MSGS:]
        c["visitor_unread"] = c.get("visitor_unread", 0) + 1; c["unread"] = 0; c["updated"] = int(time.time() * 1000)
        _save(); return list(c["msgs"])

def delete(vid):
    with _lock:
        CONVS.pop(vid, None); _save()
