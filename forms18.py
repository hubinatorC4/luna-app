"""Formularze zgłoszeniowe 18+: TESTERZY (prosty) i CASTING agentek/modelek (bardziej szczegółowy, w pełni anonimowy).
• Casting: tylko pseudonim – NIE ma pola na imię i nazwisko. Jedyny obowiązkowy element tożsamości to weryfikacja 18+
  u zewnętrznego dostawcy (dokument lub karta, verify18.py); zapisujemy wyłącznie wynik.
• Status zgłoszenia: verification = pending | verified | failed, decision = new | accepted | rejected.
  Zgłoszenie bez weryfikacji NIGDY nie jest oznaczane jako zweryfikowane.
• Ochrona: honeypot, minimalny czas wypełnienia, limit żądań (serwer), Cloudflare Turnstile (gdy skonfigurowany).
• Retencja: odrzucone zgłoszenia usuwamy po 90 dniach (razem z próbką głosu); próbki głosu są prywatne i moderowane."""
import base64, hashlib, os, re, secrets, subprocess, tempfile, threading, time
import store, age
from notify import EMAIL_RE

KEY = "f18_apps"
REJECT_TTL = 90 * 86400
DEVICES = ("android", "iphone", "desktop")
TOPICS = ("voice", "battles", "wall", "generator")
OFFERS = ("voice", "image", "both")
CATS = ("elegance", "night_city", "beach", "sport", "business", "nature", "voice_song", "casual")
ANON = ("voice_only", "no_face", "full")
AVAIL = ("weekdays", "evenings", "weekends", "flexible")
LANGS = ("pl", "en", "de", "es", "uk", "other")
CONSENTS = {
    "tester": ("terms", "privacy", "nda"),
    "casting": ("use_voice_image", "discretion", "withdraw", "gdpr"),
}
CONSENT_TEXT = {  # treść zgód zapisywana przy zgłoszeniu (PL wiąże prawnie)
    "terms": "Akceptuję regulamin.", "privacy": "Zapoznałam/em się z polityką prywatności.",
    "nda": "Zachowam w tajemnicy nieopublikowane funkcje, które zobaczę w testach (poufność testów).",
    "use_voice_image": "Wyrażam wyraźną zgodę na wykorzystanie mojego głosu i/lub wizerunku w zakresie, który wybrałam/em (art. 81 pr. aut.), dopiero po podpisaniu umowy.",
    "discretion": "Rozumiem obietnicę „Dyskrecja i anonimowość”: publicznie występuję wyłącznie pod pseudonimem, moja tożsamość nie jest ujawniana.",
    "withdraw": "Wiem, że mogę w każdej chwili wycofać zgodę i zgłoszenie, bez podawania przyczyny.",
    "gdpr": "Wyrażam zgodę na przetwarzanie danych z formularza w celu przeprowadzenia castingu (RODO, art. 6 ust. 1 lit. a).",
}
VOICE_MAX = 3 * 1024 * 1024
_lock = threading.Lock()

