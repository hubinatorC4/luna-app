"""Automatyczny filtr zbyt odważnych zdjęć (NudeNet 320n, ONNX, CPU, na serwerze – zdjęcia nie trafiają do nikogo z zewnątrz).

Użycie we WSZYSTKICH miejscach przyjmowania zdjęć od użytkowników:
    import nsfw_filter
    verdict = nsfw_filter.enforce(raw_bytes, "wall", lang)   # "ok" | "review"; przy jawnej nagości rzuca nsfw_filter.Blocked
    if verdict == "review": ...  # NIE publikuj automatycznie – do kolejki moderatora
nsfw_filter.Blocked dziedziczy po ValueError, więc istniejące `except ValueError as e: 400 + str(e)` od razu zwraca grzeczny komunikat.

Zasada FAIL-CLOSED: gdy modelu nie da się wczytać lub obraz nie da się ocenić → "review" (ręczna moderacja), nigdy "ok".
Logujemy tylko etykiety i wyniki – nigdy obraz. Odrzucone obrazy nie są nigdzie zapisywane.
Model: NudeNet 320n (github.com/notAI-tech/NudeNet, licencja AGPL-3.0 – patrz models/NUDENET_LICENSE.txt; kod tej aplikacji jest publiczny)."""
import os, subprocess, sys, tempfile, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(ROOT, "models", "nudenet_320n.onnx")
SIZE = 320
LABELS = ["FEMALE_GENITALIA_COVERED", "FACE_FEMALE", "BUTTOCKS_EXPOSED", "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED",
          "MALE_BREAST_EXPOSED", "ANUS_EXPOSED", "FEET_EXPOSED", "BELLY_COVERED", "FEET_COVERED", "ARMPITS_COVERED", "ARMPITS_EXPOSED",
          "FACE_MALE", "BELLY_EXPOSED", "MALE_GENITALIA_EXPOSED", "ANUS_COVERED", "FEMALE_BREAST_COVERED", "BUTTOCKS_COVERED"]
# Progi (strojone na bezpiecznych zdjęciach i publicznych próbkach testowych). BLOCK = odrzucenie, REVIEW = do moderatora.
# Na 600 zdjęciach ubrań (manekiny) wyniki fałszywe sięgały 0,52 → odrzucamy od 0,60, a 0,30–0,60 idzie do moderatora.
BLOCK = {"FEMALE_GENITALIA_EXPOSED": 0.55, "MALE_GENITALIA_EXPOSED": 0.55, "ANUS_EXPOSED": 0.55,
         "FEMALE_BREAST_EXPOSED": 0.60, "BUTTOCKS_EXPOSED": 0.60}
REVIEW = {"FEMALE_GENITALIA_EXPOSED": 0.30, "MALE_GENITALIA_EXPOSED": 0.30, "ANUS_EXPOSED": 0.30,
          "FEMALE_BREAST_EXPOSED": 0.30, "BUTTOCKS_EXPOSED": 0.30,
          "FEMALE_GENITALIA_COVERED": 0.45, "ANUS_COVERED": 0.45}   # widoczna tylko bielizna/strój kąpielowy w kroku
LINGERIE_BLOCK = 0.70   # krok okryty tylko bielizną (wysoka pewność) + odsłonięty brzuch/pośladki okryte bielizną → „za odważne”

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

class Blocked(ValueError):
    """Zdjęcie odrzucone (jawna nagość / zbyt odważne). str(e) = grzeczny komunikat w języku użytkownika."""
    def __init__(self, msg, labels=None):
        super().__init__(msg); self.labels = labels or {}

_sess, _lock, _err = None, threading.Lock(), ""
_tl = threading.local()   # język bieżącego żądania i ostatni werdykt (na wątek obsługi żądania)
def set_lang(lang): _tl.lang = (lang or "pl")[:2]; _tl.last = None
def last():
    """Werdykt ostatniego enforce() w tym wątku: "ok" | "review" | None. Dla miejsc, które nie zwracają werdyktu wprost."""
    return getattr(_tl, "last", None)
def _session():
    """Leniwe wczytanie (dopiero przy pierwszym zdjęciu), 1 wątek – mało RAM na darmowym Renderze."""
    global _sess, _err
    if _sess is not None: return _sess
    with _lock:
        if _sess is None:
            try:
                import onnxruntime as ort
                so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
                so.enable_cpu_mem_arena = False
                _sess = ort.InferenceSession(MODEL, sess_options=so, providers=["CPUExecutionProvider"])
            except Exception as e:
                _err = type(e).__name__ + ": " + str(e)[:120]; return None
    return _sess

def available():
    return _session() is not None

VIEWS = {"full": "pad='max(iw,ih)':'max(iw,ih)':0:0:black",          # cały obraz (jak w NudeNet)
         "center": "crop='min(iw,ih)':'min(iw,ih)'",                   # środek – mała postać na szerokim zdjęciu
         "a": "crop='min(iw,ih)':'min(iw,ih)':0:0",                    # lewa/górna część
         "b": "crop='min(iw,ih)':'min(iw,ih)':'iw-min(iw,ih)':'ih-min(iw,ih)'"}  # prawa/dolna część
