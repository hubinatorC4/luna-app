# -*- coding: utf-8 -*-
"""Profil UŻYTKOWNIKA – w pełni anonimowy: tylko nick (wymagany, unikalny, moderowany). Brak pól imię/nazwisko;
e-mail służy wyłącznie do logowania i nigdy nie jest pokazywany. Pozostałe pola opcjonalne, domyślnie prywatne."""
import base64, hashlib, re, threading, time
import store, social, imgsafe, quality

_lock = threading.Lock()
BIO_LEN, INT_MAX, INT_LEN, LINKS_MAX = 200, 6, 24, 3
PRESETS = ("ksiezyc", "gwiazda", "fala", "nuta", "serce", "chmurka")   # domyślne awatary w stylu Luny (SVG)
LINK_RE = re.compile(r"https://[\w.-]+\.[a-z]{2,}(/[\w\-./?=&%#~+]*)?", re.I)
STEPS = ("nick", "avatar", "bio", "interests", "wall", "agent")  # kroki paska ukończenia profilu

def _P(): return store.get("user_profiles", {}) or {}
def _A(): return store.get("user_avatars", {}) or {}
def _key(n): return re.sub(r"\s+", "", social._norm(n))

def get(uid):
    r = _P().get(uid) or {}
    return {"nick": r.get("nick", "") or nick_of(uid), "bio": r.get("bio", ""), "interests": r.get("interests", []), "links": r.get("links", []),
            "avatar": r.get("avatar", ""), "public": bool(r.get("public")), "hide_rank": hidden_in_rank(uid),
            "show_bio": bool(r.get("show_bio", True)), "show_interests": bool(r.get("show_interests", True)), "show_links": bool(r.get("show_links", False)),
            "tour_done": bool(r.get("tour_done")),
            # O mnie (opcjonalne, domyślnie ukryte; NIGDY nie trafia do reklam – tylko do nagłówka profilu, eksportu i usuwania konta)
            "age": r.get("age") if isinstance(r.get("age"), int) else None, "gender": r.get("gender", ""), "gender_x": r.get("gender_x", ""),
            "pron": r.get("pron", ""), "pron_x": r.get("pron_x", ""),
            "show_age": bool(r.get("show_age")), "show_gender": bool(r.get("show_gender")), "show_pron": bool(r.get("show_pron"))}

GENDERS = ("f", "m", "nb", "trans", "other", "na")   # Kobieta / Mężczyzna / Osoba niebinarna / Osoba transpłciowa / Inna / Wolę nie podawać
PRONS = ("she", "he", "they", "custom")
X_LEN = 30
_X_BAD = re.compile(r"(sex|seks|porn|erot|nsfw|fetysz|fetish|nag[aio]\b|nude|nackt|desnud|https?:|www\.|@)", re.I)
def _x(v):
    v = re.sub(r"[<>\x00-\x1f\x7f]", "", str(v or "")).strip()
    if not v: return ""
    if len(v) > X_LEN: raise ValueError(f"Maksymalnie {X_LEN} znaków.")
    if _X_BAD.search(v): raise ValueError("Ups, tego tu nie wpiszemy – spróbuj inaczej. 💚")
    return social.check_text(v, X_LEN)

def ident(uid, r=None):
    """Tylko pola, które właściciel sam pokazał. Brak daty urodzenia – sam wiek (18–99)."""
    g = r or get(uid); out = {}
    if g["show_age"] and g["age"]: out["age"] = g["age"]
    if g["show_gender"] and g["gender"] and g["gender"] != "na":
        out["g"] = g["gender"]
        if g["gender"] == "other" and g["gender_x"]: out["gx"] = g["gender_x"]
    if g["show_pron"] and g["pron"]:
        if g["pron"] != "custom": out["pn"] = g["pron"]
        elif g["pron_x"]: out["pn"] = "custom"; out["pnx"] = g["pron_x"]
    return out

def seed_moderator():
    """Jednorazowo (v1.6.9, prośba właściciela): konto moderatora Hubinator❤️ – płeć Mężczyzna, widoczna; wiek pusty."""
    if store.get("ident_seed_hub"): return
    k = _key("Hubinator❤️"); uid = None
    for u, r in _P().items():
        if k and _key(r.get("nick", "")) == k: uid = u
    if not uid:
        try:
            import accounts; uid = next((x.get("uid") or u for u, x in accounts._accts().items() if _key(x.get("name") or "") == k), None)
        except Exception: uid = None
    if not uid: return
    with _lock:
        P = _P(); r = P.get(uid) or {}
        if not r.get("gender"): r.update(gender="m", show_gender=True)
        r.pop("age", None); r["show_age"] = False; P[uid] = r; store.put("user_profiles", P)
    store.put("ident_seed_hub", int(time.time()))

