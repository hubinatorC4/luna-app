"""„Problemy techniczne” – zgłoszenia z numerem LUNA-0001. Zrzut ekranu: tylko obraz, maks. 5 MB, ponownie kodowany (bez EXIF),
przechowywany prywatnie (dostęp wyłącznie z tokenem moderatora). Honeypot + rate limit po stronie serwera."""
import base64, hashlib, re, secrets, threading, time
import store, imgsafe, notify
CATS = ("Płatności", "Dźwięk/głos", "Mikrofon", "Konto/logowanie", "Butik", "Luna Live", "Aplikacja Android", "Inne")
STATUSES = ("nowe", "w trakcie", "rozwiązane")
_lock = threading.Lock()
def _all(): return store.get("tickets", []) or []
def _shots(): return store.get("ticket_shots", {}) or {}

def submit(d):
    if str(d.get("website", "")).strip(): raise PermissionError("spam")
    try:
        if time.time() * 1000 - float(d.get("t0", 0)) < 2500: raise PermissionError("spam")
    except (TypeError, ValueError): raise PermissionError("spam")
    cat = d.get("category") if d.get("category") in CATS else None
    desc = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(d.get("description", "")).strip())[:3000]
    email = str(d.get("email", "")).strip()[:254]
    if not cat: raise ValueError("Wybierz kategorię.")
    if len(desc) < 10: raise ValueError("Opisz problem (min. 10 znaków).")
    if email and not notify.EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail albo zostaw pole puste.")
    env = d.get("env") if isinstance(d.get("env"), dict) else {}
    env = {k: re.sub(r"[<>\x00-\x1f]", "", str(env.get(k, "")))[:200] for k in ("version", "ua", "lang", "screen", "page", "twa")}
    shot = None
    if d.get("screenshot"):
        m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(d["screenshot"]))
        if not m: raise ValueError("Zrzut ekranu musi być obrazem (JPG, PNG lub WEBP).")
        raw = base64.b64decode(m.group(2))
        if len(raw) > 5 * 1024 * 1024: raise ValueError("Zrzut ekranu jest za duży (maks. 5 MB).")
        out, ext = imgsafe.reencode(raw, max_px=1600, max_in=5 * 1024 * 1024, quality=4)
        shot = f"data:image/{'png' if ext == 'png' else 'jpeg'};base64," + base64.b64encode(out).decode()
    key = secrets.token_urlsafe(10)
    with _lock:
        a = _all(); n = (store.get("ticket_seq", 0) or 0) + 1; store.put("ticket_seq", n)
        tid = f"LUNA-{n:04d}"
        a.append({"id": tid, "t": int(time.time()), "category": cat, "description": desc, "email": email, "env": env, "status": "nowe",
                  "note": "", "reply": "", "has_shot": bool(shot), "key": hashlib.sha256(key.encode()).hexdigest(), "updated": int(time.time())})
        store.put("tickets", a[-2000:])
        if shot:
            sh = _shots(); sh[tid] = shot
            if len(sh) > 200: sh = dict(list(sh.items())[-200:])
            store.put("ticket_shots", sh)
    sent = False
    if email and notify.email_enabled():
        try:
            notify._send_email(email, f"Luna – przyjęliśmy zgłoszenie {tid}", f"Dziękujemy! Twoje zgłoszenie ma numer {tid}. Odpiszemy najszybciej, jak się da (maks. 30 dni).",
                               f"<p>Dziękujemy! Twoje zgłoszenie ma numer <b>{tid}</b>.</p><p>Odpiszemy najszybciej, jak się da (maks. 30 dni).</p>"); sent = True
        except Exception: sent = False
    return tid, key, sent

def status(tid, key):
    t = next((x for x in _all() if x["id"] == str(tid)), None)
    if not t or not secrets.compare_digest(t["key"], hashlib.sha256(str(key or "").encode()).hexdigest()): return None
    return {"id": t["id"], "status": t["status"], "reply": t["reply"], "updated": t["updated"]}

def admin_list(f=None):
    f = f or {}
    out = [{k: v for k, v in t.items() if k != "key"} for t in reversed(_all())
           if (not f.get("status") or t["status"] == f["status"]) and (not f.get("category") or t["category"] == f["category"])]
    return {"items": out, "new": sum(1 for t in _all() if t["status"] == "nowe")}

def shot(tid): return _shots().get(tid)

def update(tid, d):
    with _lock:
        a = _all(); t = next((x for x in a if x["id"] == tid), None)
        if not t: raise KeyError("not found")
        if d.get("status") in STATUSES: t["status"] = d["status"]
        if "note" in d: t["note"] = str(d["note"])[:2000]
        new_reply = None
        if "reply" in d and str(d["reply"]).strip() != t["reply"]: t["reply"] = new_reply = str(d["reply"]).strip()[:3000]
        t["updated"] = int(time.time()); store.put("tickets", a)
    if new_reply and t["email"] and notify.email_enabled():
        try: notify._send_email(t["email"], f"Luna – odpowiedź na zgłoszenie {tid}", new_reply, "<p>" + new_reply.replace("<", "&lt;").replace("\n", "<br>") + "</p>")
        except Exception: pass
    return t
