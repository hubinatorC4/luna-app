# -*- coding: utf-8 -*-
"""Generator filmów agentki – egzekwowane na serwerze.
Agentka może występować TYLKO sama (jej ujęcia AI: stroje/pozy z planu + jej własny wygenerowany obraz) – bez dowolnych mediów innych osób.
Podstawowa: brak.  Premium: do 30 s, 720p (720x1280).  Pro / Ultra: do 60 s, 1080p (1080x1920).  Twardy limit 60 s.
Kolejka zadań w tle; postęp w dymku; gotowy film trafia do listy „Moje filmy” (i do Skrzynki, gdy moduł inbox jest dostępny).
Silnik: gdy skonfigurowano model wideo (LUNA_VIDEO_API_URL + LUNA_VIDEO_API_KEY) – klipy 6–10 s łączone przejściami (xfade);
bez niego – lokalny silnik ffmpeg: płynne najazdy kamery (zoompan) na ujęcia AI agentki, łączone przejściami. Zawsze widoczny znak „AI”."""
import json, os, secrets, subprocess, tempfile, threading, time, queue
import store, plans, imgsafe, profiles, quality

ROOT = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(ROOT, "data", "videos")
HARD_MAX_S = 60
CLIP_S = 8          # długość jednego klipu (modele wideo generują ok. 6–10 s)
XF = 1.0            # długość przejścia
def _envint(k, d):
    try: return int(os.getenv(k, d))
    except ValueError: return d
LIMITS = {"premium": {"max_s": 30, "h": 1280, "w": 720, "label": "720", "day": _envint("LUNA_VID_DAY_PREMIUM", 5), "month": _envint("LUNA_VID_MONTH_PREMIUM", 60)},
          "pro": {"max_s": 60, "h": 1920, "w": 1080, "label": "1080", "day": _envint("LUNA_VID_DAY_PRO", 15), "month": _envint("LUNA_VID_MONTH_PRO", 200)}}
import battle_categories as BC   # wspólne ID scenerii z Bitwami (worker Bitew)
SCENE_NAMES = {
    "city": {"pl": "Nocne miasto", "en": "Night city", "es": "Ciudad nocturna", "de": "Nachtstadt", "uk": "Нічне місто"},
    "studio": {"pl": "Scena studia", "en": "Studio stage", "es": "Plató", "de": "Studiobühne", "uk": "Студійна сцена"},
    "promenade": {"pl": "Nadmorska promenada", "en": "Seaside promenade", "es": "Paseo marítimo", "de": "Strandpromenade", "uk": "Набережна"},
    "winter": {"pl": "Zimowy las", "en": "Winter forest", "es": "Bosque nevado", "de": "Winterwald", "uk": "Зимовий ліс"},
    "gala": {"pl": "Sala balowa", "en": "Gala hall", "es": "Salón de gala", "de": "Gala-Saal", "uk": "Бальна зала"},
    "garden": {"pl": "Ogród", "en": "Garden", "es": "Jardín", "de": "Garten", "uk": "Сад"},
    "gym": {"pl": "Siłownia", "en": "Gym", "es": "Gimnasio", "de": "Fitnessstudio", "uk": "Спортзал"},
    "office": {"pl": "Biuro", "en": "Office", "es": "Oficina", "de": "Büro", "uk": "Офіс"},
    "beach": {"pl": "Plaża", "en": "Beach", "es": "Playa", "de": "Strand", "uk": "Пляж"},
}
CUSTOM_LEN = 120

def allowed_scenes(plan):
    import battles
    if plans.has(plan, "pro"): return BC.available_scenes() or list(BC.SCENES)
    if plans.has(plan, "premium"): return battles.basic_scenes()
    return []

def scene_check(plan, scene=None, custom=None):
    """None gdy wolno, inaczej (need, komunikat) do 402. Premium: 6 podstawowych z rankingu Bitew; Pro / Ultra: wszystkie + własny opis."""
    if not plans.has(plan, "premium"): return "premium", "🔒 Generator agentek od Premium · od 59,99 zł"
    if custom:
        return None if plans.has(plan, "pro") else ("pro", "Własny opis scenerii jest w planie Pro / Ultra.")
    if scene not in BC.SCENES: return "pro", "Nieznana sceneria."
    if scene not in allowed_scenes(plan): return "pro", "Ta sceneria jest w planie Pro / Ultra. Premium ma zestaw podstawowy (6 najpopularniejszych)."
    return None

