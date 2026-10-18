# -*- coding: utf-8 -*-
"""Ścianka Agentek Głosu, komentarze, głosy 👍/👎 i zgłoszenia – wspólna warstwa (store: Postgres lub JSON).
Wszystkie komentarze są moderowane przed publikacją; wpisy na Ściance od zaufanych autorów (3+ zatwierdzone) publikują się od razu.
Liczniki są wyłącznie prawdziwe – nic nie jest „zasiewane”."""
import base64, hashlib, re, secrets, threading, time, unicodedata
import store, imgsafe, avatars, official, antibot, stats, textutil, nicktier
PRICING = lambda: {}  # ustawiane przez serwer (cennik z CFG)

_lock = threading.Lock()
MAX_POST, MAX_CMT, MAX_NICK = 2000, 1000, 30
TRUST_AFTER = 3
LANGS = ("pl", "en", "es", "de", "uk")
BAD = {  # krótkie listy – filtr wstępny; ostatecznie decyduje moderator
 "pl": "kurwa kurwy kurwie chuj chuja huj pierdol pierdole pojeb jebac jebany jebana spierdalaj skurwysyn cipa pizda dziwka szmata ciota pedał",
 "en": "fuck fucking fucker shit bitch cunt dick asshole motherfucker slut whore nigger faggot retard",
 "es": "puta puto mierda coño cabron cabrón gilipollas pendejo maricon maricón zorra joder",
 "de": "scheisse scheiße fotze arschloch hurensohn wichser schlampe missgeburt fick ficken",
 "uk": "хуй хуя пизда блять бля сука єбати їбати йобаний мудак підор курва",
}
SPAM_RE = re.compile(r"(casino|kasyno|viagra|crypto ?giveaway|onlyfans|bit\.ly|t\.me/|telegram\.me|whatsapp\.com/|zarobisz|earn \$|\$\$\$)", re.I)

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.translate(str.maketrans("013457@$", "oieastas"))
_BADSET = {_norm(w) for l in BAD.values() for w in l.split()}

def check_text(t, maxlen):
    t = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(t or "")).strip()
    if not t: raise ValueError("Napisz coś. 🙂")
    if len(t) > maxlen: raise ValueError(f"Za długo – maksymalnie {maxlen} znaków.")
    words = set(re.findall(r"\w+", _norm(t))) | set(re.findall(r"\w+", _norm(textutil.strip_emoji(t))))  # emoji wstawione w środek słowa nie omijają filtra
    if words & _BADSET: raise ValueError("Ups, ten tekst zawiera słowa, których tu nie używamy. Spróbuj życzliwiej. 💚")
    if SPAM_RE.search(t) or len(re.findall(r"https?://", t)) > 2 or re.search(r"(.)\1{9,}", t): raise ValueError("To wygląda na spam – popraw tekst, proszę.")
    return t

def nick_ok(n):
    n = re.sub(r"[<>\x00-\x1f]", "", str(n or "")).strip()[:MAX_NICK]
    if len(n) < 2: raise ValueError("Podaj nick (min. 2 znaki).")
    if (set(re.findall(r"\w+", _norm(n))) | set(re.findall(r"\w+", _norm(textutil.strip_emoji(n))))) & _BADSET: raise ValueError("Wybierz inny nick.")
    if re.search(r"\b(luna|moderator|admin)\b", _norm(n)): raise ValueError("Ten nick jest zarezerwowany.")
    return n

def author_key(uid, vid):
    return ("u:" + uid) if uid else ("d:" + hashlib.sha256(("dev:" + str(vid)).encode()).hexdigest()[:20])

def _posts(): return store.get("wall_posts", []) or []
def _cmts(): return store.get("comments", []) or []
def _votes(): return store.get("votes", {}) or {}
def _bans(): return set(store.get("social_bans", []) or [])

def banned(ak): return ak in _bans()

# ---------- głosy ----------
TARGET_RE = re.compile(r"(post|cmt|item|home|agent):[\w\-]{1,40}")
def vote(target, voter, v):
    if not TARGET_RE.fullmatch(str(target)): raise ValueError("bad target")
    v = 1 if v == 1 else -1 if v == -1 else 0
    with _lock:
        V = _votes(); t = V.get(target, {})
        if v == 0 or t.get(voter) == v: t.pop(voter, None)   # ponowne kliknięcie usuwa głos
        else: t[voter] = v
        V[target] = t; store.put("votes", V)
    return counts(target, voter)

