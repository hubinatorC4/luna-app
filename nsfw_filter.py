"""Automatyczny filtr nagości – DWA modele na serwerze (zdjęcia nie trafiają do nikogo z zewnątrz), CPU, ONNX.

  1. NudeNet 320n (detektor części ciała; github.com/notAI-tech/NudeNet, AGPL-3.0 – models/NUDENET_LICENSE.txt)
  2. GantMan nsfw_model MobileNetV2 224 (klasyfikator drawings/hentai/neutral/porn/sexy; MIT – models/GANTMAN_LICENSE.txt)
  + sygnał pomocniczy: udział pikseli w kolorze skóry (tylko „do moderatora”, nigdy samodzielna blokada).

Użycie: NIE wołaj tego modułu bezpośrednio z endpointów – każde zdjęcie przechodzi przez upload_gate.image(...)
(walidacja, blokada animacji/SVG, skróty odrzuconych obrazów, skan, ponowne kodowanie). Test tests/test_upload_gate.py tego pilnuje.

Zasada FAIL-CLOSED: gdy któryś model nie wczyta się albo obrazu nie da się ocenić → werdykt "error" → enforce() ODRZUCA (Blocked).
Filtr działa dla wszystkich – także właściciela, admina i moderatorów. Nie ma flagi wyłączającej.
Logujemy tylko etykiety i wyniki – nigdy obraz. Odrzucone obrazy nie są nigdzie zapisywane (najwyżej ich skrót percepcyjny)."""
import io, os, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(ROOT, "models", "nudenet_320n.onnx")
MODEL2 = os.path.join(ROOT, "models", "gantman_mobilenet2_224.onnx")
SIZE, SIZE2 = 320, 224
LABELS = ["FEMALE_GENITALIA_COVERED", "FACE_FEMALE", "BUTTOCKS_EXPOSED", "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED",
          "MALE_BREAST_EXPOSED", "ANUS_EXPOSED", "FEET_EXPOSED", "BELLY_COVERED", "FEET_COVERED", "ARMPITS_COVERED", "ARMPITS_EXPOSED",
          "FACE_MALE", "BELLY_EXPOSED", "MALE_GENITALIA_EXPOSED", "ANUS_COVERED", "FEMALE_BREAST_COVERED", "BUTTOCKS_COVERED"]
LABELS2 = ["drawings", "hentai", "neutral", "porn", "sexy"]
# Progi v2 (t479u – zaostrzone; skalibrowane na wszystkich ubranych obrazach strony, patrz tests/calibrate_nsfw.py).
# BLOCK = odrzucenie (widoki główne), REVIEW = nie publikujemy – do kolejki moderatora (widoki główne i ćwiartki).
# Na ~3 500 ubranych zdjęciach (manekiny w beżu, berety) NudeNet sam daje fałszywe wyniki do ~0,52 → samodzielna blokada od 0,55/0,60,
# niżej (od 0,40) blokada tylko gdy POTWIERDZA drugi model (dwa głosy), inaczej moderator.
BLOCK = {"FEMALE_GENITALIA_EXPOSED": 0.55, "MALE_GENITALIA_EXPOSED": 0.55, "ANUS_EXPOSED": 0.55,
         "FEMALE_BREAST_EXPOSED": 0.60, "BUTTOCKS_EXPOSED": 0.60}
EXPOSED = ("FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED", "ANUS_EXPOSED", "FEMALE_BREAST_EXPOSED", "BUTTOCKS_EXPOSED")
CORROBORATE = (0.40, 0.50)   # NudeNet ≥ 0,40 na odsłoniętej części ORAZ drugi model porn+hentai ≥ 0,50 → blokada
REVIEW = {"FEMALE_GENITALIA_EXPOSED": 0.20, "MALE_GENITALIA_EXPOSED": 0.20, "ANUS_EXPOSED": 0.20,
          "FEMALE_BREAST_EXPOSED": 0.20, "BUTTOCKS_EXPOSED": 0.25,
          "FEMALE_GENITALIA_COVERED": 0.40, "ANUS_COVERED": 0.40,      # w kroku widoczna tylko bielizna / strój kąpielowy
          "MALE_BREAST_EXPOSED": 0.55}                                  # nagi tors – zasada „w pełni ubrani”
