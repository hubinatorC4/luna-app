"""Zgłoś 🚩 – jedno miejsce na zgłoszenia treści i osób (wpisy, komentarze, profile, czat bitwy, DM, zdjęcia),
kolejka moderatora i system „trzech poważnych naruszeń” (strike'i na koncie).

Zasady:
- zgłoszenie = (typ, id) + kategoria + opcjonalna notatka (≤500 znaków); zapisujemy kopię treści (snapshot), żeby
  decyzja była możliwa także po edycji/usunięciu; ten sam zgłaszający + ten sam cel = jedno zgłoszenie;
- limit 10 zgłoszeń / godz. na osobę (i 20 / godz. na IP); konto albo (gość) Turnstile, jeśli skonfigurowany;
- 3+ różnych zgłaszających → treść ukryta automatycznie do decyzji; kategoria „Osoba niepełnoletnia” → ukrycie od razu;
- decyzje: dismiss / remove / warn / temp_block / ban; „poważne” dokłada strike; 3. strike = trwała blokada;
- o decyzji informujemy w Skrzynce zgłaszającego i autora (uzasadnienie wg art. 17 DSA + link do odwołania);
  tożsamość zgłaszającego nigdy nie trafia do autora.
Integruje się z istniejącą moderacją: social (wall/komentarze/bany), battles (czat), inbox (DM, blokowanie), profiles, userprof."""
import hashlib, re, secrets, threading, time
import store
import reports_text as RT

_lock = threading.RLock()
TYPES = ("post", "cmt", "agent", "item", "btchat", "dm", "user", "photo")
CATS = tuple(RT.CATS)
DECISIONS = ("dismiss", "remove", "warn", "temp_block", "ban")
AUTO_HIDE_AT, MAX_STRIKES, NOTE_MAX = 3, 3, 500
PER_HOUR, PER_HOUR_IP = 10, 20
KEEP_DECIDED_S = 365 * 86400
APPEAL = "/problemy.html?odwolanie="
ID_RE = re.compile(r"[\w\-:]{1,80}")
_hits = {}

def _clean(s, n): return re.sub(r"[<>\x00-\x08\x0b-\x1f]", "", str(s or "")).strip()[:n]
def _cases(): return store.get("rp_cases", {}) or {}
def _save(C):
    if len(C) > 3000:
        C = dict(sorted(C.items(), key=lambda kv: -kv[1].get("u", 0))[:3000])
    store.put("rp_cases", C)
def _acct(uid): return store.get("rp_acct:" + uid, {}) or {}
def _acct_put(uid, a): store.put("rp_acct:" + uid, a)

def hour_ok(key, n):
    now = time.time()
    with _lock:
        L = [t for t in _hits.get(key, []) if now - t < 3600]
        if len(L) >= n: _hits[key] = L; return False
        L.append(now); _hits[key] = L
        if len(_hits) > 20000:
            for k in [k for k, v in _hits.items() if not v or now - v[-1] > 3600]: _hits.pop(k, None)
        return True

# ---------- cele zgłoszeń: odczyt kopii treści, autora, ukrywanie i przywracanie ----------
def _uid_of_ak(ak): return ak[2:] if str(ak or "").startswith("u:") else ""

def _find(key, id_):
    return next((x for x in (store.get(key, []) or []) if x.get("id") == id_), None)

