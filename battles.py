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
import store, social, antibot, notify, nicktier, partners

_lock = threading.RLock()
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
    return any(eid in (b["a"]["id"], b["b"]["id"]) for b in _all(st) + st.get("hist", []))

# ---------- wyniki, punkty, ligi (tylko prawdziwe, rozstrzygnięte bitwy) ----------
PTS_WIN = 10
LEAGUES = [("braz", 0), ("srebro", 50), ("zloto", 150), ("platyna", 300), ("diament", 500)]
ELITE_N = 10

def league(pts):
    k = LEAGUES[0][0]
    for key, lo in LEAGUES:
        if pts >= lo: k = key
    return k

def next_league(pts):
    for key, lo in LEAGUES:
        if pts < lo: return {"key": key, "at": lo}
    return None

def _results(): return store.get("bt_results", []) or []

def _stats(since=0):
    """Statystyki z dziennika wyników: tylko bitwy zakończone normalnie (bez przerwanych przez moderację),
    głosy policzone przy zamknięciu po filtrze antybotowym. Wygrana = +10 pkt; porażka i remis = 0."""
    A = {}
    for r in _results():
        if r["t"] < since: continue
        for side in ("a", "b"):
            c = r[side]; s = A.setdefault(c["id"], {"wins": 0, "played": 0, "votes": 0, "last": 0, "uid": c.get("uid"), "titles": []})
            s["played"] += 1; s["votes"] += r["v" + side]
            if r["win"] == side:
                s["wins"] += 1; s["last"] = max(s["last"], r["t"]); s["titles"].append(r["scene"])
    for s in A.values():
        s["pts"] = s["wins"] * PTS_WIN; s["pct"] = round(s["wins"] * 100 / s["played"]) if s["played"] else 0
    return A

def _rank_key(s, t0=0):
    # punkty malejąco, potem % wygranych, potem prawdziwe głosy, potem kto pierwszy osiągnął wynik
    return (-s["pts"], -s["pct"], -s["votes"], s["last"] or t0 or 0)

def _agent_rows(A=None):
    A = A if A is not None else _stats()
    rows = [dict(LUNA, uid=None, t=0)] + [{"id": e["id"], "uid": e["uid"], "name": e["name"], "img": "/api/battles/img/" + e["id"], "official": False, "t": e["t"]}
                                         for e in _entries() if e["status"] == "approved" and not social.banned(e["ak"])]
    z = {"wins": 0, "played": 0, "votes": 0, "last": 0, "titles": [], "pts": 0, "pct": 0}
    out = []
    for r in rows:
        s = A.get(r["id"], z); out.append(dict(r, **{k: s[k] for k in z}))
    out.sort(key=lambda x: _rank_key(x, x["t"]))
    for i, r in enumerate(out):
        r["pos"] = i + 1; r["league"] = league(r["pts"]); r["elite"] = i < ELITE_N and r["pts"] > 0
    return out

def _badge_map():
    return {r["id"]: r for r in _agent_rows()}

# ---------- popularność (prawdziwe zaangażowanie, filtr antybotowy jak w Polecanych) – do doboru par ----------
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
    R = _badge_map()
    def info(i): r = R.get(i) or {}; return {k: r.get(k, d) for k, d in (("wins", 0), ("titles", []), ("pts", 0), ("league", "braz"), ("elite", False), ("pos", 0), ("votes", 0))}
    out = [dict(LUNA, t=0, **info("luna"))]; out[0]["score"] = sc(LUNA_TARGETS, out[0]["votes"])
    for e in _entries():
        if e["status"] != "approved" or social.banned(e["ak"]) or e["ak"] in XA: continue
        tg = "agent:bt-" + e["id"]
        if _reports(tg) >= REPORT_HIDE and not e.get("cleared"): continue
        r = dict({"id": e["id"], "uid": e["uid"], "name": e["name"], "img": "/api/battles/img/" + e["id"], "official": False, "t": e["t"]}, **info(e["id"]))
        r["score"] = sc([tg], r["votes"]); out.append(r)
    out.sort(key=lambda x: (-x["score"], x["t"]))
    return out

