# -*- coding: utf-8 -*-
"""Profile agentek AI: oficjalny profil Luny i profile własnych agentek użytkowników.
Zasady: tylko obrazy AI (portrety Luny z aplikacji, stroje z Butiku posiadane przez właściciela, własny obraz AI po kontroli
i ponownym kodowaniu bez EXIF); profil prywatny domyślnie; limity według planu sprawdzane na serwerze; nigdy nie ujawniamy
danych właściciela (imię, e-mail, konto) – tylko imię agentki. Liczniki wyłącznie prawdziwe."""
import base64, hashlib, re, secrets, threading, time
import store, plans, social, avatars, imgsafe, butik, partners

_lock = threading.Lock()
LIMITS = {"darmowy": 0, "podstawowa": 0, "premium": 4, "pro": 12}
NEED = {"bio": "premium", "photos": "premium", "pin": "pro"}
PRICE = {"premium": "59,99 zł", "pro": "99,99 zł"}
# Zweryfikowane, w pełni zakryte portrety Luny (te same co w Galerii agentek) i plan, od którego są dostępne jako zdjęcie profilu.
LUNA_PHOTOS = {"outfit_sweter": "podstawowa", "outfit_biznes": "premium", "outfit_wieczorowa": "premium",
               "outfit_koktajlowa": "pro", "pose_prosto": "pro", "pose_zamyslona": "pro", "pose_siedzaca": "pro", "pose_polobrot": "pro"}
LUNA_ORDER = ["outfit_sweter", "outfit_biznes", "pose_prosto", "outfit_koktajlowa", "pose_zamyslona", "outfit_wieczorowa", "pose_siedzaca", "pose_polobrot", "outfit_zakiet"]
TAGS_MAX, TAG_LEN, BIO_LEN, EX_LEN, NAME_LEN = 5, 20, 280, 120, 24
PID_RE = re.compile(r"[0-9a-f]{10}")
PRIV_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|https?://|www\.|(?:\+?\d[\s-]?){9,}", re.I)

LUNA = {
    "pl": {"bio": "Ciepła trenerka głosu z hiszpańskim temperamentem. Mówi jak jest – życzliwie, konkretnie i z uśmiechem.",
           "tags": ["ciepła", "konkretna", "cierpliwa", "z humorem"], "exercise": "Ciche „mmm” na wydechu – 5 powtórzeń przed każdą rozmową."},
    "en": {"bio": "A warm voice coach with a Spanish temperament. She tells it like it is – kindly, clearly and with a smile.",
           "tags": ["warm", "direct", "patient", "witty"], "exercise": "A soft “mmm” on the out-breath – 5 times before every conversation."},
    "es": {"bio": "Una cálida entrenadora de voz con temperamento español. Dice las cosas como son: con cariño, claridad y una sonrisa.",
           "tags": ["cálida", "directa", "paciente", "con humor"], "exercise": "Un suave «mmm» al exhalar, 5 veces antes de cada conversación."},
    "de": {"bio": "Eine warmherzige Stimmtrainerin mit spanischem Temperament. Sie sagt, wie es ist – freundlich, klar und mit einem Lächeln.",
           "tags": ["warm", "direkt", "geduldig", "humorvoll"], "exercise": "Ein leises „mmm“ beim Ausatmen – 5-mal vor jedem Gespräch."},
    "uk": {"bio": "Тепла тренерка голосу з іспанським темпераментом. Каже як є – доброзичливо, чітко й з усмішкою.",
           "tags": ["тепла", "конкретна", "терпляча", "з гумором"], "exercise": "Тихе «ммм» на видиху – 5 разів перед кожною розмовою."},
}

def _P(): return store.get("agent_profiles", {}) or {}
def _owners(): return store.get("agent_profile_owner", {}) or {}
def _imgs(): return store.get("agent_profile_img", {}) or {}
def target(pid): return "agent:p-" + pid
def limit(plan): return LIMITS.get(plan, 0)

