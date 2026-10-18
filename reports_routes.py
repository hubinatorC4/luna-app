"""HTTP dla Zgłoś 🚩 (reports.py): POST /api/report, GET /api/me/standing, kolejka /api/admin/reports, blokada zapisu po sankcji."""
import re
from urllib.parse import parse_qs
import reports, antibot, social

def _err(h, msg, code, **kw): return h._json({"error": msg, **kw}, code)

def get(h, u, token_ok):
    if u.path == "/api/me/standing":
        a = h._acct()
        if not a: return h._json({"login": True})
        return h._json({"ok": True, **reports.standing(a[0]["uid"])})
    if u.path == "/api/admin/reports":
        if not token_ok(h.headers.get("X-Admin-Token")): return _err(h, "unauthorized", 401)
        q = parse_qs(u.query); g = lambda k: (q.get(k) or [""])[0][:20]
        return h._json(reports.admin_list(g("status") or "open", g("type"), g("cat")))
    m = re.fullmatch(r"/api/admin/user/avatar/([0-9a-f]{8})", u.path)
    if m:
        if not token_ok(h.headers.get("X-Admin-Token")): return _err(h, "unauthorized", 401)
        import userprof, base64
        ou = userprof.uid_by_short(m.group(1)); i = userprof._A().get(ou) if ou else None
        if not i or not i.get("b"): return _err(h, "not found", 404)
        return h._dataurl("data:image/jpeg;base64," + i["b"])
    return None

def post(h, u, data, token_ok):
    p = u.path
    if p == "/api/report":
        if data.get("website"): return h._json({"ok": True})   # honeypot
        uid, dev = h._who(); ip = h._ip(); a = h._acct()
        if "target" in data and "type" not in data:    # starsze przyciski: {target: "post:abc", reason}
            typ, _, tid = str(data.get("target", "")).partition(":"); cat, note = "other", data.get("reason", "")
        else:
            typ, tid, cat, note = str(data.get("type", "")), str(data.get("id", "")), str(data.get("cat", "")), data.get("note", "")
            if a and not h._csrf_ok(a[1]): return _err(h, "Odśwież stronę i spróbuj ponownie.", 403)
        if not uid:
            if typ in ("dm", "user"): return _err(h, "Zaloguj się, aby zgłosić.", 401, login=True)
            if antibot.turnstile_on() and not antibot.turnstile_ok(h._ts_token(data), ip): return _err(h, "Potwierdź, że nie jesteś botem.", 400, turnstile=True)
        key = ("u:" + uid) if uid else social.author_key("", dev)
        if not (reports.hour_ok("r:" + key, reports.PER_HOUR) and reports.hour_ok("rip:" + ip, reports.PER_HOUR_IP)):
            return _err(h, "Dużo zgłoszeń w krótkim czasie – moderator nie nadąża z kawą ☕ Spróbuj za godzinę.", 429)
        try: r = reports.submit(typ, tid, cat, note, uid, key, data.get("block") is True)
        except PermissionError as e:
            if str(e) == "login": return _err(h, "Zaloguj się, aby zgłosić.", 401, login=True)
            return _err(h, "To oficjalna treść Luny – napisz do nas przez pomoc, jeśli coś jest nie tak.", 400)
        except KeyError: return _err(h, "Ta treść już zniknęła – może ktoś był szybszy 🙂", 404)
        except ValueError as e: return _err(h, str(e), 400)
        return h._json({"ok": True, **r})
    if p == "/api/admin/reports":
        if not token_ok(h.headers.get("X-Admin-Token")): return _err(h, "unauthorized", 401)
        act = str(data.get("action", ""))
        try:
            if act in ("lift", "unstrike"):
                c = next((c for c in reports._cases().values() if c["id"] == str(data.get("id", ""))), None)
                if not c or not c["owner"]: raise KeyError("case")
                st = reports.lift(c["owner"]) if act == "lift" else reports.unstrike(c["owner"])
                return h._json({"ok": True, "standing": st, **reports.admin_list(str(data.get("status") or "open"))})
            sv = data.get("serious"); sv = None if sv is None else sv is True
            reports.decide(str(data.get("id", ""))[:12], act, str(data.get("cat", "")) or None, sv, int(data.get("days") or 7), str(data.get("note", "")))
        except KeyError: return _err(h, "not found", 404)
        except (ValueError, TypeError) as e: return _err(h, str(e), 400)
        return h._json({"ok": True, **reports.admin_list(str(data.get("status") or "open"))})
    return None

def write_blocked(h, path):
    if not path.startswith("/api/") or path.startswith(reports.ALLOW_BLOCKED) or path.startswith("/api/admin"): return None
    a = h._acct()
    if not a: return None
    msg = reports.write_block(a[0]["uid"])
    return h._json({"error": msg, "sanction": True}, 403) if msg else None