def _pub_c(c):
    return {k: c.get(k) for k in ("id", "name", "img", "official", "wins", "pts", "league", "elite")} | {"titles": list(c.get("titles") or [])} \
        | {"target": "agent:" + ("luna-" + social.LUNA_GAL[0] if c["id"] == "luna" else "bt-" + c["id"])}

# ---------- cykl bitew: pokazowa (globalne Top 2) + po jednej w każdej lidze ----------
def _all(st):
    return ([st["cur"]] if st.get("cur") else []) + [b for b in (st.get("lg") or {}).values() if b]

def _find(st, bid):
    return next((b for b in _all(st) if b["id"] == bid), None)

def _count(b, X):
    return (sum(1 for k, s in b["votes"].items() if s == "a" and k not in X), sum(1 for k, s in b["votes"].items() if s == "b" and k not in X))

def _finalize(st, b, now, reason="end"):
    X = excluded(); va, vb = _count(b, X)
    win = None if reason != "end" or va == vb else ("a" if va > vb else "b")
    res = {"id": b["id"], "a": b["a"], "b": b["b"], "scene": b["scene"], "lg": b.get("lg"), "start": b["start"], "end": min(now, b["end"]), "va": va, "vb": vb,
           "winner": win, "reason": reason, "hours": b["hours"]}
    st["hist"] = ([res] + st.get("hist", []))[:30]
    if b is st.get("cur"): st["cur"] = None
    else: st["lg"] = {k: v for k, v in (st.get("lg") or {}).items() if v is not b}
    if reason == "end":   # tylko rozstrzygnięte normalnie bitwy trafiają do punktów; przerwane = bez punktów
        R = _results()
        R.append({"bid": b["id"], "t": res["end"], "scene": b["scene"], "lg": b.get("lg"), "va": va, "vb": vb, "win": win,
                  "a": {"id": b["a"]["id"], "uid": _owner(b["a"]["id"])}, "b": {"id": b["b"]["id"], "uid": _owner(b["b"]["id"])}})
        store.put("bt_results", R[-5000:])
        try: _notify_result(b, va, vb, win, res["end"])
        except Exception: pass
    if win and not b.get("lg"):
        w = b[win]; st["champ"] = {"c": w, "bid": b["id"], "until": int(res["end"] + CHAMP_H * 3600), "votes": max(va, vb),
                                   "pct": round(max(va, vb) * 100 / (va + vb)), "a": b["a"], "b": b["b"], "va": va, "vb": vb, "winner": win, "scene": b["scene"]}

def _new(st, a, b, now, lg=None):
    h = duration_h(); n = st.get("n", 0); st["n"] = n + 1
    return {"id": secrets.token_hex(5), "a": _pub_c(a), "b": _pub_c(b), "scene": SCENES[n % len(SCENES)], "lg": lg,
            "start": now, "end": now + h * 3600, "hours": h, "votes": {}, "devs": {}}

def tick(now=None):
    """Zamyka zakończone bitwy; tworzy pokazową (globalnie najpopularniejsza kontra druga) i ligowe
    (najpopularniejsza kontra druga w tej samej lidze). Mniej niż 2 wolne agentki = brak bitwy, bez fikcji."""
    now = int(now or time.time())
    with _lock:
        st = _state(); ch = False
        for b in list(_all(st)):
            if now >= b["end"]: _finalize(st, b, now); ch = True
        busy = {c["id"] for b in _all(st) for c in (b["a"], b["b"])}
        el = None
        if not st.get("cur"):
            el = _eligible(); free = [c for c in el if c["id"] not in busy]
            if len(free) >= NEED:
                st["cur"] = _new(st, free[0], free[1], now); busy |= {free[0]["id"], free[1]["id"]}; ch = True
        lg = st.setdefault("lg", {})
        for key, _lo in LEAGUES:
            if lg.get(key): continue
            el = el if el is not None else _eligible()
            free = [c for c in el if c["id"] not in busy and c["league"] == key]
            if len(free) >= NEED:
                lg[key] = _new(st, free[0], free[1], now, key); busy |= {free[0]["id"], free[1]["id"]}; ch = True
        if ch: store.put("bt_state", st)
        return st