def _photo_url(ref, pid=""):
    k, _, v = str(ref).partition(":")
    if k == "l" and v in LUNA_ORDER: return f"/catalog/luna/{v}.jpg"
    if k == "b":
        i = butik.item(v); return (i.get("image_worn") or i.get("image")) if i else None
    if k == "own" and pid: return f"/api/agent/profile/img/{pid}.jpg?v={v[:8]}"
    if k == "g" and re.fullmatch(r"[0-9a-f]{12}", v): return f"/api/agent/gen/img/{v}.jpg"   # obraz z Generatora (po moderacji)
    return None

def options(plan, items, pid, has_own):
    """Zdjęcia, które właściciel może dodać: portrety Luny dostępne w jego planie, posiadane stroje z Butiku, własny obraz AI."""
    out = [{"ref": "l:" + n, "url": _photo_url("l:" + n), "plan": need, "ok": plans.has(plan, need)} for n, need in LUNA_PHOTOS.items()]
    for it in items or []:
        u = _photo_url("b:" + str(it))
        if u: out.append({"ref": "b:" + str(it), "url": u, "plan": "premium", "ok": plans.has(plan, "premium"), "butik": True})
    if has_own: out.append({"ref": "own:" + has_own, "url": _photo_url("own:" + has_own, pid), "plan": "premium", "ok": plans.has(plan, "premium"), "own": True})
    return out

def _allowed(ref, plan, items, own):
    k, _, v = str(ref).partition(":")
    if k == "l": return v in LUNA_PHOTOS and plans.has(plan, LUNA_PHOTOS[v])
    if k == "b": return v in (items or []) and butik.item(v) is not None
    if k == "own": return bool(own) and v == own
    return False

def _clean(t, n, field):
    t = re.sub(r"[<>\x00-\x08\x0b-\x1f\x7f]", "", str(t or "")).strip()
    if not t: return ""
    if len(t) > n: raise ValueError(f"Za długo – maksymalnie {n} znaków.")
    if PRIV_RE.search(t): raise ValueError("Bez e-maili, linków i numerów telefonu – profil pokazuje tylko agentkę.")
    return social.check_text(t, n)

def mine(uid):
    pid = _owners().get(uid); return pid, (_P().get(pid) if pid else None)

def caps(plan):
    return {"edit": plans.has(plan, "premium"), "bio": plans.has(plan, "premium"), "max_photos": limit(plan), "pin": plans.has(plan, "pro"),
            "need": "premium", "price": PRICE, "plan": plan, "plan_name": plans.NAMES.get(plan, plan)}

def lock(need):
    return {"error": "plan_required", "required": need, "plan_name": plans.NAMES[need], "price": PRICE[need],
            "message": f"Profil własnej agentki AI jest w planie {plans.NAMES[need]}."}

