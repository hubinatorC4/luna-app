"""Trasy HTTP formularzy 18+ (testerzy, casting), potwierdzenia „Masz 18 lat?” i panelu. Wydzielone z server.py.
get()/post() zwracają None, gdy ścieżka nie pasuje."""
import json, sys, urllib.parse
import forms18, verify18, antibot, livechat, security, accounts, testers, notify

def _qs(u, k): return (urllib.parse.parse_qs(u.query).get(k, [""])[0])[:64]

def config(casting_open=True):
    return {"verify": verify18.state(), "methods": verify18.methods(), "turnstile": antibot.TS_SITE if antibot.turnstile_on() else "",
            "testers_left": testers.remaining(), "casting_open": bool(casting_open),
            "options": {"devices": forms18.DEVICES, "topics": forms18.TOPICS, "offers": forms18.OFFERS, "cats": forms18.CATS,
                        "anon": forms18.ANON, "avail": forms18.AVAIL, "langs": forms18.LANGS}}

SAFE_CASTING = ("💖 Jesteś bezpieczna i anonimowa: występujesz tylko pod pseudonimem, Twoje prawdziwe dane nigdy nie są publiczne. "
                "Twoich danych, zdjęć i wizerunku nigdy nie wykorzystamy do promocji ani w celach zarobkowych bez Twojej odrębnej, wyraźnej, pisemnej zgody "
                "(osobno dla każdej kampanii, z prawem wycofania w każdej chwili; kampania partnerska tylko na podstawie podpisanej umowy). "
                "Wiek sprawdził zewnętrzny dostawca – u nas zostaje tylko „18+ potwierdzone”. Zgłoszenie i dane możesz usunąć w każdej chwili.")
def _notify_applicant(r, decision, code=""):
    """Wiadomość do zgłaszającego: prywatna skrzynka (jeśli ma konto i moduł skrzynki istnieje) + e-mail (jeśli skonfigurowany)."""
    who = r.get("nickname") or r.get("pseudonym") or ""
    form = "testów" if r["kind"] == "tester" else "castingu"
    if decision == "accepted":
        title = f"Twoje zgłoszenie do {form} zostało przyjęte 💚"
        body = f"Cześć {who}! Dziękujemy – Twoje zgłoszenie do {form} Luny zostało przyjęte." + (f" Twój kod testera: {code} (Premium na 60 dni – wpisz go w Ustawieniach aplikacji)." if code else " Odezwiemy się z kolejnymi krokami – zawsze tylko przez ten kanał.")
        if r["kind"] == "casting": body += " " + SAFE_CASTING
    else:
        title = f"Twoje zgłoszenie do {form}"
        body = f"Cześć {who}! Dziękujemy za zgłoszenie do {form} Luny. Tym razem nie możemy go przyjąć. Dane zgłoszenia usuniemy najpóźniej po 90 dniach."
    sent = []
    if r.get("uid"):
        try:
            import inbox  # prywatna skrzynka użytkownika (moduł może jeszcze nie być wdrożony)
            if hasattr(inbox, "deliver") and inbox.deliver(r["uid"], "important", title=title, body=body, link="/skrzynka.html"): sent.append("inbox")
        except Exception: pass
    if notify.email_enabled():
        try: notify._send_email(r["email"], "Luna – " + title, body, "<p>" + body + "</p>"); sent.append("email")
        except Exception: pass
    return sent

