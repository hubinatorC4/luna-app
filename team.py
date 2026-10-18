"""„Dołącz do zespołu” – zgłoszenia osób chcących pomóc rozwijać Lunę (moderacja, grafika, kod, marketing, tłumaczenia, głos).
Bez obietnic pensji/etatu/udziałów/umowy – warunki ustalane indywidualnie. Honeypot + limit czasu + limity żądań.
Zgłoszenia: kolejka w panelu moderatora (/api/admin/team) i skrzynka właściciela (owner.inbox → team_applications). Odrzucone usuwamy po 90 dniach."""
import re, secrets, threading, time
import store
from notify import EMAIL_RE

AREAS = ("moderation", "design", "code", "marketing", "translation", "voice", "other")
AREA_PL = {"moderation": "moderacja", "design": "grafika/design", "code": "programowanie", "marketing": "marketing/social", "translation": "tłumaczenia", "voice": "głos", "other": "inne"}
CONSENT = ("Zgadzam się na przetwarzanie moich danych (nick, e-mail, opis, link) w celu odpowiedzi na to zgłoszenie. "
           "Zgodę mogę wycofać w każdej chwili.")
KEEP_REJECTED = 90 * 86400
_lock = threading.Lock()
def _all(): return store.get("team_apps", []) or []

def submit(d, ip_hash="", uid=""):
    if str(d.get("website", "")).strip(): raise PermissionError("spam")
    try:
        if time.time() * 1000 - float(d.get("t0", 0)) < 3000: raise PermissionError("spam")
    except (TypeError, ValueError): raise PermissionError("spam")
    nick = re.sub(r"[<>\x00-\x1f]", "", str(d.get("nick", "")).strip())[:30]
    email = str(d.get("email", "")).strip()[:254]
    areas = [a for a in (d.get("areas") or []) if a in AREAS][:7] if isinstance(d.get("areas"), list) else []
    desc = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(d.get("description", "")).strip())
    link = str(d.get("portfolio", "")).strip()[:300]
    if len(nick) < 2: raise ValueError("Podaj nick (min. 2 znaki).")
    if not EMAIL_RE.fullmatch(email): raise ValueError("Podaj poprawny adres e-mail.")
    if not areas: raise ValueError("Wybierz przynajmniej jeden obszar.")
    if not 20 <= len(desc) <= 2000: raise ValueError("Opis: 20–2000 znaków.")
    if link and not re.fullmatch(r"https?://[^\s<>\"']{3,300}", link): raise ValueError("Link musi zaczynać się od https://")
    if d.get("adult") is not True: raise ValueError("Zespół jest tylko dla osób pełnoletnich – potwierdź, że masz 18 lat.")
    if d.get("consent") is not True: raise ValueError("Zaznacz zgodę na przetwarzanie danych.")
    now = int(time.time())
    rec = {"id": secrets.token_hex(6), "t": now, "nick": nick, "email": email, "areas": list(dict.fromkeys(areas)), "description": desc, "portfolio": link,
           "adult_confirmed": True, "adult_at": now, "consent": CONSENT, "consent_at": now, "lang": str(d.get("lang", "pl"))[:2], "uid": uid or "",
           "status": "new", "read": False, "ip": ip_hash}
    with _lock:
        A = _all()
        if any(a["email"].lower() == email.lower() and now - a["t"] < 86400 for a in A): return next(a for a in A if a["email"].lower() == email.lower())
        A.append(rec); store.put("team_apps", A[-1000:])
    return rec

def purge():
    now = time.time()
    with _lock:
        A = _all(); B = [a for a in A if not (a["status"] == "rejected" and now - a.get("decided", a["t"]) > KEEP_REJECTED)]
        if len(B) != len(A): store.put("team_apps", B)

def admin_list():
    purge(); return list(reversed(_all()))[:300]

def unread(): return sum(1 for a in _all() if not a.get("read"))