def clean_custom(text):
    """Własny opis scenerii (Pro / Ultra): tylko miejsce/światło/nastrój – filtr słów + moderacja ręczna przed renderem."""
    import re, social
    t = social.check_text(str(text or "").strip(), CUSTOM_LEN)
    bad = re.compile(r"\b(nag|naked|nude|sex|seks|bikini|bielizn|lingerie|dzieck|child|kid|celebryt|celebrity|logo|nike|adidas|gucci|chanel|coca|apple)\w*", re.I)
    if bad.search(t): raise ValueError("Opis scenerii może dotyczyć tylko miejsca, światła i nastroju – bez osób, marek i treści erotycznych.")
    return t

def scenes_public(lang, plan):
    import battles
    al = set(allowed_scenes(plan)); basic = set(battles.basic_scenes())
    return [{"id": k, "title": SCENE_NAMES.get(k, {}).get(lang) or SCENE_NAMES.get(k, {}).get("pl", k), "basic": k in basic, "ok": k in al}
            for k in (BC.available_scenes() or BC.SCENES)]
KEEP_DAYS = 14

def engine():
    return "model" if os.getenv("LUNA_VIDEO_API_URL") and os.getenv("LUNA_VIDEO_API_KEY") else "local"

def limits(plan):
    return dict(LIMITS["pro" if plan == "pro" else "premium"]) if plans.has(plan, "premium") else None

def _J(): return store.get("video_jobs", {}) or {}
_lock = threading.Lock(); _q = queue.Queue(); _started = [False]

def _count(uid, since):
    return sum(1 for j in _J().values() if j["uid"] == uid and j["t"] >= since and j["status"] != "failed")

def submit(uid, plan, d):
    L = limits(plan)
    if not L: return None, quality.lock("premium", "gen")
    try: secs = int(d.get("seconds") or 10)
    except (TypeError, ValueError): raise ValueError("Podaj długość filmu w sekundach.")
    if secs < 6: raise ValueError("Najkrótszy film ma 6 s.")
    if secs > HARD_MAX_S: raise ValueError("Film może mieć maksymalnie 60 s.")
    if secs > L["max_s"]: return None, dict(quality.lock("pro"), message=f"Filmy dłuższe niż {L['max_s']} s są w planie {plans.NAMES['pro']} (do 60 s).")
    q = str(d.get("quality") or L["label"])
    if q == "1080" and L["label"] != "1080": return None, quality.lock("pro")
    pid, r = profiles.mine(uid)
    if not r: raise ValueError("Najpierw utwórz profil agentki (Moje agentki).")
    shots = [s for s in (d.get("shots") or []) if s in profiles.LUNA_PHOTOS and plans.has(plan, profiles.LUNA_PHOTOS[s])][:8]
    if not shots: shots = [s for s, need in profiles.LUNA_PHOTOS.items() if plans.has(plan, need)][:4]
    custom = str(d.get("custom") or "").strip()
    scene = str(d.get("scene") or "studio")
    bad = scene_check(plan, None if custom else scene, custom or None)
    if bad: return None, dict(quality.lock(bad[0]), message=bad[1])
    if custom: custom = clean_custom(custom)
    if d.get("battle") is True:
        import battles
        if not battles.my_entry(uid): raise ValueError("Twoja agentka nie bierze udziału w Bitwie.")
    now = time.time(); day0 = now - now % 86400; mon0 = time.mktime(time.strptime(time.strftime("%Y-%m-01", time.gmtime()), "%Y-%m-%d"))
    with _lock:
        if _count(uid, day0) >= L["day"]: raise PermissionError(f"Dzisiejszy limit filmów ({L['day']}) został wykorzystany.")
        if _count(uid, mon0) >= L["month"]: raise PermissionError(f"Miesięczny limit filmów ({L['month']}) został wykorzystany.")
        if any(j["uid"] == uid and j["status"] in ("queued", "running", "review") for j in _J().values()): raise PermissionError("Poczekaj, aż skończy się poprzedni film.")
        jid = secrets.token_hex(6)
        J = _J(); J[jid] = {"id": jid, "uid": uid, "pid": pid, "plan": plan, "secs": secs, "w": L["w"], "h": L["h"], "q": L["label"], "shots": shots,
                            "own": r.get("own", ""), "scene": None if custom else scene, "custom": custom, "battle": d.get("battle") is True,
                            "status": "review" if custom else "queued", "progress": 0, "t": int(now),
                            "engine": engine(), "ai": True, "mod": "pending" if custom else "auto"}
        store.put("video_jobs", dict(sorted(J.items(), key=lambda kv: -kv[1]["t"])[:500]))
    _ensure_worker()
    if not custom: _q.put(jid)
    return {"id": jid, "status": "review" if custom else "queued", "secs": secs, "q": L["label"], "engine": engine()}, None