def _all(): return store.get(KEY, {}) or {}
def _save(a): store.put(KEY, a)
def _h(s): return hashlib.sha256(("f18:" + str(s)).encode()).hexdigest()
def _clean(s, n): return re.sub(r"[<>\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(s or "").strip())[:n]
def _pick(v, allowed): return v if v in allowed else None
def _multi(v, allowed, mx=8):
    return [x for x in dict.fromkeys(v if isinstance(v, list) else []) if x in allowed][:mx]

def purge(now=None):
    """Retencja: odrzucone > 90 dni → usunięte (z próbką głosu). Wywoływane przy zapisie i w panelu."""
    now = now or time.time(); gone = []
    with _lock:
        a = _all()
        for k, r in list(a.items()):
            if r.get("decision") == "rejected" and now - r.get("decided_at", r["t"]) > REJECT_TTL:
                gone.append(k); a.pop(k)
        if gone: _save(a)
    for k in gone: store.put("f18_voice:" + k, {})
    return gone

def _antispam(d):
    if str(d.get("website", "")).strip(): raise PermissionError("spam")
    try:
        if time.time() * 1000 - float(d.get("t0", 0)) < 4000: raise PermissionError("spam")
    except (TypeError, ValueError): raise PermissionError("spam")

def _adult(d):
    """18+: tylko „Masz 18 lat?” Tak / Nie – bez daty urodzenia (nie zbieramy jej). Starsze klienty z datą: nadal odmowa < 18, daty nie zapisujemy."""
    if d.get("adult_confirmed") is False: raise age.Underage(age.UNDER_MSG)
    if d.get("dob") and age.age_of(str(d.get("dob")).strip()) < 18: raise age.Underage(age.UNDER_MSG)
    if d.get("adult_confirmed") is not True and not d.get("dob"): raise ValueError("Potwierdź, że masz ukończone 18 lat.")
    return True

def _voice(data_url):
    """Próbka głosu (opcjonalna): audio ≤ 3 MB, przekodowane ffmpeg do mono MP3 ≤ 60 s bez metadanych. Zwraca base64 MP3."""
    m = re.fullmatch(r"data:audio/[a-z0-9.+-]+(;codecs=[^;,]+)?;base64,([A-Za-z0-9+/=]+)", str(data_url or ""), re.S)
    if not m: raise ValueError("Próbka głosu: wybierz plik audio (MP3, M4A, OGG, WAV, WEBM).")
    raw = base64.b64decode(m.group(2))
    if len(raw) > VOICE_MAX: raise ValueError("Próbka głosu może mieć maks. 3 MB.")
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "in"), os.path.join(td, "out.mp3")
        open(src, "wb").write(raw)
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", "60", "-map_metadata", "-1", "-vn", "-ac", "1", "-ar", "24000", "-b:a", "64k", dst],
                           capture_output=True, timeout=60)
        if r.returncode or not os.path.isfile(dst) or os.path.getsize(dst) < 1000: raise ValueError("Nie udało się odczytać próbki głosu – spróbuj innego pliku.")
        return base64.b64encode(open(dst, "rb").read()).decode()

def submit(kind, d, ip_hash="", uid=""):
    """Zapisuje zgłoszenie. Zwraca (rekord, klucz_statusu). Underage → grzeczna odmowa bez zapisu; spam → PermissionError."""
    if kind not in CONSENTS: raise ValueError("bad form")
    _antispam(d)
    email = str(d.get("email", "")).strip()[:254]
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail do kontaktu.")
    _adult(d)
    miss = [c for c in CONSENTS[kind] if (d.get("consents") or {}).get(c) is not True]
    if miss: raise ValueError("Zaznacz wymagane zgody.")
    now = int(time.time())
    r = {"id": secrets.token_hex(6), "kind": kind, "t": now, "email": email, "adult_confirmed": True, "adult_confirmed_at": now,
         "consents": {c: CONSENT_TEXT[c] for c in CONSENTS[kind]}, "consents_at": now,
         "verification": {"status": "pending", "method": None, "at": 0, "provider": None, "ref": None},
         "decision": "new", "decided_at": 0, "ip": ip_hash, "uid": uid or "", "read": False}
    if kind == "tester":
        nick = _clean(d.get("nickname"), 30)
        if len(nick) < 2: raise ValueError("Podaj nick (min. 2 znaki).")
        dev = _pick(d.get("device"), DEVICES)
        if not dev: raise ValueError("Wybierz urządzenie.")
        topics = _multi(d.get("topics"), TOPICS)
        if not topics: raise ValueError("Wybierz, co chcesz testować.")
        r.update(nickname=nick, device=dev, topics=topics, note=_clean(d.get("note"), 300))
    else:
        nick = _clean(d.get("pseudonym"), 40)
        if len(nick) < 2: raise ValueError("Podaj pseudonim (min. 2 znaki).")
        offer = _pick(d.get("offer"), OFFERS)
        if not offer: raise ValueError("Wybierz, co oferujesz: głos, wizerunek albo oba.")
        desc = _clean(d.get("description"), 600)
        if len(desc) < 20: raise ValueError("Napisz kilka zdań o sobie (min. 20 znaków).")
        link = str(d.get("portfolio", "")).strip()[:300]
        if link and not re.fullmatch(r"https://[^\s<>\"']{3,300}", link): raise ValueError("Link do portfolio musi zaczynać się od https://")
        phone = re.sub(r"[^\d+ ]", "", str(d.get("phone", "")))[:20].strip()
        r.update(pseudonym=nick, offer=offer, partner_posts=d.get("partner_posts") is True, promo_videos=d.get("promo_videos") is True,
                 description=desc, phone=phone, country=_clean(d.get("country"), 40), langs=_multi(d.get("langs"), LANGS),
                 cats=_multi(d.get("cats"), CATS, 3), portfolio=link, availability=_pick(d.get("availability"), AVAIL),
                 anonymity=_pick(d.get("anonymity"), ANON), voice=None)
        if d.get("voice"):
            store.put("f18_voice:" + r["id"], {"mp3": _voice(d["voice"]), "t": now})
            r["voice"] = {"status": "pending_review", "t": now}
    key = secrets.token_urlsafe(18); r["key"] = _h(key)
    purge()
    with _lock:
        a = _all()
        if any(x["kind"] == kind and x["email"].lower() == email.lower() and x["decision"] != "rejected" for x in a.values()):
            if r.get("voice"): store.put("f18_voice:" + r["id"], {})
            raise ValueError("Zgłoszenie z tym adresem e-mail już do nas dotarło – dziękujemy!")
        a[r["id"]] = r; _save(a)
    return r, key