def resolve(typ, tid):
    """→ dict(snap={nick,text,img}, author=ak|"", owner=uid|"") albo KeyError."""
    if typ in ("post", "cmt"):
        if typ == "post" and tid.startswith("off-"): raise PermissionError("official")
        x = _find("wall_posts" if typ == "post" else "comments", tid)
        if not x: raise KeyError(tid)
        img = ("/api/admin/wall/img/" + x["img"]) if typ == "post" and x.get("img") else ""
        return {"snap": {"nick": x.get("nick", ""), "text": str(x.get("text", ""))[:500], "img": img}, "author": x.get("author", ""), "owner": _uid_of_ak(x.get("author"))}
    if typ == "agent":
        if tid == "luna": raise PermissionError("official")
        if tid.startswith("p-"):
            import profiles
            r = profiles._P().get(tid[2:])
            if not r: raise KeyError(tid)
            ph = (r.get("photos") or [""])[0]
            return {"snap": {"nick": r.get("name", ""), "text": str(r.get("bio", ""))[:500], "img": profiles._photo_url(ph, tid[2:]) if ph else ""}, "author": "u:" + r["uid"], "owner": r["uid"]}
        if tid.startswith("bt-"):
            import battles
            e = next((e for e in battles._entries() if e["id"] == tid[3:]), None)
            if not e: raise KeyError(tid)
            return {"snap": {"nick": e.get("name", ""), "text": "", "img": "/api/admin/battles/img/" + e["id"]}, "author": "u:" + e.get("uid", "") if e.get("uid") else "", "owner": e.get("uid", "")}
        raise KeyError(tid)
    if typ == "item":
        return {"snap": {"nick": "", "text": "Butik: " + tid, "img": ""}, "author": "", "owner": ""}
    if typ == "btchat":
        bid, _, mid = tid.partition(":")
        import battles
        m = next((m for m in battles._chat().get(bid, []) if str(m["id"]) == mid), None)
        if not m: raise KeyError(tid)
        return {"snap": {"nick": m.get("nick", ""), "text": m.get("text", "")[:500], "img": ""}, "author": m.get("ak", ""), "owner": _uid_of_ak(m.get("ak"))}
    if typ == "dm":
        import inbox
        p, _, mid = tid.partition(":"); other = inbox.uid_of(p)
        if not other or not mid.isdigit(): raise KeyError(tid)
        return {"snap": {"nick": inbox.person(other)["nick"], "text": "", "img": ""}, "author": "u:" + other, "owner": other, "mid": int(mid)}
    if typ == "user":
        import inbox, userprof
        other = inbox.uid_of(tid)
        if not other: raise KeyError(tid)
        g = userprof.get(other)
        return {"snap": {"nick": inbox.person(other)["nick"], "text": str(g.get("bio", ""))[:500], "img": ""}, "author": "u:" + other, "owner": other}
    if typ == "photo":
        kind, _, rest = tid.partition(":")
        if kind in ("post", "agent", "user"):
            r = resolve(kind, rest); r["snap"]["text"] = ""
            if kind == "user": r["snap"]["img"] = "/api/admin/user/avatar/" + r["owner"][:8]
            return r
        raise KeyError(tid)
    raise KeyError(typ)

def _set_status(key, id_, st, case):
    import social
    with social._lock:
        L = store.get(key, []) or []
        for x in L:
            if x.get("id") == id_:
                if st == "restore": x["status"] = case.get("prev") or "approved"
                else:
                    if x.get("status") != "hidden": case["prev"] = x.get("status")
                    x["status"] = st
        store.put(key, L)

def _apply(case, how):
    """how: hide (tymczasowo, do decyzji) | restore | remove (na stałe)."""
    typ, tid = case["type"], case["tid"]
    try:
        if typ == "photo":
            kind, _, rest = tid.partition(":")
            if kind == "user":
                import userprof
                with userprof._lock:
                    A = userprof._A(); a = A.get(case["owner"])
                    if a:
                        if how == "remove": A.pop(case["owner"], None)
                        else: a["status"] = "approved" if how == "restore" else "hidden"
                        store.put("user_avatars", A)
                return
            typ, tid = kind, rest
        if typ in ("post", "cmt"):
            k = "wall_posts" if typ == "post" else "comments"
            _set_status(k, tid, "restore" if how == "restore" else "hidden", case)
        elif typ == "agent" and tid.startswith("p-"):
            import profiles
            profiles.admin(tid[2:], "show" if how == "restore" else "hide")
        elif typ == "btchat":
            import battles
            bid, _, mid = tid.partition(":")
            with battles._lock:
                C = battles._chat()
                for m in C.get(bid, []):
                    if str(m["id"]) == mid:
                        m["hidden"] = how != "restore"
                        if how == "restore": m["reports"] = []
                        if how == "remove": m["text"] = ""
                store.put("bt_chat", C)
        elif typ == "dm":
            import inbox
            p, _, mid = tid.partition(":")
            k = inbox._pair(case["owner"], case.get("rep_uid") or "")
            with inbox._lock:
                d = inbox._dm(k)
                for m in d.get("m", []):
                    if m["id"] == int(mid) and m["f"] == case["owner"]:
                        if how == "restore": m.pop("rm", None); m["x"] = m.get("x") or case["snap"].get("text", "")
                        else: m["rm"] = 1; m["x"] = ""
                store.put("dm:" + k, d)
        elif typ == "user":
            import userprof
            with userprof._lock:
                P = userprof._P(); r = P.get(case["owner"]) or {}
                if how == "restore": r["public"] = case.get("prev_public", r.get("public"))
                else:
                    case.setdefault("prev_public", r.get("public")); r["public"] = False
                    if how == "remove": r["bio"] = ""
                P[case["owner"]] = r; store.put("user_profiles", P)
    except Exception as e:
        case.setdefault("log", []).append({"t": int(time.time()), "x": "apply %s failed: %s" % (how, type(e).__name__)})