LINGERIE_BLOCK = 0.65   # krok okryty tylko bielizną (wysoka pewność) + odsłonięty brzuch/pośladki okryte bielizną → „za odważne”
# Drugi model (głos dodatkowy): wysoka pewność „porn/hentai” → blokada; umiarkowana albo „sexy” → moderator.
BLOCK2 = {"porn": 0.80, "hentai": 0.85}
REVIEW2 = {"porn": 0.40, "hentai": 0.50, "sexy": 0.55}
SKIN_REVIEW = 0.62      # > 62% pikseli w kolorze skóry (bez twarzy z bliska – patrz _skin) → moderator
MAX_PIXELS = 25_000_000 # bomba dekompresyjna → odrzucenie
WORK = 1600             # skan na kopii ≤ 1600 px (dość dla 8 widoków 320 px, a mało RAM)

MSG = {
    "pl": "Ups, trochę za mało ubrania – Luna lubi styl, nie nagość 👗 Wybierz proszę inne zdjęcie.",
    "en": "Oops, a little too little clothing – Luna loves style, not nudity 👗 Please choose another photo.",
    "de": "Hoppla, ein bisschen zu wenig Kleidung – Luna liebt Stil, keine Nacktheit 👗 Bitte wähle ein anderes Foto.",
    "es": "Uy, demasiada poca ropa: a Luna le encanta el estilo, no el desnudo 👗 Elige otra foto, por favor.",
    "uk": "Ой, трохи замало одягу – Луна любить стиль, а не оголеність 👗 Будь ласка, оберіть інше фото.",
}
MSG_REVIEW = {
    "pl": "Dzięki! Zdjęcie trafi do szybkiej kontroli moderatora, zanim ktoś je zobaczy.",
    "en": "Thanks! The photo will get a quick moderator check before anyone can see it.",
    "de": "Danke! Das Foto wird kurz von einer Moderation geprüft, bevor es jemand sieht.",
    "es": "¡Gracias! Un moderador revisará la foto antes de que nadie la vea.",
    "uk": "Дякуємо! Модератор швидко перевірить фото, перш ніж його хтось побачить.",
}
MSG_ERROR = {
    "pl": "Filtr zdjęć jest chwilowo niedostępny, więc dla bezpieczeństwa nie przyjmujemy teraz zdjęć. Spróbuj za kilka minut. 💚",
    "en": "The photo filter is temporarily unavailable, so for safety we can't accept photos right now. Please try again in a few minutes. 💚",
    "de": "Der Fotofilter ist vorübergehend nicht verfügbar, deshalb nehmen wir gerade keine Fotos an. Bitte versuche es in ein paar Minuten erneut. 💚",
    "es": "El filtro de fotos no está disponible ahora mismo, así que por seguridad no aceptamos fotos. Inténtalo de nuevo en unos minutos. 💚",
    "uk": "Фільтр фото тимчасово недоступний, тож задля безпеки ми зараз не приймаємо фото. Спробуйте за кілька хвилин. 💚",
}

class Blocked(ValueError):
    """Zdjęcie odrzucone (nagość / zbyt odważne / filtr niedostępny). str(e) = grzeczny komunikat w języku użytkownika."""
    def __init__(self, msg, labels=None, reason=""):
        super().__init__(msg); self.labels = labels or {}; self.reason = reason

class Held(ValueError):
    """Zdjęcie wstrzymane do ręcznej moderacji (miejsca bez kolejki publikacji, np. awatar na czacie). str(e) = uprzejmy komunikat."""