def get(app_id, key):
    r = _all().get(str(app_id or ""))
    if not r or not key or not secrets.compare_digest(r["key"], _h(key)): return None
    return r

def public(r):
    v = r["verification"]
    return {"id": r["id"], "kind": r["kind"], "nickname": r.get("nickname") or r.get("pseudonym"), "decision": r["decision"],
            "verification": {"status": v["status"], "method": v.get("method"), "weak": bool(v.get("weak")), "at": v.get("at", 0),
                             "card": {k: (v.get("card") or {}).get(k) for k in ("brand", "last4")} if v.get("card") else None, "reason": v.get("reason", "")}}

def set_ref(app_id, method, ref, provider):
    with _lock:
        a = _all(); r = a.get(app_id)
        if not r: raise KeyError("not found")
        if r["verification"]["status"] == "verified": return r
        r["verification"].update(method=method, ref=ref, provider=provider, started_at=int(time.time()))
        _save(a); return r

def on_result(app_id, res):
    """Wynik od dostawcy (webhook). Zapisujemy tylko status, metodę, datę, ref i (dla karty) markę/last4/typ."""
    with _lock:
        a = _all(); r = a.get(str(app_id or ""))
        if not r: return None
        if r["verification"]["status"] == "verified" and res.get("status") != "verified": return r
        r["verification"] = {"status": res["status"], "method": res.get("method"), "provider": res.get("provider"), "ref": res.get("ref"),
                             "at": int(time.time()), "weak": bool(res.get("weak")), "card": res.get("card"), "reason": res.get("reason", "")}
        r["read"] = False; _save(a); return r

def decide(app_id, decision, by="admin"):
    if decision not in ("accepted", "rejected", "new"): raise ValueError("bad decision")
    with _lock:
        a = _all(); r = a.get(app_id)
        if not r: raise KeyError("not found")
        if decision == "accepted" and r["verification"]["status"] != "verified":
            raise ValueError("Najpierw weryfikacja 18+ – nie można przyjąć zgłoszenia bez potwierdzonej pełnoletności.")
        r["decision"] = decision; r["decided_at"] = int(time.time()); r["read"] = True
        _save(a); return r

def voice_act(app_id, action):
    with _lock:
        a = _all(); r = a.get(app_id)
        if not r or not r.get("voice"): raise KeyError("not found")
        if action == "delete": r["voice"] = None; store.put("f18_voice:" + app_id, {})
        else: r["voice"]["status"] = "approved" if action == "approve" else "rejected"
        _save(a); return r

def voice_mp3(app_id):
    v = store.get("f18_voice:" + str(app_id), None)
    return base64.b64decode(v["mp3"]) if v and v.get("mp3") else None

def delete(app_id):
    with _lock:
        a = _all(); a.pop(app_id, None); _save(a)
    store.put("f18_voice:" + app_id, {})

def mark_read(app_id):
    with _lock:
        a = _all()
        if app_id in a: a[app_id]["read"] = True; _save(a)

def status_label(r):
    if r["decision"] == "rejected": return "rejected"
    if r["decision"] == "accepted": return "accepted"
    return "verified" if r["verification"]["status"] == "verified" else ("failed" if r["verification"]["status"] == "failed" else "pending")

def admin_list():
    purge()
    out = []
    for r in sorted(_all().values(), key=lambda x: -x["t"]):
        x = {k: v for k, v in r.items() if k not in ("key", "ip")}
        x["status"] = status_label(r); out.append(x)
    return out

def unread(): return sum(1 for r in _all().values() if not r.get("read"))