def _legacy(typ, tid, cat, rep_uid, rep_key, note):
    """Zgłoszenie trafia też do starych modułów, żeby dotychczasowe widoki moderacji działały jak dawniej."""
    try:
        if typ in ("post", "cmt", "agent", "item"):
            import social; social.report(typ + ":" + tid, RT.CATS[cat]["pl"] + (" – " + note if note else ""), rep_key)
        elif typ == "btchat":
            import battles; bid, _, mid = tid.partition(":"); battles.chat_report(rep_uid, rep_key, bid, int(mid))
        elif typ == "dm" and rep_uid:
            import inbox; p, _, mid = tid.partition(":"); inbox.dm_report(rep_uid, p, int(mid), RT.CATS[cat]["pl"])
        elif typ == "user" and rep_uid:
            import inbox; inbox._report(rep_uid, inbox.uid_of(tid), None, RT.CATS[cat]["pl"])
    except Exception: pass

# ---------- zgłoszenie ----------
def submit(typ, tid, cat, note, rep_uid, rep_key, block=False):
    typ = str(typ or ""); tid = str(tid or "")[:80]; cat = str(cat or "")
    if typ not in TYPES or not ID_RE.fullmatch(tid): raise ValueError("bad target")
    if cat not in CATS: raise ValueError("Wybierz powód zgłoszenia.")
    if typ in ("dm", "user") and not rep_uid: raise PermissionError("login")
    note = _clean(note, NOTE_MAX)
    r = resolve(typ, tid)
    if r["owner"] and r["owner"] == rep_uid: raise ValueError("Nie możesz zgłosić własnej treści 🙂")
    if typ == "dm":   # DM zgłasza tylko jego odbiorca – sprawdzane w inbox.dm_report (wiadomość od tej osoby do Ciebie)
        import inbox
        k = inbox._pair(rep_uid, r["owner"]); d = inbox._dm(k)
        m = next((m for m in d.get("m", []) if m["id"] == r["mid"] and m["f"] == r["owner"]), None)
        if not m: raise KeyError(tid)
        r["snap"]["text"] = str(m.get("x", ""))[:500] or ("📷 zdjęcie w czacie (podgląd w panelu: Skrzynka → zgłoszenia)" if m.get("img") else "")
    key = typ + ":" + tid; now = int(time.time()); hid = False; dup = False
    with _lock:
        C = _cases(); c = C.get(key)
        if not c:
            c = {"id": secrets.token_hex(4), "type": typ, "tid": tid, "snap": r["snap"], "author": r["author"], "owner": r["owner"],
                 "reports": [], "status": "open", "auto": False, "t": now, "u": now}
            if typ == "dm": c["rep_uid"] = rep_uid
        if c["status"] == "decided": c["status"] = "open"; c.pop("dec", None)  # nowe zgłoszenie po decyzji = ponowna kolejka
        if any(x["by"] == rep_key for x in c["reports"]): dup = True
        else:
            c["reports"].append({"by": rep_key, "uid": rep_uid, "cat": cat, "note": note, "t": now})
            c["reports"] = c["reports"][-50:]
        c["u"] = now
        uniq = len({x["by"] for x in c["reports"]})
        if c["status"] == "open" and (uniq >= AUTO_HIDE_AT or cat == "minor"):
            c["status"] = "hidden"; c["auto"] = True; c["hidden_at"] = now; c["hidden_why"] = "minor" if cat == "minor" else "reports"
            _apply(c, "hide"); hid = True
        C[key] = c; _save(C)
    if not dup: _legacy(typ, tid, cat, rep_uid, rep_key, note)
    if hid and c["owner"]: _notify_hidden(c)
    blocked = False
    if block and rep_uid and r["owner"] and r["owner"] != rep_uid:
        try:
            import inbox; inbox._unlink(rep_uid, r["owner"], True); blocked = True
        except Exception: pass
    return {"case": c["id"], "dup": dup, "hidden": c["status"] == "hidden", "blocked": blocked}

