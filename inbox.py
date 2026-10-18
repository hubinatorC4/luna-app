# -*- coding: utf-8 -*-
"""Skrzynka (prywatna skrzynka wiadomości), Znajomi i prosty czat 1:1 tylko dla znajomych.
Zasady prywatności (nie do wyłączenia):
- publicznie tylko nick i losowy identyfikator znajomego (pid) – nigdy e-mail, uid ani dane osobowe;
- wiadomości czatu widzą wyłącznie dwie osoby rozmowy; moderator widzi tylko kopię ZGŁOSZONEJ wiadomości;
- czat tylko między znajomymi (obie strony zaakceptowały), blokada odcina wszystko natychmiast;
- tylko tekst + emoji (bez plików w v1), filtr słów i spamu jak na Ściance, limity szybkości;
- eksport (RODO art. 15/20) i usunięcie wraz z kontem. Prawdziwa agentka głosowa nigdy nie występuje w skrzynce.
Magazyn: tabela luna_kv (Postgres przy DATABASE_URL, inaczej data/kv.json) – klucze opisane w README modułu poniżej.
  ib:<uid>    – wiadomości systemowe użytkownika {"m":[...], "bc":{id:{"r":1,"a":1,"d":1}}}
  ib_bcast    – komunikaty moderatora / „Co nowego” do wszystkich lub segmentu (ostatnie 100)
  fr:<uid>    – znajomi, zaproszenia, zablokowani, ustawienia, liczniki nieprzeczytanych rozmów
  fr_inv      – token linku/QR zaproszenia -> uid
  dm:<a>-<b>  – rozmowa dwóch znajomych (ostatnie 500 wiadomości)
  dm_reports  – zgłoszenia (tylko kopia zgłoszonej wiadomości albo samo zgłoszenie konta)
  ib_bt_done  – bitwy, o których wynikach już powiadomiono"""
import hashlib, re, secrets, threading, time
import presence
import store, accounts, social, nicktier, partners, livechat, notify, textutil

_lock = threading.RLock()
LANGS = ("pl", "en", "es", "de", "uk")
CATS = ("important", "updates", "battles", "friends")
MAX_MSGS, MAX_FRIENDS, MAX_DM, DM_LEN = 200, 300, 500, 1000
REPORT_HIDE = 1  # zgłoszona wiadomość znika u zgłaszającego od razu
SEGMENTS = ("all", "free", "premium", "pro", "paid", "testers")

# ---------- teksty systemowe (5 języków) ----------
T = {
 "welcome": {"pl": ("Witaj w Skrzynce 💌", "Tu trafiają ważne sprawy (konto, bezpieczeństwo, plan), nowości w aplikacji, wyniki Bitew (jeśli je włączysz) i zaproszenia od znajomych. Widzisz tylko swój nick – nikt nie zna Twojego e-maila."),
             "en": ("Welcome to your Inbox 💌", "Important matters (account, security, plan), app news, Battle results (if you turn them on) and friend invites land here. Only your nickname is visible – nobody sees your e-mail."),
             "es": ("Bienvenido a tu Buzón 💌", "Aquí llegan los asuntos importantes (cuenta, seguridad, plan), las novedades, los resultados de las Batallas (si los activas) y las invitaciones de amigos. Solo se ve tu nick: nadie ve tu e-mail."),
             "de": ("Willkommen im Postfach 💌", "Hier landen wichtige Dinge (Konto, Sicherheit, Plan), Neuigkeiten, Battle-Ergebnisse (wenn du sie einschaltest) und Freundschaftsanfragen. Sichtbar ist nur dein Nick – niemand sieht deine E-Mail."),
             "uk": ("Вітаємо у Скриньці 💌", "Сюди надходять важливі справи (акаунт, безпека, план), новини застосунку, результати Битв (якщо ввімкнете) і запрошення друзів. Видно лише ваш нік – ніхто не бачить вашого e-mail.")},
 "login": {"pl": ("🔐 Nowe logowanie na Twoje konto", "Zalogowano: {dev}. Jeśli to nie Ty – zmień hasło i wyloguj się na innych urządzeniach."),
           "en": ("🔐 New sign-in to your account", "Signed in: {dev}. If this wasn’t you, change your password and sign out on other devices."),
           "es": ("🔐 Nuevo inicio de sesión", "Inicio de sesión: {dev}. Si no fuiste tú, cambia la contraseña y cierra sesión en otros dispositivos."),
           "de": ("🔐 Neue Anmeldung bei deinem Konto", "Angemeldet: {dev}. Wenn du das nicht warst, ändere dein Passwort und melde dich auf anderen Geräten ab."),
           "uk": ("🔐 Новий вхід в акаунт", "Вхід: {dev}. Якщо це були не ви – змініть пароль і вийдіть на інших пристроях.")},
 "plan_on": {"pl": ("💎 Plan {plan} jest aktywny", "Dostęp działa do {until}. Dziękujemy! 💚 Bez automatycznego odnawiania."),
             "en": ("💎 {plan} plan is active", "Access runs until {until}. Thank you! 💚 No automatic renewal."),
             "es": ("💎 El plan {plan} está activo", "El acceso dura hasta el {until}. ¡Gracias! 💚 Sin renovación automática."),
             "de": ("💎 Plan {plan} ist aktiv", "Zugang bis {until}. Danke! 💚 Keine automatische Verlängerung."),
             "uk": ("💎 План {plan} активний", "Доступ діє до {until}. Дякуємо! 💚 Без автоматичного продовження.")},
 "plan_exp": {"pl": ("⏳ Plan {plan} wygasa {when}", "Dostęp kończy się {until}. Potem wracasz do planu Podstawowa – nic nie tracisz."),
              "en": ("⏳ {plan} plan expires {when}", "Access ends on {until}. Then you return to the Basic plan – you lose nothing."),
              "es": ("⏳ El plan {plan} vence {when}", "El acceso termina el {until}. Después vuelves al plan Básico, sin perder nada."),
              "de": ("⏳ Plan {plan} läuft {when} ab", "Zugang endet am {until}. Danach gilt wieder der Basis-Plan – nichts geht verloren."),
              "uk": ("⏳ План {plan} закінчується {when}", "Доступ завершується {until}. Потім – план Базовий, нічого не втрачаєте.")},
 "mod_ok": {"pl": ("✅ Twój wpis został zatwierdzony", "Moderator zatwierdził Twój wpis – jest już widoczny."),
            "en": ("✅ Your post was approved", "A moderator approved your post – it’s now visible."),
            "es": ("✅ Tu publicación fue aprobada", "Un moderador aprobó tu publicación: ya es visible."),
            "de": ("✅ Dein Beitrag wurde freigegeben", "Die Moderation hat deinen Beitrag freigegeben – er ist jetzt sichtbar."),
            "uk": ("✅ Ваш допис схвалено", "Модератор схвалив ваш допис – він уже видимий.")},
 "mod_no": {"pl": ("🛡️ Decyzja moderatora", "Twój wpis nie został opublikowany (zasady Ścianki: życzliwie, bez spamu, bez danych osobowych). Możesz napisać nowy."),
            "en": ("🛡️ Moderator decision", "Your post was not published (wall rules: be kind, no spam, no personal data). You can write a new one."),
            "es": ("🛡️ Decisión del moderador", "Tu publicación no se publicó (normas: amabilidad, sin spam, sin datos personales). Puedes escribir otra."),
            "de": ("🛡️ Entscheidung der Moderation", "Dein Beitrag wurde nicht veröffentlicht (Regeln: freundlich, kein Spam, keine persönlichen Daten). Du kannst einen neuen schreiben."),
            "uk": ("🛡️ Рішення модератора", "Ваш допис не опубліковано (правила: доброзичливо, без спаму й особистих даних). Можете написати новий.")},
 "bt_res": {"pl": ("🏆 Bitwa zakończona: wygrywa {win}", "{a} {va} : {vb} {b} – prawdziwe głosy. Zwyciężczyni zdobywa odznakę 🏆 na 24 h."),
            "en": ("🏆 Battle over: {win} wins", "{a} {va} : {vb} {b} – real votes. The winner gets the 🏆 badge for 24 h."),
            "es": ("🏆 Batalla terminada: gana {win}", "{a} {va} : {vb} {b} – votos reales. La ganadora recibe la insignia 🏆 durante 24 h."),
            "de": ("🏆 Battle beendet: {win} gewinnt", "{a} {va} : {vb} {b} – echte Stimmen. Die Siegerin erhält 24 h das 🏆-Abzeichen."),
            "uk": ("🏆 Битву завершено: перемагає {win}", "{a} {va} : {vb} {b} – справжні голоси. Переможниця отримує значок 🏆 на 24 год.")},
 "bt_draw": {"pl": ("⚔️ Bitwa zakończona remisem", "{a} {va} : {vb} {b} – prawdziwe głosy."), "en": ("⚔️ Battle ended in a draw", "{a} {va} : {vb} {b} – real votes."),
             "es": ("⚔️ La batalla terminó en empate", "{a} {va} : {vb} {b} – votos reales."), "de": ("⚔️ Battle endet unentschieden", "{a} {va} : {vb} {b} – echte Stimmen."),
             "uk": ("⚔️ Битва завершилася нічиєю", "{a} {va} : {vb} {b} – справжні голоси.")},
 "fr_req": {"pl": ("👋 {nick} zaprasza Cię do znajomych", "Zaakceptuj, aby pisać ze sobą na prywatnym czacie. Możesz też odrzucić albo zablokować."),
            "en": ("👋 {nick} sent you a friend request", "Accept to chat privately. You can also decline or block."),
            "es": ("👋 {nick} te envió una solicitud de amistad", "Acepta para chatear en privado. También puedes rechazarla o bloquear."),
            "de": ("👋 {nick} möchte mit dir befreundet sein", "Nimm an, um privat zu chatten. Du kannst auch ablehnen oder blockieren."),
            "uk": ("👋 {nick} запрошує вас у друзі", "Прийміть, щоб спілкуватися в приватному чаті. Також можна відхилити або заблокувати.")},
 "fr_ok": {"pl": ("💚 {nick} przyjmuje zaproszenie", "Jesteście znajomymi – możecie pisać na czacie."), "en": ("💚 {nick} accepted your request", "You’re friends now – you can chat."),
           "es": ("💚 {nick} aceptó tu solicitud", "Ya sois amigos: podéis chatear."), "de": ("💚 {nick} hat angenommen", "Ihr seid jetzt befreundet – ihr könnt chatten."),
           "uk": ("💚 {nick} прийняв(-ла) запрошення", "Ви тепер друзі – можете спілкуватися в чаті.")},
}
DEV_RE = [("Android", "Android"), ("iPhone", "iPhone"), ("iPad", "iPad"), ("Windows", "Windows"), ("Mac OS", "Mac"), ("Linux", "Linux")]
BR_RE = [("Edg/", "Edge"), ("OPR/", "Opera"), ("Firefox/", "Firefox"), ("Chrome/", "Chrome"), ("Safari/", "Safari")]