_sess, _sess2, _lock, _err = None, None, threading.Lock(), ""
_busy = threading.BoundedSemaphore(1)    # 1 skan naraz (RAM na darmowym Renderze) – zalew zdjęciami nie zatka serwera (reszta czeka)
_tl = threading.local()
def set_lang(lang): _tl.lang = (lang or "pl")[:2]; _tl.last = None
def last():
    """Werdykt ostatniego enforce() w tym wątku: "ok" | "review" | "block" | None."""
    return getattr(_tl, "last", None)

def _load(path):
    import onnxruntime as ort
    so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1; so.enable_cpu_mem_arena = False
    return ort.InferenceSession(path, sess_options=so, providers=["CPUExecutionProvider"])

def _sessions():
    """Leniwe wczytanie obu modeli (1 wątek, bez areny pamięci – mało RAM na darmowym Renderze). Brak któregokolwiek = (None, None)."""
    global _sess, _sess2, _err
    if _sess is not None and _sess2 is not None: return _sess, _sess2
    with _lock:
        try:
            if _sess is None: _sess = _load(MODEL)
            if _sess2 is None: _sess2 = _load(MODEL2)
        except Exception as e:
            _err = type(e).__name__ + ": " + str(e)[:120]; return None, None
    return _sess, _sess2

def available():
    return all(_sessions())

def status():
    """Do /api/health i panelu admina: czy oba modele działają (bez szczegółów technicznych dla gości)."""
    return {"nudenet": _sess is not None, "second_model": _sess2 is not None, "ok": available()}

# ---------- piksele ----------
def _open(raw):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    im = Image.open(io.BytesIO(raw))
    if im.width * im.height > MAX_PIXELS: raise ValueError("too big")
    if im.format == "JPEG": im.draft("RGB", (WORK, WORK))   # JPEG dekodowany od razu w mniejszej skali
    return im

def _rgb(im):
    from PIL import Image
    if im.mode in ("RGBA", "LA", "P"):   # przezroczystość → na czarnym tle (jak NudeNet) – ukryta treść w kanale alfa nie znika
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (0, 0, 0)); bg.paste(im, mask=im.split()[-1]); return bg
    return im.convert("RGB")

def _square(im, s):
    """Dopełnienie do kwadratu czarnym tłem (lewy-górny róg, jak w NudeNet) i skalowanie do s×s."""
    from PIL import Image
    m = max(im.size); c = Image.new("RGB", (m, m), (0, 0, 0)); c.paste(im, (0, 0))
    return c.resize((s, s), Image.BILINEAR)

