# -*- coding: utf-8 -*-
"""Bitwy agentek: dwie agentki AI naprzeciw siebie w scenerii, głosowanie widzów i czat na żywo.
Zasady uczciwości (nie do wyłączenia):
- startują tylko agentki AI: Luna (oficjalna agentka AI) i zatwierdzone przez moderatora agentki AI użytkowników, które same się zgłosiły;
  nigdy prawdziwe osoby ani prawdziwa agentka głosowa;
- dobór par: najpopularniejsza kontra druga w rankingu prawdziwego zaangażowania (te same filtry antybotowe co Polecane);
- mniej niż 2 uprawnione agentki = uczciwy stan oczekiwania, bez fikcyjnych rywalek, głosów i widzów;
- 1 głos na konto (i na urządzenie) w bitwie, bez głosowania na własną agentkę; liczą się tylko konta po filtrze antybotowym;
- bitwa trwa od 24 h do 7 dni (czas ustalany przy tworzeniu, pilnowany po stronie serwera), głosowanie zamyka się samo, zwycięzca jest ogłaszany;
- nagroda: odznaka 🏆 przy agentce i wyróżnienie „Zwyciężczyni” na karcie Bitew przez 24 h. Bez nagród pieniężnych."""
import hashlib, re, secrets, threading, time
import store, social, antibot, notify, nicktier

_lock = threading.Lock()
MIN_H, MAX_H, DEF_H = 24, 168, 72
CHAMP_H = 24
NEED = 2
REPORT_HIDE = 3
SCENES = ["city", "studio", "promenade", "winter", "gala", "garden"]
ENTER_PLAN = "premium"          # każdy płatny plan (Premium, Pro) może zgłosić agentkę
LUNA = {"id": "luna", "name": "Luna", "img": "/catalog/luna/outfit_sweter.jpg", "official": True}
LUNA_TARGETS = ["agent:luna-" + n for n in social.LUNA_GAL]

_view = {}  # skrót urządzenia -> ostatnie odpytanie (prawdziwi oglądający w ostatnich 45 s; bez botów)
def touch(dev):
    now = time.time(); h = hashlib.sha256(("btv:" + str(dev)).encode()).hexdigest()[:12]
    with _lock:
        _view[h] = now
        for k in [k for k, t in _view.items() if now - t > 45]: _view.pop(k, None)
def viewers():
    now = time.time(); return sum(1 for t in list(_view.values()) if now - t <= 45)

def _entries(): return store.get("bt_entries", []) or []
def _state(): return store.get("bt_state", {}) or {}
def _cfg(): return store.get("bt_cfg", {}) or {}

def duration_h():
    try: h = int(_cfg().get("hours", DEF_H))
    except (TypeError, ValueError): h = DEF_H
    return max(MIN_H, min(MAX_H, h))

def set_duration(h):
    h = int(h)
    if not MIN_H <= h <= MAX_H: raise ValueError(f"Czas bitwy: od {MIN_H} do {MAX_H} godzin.")
    c = _cfg(); c["hours"] = h; store.put("bt_cfg", c); return h

def excluded():
    """Głosy, które się nie liczą: konta ukryte przez filtr antybotowy; konta bez potwierdzonego e-maila – gdy weryfikacja e-mail działa."""
    X = antibot.excluded()
    return X if notify.email_enabled() else set(antibot._cache["hidden"])

def _reports(target):
    return sum(1 for r in (store.get("social_reports", []) or []) if r["target"] == target)

# ---------- zgłoszenia agentek ----------
def name_ok(n):
    n = re.sub(r"[<>\x00-\x1f]", "", str(n or "")).strip()[:24]
    if len(n) < 2: raise ValueError("Podaj imię agentki (min. 2 znaki).")
    if set(re.findall(r"\w+", social._norm(n))) & social._BADSET: raise ValueError("Wybierz inne imię agentki.")
    if re.search(r"\b(luna|moderator|admin)\b", social._norm(n)): raise ValueError("To imię jest zarezerwowane.")
    return n

def my_entry(uid):
    if not uid: return None
    return next((e for e in _entries() if e["uid"] == uid and e["status"] in ("pending", "approved")), None)