# ---------- Skrzynka ----------
def _lang_of(uid):
    try:
        import userprof; l = userprof.lang_of(uid)
        return l if l in RT.L5 else "pl"
    except Exception: return "pl"

def _deliver(uid, ti, bo, link, dedupe):
    """Wiadomość systemowa w 5 językach (tłumaczona przy odczycie skrzynki)."""
    try: import inbox
    except Exception: return None
    m = inbox.deliver(uid, "important", title="🛡️", body=".", link=link, dedupe=dedupe)
    if not m: return None
    with inbox._lock:
        d = inbox._ib(uid)
        for x in d.get("m", []):
            if x["id"] == m["id"]: x["ti"] = ti; x["bo"] = bo
        store.put("ib:" + uid, d)
    return m

def _snip(c, l):
    t = (c["snap"].get("text") or "").replace("\n", " ")
    return (" („" + t[:60] + ("…" if len(t) > 60 else "") + "”)") if t else ""

def _what(c): return RT.WHAT.get(c["type"], RT.WHAT["post"])

def _notify_hidden(c):
    ti = dict(RT.T_HID); bo = {l: RT.B_HID[l].format(what=_what(c)[l], snip=_snip(c, l)) for l in RT.L5}
    _deliver(c["owner"], ti, bo, APPEAL + c["id"], "rph:" + c["id"])

def _fmt_date(ts): return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts))

def _notify_decision(c, dec):
    """Uzasadnienie (art. 17 DSA) dla autora i krótka informacja dla zgłaszających (bez danych drugiej strony)."""
    action = dec["action"]; cat = dec["cat"]
    if c["owner"] and action != "dismiss":
        st = None
        if dec.get("egregious") or dec.get("strike_n"):
            st = {l: (RT.EGREG[l] if dec.get("egregious") else "") + (RT.STRIKE[l].format(n=dec["strike_n"]) if dec.get("strike_n") else "")
                     + (RT.STRIKE3[l] if dec.get("strike_n", 0) >= MAX_STRIKES and not dec.get("egregious") else "") for l in RT.L5}
        dlab = RT.DEC["ban" if dec.get("final") == "ban" else action]
        ti = {l: RT.T_DEC[l].format(dec=dlab[l]) for l in RT.L5}
        bo = {l: RT.B_DEC[l].format(what=_what(c)[l], snip=_snip(c, l), cat=RT.CATS[cat][l], dec=dlab[l],
                                    until=RT.UNTIL[l].format(d=_fmt_date(dec["until"])) if dec.get("until") and dec.get("final") != "ban" else "",
                                    strike=(st[l] + "\n") if st else "", auto=RT.AUTO[l] if c.get("auto") else "",
                                    note=RT.NOTE[l].format(x=dec["note"]) if dec.get("note") else "", case=c["id"]) for l in RT.L5}
        _deliver(c["owner"], ti, bo, APPEAL + c["id"], "rpd:" + c["id"] + ":" + str(dec["t"]))
    res = RT.RES["dismiss" if action == "dismiss" else "action"]
    for uid in {x["uid"] for x in c["reports"] if x.get("uid") and x["t"] <= dec["t"]}:
        bo = {l: RT.B_REP[l].format(what=_what(c)[l], cat=RT.CATS[cat][l], res=res[l], case=c["id"]) for l in RT.L5}
        _deliver(uid, dict(RT.T_REP), bo, APPEAL + c["id"], "rpr:" + c["id"] + ":" + str(dec["t"]))