def views(im):
    """Widoki 320×320: cały obraz, środek, lewa/górna, prawa/dolna część oraz 4 ćwiartki (mała postać na dużym zdjęciu też jest widoczna)."""
    w, h = im.size; m = min(w, h)
    crops = [None, ((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m), (0, 0, m, m), (w - m, h - m, w, h)]
    if min(w, h) >= 256:   # ćwiartki tylko gdy jest co ciąć (miniatury awatarów – wystarczą widoki główne)
        crops += [(0, 0, w // 2, h // 2), (w // 2, 0, w, h // 2), (0, h // 2, w // 2, h), (w // 2, h // 2, w, h)]
    out = []
    for c in crops: out.append(_square(im if c is None else im.crop(c), SIZE))
    return out

def _skin(im):
    """Udział pikseli w kolorze skóry (reguła YCbCr, Chai & Ngan) na obrazie 96×96 z pominięciem środkowej-górnej części (twarz z bliska)."""
    import numpy as np
    a = np.asarray(im.resize((96, 96)).convert("YCbCr"), dtype=np.int16)
    cb, cr = a[..., 1], a[..., 2]
    sk = (cb >= 77) & (cb <= 127) & (cr >= 133) & (cr <= 173) & (a[..., 0] > 40)
    sk[0:40, 24:72] = False   # górny środek (zwykle twarz/szyja na portrecie) nie liczy się do „gołej skóry”
    return round(float(sk.sum()) / (96 * 96 - 40 * 48), 3)

def scores(raw=None, im=None):
    """Najwyższe wyniki etykiet obu modeli + udział skóry. Rzuca wyjątek, gdy model/obraz niedostępny (→ fail-closed)."""
    import numpy as np
    s1, s2 = _sessions()
    if s1 is None or s2 is None: raise RuntimeError("model unavailable: " + _err)
    if im is None: im = _open(raw); im.load()
    im = _rgb(im)
    if max(im.size) > WORK: im.thumbnail((WORK, WORK))
    best = [None, None]; n1 = s1.get_inputs()[0].name
    for i, v in enumerate(views(im)):   # pojedynczo = mniej RAM; widoki 0–3 = główne, 4–7 = ćwiartki
        x = np.ascontiguousarray((np.asarray(v, dtype=np.float32) / 255.0).transpose(2, 0, 1)[None])
        mx = s1.run(None, {n1: x})[0][0, 4:, :].max(axis=1); g = 0 if i < 4 else 1
        best[g] = mx if best[g] is None else np.maximum(best[g], mx)
    sc = {LABELS[i]: round(float(best[0][i]), 3) for i in range(len(LABELS))}
    if best[1] is not None:   # ćwiartki: tylko sygnał „do moderatora” (powiększony fragment częściej myli beżowy materiał ze skórą)
        sc.update({"t_" + LABELS[i]: round(float(best[1][i]), 3) for i in range(len(LABELS)) if LABELS[i] in REVIEW})
    from PIL import Image
    w, h = im.size; m = min(w, h); n2 = s2.get_inputs()[0].name; b2 = None
    for v in (im.resize((SIZE2, SIZE2), Image.BILINEAR), im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m)).resize((SIZE2, SIZE2), Image.BILINEAR)):
        p = s2.run(None, {n2: (np.asarray(v, dtype=np.float32) / 255.0)[None]})[0][0]
        b2 = p if b2 is None else np.maximum(b2, p)
    sc.update({"m2_" + LABELS2[i]: round(float(b2[i]), 3) for i in range(len(LABELS2))})
    sc["skin"] = _skin(im)
    return sc

def decide(sc):
    """(werdykt, powód) z wyników – czysta funkcja (testowana bez modeli)."""
    for k, t in BLOCK.items():
        if sc.get(k, 0) >= t: return "block", k
    for k, t in BLOCK2.items():
        if sc.get("m2_" + k, 0) >= t: return "block", "M2_" + k.upper()
    m2 = sc.get("m2_porn", 0) + sc.get("m2_hentai", 0)
    for k in EXPOSED:
        if sc.get(k, 0) >= CORROBORATE[0] and m2 >= CORROBORATE[1]: return "block", "TWO_VOTES_" + k
    g = sc.get("FEMALE_GENITALIA_COVERED", 0)
    if g >= LINGERIE_BLOCK and (sc.get("BELLY_EXPOSED", 0) >= 0.5 or sc.get("BUTTOCKS_COVERED", 0) >= 0.5): return "block", "LINGERIE_LEVEL"
    for k, t in REVIEW.items():
        if max(sc.get(k, 0), sc.get("t_" + k, 0)) >= t: return "review", k
    for k, t in REVIEW2.items():
        if sc.get("m2_" + k, 0) >= t: return "review", "M2_" + k.upper()
    if sc.get("BUTTOCKS_COVERED", 0) >= 0.5 and sc.get("BELLY_EXPOSED", 0) >= 0.4: return "review", "REVEALING"
    if sc.get("FEMALE_BREAST_COVERED", 0) >= 0.55 and sc.get("BELLY_EXPOSED", 0) >= 0.5: return "review", "SWIM_OR_LINGERIE"
    if sc.get("BELLY_EXPOSED", 0) >= 0.6 and sc.get("BELLY_COVERED", 0) < 0.3: return "review", "REVEALING_BELLY"
    if sc.get("skin", 0) >= SKIN_REVIEW: return "review", "SKIN_RATIO"
    return "ok", ""

def classify(raw, im=None):
    """(werdykt, powód, wyniki). Werdykt: ok | review | block | error (błąd/model niedostępny – endpointy traktują jak blokadę)."""
    with _busy:
        try: sc = scores(raw, im)
        except Exception as e: return "error", "unavailable:" + type(e).__name__, {}
    v, why = decide(sc)
    return v, why, sc

def frames(raw, n=24):
    """Klatki do skanu: obraz statyczny = 1; GIF/WebP/APNG animowany = do n klatek rozłożonych równo (każda skanowana)."""
    im = _open(raw); cnt = int(getattr(im, "n_frames", 1) or 1)
    if cnt <= 1: im.load(); return [im.copy()]
    idx = list(range(cnt)) if cnt <= n else sorted({round(i * (cnt - 1) / (n - 1)) for i in range(n)}); out = []
    for i in idx: im.seek(i); out.append(im.convert("RGBA").copy())
    return out

def classify_all(raw):
    """Jak classify, ale skanuje każdą próbkę klatek (animacje). Najgorszy werdykt wygrywa."""
    try: fr = frames(raw)
    except Exception as e: return "error", "decode:" + type(e).__name__, {}
    rank = {"ok": 0, "review": 1, "block": 2, "error": 3}; worst = ("ok", "", {})
    for f in fr:
        r = classify(None, f)
        if rank[r[0]] > rank[worst[0]]: worst = r
        if worst[0] in ("block", "error"): break
    return worst

def _log(ctx, verdict, reason, sc, ms):
    top = {k: v for k, v in sorted(sc.items(), key=lambda x: -x[1]) if v >= 0.2 and not k.startswith(("FACE_", "FEET_", "m2_neutral", "m2_drawings"))}
    try: sys.stderr.write("nsfw ctx=%s verdict=%s reason=%s ms=%d labels=%s\n" % (str(ctx)[:20], verdict, reason, ms, top))
    except Exception: pass

def enforce(raw, ctx="upload", lang=None):
    """Zwraca "ok" albo "review"; przy blokadzie LUB błędzie filtra rzuca Blocked (ValueError) z komunikatem w języku `lang`.
    Werdykt "review" = NIE publikuj automatycznie, tylko do kolejki moderatora."""
    lang = lang or getattr(_tl, "lang", "pl")
    t0 = time.time(); v, why, sc = classify_all(raw)
    _log(ctx, v, why, sc, (time.time() - t0) * 1000)
    _tl.last = "block" if v in ("block", "error") else v
    if v == "block": raise Blocked(message(lang), sc, why)
    if v == "error": raise Blocked(MSG_ERROR.get(lang[:2], MSG_ERROR["pl"]), {}, why)
    return v

def check_dataurl(data_url, ctx="upload", lang=None):
    """data:image/...;base64,... → ok/review; zły format = Blocked (fail-closed)."""
    import base64, re
    m = re.fullmatch(r"data:image/[\w.+-]+;base64,(.+)", str(data_url or ""), re.S)
    try: raw = base64.b64decode(m.group(1), validate=True) if m else b""
    except Exception: raw = b""
    if not raw: raise Blocked(message(lang), {}, "bad_dataurl")
    return enforce(raw, ctx, lang)

def message(lang=None): lang = lang or getattr(_tl, "lang", "pl"); return MSG.get(lang[:2], MSG["pl"])
def review_message(lang=None): lang = lang or getattr(_tl, "lang", "pl"); return MSG_REVIEW.get(lang[:2], MSG_REVIEW["pl"])

def selftest():
    """Rozgrzewka przy starcie: wczytuje modele i ocenia syntetyczny, neutralny obraz (gradient). True = filtr gotowy."""
    try:
        from PIL import Image
        im = Image.linear_gradient("L").convert("RGB").resize((320, 240))
        v, why, _ = classify(None, im)
        return v != "error"
    except Exception: return False