def counts(target, voter=None, V=None, X=None):
    """Publiczne liczniki: bez głosów kont ukrytych w cieniu (antibot) i kont bez potwierdzonego e-maila."""
    t = (V if V is not None else _votes()).get(target, {}); X = X if X is not None else antibot.excluded()
    return {"up": sum(1 for k, x in t.items() if x == 1 and k not in X), "down": sum(1 for k, x in t.items() if x == -1 and k not in X), "mine": t.get(voter, 0) if voter else 0}
def _cm_ok(c, X): return c["status"] == "approved" and c["author"] not in X

# ---------- Ścianka ----------
def _trusted(ak): return sum(1 for p in _posts() if p["author"] == ak and p.get("ever_approved")) >= TRUST_AFTER

def create_post(d, uid, vid, acct_nick=None):
    ak = author_key(uid, vid)
    if banned(ak): raise PermissionError("Twoje konto ma zablokowaną możliwość publikowania.")
    if not uid and d.get("adult") is not True: raise ValueError("Potwierdź, że masz ukończone 18 lat.")
    text = check_text(d.get("text"), MAX_POST)
    nick = acct_nick or nick_ok(d.get("nick"))
    img_id = None; img_kind = None
    if d.get("image") and d.get("img_kind") == "user":
        url = user_photo_wall(d.get("image"), d.get("user_decl"), uid)
        img_kind = "user"
    elif d.get("image"):
        url, _info = avatars_check_wall(d.get("image"), d.get("img_decl")); img_kind = "ai"
    if d.get("image"):
        img_id = secrets.token_hex(8)
        with _lock:
            I = store.get("wall_img", {}) or {}; I[img_id] = url
            store.put("wall_img", dict(list(I.items())[-400:]))
    agent = re.sub(r"[^\w\-]", "", str(d.get("agent", "")))[:40] or None
    auto = _trusted(ak) and img_kind != "user"  # zdjęcia użytkownika zawsze przechodzą przez moderację przed publikacją
    lang = d.get("lang") if d.get("lang") in LANGS else "pl"
    p = {"id": secrets.token_hex(6), "lang": lang, "variants": {}, "official": False, "author": ak, "uid": uid or "", "nick": nick, "text": text, "img": img_id, "img_kind": img_kind, "agent": agent,
         "t": int(time.time()), "edited": 0, "status": "approved" if auto else "pending", "ever_approved": auto, "reports": 0}
    with _lock:
        P = _posts(); P.append(p); store.put("wall_posts", P[-3000:])
    return p

def avatars_check_wall(data_url, declared):
    """Ten sam test „tylko AI” co dla awatarów (EXIF aparatu → odrzucenie, chyba że jest znacznik AI), większy rozmiar."""
    if declared is not True: raise ValueError("Zaznacz oświadczenie, że to obraz wygenerowany przez AI i nie przedstawia prawdziwej osoby.")
    m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 5 * 1024 * 1024: raise ValueError("Plik jest za duży (maks. 5 MB).")
    info = avatars.inspect(raw)
    if info["camera"] and not info["ai_markers"]:
        raise PermissionError("Ten plik wygląda na zdjęcie z aparatu lub telefonu. Na Ściance publikujemy tylko obrazy wygenerowane przez AI.")
    out, ext = imgsafe.reencode(raw, max_px=1920, max_in=5 * 1024 * 1024, quality=3)  # wydawane dalej według planu oglądającego
    return f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode(), info

USER_DECL = ("own", "no_nudity", "no_minors", "consent", "no_brands")
def user_photo_wall(data_url, decl, uid):
    """Własne zdjęcie użytkownika (nie AI) na wall: tylko z kontem, oświadczenia, maks. 854 px, bez EXIF/GPS, zawsze moderacja."""
    import quality
    if not uid: raise PermissionError("Własne zdjęcia mogą dodawać zalogowani użytkownicy (konto pozwala je zgłosić i usunąć).")
    if not isinstance(decl, dict) or not all(decl.get(k) is True for k in USER_DECL):
        raise ValueError("Zaznacz wszystkie oświadczenia: to Twoje zdjęcie, bez nagości, bez osób niepełnoletnich, inne osoby wyraziły zgodę, bez marek i logo.")
    m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 5 * 1024 * 1024: raise ValueError("Plik jest za duży (maks. 5 MB).")
    out, ext = imgsafe.reencode(raw, max_px=quality.USER_PHOTO_PX, max_in=5 * 1024 * 1024, quality=4)  # bez EXIF/GPS
    quality.user_photo_mark(raw); quality.user_photo_mark(out)  # nigdy jako twarz agentki
    return f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode()