def nick_of(uid):
    n = (_P().get(uid) or {}).get("nick", "")
    if n: return n
    try:
        import accounts; return ((accounts._accts().get(uid) or {}).get("name") or "").strip()  # ten sam nick co w Skrzynce/Znajomych
    except Exception: return ""
def hidden_in_rank(uid):
    import battles; return uid in battles._priv()  # jedno źródło prawdy z rankingiem Bitew (bt_priv)

def set_nick(uid, n):
    import moderator
    if moderator.is_admin_uid(uid) and moderator.login_key(n) == moderator.login_key(moderator.admin_nick()): n = moderator.admin_nick()   # zarezerwowany nick właściciela
    else: n = social.nick_ok(n)
    if len(n) > 24: n = n[:24]
    k = _key(n)
    with _lock:
        P = _P()
        if any(_key(v.get("nick", "")) == k for u, v in P.items() if u != uid): raise ValueError("Ten nick jest już zajęty – wybierz inny.")
        import accounts
        if any(x.get("uid") != uid and _key(x.get("name") or "") == k for x in accounts._accts().values()): raise ValueError("Ten nick jest już zajęty – wybierz inny.")
        r = P.get(uid) or {}; r["nick"] = n; P[uid] = r; store.put("user_profiles", P)
    with accounts._lock:  # jeden nick w całej aplikacji (Skrzynka, Znajomi, rankingi)
        A = accounts._accts()
        if uid in A: A[uid]["name"] = n; store.put("accounts", A)
    return n

def save(uid, d):
    out = {}
    if "nick" in d: out["nick"] = set_nick(uid, d.get("nick"))
    elif not nick_of(uid): raise ValueError("Najpierw wybierz nick.")
    with _lock:
        P = _P(); r = P.get(uid) or {}
        if "bio" in d:
            b = str(d.get("bio") or "").strip()
            r["bio"] = social.check_text(b, BIO_LEN) if b else ""
            if b and re.search(r"[\w.+-]+@[\w-]+\.[\w.]+|(?:\+?\d[\s-]?){9,}", b): raise ValueError("Nie podawaj w opisie e-maila ani numeru telefonu – profil jest anonimowy.")
        if "interests" in d:
            it = [re.sub(r"[<>\x00-\x1f]", "", str(x)).strip()[:INT_LEN] for x in (d.get("interests") or [])][:INT_MAX]
            for x in it:
                if x: social.check_text(x, INT_LEN)
            r["interests"] = [x for x in it if x]
        if "links" in d:
            L = [str(x).strip()[:120] for x in (d.get("links") or []) if str(x).strip()][:LINKS_MAX]
            for x in L:
                if not LINK_RE.fullmatch(x): raise ValueError("Linki muszą zaczynać się od https://")
            r["links"] = L
        if "hide_rank" in d:
            import battles; battles.set_privacy(uid, d.get("hide_rank") is True)
        if d.get("lang") in ("pl", "en", "es", "de", "uk"): r["lang"] = d["lang"]
        if "age" in d:
            a = d.get("age")
            if a in (None, "", 0): r["age"] = None
            else:
                try: a = int(str(a).strip())
                except Exception: raise ValueError("Wiek podaj liczbą (18–99).")
                if a < 18: raise ValueError("Luna jest tylko dla osób pełnoletnich – wiek musi wynosić co najmniej 18 lat.")
                if a > 99: raise ValueError("Wiek podaj w zakresie 18–99.")
                r["age"] = a
        if "gender" in d:
            g = str(d.get("gender") or "")
            if g and g not in GENDERS: raise ValueError("Nieznana opcja płci.")
            r["gender"] = g; r["gender_x"] = _x(d.get("gender_x")) if g == "other" else ""
        if "pron" in d:
            pn = str(d.get("pron") or "")
            if pn and pn not in PRONS: raise ValueError("Nieznane zaimki.")
            r["pron"] = pn; r["pron_x"] = _x(d.get("pron_x")) if pn == "custom" else ""
            if pn == "custom" and not r["pron_x"]: r["pron"] = ""
        for k in ("public", "show_bio", "show_interests", "show_links", "tour_done", "show_age", "show_gender", "show_pron"):
            if k in d: r[k] = d.get(k) is True
        if "avatar" in d and str(d["avatar"]).startswith("preset:"):
            v = str(d["avatar"])[7:]
            import tester_perks
            if v in tester_perks.AVATARS:   # awatary testerów – tylko dla aktywnych testerów (sprawdzane na serwerze)
                if not tester_perks.is_tester_uid(uid): raise PermissionError("Ten awatar to dodatek tylko dla testerów 🎟️")
            elif v not in PRESETS: raise ValueError("Nieznany awatar.")
            r["avatar"] = "preset:" + v
        if "avatar" in d and str(d["avatar"]).startswith("gen:"):
            r["avatar"] = str(d["avatar"])[:20]  # sprawdzane w serwerze (Premium+ i własny wygenerowany obraz)
        P[uid] = {**(P.get(uid) or {}), **r}; store.put("user_profiles", P)
    return get(uid)

