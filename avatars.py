"""Awatary użytkowników: wolno wgrywać tylko obrazy wygenerowane przez AI (lub ikony).
Kontrola heurystyczna – NIE jest w 100% skuteczna: odrzucamy pliki z metadanymi aparatu (EXIF Make/Model/LensModel/GPS/
DateTimeOriginal), chyba że plik ma znacznik AI (IPTC DigitalSourceType trainedAlgorithmicMedia, manifest C2PA, znane tagi
generatorów). Po kontroli obraz jest ponownie kodowany, a metadane usuwane. Wymagane jest też oświadczenie użytkownika."""
import base64, hashlib, re, struct, threading, time
import store, imgsafe

DECL = "Oświadczam, że to obraz wygenerowany przez AI i nie przedstawia prawdziwej osoby."
CAMERA_TAGS = {0x010F: "Make", 0x0110: "Model", 0xA434: "LensModel", 0x9003: "DateTimeOriginal", 0x8825: "GPS"}
AI_MARKERS = [b"trainedAlgorithmicMedia", b"compositeWithTrainedAlgorithmicMedia", b"algorithmicMedia",
              b"c2pa", b"C2PA", b"DALL-E", b"DALL\xc2\xb7E", b"Midjourney", b"Stable Diffusion", b"stable-diffusion",
              b"Adobe Firefly", b"Grok Imagine", b"NovelAI", b"ComfyUI", b"Leonardo.Ai", b"Ideogram"]
_lock = threading.Lock()

def _tiff_tags(t):
    """Zwraca zbiór nazw tagów aparatu znalezionych w bloku TIFF/EXIF."""
    found = set()
    if len(t) < 8 or t[:2] not in (b"II", b"MM"): return found
    e = "<" if t[:2] == b"II" else ">"
    def ifd(off, depth=0):
        if depth > 3 or off <= 0 or off + 2 > len(t): return
        n = struct.unpack(e + "H", t[off:off + 2])[0]
        for i in range(min(n, 400)):
            p = off + 2 + i * 12
            if p + 12 > len(t): return
            tag, typ, cnt = struct.unpack(e + "HHI", t[p:p + 8]); val = struct.unpack(e + "I", t[p + 8:p + 12])[0]
            if tag in CAMERA_TAGS:
                # pusty Make/Model nie liczy się jako aparat
                if tag in (0x010F, 0x0110, 0xA434) and typ == 2:
                    s = t[val:val + cnt] if cnt > 4 else t[p + 8:p + 8 + cnt]
                    if s.strip(b"\x00 "): found.add(CAMERA_TAGS[tag])
                else: found.add(CAMERA_TAGS[tag])
            if tag == 0x8769: ifd(val, depth + 1)  # Exif SubIFD
    try: ifd(struct.unpack(e + "I", t[4:8])[0])
    except Exception: pass
    return found

def exif_blocks(raw):
    k = imgsafe.kind(raw); out = []
    if k == "jpg":
        i = 2
        while i + 4 < len(raw) and raw[i] == 0xFF:
            m = raw[i + 1]; ln = struct.unpack(">H", raw[i + 2:i + 4])[0]
            seg = raw[i + 4:i + 2 + ln]
            if m == 0xE1 and seg.startswith(b"Exif\x00\x00"): out.append(seg[6:])
            if m == 0xDA: break
            i += 2 + ln
    elif k == "png":
        i = 8
        while i + 8 < len(raw):
            ln = struct.unpack(">I", raw[i:i + 4])[0]; typ = raw[i + 4:i + 8]
            if typ == b"eXIf": out.append(raw[i + 8:i + 8 + ln])
            i += 12 + ln
    elif k == "webp":
        i = 12
        while i + 8 < len(raw):
            typ = raw[i:i + 4]; ln = struct.unpack("<I", raw[i + 4:i + 8])[0]
            if typ == b"EXIF":
                b = raw[i + 8:i + 8 + ln]; out.append(b[6:] if b.startswith(b"Exif\x00\x00") else b)
            i += 8 + ln + (ln & 1)
    return out