def enter(uid, d):
    if not uid: raise PermissionError("Zaloguj się, aby zgłosić agentkę.")
    ak = "u:" + uid
    if social.banned(ak): raise PermissionError("Twoje konto ma zablokowaną możliwość udziału w bitwach.")
    if my_entry(uid): raise ValueError("Masz już zgłoszoną agentkę. Najpierw ją wycofaj.")
    if d.get("modest") is not True: raise ValueError("Potwierdź, że agentka jest w pełni ubrana i przedstawiona skromnie.")
    if d.get("rules") is not True: raise ValueError("Zaakceptuj zasady Bitew agentek.")
    name = name_ok(d.get("name"))
    url, _info = social.avatars_check_wall(d.get("image"), d.get("img_decl"))
    eid = secrets.token_hex(5)
    e = {"id": eid, "uid": uid, "ak": ak, "name": name, "t": int(time.time()), "status": "pending", "wins": 0, "bt_votes": 0}
    with _lock:
        I = store.get("bt_img", {}) or {}; I[eid] = url; store.put("bt_img", dict(list(I.items())[-300:]))
        E = _entries(); E.append(e); store.put("bt_entries", E[-1000:])
    return e

def withdraw(uid):
    with _lock:
        E = _entries(); ch = False
        for e in E:
            if e["uid"] == uid and e["status"] in ("pending", "approved"): e["status"] = "withdrawn"; ch = True
        if ch: store.put("bt_entries", E)
    if ch: _cancel_if_in_battle(lambda c: c.get("id") != "luna" and _owner(c["id"]) == uid, "withdrawn")
    return ch

def entry_img(eid, uid=None, admin=False):
    e = next((x for x in _entries() if x["id"] == eid), None)
    if not e: return None
    if e["status"] == "approved" or admin or (uid and e["uid"] == uid) or _in_history(eid):
        return (store.get("bt_img", {}) or {}).get(eid)
    return None

def _in_history(eid):
    st = _state()
    return any(eid in (b["a"]["id"], b["b"]["id"]) for b in ([st["cur"]] if st.get("cur") else []) + st.get("hist", []))

# ---------- ranking (prawdziwe zaangażowanie, filtr antybotowy jak w Polecanych) ----------
def _eligible():
    X = antibot.excluded(); XA = excluded(); V = social._votes(); C = social._cmts()
    cmc = {}
    for c in C:
        if c["status"] == "approved" and c["author"] not in X: cmc[c["target"]] = cmc.get(c["target"], 0) + 1
    def sc(targets, extra):
        up = dn = cm = 0
        for t in targets:
            c = social.counts(t, None, V, X); up += c["up"]; dn += c["down"]; cm += cmc.get(t, 0)
        return round(up - 0.5 * dn + 2 * cm + extra, 2)
    lu = _cfg().get("luna", {"wins": 0, "bt_votes": 0})
    out = [dict(LUNA, score=sc(LUNA_TARGETS, lu.get("bt_votes", 0)), wins=lu.get("wins", 0), t=0)]
    for e in _entries():
        if e["status"] != "approved" or social.banned(e["ak"]) or e["ak"] in XA: continue
        tg = "agent:bt-" + e["id"]
        if _reports(tg) >= REPORT_HIDE and not e.get("cleared"): continue
        out.append({"id": e["id"], "uid": e["uid"], "name": e["name"], "img": "/api/battles/img/" + e["id"], "official": False,
                    "score": sc([tg], e.get("bt_votes", 0)), "wins": e.get("wins", 0), "t": e["t"]})
    out.sort(key=lambda x: (-x["score"], x["t"]))
    return out

def _pub_c(c):
    return {k: c.get(k) for k in ("id", "name", "img", "official", "wins")} | {"target": "agent:" + ("luna-" + social.LUNA_GAL[0] if c["id"] == "luna" else "bt-" + c["id"])}

# ---------- cykl bitwy ----------
def _finalize(st, now, reason="end"):
    b = st.get("cur")
    if not b: return
    X = excluded()
    va = sum(1 for k, s in b["votes"].items() if s == "a" and k not in X); vb = sum(1 for k, s in b["votes"].items() if s == "b" and k not in X)
    win = None if reason != "end" or va == vb else ("a" if va > vb else "b")
    res = {"id": b["id"], "a": b["a"], "b": b["b"], "scene": b["scene"], "start": b["start"], "end": min(now, b["end"]), "va": va, "vb": vb,
           "winner": win, "reason": reason, "hours": b["hours"]}
    st["hist"] = ([res] + st.get("hist", []))[:30]; st["cur"] = None
    if win:
        w = b[win]; st["champ"] = {"c": w, "bid": b["id"], "until": int(res["end"] + CHAMP_H * 3600), "votes": max(va, vb),
                                   "pct": round(max(va, vb) * 100 / (va + vb)), "a": b["a"], "b": b["b"], "va": va, "vb": vb, "winner": win, "scene": b["scene"]}
    # zapis prawdziwych głosów i zwycięstw do rankingu
    E = _entries(); cfg = _cfg(); ch = False
    for side, n in (("a", va), ("b", vb)):
        c = b[side]
        if c["id"] == "luna":
            lu = cfg.setdefault("luna", {"wins": 0, "bt_votes": 0}); lu["bt_votes"] = lu.get("bt_votes", 0) + n
            if win == side: lu["wins"] = lu.get("wins", 0) + 1
        else:
            for e in E:
                if e["id"] == c["id"]:
                    e["bt_votes"] = e.get("bt_votes", 0) + n
                    if win == side: e["wins"] = e.get("wins", 0) + 1
                    ch = True
    store.put("bt_cfg", cfg)
    if ch: store.put("bt_entries", E)

