# -*- coding: utf-8 -*-
"""Pomoc na żywo (v1.6.6): pierwsza linia to Asystent AI (helpbot.py), potem „Porozmawiaj z moderatorem”.
Uczciwie: rozmowa na żywo trafia do człowieka TYLKO wtedy, gdy moderator ma otwarty widok /admin-support.html
z włączonym „Jestem dostępny” (heartbeat co ~20 s). W przeciwnym razie: „Moderator jest teraz offline – zostaw wiadomość”
i formularz „Napisz do moderatora” (tickets.submit_support). Nigdy nie obiecujemy ludzi 24/7.
Tożsamość wsparcia: „Zespół Luny · Moderator” – nigdy prawdziwe imię ani dane właściciela.
Magazyn: sesje w pamięci + luna_kv „sup_live” (zapis przy zmianach), zgłoszenia w „tickets”."""
import re, secrets, threading, time
import store, tickets, notify, livechat, antibot

ONLINE_WINDOW = 60          # s od ostatniego heartbeat
SID_RE = re.compile(r"[0-9a-f]{24}")
MAX_SESS, MAX_MSGS, MAX_TEXT = 300, 200, 1000
MOD_NAME = "Zespół Luny · Moderator"
_lock = threading.RLock()
_presence = {"seen": 0, "available": False}
_S = None

def _sessions():
    global _S
    if _S is None:
        v = store.get("sup_live", {}) or {}
        _S = v if isinstance(v, dict) else {}
    return _S

def _save():
    try: store.put("sup_live", _sessions())
    except Exception: pass

def online():
    return bool(_presence["available"]) and time.time() - _presence["seen"] < ONLINE_WINDOW

def ping(available):
    with _lock:
        _presence["seen"] = time.time(); _presence["available"] = bool(available)
    return online()

def _msg(frm, text):
    return {"id": secrets.token_hex(4), "from": frm, "text": text, "t": int(time.time() * 1000)}

def _clean(t): return livechat.clean_text(t, MAX_TEXT)

def start(uid, lang, transcript):
    """Nowa sesja na żywo. transcript = rozmowa z Asystentem AI (tylko gdy użytkownik zgodził się ją dołączyć)."""
    if not online(): raise LookupError("offline")
    sid = secrets.token_hex(12)
    with _lock:
        S = _sessions()
        if len(S) >= MAX_SESS:
            for k in sorted(S, key=lambda k: S[k].get("updated", 0))[:len(S) - MAX_SESS + 1]: S.pop(k, None)
        ctx = []
        for m in (transcript or [])[-20:]:
            if isinstance(m, dict):
                ctx.append(("Użytkownik: " if m.get("who") == "me" else "Asystent AI: ") + tickets._SENS.sub("***", _clean(m.get("t")))[:400])
        S[sid] = {"sid": sid, "uid": uid or "", "lang": lang, "created": int(time.time()), "updated": int(time.time()), "closed": False,
                  "unread": 0, "ctx": "\n".join(ctx)[:6000], "msgs": []}
        _save()
    return sid

def user_send(sid, text):
    text = _clean(text)
    if not text: raise ValueError("empty")
    text = tickets._SENS.sub("***", text)
    with _lock:
        s = _sessions().get(sid)
        if not s or s.get("closed"): raise KeyError("closed")
        s["msgs"].append(_msg("me", text)); s["msgs"] = s["msgs"][-MAX_MSGS:]
        s["unread"] = s.get("unread", 0) + 1; s["updated"] = int(time.time()); _save()
        return s["msgs"][-1]

def user_poll(sid, since=0):
    s = _sessions().get(sid)
    if not s: raise KeyError("gone")
    return {"msgs": [m for m in s["msgs"] if m["t"] > since], "closed": bool(s.get("closed")), "online": online(), "mod": MOD_NAME}

def admin_list():
    S = _sessions(); out = []
    for s in sorted(S.values(), key=lambda x: -x.get("updated", 0)):
        last = s["msgs"][-1] if s["msgs"] else {}
        out.append({"sid": s["sid"], "who": "Zalogowany użytkownik" if s.get("uid") else "Gość", "lang": s.get("lang"), "updated": s.get("updated"),
                    "closed": s.get("closed"), "unread": s.get("unread", 0), "last": (last.get("text") or "")[:100], "count": len(s["msgs"])})
    return out[:100]

