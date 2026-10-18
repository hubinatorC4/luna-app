# -*- coding: utf-8 -*-
"""Generator agentek z OPISU (v1.6.6, t429u/t430u). Bez przesyłania zdjęć przez zwykłych użytkowników.
Kroki: 1 Opis → 2 Warianty (AI, kilka próbek) → 3 Wybór (1–4) → 4 Sprawdzenie (nsfw_filter + moderacja, tylko wybrane) → 5 Profil gotowy.
Uczciwość: prawdziwa generacja wymaga dostawcy AI (LUNA_IMAGE_API_URL / LUNA_IMAGE_API_KEY, wideo: LUNA_VIDEO_API_URL / KEY).
Bez klucza zadanie czeka w kolejce z jasnym komunikatem – nigdy nie podstawiamy gotowych zdjęć Luny jako „wygenerowanych”.
Kontrakt dostawcy obrazów: POST {prompt, negative, n, max_px} → {"images": ["<base64 JPEG/PNG>", ...]}.
Kontrakt dostawcy wideo:   POST {prompt, image (base64 twarzy agentki), n, seconds, height} → {"videos": ["<base64 MP4>", ...]}.
Agentki na podstawie zdjęć PRAWDZIWEJ osoby: tylko ścieżka admina przy potwierdzonej współpracy (umowa + zgoda), flaga na agentce."""
import base64, hashlib, json, os, re, secrets, threading, time, urllib.request
import store, plans, quality, imgsafe, social

N_IMG, N_VID, PICK_MAX = 4, 3, 4
DESC_LEN, NAME_LEN = 200, 24
SRC_TTL = 30 * 86400
_lock = threading.Lock()

def _o(pl, en, es, de, uk): return {"pl": pl, "en": en, "es": es, "de": de, "uk": uk}
OPTS = {
 "hair": {"blond": _o("blond", "blonde", "rubio", "blond", "біляве"), "brown": _o("brązowe", "brown", "castaño", "braun", "каштанове"),
          "black": _o("czarne", "black", "negro", "schwarz", "чорне"), "red": _o("rude", "red", "pelirrojo", "rot", "руде"),
          "silver": _o("srebrne", "silver", "plateado", "silbern", "срібне"), "pastel": _o("pastelowe", "pastel", "pastel", "pastell", "пастельне")},
 "eyes": {"brown": _o("brązowe", "brown", "marrones", "braun", "карі"), "blue": _o("niebieskie", "blue", "azules", "blau", "блакитні"),
          "green": _o("zielone", "green", "verdes", "grün", "зелені"), "hazel": _o("piwne", "hazel", "avellana", "haselnuss", "горіхові"),
          "grey": _o("szare", "grey", "grises", "grau", "сірі")},
 "style": {"elegant": _o("elegancki", "elegant", "elegante", "elegant", "елегантний"), "casual": _o("swobodny", "casual", "informal", "lässig", "повсякденний"),
           "sporty": _o("sportowy", "sporty", "deportivo", "sportlich", "спортивний"), "business": _o("biznesowy", "business", "de negocios", "business", "діловий"),
           "retro": _o("retro", "retro", "retro", "retro", "ретро"), "boho": _o("boho", "boho", "boho", "boho", "бохо")},
 "outfit": {"sweater": _o("sweter z golfem", "turtleneck sweater", "jersey de cuello alto", "Rollkragenpullover", "светр з горлом"),
            "blazer": _o("marynarka i spodnie", "blazer and trousers", "americana y pantalón", "Blazer und Hose", "жакет і штани"),
            "maxi": _o("sukienka maxi z rękawem", "long-sleeve maxi dress", "vestido largo con manga", "Maxikleid mit Ärmeln", "сукня максі з рукавами"),
            "jumpsuit": _o("kombinezon", "jumpsuit", "mono", "Jumpsuit", "комбінезон"), "coat": _o("płaszcz", "coat", "abrigo", "Mantel", "пальто"),
            "tracksuit": _o("dres", "tracksuit", "chándal", "Trainingsanzug", "спортивний костюм")},
 "personality": {"calm": _o("spokojna", "calm", "tranquila", "ruhig", "спокійна"), "cheerful": _o("pogodna", "cheerful", "alegre", "fröhlich", "життєрадісна"),
                 "witty": _o("dowcipna", "witty", "ingeniosa", "witzig", "дотепна"), "warm": _o("ciepła", "warm", "cálida", "herzlich", "тепла"),
                 "energetic": _o("energiczna", "energetic", "enérgica", "energisch", "енергійна"), "factual": _o("rzeczowa", "matter-of-fact", "directa", "sachlich", "по суті")},
 "voice": {"soft": _o("miękki", "soft", "suave", "sanft", "м'який"), "warm": _o("ciepły", "warm", "cálida", "warm", "теплий"),
           "bright": _o("jasny", "bright", "brillante", "hell", "дзвінкий"), "low": _o("niski", "low", "grave", "tief", "низький"),
           "crisp": _o("wyraźny", "crisp", "nítida", "klar", "чіткий")},
 "spec": {"diction": _o("dykcja", "diction", "dicción", "Aussprache", "дикція"), "breath": _o("oddech", "breathing", "respiración", "Atmung", "дихання"),
          "public": _o("wystąpienia", "public speaking", "hablar en público", "Reden halten", "виступи"), "tempo": _o("tempo mowy", "speech pace", "ritmo del habla", "Sprechtempo", "темп мовлення"),
          "confidence": _o("pewność siebie", "confidence", "seguridad", "Selbstsicherheit", "впевненість"), "emotion": _o("emocje w głosie", "emotion in voice", "emoción en la voz", "Gefühl in der Stimme", "емоції в голосі")},
}
EN_PROMPT = {"hair": "{} hair", "eyes": "{} eyes", "style": "{} style", "outfit": "wearing a modest {}"}
SAFE = ("original fictional adult woman (25+), fully clothed modest outfit, friendly portrait, soft studio light, no logos or brands, "
        "does not resemble any real person, clearly an AI character")