def _upd(jid, **kw):
    with _lock:
        J = _J(); j = J.get(jid)
        if j: j.update(kw); store.put("video_jobs", J)
        return j

def _sources(j):
    srcs = []
    for s in j["shots"]:
        p = os.path.join(ROOT, "static", "catalog", "luna", s + "@2x.jpg")
        if not os.path.exists(p): p = p.replace("@2x", "")
        if os.path.exists(p): srcs.append(p)
    return srcs

def _render_local(j, tmp):
    """Klipy CLIP_S s z płynnym najazdem kamery na ujęcia AI agentki → xfade → znak AI → H.264."""
    ff = imgsafe._ff(); W, H = j["w"], j["h"]; fps = 30
    srcs = _sources(j)
    if not srcs: raise ValueError("Brak ujęć agentki.")
    n = max(1, round((j["secs"] - XF) / (CLIP_S - XF)))
    clip = (j["secs"] + (n - 1) * XF) / n
    clips = []
    for i in range(n):
        src = srcs[i % len(srcs)]; out = os.path.join(tmp, f"c{i}.mp4"); fr = int(clip * fps)
        zin = i % 2 == 0
        z = f"'min(1.0+0.12*on/{fr},1.12)'" if zin else f"'max(1.12-0.12*on/{fr},1.0)'"
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z={z}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps={fps},format=yuv420p")
        r = subprocess.run([ff, "-v", "error", "-y", "-loop", "1", "-i", src, "-vf", vf, "-t", f"{clip:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out],
                           capture_output=True, timeout=600)
        if r.returncode: raise ValueError("render: " + r.stderr.decode()[-200:])
        clips.append(out); _upd(j["id"], progress=int(70 * (i + 1) / n))
    label = os.path.join(ROOT, "static", "ai-label-1080.png" if H >= 1920 else "ai-label-720.png")
    inp = sum([["-i", c] for c in clips], []) + ["-i", label]
    if n == 1: fc = "[0:v]null[v]"
    else:
        fc, last, off = "", "[0:v]", 0.0
        for i in range(1, n):
            off += clip - XF; tag = f"[x{i}]"
            fc += f"{last}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.2f}{tag};"; last = tag
        fc += f"{last}null[v]"
    fc += f";[v][{n}:v]overlay=W-w-{W//27}:{H//40},format=yuv420p[o]"
    out = os.path.join(tmp, "final.mp4")
    br = "8M" if H >= 1920 else "4M"
    r = subprocess.run([ff, "-v", "error", "-y", *inp, "-filter_complex", fc, "-map", "[o]", "-t", str(min(j["secs"], HARD_MAX_S)),
                        "-c:v", "libx264", "-profile:v", "high", "-preset", "veryfast", "-b:v", br, "-maxrate", br, "-bufsize", "16M",
                        "-movflags", "+faststart", "-map_metadata", "-1", out], capture_output=True, timeout=900)
    if r.returncode: raise ValueError("concat: " + r.stderr.decode()[-200:])
    return out

def _poster(ff, mp4, dst):
    subprocess.run([ff, "-v", "error", "-y", "-ss", "1", "-i", mp4, "-frames:v", "1", "-q:v", "2", dst], capture_output=True, timeout=60)

def _work():
    while True:
        jid = _q.get()
        j = _J().get(jid)
        if not j or j["status"] != "queued": continue
        _upd(jid, status="running", progress=1)
        try:
            os.makedirs(VDIR, exist_ok=True)
            with tempfile.TemporaryDirectory() as tmp:
                if j["engine"] == "model": raise ValueError("Model wideo nie jest jeszcze podłączony – użyto silnika lokalnego.")
                out = _render_local(j, tmp)
                dst = os.path.join(VDIR, jid + ".mp4"); os.replace(out, dst)
                _poster(imgsafe._ff(), dst, os.path.join(VDIR, jid + ".jpg"))
            _upd(jid, status="ready", progress=100, done=int(time.time()), size=os.path.getsize(dst))
            _notify_ready(_J().get(jid))
        except Exception as e:
            _upd(jid, status="failed", error=str(e)[:200])

READY_T = {"pl": ("🎬 Film Twojej agentki jest gotowy", "{s} s · {q}p · ze znakiem „AI”. Popcorn opcjonalny – film czeka w Mój panel → Generator agentek."),
           "en": ("🎬 Your agent’s video is ready", "{s} s · {q}p · with the “AI” label. Popcorn optional – it’s waiting in My panel → Agent generator."),
           "es": ("🎬 El vídeo de tu agente está listo", "{s} s · {q}p · con la marca «AI». Palomitas opcionales: te espera en Mi panel → Generador de agentes."),
           "de": ("🎬 Das Video deiner Agentin ist fertig", "{s} s · {q}p · mit „AI“-Zeichen. Popcorn optional – es wartet unter Mein Bereich → Agentinnen-Generator."),
           "uk": ("🎬 Відео вашої агентки готове", "{s} с · {q}p · з позначкою «AI». Попкорн за бажанням – відео чекає в Моя панель → Генератор агенток.")}
def _notify_ready(j):
    """Gotowy film → wiadomość w Skrzynce (kategoria Ważne, tłumaczona przy odczycie) + push, jeśli włączony."""
    try:
        import inbox
        ti = {l: v[0] for l, v in READY_T.items()}; bo = {l: v[1].format(s=j["secs"], q=j["q"]) for l, v in READY_T.items()}
        inbox.deliver(j["uid"], "important", title=ti, body=bo, link="/ustawienia.html#gen", dedupe="vid:" + j["id"])
    except Exception as e:
        import sys; sys.stderr.write("video inbox %s\n" % type(e).__name__)

def _ensure_worker():
    if not _started[0]:
        _started[0] = True; threading.Thread(target=_work, daemon=True).start()
        for jid, j in _J().items():  # wznowienie po restarcie
            if j["status"] in ("queued", "running"): _upd(jid, status="queued"); _q.put(jid)

def admin_list():
    return [{k: j.get(k) for k in ("id", "status", "secs", "q", "t", "custom", "scene", "battle", "error")} | {"u": j["uid"][:8]}
            for j in sorted(_J().values(), key=lambda x: (x["status"] != "review", -x["t"]))][:100]

def admin_action(jid, action):
    j = _J().get(jid)
    if not j: raise ValueError("Nie ma takiego zadania.")
    if action == "approve" and j["status"] == "review": _upd(jid, status="queued", mod="approved"); _ensure_worker(); _q.put(jid)
    elif action == "reject" and j["status"] == "review": _upd(jid, status="failed", mod="rejected", error="Opis scenerii odrzucony przez moderację.")
    elif action == "remove":
        with _lock:
            J = _J(); J.pop(jid, None); store.put("video_jobs", J)
        for e in ("mp4", "jpg"):
            try: os.remove(os.path.join(VDIR, jid + "." + e))
            except OSError: pass
    else: raise ValueError("bad action")

def mine(uid):
    return [{k: j.get(k) for k in ("id", "status", "progress", "secs", "q", "t", "error", "battle", "engine", "scene", "custom")} |
            ({"url": f"/api/agent/video/{j['id']}.mp4", "poster": f"/api/agent/video/{j['id']}.jpg"} if j["status"] == "ready" else {})
            for j in sorted(_J().values(), key=lambda x: -x["t"]) if j["uid"] == uid][:30]

def file_for(jid, ext, viewer_uid, viewer_plan):
    j = _J().get(jid)
    if not j or j["status"] != "ready": return None, None
    if j["uid"] != viewer_uid and not j.get("public"): return None, None
    if ext == "mp4" and j["uid"] != viewer_uid:
        err = quality.check_video(viewer_plan, int(j["q"]))
        if err: return None, err
    p = os.path.join(VDIR, jid + "." + ext)
    return (p if os.path.exists(p) else None), None

def delete(uid, jid):
    with _lock:
        J = _J(); j = J.get(jid)
        if not j or j["uid"] != uid: raise PermissionError("To nie Twój film.")
        J.pop(jid); store.put("video_jobs", J)
    for e in ("mp4", "jpg"):
        try: os.remove(os.path.join(VDIR, jid + "." + e))
        except OSError: pass

def delete_owner(uid):
    for j in [j for j in _J().values() if j["uid"] == uid]:
        try: delete(uid, j["id"])
        except Exception: pass