def save(uid, plan, items, d):
    """Zapis profilu właściciela. Zwraca (rekord, None) albo (None, błąd planu). ValueError dla złych danych."""
    if not plans.has(plan, "premium"): return None, lock("premium")
    with _lock:
        P = _P(); O = _owners(); pid = O.get(uid)
        r = P.get(pid) if pid else None
        if not r:
            pid = secrets.token_hex(5); r = {"id": pid, "uid": uid, "t": int(time.time()), "public": False, "photos": [], "pinned": "", "tags": [], "bio": "", "exercise": "", "name": ""}
        nm = re.sub(r"[<>\x00-\x1f]", "", str(d.get("name", r["name"]) or "")).strip()[:NAME_LEN]
        if len(nm) < 2: raise ValueError("Podaj imię agentki (min. 2 znaki).")
        if re.fullmatch(r"\W*luna\W*", social._norm(nm)): raise ValueError("Imię „Luna” jest zarezerwowane dla oficjalnej agentki.")
        _clean(nm, NAME_LEN, "name")
        bio = _clean(d.get("bio", r["bio"]), BIO_LEN, "bio"); ex = _clean(d.get("exercise", r["exercise"]), EX_LEN, "exercise")
        tags = d.get("tags", r["tags"]); tags = tags if isinstance(tags, list) else []
        tags = [x for x in (_clean(t, TAG_LEN, "tag").lstrip("#") for t in tags[:TAGS_MAX + 3]) if x][:TAGS_MAX]
        ph = d.get("photos", r["photos"]); ph = [str(x) for x in ph] if isinstance(ph, list) else []
        ph = list(dict.fromkeys(ph))
        own = r.get("own", "")
        bad = [x for x in ph if not (_allowed(x, plan, items, own) or (x.startswith("g:") and x[2:] in (r.get("gen_imgs") or [])))]
        if bad: raise ValueError("Tego zdjęcia nie można dodać w Twoim planie.")
        if len(ph) > limit(plan): return None, dict(lock("pro") if plan != "pro" else {"error": "too_many"}, max=limit(plan),
                                                     message=f"W planie {plans.NAMES[plan]} profil ma do {limit(plan)} zdjęć.")
        pin = str(d.get("pinned", r.get("pinned", "")) or "")
        if pin and not plans.has(plan, "pro"): return None, dict(lock("pro"), message="Przypięte ulubione zdjęcie jest w planie Pro / Ultra.")
        if pin and pin not in ph: pin = ""
        r.update(name=nm, bio=bio, exercise=ex, tags=tags, photos=ph, pinned=pin, public=d.get("public", r["public"]) is True, edited=int(time.time()))
        P[pid] = r; O[uid] = pid; store.put("agent_profiles", P); store.put("agent_profile_owner", O)
    return r, None

def save_own(uid, plan, data_url, declared):
    """Własny obraz AI agentki: oświadczenie + odrzucenie zdjęć z aparatu + ponowne kodowanie bez EXIF + kolejka moderacji."""
    if not plans.has(plan, "premium"): return None, lock("premium")
    pid, r = mine(uid)
    if not r: raise ValueError("Najpierw zapisz profil (imię agentki).")
    import quality
    try: _raw0 = base64.b64decode(re.sub(r"^data:image/\w+;base64,", "", str(data_url or "")))
    except Exception: _raw0 = b""
    if _raw0 and quality.is_user_photo(_raw0):
        raise PermissionError("To zdjęcie zostało dodane jako „Zdjęcie użytkownika” – nie może być twarzą agentki AI.")
    url, info = avatars.check_upload(data_url, declared, "prof-" + pid, r["name"])  # pełna bramka (upload_gate) + kolejka moderacji awatarów
    import upload_gate
    g = upload_gate.image(data_url, "agent_own", max_px=768, max_in=5 * 1024 * 1024, quality=4, review="hold")  # ten sam plik, większy rozmiar
    out, ext = g.bytes, g.ext
    h = hashlib.sha1(out, usedforsecurity=False).hexdigest()[:10]
    with _lock:
        I = _imgs(); I[pid] = {"b": base64.b64encode(out).decode(), "ext": ext, "h": h, "t": int(time.time())}; store.put("agent_profile_img", I)
        P = _P(); x = P.get(pid)
        old = x.get("own", "")
        x["own"] = h; x["photos"] = [("own:" + h) if p == "own:" + old else p for p in x["photos"]]
        if x.get("pinned") == "own:" + old: x["pinned"] = "own:" + h
        P[pid] = x; store.put("agent_profiles", P)
        M = store.get("avatar_mod", {}) or {}
        for k, v in M.items():
            if v.get("vid") == "prof-" + pid: v["kind"] = "profile"; v["uid"] = uid[:8]; v["profile"] = pid
        store.put("avatar_mod", M)
    return h, None