NEG = "nudity, lingerie, swimwear, cleavage, sexual, minor, child, teen, logo, brand, celebrity, real person, text, watermark"
# czarna lista opisu: treści seksualne, nieletni, marki, „jak <prawdziwa osoba>”
BLOCK = re.compile(r"(sex|seks|nag[aio]|nud|erot|porn|bielizn|lingerie|bikini|strip|topless|cycki|biust|boob|nsfw|fetysz|fetish|"
                   r"dziec|dziewczynk|nastolat|nieletn|teen|child|kid|loli|schoolgirl|uczennic|minor|"
                   r"\b(?:nike|adidas|gucci|chanel|louis ?vuitton|prada|dior|zara|h&m|apple|coca[- ]?cola|pepsi|supreme|balenciaga|versace)\b|"
                   r"celeb|influencer|gwiazd[ay] (?:filmu|tv)|aktork[ai]\b|piosenkark)", re.I)
FULLNAME = re.compile(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\b")

def engine_img(): return bool(os.getenv("LUNA_IMAGE_API_URL") and os.getenv("LUNA_IMAGE_API_KEY"))
def engine_vid(): return bool(os.getenv("LUNA_VIDEO_API_URL") and os.getenv("LUNA_VIDEO_API_KEY"))

def options(lang="pl"):
    return {k: [{"id": i, "label": v.get(lang) or v["pl"]} for i, v in d.items()] for k, d in OPTS.items()}

def clean_desc(t):
    t = re.sub(r"[<>\x00-\x1f\x7f]", "", str(t or "")).strip()[:DESC_LEN]
    if not t: return ""
    if BLOCK.search(t): raise ValueError("Opis zawiera niedozwolone słowa (treści seksualne, nieletni, marki albo prawdziwe osoby). Opisz charakter i styl agentki. 💚")
    if FULLNAME.search(t): raise ValueError("Bez imion i nazwisk prawdziwych osób – agentka ma być oryginalna. 😉")
    social.check_text(t, DESC_LEN)
    return t

def _J(): return store.get("agent_gen", {}) or {}
def _put(J): store.put("agent_gen", J)

def prompt(d):
    parts = [EN_PROMPT[k].format(OPTS[k][d[k]]["en"]) for k in ("hair", "eyes", "style", "outfit") if d.get(k)]
    if d.get("personality"): parts.append(OPTS["personality"][d["personality"]]["en"] + " expression")
    if d.get("desc"): parts.append("details: " + d["desc"])
    return ", ".join(parts + [SAFE])

def _draft_in(d):
    out = {}
    for k in ("hair", "eyes", "style", "outfit", "personality", "voice"):
        v = str(d.get(k) or "")
        if v and v not in OPTS[k]: raise ValueError("Nieznana opcja.")
        out[k] = v
    for k in ("hair", "outfit", "personality"):
        if not out[k]: raise ValueError("Wybierz włosy, strój i charakter – resztę możesz pominąć.")
    sp = [s for s in (d.get("spec") or []) if s in OPTS["spec"]][:3]
    out["spec"] = sp or ["diction"]
    out["desc"] = clean_desc(d.get("desc"))
    nm = re.sub(r"[<>\x00-\x1f]", "", str(d.get("name") or "")).strip()[:NAME_LEN]
    if nm:
        if re.fullmatch(r"\W*luna\W*", nm.lower()) or FULLNAME.search(nm) or BLOCK.search(nm): raise ValueError("Wybierz inne imię agentki.")
        social.check_text(nm, NAME_LEN)
    out["name"] = nm
    return out

def current(uid):
    J = _J(); js = [j for j in J.values() if j["uid"] == uid and j["kind"] == "img"]
    return max(js, key=lambda j: j["t"]) if js else None

def submit(uid, plan, d):
    """Krok 1→2: zapis opisu i zadanie wygenerowania wariantów (w planie). Zwraca (zadanie, None) albo (None, blokada planu)."""
    if not plans.has(plan, "premium"): return None, quality.lock("premium", "gen")
    dr = _draft_in(d)
    cur = current(uid)
    if cur and cur["status"] in ("waiting", "generating", "checking"): raise ValueError("Poprzednie zadanie jeszcze trwa. 🙂")
    j = {"id": secrets.token_hex(6), "uid": uid, "kind": "img", "t": int(time.time()), "plan": plan, "px": quality.caps(plan)["gen_px"],
         "draft": dr, "prompt": prompt(dr), "status": "waiting", "variants": [], "picked": [], "approved": [], "note": ""}
    with _lock: J = _J(); J[j["id"]] = j; _put(J)
    _kick(j["id"])
    return view(j), None

def _call(url, key, body, timeout=120):
    rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(rq, timeout=timeout) as r: return json.loads(r.read().decode())

def _kick(jid):
    j = _J().get(jid)
    if not j: return
    if (j["kind"] == "img" and not engine_img()) or (j["kind"] == "vid" and not engine_vid()): return  # czeka w kolejce – uczciwie
    threading.Thread(target=_run, args=(jid,), daemon=True).start()

def _upd(jid, **kw):
    with _lock:
        J = _J(); j = J.get(jid)
        if j: j.update(kw); _put(J)
        return j

def _run(jid):
    j = _J().get(jid)
    if not j or j["status"] != "waiting": return
    ok, n, lim = quality.gen_take(j["uid"], j["plan"])
    if not ok: _upd(jid, note="limit"); return   # limit dzienny – zadanie poczeka do jutra
    _upd(jid, status="generating")
    try:
        if j["kind"] == "img":
            r = _call(os.getenv("LUNA_IMAGE_API_URL"), os.getenv("LUNA_IMAGE_API_KEY"), {"prompt": j["prompt"], "negative": NEG, "n": N_IMG, "max_px": j["px"]})
            vs = []
            for b in (r.get("images") or [])[:N_IMG]:
                out, ext = imgsafe.reencode(base64.b64decode(b), max_px=j["px"], max_in=20 * 1024 * 1024, quality=2)
                if quality.is_user_photo(out): continue   # odcisk: zdjęcie z walla nigdy nie zostaje twarzą agentki
                vid = secrets.token_hex(6); store.put("agimg:" + vid, {"b": base64.b64encode(out).decode(), "ext": ext, "uid": j["uid"], "ai": True})
                vs.append(vid)
        else:
            face = store.get("agimg:" + j["face"], {}) or {}
            r = _call(os.getenv("LUNA_VIDEO_API_URL"), os.getenv("LUNA_VIDEO_API_KEY"), {"prompt": j["prompt"], "negative": NEG, "image": face.get("b", ""), "n": N_VID,
                                                                                         "seconds": j["secs"], "height": j["h"]}, timeout=600)
            import agentvideo
            os.makedirs(agentvideo.VDIR, exist_ok=True); vs = []
            for b in (r.get("videos") or [])[:N_VID]:
                vid = secrets.token_hex(6); open(os.path.join(agentvideo.VDIR, "g_" + vid + ".mp4"), "wb").write(base64.b64decode(b)); vs.append(vid)
        _upd(jid, status="variants" if vs else "failed", variants=vs, note="" if vs else "empty")
    except Exception as e:
        _upd(jid, status="waiting", note="retry")   # błąd dostawcy: zostaje w kolejce

def pick(uid, jid, ids):
    """Krok 3→4: wybrane warianty (1–4) idą do nsfw_filter + moderacji; pozostałe są usuwane."""
    J = _J(); j = J.get(jid)
    if not j or j["uid"] != uid or j["status"] != "variants": raise ValueError("Nie ma wariantów do wyboru.")
    ids = [i for i in dict.fromkeys(ids or []) if i in j["variants"]][:PICK_MAX if j["kind"] == "img" else 1]
    if not ids: raise ValueError("Wybierz co najmniej jeden wariant.")
    for v in j["variants"]:
        if v not in ids: _drop(j, v)
    verdict = {}
    for v in ids:
        verdict[v] = _nsfw(j, v)
    bad = [v for v, ok in verdict.items() if ok is False]
    for v in bad: _drop(j, v)
    keep = [v for v in ids if v not in bad]
    j2 = _upd(jid, picked=keep, variants=keep, status="checking" if keep else "rejected", note="nsfw" if bad else "")
    return view(j2)

def _nsfw(j, v):
    """nsfw_filter (moduł zespołu bezpieczeństwa). Brak modułu lub błąd = „zamknięte”: decyzję podejmuje moderator (None)."""
    try:
        import nsfw_filter
        if j["kind"] != "img": return None    # wideo: filtr klatkowy nie jest jeszcze dostępny → moderator
        raw = base64.b64decode((store.get("agimg:" + v) or {})["b"])
        verdict, _why, _sc = nsfw_filter.classify(raw)   # ok | review | block (fail-closed → review)
        return False if verdict == "block" else None   # nawet „ok” i tak trafia do moderatora
    except Exception: return None

def _drop(j, v):
    if j["kind"] == "img": store.put("agimg:" + v, None)
    else:
        try:
            import agentvideo; os.remove(os.path.join(agentvideo.VDIR, "g_" + v + ".mp4"))
        except Exception: pass

def moderate(jid, approve_ids, plan_of):
    """Krok 4→5 (moderator): zatwierdzone obrazy → agentka z automatycznym profilem; odrzucone są usuwane."""
    J = _J(); j = J.get(jid)
    if not j or j["status"] != "checking": raise ValueError("Brak zadania do sprawdzenia.")
    ok = [v for v in j["picked"] if v in (approve_ids or [])]
    for v in j["picked"]:
        if v not in ok: _drop(j, v)
    if not ok: _upd(jid, status="rejected", approved=[], note="mod"); return _J()[jid]
    if j["kind"] == "img":
        import profiles
        mark_approved(ok)
        pid = profiles.create_from_gen(j["uid"], plan_of(j["uid"]), j["draft"], ok)
        _upd(jid, status="done", approved=ok, pid=pid)
    else:
        _upd(jid, status="done", approved=ok)
    try:
        import inbox
        inbox.deliver(j["uid"], "important", title={"pl": "✨ Twoja agentka AI jest gotowa", "en": "✨ Your AI agent is ready", "es": "✨ Tu agente IA está lista",
                                                    "de": "✨ Deine KI-Agentin ist fertig", "uk": "✨ Ваша ШІ-агентка готова"} if j["kind"] == "img" else
                      {"pl": "🎬 Film agentki zatwierdzony", "en": "🎬 Agent video approved", "es": "🎬 Vídeo de la agente aprobado", "de": "🎬 Agentinnen-Video freigegeben", "uk": "🎬 Відео агентки схвалено"},
                      body={"pl": "Przeszła sprawdzenie i ma już profil. Pora na pierwszą bitwę? 😄", "en": "She passed the check and has a profile. First battle, maybe? 😄",
                            "es": "Pasó la revisión y ya tiene perfil. ¿Primera batalla? 😄", "de": "Sie hat die Prüfung bestanden und ein Profil. Erstes Battle? 😄",
                            "uk": "Вона пройшла перевірку й уже має профіль. Може, перший батл? 😄"}, link="/agentka.html?id=me", dedupe="ag:" + jid)
    except Exception: pass
    return _J()[jid]

def submit_video(uid, plan, pid_face):
    if not plans.has(plan, "premium"): return None, quality.lock("premium", "gen")
    import agentvideo
    L = agentvideo.limits(plan)
    cur = current(uid)
    if not cur or cur["status"] != "done" or not cur.get("approved"): raise ValueError("Najpierw stwórz agentkę (obraz musi przejść sprawdzenie).")
    if any(j["uid"] == uid and j["kind"] == "vid" and j["status"] in ("waiting", "generating", "checking") for j in _J().values()):
        raise ValueError("Film już się robi. Cierpliwości – dobre ujęcia lubią spokój. 🎬")
    j = {"id": secrets.token_hex(6), "uid": uid, "kind": "vid", "t": int(time.time()), "plan": plan, "secs": L["max_s"], "h": int(L["label"]),
         "face": cur["approved"][0], "prompt": cur["prompt"] + ", gentle natural movement, speaking calmly to camera", "status": "waiting", "variants": [], "picked": [], "approved": [], "note": ""}
    with _lock: J = _J(); J[j["id"]] = j; _put(J)
    _kick(j["id"]); return view(j), None

def view(j):
    if not j: return None
    u = (lambda v: f"/api/agent/gen/img/{v}.jpg") if j["kind"] == "img" else (lambda v: f"/api/agent/gen/vid/{v}.mp4")
    st = j["status"]
    step = {"waiting": 2, "generating": 2, "variants": 3, "checking": 4, "rejected": 1, "failed": 1, "done": 5}.get(st, 1)
    return {"id": j["id"], "kind": j["kind"], "status": st, "step": step, "note": j.get("note", ""), "t": j["t"],
            "variants": [{"id": v, "url": u(v)} for v in j["variants"]], "picked": j["picked"], "pid": j.get("pid"),
            "secs": j.get("secs"), "h": j.get("h"), "engine": engine_img() if j["kind"] == "img" else engine_vid(), "draft": j.get("draft")}

def state(uid):
    J = _J()
    vids = sorted([j for j in J.values() if j["uid"] == uid and j["kind"] == "vid"], key=lambda j: -j["t"])
    return {"img": view(current(uid)), "vid": view(vids[0]) if vids else None, "engine": {"img": engine_img(), "video": engine_vid()}}

def img_for(vid, viewer_uid):
    i = store.get("agimg:" + vid) or None
    if not i: return None
    if i.get("approved") or i.get("uid") == viewer_uid: return i
    return None

def mark_approved(vids):
    for v in vids:
        i = store.get("agimg:" + v)
        if i: i["approved"] = True; store.put("agimg:" + v, i)

def admin_list():
    return [dict(view(j), uid8=j["uid"][:8], prompt=j["prompt"]) for j in sorted(_J().values(), key=lambda j: -j["t"]) if j["status"] in ("checking", "waiting", "generating")][:100]

def delete_owner(uid):
    with _lock:
        J = _J()
        for k in [k for k, j in J.items() if j["uid"] == uid]:
            for v in J[k]["variants"] + J[k].get("approved", []): _drop(J[k], v)
            J.pop(k)
        _put(J)

def purge(now=None):
    """Porządki: zadania i niewybrane warianty starsze niż 30 dni są usuwane (oczekujące w kolejce też)."""
    now = now or time.time()
    with _lock:
        J = _J(); n = 0
        for k in [k for k, j in J.items() if j["status"] != "done" and now - j["t"] > SRC_TTL]:
            for v in J[k]["variants"]: _drop(J[k], v)
            J.pop(k); n += 1
        if n: _put(J)
    return n

def vid_path(v, viewer_uid):
    import agentvideo
    for j in _J().values():
        if j["kind"] == "vid" and v in j["variants"] + j.get("approved", []) and (j["uid"] == viewer_uid or v in j.get("approved", [])):
            p = os.path.join(agentvideo.VDIR, "g_" + v + ".mp4")
            return p if os.path.exists(p) else None
    return None

def tick():
    """Co minutę: zadania czekające w kolejce ruszają, gdy dostawca AI jest skonfigurowany (np. po dodaniu klucza)."""
    n = 0
    for j in list(_J().values()):
        if j["status"] == "waiting" and ((j["kind"] == "img" and engine_img()) or (j["kind"] == "vid" and engine_vid())):
            _kick(j["id"]); n += 1
    return n