def edit_post(pid, d, uid, vid):
    ak = author_key(uid, vid)
    with _lock:
        P = _posts(); p = next((x for x in P if x["id"] == pid and x["status"] != "deleted"), None)
        if not p or p["author"] != ak: raise PermissionError("To nie Twój wpis.")
        p["text"] = check_text(d.get("text"), MAX_POST); p["edited"] = int(time.time())
        if not _trusted(ak): p["status"] = "pending"
        store.put("wall_posts", P)
    return p

def delete_post(pid, uid, vid, mod=False):
    ak = author_key(uid, vid)
    with _lock:
        P = _posts(); p = next((x for x in P if x["id"] == pid), None)
        if not p or (not mod and p["author"] != ak): raise PermissionError("To nie Twój wpis.")
        P = [x for x in P if x["id"] != pid]; store.put("wall_posts", P)
        store.put("comments", [c for c in _cmts() if c["target"] != "post:" + pid])
        I = store.get("wall_img", {}) or {}
        if p.get("img") in I: I.pop(p["img"]); store.put("wall_img", I)

def wall_img(iid):
    P = {p.get("img"): p for p in _posts() if p.get("img")}
    p = P.get(iid)
    if not p or p["status"] != "approved": return None
    return (store.get("wall_img", {}) or {}).get(iid)

def _variants(p):
    v = {p.get("lang", "pl"): p["text"]}; v.update({k: t for k, t in (p.get("variants") or {}).items() if k in LANGS and t}); return v

def public_post(p, voter, V, C, mine_ak, lang="pl", T=None):
    c = counts("post:" + p["id"], voter, V)
    va = _variants(p); shown = lang if lang in va else p.get("lang", "pl")
    X = antibot.excluded()
    cm = [x for x in C if x["target"] == "post:" + p["id"] and _cm_ok(x, X)]
    return {"views": stats.post_views(p["id"], T), "id": p["id"], "nick": p["nick"], "tier": "" if p.get("official") else nicktier.of_author(p["author"]), "text": va[shown], "lang": shown, "orig": p.get("lang", "pl"), "variants": va if len(va) > 1 else None, "official": p.get("official", False), "img": ("/api/wall/img/" + p["img"]) if p.get("img") else None, "img_kind": p.get("img_kind") or ("ai" if p.get("img") else None), "agent": p.get("agent"),
            "t": p["t"], "edited": p.get("edited", 0), "votes": c, "ncomments": len(cm), "mine": p["author"] == mine_ak, "pending": p["status"] != "approved"}

def _off_hidden(): return set(store.get("official_hidden", []) or [])
def _pinned(): return list(store.get("wall_pinned", []) or [])

def official_admin():
    H = _off_hidden(); Pn = set(_pinned())
    return {"items": [{"id": o["id"], "title": o["v"]["pl"].get("h") or o["v"]["pl"].get("text", "")[:80], "hidden": o["id"] in H, "pinned": o["id"] in Pn} for o in official.raw()]}

def official_action(id_, action):
    if not official.get(id_): raise KeyError(id_)
    if action in ("hide", "show"): moderate("post", id_, "hide" if action == "hide" else "unhide")
    elif action in ("pin", "unpin"):
        with _lock:
            Pn = [x for x in _pinned() if x != id_]
            if action == "pin": Pn.insert(0, id_)
            store.put("wall_pinned", Pn[:3])
    else: raise ValueError("bad action")
    return official_admin()