def set_avatar_upload(uid, plan, data_url):
    """Dowolny obraz (własne zdjęcie, ilustracja, obraz AI) – bez etykiety „zdjęcie użytkownika”, ale ze standardową moderacją
    (kolejka avatar_mod, zgłoszenia, blokada), bez EXIF; rozmiar według limitu jakości planu."""
    m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 5 * 1024 * 1024: raise ValueError("Plik jest za duży (maks. 5 MB).")
    import upload_gate
    px = min(quality.caps(plan)["img"], 1024)  # awatar: limit planu (854 / 1024), wyświetlany w 2x/3x
    g = upload_gate.image(raw, "user_avatar", max_px=px, max_in=5 * 1024 * 1024, quality=4)  # nagość → Blocked; status i tak „pending” do decyzji moderatora
    nsfw, out, ext = g.verdict, g.bytes, g.ext
    thumb, _ = upload_gate.derived(out, max_px=64, quality=6)
    h = hashlib.sha1(out).hexdigest()[:12]
    with _lock:
        A = _A(); A[uid] = {"b": base64.b64encode(out).decode(), "ext": ext, "h": h, "status": "pending", "t": int(time.time())}; store.put("user_avatars", A)
        P = _P(); r = P.get(uid) or {}; r["avatar"] = "up:" + h; P[uid] = r; store.put("user_profiles", P)
        M = store.get("avatar_mod", {}) or {}
        M["ua-" + h] = {"id": "ua-" + h, "vid": "user-" + uid[:8], "uid": uid[:8], "name": nick_of(uid), "t": int(time.time()), "kind": "user_avatar",
                        "thumb": "data:image/jpeg;base64," + base64.b64encode(thumb).decode(), "ai_markers": [], "reports": 0, "user": uid, **({"nsfw_review": True} if nsfw != "ok" else {})}
        store.put("avatar_mod", dict(sorted(M.items(), key=lambda kv: -kv[1]["t"])[:300]))
    return "up:" + h, px

def moderate_avatar(uid, ok):
    with _lock:
        A = _A(); a = A.get(uid)
        if not a: return
        if ok: a["status"] = "approved"; A[uid] = a
        else:
            A.pop(uid, None); P = _P(); r = P.get(uid) or {}
            if str(r.get("avatar", "")).startswith("up:"): r["avatar"] = ""; P[uid] = r; store.put("user_profiles", P)
        store.put("user_avatars", A)

def avatar_img(uid, viewer_uid=None):
    a = _A().get(uid)
    if not a: return None
    if a["status"] != "approved" and viewer_uid != uid: return None  # przed akceptacją widzi tylko właściciel
    return a

def completion(uid, has_wall=False, has_agent=False):
    r = get(uid)
    done = {"nick": bool(r["nick"]), "avatar": bool(r["avatar"]), "bio": bool(r["bio"]), "interests": bool(r["interests"]), "wall": has_wall, "agent": has_agent}
    return {"steps": done, "pct": round(100 * sum(done.values()) / len(STEPS))}

def public_view(nick, viewer_uid=None):
    k = _key(nick or "")
    for uid, r in _P().items():
        if _key(r.get("nick", "")) == k and k:
            if not r.get("public") and viewer_uid != uid: return {"private": True}
            g = get(uid)
            av = g["avatar"]
            if av.startswith("up:") and not avatar_img(uid, viewer_uid): av = ""
            import moderator
            if moderator.is_admin_uid(uid): av = "mod:mustang"   # moderator: animowany mustang w niebieskiej ramce (flaga tylko z serwera)
            return {"mod": moderator.is_admin_uid(uid), "staff": moderator.staff_of_uid(uid), "model": moderator.is_model_uid(uid), "look": moderator.look_public(uid), "nick": g["nick"], "avatar": av, "uref": uid[:8] if av.startswith("up:") else "",
                    "bio": g["bio"] if g["show_bio"] else "", "interests": g["interests"] if g["show_interests"] else [],
                    "links": g["links"] if g["show_links"] else [], "mine": viewer_uid == uid, "pr": _pr(viewer_uid, uid), "ident": ident(uid, g)}
    return {"missing": True}