NOTE = {
 "contact": {"pl": ("🤝 Dołącz do zespołu – odezwiemy się", "Dzięki za zgłoszenie do zespołu Luny! Moderator przeczytał je i odezwie się do Ciebie e-mailem, żeby porozmawiać o szczegółach. Warunki ewentualnej współpracy ustalamy indywidualnie."),
             "en": ("🤝 Join the team – we’ll be in touch", "Thanks for applying to the Luna team! A moderator has read it and will e-mail you to talk details. Any terms of collaboration are agreed individually."),
             "es": ("🤝 Únete al equipo – te escribiremos", "¡Gracias por tu solicitud al equipo de Luna! Un moderador la ha leído y te escribirá por correo para hablar de los detalles. Las condiciones de una posible colaboración se acuerdan individualmente."),
             "de": ("🤝 Werde Teil des Teams – wir melden uns", "Danke für deine Bewerbung im Luna-Team! Ein Moderator hat sie gelesen und meldet sich per E-Mail, um Details zu besprechen. Bedingungen einer möglichen Zusammenarbeit vereinbaren wir individuell."),
             "uk": ("🤝 Приєднуйтесь до команди – ми напишемо", "Дякуємо за заявку до команди Луни! Модератор її прочитав і напише вам e-mailом, щоб обговорити деталі. Умови можливої співпраці погоджуємо індивідуально.")},
 "rejected": {"pl": ("🤝 Dołącz do zespołu – dziękujemy", "Dziękujemy za chęć pomocy! Na razie nie mamy zadania, które pasowałoby do Twojego zgłoszenia – ale Luna zapamiętała Twój entuzjazm 💚 Możesz zgłosić się ponownie w przyszłości."),
              "en": ("🤝 Join the team – thank you", "Thank you for wanting to help! Right now we don’t have a task that fits your application – but Luna remembers your enthusiasm 💚 You’re welcome to apply again in the future."),
              "es": ("🤝 Únete al equipo – gracias", "¡Gracias por querer ayudar! Ahora mismo no tenemos una tarea que encaje con tu solicitud, pero Luna recuerda tu entusiasmo 💚 Puedes volver a apuntarte en el futuro."),
              "de": ("🤝 Werde Teil des Teams – danke", "Danke, dass du helfen möchtest! Gerade haben wir keine Aufgabe, die zu deiner Bewerbung passt – aber Luna merkt sich deine Begeisterung 💚 Du kannst dich gern später wieder melden."),
              "uk": ("🤝 Приєднуйтесь до команди – дякуємо", "Дякуємо за бажання допомогти! Зараз у нас немає завдання, що пасувало б до вашої заявки, – але Луна запам’ятала ваш ентузіазм 💚 Ви можете подати заявку знову згодом.")},
}

def _notify(a, kind):
    if not a.get("uid"): return
    try:
        import inbox
        m = inbox.deliver(a["uid"], "important", title="🤝", body=".", dedupe="team:" + a["id"] + kind)
        if not m: return
        with inbox._lock:
            d = inbox._ib(a["uid"])
            for x in d.get("m", []):
                if x["id"] == m["id"]: x["ti"] = {l: v[0] for l, v in NOTE[kind].items()}; x["bo"] = {l: v[1] for l, v in NOTE[kind].items()}
            store.put("ib:" + a["uid"], d)
    except Exception: pass

def act(id_, action):
    with _lock:
        A = _all(); a = next((x for x in A if x["id"] == id_), None)
        if not a: raise KeyError(id_)
        if action == "read": a["read"] = True
        elif action in ("contact", "rejected", "new"): a["status"] = action; a["read"] = True; a["decided"] = int(time.time())
        elif action == "delete": A = [x for x in A if x["id"] != id_]
        else: raise ValueError("bad action")
        store.put("team_apps", A)
    if action in ("contact", "rejected"): _notify(a, action)
    return admin_list()

# ---------- HTTP ----------
def post(h, u, data, token_ok):
    if u.path == "/api/team/apply":
        import livechat, hashlib
        ip = h._ip()
        if not (livechat.rate_ok("team:" + ip, 2, 6) and livechat.rate_ok("team:*", 30, 600)):
            return h._json({"error": "Dużo zgłoszeń naraz – Luna nadrabia lekturę 📚 Spróbuj za chwilę."}, 429)
        uid, _dev = h._who()
        try: rec = submit(data, hashlib.sha256(("team:" + ip).encode()).hexdigest()[:12], uid)
        except PermissionError: return h._json({"ok": True})   # honeypot / za szybko – bez sygnału dla botów
        except ValueError as e: return h._json({"error": str(e)}, 400)
        h._team_new = rec
        return h._json({"ok": True})
    if u.path == "/api/admin/team":
        if not token_ok(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        try: return h._json({"ok": True, "items": act(str(data.get("id", ""))[:12], str(data.get("action", "")))})
        except KeyError: return h._json({"error": "not found"}, 404)
        except ValueError as e: return h._json({"error": str(e)}, 400)
    return None

def get(h, u, token_ok):
    if u.path == "/api/admin/team":
        if not token_ok(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        return h._json({"ok": True, "items": admin_list(), "areas": AREA_PL})
    return None