GEN_CROPS = {"portret": "crop='min(iw,ih*4/5)':ih", "kwadrat": "crop='min(iw,ih)':'min(iw,ih)'", "szeroki": "null"}
def generate(uid, plan, base, crop="portret"):
    """Generator agentek: obraz AI złożony z istniejących ujęć AI Luny (strój/poza dozwolone w planie), wyjście wg planu:
    Premium 1280 px, Pro / Ultra 1920 px (najwyższa rozdzielczość źródła – bez powiększania). Dzienny limit. Zawsze oznaczony jako AI."""
    import quality, os, subprocess, tempfile
    if not plans.has(plan, "premium"): return None, quality.lock("premium", "gen")
    if base not in LUNA_PHOTOS: raise ValueError("Wybierz strój lub pozę z listy.")
    if not plans.has(plan, LUNA_PHOTOS[base]): return None, dict(quality.lock(LUNA_PHOTOS[base], "gen"), message=f"Ta poza/strój jest w planie {plans.NAMES[LUNA_PHOTOS[base]]}.")
    if crop not in GEN_CROPS: crop = "portret"
    pid, r = mine(uid)
    if not r: raise ValueError("Najpierw zapisz profil (imię agentki).")
    ok, n, lim = quality.gen_take(uid, plan)
    if not ok: raise PermissionError(f"Dzisiejszy limit generatora ({lim}) został wykorzystany. Wróć jutro. 💚")
    px = quality.caps(plan)["gen_px"]
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "catalog", "luna", base + "@2x.jpg")
    if not os.path.exists(src): src = src.replace("@2x", "")
    with tempfile.TemporaryDirectory() as d:
        dst = os.path.join(d, "o.jpg")
        vf = GEN_CROPS[crop] + f",scale='min({px},iw)':'min({px},ih)':force_original_aspect_ratio=decrease"
        rr = subprocess.run([imgsafe._ff(), "-v", "error", "-y", "-i", src, "-map_metadata", "-1", "-frames:v", "1", "-vf", vf, "-q:v", "2", dst], capture_output=True, timeout=30)
        if rr.returncode or not os.path.exists(dst): raise ValueError("Nie udało się wygenerować obrazu.")
        out = open(dst, "rb").read()
        import upload_gate   # wynik generatora też przez bramkę (źródło: ubrane ujęcia Luny; blokada = brak obrazu)
        out = upload_gate.image(out, "luna_gen", max_px=px, max_in=20 * 1024 * 1024, quality=2).bytes
        pr = subprocess.run([imgsafe._ff(), "-i", dst], capture_output=True, timeout=10).stderr.decode()
        mm = re.search(r", (\d{2,5})x(\d{2,5})", pr); real = max(int(mm.group(1)), int(mm.group(2))) if mm else px
    h = hashlib.sha1(out).hexdigest()[:10]
    with _lock:
        I = _imgs(); I[pid] = {"b": base64.b64encode(out).decode(), "ext": "jpg", "h": h, "t": int(time.time()), "gen": base, "ai": True}; store.put("agent_profile_img", I)
        P = _P(); x = P.get(pid); old = x.get("own", "")
        x["own"] = h; x["photos"] = [("own:" + h) if p == "own:" + old else p for p in x["photos"]]
        if x.get("pinned") == "own:" + old: x["pinned"] = "own:" + h
        P[pid] = x; store.put("agent_profiles", P)
    return {"h": h, "url": _photo_url("own:" + h, pid), "ref": "own:" + h, "px": real, "cap_px": px, "used": n, "limit": lim, "ai": True}, None

def own_img(pid):
    r = _P().get(pid)
    if not r or r.get("hidden") or r["uid"][:8] in avatars.blocked_uids(): return None
    i = _imgs().get(pid); return i if i and i["h"] == r.get("own") else None

