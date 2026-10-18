"""Wykrywanie fałszywych kont i botów. Podejrzane konta są oznaczane i UKRYWANE W CIENIU: ich polubienia,
wyświetlenia i komentarze nie liczą się w publicznych licznikach (autor nadal widzi swoje). Nic nie jest kasowane
automatycznie – usunięcie lub przywrócenie robi właściciel w panelu. Bez przechowywania IP: grupowanie po dziennym skrócie."""
import collections, difflib, hashlib, os, re, secrets, threading, time, datetime, json, urllib.request, urllib.parse
import store
_lock = threading.Lock()
THRESH = 5
DISPOSABLE = set("""10minutemail.com 10minutemail.net 20minutemail.com 33mail.com anonbox.net anonymbox.com burnermail.io byom.de
dispostable.com discard.email discardmail.com discardmail.de dropmail.me emailondeck.com emailfake.com email-fake.com fakeinbox.com
fakemail.net filzmail.com getairmail.com getnada.com nada.email guerrillamail.com guerrillamail.net guerrillamail.org guerrillamail.biz
guerrillamail.de guerrillamailblock.com sharklasers.com grr.la pokemail.net spam4.me harakirimail.com incognitomail.org inboxbear.com
inboxkitten.com jetable.org mailcatch.com maildrop.cc mailinator.com mailinator.net mailinator2.com mailnesia.com mailnull.com
mailpoof.com mailsac.com mailtemp.net mintemail.com moakt.com mohmal.com mytemp.email mytrashmail.com no-spam.ws nowmymail.com
oneoff.email spambox.us spamgourmet.com spamex.com tempail.com tempmail.com temp-mail.org temp-mail.io tempmail.net tempmailo.com
tempinbox.com tempr.email throwawaymail.com trashmail.com trashmail.de trashmail.net trashmail.io wegwerfmail.de wegwerfmail.net
yopmail.com yopmail.fr yopmail.net cool.fr.nf jetable.fr.nf courriel.fr.nf moncourrier.fr.nf monemail.fr.nf monmail.fr.nf
mailforspam.com spamfree24.org trbvm.com tmail.ws tmpmail.org tmpmail.net emltmp.com 1secmail.com 1secmail.net 1secmail.org
minuteinbox.com fakemailgenerator.com mail.tm mailbox.in.ua tempmailaddress.com luxusmail.org owlymail.com mailgun.top
gufum.com kzccv.com lyricspad.net tempmail.plus mailto.plus fexpost.com fexbox.org rover.info inpwa.com""".split())
UA_BOT = re.compile(r"(?i)headless|phantom|selenium|puppeteer|playwright|webdriver|python|curl|wget|httpclient|okhttp|go-http|axios|node-fetch|scrapy|bot\b|crawler|spider")
REASONS = {"headless_ua": "Automatyczna przeglądarka / bot (User-Agent)", "burst_votes": "Seria polubień w kilka sekund",
           "burst_comments": "Seria komentarzy w kilka sekund", "dup_comment": "Powtarzany komentarz (ta sama treść)",
           "near_dup_comment": "Prawie identyczny komentarz", "multi_account": "Wiele kont z jednej sieci (skrót dzienny)",
           "signup_rate": "Za dużo rejestracji z jednej sieci", "disposable_email": "Jednorazowy adres e-mail",
           "honeypot": "Wypełnione ukryte pole formularza", "too_fast": "Formularz wypełniony nienaturalnie szybko",
           "same_text_many": "Ta sama treść od wielu kont", "view_bot": "Wyświetlenia odrzucone przez filtr botów"}
_recent = collections.defaultdict(collections.deque)   # (kind, ak) -> czasy
_net = {}                                             # dzień -> {skrót sieci: set(ak)}
_cache = {"t": 0, "hidden": set(), "unver": set()}
def _day(): return datetime.date.today().isoformat()
def _salt():
    s = store.get("ab_salt", {}) or {}
    d = _day()
    if d not in s: s = {d: secrets.token_hex(16)}; store.put("ab_salt", s)
    return s[d]
def net_hash(ip): return hashlib.sha256((_salt() + "|" + (ip or "")).encode()).hexdigest()[:12]
def _all(): return store.get("suspects", {}) or {}
def flag(ak, reason, pts, label=None):
    if not ak: return
    with _lock:
        S = _all(); e = S.get(ak) or {"score": 0, "reasons": {}, "t": int(time.time()), "status": "ok", "label": ""}
        if e.get("status") == "restored": return       # właściciel przywrócił – nie oznaczamy ponownie automatycznie
        e["reasons"][reason] = e["reasons"].get(reason, 0) + 1
        e["score"] = min(100, e["score"] + pts); e["last"] = int(time.time())
        if label and not e.get("label"): e["label"] = str(label)[:60]
        if e["score"] >= THRESH and e["status"] != "flagged": e["status"] = "flagged"; e["flagged_at"] = int(time.time())
        S[ak] = e; store.put("suspects", S)
        _cache["t"] = 0
def _unverified():
    a = store.get("accounts", {}) or {}
    return {"u:" + u for u, x in a.items() if not x.get("verified")}
