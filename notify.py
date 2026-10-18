"""Powiadomienia: Web Push (VAPID) i e-mail (Brevo / Resend). Bez kluczy – funkcje wyłączone z czytelnym statusem."""
import hashlib, html, json, os, re, secrets, threading, time, urllib.request
import store

PUB = os.getenv("VAPID_PUBLIC_KEY", "").strip()
PRIV = os.getenv("VAPID_PRIVATE_KEY", "").strip()
SUBJ = os.getenv("VAPID_SUBJECT", "mailto:luna-team@users.noreply.github.com").strip()
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "").strip().lower()
EMAIL_KEY = os.getenv("EMAIL_API_KEY", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://luna-voice-coach.onrender.com").rstrip("/")
CRON_SECRET = os.getenv("CRON_SECRET", "").strip()
TOPICS = ("live", "video", "update", "battle")
DEFAULT_TOPICS = ("live", "video", "update")   # "battle" tylko po włączeniu „Powiadom mnie o wyniku bitwy”
MOD_TOPIC = "mod"  # tylko z tokenem moderatora
_lock = threading.Lock()
LOG = []  # ostatnie zdarzenia (bez danych osobowych)

def log(t):
    LOG.append({"t": int(time.time()), "msg": t}); del LOG[:-30]

def push_enabled(): return bool(PUB and PRIV)
def email_enabled(): return EMAIL_PROVIDER in ("brevo", "resend") and bool(EMAIL_KEY and EMAIL_FROM)

# ---------- Web Push ----------
def _subs(): return store.get("push_subs", {}) or {}

def subscribe(sub, topics, uid=None, mod=False, merge=False):
    if not isinstance(sub, dict) or not re.match(r"https://", str(sub.get("endpoint", ""))) or not isinstance(sub.get("keys"), dict):
        raise ValueError("bad subscription")
    keys = sub["keys"]
    if not (isinstance(keys.get("p256dh"), str) and isinstance(keys.get("auth"), str)) or len(json.dumps(sub)) > 2000:
        raise ValueError("bad subscription")
    topics = ([MOD_TOPIC] if mod and MOD_TOPIC in (topics or []) else []) + ([t for t in (topics or DEFAULT_TOPICS) if t in TOPICS] or ([] if mod else list(DEFAULT_TOPICS)))
    h = hashlib.sha256(sub["endpoint"].encode()).hexdigest()[:32]
    with _lock:
        d = _subs()
        if h not in d and len(d) >= 20000: raise ValueError("limit")
        if merge and h in d: topics = sorted(set(d[h].get("topics", [])) | set(topics))
        d[h] = {"sub": {"endpoint": sub["endpoint"], "keys": {"p256dh": keys["p256dh"], "auth": keys["auth"]}}, "topics": topics, "t": int(time.time()), "uid": uid or d.get(h, {}).get("uid")}
        store.put("push_subs", d)
    return h

def unsubscribe(endpoint):
    h = hashlib.sha256(str(endpoint).encode()).hexdigest()[:32]
    with _lock:
        d = _subs(); d.pop(h, None); store.put("push_subs", d)

def send_push(topic, title, body, url="/", tag=None, uid=None):
    if not push_enabled(): return {"sent": 0, "failed": 0, "disabled": True}
    from pywebpush import webpush, WebPushException
    payload = json.dumps({"title": title[:80], "body": body[:200], "url": url if str(url).startswith("/") else "/", "tag": tag or topic}, ensure_ascii=False)
    sent = failed = 0; dead = []
    for h, s in list(_subs().items()):
        if uid is not None:
            if s.get("uid") != uid or (topic == "battle" and "battle" not in s.get("topics", [])): continue
        elif topic == "manual" and MOD_TOPIC in s.get("topics", []) and len(s.get("topics", [])) == 1: continue
        elif topic != "manual" and topic not in s.get("topics", DEFAULT_TOPICS): continue
        if topic == "update" and s.get("uid"):
            try:
                import userprof
                if not userprof.notif_on(s["uid"], "updates"): continue  # Mój panel → Powiadomienia → Nowości w aplikacji
            except Exception: pass
        try:
            webpush(s["sub"], payload, vapid_private_key=PRIV, vapid_claims={"sub": SUBJ}, ttl=3600 * 12, timeout=10)
            sent += 1
        except WebPushException as e:
            failed += 1
            if e.response is not None and e.response.status_code in (404, 410): dead.append(h)
        except Exception:
            failed += 1
    if dead:
        with _lock:
            d = _subs(); [d.pop(h, None) for h in dead]; store.put("push_subs", d)
    log(f"push {topic}: wysłano {sent}, błędy {failed}")
    return {"sent": sent, "failed": failed, "removed": len(dead)}

# ---------- E-mail ----------
EMAIL_RE = re.compile(r"[^@\s<>\"']{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}")
CONSENT = ("Wyrażam zgodę na otrzymywanie e-mailowych przypomnień o transmisjach Luna Live na podany adres. "
           "Zgodę mogę wycofać w każdej chwili linkiem „Wypisz się” w każdej wiadomości.")

def _esubs(): return store.get("email_subs", {}) or {}

def _send_email(to, subject, text, html_body, unsub_url=None):
    if not email_enabled(): raise RuntimeError("Wysyłka e-mail jest wyłączona (brak klucza dostawcy).")
    m = re.match(r"\s*(.*?)\s*<([^>]+)>\s*$", EMAIL_FROM); name, addr = (m.group(1) or "Luna", m.group(2)) if m else ("Luna", EMAIL_FROM)
    headers = {"List-Unsubscribe": f"<{unsub_url}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"} if unsub_url else {}
    if EMAIL_PROVIDER == "brevo":
        url, h = "https://api.brevo.com/v3/smtp/email", {"api-key": EMAIL_KEY}
        body = {"sender": {"name": name, "email": addr}, "to": [{"email": to}], "subject": subject, "textContent": text, "htmlContent": html_body}
        if headers: body["headers"] = headers
    else:
        url, h = "https://api.resend.com/emails", {"Authorization": "Bearer " + EMAIL_KEY}
        body = {"from": EMAIL_FROM, "to": [to], "subject": subject, "text": text, "html": html_body}
        if headers: body["headers"] = headers
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**h, "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r: return r.status

def _mail(to, token, subject, lines, cta=None):
    unsub = f"{PUBLIC_URL}/api/email/unsubscribe?t={token}"
    text = "\n\n".join(lines + ([f"{cta[0]}: {cta[1]}"] if cta else []) + [f"Wypisz się: {unsub}", "Luna – asystentka AI (postać wygenerowana sztucznie)."])
    btn = f'<p><a href="{html.escape(cta[1])}" style="background:#ff9000;color:#000;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:bold">{html.escape(cta[0])}</a></p>' if cta else ""
    hb = ("<div style='font-family:Arial,sans-serif;max-width:520px'>" + "".join(f"<p>{html.escape(l)}</p>" for l in lines) + btn +
          f"<p style='color:#888;font-size:12px'>Otrzymujesz tę wiadomość, bo zapisałeś(-aś) się na przypomnienia Luna Live. "
          f"<a href='{unsub}'>Wypisz się</a>. Luna – asystentka AI (postać wygenerowana sztucznie).</p></div>")
    return _send_email(to, subject, text, hb, unsub)

def email_subscribe(email, consent, ip=""):
    email = str(email or "").strip()[:254]
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail.")
    if consent is not True: raise ValueError("Zaznacz zgodę na otrzymywanie przypomnień.")
    with _lock:
        d = _esubs()
        for t, s in d.items():
            if s["email"].lower() == email.lower(): return t, s.get("confirmed", False)
        if len(d) >= 20000: raise ValueError("limit")
        t = secrets.token_urlsafe(18)
        d[t] = {"email": email, "confirmed": False, "confirm_sent": False, "t": int(time.time()), "consent": CONSENT,
                "ip": hashlib.sha256(("luna" + ip).encode()).hexdigest()[:16]}
        store.put("email_subs", d)
    send_confirmations()
    return t, False

def send_confirmations():
    if not email_enabled(): return 0
    n = 0
    for t, s in list(_esubs().items()):
        if s.get("confirmed") or s.get("confirm_sent"): continue
        try:
            _mail(s["email"], t, "Potwierdź zapis na przypomnienia Luna Live",
                  ["Cześć! Ktoś (mamy nadzieję, że Ty) zapisał ten adres na e-mailowe przypomnienia o transmisjach Luna Live.",
                   "Kliknij przycisk, aby potwierdzić. Jeśli to nie Ty – zignoruj tę wiadomość."],
                  ("Potwierdzam zapis", f"{PUBLIC_URL}/api/email/confirm?t={t}"))
            with _lock:
                d = _esubs()
                if t in d: d[t]["confirm_sent"] = True; store.put("email_subs", d)
            n += 1
        except Exception as e:
            log("e-mail potwierdzenie: błąd " + type(e).__name__); break
    return n

def email_confirm(t):
    with _lock:
        d = _esubs()
        if t not in d: return False
        d[t]["confirmed"] = True; d[t]["confirmed_at"] = int(time.time()); store.put("email_subs", d); return True

def email_unsubscribe(t):
    with _lock:
        d = _esubs()
        if t not in d: return False
        d.pop(t); store.put("email_subs", d); return True

def email_reminder(when_text):
    sent = failed = 0
    for t, s in list(_esubs().items()):
        if not s.get("confirmed"): continue
        try:
            _mail(s["email"], t, "Jutro Luna Live – przypomnienie",
                  [f"Przypominamy: Luna Live już jutro, {when_text} (czas polski).",
                   "Będą pytania z czatu, łamaniec językowy tygodnia i krótkie ćwiczenia głosu. Luna jest asystentką AI."],
                  ("Otwórz Luna Live", f"{PUBLIC_URL}/live.html")); sent += 1
        except Exception:
            failed += 1
    log(f"e-mail przypomnienie: wysłano {sent}, błędy {failed}")
    return {"sent": sent, "failed": failed}

def test_email(to):
    if not EMAIL_RE.fullmatch(str(to or "")): raise ValueError("Niepoprawny adres.")
    return _mail(to, "test", "Luna – testowa wiadomość", ["To jest testowa wiadomość z panelu producenta Luny."], None)

def status():
    es = _esubs(); ps = _subs()
    return {"push": {"enabled": push_enabled(), "subscribers": len(ps)},
            "email": {"enabled": email_enabled(), "provider": EMAIL_PROVIDER or None, "from_set": bool(EMAIL_FROM),
                      "subscribers": len(es), "confirmed": sum(1 for s in es.values() if s.get("confirmed"))},
            "cron": {"configured": bool(CRON_SECRET), "last": store.get("cron_last", None)},
            "storage": store.status(), "log": LOG[-10:]}