def _pr(viewer, uid):
    try:
        import presence; return presence.status(viewer, uid)
    except Exception: return None

def uid_by_short(s):
    return next((u for u in _P() if u[:8] == s), None)

def delete(uid):
    with _lock:
        P = _P(); P.pop(uid, None); store.put("user_profiles", P)
        A = _A(); A.pop(uid, None); store.put("user_avatars", A)

# ---------- ustawienia: powiadomienia, zaproszenia, zablokowani ----------
NOTIF_TYPES = ("battles", "friends", "messages", "updates")
INVITE = ("all", "friends_of_friends", "nobody")
def settings(uid):
    r = _P().get(uid) or {}
    n = r.get("notif") or {}
    return {"notif": {k: bool(n.get(k, True)) for k in NOTIF_TYPES}, "invite": r.get("invite", "all"),
            "blocked": [{"nick": x} for x in (r.get("blocked") or [])], "delete_at": r.get("delete_at", 0),
            "bubbles": r.get("bubbles", True) is not False,
            "online_vis": r.get("online_vis") if r.get("online_vis") in ("all", "close", "nobody") else "close"}
def notif_on(uid, kind):
    """Przełączniki z Mój panel → Powiadomienia (domyślnie włączone). Bramkują wysyłkę push: friends, messages, updates."""
    if not uid: return True
    return bool(((_P().get(uid) or {}).get("notif") or {}).get(kind, True))
def save_settings(uid, d):
    with _lock:
        P = _P(); r = P.get(uid) or {}
        if isinstance(d.get("notif"), dict):
            n = r.get("notif") or {}; n.update({k: d["notif"][k] is True for k in NOTIF_TYPES if k in d["notif"]}); r["notif"] = n
        if d.get("invite") in INVITE: r["invite"] = d["invite"]
        if d.get("bubbles") in (True, False): r["bubbles"] = d["bubbles"]  # Dymki Luny
        if d.get("online_vis") in ("all", "close", "nobody"): r["online_vis"] = d["online_vis"]  # Kto widzi, że jestem online
        if "block" in d or "unblock" in d:
            B = list(r.get("blocked") or [])
            if d.get("block"):
                b = social.nick_ok(d["block"])
                if b not in B: B.append(b)
            if d.get("unblock"): B = [x for x in B if x != d["unblock"]]
            r["blocked"] = B[:200]
        P[uid] = r; store.put("user_profiles", P)
    return settings(uid)

# ---------- usunięcie konta: 2 kroki (wpisz nick) → 30 dni na przywrócenie → trwałe usunięcie ----------
GRACE = 30 * 86400
def request_delete(uid, typed, acct_name=""):
    nk = nick_of(uid) or acct_name
    if not nk or _key(typed or "") != _key(nk): raise ValueError("Wpisz dokładnie swój nick, aby potwierdzić.")
    with _lock:
        P = _P(); r = P.get(uid) or {}; r["delete_at"] = int(time.time()) + GRACE; r["public_before_delete"] = bool(r.get("public")); r["public"] = False
        P[uid] = r; store.put("user_profiles", P)
    return r["delete_at"]
def cancel_delete(uid):
    with _lock:
        P = _P(); r = P.get(uid) or {}
        if not r.get("delete_at"): return False
        r.pop("delete_at", None); r["public"] = bool(r.pop("public_before_delete", False)); P[uid] = r; store.put("user_profiles", P)
    return True
def due_deletions(now=None):
    now = now or time.time()
    return [u for u, r in _P().items() if r.get("delete_at") and r["delete_at"] <= now]

def lang_of(uid):
    l = (_P().get(uid) or {}).get("lang", "")
    return l if l in ("pl", "en", "es", "de", "uk") else ""
def set_lang(uid, l):
    if l not in ("pl", "en", "es", "de", "uk"): raise ValueError("Nieznany język.")
    with _lock:
        P = _P(); r = P.get(uid) or {}; r["lang"] = l; P[uid] = r; store.put("user_profiles", P)