def tick(now=None):
    """Zamyka zakończone bitwy i – jeśli są co najmniej 2 uprawnione agentki – tworzy nową (top 1 kontra top 2)."""
    now = int(now or time.time())
    with _lock:
        st = _state(); ch = False
        if st.get("cur") and now >= st["cur"]["end"]: _finalize(st, now); ch = True
        if not st.get("cur"):
            el = _eligible()
            if len(el) >= NEED:
                h = duration_h(); n = st.get("n", 0)
                st["cur"] = {"id": secrets.token_hex(5), "a": _pub_c(el[0]), "b": _pub_c(el[1]), "scene": SCENES[n % len(SCENES)],
                             "start": now, "end": now + h * 3600, "hours": h, "votes": {}, "devs": {}}
                st["n"] = n + 1; ch = True
        if ch: store.put("bt_state", st)
        return st

def _cancel_if_in_battle(pred, reason):
    with _lock:
        st = _state(); b = st.get("cur")
        if b and (pred(b["a"]) or pred(b["b"])): _finalize(st, int(time.time()), reason); store.put("bt_state", st)

def public(uid=None, dev=""):
    st = tick(); now = int(time.time()); X = excluded()
    voter = "u:" + uid if uid else None
    out = {"now": now, "viewers": viewers(), "need": NEED, "min_h": MIN_H, "max_h": MAX_H, "scenes": SCENES, "enter_plan": ENTER_PLAN}
    b = st.get("cur")
    if b:
        va = sum(1 for k, s in b["votes"].items() if s == "a" and k not in X); vb = sum(1 for k, s in b["votes"].items() if s == "b" and k not in X)
        own = uid and any(c.get("id") != "luna" and _owner(c["id"]) == uid for c in (b["a"], b["b"]))
        out.update(state="live", battle={"id": b["id"], "a": b["a"], "b": b["b"], "scene": b["scene"], "start": b["start"], "end": b["end"], "hours": b["hours"],
                                         "votes": {"a": va, "b": vb}, "mine": b["votes"].get(voter) if voter else None, "own": bool(own)})
    else:
        el = _eligible(); out.update(state="waiting", eligible=len(el), missing=max(0, NEED - len(el)))
    ch = st.get("champ")
    if ch and ch["until"] > now: out["champion"] = ch
    out["last"] = [{k: h[k] for k in ("id", "a", "b", "scene", "end", "va", "vb", "winner", "reason")} for h in st.get("hist", [])[:5]]
    me = my_entry(uid)
    out["my_entry"] = {"id": me["id"], "name": me["name"], "status": me["status"], "img": "/api/battles/img/" + me["id"], "wins": me.get("wins", 0)} if me else None
    return out

def _owner(eid):
    e = next((x for x in _entries() if x["id"] == eid), None); return e["uid"] if e else None

def vote(uid, dev, bid, side):
    if not uid: raise PermissionError("Zaloguj się, aby głosować – 1 konto = 1 głos.")
    if side not in ("a", "b"): raise ValueError("bad side")
    ak = "u:" + uid; dh = hashlib.sha256(("btdev:" + str(dev)).encode()).hexdigest()[:16]
    if social.banned(ak): raise PermissionError("Twoje konto nie może głosować.")
    tick()
    with _lock:
        st = _state(); b = st.get("cur")
        if not b or b["id"] != bid: raise ValueError("Ta bitwa już się zakończyła – głosowanie jest zamknięte.")
        if int(time.time()) >= b["end"]: raise ValueError("Głosowanie jest zamknięte.")
        if any(c["id"] != "luna" and _owner(c["id"]) == uid for c in (b["a"], b["b"])): raise PermissionError("Nie możesz głosować w bitwie swojej agentki.")
        if ak in b["votes"]: raise ValueError("Już oddałeś głos w tej bitwie. 1 konto = 1 głos.")
        if b.setdefault("devs", {}).get(dh) not in (None, ak): raise ValueError("Z tego urządzenia oddano już głos w tej bitwie.")
        b["votes"][ak] = side; b["devs"][dh] = ak; store.put("bt_state", st)
    return public(uid, dev)