def feed(sort, before, limit, uid, vid, lang="pl"):
    voter = author_key(uid, vid); V = _votes(); C = _cmts(); hid = _off_hidden()
    X = antibot.excluded(); T = stats.totals()
    P = [p for p in _posts() if (p["status"] == "approved" and p["author"] not in X) or (p["author"] == voter and p["status"] in ("approved", "pending"))]
    P += [dict(o, _off=True) for o in official.raw() if o["id"] not in hid]
    PIN = [i for i in _pinned()]; pin_posts = [p for pid in PIN for p in P if p["id"] == pid]
    P = [p for p in P if p["id"] not in PIN]
    def score(p): c = counts("post:" + p["id"], None, V, X); return c["up"] - c["down"]
    if sort == "hot":
        # Ranking wg prawdziwego zaangażowania (tylko sygnały po filtrze antybotowym) z zanikiem w czasie.
        now = time.time(); S30 = stats.series(30)
        cmc = {}
        for x in C:
            if x["status"] == "approved" and x["author"] not in X: cmc[x["target"]] = cmc.get(x["target"], 0) + 1
        def hot(p):
            k = "post:" + p["id"]; c = counts(k, None, V, X); sh = sum(d.get(k + ":share", 0) for d in S30.values())
            raw = 1 + c["up"] - 0.5 * c["down"] + 2 * cmc.get(k, 0) + 3 * sh
            h = max(raw, 0.1) / ((max(now - p["t"], 0) / 3600 + 2) ** 1.3)
            return h * (4 if p.get("_off") else 1)   # oficjalne wpisy zachowują priorytet
        P.sort(key=lambda p: (hot(p), p["t"]), reverse=True)
        start = int(before or 0); items = P[start:start + limit]; nxt = start + limit if len(P) > start + limit else None
    elif sort == "top":
        wk = time.time() - 7 * 86400
        P = [p for p in P if p["t"] >= wk or p.get("_off")]
        P.sort(key=lambda p: (score(p), p["t"]), reverse=True)
        start = int(before or 0); items = P[start:start + limit]; nxt = start + limit if len(P) > start + limit else None
    else:
        P.sort(key=lambda p: p["t"], reverse=True)
        if before: P = [p for p in P if p["t"] < int(before)]
        items = P[:limit]; nxt = items[-1]["t"] if len(P) > limit else None
    pr = PRICING()
    def pub(p):
        if p.get("_off"):
            cm = [x for x in C if x["target"] == "post:" + p["id"] and _cm_ok(x, X)]
            return official.public(p, lang, pr, {"votes": counts("post:" + p["id"], voter, V, X), "ncomments": len(cm), "views": stats.post_views(p["id"], T)})
        return public_post(p, voter, V, C, voter, lang, T)
    first = (sort in ("top", "hot") and not int(before or 0)) or (sort != "top" and not before)
    out = ([dict(pub(p), pinned=True) for p in pin_posts] if first else []) + [pub(p) for p in items]
    return {"items": out, "next": nxt}

def get_post(pid):
    if str(pid).startswith("off-"):
        o = official.get(pid)
        if not o or pid in _off_hidden(): return None
        return {"id": o["id"], "nick": official.data()["account"]["pl"], "text": o["v"]["pl"]["text"], "img": None, "img_url": o["img"], "official": True, "v": o["v"]}
    return next((p for p in _posts() if p["id"] == pid and p["status"] == "approved"), None)

# ---------- komentarze ----------
def add_comment(d, uid, vid, acct_nick=None):
    ak = author_key(uid, vid)
    if banned(ak): raise PermissionError("Twoje konto ma zablokowaną możliwość komentowania.")
    target = str(d.get("target", ""))
    if not TARGET_RE.fullmatch(target): raise ValueError("bad target")
    if target.startswith("post:") and not get_post(target[5:]): raise ValueError("Ten wpis nie istnieje.")
    text = check_text(d.get("text"), MAX_CMT); nick = acct_nick or nick_ok(d.get("nick"))
    parent = str(d.get("parent") or "")[:12] or None
    C = _cmts()
    if parent:
        par = next((c for c in C if c["id"] == parent and c["target"] == target), None)
        if not par: raise ValueError("Nie ma takiego komentarza.")
        if par.get("parent"): parent = par["parent"]  # tylko 1 poziom odpowiedzi
    rating = d.get("rating")
    rating = int(rating) if target.startswith("item:") and str(rating).isdigit() and 1 <= int(rating) <= 5 else None
    c = {"id": secrets.token_hex(6), "target": target, "parent": parent, "author": ak, "uid": uid or "", "nick": nick, "text": text,
         "rating": rating, "t": int(time.time()), "status": "pending", "reports": 0}
    with _lock:
        C = _cmts(); C.append(c); store.put("comments", C[-8000:])
    return c