def _cancel_if_in_battle(pred, reason):
    with _lock:
        st = _state(); ch = False
        for b in list(_all(st)):
            if pred(b["a"]) or pred(b["b"]): _finalize(st, b, int(time.time()), reason); ch = True
        if ch: store.put("bt_state", st)

def _summary(b, X):
    va, vb = _count(b, X)
    return {"id": b["id"], "lg": b.get("lg"), "main": not b.get("lg"), "scene": b["scene"], "end": b["end"], "votes": {"a": va, "b": vb},
            "a": {k: b["a"].get(k) for k in ("id", "name", "img", "league")}, "b": {k: b["b"].get(k) for k in ("id", "name", "img", "league")}}

def public(uid=None, dev="", bid=None):
    st = tick(); now = int(time.time()); X = excluded()
    voter = "u:" + uid if uid else None
    out = {"now": now, "viewers": viewers(), "need": NEED, "min_h": MIN_H, "max_h": MAX_H, "scenes": SCENES, "enter_plan": ENTER_PLAN,
           "leagues": [{"key": k, "from": lo} for k, lo in LEAGUES], "pts_win": PTS_WIN}
    b = (bid and _find(st, bid)) or st.get("cur")
    if b:
        va, vb = _count(b, X)
        own = uid and any(c.get("id") != "luna" and _owner(c["id"]) == uid for c in (b["a"], b["b"]))
        out.update(state="live", battle={"id": b["id"], "lg": b.get("lg"), "a": b["a"], "b": b["b"], "scene": b["scene"], "start": b["start"], "end": b["end"], "hours": b["hours"],
                                         "votes": {"a": va, "b": vb}, "mine": b["votes"].get(voter) if voter else None, "own": bool(own)})
    else:
        el = _eligible(); out.update(state="waiting", eligible=len(el), missing=max(0, NEED - len(el)))
    out["others"] = [_summary(x, X) for x in _all(st)]
    ch = st.get("champ")
    if ch and ch["until"] > now: out["champion"] = ch
    out["last"] = [{k: h.get(k) for k in ("id", "a", "b", "scene", "lg", "end", "va", "vb", "winner", "reason")} for h in st.get("hist", [])[:5]]
    _mark_partners(out)
    me = my_entry(uid)
    if me:
        r = _badge_map().get(me["id"]) or {}
        out["my_entry"] = {"id": me["id"], "name": me["name"], "status": me["status"], "img": "/api/battles/img/" + me["id"],
                           "wins": r.get("wins", 0), "pts": r.get("pts", 0), "league": r.get("league", "braz"), "titles": r.get("titles", []), "pos": r.get("pos")}
    else: out["my_entry"] = None
    if uid:   # ostatnie prawdziwe wygrane agentek tego konta (do animacji „+10 pkt”, raz na bitwę)
        out["my_wins"] = [r["bid"] for r in _results()[-200:] if r["win"] and r[r["win"]].get("uid") == uid and now - r["t"] < 7 * 86400]
    return out

def _mark_partners(out):
    """Flaga „Agentka współpracująca” liczona na bieżąco (nigdy dla Luny), bez ujawniania właściciela."""
    E = {e["id"]: e["uid"] for e in _entries()}
    def mk(c):
        if isinstance(c, dict) and c.get("id") and c["id"] != "luna": c["partner"] = partners.is_partner(E.get(c["id"]))
    b = out.get("battle") or {}; mk(b.get("a")); mk(b.get("b"))
    ch = out.get("champion") or {}; mk(ch.get("c")); mk(ch.get("a")); mk(ch.get("b"))
    for h in out.get("last", []): mk(h.get("a")); mk(h.get("b"))
    for o in out.get("others", []): mk(o.get("a")); mk(o.get("b"))

def _owner(eid):
    if eid == "luna": return None
    e = next((x for x in _entries() if x["id"] == eid), None); return e["uid"] if e else None

def profile(aid):
    """Publiczny profil agentki: imię, obraz, punkty, liga, Elita, wygrane i tytuły (tylko z prawdziwych wyników)."""
    r = _badge_map().get(aid)
    if not r: return None
    return {k: r[k] for k in ("id", "name", "img", "official", "wins", "played", "pct", "pts", "league", "elite", "titles", "pos")} | {"next": next_league(r["pts"])}