# ---------- czat na żywo ----------
def _chat(): return store.get("bt_chat", {}) or {}

def chat_list(bid, uid=None, since=0):
    X = excluded(); me = "u:" + uid if uid else None
    L = _chat().get(bid, [])
    items = [{"id": m["id"], "nick": m["nick"], "tier": nicktier.of_author(m["ak"]), "text": m["text"], "t": m["t"], "mine": m["ak"] == me}
             for m in L if m["id"] > since and ((not m.get("hidden") and m["ak"] not in X) or m["ak"] == me)]
    return {"items": items[-80:], "last": L[-1]["id"] if L else 0}

def chat_post(uid, nick, bid, text):
    if not uid: raise PermissionError("Zaloguj się, aby pisać na czacie bitwy.")
    ak = "u:" + uid
    if social.banned(ak): raise PermissionError("Nie możesz pisać na tym czacie.")
    text = social.check_text(text, 300)
    try: nick = social.nick_ok(nick)
    except ValueError: nick = "Widz " + uid[:4]
    with _lock:
        st = _state(); b = st.get("cur")
        if not b or b["id"] != bid: raise ValueError("Czat tej bitwy jest zamknięty.")
        C = _chat(); L = C.get(bid, []); mid = (L[-1]["id"] + 1) if L else 1
        m = {"id": mid, "ak": ak, "nick": nick, "text": text, "t": int(time.time()), "reports": [], "hidden": False}
        L.append(m); C[bid] = L[-300:]
        for k in [k for k in C if k != bid and k not in [h["id"] for h in st.get("hist", [])[:3]]]: C.pop(k, None)
        store.put("bt_chat", C)
    return m, L

def chat_report(uid, dev, bid, mid):
    who = ("u:" + uid) if uid else ("d:" + hashlib.sha256(str(dev).encode()).hexdigest()[:20])
    with _lock:
        C = _chat()
        for m in C.get(bid, []):
            if m["id"] == int(mid):
                if who not in m["reports"]: m["reports"].append(who)
                if len(m["reports"]) >= REPORT_HIDE: m["hidden"] = True
        store.put("bt_chat", C)

# ---------- moderacja ----------
def admin_list():
    st = tick(); C = _chat()
    E = [dict(e, reports=_reports("agent:bt-" + e["id"]), img="/api/admin/battles/img/" + e["id"]) for e in _entries() if e["status"] in ("pending", "approved")]
    chat = [dict(m, bid=bid, nrep=len(m["reports"])) for bid, L in C.items() for m in L if m["reports"] or m.get("hidden")]
    return {"entries": sorted(E, key=lambda e: (e["status"] != "pending", -e["t"])), "cur": st.get("cur") and {k: v for k, v in st["cur"].items() if k not in ("votes", "devs")},
            "hist": st.get("hist", [])[:10], "hours": duration_h(), "chat_flagged": chat[-100:], "eligible": [{"id": c["id"], "name": c["name"], "score": c["score"]} for c in _eligible()]}

def admin_action(d):
    a = d.get("action"); i = str(d.get("id", ""))
    if a == "hours": set_duration(d.get("hours")); return admin_list()
    if a in ("approve", "reject", "remove", "clear_reports"):
        with _lock:
            E = _entries(); e = next((x for x in E if x["id"] == i), None)
            if not e: raise KeyError(i)
            if a == "approve": e["status"] = "approved"
            elif a == "reject": e["status"] = "rejected"
            elif a == "remove": e["status"] = "removed"
            else: e["cleared"] = True
            store.put("bt_entries", E)
        if a in ("reject", "remove"): _cancel_if_in_battle(lambda c: c.get("id") == i, "removed")
        return admin_list()
    if a in ("chat_delete", "chat_restore", "chat_ban"):
        bid = str(d.get("bid", "")); mid = int(d.get("mid", 0))
        with _lock:
            C = _chat(); L = C.get(bid, []); m = next((x for x in L if x["id"] == mid), None)
            if not m: raise KeyError(mid)
            if a == "chat_restore": m["hidden"] = False; m["reports"] = []
            else: m["hidden"] = True
            store.put("bt_chat", C)
        if a == "chat_ban":
            B = social._bans(); B.add(m["ak"]); store.put("social_bans", sorted(B))
        return admin_list()
    raise ValueError("bad action")