def _partner(ak):
    try:
        import partners
        return partners.is_partner(ak[2:]) if str(ak).startswith("u:") else False
    except Exception: return False

def list_comments(target, uid, vid):
    voter = author_key(uid, vid); V = _votes(); X = antibot.excluded()
    out = [{"id": c["id"], "parent": c["parent"], "nick": c["nick"], "tier": nicktier.of_author(c["author"]), "partner": _partner(c["author"]), "text": c["text"], "rating": c.get("rating"), "t": c["t"],
            "votes": counts("cmt:" + c["id"], voter, V, X), "pending": c["status"] != "approved", "mine": c["author"] == voter}
           for c in _cmts() if c["target"] == target and (_cm_ok(c, X) or (c["author"] == voter and c["status"] in ("approved", "pending")))]
    rs = [c["rating"] for c in out if c.get("rating") and not c["pending"]]
    return {"items": sorted(out, key=lambda c: c["t"]), "rating": round(sum(rs) / len(rs), 1) if rs else None, "nratings": len(rs)}

# ---------- zgłoszenia i moderacja ----------
def report(target, reason, reporter):
    if not TARGET_RE.fullmatch(str(target)): raise ValueError("bad target")
    with _lock:
        R = store.get("social_reports", []) or []
        if any(r["target"] == target and r["by"] == reporter for r in R): return
        R.append({"target": target, "reason": re.sub(r"[<>]", "", str(reason or ""))[:200], "by": reporter, "t": int(time.time())})
        store.put("social_reports", R[-2000:])
        kind, _, id_ = target.partition(":")
        key = {"post": "wall_posts", "cmt": "comments"}.get(kind)
        if key:
            L = store.get(key, []) or []
            for x in L:
                if x["id"] == id_: x["reports"] = x.get("reports", 0) + 1
            store.put(key, L)

def admin_list():
    P = _posts(); C = _cmts(); V = _votes()
    pend_p = [p | {"img_url": ("/api/admin/wall/img/" + p["img"]) if p.get("img") else None} for p in P if p["status"] == "pending" or p.get("reports")]
    pend_c = [c for c in C if c["status"] == "pending" or c.get("reports")]
    return {"posts": sorted(pend_p, key=lambda p: -p["t"])[:200], "comments": sorted(pend_c, key=lambda c: -c["t"])[:300],
            "reports": list(reversed(store.get("social_reports", []) or []))[:200], "bans": sorted(_bans()),
            "stats": {"posts": sum(1 for p in P if p["status"] == "approved"), "comments": sum(1 for c in C if c["status"] == "approved"),
                      "pending": len([p for p in P if p["status"] == "pending"]) + len([c for c in C if c["status"] == "pending"])}}

def moderate(kind, id_, action, extra=None):
    if kind == "post" and str(id_).startswith("off-"):  # oficjalne wpisy z pliku w repo: tylko ukryj / przywróć
        if not official.get(id_): raise KeyError(id_)
        with _lock:
            H = _off_hidden()
            if action in ("hide", "delete", "reject"): H.add(id_)
            elif action in ("approve", "dismiss", "unhide"): H.discard(id_)
            else: raise ValueError("bad action")
            store.put("official_hidden", sorted(H))
            R = [r for r in (store.get("social_reports", []) or []) if r["target"] != f"post:{id_}" or action not in ("approve", "dismiss")]; store.put("social_reports", R)
        return {"id": id_, "hidden": id_ in H}
    key = {"post": "wall_posts", "cmt": "comments"}[kind]
    with _lock:
        L = store.get(key, []) or []; x = next((i for i in L if i["id"] == id_), None)
        if not x: raise KeyError(id_)
        if action == "approve": x["status"] = "approved"; x["ever_approved"] = True; x["reports"] = 0
        elif action == "reject": x["status"] = "rejected"
        elif action == "hide": x["status"] = "hidden"
        elif action == "delete": L = [i for i in L if i["id"] != id_]
        elif action == "ban":
            B = _bans(); B.add(x["author"]); store.put("social_bans", sorted(B)); x["status"] = "hidden"
        elif action == "dismiss": x["reports"] = 0
        elif action == "variants" and kind == "post":
            x["variants"] = {k: check_text(t, MAX_POST) for k, t in (extra or {}).items() if k in LANGS and str(t).strip()}
        else: raise ValueError("bad action")
        store.put(key, L)
        if action in ("delete", "dismiss", "approve"):
            R = [r for r in (store.get("social_reports", []) or []) if r["target"] != f"{kind}:{id_}"]; store.put("social_reports", R)
    return x