def _tx(key, lang, **kw):
    d = T[key].get(lang) or T[key]["pl"]
    try: return d[0].format(**kw), d[1].format(**kw)
    except (KeyError, IndexError): return d

# ---------- identyfikatory publiczne ----------
_pidc = {"t": 0, "m": {}}
def pid(uid): return hashlib.sha256(("luna-fr:" + uid).encode()).hexdigest()[:12]
def uid_of(p):
    p = str(p or "")[:12]
    if not re.fullmatch(r"[0-9a-f]{12}", p): return None
    now = time.time()
    if p not in _pidc["m"] or now - _pidc["t"] > 300:
        _pidc["m"] = {pid(u): u for u in accounts._accts()}; _pidc["t"] = now
    return _pidc["m"].get(p)

def nick_of(u):
    n = (u or {}).get("nick") or (u or {}).get("name") or ""
    return n.strip() or None

def _ident(uid):
    try:
        import userprof; return userprof.ident(uid)
    except Exception: return {}

def person(uid, A=None):
    """Publiczna karta osoby: nick, styl nicku według planu, ramka partnera. Bez e-maila i uid."""
    u = (A or accounts._accts()).get(uid)
    if not u: return {"pid": pid(uid), "nick": social.DELETED_NICK, "tier": "", "gone": True}
    n = nick_of(u) or ("Luna·" + pid(uid)[:4])
    try: pr = partners.is_partner(uid)
    except Exception: pr = False
    return {"pid": pid(uid), "nick": n, "tier": nicktier.of_uid(uid), "partner": bool(pr), "ini": n[:1].upper(), "ident": _ident(uid)}

# ---------- magazyn ----------
def _ib(uid): return store.get("ib:" + uid, {}) or {}
def _fr(uid):
    f = store.get("fr:" + uid, {}) or {}
    for k in ("friends", "in", "out", "blocked", "unread"): f.setdefault(k, {})
    f.setdefault("prefs", {}); return f
def _save_fr(uid, f): store.put("fr:" + uid, f)
def prefs(uid):
    p = _fr(uid)["prefs"]
    try:
        import battles; bt = battles.notify_on(uid)  # jedno źródło prawdy: ustawienie powiadomień o wyniku z Bitew (bt_notify)
    except Exception: bt = bool(p.get("battles", False))
    return {"invites": p.get("invites", "all"), "receipts": bool(p.get("receipts", True)), "battles": bool(bt),
            "security": bool(p.get("security", True)), "push": bool(p.get("push", True)), "online": presence.vis(uid)}
def _pair(a, b): return "-".join(sorted((a, b)))
def _want(uid, kind):
    try:
        import userprof; return userprof.notif_on(uid, kind)
    except Exception: return True

