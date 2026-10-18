# -*- coding: utf-8 -*-
"""JEDNA bramka dla KAŻDEGO obrazu, który wchodzi na stronę lub do aplikacji (t479u). Kolejność warstw:

  1. format: tylko data:image/(png|jpeg|webp);base64 z poprawnym base64 (albo surowe bajty z serwera)
  2. rozmiar pliku i wymiary (maks. 8000 px na boku / 40 MPx – bomby dekompresyjne odrzucone)
  3. sygnatura pliku = JPG/PNG/WEBP (SVG, HTML, GIF, PDF, skrypty i pliki „udające” obraz → odrzucone)
  4. animacje (GIF, APNG, animowany WebP) → odrzucone; skanowane są i tak wszystkie próbki klatek
  5. treści aktywne w pliku (<script, <svg, <html, <?php, %PDF) → odrzucone (pliki-poligloty)
  6. skrót percepcyjny (dHash 64 bit + odbicie lustrzane) na liście wcześniej odrzuconych i dodanych przez admina → odrzucone
  7. filtr nagości nsfw_filter (NudeNet + drugi model + udział skóry): block/error → odrzucone; review → zależnie od miejsca:
       "queue" – zwracamy werdykt, miejsce NIE publikuje automatycznie (kolejka Panelu admina)
       "hold"  – miejsce bez kolejki (awatar na czacie, wgrania admina): uprzejma odmowa (Held), skrót trafia do przeglądu
       "block" – odrzucenie (generator agentek: wariant „na granicy” jest od razu usuwany)
  8. ponowne kodowanie (ffmpeg): nowy plik bez EXIF/GPS/metadanych i bez doklejonych danych; sprawdzenie sygnatury wyniku
Bez wyjątków dla właściciela/admina/moderatora. Odrzucone obrazy nie są zapisywane – tylko skrót percepcyjny + wpis w dzienniku audytu."""
import base64, hashlib, io, re, threading, time
import imgsafe, nsfw_filter

MAX_SIDE, MAX_PIXELS = 8000, 25_000_000
DATAURL = re.compile(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\s]+)", re.S)
ACTIVE = re.compile(rb"<\s*(script|svg|html|iframe|object|embed|body)\b|<\?php|<\?xml|javascript:|%PDF-", re.I)
HAM = 6    # maks. odległość Hamminga dla „tego samego” obrazu (po przeskalowaniu/kompresji)
_lock = threading.Lock()

MSG = {
 "format": {"pl": "Dozwolone są tylko zdjęcia JPG, PNG lub WEBP.", "en": "Only JPG, PNG or WEBP images are allowed.",
            "es": "Solo se permiten imágenes JPG, PNG o WEBP.", "de": "Erlaubt sind nur JPG-, PNG- oder WEBP-Bilder.", "uk": "Дозволені лише зображення JPG, PNG або WEBP."},
 "anim":   {"pl": "Animacje (GIF / animowany WebP / APNG) nie są przyjmowane – wybierz zwykłe zdjęcie.", "en": "Animations (GIF / animated WebP / APNG) aren't accepted – please choose a still image.",
            "es": "No se aceptan animaciones (GIF / WebP animado / APNG): elige una imagen fija.", "de": "Animationen (GIF / animiertes WebP / APNG) werden nicht angenommen – bitte wähle ein Standbild.",
            "uk": "Анімації (GIF / анімований WebP / APNG) не приймаються – оберіть звичайне фото."},
 "size":   {"pl": "Obraz jest za duży.", "en": "The image is too large.", "es": "La imagen es demasiado grande.", "de": "Das Bild ist zu groß.", "uk": "Зображення завелике."},
 "hold":   nsfw_filter.MSG_REVIEW,
}
def _m(key, lang=None):
    lang = (lang or getattr(nsfw_filter._tl, "lang", "pl"))[:2]; d = MSG[key]; return d.get(lang, d["pl"])

class Rejected(ValueError):
    """Plik odrzucony przed skanem (format/rozmiar/animacja/treść aktywna). str(e) = komunikat dla użytkownika."""

class Result:
    __slots__ = ("bytes", "ext", "verdict", "dhash", "reason")
    def __init__(self, b, ext, verdict, dh, reason=""): self.bytes, self.ext, self.verdict, self.dhash, self.reason = b, ext, verdict, dh, reason
    def dataurl(self): return f"data:image/{'png' if self.ext == 'png' else 'webp' if self.ext == 'webp' else 'jpeg'};base64," + base64.b64encode(self.bytes).decode()
    def b64(self): return base64.b64encode(self.bytes).decode()

def decode(src, lang=None):
    """data URL (tylko PNG/JPEG/WEBP) albo bajty → bajty. Zły format → Rejected."""
    if isinstance(src, (bytes, bytearray)): return bytes(src)
    m = DATAURL.fullmatch(str(src or "").strip())
    if not m: raise Rejected(_m("format", lang))
    try: return base64.b64decode(re.sub(r"\s+", "", m.group(2)), validate=True)
    except Exception: raise Rejected(_m("format", lang))