# ---------- konto: strike'i i blokady ----------
def standing(uid):
    a = _acct(uid); now = time.time()
    bu = int(a.get("block_until", 0) or 0)
    return {"strikes": len(a.get("strikes", [])), "max": MAX_STRIKES, "banned": bool(a.get("banned")),
            "block_until": bu if bu > now else 0, "warns": int(a.get("warns", 0)),
            "history": [{"t": h["t"], "action": h["action"], "cat": h["cat"], "serious": bool(h.get("serious")), "case": h.get("case", "")}
                        for h in a.get("history", [])][-20:][::-1]}

def write_block(uid):
    """None albo komunikat (PL), gdy konto ma aktywną blokadę – zapis (wpisy, czat, DM, bitwy) jest wtedy wstrzymany."""
    if not uid: return None
    a = _acct(uid)
    if a.get("banned"): return RT.BANNED["pl"]
    bu = int(a.get("block_until", 0) or 0)
    if bu > time.time(): return RT.BLOCKED["pl"].format(d=_fmt_date(bu))
    return None

ALLOW_BLOCKED = ("/api/account/", "/api/inbox", "/api/tickets", "/api/help", "/api/age/", "/api/me/lang", "/api/forms/delete", "/api/me/delete", "/api/me/export", "/api/push")

def _sanction(uid, ak, action, cat, serious, days, case_id):
    """Zwraca dict z wynikiem: strike_n, final (np. ban po 3. strike'u), until."""
    out = {}
    if not uid:
        if action == "ban" and ak:   # treści gościa (urządzenie): ban urządzenia w Ściance
            import social
            with social._lock: B = social._bans(); B.add(ak); store.put("social_bans", sorted(B))
            out["final"] = "ban"
        return out
    now = int(time.time())
    with _lock:
        a = _acct(uid); S = a.setdefault("strikes", [])
        if action == "warn": a["warns"] = int(a.get("warns", 0)) + 1
        if serious and action in ("remove", "warn", "temp_block", "ban"):
            S.append({"t": now, "cat": cat, "case": case_id}); out["strike_n"] = min(len(S), MAX_STRIKES)
        if action == "temp_block":
            a["block_until"] = max(int(a.get("block_until", 0) or 0), now + max(1, min(int(days or 7), 90)) * 86400); out["until"] = a["block_until"]
        if action == "ban" or len(S) >= MAX_STRIKES:
            a["banned"] = now; out["final"] = "ban"
            if action == "ban" and len(S) < MAX_STRIKES: out["egregious"] = True
        a.setdefault("history", []).append({"t": now, "action": out.get("final") or action, "cat": cat, "serious": bool(serious), "case": case_id})
        a["history"] = a["history"][-100:]
        _acct_put(uid, a)
    if out.get("final") == "ban":
        try:
            import social
            with social._lock: B = social._bans(); B.add("u:" + uid); store.put("social_bans", sorted(B))
        except Exception: pass
    return out

def lift(uid):
    """Zdjęcie blokady (np. po uwzględnionym odwołaniu). Strike'i zostają, chyba że admin cofnie je osobno."""
    with _lock:
        a = _acct(uid); a["banned"] = 0; a["block_until"] = 0
        a.setdefault("history", []).append({"t": int(time.time()), "action": "lift", "cat": "other", "serious": False}); _acct_put(uid, a)
    try:
        import social
        with social._lock: B = social._bans(); B.discard("u:" + uid); store.put("social_bans", sorted(B))
    except Exception: pass
    return standing(uid)

def unstrike(uid):
    with _lock:
        a = _acct(uid)
        if a.get("strikes"): a["strikes"].pop()
        a.setdefault("history", []).append({"t": int(time.time()), "action": "unstrike", "cat": "other", "serious": False}); _acct_put(uid, a)
    return standing(uid)