def excluded():
    """Klucze autorów, których głosy/komentarze nie liczą się publicznie (ukryci w cieniu + konta bez potwierdzonego e-maila)."""
    if time.time() - _cache["t"] > 10:
        S = _all(); _cache["hidden"] = {k for k, e in S.items() if e.get("status") == "flagged"}
        try:
            import notify; ver_on = notify.email_enabled()
        except Exception: ver_on = False
        # jak w Bitwach: konta bez potwierdzonego e-maila wyłączamy z liczenia tylko wtedy, gdy potwierdzanie e-maili naprawdę działa
        _cache["unver"] = _unverified() if ver_on else set(); _cache["t"] = time.time()
    return _cache["hidden"] | _cache["unver"]
def hidden(ak): excluded(); return ak in _cache["hidden"]
def burst(kind, ak, n, secs):
    now = time.time(); q = _recent[(kind, ak)]; q.append(now)
    while q and now - q[0] > secs: q.popleft()
    if len(q) > n: q.clear(); return True
    return False
def check_ua(ak, ua, label=None):
    if UA_BOT.search(ua or "") or not ua: flag(ak, "headless_ua", THRESH, label); return True
    return False
def on_write(ak, ip, ua, label=None):
    """Wspólne sygnały przy każdej akcji zapisu (głos, komentarz, wpis)."""
    check_ua(ak, ua, label)
    d = _day(); h = net_hash(ip)
    with _lock:
        for k in [k for k in _net if k != d]: _net.pop(k)
        s = _net.setdefault(d, {}).setdefault(h, set()); new = ak not in s; s.add(ak); many = len(s) > 5
    if new and many: flag(ak, "multi_account", 3, label)
def on_vote(ak, ip, ua):
    on_write(ak, ip, ua)
    if burst("v", ak, 12, 15): flag(ak, "burst_votes", THRESH)
def _norm(t): return re.sub(r"\W+", " ", str(t).lower()).strip()
def on_comment(ak, ip, ua, text, nick, comments):
    on_write(ak, ip, ua, nick)
    if burst("c", ak, 3, 30): flag(ak, "burst_comments", THRESH, nick)
    n = _norm(text)
    if len(n) < 6: return
    now = time.time()
    mine = [c for c in comments if c.get("author") == ak and now - c.get("t", 0) < 86400][-20:]
    if any(_norm(c["text"]) == n for c in mine): flag(ak, "dup_comment", 3, nick)
    elif any(difflib.SequenceMatcher(None, _norm(c["text"]), n).ratio() > .9 for c in mine): flag(ak, "near_dup_comment", 2, nick)
    others = {c.get("author") for c in comments if c.get("author") != ak and now - c.get("t", 0) < 86400 and _norm(c.get("text", "")) == n}
    if len(n) > 12 and len(others) >= 2:
        flag(ak, "same_text_many", 3, nick)
        for o in others: flag(o, "same_text_many", 3)
def signup_check(email, ip, ua, d):
    """Zwraca (ok, komunikat). Odrzuca: honeypot, zbyt szybkie wypełnienie, jednorazowy e-mail, limit rejestracji z sieci."""
    if d.get("website"): return False, "honeypot"
    try: ft = float(d.get("fill_ms") or 0)
    except (TypeError, ValueError): ft = 0
    if d.get("fill_ms") is not None and ft < 2500: return False, "Za szybko – spróbuj ponownie za chwilę."
    dom = str(email).rsplit("@", 1)[-1].lower().strip()
    if dom in DISPOSABLE or any(dom.endswith("." + x) for x in DISPOSABLE): return False, "Jednorazowe adresy e-mail nie są obsługiwane – użyj swojego stałego adresu."
    h = net_hash(ip); R = store.get("ab_signups", {}) or {}; d0 = _day()
    R = {k: v for k, v in R.items() if k.startswith(d0)}
    if R.get(d0 + h, 0) >= 3: return False, "Za dużo rejestracji z tej sieci – spróbuj jutro."
    R[d0 + h] = R.get(d0 + h, 0) + 1; store.put("ab_signups", R)
    return True, ""
TS_SECRET = os.getenv("TURNSTILE_SECRET", "").strip(); TS_SITE = os.getenv("TURNSTILE_SITEKEY", "").strip()
def turnstile_on(): return bool(TS_SECRET and TS_SITE)
def turnstile_ok(token, ip):
    if not turnstile_on(): return True
    try:
        body = urllib.parse.urlencode({"secret": TS_SECRET, "response": token or "", "remoteip": ip or ""}).encode()
        r = json.load(urllib.request.urlopen("https://challenges.cloudflare.com/turnstile/v0/siteverify", body, timeout=8))
        return bool(r.get("success"))
    except Exception: return False
def admin_list():
    S = _all(); out = []
    for ak, e in S.items():
        if e.get("status") == "ok" and e.get("score", 0) < 2: continue
        out.append({"ak": ak, "kind": "konto" if ak.startswith("u:") else "urządzenie", "label": e.get("label", ""), "score": e.get("score", 0),
                    "status": e.get("status"), "reasons": [{"code": k, "label": REASONS.get(k, k), "n": n} for k, n in e.get("reasons", {}).items()],
                    "t": e.get("flagged_at") or e.get("t")})
    out.sort(key=lambda x: (x["status"] != "flagged", -x["score"]))
    return out
def restore(ak):
    with _lock:
        S = _all(); e = S.get(ak)
        if e: e["status"] = "restored"; e["score"] = 0; S[ak] = e; store.put("suspects", S)
        _cache["t"] = 0
def forget(ak):
    with _lock:
        S = _all(); S.pop(ak, None); store.put("suspects", S); _cache["t"] = 0