def admin_conv(sid):
    with _lock:
        s = _sessions().get(sid)
        if not s: raise KeyError("gone")
        if s.get("unread"): s["unread"] = 0; _save()
        return {k: s[k] for k in ("sid", "lang", "created", "updated", "closed", "ctx", "msgs")} | {"who": "Zalogowany użytkownik" if s.get("uid") else "Gość"}

def admin_reply(sid, text):
    text = _clean(text)
    if not text: raise ValueError("empty")
    with _lock:
        s = _sessions().get(sid)
        if not s: raise KeyError("gone")
        s["msgs"].append(_msg("mod", text)); s["msgs"] = s["msgs"][-MAX_MSGS:]; s["updated"] = int(time.time()); _save()
    ping(True)

def admin_close(sid, delete=False):
    with _lock:
        S = _sessions()
        if delete: S.pop(sid, None)
        elif sid in S: S[sid]["closed"] = True; S[sid]["msgs"].append(_msg("system", "closed"))
        _save()

def _email_admin(tid, d):
    to = __import__("os").getenv("SUPPORT_ADMIN_EMAIL", "").strip()
    if not (to and notify.email_enabled()): return
    def go():
        try:
            body = f"Nowe zgłoszenie {tid} ({tickets.SUP_LABELS.get(d.get('category'), '')}): {str(d.get('title', ''))[:120]}\nOdpowiedz w /admin-support.html"
            notify._send_email(to, f"Luna – nowe zgłoszenie {tid}", body, "<p>" + body.replace("<", "&lt;").replace("\n", "<br>") + "</p>")
        except Exception: pass
    threading.Thread(target=go, daemon=True).start()

ERR = {"fast": "Za szybko – odczekaj sekundę i wyślij ponownie.", "cat": "Wybierz kategorię sprawy.", "title": "Tytuł: od 5 do 120 znaków.", "desc": "Opis: od 20 do 4000 znaków.",
       "email": "Podaj poprawny e-mail albo zostaw pole puste.", "shot_type": "Zrzut ekranu musi być obrazem (JPG, PNG lub WEBP).",
       "shot_size": "Zrzut ekranu jest za duży (maks. 5 MB).", "shot_nsfw": "Tego zrzutu nie przyjmiemy – filtr nagości mówi stanowcze „nie”. Wyślij inny obraz.", "captcha": "Potwierdź, że nie jesteś botem."}

# ---------- HTTP ----------
TOKEN_OK = lambda t: False
MOD_PUSH = lambda title, body: None