def _pixels(raw):
    """Jedno wywołanie ffmpeg → 4 widoki 320×320 RGB (cały obraz z dopełnieniem jak w NudeNet, środek, lewa/górna, prawa/dolna część),
    złożone w jedną klatkę i pocięte w numpy. Nic nie jest zapisywane poza katalogiem tymczasowym (usuwanym od razu)."""
    import numpy as np, imgsafe
    names = list(VIEWS)
    fc = "[0:v]format=rgb24,split=4" + "".join(f"[i{k}]" for k in range(4)) + ";" + ";".join(
        f"[i{k}]{VIEWS[n]},scale={SIZE}:{SIZE}[o{k}]" for k, n in enumerate(names)) + ";" + "".join(f"[o{k}]" for k in range(4)) + "vstack=4[out]"
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in"); open(src, "wb").write(raw)
        r = subprocess.run([imgsafe._ff(), "-v", "error", "-i", src, "-frames:v", "1", "-filter_complex", fc, "-map", "[out]",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=25)
    if r.returncode or len(r.stdout) != 4 * SIZE * SIZE * 3: raise ValueError("decode")
    a = np.frombuffer(r.stdout, dtype=np.uint8).reshape(4, SIZE, SIZE, 3).astype(np.float32) / 255.0
    return np.ascontiguousarray(a.transpose(0, 3, 1, 2))

def scores(raw):
    """Najwyższy wynik każdej etykiety w obrazie (0–1). Rzuca wyjątek, gdy model/obraz niedostępny."""
    import numpy as np
    s = _session()
    if s is None: raise RuntimeError("model unavailable: " + _err)
    x = _pixels(raw); best = None
    for i in range(x.shape[0]):   # 4 widoki – postać nie „ginie” na szerokim zdjęciu; pojedynczo = mniej RAM
        out = s.run(None, {s.get_inputs()[0].name: x[i:i + 1]})[0]
        mx = out[0, 4:, :].max(axis=1)   # [18] najwyższy wynik każdej klasy
        best = mx if best is None else np.maximum(best, mx)
    return {LABELS[i]: round(float(best[i]), 3) for i in range(len(LABELS))}

def classify(raw):
    """Zwraca (werdykt, powód, etykiety). Werdykt: ok | review | block. Fail-closed → review."""
    try: sc = scores(raw)
    except Exception as e:
        return "review", "unavailable:" + type(e).__name__, {}
    for k, t in BLOCK.items():
        if sc.get(k, 0) >= t: return "block", k, sc
    g = sc.get("FEMALE_GENITALIA_COVERED", 0)
    if g >= LINGERIE_BLOCK and (sc.get("BELLY_EXPOSED", 0) >= 0.5 or sc.get("BUTTOCKS_COVERED", 0) >= 0.5):
        return "block", "LINGERIE_LEVEL", sc
    for k, t in REVIEW.items():
        if sc.get(k, 0) >= t: return "review", k, sc
    if sc.get("BUTTOCKS_COVERED", 0) >= 0.6 and sc.get("BELLY_EXPOSED", 0) >= 0.5: return "review", "REVEALING", sc
    if sc.get("FEMALE_BREAST_COVERED", 0) >= 0.6 and sc.get("BELLY_EXPOSED", 0) >= 0.6: return "review", "SWIM_OR_LINGERIE", sc
    if sc.get("BELLY_EXPOSED", 0) >= 0.7 and sc.get("BELLY_COVERED", 0) < 0.3: return "review", "REVEALING_BELLY", sc
    return "ok", "", sc

def _log(ctx, verdict, reason, sc, ms):
    top = {k: v for k, v in sorted(sc.items(), key=lambda x: -x[1]) if v >= 0.2 and not k.startswith(("FACE_", "FEET_"))}
    try: sys.stderr.write("nsfw ctx=%s verdict=%s reason=%s ms=%d labels=%s\n" % (str(ctx)[:20], verdict, reason, ms, top))
    except Exception: pass

def enforce(raw, ctx="upload", lang=None):
    """Główna funkcja dla endpointów. Zwraca "ok" albo "review"; przy odrzuceniu rzuca Blocked (ValueError) z komunikatem w języku `lang`
    (domyślnie język bieżącego żądania). Werdykt "review" = NIE publikuj automatycznie, tylko do kolejki moderatora."""
    lang = lang or getattr(_tl, "lang", "pl")
    t0 = time.time(); v, why, sc = classify(raw)
    _log(ctx, v, why, sc, (time.time() - t0) * 1000)
    _tl.last = "block" if v == "block" else v
    if v == "block": raise Blocked(message(lang), sc)
    return v

def check_dataurl(data_url, ctx="upload", lang=None):
    """To samo dla data:image/...;base64,... (zwraca ok/review, rzuca Blocked)."""
    import base64, re
    m = re.fullmatch(r"data:image/[\w.+-]+;base64,(.+)", str(data_url or ""), re.S)
    if not m: return "review"
    try: raw = base64.b64decode(m.group(1))
    except Exception: return "review"
    return enforce(raw, ctx, lang)

def message(lang=None): lang = lang or getattr(_tl, "lang", "pl"); return MSG.get(lang[:2], MSG["pl"])
def review_message(lang=None): lang = lang or getattr(_tl, "lang", "pl"); return MSG_REVIEW.get(lang[:2], MSG_REVIEW["pl"])

class Held(ValueError):
    """Zdjęcie wstrzymane do ręcznej moderacji (miejsca bez kolejki publikacji, np. awatar na czacie). str(e) = uprzejmy komunikat."""