def inspect(raw, max_in, lang=None):
    """Warstwy 2–5. Zwraca obiekt PIL (wczytany nagłówek). Rzuca Rejected."""
    if not raw or len(raw) > max_in: raise Rejected(_m("size", lang))
    k = imgsafe.kind(raw)
    if not k: raise Rejected(_m("format", lang))
    if ACTIVE.search(raw): raise Rejected(_m("format", lang))
    if k == "png" and b"acTL" in raw[:raw.find(b"IDAT") if b"IDAT" in raw else len(raw)]: raise Rejected(_m("anim", lang))
    if k == "webp" and (b"ANIM" in raw[:4096] or b"ANMF" in raw): raise Rejected(_m("anim", lang))
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        im = Image.open(io.BytesIO(raw))
        if (im.format or "").upper() not in ("JPEG", "PNG", "WEBP", "MPO"): raise Rejected(_m("format", lang))
        w, h = im.size
        if w < 8 or h < 8 or max(w, h) > MAX_SIDE or w * h > MAX_PIXELS: raise Rejected(_m("size", lang))
        if int(getattr(im, "n_frames", 1) or 1) > 1 and (im.format or "").upper() != "MPO": raise Rejected(_m("anim", lang))
        if im.format == "JPEG": im.draft("RGB", (512, 512))   # do skrótu wystarczy mała wersja (mniej RAM); pełny dekod i tak robi ffmpeg
        im.load()
    except Rejected: raise
    except Exception: raise Rejected(_m("format", lang))
    return im

# ---------- skrót percepcyjny (dHash) ----------
def dhash(im):
    """64-bitowy dHash (9×8 w skali szarości) oraz jego odbicie lustrzane – „ten sam” obraz po zmianie rozmiaru/kompresji ma bliski skrót."""
    from PIL import Image, ImageOps
    g = im.convert("L")
    out = []
    for x in (g, ImageOps.mirror(g)):
        p = list(x.resize((9, 8), Image.LANCZOS).getdata()); v = 0
        for r in range(8):
            for c in range(8): v = (v << 1) | (1 if p[r * 9 + c] > p[r * 9 + c + 1] else 0)
        out.append("%016x" % v)
    return out

def _hl():
    import store; return store.get("nsfw_hash_block", []) or []

def blocked_hash(hs):
    """Czy któryś skrót (lub odbicie) jest blisko skrótu z listy odrzuconych."""
    L = _hl()
    for h in hs:
        a = int(h, 16)
        for e in L:
            try:
                if bin(a ^ int(e["h"], 16)).count("1") <= HAM: return e
            except Exception: continue
    return None

def add_hash(h, src="auto", note=""):
    """Dodaje skrót do listy odrzuconych (automatycznie przy blokadzie albo przez admina). Bez obrazu – tylko 16 znaków hex."""
    if not re.fullmatch(r"[0-9a-f]{16}", str(h or "")): raise ValueError("Skrót: 16 znaków 0-9a-f.")
    import store
    with _lock:
        L = _hl()
        if not any(e.get("h") == h for e in L):
            L.append({"h": h, "t": int(time.time()), "src": str(src)[:12], "note": re.sub(r"[<>\x00-\x1f]", "", str(note))[:60]})
            store.put("nsfw_hash_block", L[-5000:])
    return True

def remove_hash(h):
    import store
    with _lock: store.put("nsfw_hash_block", [e for e in _hl() if e.get("h") != h])

def _stat(key):
    try:
        import store
        with _lock:
            S = store.get("nsfw_stats", {}) or {}; d = time.strftime("%Y-%m-%d", time.gmtime())
            S.setdefault(d, {}); S[d][key] = int(S[d].get(key, 0)) + 1
            store.put("nsfw_stats", dict(sorted(S.items())[-60:]))
    except Exception: pass

def _audit(action, ctx, reason, hs):
    try:
        import security; security.audit(action, "", f"ctx={str(ctx)[:20]} reason={str(reason)[:40]} h={hs[0] if hs else ''}")
    except Exception: pass

def _held_review(ctx, hs, reason):
    """Przegląd dla miejsc bez kolejki publikacji: zapisujemy tylko skrót i powód (bez obrazu), admin widzi to w Panelu."""
    try:
        import store
        with _lock:
            Q = store.get("nsfw_held", []) or []
            Q.append({"t": int(time.time()), "ctx": str(ctx)[:20], "h": hs[0] if hs else "", "reason": str(reason)[:40]})
            store.put("nsfw_held", Q[-500:])
    except Exception: pass

