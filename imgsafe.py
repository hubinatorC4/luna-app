"""Bezpieczne obrazy: sprawdzenie sygnatury, limit rozmiaru, ponowne kodowanie przez ffmpeg (usuwa EXIF/metadane)."""
import base64, hashlib, os, re, subprocess, tempfile, threading

def _ff():
    import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()

def kind(raw):
    s = raw[:12]
    if s.startswith(b"\xff\xd8\xff"): return "jpg"
    if s.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    if s[:4] == b"RIFF" and s[8:12] == b"WEBP": return "webp"
    return None

def reencode(raw, max_px=1024, max_in=4 * 1024 * 1024, quality=4):
    """Zwraca bajty JPEG bez metadanych (lub PNG gdy wejście PNG – zachowuje przezroczystość). Rzuca ValueError."""
    if len(raw) > max_in: raise ValueError("Obraz jest za duży.")
    k = kind(raw)
    if not k: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    out_ext = "png" if k == "png" else "jpg"
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in." + k), os.path.join(d, "out." + out_ext)
        open(src, "wb").write(raw)
        vf = f"scale='min({max_px},iw)':'min({max_px},ih)':force_original_aspect_ratio=decrease"
        cmd = [_ff(), "-v", "error", "-y", "-i", src, "-map_metadata", "-1", "-map_chapters", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact", "-frames:v", "1", "-vf", vf]
        cmd += (["-q:v", str(quality)] if out_ext == "jpg" else []) + [dst]
        r = subprocess.run(cmd, capture_output=True, timeout=20)
        if r.returncode or not os.path.exists(dst): raise ValueError("Nie udało się przetworzyć obrazu.")
        return open(dst, "rb").read(), out_ext

_cache, _lock = {}, threading.Lock()
def safe_avatar_dataurl(a, max_bytes=24 * 1024):
    """Awatar jako data URL → ponownie zakodowany 96 px JPEG bez metadanych (z pamięcią podręczną)."""
    m = re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", str(a or ""))
    if not m: return ""
    try: raw = base64.b64decode(m.group(2), validate=True)
    except Exception: return ""
    if len(raw) > max_bytes: return ""
    h = hashlib.sha1(raw, usedforsecurity=False).hexdigest()
    with _lock:
        if h in _cache: return _cache[h]
    try:
        out, ext = reencode(raw, max_px=96, max_in=max_bytes, quality=5)
        url = f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode()
    except Exception:
        url = ""
    with _lock:
        if len(_cache) > 2000: _cache.clear()
        _cache[h] = url
    return url

def reencode_webp(raw, max_px=1280, max_in=10 * 1024 * 1024, quality=80):
    """Zdjęcia z czatu: WebP bez metadanych (EXIF/GPS), maks. max_px na dłuższym boku. Rzuca ValueError."""
    if len(raw) > max_in: raise ValueError("Obraz jest za duży.")
    k = kind(raw)
    if not k: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in." + k), os.path.join(d, "out.webp")
        open(src, "wb").write(raw)
        vf = f"scale='min({max_px},iw)':'min({max_px},ih)':force_original_aspect_ratio=decrease"
        cmd = [_ff(), "-v", "error", "-y", "-i", src, "-map_metadata", "-1", "-map_chapters", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
               "-frames:v", "1", "-vf", vf, "-c:v", "libwebp", "-quality", str(int(quality)), "-compression_level", "4", dst]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode or not os.path.exists(dst): raise ValueError("Nie udało się przetworzyć obrazu.")
        return open(dst, "rb").read()