def handle_get(h, u):
    from urllib.parse import parse_qs
    p = u.path; q = {k: v[0] for k, v in parse_qs(u.query).items()}
    if p == "/api/support/status":
        return h._json({"online": online(), "mod": MOD_NAME, "cats": list(tickets.SUP_CATS),
                        "login": bool(h._acct())})
    if p == "/api/support/live":
        sid = q.get("sid", "")
        if not SID_RE.fullmatch(sid): return h._json({"error": "bad id"}, 400)
        try: return h._json(user_poll(sid, int(q.get("since", "0") or 0) if str(q.get("since", "0")).isdigit() else 0))
        except KeyError: return h._json({"error": "gone", "closed": True, "online": online()}, 404)
    if p == "/api/support/mine":
        a = h._acct(); items = tickets.mine(a[0]["uid"]) if a else []
        for pair in (q.get("k", "") or "").split(",")[:20]:   # zgłoszenia bez konta: id:klucz z localStorage
            if ":" in pair:
                i, k = pair.split(":", 1); st = tickets.status_full(i[:12], k[:40])
                if st and not any(x["id"] == st["id"] for x in items): items.append(st)
        return h._json({"items": items, "login": bool(a)})
    if p.startswith("/api/admin/support"):
        if not TOKEN_OK(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        if p == "/api/admin/support":
            tl = tickets.admin_list({k: q[k] for k in ("status",) if q.get(k)})
            items = [dict({k: v for k, v in t.items() if k != "uid"}, inbox=bool(t.get("uid"))) for t in tl["items"]
                     if (not q.get("cat") or t.get("cat_id", "") == q["cat"] or t.get("category") == q["cat"])
                     and (not q.get("q") or q["q"].lower() in (str(t.get("title", "")) + " " + t.get("description", "") + " " + t["id"]).lower())]
            return h._json({"online": online(), "available": _presence["available"], "live": admin_list(), "tickets": items[:300], "new": tl["new"],
                            "cats": tickets.SUP_LABELS, "statuses": tickets.STATUSES, "email": notify.email_enabled()})
        if p == "/api/admin/support/live":
            try: return h._json(admin_conv(q.get("sid", "")))
            except KeyError: return h._json({"error": "not found"}, 404)
        if p == "/api/admin/support/shot":
            sh = tickets.shot(q.get("id", ""))
            return h._json({"shot": sh} if sh else {"error": "not found"}, 200 if sh else 404)
    return None

def handle_post(h, u, data):
    p = u.path; ip = h._ip()
    if p.startswith("/api/admin/support"):
        if not TOKEN_OK(h.headers.get("X-Admin-Token")): return h._json({"error": "unauthorized"}, 401)
        try:
            if p == "/api/admin/support/ping": return h._json({"ok": True, "online": ping(data.get("available", True))})
            if p == "/api/admin/support/reply": admin_reply(str(data.get("sid", "")), data.get("text")); return h._json({"ok": True})
            if p == "/api/admin/support/close": admin_close(str(data.get("sid", "")), bool(data.get("delete"))); return h._json({"ok": True})
            if p == "/api/admin/support/ticket":
                tickets.update(str(data.get("id", "")), {k: data[k] for k in ("status", "note", "reply") if k in data}); return h._json({"ok": True})
        except KeyError: return h._json({"error": "not found"}, 404)
        except ValueError as e: return h._json({"error": str(e)}, 400)
        return h._json({"error": "not found"}, 404)
    a = h._acct(); uid = a[0]["uid"] if a else ""
    if p == "/api/support/live":
        act = data.get("action")
        if act == "start":
            if not livechat.rate_ok("sls:" + ip, 3, 30): return h._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            try: sid = start(uid, str(data.get("lang", "pl"))[:2], data.get("transcript") if data.get("transcript_consent") and isinstance(data.get("transcript"), list) else [])
            except LookupError: return h._json({"online": False}, 409)
            try: MOD_PUSH("Pomoc na żywo – nowa rozmowa", "Ktoś czeka na moderatora")
            except Exception: pass
            return h._json({"ok": True, "sid": sid, "online": True})
        sid = str(data.get("sid", ""))
        if not SID_RE.fullmatch(sid): return h._json({"error": "bad id"}, 400)
        if act == "send":
            if not (livechat.rate_ok("slm:" + ip, 12, 600) and livechat.rate_ok("slm:" + sid, 10, 400)): return h._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            try: return h._json({"ok": True, "msg": user_send(sid, data.get("text")), "online": online()})
            except KeyError: return h._json({"error": "closed", "closed": True}, 409)
            except ValueError: return h._json({"error": "empty"}, 400)
        if act == "end": admin_close(sid); return h._json({"ok": True})
        return h._json({"error": "bad action"}, 400)
    if p == "/api/support/ticket":
        if not livechat.rate_ok("spv:" + ip, 20, 200): return h._json({"error": "Za dużo prób – spróbuj za chwilę.", "code": "rate"}, 429)
        gate = lambda: livechat.rate_ok("spt:" + ip, 3, 15) and livechat.rate_ok("spt:*", 60, 1000) and (not uid or livechat.rate_ok("spt:" + uid, 3, 10))
        # Turnstile: widżet wymaga zmiany CSP (script-src) – na razie honeypot + czas wypełnienia + limity; patrz ZMIANY.md
        try: tid, key = tickets.submit_support(data, uid, gate)
        except PermissionError: return h._json({"ok": True, "id": "LUNA-0000", "key": ""})   # honeypot: udajemy sukces
        except OverflowError: return h._json({"error": "Za dużo zgłoszeń – spróbuj za chwilę.", "code": "rate"}, 429)
        except ValueError as e: return h._json({"error": ERR.get(str(e), "Błędne dane."), "code": str(e)}, 400)
        try: MOD_PUSH("Napisz do moderatora – " + tid, str(data.get("title", ""))[:80])
        except Exception: pass
        _email_admin(tid, data)
        return h._json({"ok": True, "id": tid, "key": key, "inbox": bool(uid)})
    return None
