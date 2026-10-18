# -*- coding: utf-8 -*-
"""Ścianka Luny, komentarze, głosy 👍/👎 i zgłoszenia – wspólna warstwa (store: Postgres lub JSON).
Wszystkie komentarze są moderowane przed publikacją; wpisy na Ściance od zaufanych autorów (3+ zatwierdzone) publikują się od razu.
Liczniki są wyłącznie prawdziwe – nic nie jest „zasiewane”."""
import base64, hashlib, re, secrets, threading, time, unicodedata
import store, imgsafe, avatars

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
    words = set(re.findall(r"\w+", _norm(t)))
    if words & _BADSET: raise ValueError("Ups, ten tekst zawiera słowa, których tu nie używamy. Spróbuj życzliwiej. 💚")
    if SPAM_RE.search(t) or len(re.findall(r"https?://", t)) > 2 or re.search(r"(.)\1{9,}", t): raise ValueError("To wygląda na spam – popraw tekst, proszę.")
    return t

def nick_ok(n):
    n = re.sub(r"[<>\x00-\x1f]", "", str(n or "")).strip()[:MAX_NICK]
    if len(n) < 2: raise ValueError("Podaj nick (min. 2 znaki).")
    if set(re.findall(r"\w+", _norm(n))) & _BADSET: raise ValueError("Wybierz inny nick.")
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

def counts(target, voter=None, V=None):
    t = (V if V is not None else _votes()).get(target, {})
    return {"up": sum(1 for x in t.values() if x == 1), "down": sum(1 for x in t.values() if x == -1), "mine": t.get(voter, 0) if voter else 0}

# ---------- Ścianka ----------
def _trusted(ak): return sum(1 for p in _posts() if p["author"] == ak and p.get("ever_approved")) >= TRUST_AFTER

def create_post(d, uid, vid, acct_nick=None):
    ak = author_key(uid, vid)
    if banned(ak): raise PermissionError("Twoje konto ma zablokowaną możliwość publikowania.")
    if not uid and d.get("adult") is not True: raise ValueError("Potwierdź, że masz ukończone 18 lat.")
    text = check_text(d.get("text"), MAX_POST)
    nick = acct_nick or nick_ok(d.get("nick"))
    img_id = None
    if d.get("image"):
        url, _info = avatars_check_wall(d.get("image"), d.get("img_decl"))
        img_id = secrets.token_hex(8)
        with _lock:
            I = store.get("wall_img", {}) or {}; I[img_id] = url
            store.put("wall_img", dict(list(I.items())[-400:]))
    agent = re.sub(r"[^\w\-]", "", str(d.get("agent", "")))[:40] or None
    auto = _trusted(ak)
    lang = d.get("lang") if d.get("lang") in LANGS else "pl"
    p = {"id": secrets.token_hex(6), "lang": lang, "variants": {}, "official": False, "author": ak, "uid": uid or "", "nick": nick, "text": text, "img": img_id, "agent": agent,
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
    out, ext = imgsafe.reencode(raw, max_px=1024, max_in=5 * 1024 * 1024, quality=5)
    return f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode(), info

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

def public_post(p, voter, V, C, mine_ak, lang="pl"):
    c = counts("post:" + p["id"], voter, V)
    va = _variants(p); shown = lang if lang in va else p.get("lang", "pl")
    cm = [x for x in C if x["target"] == "post:" + p["id"] and x["status"] == "approved"]
    return {"id": p["id"], "nick": p["nick"], "text": va[shown], "lang": shown, "orig": p.get("lang", "pl"), "variants": va if len(va) > 1 else None, "official": p.get("official", False), "img": ("/api/wall/img/" + p["img"]) if p.get("img") else None, "agent": p.get("agent"),
            "t": p["t"], "edited": p.get("edited", 0), "votes": c, "ncomments": len(cm), "mine": p["author"] == mine_ak, "pending": p["status"] != "approved"}

def feed(sort, before, limit, uid, vid, lang="pl"):
    voter = author_key(uid, vid); V = _votes(); C = _cmts()
    P = [p for p in _posts() if p["status"] == "approved" or (p["author"] == voter and p["status"] == "pending")]
    if sort == "top":
        wk = time.time() - 7 * 86400
        P = [p for p in P if p["t"] >= wk]
        P.sort(key=lambda p: (counts("post:" + p["id"], None, V)["up"] - counts("post:" + p["id"], None, V)["down"], p["t"]), reverse=True)
        start = int(before or 0); items = P[start:start + limit]; nxt = start + limit if len(P) > start + limit else None
    else:
        P.sort(key=lambda p: p["t"], reverse=True)
        if before: P = [p for p in P if p["t"] < int(before)]
        items = P[:limit]; nxt = items[-1]["t"] if len(P) > limit else None
    return {"items": [public_post(p, voter, V, C, voter, lang) for p in items], "next": nxt}

def get_post(pid):
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

def list_comments(target, uid, vid):
    voter = author_key(uid, vid); V = _votes()
    out = [{"id": c["id"], "parent": c["parent"], "nick": c["nick"], "text": c["text"], "rating": c.get("rating"), "t": c["t"],
            "votes": counts("cmt:" + c["id"], voter, V), "pending": c["status"] != "approved"}
           for c in _cmts() if c["target"] == target and (c["status"] == "approved" or (c["author"] == voter and c["status"] == "pending"))]
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