# ---------- wiadomości systemowe ----------
def deliver(uid, cat, key=None, kw=None, title=None, body=None, link=None, dedupe=None, t=None):
    """Dodaje wiadomość do skrzynki użytkownika. key = szablon z T (tłumaczony przy odczycie), albo własny title/body."""
    if not uid or cat not in CATS: return None
    with _lock:
        d = _ib(uid); M = d.setdefault("m", [])
        if dedupe and any(m.get("dd") == dedupe for m in M): return None
        m = {"id": secrets.token_hex(5), "cat": cat, "t": int(t or time.time()), "r": 0, "a": 0}
        if key: m["k"] = key; m["kw"] = {k: str(v)[:80] for k, v in (kw or {}).items()}
        elif isinstance(title, dict):  # tytuł/treść w 5 językach (wybierane przy odczycie)
            m["ti"] = {k: str(v)[:120] for k, v in title.items()}; m["bo"] = {k: str(v)[:2000] for k, v in (body or {}).items()}
        else: m["ti"] = str(title or "")[:120]; m["bo"] = str(body or "")[:2000]
        if link and str(link).startswith("/"): m["ln"] = str(link)[:200]
        if dedupe: m["dd"] = str(dedupe)[:60]
        M.append(m); d["m"] = M[-MAX_MSGS:]; store.put("ib:" + uid, d)
    if cat in ("important", "friends") and key != "welcome" and notify.push_enabled() and prefs(uid)["push"] and (cat != "friends" or _want(uid, "friends")):
        try:
            ti, bo = _render(m, "pl")
            threading.Thread(target=notify.send_push, args=("manual", ti, bo, "/skrzynka.html"), kwargs={"tag": "inbox", "uid": uid}, daemon=True).start()
        except Exception: pass
    return m

def _render(m, lang):
    if m.get("k") in T: return _tx(m["k"], lang, **m.get("kw", {}))
    if isinstance(m.get("ti"), dict): return (m["ti"].get(lang) or m["ti"].get("pl") or ""), (m["bo"].get(lang) or m["bo"].get("pl") or "")
    return m.get("ti", ""), m.get("bo", "")

def _bcasts(): return store.get("ib_bcast", []) or []
def _in_seg(u, seg):
    if seg == "all": return True
    pl = accounts.plan(u)["plan"]
    return {"free": pl in ("darmowy", "podstawowa"), "premium": pl == "premium", "pro": pl == "pro", "paid": pl in ("premium", "pro"),
            "testers": bool(u.get("tester"))}.get(seg, False)

def _all_for(uid, u):
    d = _ib(uid); st = d.get("bc", {}); out = list(d.get("m", []))
    since = (u.get("created") or 0) - 14 * 86400
    for b in _bcasts():
        if b["t"] < since or not _in_seg(u, b.get("seg", "all")): continue
        s = st.get(b["id"], {})
        if s.get("d"): continue
        out.append(dict(b, r=s.get("r", 0), a=s.get("a", 0), bc=1))
    return out, d

def _ensure_welcome(uid):
    d = _ib(uid)
    if not d.get("w"):
        with _lock:
            d = _ib(uid)
            if d.get("w"): return
            d["w"] = 1; store.put("ib:" + uid, d)
        u = accounts._accts().get(uid) or {}
        deliver(uid, "important", "welcome", dedupe="welcome", t=max(u.get("created") or 0, time.time() - 30 * 86400))

def listing(uid, lang="pl", cat="", box="inbox"):
    u = accounts._accts().get(uid) or {}
    _ensure_welcome(uid)
    M, _ = _all_for(uid, u)
    out = []
    for m in sorted(M, key=lambda x: -x["t"]):
        if box == "archive" and not m.get("a"): continue
        if box != "archive" and m.get("a"): continue
        if cat in CATS and m["cat"] != cat: continue
        ti, bo = _render(m, lang)
        out.append({"id": ("b" if m.get("bc") else "") + m["id"], "cat": m["cat"], "t": m["t"], "title": ti, "body": bo, "link": m.get("ln"),
                    "read": bool(m.get("r")), "archived": bool(m.get("a")), "from": "Luna (AI) · zespół" if m.get("bc") else "Luna"})
    return {"items": out[:200], "unread": unread(uid)}

def act(uid, ids, action):
    if action not in ("read", "unread", "archive", "unarchive", "delete", "read_all"): raise ValueError("bad action")
    ids = [str(i)[:12] for i in (ids or [])][:300]
    with _lock:
        d = _ib(uid); st = d.setdefault("bc", {}); M = d.setdefault("m", [])
        if action == "read_all":
            for m in M: m["r"] = 1
            u = accounts._accts().get(uid) or {}
            for b in _bcasts():
                if _in_seg(u, b.get("seg", "all")): st.setdefault(b["id"], {})["r"] = 1
        else:
            f = {"read": ("r", 1), "unread": ("r", 0), "archive": ("a", 1), "unarchive": ("a", 0), "delete": ("d", 1)}[action]
            for i in ids:
                if i.startswith("b"):
                    st.setdefault(i[1:], {})[f[0]] = f[1]
                elif action == "delete": M[:] = [m for m in M if m["id"] != i]
                else:
                    for m in M:
                        if m["id"] == i: m[f[0]] = f[1]
            d["bc"] = dict(list(st.items())[-300:])
        store.put("ib:" + uid, d)
    return unread(uid)

def unread(uid):
    u = accounts._accts().get(uid) or {}
    M, _ = _all_for(uid, u); c = {k: 0 for k in CATS}
    for m in M:
        if not m.get("r") and not m.get("a"): c[m["cat"]] += 1
    f = _fr(uid); dm = sum(int(v) for v in f["unread"].values()); req = len(f["in"])
    if not _ib(uid).get("w"): c["important"] += 1  # wiadomość powitalna czeka
    return {"total": sum(c.values()) + dm + req, "inbox": sum(c.values()), "cats": c, "chat": dm, "requests": req}

def broadcast(title, body, cat="updates", seg="all", link=None, by="admin", key=None):
    if cat not in CATS: raise ValueError("Zła kategoria.")
    if seg not in SEGMENTS: raise ValueError("Zły segment.")
    def clean(v, n):
        if isinstance(v, dict): return {l: str(v[l]).strip()[:n] for l in LANGS if str(v.get(l) or "").strip()}
        return {"pl": str(v or "").strip()[:n]}
    ti, bo = clean(title, 120), clean(body, 2000)
    if not ti.get("pl") or not bo.get("pl"): raise ValueError("Podaj tytuł i treść (co najmniej po polsku).")
    with _lock:
        B = _bcasts()
        if key and any(b.get("key") == key for b in B): return None
        b = {"id": secrets.token_hex(5), "t": int(time.time()), "cat": cat, "seg": seg, "ti": ti, "bo": bo, "by": by}
        if link and str(link).startswith("/"): b["ln"] = str(link)[:200]
        if key: b["key"] = key
        B.append(b); store.put("ib_bcast", B[-100:])
    return b

def admin_broadcasts():
    return [{"id": b["id"], "t": b["t"], "cat": b["cat"], "seg": b.get("seg", "all"), "title": b["ti"].get("pl"), "by": b.get("by")} for b in reversed(_bcasts())]

def admin_delete_broadcast(bid):
    with _lock: store.put("ib_bcast", [b for b in _bcasts() if b["id"] != bid])

# ---------- Znajomi ----------
def _invite_tok(uid):
    f = _fr(uid)
    if not f.get("inv"):
        with _lock:
            f = _fr(uid); t = secrets.token_urlsafe(9); f["inv"] = t; _save_fr(uid, f)
            I = store.get("fr_inv", {}) or {}; I[t] = uid; store.put("fr_inv", I)
    return f["inv"]