def get(h, u, token_ok, casting_open):
    p = u.path
    if p == "/api/forms/config": return h._json(config(casting_open))
    if p == "/api/forms/status":
        if not livechat.rate_ok("f18s:" + h._ip(), 30, 2000): return h._json({"error": "rate limited"}, 429)
        r = forms18.get(_qs(u, "id"), _qs(u, "k"))
        return h._json(forms18.public(r)) if r else h._json({"error": "not found"}, 404)
    if p in ("/api/admin/forms", "/api/admin/forms/voice"):
        if not token_ok(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        if p.endswith("voice"):
            b = forms18.voice_mp3(_qs(u, "id"))
            if not b: return h._json({"error": "not found"}, 404)
            h.send_response(200); h.send_header("Content-Type", "audio/mpeg"); h.send_header("Content-Length", str(len(b)))
            h.send_header("Cache-Control", "private, no-store"); h.end_headers(); h.wfile.write(b); return True
        return h._json({"items": forms18.admin_list(), "unread": forms18.unread(), "verify": verify18.state(), "methods": verify18.methods(),
                        "env_needed": verify18.ENV_NEEDED, "testers_left": testers.remaining()})
    return None

def post(h, u, data, token_ok, casting_open, base_url):
    p = u.path; ip = h._ip()
    if p in ("/api/forms/tester", "/api/forms/casting"):
        kind = p.rsplit("/", 1)[-1]
        if not (livechat.rate_ok("f18:" + ip, 2, 8) and livechat.rate_ok("f18:*", 40, 600)): return h._json({"error": "Za dużo zgłoszeń – spróbuj później."}, 429)
        if kind == "casting" and not casting_open: return h._json({"error": "Zgłoszenia zamknięte, finał wkrótce."}, 403)
        if kind == "tester" and testers.remaining() <= 0: return h._json({"error": "Komplet! Wszystkie 50 miejsc dla testerów jest już zajętych."}, 409)
        if not antibot.turnstile_ok(data.get("turnstile"), ip): return h._json({"error": "Potwierdź, że nie jesteś botem (Turnstile).", "turnstile": True}, 400)
        a = h._acct()
        try: r, key = forms18.submit(kind, data, security.ip_hash(ip), a[0]["uid"] if a else "")
        except PermissionError: return h._json({"ok": True, "id": "", "key": "", "verify": "soon"})  # spam: udajemy sukces, nic nie zapisujemy
        except forms18.age.Underage as e: return h._json({"error": str(e), "underage": True}, 403)
        except ValueError as e: return h._json({"error": str(e)}, 400)
        return h._json({"ok": True, "id": r["id"], "key": key, "verify": verify18.state(), "methods": verify18.methods(), "status": forms18.public(r)})
    if p == "/api/forms/verify":
        if not livechat.rate_ok("f18v:" + ip, 5, 40): return h._json({"error": "Za dużo prób – spróbuj później."}, 429)
        r = forms18.get(str(data.get("id", ""))[:20], str(data.get("k", ""))[:64])
        if not r: return h._json({"error": "Nie znaleziono zgłoszenia."}, 404)
        if r["verification"]["status"] == "verified": return h._json({"ok": True, "already": True})
        ret = f"{base_url}/zgloszenie.html?f={r['kind']}&id={r['id']}&k={urllib.parse.quote(str(data.get('k', '')))}"
        try: s = verify18.start(r["id"], r["kind"], data.get("method"), ret)
        except RuntimeError: return h._json({"soon": True, "error": "Weryfikacja wkrótce – Twoje zgłoszenie czeka jako „oczekuje na weryfikację”."}, 503)
        except ValueError as e: return h._json({"error": str(e)}, 400)
        except Exception as e:
            sys.stderr.write("verify18 start %s\n" % type(e).__name__); return h._json({"error": "Dostawca weryfikacji jest chwilowo niedostępny – spróbuj za chwilę."}, 502)
        forms18.set_ref(r["id"], data.get("method"), s["ref"], s["provider"])
        return h._json({"ok": True, "url": s["url"]})
    if p == "/api/forms/delete":   # zgłaszający może w każdej chwili usunąć zgłoszenie i dane (z próbką głosu)
        if not livechat.rate_ok("f18d:" + ip, 5, 40): return h._json({"error": "Za dużo prób."}, 429)
        r = forms18.get(str(data.get("id", ""))[:20], str(data.get("k", ""))[:64])
        if not r: return h._json({"error": "Nie znaleziono zgłoszenia."}, 404)
        forms18.delete(r["id"]); return h._json({"ok": True})
    if p == "/api/account/confirm-adult":
        a = h._acct()
        if not a: return h._json({"error": "Zaloguj się."}, 401)
        if not h._csrf_ok(a[1]): return h._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
        if data.get("adult_confirmed") is not True: return h._json({"error": "Potwierdź, że masz ukończone 18 lat."}, 400)
        u2 = accounts.confirm_adult(a[0]["uid"])
        return h._json({"ok": True, "user": accounts.public(u2)})
    if p == "/api/admin/forms":
        if not token_ok(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        act, aid = data.get("action"), str(data.get("id", ""))[:20]
        security.audit("forms " + str(act), ip, aid)
        try:
            extra = {}
            if act in ("accept", "reject", "reset"):
                r = forms18.decide(aid, {"accept": "accepted", "reject": "rejected", "reset": "new"}[act])
                code = ""
                if act == "accept" and r["kind"] == "tester":
                    code = testers.from_application(r); extra["tester_code"] = code
                if act in ("accept", "reject") and data.get("notify", True): extra["notified"] = _notify_applicant(r, r["decision"], code)
            elif act in ("voice_approve", "voice_reject", "voice_delete"): forms18.voice_act(aid, act[6:])
            elif act == "delete": forms18.delete(aid)
            elif act == "read": forms18.mark_read(aid)
            else: return h._json({"error": "bad action"}, 400)
        except KeyError: return h._json({"error": "not found"}, 404)
        except (ValueError, OverflowError) as e: return h._json({"error": str(e)}, 400)
        return h._json({"ok": True, **extra, "items": forms18.admin_list(), "unread": forms18.unread()})
    return None

def webhook(event):
    """Zdarzenia weryfikacji 18+ ze Stripe. Zwraca opis wyniku albo None (zdarzenie nie dotyczy weryfikacji)."""
    res = verify18.handle(event)
    if not res: return None
    app_id, out = res
    r = forms18.on_result(app_id, out)
    return "verify18:" + (out["status"] if r else "unknown_app")

ADULT_FREE = ("/api/account/", "/api/age/", "/api/forms/", "/api/admin/", "/api/stripe/", "/api/push/", "/api/stats", "/api/track", "/api/tickets", "/api/help")
def needs_adult(h, path):
    """Każde konto musi mieć potwierdzenie 18+. Konta sprzed wprowadzenia „Masz 18 lat?” dostają prośbę przy logowaniu;
    do tego czasu zapis (POST) poza kontem/pomocą jest blokowany."""
    if path.startswith(ADULT_FREE): return False
    a = h._acct()
    return bool(a and not a[0].get("adult_confirmed_at"))

FOOT_LINKS = (('/zaufanie.html', '🛡️ Bezpieczeństwo i anonimowość'), ('/zespol.html', '🤝 Dołącz do zespołu'))
def trust_link(doc, path):
    """Dodaje w stopce każdej strony linki „Bezpieczeństwo i anonimowość” i „Dołącz do zespołu” (przed „Regulamin”)."""
    if path == "/panel.html" or "<footer" not in doc: return doc
    i = doc.rfind("<footer"); foot = doc[i:]
    for href, label in FOOT_LINKS:
        if f'href="{href}"' in foot: continue
        for sep, needle in ((" · ", ' · <a href="/regulamin.html">'), ("", '<a href="/regulamin.html">')):
            if needle in foot:
                link = f'<a href="{href}">{label}</a>'
                foot = foot.replace(needle, (sep + link + needle) if sep else (link + needle), 1); break
    return doc[:i] + foot