def battle_stats(pid, uid=None):
    """Prawdziwe statystyki z Bitew agentek (wygrane i historia). None, gdy brak danych – wtedy profil ich nie pokazuje."""
    try:
        import battles
        if pid == "luna": eid, wins = "luna", (battles._cfg().get("luna") or {}).get("wins", 0)
        else:
            e = battles.my_entry(uid) if uid else None
            if not e or e.get("status") != "approved": return None
            eid, wins = e["id"], e.get("wins", 0)
        hist = []
        for b in battles._state().get("hist", []):
            if b.get("reason") != "end" or eid not in (b["a"]["id"], b["b"]["id"]): continue
            me, op = ("a", "b") if b["a"]["id"] == eid else ("b", "a")
            hist.append({"opp": b[op]["name"], "mine": b["v" + me], "theirs": b["v" + op], "end": b["end"],
                         "result": "win" if b.get("winner") == me else "draw" if not b.get("winner") else "loss"})
        out = {"wins": wins, "history": hist[:20]}
        try:   # specjalizacje (kategorie bitew) i miejsce w rankingu każdej kategorii – z prawdziwych wyników
            import battle_categories as BC
            pr = battles.profile(eid) or {}
            out["cats"] = [{"id": c, "emoji": BC.CAT[c]["emoji"], "name": BC.CAT[c]["name"], "rank": (pr.get("cranks") or {}).get(c)} for c in (pr.get("cats") or []) if c in BC.CAT]
        except Exception: out["cats"] = []
        return out if (wins or hist or out["cats"]) else None
    except Exception: return None

def view(pid, lang="pl", viewer=None, owner_uid=None, owner_plan=None):
    """Publiczny widok profilu (bez danych właściciela). None = brak lub prywatny (dla obcych)."""
    lg = lang if lang in LUNA else "pl"
    if pid == "luna":
        L = LUNA[lg]; t = target("luna"); c = social.counts(t, viewer)
        return {"id": "luna", "official": True, "ai": True, "name": "Luna", "bio": L["bio"], "tags": L["tags"], "exercise": L["exercise"],
                "photos": [{"ref": "l:" + n, "url": f"/catalog/luna/{n}.jpg"} for n in LUNA_ORDER], "pinned": "l:pose_prosto",
                "likes": c["up"], "liked": c["mine"] == 1, "target": t, "public": True, "battles": battle_stats("luna"), "tier": "", "partner": None}
    if not PID_RE.fullmatch(str(pid or "")): return None
    r = _P().get(pid)
    if not r or r.get("hidden"): return None
    is_owner = owner_uid is not None and r["uid"] == owner_uid
    if not is_owner and not r.get("public"): return None
    pl = owner_plan or "darmowy"
    if not is_owner and not plans.has(pl, "premium"): return None  # bez planu profil nie jest publiczny
    lim = max(limit(pl), 0)
    ph = [p for p in r["photos"] if _photo_url(p, pid) and not (p.startswith("own:") and not own_img(pid))][:lim]
    pin = r.get("pinned") if plans.has(pl, "pro") and r.get("pinned") in ph else ""
    t = target(pid); c = social.counts(t, viewer)
    return {"id": pid, "official": False, "ai": True, "name": r["name"], "bio": r["bio"] if plans.has(pl, "premium") else "", "tags": r["tags"],
            "exercise": r["exercise"], "photos": [{"ref": p, "url": _photo_url(p, pid)} for p in ph], "pinned": pin,
            "likes": c["up"], "liked": c["mine"] == 1, "target": t, "public": bool(r.get("public")), "mine": is_owner,
            "battles": battle_stats(pid, r["uid"]), "partner": partners.get(r["uid"]), "tier": pl if pl in ("premium", "pro") else "plain",
            "pr": _pr(owner_uid, r["uid"])}  # status online twórczyni – tylko gdy jej ustawienie prywatności na to pozwala (presence.can_see)

def _pr(viewer, uid):
    try:
        import presence; return presence.status(viewer, uid)
    except Exception: return None

def public_ids():
    return [k for k, v in _P().items() if v.get("public") and not v.get("hidden")]

def admin(pid, action):
    with _lock:
        P = _P(); r = P.get(pid)
        if not r: raise KeyError(pid)
        if action in ("hide", "show"): r["hidden"] = action == "hide"
        elif action == "private": r["public"] = False
        else: raise ValueError("bad action")
        store.put("agent_profiles", P)
    return {k: v for k, v in r.items() if k != "uid"}

def delete_owner(uid):
    with _lock:
        O = _owners(); pid = O.pop(uid, None)
        if not pid: return
        P = _P(); P.pop(pid, None); I = _imgs(); I.pop(pid, None)
        store.put("agent_profiles", P); store.put("agent_profile_owner", O); store.put("agent_profile_img", I)