def reset_invite(uid):
    with _lock:
        f = _fr(uid); I = store.get("fr_inv", {}) or {}
        I.pop(f.get("inv", ""), None); store.put("fr_inv", I); f["inv"] = ""; _save_fr(uid, f)
    return _invite_tok(uid)

def invite_owner(tok):
    return (store.get("fr_inv", {}) or {}).get(str(tok or "")[:20])

def find_nick(n):
    n = str(n or "").strip().lstrip("@").lower()[:30]
    if len(n) < 2: raise ValueError("Podaj nick (min. 2 znaki).")
    hits = [u["uid"] for u in accounts._accts().values() if (nick_of(u) or "").lower() == n]
    if not hits: raise ValueError("Nie znaleziono takiego nicku. Poproś o link zaproszenia.")
    if len(hits) > 1: raise ValueError("Ten nick ma kilka osób – poproś o link albo kod QR zaproszenia.")
    return hits[0]

def request(uid, target):
    if not target or target == uid: raise ValueError("Nie możesz zaprosić samego siebie. 🙂")
    if social.banned("u:" + uid): raise PermissionError("Twoje konto ma zablokowane zaproszenia.")
    me = person(uid)
    with _lock:
        fa, fb = _fr(uid), _fr(target)
        if uid in fb["blocked"] or target in fa["blocked"]: raise ValueError("Nie można wysłać zaproszenia do tej osoby.")
        if target in fa["friends"]: raise ValueError("Jesteście już znajomymi.")
        if target in fa["in"]: return accept(uid, target)  # zaproszenie w drugą stronę = akceptacja
        if target in fa["out"]: raise ValueError("Zaproszenie już wysłane – czeka na odpowiedź.")
        if prefs(target)["invites"] == "none": raise ValueError("Ta osoba nie przyjmuje teraz zaproszeń. Może Cię zaprosić sama.")
        if len(fa["friends"]) + len(fa["out"]) >= MAX_FRIENDS: raise ValueError("Osiągnięto limit znajomych.")
        if len(fb["in"]) >= 100: raise ValueError("Ta osoba ma za dużo oczekujących zaproszeń.")
        now = int(time.time()); fa["out"][target] = now; fb["in"][uid] = now
        _save_fr(uid, fa); _save_fr(target, fb)
    deliver(target, "friends", "fr_req", {"nick": me["nick"]}, link="/znajomi.html", dedupe="frq:" + uid + ":" + str(now // 86400))
    return {"status": "sent"}

def accept(uid, other):
    with _lock:
        fa, fb = _fr(uid), _fr(other)
        if other not in fa["in"]: raise ValueError("Nie ma takiego zaproszenia.")
        now = int(time.time())
        fa["in"].pop(other, None); fb["out"].pop(uid, None); fa["out"].pop(other, None); fb["in"].pop(uid, None)
        fa["friends"][other] = now; fb["friends"][uid] = now
        _save_fr(uid, fa); _save_fr(other, fb)
    deliver(other, "friends", "fr_ok", {"nick": person(uid)["nick"]}, link="/znajomi.html#c=" + pid(uid))
    return {"status": "friends"}

def _unlink(uid, other, block=False):
    with _lock:
        fa, fb = _fr(uid), _fr(other)
        for k in ("friends", "in", "out", "close"): fa.setdefault(k, {}).pop(other, None); fb.setdefault(k, {}).pop(uid, None)
        k = _pair(uid, other); fa["unread"].pop(k, None); fb["unread"].pop(k, None)
        if block: fa["blocked"][other] = int(time.time())
        _save_fr(uid, fa); _save_fr(other, fb)

def friend_act(uid, p, action, reason=""):
    other = uid_of(p)
    if not other: raise KeyError("not found")
    if action == "accept": return accept(uid, other)
    if action in ("decline", "cancel", "remove"): _unlink(uid, other); return {"status": "none"}
    if action == "block": _unlink(uid, other, True); return {"status": "blocked"}
    if action == "unblock":
        with _lock: f = _fr(uid); f["blocked"].pop(other, None); _save_fr(uid, f)
        return {"status": "none"}
    if action == "report":
        _report(uid, other, None, reason); return {"status": "reported"}
    if action == "request": return request(uid, other)
    if action in ("close", "unclose"):  # ⭐ „Bliski znajomy” – tylko dla znajomych; decyduje, kto widzi status online
        with _lock:
            f = _fr(uid)
            if other not in f["friends"]: raise PermissionError("Tylko znajomych można oznaczyć jako bliskich.")
            c = f.setdefault("close", {})
            if action == "close": c[other] = int(time.time())
            else: c.pop(other, None)
            _save_fr(uid, f)
        return {"status": "friends", "close": action == "close"}
    raise ValueError("bad action")

def friends(uid, base=""):
    f = _fr(uid); A = accounts._accts()
    def lst(d): return [dict(person(x, A), since=t) for x, t in sorted(d.items(), key=lambda kv: -kv[1])]
    fl = []
    for x, t in sorted(f["friends"].items(), key=lambda kv: -kv[1]):
        c = person(x, A); k = _pair(uid, x)
        c.update(since=t, unread=int(f["unread"].get(k, 0)), last=(f.get("last") or {}).get(k), close=x in (f.get("close") or {}), pr=presence.status(uid, x))
        fl.append(c)
    fl.sort(key=lambda c: -((c.get("last") or {}).get("t") or c["since"]))
    tok = _invite_tok(uid); me = person(uid, A)
    return {"me": me, "has_nick": bool(nick_of(A.get(uid))), "friends": fl, "incoming": lst(f["in"]), "outgoing": lst(f["out"]), "blocked": lst(f["blocked"]),
            "invite": {"token": tok, "url": f"{base}/znajomi.html?zapros={tok}"}, "prefs": prefs(uid)}

PREF_KEYS = {"invites": ("all", "none"), "receipts": (True, False), "battles": (True, False), "security": (True, False), "push": (True, False)}
def set_prefs(uid, d):
    with _lock:
        f = _fr(uid)
        for k, allowed in PREF_KEYS.items():
            if k in d and d[k] in allowed and d[k] is not None: f["prefs"][k] = d[k]
        _save_fr(uid, f)
    if d.get("online") in presence.VIS: presence.set_vis(uid, d["online"])
    if d.get("battles") in (True, False):
        try:
            import battles; battles.set_notify(uid, d["battles"], str(d.get("lang") or "pl")[:2])
        except Exception: pass
    return prefs(uid)

def set_nick(uid, n):
    n = social.nick_ok(n)
    if any(x["uid"] != uid and (nick_of(x) or "").lower() == n.lower() for x in accounts._accts().values()): raise ValueError("Ten nick jest już zajęty – wybierz inny.")
    with accounts._lock:
        a = accounts._accts(); a[uid]["name"] = n; store.put("accounts", a)
    try:
        import userprof
        with userprof._lock:
            P = userprof._P(); r = P.get(uid) or {}; r["nick"] = n; P[uid] = r; store.put("user_profiles", P)  # jeden nick z Mój panel
    except Exception: pass
    _pidc["t"] = 0; return n

# ---------- czat 1:1 ----------
def _dm(k): return store.get("dm:" + k, {}) or {}
def _need_friend(uid, other):
    if not other or other not in _fr(uid)["friends"]: raise PermissionError("Czat jest tylko dla znajomych.")

def dm_list(uid, p, since=0):
    other = uid_of(p); _need_friend(uid, other)
    k = _pair(uid, other); d = _dm(k); M = d.get("m", [])
    hid = set(d.get("hid", {}).get(uid, []))
    last = M[-1]["id"] if M else 0
    pa, pb = prefs(uid), prefs(other)
    with _lock:
        d = _dm(k); rd = d.setdefault("rd", {})
        if last and rd.get(uid, 0) < last: rd[uid] = last; store.put("dm:" + k, d)
        f = _fr(uid)
        if f["unread"].get(k): f["unread"].pop(k, None); _save_fr(uid, f)
    seen = d.get("rd", {}).get(other, 0) if (pa["receipts"] and pb["receipts"]) else None
    out = [dict({"id": m["id"], "mine": m["f"] == uid, "text": m["x"], "t": m["t"]},
                **({"photo": True, "hold": bool(m.get("hold")), "auto": bool(m.get("ar")), "w": m.get("w"), "h": m.get("h")} if m.get("img") else {}))
           for m in M if m["id"] > since and m["id"] not in hid and not m.get("rm")]
    return {"items": out, "last": last, "seen": seen, "peer": dict(person(other), pr=presence.status(uid, other)), "receipts": pa["receipts"] and pb["receipts"]}

def dm_send(uid, p, text):
    other = uid_of(p); _need_friend(uid, other)
    if social.banned("u:" + uid): raise PermissionError("Nie możesz pisać na czacie.")
    if uid in _fr(other)["blocked"]: raise PermissionError("Nie możesz pisać do tej osoby.")
    text = social.check_text(textutil.fix_surrogates(text), DM_LEN)
    if not (livechat.rate_ok("dm:" + uid, 12, 1500) and livechat.rate_ok("dm:" + uid + ":" + other, 8, 600)): raise OverflowError("Za szybko – odczekaj chwilę.")
    k = _pair(uid, other)
    with _lock:
        d = _dm(k); M = d.setdefault("m", []); mid = (M[-1]["id"] + 1) if M else 1
        M.append({"id": mid, "f": uid, "x": text, "t": int(time.time())}); d["m"] = M[-MAX_DM:]
        d.setdefault("rd", {})[uid] = mid; store.put("dm:" + k, d)
        fo = _fr(other); fo["unread"][k] = int(fo["unread"].get(k, 0)) + 1
        lastv = {"t": int(time.time()), "x": text[:60]}
        fo.setdefault("last", {})[k] = lastv; _save_fr(other, fo)
        fm = _fr(uid); fm.setdefault("last", {})[k] = lastv; _save_fr(uid, fm)
    if notify.push_enabled() and prefs(other)["push"] and _want(other, "messages") and int(fo["unread"][k]) == 1:
        threading.Thread(target=notify.send_push, args=("manual", "💬 " + person(uid)["nick"], "Nowa wiadomość na czacie Luny", "/znajomi.html"), kwargs={"tag": "dm", "uid": other}, daemon=True).start()
    return mid

# ---------- zdjęcia w czacie 1:1 (v1.6.7) ----------
# Limity dzienne na serwerze: Podstawowa 5/854 px, Premium 30/1280 px, Pro / Ultra i agentki współpracujące 100/1920 px, moderator bez limitu.
PH_CAPS = {"darmowy": (5, 854), "podstawowa": (5, 854), "premium": (30, 1280), "pro": (100, 1920)}
PH_MAX_IN = 10 * 1024 * 1024
PH_MSG = {"limit": "Dzisiejszy limit zdjęć ({n}) wyczerpany – nawet Luna robi przerwę między sesjami 📸 Wróć jutro{up}.",
          "up_premium": " albo przejdź na Premium (30 zdjęć dziennie)", "up_pro": " albo przejdź na Pro / Ultra (100 zdjęć dziennie)",
          "fast": "Wolniej, paparazzi! 📷 Odczekaj chwilę przed kolejnym zdjęciem.", "blocked_img": "To zdjęcie zostało wcześniej usunięte przez moderatora i nie może zostać wysłane ponownie."}
def ph_caps(plan, admin=False, partner=False):
    if admin: return None, 1920
    if partner: return PH_CAPS["pro"]
    return PH_CAPS.get(plan, PH_CAPS["podstawowa"])
def _day(): return time.strftime("%Y-%m-%d", time.gmtime())
def ph_used(uid):
    u = store.get("dmpu:" + uid, {}) or {}
    return int(u.get("n", 0)) if u.get("d") == _day() else 0
def ph_status(uid, plan, admin=False, partner=False):
    lim, px = ph_caps(plan, admin, partner)
    return {"limit": lim, "px": px, "used": ph_used(uid), "ack": bool(_fr(uid).get("ph_ack")), "max_mb": PH_MAX_IN // (1024 * 1024)}

def dm_photo(uid, p, data_url, plan, admin=False, partner=False, ack=False):
    import base64 as _b64, quality, imgsafe
    other = uid_of(p); _need_friend(uid, other)
    if social.banned("u:" + uid): raise PermissionError("Nie możesz pisać na czacie.")
    if uid in _fr(other)["blocked"] or other in _fr(uid)["blocked"]: raise PermissionError("Nie możesz pisać do tej osoby.")
    f = _fr(uid)
    if not f.get("ph_ack"):
        if not ack: raise LookupError("ack")   # zasada „bez nagości” – potwierdzenie przy pierwszym zdjęciu
        with _lock: f = _fr(uid); f["ph_ack"] = int(time.time()); _save_fr(uid, f)
    m = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)", str(data_url or ""))
    if not m: raise ValueError("Dozwolone są tylko zdjęcia JPG, PNG lub WEBP.")
    raw = _b64.b64decode(m.group(2))
    if len(raw) > PH_MAX_IN: raise ValueError("Zdjęcie jest za duże (maks. 10 MB).")
    if not imgsafe.kind(raw): raise ValueError("Dozwolone są tylko zdjęcia JPG, PNG lub WEBP.")
    lim, px = ph_caps(plan, admin, partner)
    if lim is not None and ph_used(uid) >= lim:
        up = "" if plan == "pro" or partner else (PH_MSG["up_pro"] if plan == "premium" else PH_MSG["up_premium"])
        raise OverflowError(PH_MSG["limit"].format(n=lim, up=up))
    if not admin and not livechat.rate_ok("dmph:" + uid, 6, 2000): raise OverflowError(PH_MSG["fast"])
    blk = set(store.get("dm_ph_block", []) or [])
    hr = hashlib.sha256(raw).hexdigest()
    if hr in blk: raise PermissionError(PH_MSG["blocked_img"])
    import nsfw_filter
    verdict = nsfw_filter.enforce(raw, "dm")   # jawna nagość → Blocked (400, nic nie zapisujemy); granica/niepewność → "review" (wstrzymane do moderatora)
    out = imgsafe.reencode_webp(raw, max_px=px, max_in=PH_MAX_IN)
    ho = hashlib.sha256(out).hexdigest()
    if ho in blk: raise PermissionError(PH_MSG["blocked_img"])
    try: quality.user_photo_mark(raw); quality.user_photo_mark(out)   # odcisk: nigdy jako twarz agentki
    except Exception: pass
    w = h = None
    try:
        import struct
        if out[12:16] == b"VP8X": w = 1 + int.from_bytes(out[24:27], "little"); h = 1 + int.from_bytes(out[27:30], "little")
        elif out[12:16] == b"VP8 ": w, h = struct.unpack("<HH", out[26:30]); w &= 0x3fff; h &= 0x3fff
        elif out[12:16] == b"VP8L": b = int.from_bytes(out[21:25], "little"); w = (b & 0x3fff) + 1; h = ((b >> 14) & 0x3fff) + 1
    except Exception: pass
    iid = secrets.token_hex(8); k = _pair(uid, other)
    store.put("dmimg:" + iid, {"k": k, "b": _b64.b64encode(out).decode(), "hr": hr, "ho": ho, "t": int(time.time())})
    with _lock:
        d = _dm(k); M = d.setdefault("m", []); mid = (M[-1]["id"] + 1) if M else 1
        M.append({"id": mid, "f": uid, "x": "", "img": iid, "w": w, "h": h, "t": int(time.time()), **({"hold": 1, "ar": 1} if verdict != "ok" else {})})
        if len(M) > MAX_DM:
            for old in M[:-MAX_DM]:
                if old.get("img"): store.put("dmimg:" + old["img"], {})
        d["m"] = M[-MAX_DM:]
        d.setdefault("rd", {})[uid] = mid; store.put("dm:" + k, d)
        fo = _fr(other); fo["unread"][k] = int(fo["unread"].get(k, 0)) + 1
        lastv = {"t": int(time.time()), "x": "📷"}
        fo.setdefault("last", {})[k] = lastv; _save_fr(other, fo)
        fm = _fr(uid); fm.setdefault("last", {})[k] = lastv; _save_fr(uid, fm)
        u = store.get("dmpu:" + uid, {}) or {}
        store.put("dmpu:" + uid, {"d": _day(), "n": (int(u.get("n", 0)) if u.get("d") == _day() else 0) + 1})
        if verdict != "ok":   # automatyczny filtr niepewny → kolejka moderatora (odbiorca nic nie widzi do decyzji)
            R = store.get("dm_reports", []) or []
            R.append({"id": secrets.token_hex(5), "t": int(time.time()), "by": uid, "who": uid, "pair": k, "mid": mid, "copy": "[zdjęcie]", "img": iid,
                      "reason": "Automatyczny filtr: do sprawdzenia", "st": "open", "auto": 1})
            store.put("dm_reports", R[-500:])
    if notify.push_enabled() and prefs(other)["push"] and int(fo["unread"][k]) == 1:
        threading.Thread(target=notify.send_push, args=("manual", "📷 " + person(uid)["nick"], "Nowe zdjęcie na czacie Luny", "/znajomi.html"), kwargs={"tag": "dm", "uid": other}, daemon=True).start()
    return mid, verdict

def dm_img(uid, p, mid):
    """Bajty zdjęcia – tylko dla dwóch osób rozmowy; zgłoszone (hold) i usunięte nie są wydawane."""
    import base64 as _b64
    other = uid_of(p)
    if not other: raise KeyError("not found")
    k = _pair(uid, other); d = _dm(k)
    m = next((x for x in d.get("m", []) if x["id"] == int(mid) and x.get("img")), None)
    if not m or m.get("rm") or m.get("hold") or int(mid) in set(d.get("hid", {}).get(uid, [])): raise KeyError("not found")
    if uid in _fr(other)["blocked"] or other in _fr(uid)["blocked"]: raise PermissionError("blocked")
    im = store.get("dmimg:" + m["img"], {}) or {}
    if not im.get("b"): raise KeyError("not found")
    return _b64.b64decode(im["b"])

def admin_report_img(rid):
    import base64 as _b64
    r = next((x for x in (store.get("dm_reports", []) or []) if x["id"] == rid and x.get("img")), None)
    if not r: raise KeyError("not found")
    im = store.get("dmimg:" + r["img"], {}) or {}
    if not im.get("b"): raise KeyError("not found")
    return _b64.b64decode(im["b"])

def _ph_remove(iid, block=False):
    im = store.get("dmimg:" + iid, {}) or {}
    if block and im:
        B = store.get("dm_ph_block", []) or []
        for h_ in (im.get("hr"), im.get("ho")):
            if h_ and h_ not in B: B.append(h_)
        store.put("dm_ph_block", B[-5000:])
    store.put("dmimg:" + iid, {})

def _report(uid, other, mid, reason):
    copy = None; img = None; k = _pair(uid, other)
    if mid is not None:
        with _lock:
            d = _dm(k); m = next((m for m in d.get("m", []) if m["id"] == int(mid) and m["f"] == other), None)
            if not m: raise KeyError("not found")
            copy = m["x"] if not m.get("img") else "[zdjęcie]"; img = m.get("img")
            if img: m["hold"] = 1   # zgłoszone zdjęcie znika u obu stron do decyzji moderatora
            h = d.setdefault("hid", {}).setdefault(uid, [])
            if m["id"] not in h: h.append(m["id"]); d["hid"][uid] = h[-200:]
            store.put("dm:" + k, d)
    R = store.get("dm_reports", []) or []
    if any(r["by"] == uid and r["who"] == other and r.get("mid") == mid and r["st"] == "open" for r in R): return
    R.append({"id": secrets.token_hex(5), "t": int(time.time()), "by": uid, "who": other, "pair": k, "mid": mid, "copy": copy, "img": img,
              "reason": re.sub(r"[<>\x00-\x1f]", "", str(reason or ""))[:200], "st": "open"})
    store.put("dm_reports", R[-500:])

def dm_report(uid, p, mid, reason=""):
    other = uid_of(p)
    if not other: raise KeyError("not found")
    _report(uid, other, int(mid), reason)

def admin_reports():
    A = accounts._accts()
    return [{"id": r["id"], "t": r["t"], "reporter": "🤖 filtr automatyczny" if r.get("auto") else person(r["by"], A)["nick"], "auto": bool(r.get("auto")), "reported": person(r["who"], A)["nick"], "kind": "message" if r.get("mid") else "account",
             "message": r.get("copy"), "reason": r.get("reason"), "status": r["st"], "photo": bool(r.get("img")),
             "img_url": f"/api/admin/inbox/img?id={r['id']}" if r.get("img") and r["st"] == "open" else None} for r in reversed(store.get("dm_reports", []) or [])][:200]

def admin_report_act(rid, action):
    with _lock:
        R = store.get("dm_reports", []) or []; r = next((x for x in R if x["id"] == rid), None)
        if not r: raise KeyError("not found")
        if action == "remove" and r.get("mid"):
            d = _dm(r["pair"])
            for m in d.get("m", []):
                if m["id"] == r["mid"]: m["rm"] = 1; m["x"] = ""
            store.put("dm:" + r["pair"], d)
            if r.get("img"): _ph_remove(r["img"], block=True)
        elif action == "dismiss" and r.get("img"):
            d = _dm(r["pair"])
            for m in d.get("m", []):
                if m["id"] == r["mid"]: m.pop("hold", None)
            store.put("dm:" + r["pair"], d)
        elif action == "ban":
            B = social._bans(); B.add("u:" + r["who"]); store.put("social_bans", sorted(B))
        elif action != "dismiss": raise ValueError("bad action")
        r["st"] = action; store.put("dm_reports", R)
    return admin_reports()

# ---------- integracje ----------
def on_login(uid, ua=""):
    if not prefs(uid)["security"]: return
    dev = next((n for k, n in DEV_RE if k in (ua or "")), "?"); br = next((n for k, n in BR_RE if k in (ua or "")), "")
    deliver(uid, "important", "login", {"dev": (br + " · " + dev) if br else dev}, dedupe="lg:" + dev + br + ":" + time.strftime("%Y%m%d%H"))

def on_plan(uid, plan_name, until):
    deliver(uid, "important", "plan_on", {"plan": plan_name, "until": time.strftime("%d.%m.%Y", time.localtime(until))}, link="/app.html#plans", dedupe="po:" + str(until))

def on_plan_expiring(uid, plan_name, until, tag):
    deliver(uid, "important", "plan_exp", {"plan": plan_name, "until": time.strftime("%d.%m.%Y", time.localtime(until)), "when": "za 7 dni" if tag == "7d" else "jutro"},
            link="/app.html#plans", dedupe="pe:" + tag + ":" + str(until))

def on_moderation(kind, item, action):
    a = str((item or {}).get("author", ""))
    if kind != "post" or not a.startswith("u:") or action not in ("approve", "reject"): return
    deliver(a[2:], "important", "mod_ok" if action == "approve" else "mod_no", link="/scianka.html" if action == "approve" else None, dedupe="md:" + str(item.get("id")) + action)

def battle_tick():
    """Po zakończeniu bitwy: wynik do skrzynek osób, które włączyły „Wyniki Bitew”, i do twórczyń obu agentek."""
    try: import battles
    except Exception: return 0
    st = battles._state(); H = st.get("hist", [])[:10]
    if not H: return 0
    done = set(store.get("ib_bt_done", []) or []); n = 0
    new = [h for h in H if h["id"] not in done and h.get("reason") == "end"]
    if not new:
        if not done: store.put("ib_bt_done", [h["id"] for h in H])
        return 0
    owners = {e["id"]: e["uid"] for e in battles._entries()}
    for h in new:
        done.add(h["id"])
        win = h.get("winner"); a, b = h["a"]["name"], h["b"]["name"]
        kw = {"a": a, "b": b, "va": h["va"], "vb": h["vb"], "win": h[win]["name"] if win else ""}
        targets = {u for u in (owners.get(h["a"]["id"]), owners.get(h["b"]["id"])) if u}
        try: subs = set(battles._nsubs())
        except Exception: subs = set()
        for uid in accounts._accts():
            if uid in targets or uid in subs or _fr(uid)["prefs"].get("battles"):
                deliver(uid, "battles", "bt_res" if win else "bt_draw", kw, link="/bitwy.html", dedupe="bt:" + h["id"]); n += 1
    store.put("ib_bt_done", list(done)[-100:])
    return n

WHATS_NEW = {}  # wersja -> (tytuł, treść) w 5 językach; ustawiane przez serwer przy starcie
def announce_version(ver, items):
    if not items: return None
    return broadcast(items[0], items[1], "updates", "all", "/app.html", by="system", key="ver:" + ver)

# ---------- RODO ----------
def export(uid):
    A = accounts._accts(); f = _fr(uid); M, _ = _all_for(uid, A.get(uid) or {})
    conv = []
    for o in list(f["friends"]) + list(f["blocked"]):
        d = _dm(_pair(uid, o))
        if d.get("m"): conv.append({"with": person(o, A)["nick"], "my_messages": [{"t": m["t"], "text": m["x"] or ("[zdjęcie]" if m.get("img") else "")} for m in d["m"] if m["f"] == uid]})
    return {"inbox": [{"t": m["t"], "cat": m["cat"], "title": _render(m, "pl")[0], "body": _render(m, "pl")[1]} for m in M],
            "friends": [person(x, A)["nick"] for x in f["friends"]], "friend_requests_sent": [person(x, A)["nick"] for x in f["out"]],
            "blocked": [person(x, A)["nick"] for x in f["blocked"]], "settings": prefs(uid), "chats": conv,
            "reports_made": [{"t": r["t"], "reason": r.get("reason")} for r in (store.get("dm_reports", []) or []) if r["by"] == uid]}

def delete_user(uid):
    """Usuwa skrzynkę, znajomości, rozmowy (u obu stron), link zaproszenia i zgłoszenia złożone przez osobę."""
    with _lock:
        f = _fr(uid)
        for o in set(f["friends"]) | set(f["in"]) | set(f["out"]) | set(f["blocked"]):
            fo = _fr(o)
            for k in ("friends", "in", "out", "blocked"): fo[k].pop(uid, None)
            fo["unread"].pop(_pair(uid, o), None); (fo.get("last") or {}).pop(_pair(uid, o), None); _save_fr(o, fo)
            for m in _dm(_pair(uid, o)).get("m", []):
                if m.get("img"): store.put("dmimg:" + m["img"], {})
            store.put("dm:" + _pair(uid, o), {})
        I = store.get("fr_inv", {}) or {}
        if f.get("inv") in I: I.pop(f["inv"]); store.put("fr_inv", I)
        store.put("fr:" + uid, {}); store.put("ib:" + uid, {})
        R = [r for r in (store.get("dm_reports", []) or []) if r["by"] != uid]
        for r in R:
            if r["who"] == uid: r["copy"] = None
        store.put("dm_reports", R)
    _pidc["t"] = 0

# ---------- QR ----------
def qr_svg(url):
    try: import segno
    except Exception: return None
    import io
    b = io.BytesIO(); segno.make(url, error="m").save(b, kind="svg", scale=6, border=2, dark="#0b0705", light="#ffffff", xmldecl=False)
    return b.getvalue()

# ---------- HTTP ----------
TOKEN_OK = lambda t: False  # serwer podstawia weryfikację tokenu moderatora
PLAN_OF = lambda h, uid: ("podstawowa", False, False)  # serwer podstawia: (plan, moderator?, agentka współpracująca?)
def _lang(h, u):
    import api_i18n
    return api_i18n.req_lang(u.query, h.headers) or "pl"

def handle_get(h, u):
    from urllib.parse import parse_qs
    p = u.path; q = parse_qs(u.query)
    if p == "/api/admin/inbox/img":
        if not TOKEN_OK(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        try: b = admin_report_img((q.get("id") or [""])[0][:12])
        except KeyError: return h._json({"error": "not found"}, 404)
        h.send_response(200); h.send_header("Content-Type", "image/webp"); h.send_header("Content-Length", str(len(b)))
        h.send_header("Cache-Control", "private, no-store"); h.end_headers(); h.wfile.write(b); return True
    if p == "/api/admin/inbox":
        if not TOKEN_OK(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        return h._json({"broadcasts": admin_broadcasts(), "reports": admin_reports(), "segments": SEGMENTS, "categories": CATS})
    a = h._acct()
    if p == "/api/inbox/unread":
        if not a: return h._json({"login": False, "total": 0})
        return h._json(dict(unread(a[0]["uid"]), login=True))
    if not a: return h._json({"error": "Zaloguj się, aby otworzyć Skrzynkę.", "login": True}, 401)
    uid = a[0]["uid"]; base = notify.PUBLIC_URL.rstrip("/")
    if p == "/api/inbox":
        return h._json(listing(uid, _lang(h, u), (q.get("cat") or [""])[0], (q.get("box") or ["inbox"])[0]))
    if p == "/api/friends":
        return h._json(friends(uid, base))
    if p == "/api/friends/settings":
        f = friends(uid, base)
        return h._json({"keys": {"invites": {"value": f["prefs"]["invites"], "options": ["all", "none"]}, "receipts": {"value": f["prefs"]["receipts"]},
                                 "battles": {"value": f["prefs"]["battles"]}, "security": {"value": f["prefs"]["security"]}, "push": {"value": f["prefs"]["push"]},
                                 "online": {"value": f["prefs"]["online"], "options": list(presence.VIS)}},
                        "blocked": f["blocked"], "routes": {"inbox": "/skrzynka.html", "friends": "/znajomi.html", "privacy": "/znajomi.html#prywatnosc"}})
    if p == "/api/friends/invite":
        tok = (q.get("t") or [""])[0]; o = invite_owner(tok)
        if not o: return h._json({"error": "Ten link zaproszenia jest nieaktualny."}, 404)
        f = _fr(uid)
        return h._json({"person": person(o), "self": o == uid, "status": "friends" if o in f["friends"] else "sent" if o in f["out"] else "incoming" if o in f["in"] else "none"})
    if p == "/api/friends/qr.svg":
        svg = qr_svg(f"{base}/znajomi.html?zapros={_invite_tok(uid)}")
        if not svg: return h._json({"error": "QR niedostępny"}, 404)
        h.send_response(200); h.send_header("Content-Type", "image/svg+xml"); h.send_header("Content-Length", str(len(svg)))
        h.send_header("Cache-Control", "private, no-store"); h.end_headers(); h.wfile.write(svg); return True
    if p == "/api/dm/img":
        try: b = dm_img(uid, (q.get("pid") or [""])[0], int((q.get("mid") or ["0"])[0] or 0))
        except (KeyError, ValueError, PermissionError): return h._json({"error": "not found"}, 404)
        h.send_response(200); h.send_header("Content-Type", "image/webp"); h.send_header("Content-Length", str(len(b)))
        h.send_header("Cache-Control", "private, no-store"); h.send_header("X-Content-Type-Options", "nosniff"); h.end_headers(); h.wfile.write(b); return True
    if p == "/api/dm/photo/status":
        pl, adm, pt = PLAN_OF(h, uid)
        return h._json(ph_status(uid, pl, adm, pt))
    if p == "/api/dm":
        s = (q.get("since") or ["0"])[0]
        try: return h._json(dm_list(uid, (q.get("pid") or [""])[0], int(s) if s.isdigit() else 0))
        except PermissionError as e: return h._json({"error": str(e)}, 403)
    return None

def handle_post(h, u, data):
    p = u.path; ip = h._ip()
    if p.startswith("/api/admin/inbox"):
        if not TOKEN_OK(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        try:
            if p == "/api/admin/inbox/broadcast":
                if data.get("action") == "delete": admin_delete_broadcast(str(data.get("id", ""))[:12]); return h._json({"ok": True, "broadcasts": admin_broadcasts()})
                b = broadcast(data.get("title"), data.get("body"), data.get("cat") or "updates", data.get("segment") or "all", data.get("link"))
                return h._json({"ok": True, "id": b["id"], "broadcasts": admin_broadcasts()})
            if p == "/api/admin/inbox/report": return h._json({"ok": True, "reports": admin_report_act(str(data.get("id", ""))[:12], data.get("action"))})
        except KeyError: return h._json({"error": "not found"}, 404)
        except ValueError as e: return h._json({"error": str(e)}, 400)
        return h._json({"error": "not found"}, 404)
    a = h._acct()
    if not a: return h._json({"error": "Zaloguj się.", "login": True}, 401)
    if not h._csrf_ok(a[1]): return h._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
    uid = a[0]["uid"]
    try:
        if p == "/api/inbox/act": return h._json({"ok": True, "unread": act(uid, data.get("ids"), data.get("action"))})
        if p == "/api/friends/request":
            if not (livechat.rate_ok("frq:" + uid, 6, 60) and livechat.rate_ok("frq:" + ip, 10, 120)): return h._json({"error": "Za dużo zaproszeń – spróbuj później."}, 429)
            t = invite_owner(data.get("invite")) if data.get("invite") else (uid_of(data.get("pid")) if data.get("pid") else find_nick(data.get("nick")))
            if not t: return h._json({"error": "Ten link zaproszenia jest nieaktualny."}, 404)
            return h._json({"ok": True, **request(uid, t), "person": person(t)})
        if p == "/api/friends/act":
            if not livechat.rate_ok("fra:" + uid, 30, 600): return h._json({"error": "Za szybko."}, 429)
            return h._json({"ok": True, **friend_act(uid, data.get("pid"), data.get("action"), data.get("reason"))})
        if p == "/api/friends/prefs": return h._json({"ok": True, "prefs": set_prefs(uid, data)})
        if p == "/api/friends/invite/reset": return h._json({"ok": True, "token": reset_invite(uid)})
        if p == "/api/friends/nick":
            if not livechat.rate_ok("nick:" + uid, 3, 10): return h._json({"error": "Za szybko."}, 429)
            return h._json({"ok": True, "nick": set_nick(uid, data.get("nick"))})
        if p == "/api/dm":
            mid = dm_send(uid, data.get("pid"), data.get("text"))
            return h._json({"ok": True, "id": mid, **dm_list(uid, data.get("pid"), int(data.get("since") or 0))})
        if p == "/api/dm/photo":
            pl, adm, pt = PLAN_OF(h, uid)
            try: mid, verdict = dm_photo(uid, data.get("pid"), data.get("image"), pl, adm, pt, data.get("ack") is True)
            except LookupError: return h._json({"error": "ack", "need_ack": True}, 409)
            except OverflowError as e: return h._json({"error": str(e), "limit": True, **ph_status(uid, pl, adm, pt)}, 429)
            import nsfw_filter
            return h._json({"ok": True, "id": mid, **({"review": nsfw_filter.review_message()} if verdict != "ok" else {}), "photo": ph_status(uid, pl, adm, pt), **dm_list(uid, data.get("pid"), int(data.get("since") or 0))})
        if p == "/api/dm/report":
            if not livechat.rate_ok("dmr:" + uid, 5, 40): return h._json({"error": "Za dużo zgłoszeń."}, 429)
            dm_report(uid, data.get("pid"), data.get("mid"), data.get("reason")); return h._json({"ok": True})
    except OverflowError as e: return h._json({"error": str(e)}, 429)
    except PermissionError as e: return h._json({"error": str(e)}, 403)
    except KeyError: return h._json({"error": "not found"}, 404)
    except (ValueError, TypeError) as e: return h._json({"error": str(e) if isinstance(e, ValueError) else "bad request"}, 400)
    return h._json({"error": "not found"}, 404)