def image(src, ctx, *, max_px=1024, max_in=5 * 1024 * 1024, quality=4, fmt="auto", review="queue", lang=None):
    """Bramka dla każdego obrazu. Zwraca Result (bytes, ext, verdict "ok"|"review", dhash). Rzuca Rejected / nsfw_filter.Blocked / nsfw_filter.Held."""
    raw = decode(src, lang)
    im = inspect(raw, max_in, lang)
    hs = dhash(im)
    hit = blocked_hash(hs)
    if hit:
        _stat("hash_block"); _audit("nsfw_block", ctx, "hash_list", hs)
        raise nsfw_filter.Blocked(nsfw_filter.message(lang), {}, "hash_list")
    try: verdict = nsfw_filter.enforce(raw, ctx, lang)
    except nsfw_filter.Blocked as e:
        if e.reason and not str(e.reason).startswith(("unavailable", "decode")):
            try: add_hash(hs[0], "auto", str(e.reason)[:30])   # ten sam obraz po przeskalowaniu nie wróci
            except Exception: pass
            _stat("block")
        else: _stat("error")
        _audit("nsfw_block", ctx, e.reason, hs)
        raise
    if verdict == "review":
        _stat("review")
        if review == "block":
            _audit("nsfw_review_drop", ctx, "review", hs); raise nsfw_filter.Blocked(nsfw_filter.message(lang), {}, "review_strict")
        if review == "hold":
            _held_review(ctx, hs, "review"); _audit("nsfw_hold", ctx, "review", hs); raise nsfw_filter.Held(_m("hold", lang))
    else: _stat("ok")
    try:
        if fmt == "webp": out, ext = imgsafe.reencode_webp(raw, max_px=max_px, max_in=max_in), "webp"
        else: out, ext = imgsafe.reencode(raw, max_px=max_px, max_in=max_in, quality=quality)
    except ValueError: raise Rejected(_m("format", lang))
    if imgsafe.kind(out) not in ("jpg", "png", "webp") or ACTIVE.search(out): raise Rejected(_m("format", lang))
    return Result(out, ext, verdict, hs)

def derived(b, *, max_px, quality=4):
    """Pochodna (miniatura/zmiana rozmiaru) obrazu, który JUŻ przeszedł image(). Tylko dla bajtów zwróconych przez bramkę lub zapisanych po niej."""
    return imgsafe.reencode(b, max_px=max_px, max_in=max(len(b) + 1, 12 * 1024 * 1024), quality=quality)

def video_file(path, ctx="video", n=24, lang=None):
    """Wideo (np. od dostawcy AI): próbki klatek równomiernie z całego filmu, KAŻDA przez nsfw_filter. ok | review; block/error → Blocked."""
    import os, subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([imgsafe._ff(), "-v", "error", "-i", path, "-vf", f"fps=1,scale='min(1024,iw)':-2", "-frames:v", str(n), "-q:v", "3",
                            os.path.join(d, "f%03d.jpg")], capture_output=True, timeout=180)
        fs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
        if r.returncode or not fs: _audit("nsfw_block", ctx, "video_decode", []); raise nsfw_filter.Blocked(nsfw_filter.MSG_ERROR["pl"], {}, "video_decode")
        worst = "ok"
        for f in fs:
            v = nsfw_filter.enforce(open(os.path.join(d, f), "rb").read(), ctx, lang)   # Blocked leci dalej
            if v == "review": worst = "review"
    return worst

def stats():
    import store
    return {"days": store.get("nsfw_stats", {}) or {}, "hashes": len(_hl()), "held": (store.get("nsfw_held", []) or [])[-100:][::-1], "filter": nsfw_filter.status()}

_sa, _sal = {}, threading.Lock()
def small_avatar_dataurl(a, max_bytes=24 * 1024):
    """Mały awatar z czatu na żywo (data URL ≤ 24 KB) → 96 px bez metadanych PO pełnej bramce; „na granicy” lub odrzucony → "" (domyślny awatar).
    Wynik w pamięci podręcznej po skrócie pliku (ten sam awatar w każdej wiadomości nie jest skanowany ponownie)."""
    s = str(a or "")
    if not s.startswith("data:image/") or len(s) > max_bytes * 4 // 3 + 64: return ""
    k = hashlib.sha256(s.encode()).hexdigest()
    with _sal:
        if k in _sa: return _sa[k]
    try: url = image(s, "chat_avatar", max_px=96, max_in=max_bytes, quality=5, review="block").dataurl()
    except Exception: url = ""
    with _sal:
        if len(_sa) > 2000: _sa.clear()
        _sa[k] = url
    return url

def hash_stored(src_b, note="mod"):
    """Moderator usunął obraz z kolejki → jego skrót trafia na listę (ten sam plik nie wróci po przeskalowaniu). src_b: bajty, base64 albo data URL."""
    try:
        if isinstance(src_b, str):
            s = src_b.split(",", 1)[1] if src_b.startswith("data:") else src_b
            src_b = base64.b64decode(s)
        from PIL import Image
        im = Image.open(io.BytesIO(src_b)); im.load()
        add_hash(dhash(im)[0], "mod", note); return True
    except Exception: return False