AUTO_NAMES = ("Mira", "Ola", "Iga", "Nela", "Zoe", "Ada", "Lena", "Maja", "Ina", "Tola")
def create_from_gen(uid, plan, draft, img_ids):
    """Generator z opisu (krok 5): agentka z automatycznym profilem – imię, 1–3 specjalizacje, krótkie bio – i zatwierdzonymi obrazami AI.
    Możliwości profilu wynikają z planu właścicielki (limit zdjęć, przypięte itd.); profil startuje jako prywatny."""
    import agentgen as G
    sp = [G.OPTS["spec"][x]["pl"] for x in draft.get("spec", [])][:3]
    pers = G.OPTS["personality"].get(draft.get("personality") or "", {}).get("pl", "")
    voice = G.OPTS["voice"].get(draft.get("voice") or "", {}).get("pl", "")
    with _lock:
        P = _P(); O = _owners(); pid = O.get(uid); r = P.get(pid) if pid else None
        if not r:
            pid = secrets.token_hex(5); r = {"id": pid, "uid": uid, "t": int(time.time()), "public": False, "photos": [], "pinned": "", "tags": [], "bio": "", "exercise": "", "name": ""}
            O[uid] = pid; store.put("agent_profile_owner", O)
        nm = draft.get("name") or r.get("name") or AUTO_NAMES[int(hashlib.sha1((uid + pid).encode()).hexdigest(), 16) % len(AUTO_NAMES)]
        bio = (pers.capitalize() + " trenerka AI" if pers else "Trenerka AI") + (": " + ", ".join(sp) if sp else "") + "." + (f" Głos: {voice}." if voice else "")
        gi = list(dict.fromkeys((r.get("gen_imgs") or []) + list(img_ids)))[-24:]
        ph = ["g:" + v for v in img_ids]   # profil z Generatora: tylko zatwierdzone obrazy AI tej agentki
        r.update(name=nm[:NAME_LEN], bio=bio[:BIO_LEN], tags=sp, photos=ph[:limit(plan)], gen_imgs=gi, from_gen=True, edited=int(time.time()))
        P[pid] = r; store.put("agent_profiles", P)
    return pid

def admin_real_photo(pid, data_url, agreement):
    """TYLKO admin: agentka na podstawie zdjęć PRAWDZIWEJ osoby – wyłącznie przy potwierdzonej współpracy (partnerka/casting,
    podpisana umowa i zgoda). Flaga real_person + numer umowy na agentce. Zwykli użytkownicy nie mają tej ścieżki."""
    import partners
    agreement = re.sub(r"[^\w./ -]", "", str(agreement or ""))[:60]
    if len(agreement) < 3: raise ValueError("Podaj numer podpisanej umowy / zgody.")
    with _lock:
        P = _P(); r = P.get(pid)
        if not r: raise ValueError("Nie ma takiej agentki.")
        if not partners.is_partner(r["uid"]): raise PermissionError("Najpierw nadaj status współpracy (partnerka / casting).")
    import upload_gate   # filtr nagości obowiązuje też ścieżkę admina; „na granicy” = odmowa (Held), bez publikacji
    g = upload_gate.image(data_url, "admin_real", max_px=1920, max_in=12 * 1024 * 1024, quality=2, review="hold")
    out, ext = g.bytes, g.ext
    h = hashlib.sha1(out).hexdigest()[:10]
    with _lock:
        I = _imgs(); I[pid] = {"b": base64.b64encode(out).decode(), "ext": ext, "h": h, "t": int(time.time()), "ai": False, "real_person": True}; store.put("agent_profile_img", I)
        P = _P(); r = P[pid]; r["own"] = h; r["real_person"] = True; r["agreement"] = agreement
        if "own:" + h not in r["photos"]: r["photos"] = ["own:" + h] + r["photos"]
        P[pid] = r; store.put("agent_profiles", P)
    return {"ok": True, "own": h}