# ---------- decyzje moderatora ----------
def decide(case_id, action, cat=None, serious=None, days=7, note=""):
    if action not in DECISIONS: raise ValueError("bad action")
    with _lock:
        C = _cases(); key = next((k for k, v in C.items() if v["id"] == case_id), None)
        if not key: raise KeyError(case_id)
        c = C[key]
        cats = [x["cat"] for x in c["reports"]]
        cat = cat if cat in CATS else (max(set(cats), key=cats.count) if cats else "other")
        if serious is None: serious = action in ("temp_block", "ban")
        if action == "dismiss": _apply(c, "restore") if c["status"] == "hidden" or c.get("auto") else None
        elif c["type"] != "item": _apply(c, "remove")
        now = int(time.time())
        res = _sanction(c["owner"], c["author"], action, cat, bool(serious) and action != "dismiss", days, c["id"]) if action != "dismiss" else {}
        dec = {"action": action, "cat": cat, "serious": bool(serious) and action != "dismiss", "t": now, "note": _clean(note, 300), **res}
        c["dec"] = dec; c["status"] = "decided"; c["u"] = now
        c.setdefault("log", []).append({"t": now, "x": action}); C[key] = c; _save(C)
    _notify_decision(c, dec)
    return admin_view(c)

# ---------- widoki ----------
def admin_view(c):
    cats = {}
    for x in c["reports"]: cats[x["cat"]] = cats.get(x["cat"], 0) + 1
    st = standing(c["owner"]) if c["owner"] else None
    return {"id": c["id"], "type": c["type"], "tid": c["tid"], "snap": c["snap"], "status": c["status"], "auto": c.get("auto", False),
            "hidden_why": c.get("hidden_why", ""), "n": len({x["by"] for x in c["reports"]}), "guests": sum(1 for x in c["reports"] if not x.get("uid")),
            "cats": cats, "notes": [x["note"] for x in c["reports"] if x.get("note")][-10:], "t": c["t"], "u": c["u"], "dec": c.get("dec"),
            "author_kind": "account" if c["owner"] else ("guest" if c["author"] else "none"), "owner_short": c["owner"][:8] if c["owner"] else "",
            "standing": st and {k: st[k] for k in ("strikes", "max", "banned", "block_until", "warns")}}

def purge():
    now = time.time()
    with _lock:
        C = _cases(); n = len(C)
        C = {k: v for k, v in C.items() if not (v["status"] == "decided" and now - v["u"] > KEEP_DECIDED_S)}
        if len(C) != n: _save(C)

def admin_list(status="open", typ="", cat=""):
    purge()
    out = []
    for c in sorted(_cases().values(), key=lambda c: (c["status"] == "decided", -(c["status"] == "hidden"), -c["u"])):
        if status == "open" and c["status"] == "decided": continue
        if status in ("hidden", "decided") and c["status"] != status: continue
        if typ and c["type"] != typ: continue
        if cat and not any(x["cat"] == cat for x in c["reports"]): continue
        out.append(admin_view(c))
        if len(out) >= 200: break
    C = _cases().values()
    return {"items": out, "counts": {"open": sum(1 for c in C if c["status"] == "open"), "hidden": sum(1 for c in C if c["status"] == "hidden"),
                                     "decided": sum(1 for c in C if c["status"] == "decided")},
            "cats": {k: v["pl"] for k, v in RT.CATS.items()}, "types": {k: v["pl"] for k, v in RT.WHAT.items()}, "decisions": {k: v["pl"] for k, v in RT.DEC.items()},
            "rules": {"auto_hide_at": AUTO_HIDE_AT, "max_strikes": MAX_STRIKES}}

def open_count():
    return sum(1 for c in _cases().values() if c["status"] != "decided")

def _eh(email): return hashlib.sha256(("luna-ban:" + str(email or "").strip().lower()).encode()).hexdigest()

def email_banned(email):
    return bool(email) and _eh(email) in set(store.get("rp_banned_emails", []) or [])

def delete_user(uid, email=""):
    """RODO – usunięcie konta: znikają strike'i i nasze ślady jako zgłaszającego (kopie treści w sprawach zostają anonimowe).
    Przy trwałej blokadzie zostaje wyłącznie skrót e-maila (bez samego adresu), żeby zablokowana osoba nie założyła od razu nowego konta."""
    with _lock:
        if _acct(uid).get("banned") and email:
            B = store.get("rp_banned_emails", []) or []
            if _eh(email) not in B: B.append(_eh(email)); store.put("rp_banned_emails", B[-5000:])
        store.put("rp_acct:" + uid, {})
        C = _cases()
        for c in C.values():
            for x in c["reports"]:
                if x.get("uid") == uid: x["uid"] = ""; x["by"] = "x:" + hashlib.sha256(x["by"].encode()).hexdigest()[:12]
        _save(C)