def inspect(raw):
    cam = set()
    for b in exif_blocks(raw): cam |= _tiff_tags(b)
    markers = sorted({m.decode("utf-8", "replace") for m in AI_MARKERS if m in raw})
    return {"camera": sorted(cam), "ai_markers": markers}

def check_upload(data_url, declared, vid="", name=""):
    if declared is not True: raise ValueError("Zaznacz oświadczenie, że to obraz wygenerowany przez AI i nie przedstawia prawdziwej osoby.")
    m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m: raise ValueError("Dozwolone są tylko obrazy JPG, PNG lub WEBP.")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 5 * 1024 * 1024: raise ValueError("Plik jest za duży (maks. 5 MB).")
    info = inspect(raw)
    if info["camera"] and not info["ai_markers"]:
        raise PermissionError("Ten plik wygląda na zdjęcie z aparatu lub telefonu (" + ", ".join(info["camera"]) +
                              "). Awatarem może być tylko obraz wygenerowany przez AI albo gotowa ikona – wybierz awatar z galerii lub wygeneruj go w aplikacji.")
    import nsfw_filter, upload_gate
    g = upload_gate.image(raw, "avatar", max_px=256, max_in=5 * 1024 * 1024, quality=4)  # wszystkie warstwy; nagość → Blocked
    nsfw, out, ext = g.verdict, g.bytes, g.ext
    url = f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode()
    thumb, _ = upload_gate.derived(out, max_px=64, quality=6)
    rec = {"id": hashlib.sha1(out, usedforsecurity=False).hexdigest()[:16], "vid": str(vid)[:32], "uid": str(vid)[:8], "name": str(name)[:30], "t": int(time.time()),
           "thumb": "data:image/jpeg;base64," + base64.b64encode(thumb).decode(), "ai_markers": info["ai_markers"], "kind": "upload", "reports": 0}
    if nsfw != "ok": rec["nsfw_review"] = True
    with _lock:
        u = store.get("avatar_mod", {}) or {}; u[rec["id"]] = {**u.get(rec["id"], {}), **rec}
        store.put("avatar_mod", dict(sorted(u.items(), key=lambda kv: -kv[1]["t"])[:300]))
    if nsfw != "ok": raise nsfw_filter.Held(nsfw_filter.review_message())  # awatar od razu widać na czacie → na granicy: nie publikujemy
    return url, info

def report(uid, name, avatar, reason=""):
    if not re.fullmatch(r"[0-9a-f]{8}", str(uid or "")): raise ValueError("bad id")
    import upload_gate
    thumb = upload_gate.small_avatar_dataurl(avatar) if avatar else ""   # moderator nie zobaczy miniatury, którą filtr odrzuca
    rid = "r" + uid
    with _lock:
        u = store.get("avatar_mod", {}) or {}
        r = u.get(rid) or {"id": rid, "uid": uid, "vid": "", "kind": "report", "reports": 0, "reasons": []}
        r.update({"name": str(name)[:30], "t": int(time.time()), "thumb": thumb or r.get("thumb", "")}); r["reports"] += 1
        r["reasons"] = (r.get("reasons", []) + [str(reason)[:120]])[-5:]
        u[rid] = r; store.put("avatar_mod", u)

def blocked_uids(): return set(store.get("avatar_blocked", []) or [])

def block(uid, on=True):
    with _lock:
        b = blocked_uids(); (b.add if on else b.discard)(uid); store.put("avatar_blocked", sorted(b))

def dismiss(id_):
    with _lock:
        u = store.get("avatar_mod", {}) or {}; u.pop(id_, None); store.put("avatar_mod", u)

def admin_list():
    b = blocked_uids()
    return [{**v, "blocked": v["uid"] in b} for v in sorted((store.get("avatar_mod", {}) or {}).values(), key=lambda v: (-(v.get("kind") == "report"), -v["t"]))]
