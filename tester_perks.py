"""Dodatki tylko dla testerów (egzekwowane na serwerze): odznaka testera, ekskluzywne emotki (czat/komentarze/DM/Live),
awatary testerów i wybór koloru ramki awatara w „Mój panel”. Tester = konto z podpiętym kodem testera, który jest aktywny
(granted i nie wygasł) albo nagłówek X-Tester z aktywnym kodem (aplikacja bez konta).
Kolory zastrzeżone NIE są dostępne: elektryczny niebieski moderatora (⚡ #0A2BFF/#1E5BFF/#3D7BFF) i róż Modelek (#FF3D9A)."""
import re
import store, testers

# Domyślne obwódki testera (bez zmian) + 6 łagodnych presetów
FRAMES = {
    "fioletowa": "#8B5CF6", "niebieska": "#3B82F6",          # dotychczasowe – domyślne
    "mietowa": "#6EE7B7", "brzoskwiniowa": "#FDBA74", "lawendowa": "#C4B5FD",
    "morska": "#5EEAD4", "sloneczna": "#FCD34D", "szalwiowa": "#A3C9A8",
}
FRAME_NAMES = {
    "fioletowa": ["Fioletowa", "Purple", "Morado", "Lila", "Фіолетова"], "niebieska": ["Niebieska", "Blue", "Azul", "Blau", "Синя"],
    "mietowa": ["Miętowa", "Mint", "Menta", "Minze", "М’ятна"], "brzoskwiniowa": ["Brzoskwiniowa", "Peach", "Melocotón", "Pfirsich", "Персикова"],
    "lawendowa": ["Lawendowa", "Lavender", "Lavanda", "Lavendel", "Лавандова"], "morska": ["Morska", "Sea green", "Verde mar", "Meeresgrün", "Морська"],
    "sloneczna": ["Słoneczna", "Sunny", "Soleada", "Sonnig", "Сонячна"], "szalwiowa": ["Szałwiowa", "Sage", "Salvia", "Salbei", "Шавлієва"],
}
RESERVED = {"#0A2BFF", "#1E5BFF", "#3D7BFF", "#FF3D9A"}
assert not RESERVED & {v.upper() for v in FRAMES.values()}
AVATARS = ("tester-mikrofon", "tester-kometa", "tester-fala", "tester-rakieta")      # /avatars/preset-<id>.svg
EMOTES = ("mic", "luna", "fala", "brawo", "hehe", "ok", "serce")                     # :t-<id>: → /tester/emotes/<id>.svg
EMO_RE = re.compile(r":t-([a-z]{2,8}):")

def _code_active(code):
    st = testers.status(code) if code else {}
    return st if st.get("granted") else None

def tester_of(h):
    """Kod aktywnego testera dla żądania (konto → kod; inaczej nagłówek X-Tester). None, gdy nie tester."""
    try:
        a = h._acct()
        if a and a[0].get("tester") and _code_active(a[0]["tester"]): return a[0]["tester"]
    except Exception: pass
    c = str(h.headers.get("X-Tester") or "").strip().upper()[:12]
    return c if c and _code_active(c) else None

def is_tester_uid(uid):
    import accounts
    u = accounts._accts().get(uid or "") or {}
    return bool(u.get("tester") and _code_active(u["tester"]))

def filter_text(text, ok):
    """Emotki testerów zostają tylko u testerów; nieznane kody i cudze próby są usuwane."""
    if not isinstance(text, str) or ":t-" not in text: return text
    return EMO_RE.sub(lambda m: m.group(0) if ok and m.group(1) in EMOTES else "", text)

def frame_color(code):
    t = testers._all().get(code or "") or {}
    f = t.get("frame")
    return FRAMES.get(f) or testers.RINGS.get(t.get("ring")) or FRAMES["fioletowa"]

def set_frame(code, key):
    if key not in FRAMES: raise ValueError("Nieznany kolor ramki.")
    if not _code_active(code): raise PermissionError("Kolor ramki to dodatek dla aktywnych testerów.")
    with testers._lock:
        t = testers._all(); v = t.get(code)
        if not v: raise PermissionError("Kolor ramki to dodatek dla aktywnych testerów.")
        v["frame"] = key
        if key in testers.RINGS: v["ring"] = key
        store.put("testers", t)
    return frame_color(code)

def catalog():
    return {"frames": [{"id": k, "color": v, "names": FRAME_NAMES[k], "default": k in testers.RINGS} for k, v in FRAMES.items()],
            "avatars": ["preset:" + a for a in AVATARS], "emotes": [{"code": f":t-{e}:", "src": f"/tester/emotes/{e}.svg"} for e in EMOTES],
            "badge": "/tester/badge.svg"}

def mine(h):
    code = tester_of(h)
    if not code: return {"tester": False, **catalog()}
    st = testers.status(code); t = testers._all().get(code) or {}
    return {"tester": True, "until": st.get("until", 0), "frame": t.get("frame") or t.get("ring") or "fioletowa", "color": frame_color(code), **catalog()}

# ---------- HTTP ----------
EMOTE_PATHS = ("/api/comments", "/api/battles/chat", "/api/dm", "/api/live-room/chat", "/api/live/send", "/api/wall/post", "/api/wall/edit")

def pre_post(h, path, data):
    """Wywoływane w do_POST przed innymi trasami: filtr emotek dla nie-testerów."""
    if path in EMOTE_PATHS and isinstance(data, dict):
        ok = None
        for k in ("text", "msg", "message"):
            if isinstance(data.get(k), str) and ":t-" in data[k]:
                if ok is None: ok = bool(tester_of(h))
                data[k] = filter_text(data[k], ok)

def get(h, u):
    if u.path == "/api/tester/perks": return h._json(mine(h))
    return None

def post(h, u, data):
    if u.path != "/api/tester/frame": return None
    a = h._acct(); code = tester_of(h)
    if a and not h._csrf_ok(a[1]): return h._json({"error": "Odśwież stronę (CSRF)."}, 403)
    if not code: return h._json({"error": "Kolor ramki to dodatek tylko dla testerów 🎟️", "tester": False}, 403)
    import livechat
    if not livechat.rate_ok("tframe:" + code, 20, 60): return h._json({"error": "Za szybko – ramka też musi złapać oddech 🎨"}, 429)
    try: return h._json({"ok": True, "frame": str(data.get("frame")), "color": set_frame(code, str(data.get("frame", "")))})
    except PermissionError as e: return h._json({"error": str(e)}, 403)
    except ValueError as e: return h._json({"error": str(e)}, 400)