def vote(uid, dev, bid, side):
    if not uid: raise PermissionError("Zaloguj się, aby głosować – 1 konto = 1 głos.")
    if side not in ("a", "b"): raise ValueError("bad side")
    ak = "u:" + uid; dh = hashlib.sha256(("btdev:" + str(dev)).encode()).hexdigest()[:16]
    if social.banned(ak): raise PermissionError("Twoje konto nie może głosować.")
    tick()
    with _lock:
        st = _state(); b = _find(st, bid)
        if not b: raise ValueError("Ta bitwa już się zakończyła – głosowanie jest zamknięte.")
        if int(time.time()) >= b["end"]: raise ValueError("Głosowanie jest zamknięte.")
        if any(c["id"] != "luna" and _owner(c["id"]) == uid for c in (b["a"], b["b"])): raise PermissionError("Nie możesz głosować w bitwie swojej agentki.")
        if ak in b["votes"]: raise ValueError("Już oddałeś głos w tej bitwie. 1 konto = 1 głos.")
        if b.setdefault("devs", {}).get(dh) not in (None, ak): raise ValueError("Z tego urządzenia oddano już głos w tej bitwie.")
        b["votes"][ak] = side; b["devs"][dh] = ak; store.put("bt_state", st)
    return public(uid, dev, bid)

# ---------- ranking: agentki (globalnie i w ligach) oraz Top użytkowników ----------
def _priv(): return set(store.get("bt_priv", []) or [])

def set_privacy(uid, hide):
    with _lock:
        P = _priv(); (P.add if hide else P.discard)(uid); store.put("bt_priv", sorted(P))
    return bool(hide)