def unban(ak):
    B = _bans(); B.discard(ak); store.put("social_bans", sorted(B))

def admin_img(iid): return (store.get("wall_img", {}) or {}).get(iid)

# ---------- usuwanie / anonimizacja autora ----------
DELETED_NICK = "Usunięty użytkownik"
def anonymise_author(ak):
    """Usunięcie konta przez użytkownika: wpisy i komentarze zostają, ale bez nicku i powiązania z osobą; głosy zostają jako anonimowe."""
    anon = "x:" + secrets.token_hex(8)
    with _lock:
        C = _cmts(); ch = False
        for c in C:
            if c["author"] == ak: c.update(author=anon, uid="", nick=DELETED_NICK); ch = True
        if ch: store.put("comments", C)
        P = _posts(); ch = False
        for p in P:
            if p["author"] == ak: p.update(author=anon, uid="", nick=DELETED_NICK); p.pop("agent", None); ch = True
        if ch: store.put("wall_posts", P)
        V = _votes(); ch = False
        for t in V.values():
            if ak in t: t[anon] = t.pop(ak); ch = True
        if ch: store.put("votes", V)
def purge_author(ak, ban=False):
    """Usunięcie konta-bota przez właściciela: kasuje jego wpisy, komentarze i głosy."""
    with _lock:
        store.put("comments", [c for c in _cmts() if c["author"] != ak])
        store.put("wall_posts", [p for p in _posts() if p["author"] != ak])
        V = _votes()
        for t in V.values(): t.pop(ak, None)
        store.put("votes", V)
        if ban:
            b = _bans(); b.add(ak); store.put("social_bans", sorted(b))


LUNA_GAL = ["outfit_sweter", "outfit_biznes", "pose_prosto", "outfit_koktajlowa", "pose_zamyslona", "outfit_wieczorowa", "pose_siedzaca", "pose_polobrot", "outfit_zakiet"]
LUNA_T = 1792300000

def gallery(offset=0, limit=24):
    """Galeria agentek: zatwierdzone wpisy z obrazem (postacie AI) + oficjalne wpisy Luny z obrazem. Tylko prawdziwe dane.
    Agentka tygodnia: wpis z obrazem z ostatnich 7 dni z największą liczbą prawdziwych polubień (min. 1) – inaczej brak."""
    V = _votes(); X = antibot.excluded(); hid = _off_hidden()
    P = [p for p in _posts() if p["status"] == "approved" and p.get("img") and p["author"] not in X]
    out = [{"id": p["id"], "img": "/api/wall/img/" + p["img"], "nick": p["nick"], "agent": p.get("agent"), "t": p["t"], "official": False} for p in P]
    for x in out: x["likes"] = counts("post:" + x["id"], None, V, X)["up"]; x["target"] = "post:" + x["id"]
    # Luna – jedyna obecna agentka: jej prawdziwe, w pełni zakryte portrety z serwisu (bez głębokich dekoltów).
    for i, n in enumerate(LUNA_GAL):
        out.append({"id": "luna-" + n, "img": f"/catalog/luna/{n}.jpg", "nick": "Luna", "agent": "Luna", "t": LUNA_T - i, "official": True,
                    "target": "agent:luna-" + n, "likes": counts("agent:luna-" + n, None, V, X)["up"]})
    out.sort(key=lambda x: -x["t"])
    wk = time.time() - 7 * 86400
    cand = [x for x in out if x["t"] >= wk and x["likes"] >= 1]
    week = max(cand, key=lambda x: (x["likes"], x["t"])) if cand else None
    off = max(0, int(offset or 0)); lim = max(1, min(48, int(limit or 24)))
    return {"items": out[off:off + lim], "total": len(out), "next": off + lim if len(out) > off + lim else None, "week": week}