def _period_since(period, now=None):
    import datetime
    try:
        from zoneinfo import ZoneInfo; tz = ZoneInfo("Europe/Warsaw")
    except Exception: tz = datetime.timezone.utc
    d = datetime.datetime.fromtimestamp(now or time.time(), tz)
    if period == "month": return int(d.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())
    if period == "week": return int((d - datetime.timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    return 0

def _agents_created(uid):
    # agentki AI tego konta zapisane w bazie (zgłoszone do bitew; bez odrzuconych i usuniętych przez moderację)
    return sum(1 for e in _entries() if e["uid"] == uid and e["status"] in ("pending", "approved", "withdrawn"))

def users_board(period="all", uid=None, accts=None, plan_of=None, limit=100):
    """Top użytkowników według wygranych bitew ich agentek. Tylko nicki (bez imion, nazwisk i e-maili),
    ukryci przełącznikiem prywatności nie są pokazywani publicznie. Kolejność: punkty, % wygranych, głosy, kto pierwszy."""
    since = _period_since(period); A = _stats(since); ALL = _stats(0); accts = accts or {}
    U = {}
    for aid, s in A.items():
        u = s.get("uid")
        if not u: continue
        x = U.setdefault(u, {"wins": 0, "played": 0, "votes": 0, "last": 0})
        x["wins"] += s["wins"]; x["played"] += s["played"]; x["votes"] += s["votes"]; x["last"] = max(x["last"], s["last"])
    tot = {}
    for aid, s in ALL.items():
        if s.get("uid"): tot[s["uid"]] = tot.get(s["uid"], 0) + s["pts"]
    P = _priv(); rows = []
    for u, x in U.items():
        if social.banned("u:" + u) or u not in accts: continue
        x["pts"] = x["wins"] * PTS_WIN; x["pct"] = round(x["wins"] * 100 / x["played"]) if x["played"] else 0
        a = accts[u]
        try: nick = social.nick_ok(a.get("name") or "")
        except ValueError: nick = ""
        rows.append(dict(x, uid=u, nick=nick or ("Widz " + u[:4]), plan=nicktier.of_uid(u) or "podstawowa", league=league(tot.get(u, 0)),
                         total_pts=tot.get(u, 0), agents=_agents_created(u), hidden=u in P))
    rows.sort(key=_rank_key)
    pub = []; me = None
    for r in rows:
        if r["hidden"] and r["uid"] != uid: continue
        r["pos"] = len(pub) + 1; pub.append(r)
        if r["uid"] == uid: me = r
    strip = lambda r: {k: v for k, v in r.items() if k not in ("uid", "last")} | {"me": r["uid"] == uid}
    out = {"period": period, "items": [strip(r) for r in pub if not r["hidden"]][:limit], "me": strip(me) if me else None, "hidden": bool(uid and uid in P)}
    if uid and not me:
        tp = tot.get(uid, 0)
        out["me"] = {"pos": None, "nick": None, "wins": 0, "played": 0, "pts": 0, "pct": 0, "league": league(tp), "total_pts": tp, "agents": _agents_created(uid), "me": True}
    return out

def ranking(uid=None, period="all", accts=None, plan_of=None):
    rows = _agent_rows()
    pub = lambda r: {k: r[k] for k in ("pos", "id", "name", "img", "official", "pts", "wins", "played", "pct", "votes", "league", "elite", "titles")}
    by = {k: [] for k, _ in LEAGUES}
    for r in rows: by[r["league"]].append(pub(r) | {"lpos": len(by[r["league"]]) + 1})
    mine = None
    me = my_entry(uid)
    if me:
        r = next((x for x in rows if x["id"] == me["id"]), None)
        if r: mine = pub(r) | {"next": next_league(r["pts"]), "from": dict(LEAGUES)[r["league"]], "lpos": next(i + 1 for i, x in enumerate(by[r["league"]]) if x["id"] == r["id"])}
    return {"leagues": [{"key": k, "from": lo} for k, lo in LEAGUES], "pts_win": PTS_WIN, "elite_n": ELITE_N,
            "agents": [pub(r) for r in rows], "by_league": by, "my_agent": mine, "has_results": bool(_results()),
            "users": users_board(period, uid, accts, plan_of)}

# ---------- opcjonalne powiadomienie o wyniku (domyślnie wyłączone; raz na bitwę na osobę) ----------
NOTE_LANGS = ("pl", "en", "es", "de", "uk")
TTL = {"pl": {"city": "Miss Nocnego Miasta", "studio": "Miss Sceny Studia", "promenade": "Miss Nadmorskiej Promenady", "winter": "Miss Zimowego Lasu", "gala": "Miss Sali Balowej", "garden": "Miss Ogrodu"},
       "en": {"city": "Miss Night City", "studio": "Miss Studio Stage", "promenade": "Miss Seaside Promenade", "winter": "Miss Winter Forest", "gala": "Miss Gala Hall", "garden": "Miss Garden"},
       "es": {"city": "Miss Ciudad Nocturna", "studio": "Miss Plató", "promenade": "Miss Paseo Marítimo", "winter": "Miss Bosque Nevado", "gala": "Miss Salón de Gala", "garden": "Miss Jardín"},
       "de": {"city": "Miss Nachtstadt", "studio": "Miss Studiobühne", "promenade": "Miss Strandpromenade", "winter": "Miss Winterwald", "gala": "Miss Gala-Saal", "garden": "Miss Garten"},
       "uk": {"city": "Міс Нічного Міста", "studio": "Міс Студійної Сцени", "promenade": "Міс Набережної", "winter": "Міс Зимового Лісу", "gala": "Міс Бальної Зали", "garden": "Міс Саду"}}
NTXT = {"pl": ("Bitwa zakończona", "{w} wygrywa", "Remis"), "en": ("Battle over", "{w} wins", "Draw"), "es": ("Batalla terminada", "{w} gana", "Empate"),
        "de": ("Battle beendet", "{w} gewinnt", "Unentschieden"), "uk": ("Битву завершено", "{w} перемагає", "Нічия")}

def _nsubs(): return store.get("bt_notify", {}) or {}

def set_notify(uid, on, lang="pl"):
    with _lock:
        N = _nsubs()
        if on: N[uid] = {"lang": lang if lang in NOTE_LANGS else "pl", "t": int(time.time())}
        else: N.pop(uid, None)
        store.put("bt_notify", N)
    return bool(on)

def notify_on(uid): return bool(uid and uid in _nsubs())

def _pct(va, vb):
    if not va + vb: return "50", "50"
    a = int(va * 1000 / (va + vb) + 0.5); return f"{a // 10},{a % 10}", f"{(1000 - a) // 10},{(1000 - a) % 10}"

def note_text(n, lang="pl"):
    t = NTXT.get(lang, NTXT["pl"]); pa, pb = n["pa"], n["pb"]
    if lang == "en": pa, pb = pa.replace(",", "."), pb.replace(",", ".")
    if n["win"]:
        w = n[n["win"]]
        return f"🏆 {t[0]}: {t[1].format(w=w)} {pa}% : {pb}% · {TTL.get(lang, TTL['pl']).get(n['scene'], '')}"
    return f"⚔️ {t[0]}: {t[2]} {pa}% : {pb}%"

def _notify_result(b, va, vb, win, end):
    N = _nsubs()
    if not N: return
    pa, pb = _pct(va, vb)
    n = {"bid": b["id"], "t": int(end), "a": b["a"]["name"], "b": b["b"]["name"], "va": va, "vb": vb, "pa": pa, "pb": pb, "win": win, "scene": b["scene"], "lg": b.get("lg"), "seen": False}
    with _lock:
        S = store.get("bt_notes", {}) or {}
        for uid in N:
            L = S.get(uid, [])
            if any(x["bid"] == b["id"] for x in L): continue   # raz na bitwę
            S[uid] = (L + [n])[-30:]
        store.put("bt_notes", S)
    def push():
        for uid, cfg in list(N.items()):
            lang = cfg.get("lang", "pl")
            try: notify.send_push("battle", "Luna · " + NTXT.get(lang, NTXT["pl"])[0], note_text(n, lang), url="/bitwy.html?sum=" + b["id"], tag="bt-" + b["id"], uid=uid)
            except Exception: pass
    threading.Thread(target=push, daemon=True).start()

def notes(uid):
    if not uid: return []
    return list(reversed((store.get("bt_notes", {}) or {}).get(uid, [])))

def notes_seen(uid, bids):
    with _lock:
        S = store.get("bt_notes", {}) or {}
        for x in S.get(uid, []):
            if not bids or x["bid"] in bids: x["seen"] = True
        store.put("bt_notes", S)

def summary(bid):
    """Podsumowanie zakończonej bitwy z historii (prawdziwy wynik)."""
    h = next((x for x in _state().get("hist", []) if x["id"] == bid), None)
    if not h: return None
    pa, pb = _pct(h["va"], h["vb"])
    return {k: h.get(k) for k in ("id", "a", "b", "scene", "lg", "start", "end", "va", "vb", "winner", "reason", "hours")} | {"pa": pa, "pb": pb}

# ---------- czat na żywo ----------
def _chat(): return store.get("bt_chat", {}) or {}

def chat_list(bid, uid=None, since=0):
    X = excluded(); me = "u:" + uid if uid else None
    L = _chat().get(bid, [])
    items = [{"id": m["id"], "nick": m["nick"], "tier": nicktier.of_author(m["ak"]), "partner": partners.is_partner(m["ak"][2:] if m["ak"].startswith("u:") else ""), "text": m["text"], "t": m["t"], "mine": m["ak"] == me}
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
        st = _state(); b = _find(st, bid)
        if not b: raise ValueError("Czat tej bitwy jest zamknięty.")
        C = _chat(); L = C.get(bid, []); mid = (L[-1]["id"] + 1) if L else 1
        m = {"id": mid, "ak": ak, "nick": nick, "text": text, "t": int(time.time()), "reports": [], "hidden": False}
        L.append(m); C[bid] = L[-300:]
        keep = {x["id"] for x in _all(st)} | {h["id"] for h in st.get("hist", [])[:6]}
        for k in [k for k in C if k not in keep]: C.pop(k, None)
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
            "league_battles": [{k: v for k, v in b.items() if k not in ("votes", "devs")} for b in (st.get("lg") or {}).values() if b],
            "hist": st.get("hist", [])[:10], "hours": duration_h(), "chat_flagged": chat[-100:], "eligible": [{"id": c["id"], "name": c["name"], "score": c["score"], "pts": c["pts"], "league": c["league"]} for c in _eligible()]}

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
