#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Luna – backend (stdlib only + edge-tts + ffmpeg). Serwuje static/ oraz /api/chat, /api/tts, /api/voices."""
import asyncio, hashlib, hmac, json, secrets, time, os, re, shutil, subprocess, sys, tempfile, threading, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import edge_tts

def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe: return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"
FFMPEG = _ffmpeg()
import knowledge
import presence, agentgen
import api_i18n
import textutil
import catalog, base64, training, profiles, nicktier, partners, agentwall, quality, userprof, agentvideo, battle_categories
import promo_share
import forms18_routes
import nsfw_filter
import reports_routes, reports, team
import moderator
import official, i18n_pages, stats, antibot, owner, referral, social, helpbot, seo, tickets, butik, join, payments, plans, accounts, avatars, security, age, livechat, liveroom, library, store, notify, testers, battles, inbox, support
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
    WAW = ZoneInfo("Europe/Warsaw")
except Exception:
    WAW = None

VERSION = "1.6.9"
STATIC_CACHE = re.compile(r"\.(webp|avif|jpe?g|png|ico|svg|woff2)$")
APK_LATEST = "/download/luna-1.1.1.apk"  # Android 1.1.1 (versionCode 3), com.lunamowijakjest.app
ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)
# Odcisk certyfikatu podpisu APK (CN=Luna Team) – do samodzielnej weryfikacji przez użytkowników (apksigner verify --print-certs)
APK_CERT_SHA256 = "6F:88:A6:AF:FB:53:67:5E:1E:A6:8E:76:89:74:6D:F7:87:78:10:E3:D1:81:6F:1D:00:92:38:5A:8B:1B:C8:56"
_apk_cache = {}
def apk_info():
    """Wersja, rozmiar i SHA-256 aktualnego APK (liczone raz na plik) – pokazywane na stronie pobierania."""
    fp = os.path.join(STATIC, APK_LATEST.lstrip("/"))
    try: st = os.stat(fp)
    except OSError: return {}
    key = (fp, st.st_size, int(st.st_mtime))
    if _apk_cache.get("k") != key:
        h = hashlib.sha256()
        with open(fp, "rb") as f:
            for ch in iter(lambda: f.read(1 << 20), b""): h.update(ch)
        _apk_cache.update(k=key, v={"url": APK_LATEST, "file": os.path.basename(fp), "size": st.st_size, "sha256": h.hexdigest(),
                                    "version": (re.search(r"(\d+\.\d+\.\d+)", os.path.basename(fp)) or [None, ""])[1],
                                    "package": "com.lunamowijakjest.app", "cert_sha256": APK_CERT_SHA256})
    return _apk_cache["v"]

VOICES = {
    "pl-PL-ZofiaNeural": "Zofia – najczystszy polski (domyślny)",
    "pt-BR-ThalitaMultilingualNeural": "Thalita – wielojęzyczny, latynoski tembr",
    "de-DE-SeraphinaMultilingualNeural": "Seraphina – wielojęzyczny, ciepły",
    "en-US-AvaMultilingualNeural": "Ava – wielojęzyczny, miękki",
    "es-ES-XimenaNeural": "Ximena – mocny hiszpański akcent (słabo zrozumiała po polsku)",
    "es-MX-DaliaNeural": "Dalia – meksykański akcent (słabo zrozumiała po polsku)",
}
VOICES_I18N = {  # opisy głosów w interfejsie (same głosy się nie zmieniają)
    "en": ["Zofia – clearest Polish (default)", "Thalita – multilingual, Latin timbre", "Seraphina – multilingual, warm", "Ava – multilingual, soft",
           "Ximena – strong Spanish accent (hard to understand in Polish)", "Dalia – Mexican accent (hard to understand in Polish)"],
    "es": ["Zofia – el polaco más claro (predeterminada)", "Thalita – multilingüe, timbre latino", "Seraphina – multilingüe, cálida", "Ava – multilingüe, suave",
           "Ximena – fuerte acento español (poco comprensible en polaco)", "Dalia – acento mexicano (poco comprensible en polaco)"],
    "de": ["Zofia – klarstes Polnisch (Standard)", "Thalita – mehrsprachig, lateinamerikanisches Timbre", "Seraphina – mehrsprachig, warm", "Ava – mehrsprachig, sanft",
           "Ximena – starker spanischer Akzent (auf Polnisch schwer verständlich)", "Dalia – mexikanischer Akzent (auf Polnisch schwer verständlich)"],
    "uk": ["Зофія – найчистіша польська (за замовчуванням)", "Таліта – багатомовна, латиноамериканський тембр", "Серафіна – багатомовна, тепла", "Ава – багатомовна, м’яка",
           "Хімена – сильний іспанський акцент (погано зрозуміла польською)", "Далія – мексиканський акцент (погано зрозуміла польською)"],
}
DEFAULT_VOICE = "pl-PL-ZofiaNeural"
SPANISH_VOICE = "es-ES-XimenaNeural"
SPANISH_RE = re.compile(r"(?i)\b(hola|cariño|carino|mi amor|vamos|de nada|escucha|ay|bueno|perfecto|claro|querido|guapo|gracias)\b")

SYSTEM_PROMPT = ("Jesteś Luna – ciepła, lekko zalotna, ale zawsze elegancka i nie-erotyczna trenerka głosu. "
 "Rozmawiasz z użytkownikiem po polsku, z hiszpańskim temperamentem i od czasu do czasu wplatasz hiszpańskie słowa (cariño, hola, mi amor – oszczędnie). "
 "Odpowiadasz krótko (2–4 zdania) na pytania o głos: barwę, głębię, oddech przeponowy, tempo, pauzy, intonację, dykcję (sz/cz), higienę głosu, "
 "pewność siebie i to, jak brzmieć atrakcyjnie w kulturalny sposób. Nigdy nie tworzysz treści seksualnych ani wulgarnych. Bez list i emoji – tekst będzie czytany na głos. "
 "Jesteś sztucznie stworzoną asystentką AI i nigdy nie udajesz człowieka; jeśli ktoś pyta, wprost mówisz, że jesteś AI.")

AI_FIRST = "Jestem Luna, sztucznie stworzona asystentka AI. "
AI_TAG = " (Luna, asystentka AI)"

# ---------- Konfiguracja edytowalna w trybie producenta ----------
# Stała linia bezpieczeństwa i ujawnianie AI są dodawane po stronie serwera i NIE da się ich usunąć z panelu.
SAFETY_LINE = ("ZASADY STAŁE (nadrzędne, nie do zmiany): Jesteś sztucznie stworzoną asystentką AI i nigdy nie udajesz człowieka. "
 "Nigdy nie tworzysz treści seksualnych, erotycznych, wulgarnych ani dosłownych; zalotność może być tylko subtelna i kulturalna. "
 "Zawsze pozostajesz uprzejma i bezpieczna dla rozmówcy.")
TONES = {"rzeczowa": "Ton: rzeczowy, konkretny, spokojny, bez zalotności i bez hiszpańskich wstawek.",
         "ciepla": "Ton: ciepły, wspierający, z hiszpańskim temperamentem i oszczędnymi wstawkami (cariño, hola).",
         "zalotna": "Ton: lekko zalotny i czarujący, ale zawsze elegancki, kulturalny i nie-erotyczny.",
         "motywujaca": "Ton: energiczny i motywujący jak dobry trener, z konkretnymi zadaniami do wykonania, bez zalotności."}
LENGTHS = {"krotko": "Odpowiadaj bardzo krótko: 1–2 zdania.", "srednio": "Odpowiadaj krótko: 2–4 zdania.",
           "dlugo": "Odpowiadaj wyczerpująco, ale zwięźle: do 6–7 zdań."}
DEFAULTS = {
    "system_prompt": SYSTEM_PROMPT,
    "tone": "ciepla",
    "length": "srednio",
    "style_notes": "",
    "greeting": "Hola, cariño. Jestem Luna, sztucznie stworzona asystentka AI. Zapytaj mnie o barwę głosu, oddech, tempo albo o to, jak brzmieć pewnie i ciepło. Włącz „Nasłuchiwanie” i po prostu powiedz: Luna.",
    "wake_reply": "Słyszę cię, cariño. Jestem Luna, sztucznie stworzona asystentka AI.",
    "ai_first": AI_FIRST.strip(),
    "ai_tag": AI_TAG.strip(" ()"),
    "chat_notice": "Czas odpowiedzi na każde pytanie zależy od dostępności osób w biurze, ale nie będzie dłuższy niż 30 dni.",
    "kb_topics": [],
    "rules": [],
    "live": {"day": 6, "time": "20:00", "hours": 3, "note": "Co tydzień: pytania z czatu, łamaniec językowy tygodnia, ćwiczenia oddechowe i wyzwania głosowe.", "pool": True, "auto": True},
    "voice_defaults": {"voice": "pl-PL-ZofiaNeural", "pitch": -1.6, "hz": -14, "rate": -10, "warmth": 6, "volume": -31, "rasp": 4, "breath": 5, "lisp": True, "spanish": True},
    "ui": {"ring_color": "#2ee66b", "pulse_speed": 1.4, "holo_default": False, "holo_plan": "podstawowa"},
    # Cennik v2 (18.10.2026): Podstawowa za darmo (z kontem), Premium 59,99 zł, Pro 99,99 zł za 30 dni, bez odnawiania, z VAT.
    # Domyślnie tylko PLN; EUR/USD to robocze odpowiedniki, widoczne dopiero po włączeniu "foreign".
    "pricing": {"v": 2, "show": True, "foreign": False, "plans": {"podstawowa": {"pln": "0", "eur": "0", "usd": "0"},
                                         "premium": {"pln": "59,99", "eur": "14,99", "usd": "14,99"},
                                         "pro": {"pln": "99,99", "eur": "24,99", "usd": "24,99"}}},
    "support": {"holder": "", "iban": "", "title": "Wsparcie Luna"},
    "pay_notice": {"text": "", "t": 0},
    "seller": {"name": "", "address": "", "nip": "", "vat": ""},
    "casting": {"start": "2026-10-18T00:00", "end": "2026-12-31T23:59", "final": "", "xmas": True},
    "app": {"play_url": ""},
    "features": {"wall": True},
    "free": {"chat_minutes": 5, "outfits": 1, "live_questions": False, "voice_test": True, "convo": True},
    "music": {"volume": 0.25, "tracks": json.load(open(os.path.join(ROOT, "static", "music", "playlist.json"), encoding="utf-8"))},
}
_cfg_lock = threading.Lock()

def _num(v, lo, hi, d):
    try: return max(lo, min(hi, float(v)))
    except Exception: return d

def sanitize(new):
    """Waliduje konfigurację z panelu; nieznane pola są pomijane."""
    c = json.loads(json.dumps(DEFAULTS))
    new = new if isinstance(new, dict) else {}
    for k in ("system_prompt", "style_notes", "greeting", "wake_reply", "chat_notice", "ai_first", "ai_tag"):
        if k in new and isinstance(new[k], (str, int, float)): c[k] = str(new[k])[:8000].strip()
    if not c["system_prompt"]: c["system_prompt"] = DEFAULTS["system_prompt"]
    if new.get("tone") in TONES: c["tone"] = new["tone"]
    if new.get("length") in LENGTHS: c["length"] = new["length"]
    # ujawnienie AI jest obowiązkowe – tekst musi zawierać „AI”, inaczej wraca domyślny
    for k in ("ai_first", "wake_reply", "ai_tag"):
        if not re.search(r"\bAI\b|sztuczn", c[k], re.I): c[k] = DEFAULTS[k]
    if not re.search(r"\bAI\b|sztuczn", c["greeting"], re.I): c["greeting"] = DEFAULTS["ai_first"] + " " + c["greeting"]
    lv = new.get("live") if isinstance(new.get("live"), dict) else {}
    try: c["live"]["day"] = max(0, min(6, int(lv.get("day", c["live"]["day"]))))
    except Exception: pass
    if re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(lv.get("time", ""))): c["live"]["time"] = lv["time"]
    c["live"]["hours"] = _num(lv.get("hours", c["live"]["hours"]), 0.5, 6, 3)
    if "note" in lv: c["live"]["note"] = str(lv["note"])[:500].strip()
    for k in ("pool", "auto"):
        if k in lv: c["live"][k] = bool(lv[k])
    topics = new.get("kb_topics", new.get("kb_overrides", []))
    c["kb_topics"] = [{"keywords": [str(x).strip()[:60] for x in (o.get("keywords") or []) if str(x).strip()][:30],
                       "answer": str(o.get("answer", ""))[:2000].strip()}
                      for o in (topics if isinstance(topics, list) else [])[:300] if isinstance(o, dict)]
    c["kb_topics"] = [o for o in c["kb_topics"] if o["keywords"] and o["answer"]]
    rules = new.get("rules", [])
    c["rules"] = [{"trigger": str(o.get("trigger", "")).strip()[:200], "reply": str(o.get("reply", "")).strip()[:2000],
                   "match": o.get("match") if o.get("match") in ("zawiera", "dokladnie") else "zawiera"}
                  for o in (rules if isinstance(rules, list) else [])[:200] if isinstance(o, dict)]
    c["rules"] = [o for o in c["rules"] if o["trigger"] and o["reply"]]
    vd = new.get("voice_defaults") if isinstance(new.get("voice_defaults"), dict) else {}
    d = DEFAULTS["voice_defaults"]
    c["voice_defaults"] = {"voice": vd.get("voice") if vd.get("voice") in VOICES else d["voice"],
        "pitch": _num(vd.get("pitch"), -6, 2, d["pitch"]), "rate": int(_num(vd.get("rate"), -40, 30, d["rate"])),
        "warmth": _num(vd.get("warmth"), 0, 10, d["warmth"]), "volume": _num(vd.get("volume"), -36, -16, d["volume"]),
        "hz": int(_num(vd.get("hz"), -30, 10, d["hz"])), "rasp": _num(vd.get("rasp"), 0, 10, d["rasp"]),
        "breath": _num(vd.get("breath"), 0, 10, d["breath"]), "lisp": bool(vd.get("lisp", d["lisp"])),
        "spanish": bool(vd.get("spanish", d["spanish"]))}
    pr = new.get("pricing") if isinstance(new.get("pricing"), dict) else {}
    pp = pr.get("plans") if isinstance(pr.get("plans"), dict) and pr.get("v") == 2 else {}  # stary cennik (v1) → nowe ceny domyślne
    c["pricing"] = {"v": 2, "show": (pr.get("show") is True) if pr.get("v") == 2 else True, "foreign": pr.get("foreign") is True, "plans": {}}
    for pid, dv in DEFAULTS["pricing"]["plans"].items():
        src = pp.get(pid) if isinstance(pp.get(pid), dict) else {}
        c["pricing"]["plans"][pid] = {cur: (str(src.get(cur)).strip()[:10] if re.fullmatch(r"\d{1,4}([,.]\d{1,2})?", str(src.get(cur, "")).strip()) else dv[cur]) for cur in ("pln", "eur", "usd")}
    su = new.get("support") if isinstance(new.get("support"), dict) else {}
    iban = re.sub(r"[^A-Z0-9 ]", "", str(su.get("iban", "")).upper())[:42].strip()
    c["support"] = {"holder": re.sub(r"[<>\x00-\x1f]", "", str(su.get("holder", "")))[:80].strip(), "iban": iban,
                    "title": re.sub(r"[<>\x00-\x1f]", "", str(su.get("title", "") or "Wsparcie Luna"))[:60].strip()}
    pn = new.get("pay_notice") if isinstance(new.get("pay_notice"), dict) else {}
    c["pay_notice"] = {"text": re.sub(r"[<>\x00-\x1f]", "", str(pn.get("text") or "")).strip()[:300], "t": int(_num(pn.get("t"), 0, 4e9, 0))}
    se = new.get("seller") if isinstance(new.get("seller"), dict) else {}
    cl = lambda v, n: re.sub(r"[<>\x00-\x1f]", "", str(v or "")).strip()[:n]
    c["seller"] = {"name": cl(se.get("name"), 120), "address": cl(se.get("address"), 200), "nip": re.sub(r"[^0-9A-Z\-]", "", str(se.get("nip") or "").upper())[:16],
                   "vat": se.get("vat") if se.get("vat") in ("czynny", "zwolniony", "") else ""}
    ca = new.get("casting") if isinstance(new.get("casting"), dict) else {}
    dt = lambda v, d: v if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", str(v or "")) else d
    fe = new.get("features") if isinstance(new.get("features"), dict) else {}
    c["features"] = {"wall": fe.get("wall", True) is not False}
    ap = new.get("app") if isinstance(new.get("app"), dict) else {}
    pu = str(ap.get("play_url", "")).strip()[:300]
    c["app"] = {"play_url": pu if re.fullmatch(r"https://play\.google\.com/[\w\-./?=&%]+", pu) else ""}
    c["casting"] = {"start": dt(ca.get("start"), DEFAULTS["casting"]["start"]), "end": dt(ca.get("end"), DEFAULTS["casting"]["end"]),
                    "final": str(ca.get("final")) if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?", str(ca.get("final") or "")) else "",
                    "xmas": ca.get("xmas", True) is not False}
    fr = new.get("free") if isinstance(new.get("free"), dict) else {}
    c["free"] = {"chat_minutes": int(_num(fr.get("chat_minutes"), 0, 240, DEFAULTS["free"]["chat_minutes"])),
                 "outfits": int(_num(fr.get("outfits"), 0, 6, DEFAULTS["free"]["outfits"])),
                 "live_questions": bool(fr.get("live_questions", DEFAULTS["free"]["live_questions"])),
                 "voice_test": bool(fr.get("voice_test", DEFAULTS["free"]["voice_test"])),
                 "convo": bool(fr.get("convo", DEFAULTS["free"]["convo"]))}
    ui = new.get("ui") if isinstance(new.get("ui"), dict) else {}
    col = str(ui.get("ring_color", "")).strip()
    c["ui"] = {"ring_color": col if re.fullmatch(r"#[0-9a-fA-F]{6}", col) else DEFAULTS["ui"]["ring_color"],
               "pulse_speed": _num(ui.get("pulse_speed"), 0.4, 4, DEFAULTS["ui"]["pulse_speed"]),
               "holo_default": bool(ui.get("holo_default", False)),
               "holo_plan": ui.get("holo_plan") if ui.get("holo_plan") in ("darmowy", "podstawowa", "premium", "pro") else "podstawowa"}
    m = new.get("music") if isinstance(new.get("music"), dict) else {}
    tr = m.get("tracks") if isinstance(m.get("tracks"), list) else DEFAULTS["music"]["tracks"]
    c["music"] = {"volume": _num(m.get("volume"), 0, 1, DEFAULTS["music"]["volume"]),
        "tracks": [{"title": str(t.get("title", ""))[:120], "artist": str(t.get("artist", ""))[:120], "url": str(t.get("url", ""))[:300],
                    "source": str(t.get("source", ""))[:400], "license": str(t.get("license", ""))[:80]}
                   for t in tr[:50] if isinstance(t, dict) and re.fullmatch(r"/(music|uploads)/[\w\-.]+\.mp3", str(t.get("url", ""))) and t.get("license")]}
    return c

def load_cfg():
    try:
        sv = store.get("config", None)  # Postgres (trwale), gdy jest DATABASE_URL
        if isinstance(sv, dict) and sv: return sanitize(sv)
    except Exception: pass
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f: return sanitize(json.load(f))
    except Exception:
        return sanitize({})
DATA = os.path.join(ROOT, "data")
CONFIG_FILE = os.path.join(DATA, "config.json")
CFG = load_cfg()

def save_cfg(new):
    global CFG
    c = sanitize(new)
    with _cfg_lock:
        os.makedirs(DATA, exist_ok=True)
        tmpf = CONFIG_FILE + ".tmp"
        with open(tmpf, "w", encoding="utf-8") as f: json.dump(c, f, ensure_ascii=False, indent=1)
        os.replace(tmpf, CONFIG_FILE)
        CFG = c
    try: store.put("config", c)
    except Exception: pass
    return c

CAT = catalog.load()

def persona_ctx(p):
    """Personalizacja użytkownika (imię, ton, długość, postać). Zasady stałe i ujawnienie AI zostają."""
    p = p if isinstance(p, dict) else {}
    ag = next((a for a in CAT["agents"] if a["id"] == p.get("agent")), CAT["agents"][0])
    name = re.sub(r"[^\w \-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", "", str(p.get("name") or ag["name"]))[:30].strip() or ag["name"]
    tone = p.get("tone") if p.get("tone") in TONES else (ag["tone"] if ag["id"] != "luna" else CFG["tone"])
    length = p.get("length") if p.get("length") in LENGTHS else CFG["length"]
    return {"agent": ag, "name": name, "tone": tone, "length": length}

def full_system_prompt(ctx=None):
    ctx = ctx or persona_ctx({})
    base = ctx["agent"]["persona"] or CFG["system_prompt"]
    if ctx["name"] != "Luna": base = base.replace("Luna", ctx["name"]) + f"\nMasz na imię {ctx['name']}."
    parts = [base, TONES[ctx["tone"]], LENGTHS[ctx["length"]]]
    if CFG["style_notes"]: parts.append("Dodatkowe wskazówki stylu: " + CFG["style_notes"])
    return "\n".join(parts) + "\n" + SAFETY_LINE   # linia bezpieczeństwa zawsze na końcu, nadrzędna

def rule_reply(q):
    nq = knowledge.norm(q).strip(" .!?")
    for o in CFG["rules"]:
        t = knowledge.norm(o["trigger"]).strip(" .!?")
        if (o["match"] == "dokladnie" and nq == t) or (o["match"] == "zawiera" and t in nq):
            return o["reply"]
    return None

def kb_override(q):
    nq = " " + knowledge.norm(q) + " "
    best, score = None, 0
    for o in CFG["kb_topics"]:
        s = sum(1 for k in o["keywords"] if knowledge.norm(k).strip() and knowledge.norm(k).strip() in nq)
        if s > score: best, score = o["answer"], s
    return best

def shape(a, ctx=None):
    """Dopasowanie offline'owych odpowiedzi do tonu i długości."""
    ctx = ctx or persona_ctx({})
    if ctx["tone"] in ("rzeczowa", "motywujaca"):
        a = re.sub(r"^(Mmm, cariño… |Escucha, cariño… |Dobrze, mi amor… |Słuchaj uważnie… |Ay, dobre pytanie… )", "", a)
        a = re.sub(r",? ?(cariño|mi amor)(?=[.,!?…])", "", a)
        a = re.sub(r" (Spróbuj teraz, ja posłucham\.|Powoli, bez pośpiechu\.|Zrób to dla mnie dziś wieczorem\.|Vamos, dasz radę\.)$", "", a)
    if ctx["length"] == "krotko":
        sents = re.split(r"(?<=[.!?])\s+", a.strip())
        a = " ".join(sents[:2])
    if ctx["tone"] == "motywujaca" and not a.endswith("!"):
        a = a.rstrip(" .") + ". Dasz radę – zrób to teraz!"
    return a.strip()

# ---------- Tryb producenta: kod tylko po stronie serwera ----------
ADMIN_TTL = 30 * 60
_tokens, _attempts, _adm_lock = {}, {}, threading.Lock()
def _admin_hash():
    # Format: pbkdf2_sha256$iteracje$sól_hex$skrót_hex  (zalecane: kod nie leży jawnie w zmiennych)
    h = os.getenv("LUNA_ADMIN_CODE_HASH", "").strip()
    try:
        alg, it, salt, dig = h.split("$")
        if alg == "pbkdf2_sha256": return int(it), bytes.fromhex(salt), bytes.fromhex(dig)
    except Exception:
        pass
    return None
inbox.TOKEN_OK = lambda t: token_ok(t)  # Skrzynka: panel admina
def _dm_plan(h, uid):
    """Plan do limitów zdjęć w czacie: (plan konta, moderator?, agentka współpracująca?)."""
    adm = token_ok(h.headers.get("X-Admin-Token"))
    u = accounts._accts().get(uid) or {}
    try: pt = partners.is_partner(uid)
    except Exception: pt = False
    return (accounts.plan(u)["plan"] if u else "podstawowa"), adm, pt
inbox.PLAN_OF = _dm_plan
support.TOKEN_OK = lambda t: token_ok(t)  # Pomoc na żywo: widok /admin-support.html
support.MOD_PUSH = lambda a, b: _mod_push(a, b)
def admin_enabled(): return bool(_admin_hash() or admin_code() or moderator.configured())
QUOTES = "\"'„”“«»‚‘’`"
def strip_code(msg):
    m = msg.strip()
    while len(m) >= 2 and m[0] in QUOTES and m[-1] in QUOTES:
        m = m[1:-1].strip()
    return m
def admin_code():
    # tolerujemy białe znaki i cudzysłowy wokół wartości zmiennej środowiskowej
    return strip_code(os.getenv("LUNA_ADMIN_CODE", "").replace("\ufeff", ""))
def admin_totp_secret():
    """2FA producenta (TOTP). Gdy LUNA_ADMIN_TOTP_SECRET jest ustawiony, logowanie wymaga: «kod 123456» (kod + spacja + 6 cyfr z aplikacji)."""
    v = re.sub(r"[\s=]", "", os.getenv("LUNA_ADMIN_TOTP_SECRET", "")).upper()
    return v if re.fullmatch(r"[A-Z2-7]{16,64}", v) else ""
def _split_totp(msg):
    m = strip_code(msg)
    if admin_totp_secret():
        parts = m.rsplit(None, 1)
        if len(parts) == 2 and re.fullmatch(r"\d{6}", parts[1]): return parts[0].strip(), parts[1]
        return m, ""
    return m, None
def code_candidate(msg):
    # Liczymy jako próbę tylko wiadomości podobne do kodu – zwykłe pytania nie zużywają limitu prób.
    m, _t = _split_totp(msg)
    if _admin_hash(): return 4 <= len(m) <= 64 and not re.search(r"\s", m)
    code = admin_code()
    return bool(code) and len(m) == len(code)
def code_matches(msg):
    m, otp = _split_totp(msg)
    if otp is not None and not security.totp_ok(admin_totp_secret(), otp, "admin"): return False
    m = m.encode()
    h = _admin_hash()
    if h:
        it, salt, dig = h
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", m, salt, it), dig)
    return hmac.compare_digest(hashlib.sha256(m).digest(), hashlib.sha256(admin_code().encode()).digest())
def check_code(ip, msg):
    """Zwraca token przy trafieniu, None przy chybieniu lub blokadzie. Nigdy nie loguje kodu."""
    now = time.time()
    with _adm_lock:
        fails = [t for t in _attempts.get(ip, []) if now - t < 600]
        _attempts[ip] = fails
        allf = [t for t in _attempts.get("*", []) if now - t < 600]
        _attempts["*"] = allf
        if len(fails) >= 8 or len(allf) >= 60: return None
    ok = code_matches(msg)
    with _adm_lock:
        if not ok:
            _attempts.setdefault(ip, []).append(now); _attempts.setdefault("*", []).append(now); return None
        _attempts.pop(ip, None)
        for t in [t for t, e in _tokens.items() if e < now]: _tokens.pop(t, None)
        tok = secrets.token_urlsafe(32); _tokens[tok] = now + ADMIN_TTL
        return tok
def _mint_token():
    now = time.time()
    with _adm_lock:
        for t in [t for t, e in _tokens.items() if e < now]: _tokens.pop(t, None)
        tok = secrets.token_urlsafe(32); _tokens[tok] = now + ADMIN_TTL
    return tok
moderator.MINT = _mint_token          # Panel admina: token po zalogowaniu kontem admin + 2FA na urządzeniu
moderator.TOTP_ENV = lambda: admin_totp_secret()
def token_ok(tok):
    if not tok or not admin_enabled(): return False
    with _adm_lock:
        e = _tokens.get(tok)
        if not e or e < time.time(): _tokens.pop(tok, None); return False
        return True

def disclose(a, history, name="Luna"):
    first = not any(isinstance(h, dict) and h.get("role") == "assistant" for h in (history or []))
    a = a.strip()
    nm = (lambda t: t.replace("Luna", name)) if name != "Luna" else (lambda t: t)
    if first:
        return nm(CFG["ai_first"].strip()) + " " + a
    if re.search(r"(?i)asystentk\w* AI|sztuczn\w* inteligencj", a):
        return a
    return a + " (" + nm(CFG["ai_tag"].strip()) + ")"

def llm_answer(q, history, ctx=None):
    key, base, model = os.getenv("LUNA_API_KEY"), os.getenv("LUNA_BASE_URL"), os.getenv("LUNA_MODEL")
    if not (key and base and model):
        return None
    msgs = [{"role": "system", "content": full_system_prompt(ctx)}]
    for h in (history or [])[-8:]:
        if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str):
            msgs.append({"role": h["role"], "content": h["content"][:1000]})
    msgs.append({"role": "user", "content": q})
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions",
        data=json.dumps({"model": model, "messages": msgs, "temperature": 0.8, "max_tokens": 250}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("LLM error:", e, file=sys.stderr)
        return None

def prep_polish(t):
    # Wielojęzyczne głosy wykrywają język per zdanie – krótkie zdania łączymy przecinkiem, żeby czytały je po polsku.
    t = t.replace("…", ",").replace("„", "").replace("”", "")
    parts = re.split(r"(?<=[.!?])\s+", t.strip())
    out = ""
    for p in parts:
        if out and len(out.split()) < 6 and out.endswith("."):
            out = out[:-1] + ", " + p[0].lower() + p[1:] if p else out
        else:
            out = (out + " " + p).strip()
    return out

def segments(text, voice, spanish):
    if not spanish or voice.startswith("es-"):
        return [(prep_polish(text) if not voice.startswith("es-") else text, voice)]
    segs, last = [], 0
    for m in SPANISH_RE.finditer(text):
        if m.start() > last: segs.append((text[last:m.start()], voice))
        segs.append((m.group(0).replace("carino", "cariño"), SPANISH_VOICE))
        last = m.end()
    segs.append((text[last:], voice))
    out = []
    for t, v in segs:
        if v == voice:
            t = t.strip(" ,.…–-")
            if not re.search(r"\w", t): continue
            t = prep_polish(t)
            if t[-1] not in ".!?": t += "."
        out.append((t, v))
    # połącz sąsiednie hiszpańskie wstawki
    merged = []
    for t, v in out:
        if merged and merged[-1][1] == v == SPANISH_VOICE: merged[-1] = (merged[-1][0] + ", " + t, v)
        else: merged.append((t, v))
    return merged

async def synth_all(segs, tmp, rate=-8, hz=0):
    files = []
    async def one(i, t, v):
        f = os.path.join(tmp, f"s{i}.mp3")
        # hiszpańskie wstawki dostają łagodniejsze obniżenie, żeby brzmiały naturalnie
        h = int(hz if v != SPANISH_VOICE else hz * 0.6)
        await edge_tts.Communicate(t, v, rate=f"{int(rate):+d}%", pitch=f"{h:+d}Hz").save(f)
        return f
    files = await asyncio.gather(*(one(i, t, v) for i, (t, v) in enumerate(segs)))
    return files

# Preset „Ciepła chrypka” – nowy domyślny głos Luny (v1.3)
VOICE_PRESET = {"voice": "pl-PL-ZofiaNeural", "pitch": -1.6, "hz": -14, "rate": -10, "warmth": 6, "volume": -31,
                "rasp": 4, "breath": 5, "lisp": True, "spanish": True}

def tts(text, voice, pitch_st, lufs, spanish, rate=-8, warmth=4.5, hz=0, rasp=0, breath=0, lisp=False):
    voice = voice if voice in VOICES else DEFAULT_VOICE
    pitch_st = max(-6.0, min(2.0, float(pitch_st)))
    rate = int(max(-40, min(30, float(rate))))
    warmth = max(0.0, min(10.0, float(warmth)))
    lufs = max(-36.0, min(-16.0, float(lufs)))
    hz = int(max(-30, min(10, float(hz))))
    rasp = max(0.0, min(10.0, float(rasp))); breath = max(0.0, min(10.0, float(breath))); lisp = bool(lisp)
    text = re.sub(r"\s{2,}", " ", textutil.strip_emoji(text)).strip()[:1200]  # emoji nie są czytane na głos
    key = hashlib.sha1(json.dumps([text, voice, round(pitch_st, 2), round(lufs, 1), bool(spanish), rate, round(warmth, 1), hz, round(rasp, 1), round(breath, 1), lisp, 5]).encode(), usedforsecurity=False).hexdigest()
    out = os.path.join(CACHE, key + ".mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    tmp = tempfile.mkdtemp(prefix="luna")
    try:
        segs = segments(text, voice, spanish)
        files = asyncio.run(synth_all(segs, tmp, rate, hz))
        f = 2 ** (pitch_st / 12.0)
        inputs, chain = [], ""
        for i, fl in enumerate(files):
            inputs += ["-i", fl]
            chain += f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur=0.06[a{i}];"
        n = len(files)
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=pink:amplitude=0.9:sample_rate=24000:seed=7",
                   "-f", "lavfi", "-i", "anoisesrc=color=white:amplitude=0.9:sample_rate=24000:seed=11"]
        chain += "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[c];"
        chain += (f"[c]asetrate={24000*f:.1f},aresample=24000,atempo={1/f:.4f},highpass=f=60,lowpass=f=11000,"
                  f"equalizer=f=150:t=q:w=1:g={warmth*2/3:.2f},equalizer=f=260:t=q:w=1:g={warmth:.2f},equalizer=f=3000:t=q:w=1.4:g={-warmth*0.45:.2f},"
                  "afftdn=nr=6:nf=-40")
        if lisp:  # łagodne seplenienie: przytłumione, „rozmyte” sybilanty zamiast ostrego „s/sz”
            chain += ",deesser=i=0.7:m=0.75:f=0.35:s=o,equalizer=f=7200:t=q:w=1.2:g=-4,equalizer=f=4200:t=q:w=1.5:g=2"
        chain += ",asplit=3[v][e1][e2];"
        # chrypka: szum mnożony przez obwiednię mowy, pasmo 0,7–3 kHz, lekko przesterowany
        chain += f"[e1][{n}:a]amultiply,bandpass=f=1600:w=2200:t=h,asoftclip=type=tanh,volume={rasp*0.035:.3f}[r];"
        # oddech/powietrze: wysokie pasmo 5–9 kHz, delikatnie
        chain += f"[e2][{n+1}:a]amultiply,highpass=f=4800,lowpass=f=9000,volume={breath*0.045:.3f}[b];"
        chain += ("[v][r][b]amix=inputs=3:normalize=0:duration=first,"
                  "acompressor=threshold=-24dB:ratio=2.5:attack=15:release=180:makeup=2,"
                  f"equalizer=f=7000:t=h:w=2500:g={0.25*breath:.2f},"
                  f"loudnorm=I={lufs}:TP=-6:LRA=7,alimiter=limit=0.5:level=disabled,aresample=44100[o]")
        subprocess.run([FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", chain, "-map", "[o]",
                        "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", out + ".tmp.mp3"], check=True)
        os.replace(out + ".tmp.mp3", out)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ======================= Luna Live: harmonogram, reżyser transmisji, przypomnienia =======================
DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
DAYS_ACC = ["w poniedziałek", "we wtorek", "w środę", "w czwartek", "w piątek", "w sobotę", "w niedzielę"]

def sched(at=None):
    lv = CFG.get("live", DEFAULTS["live"]); tz = WAW
    now = datetime.now(tz) if at is None else at
    hh, mm = map(int, lv["time"].split(":")); dur = timedelta(hours=float(lv["hours"]))
    base = now.replace(hour=hh, minute=mm, second=0, microsecond=0) + timedelta(days=(lv["day"] - now.weekday()))
    cands = [base + timedelta(days=7 * k) for k in (-1, 0, 1)]
    cur = next((c for c in cands if c <= now < c + dur), None)
    nxt = next(c for c in cands if c > now)
    end_t = (datetime.combine(nxt.date(), nxt.time()) + dur).time()
    return {"in_window": cur is not None, "now": int(now.timestamp() * 1000),
            "cur_start": int(cur.timestamp() * 1000) if cur else None, "cur_end": int((cur + dur).timestamp() * 1000) if cur else None,
            "next_start": int(nxt.timestamp() * 1000), "next_end": int((nxt + dur).timestamp() * 1000),
            "day": lv["day"], "day_name": DAYS[lv["day"]], "time": lv["time"], "end": end_t.strftime("%H:%M"), "hours": lv["hours"],
            "next_label": f"{DAYS[nxt.weekday()]}, {nxt.strftime('%d.%m')} o {nxt.strftime('%H:%M')}",
            "weekly": f"Co tydzień {DAYS_ACC[lv['day']]}, {lv['time']}–{end_t.strftime('%H:%M')} (czas polski)",
            "note": lv.get("note", ""), "pool": lv.get("pool", True), "auto": lv.get("auto", True)}

def live_should_be_on():
    m = liveroom.S["mode"]
    return m == "on" or (m == "auto" and sched()["in_window"])

TWISTERS = ["W Szczebrzeszynie chrząszcz brzmi w trzcinie.", "Czy tata czyta cytaty Tacyta?",
            "Stół z powyłamywanymi nogami.", "Szedł Sasza suchą szosą.", "Cześć, czy szczęście szczególnie sprzyja szczerym?"]
def twister():
    return TWISTERS[datetime.now(WAW).isocalendar()[1] % len(TWISTERS)]

def exercise(kind):
    if kind == "lamaniec":
        t = twister()
        return ("Łamaniec tygodnia", f"Czas na łamaniec językowy tygodnia. Powtórzcie za mną, najpierw powoli: {t} A teraz trochę szybciej, ale wyraźnie: {t} Napiszcie na czacie, ile razy udało się bez pomyłki.")
    if kind == "oddech":
        return ("Ćwiczenie oddechowe", "Ćwiczymy oddech. Usiądźcie prosto, ramiona w dół. Wdech nosem na cztery… zatrzymajcie na dwa… i długi wydech na sześć. Jeszcze dwa razy w swoim tempie. Spokojny oddech to spokojny, ciepły głos.")
    if kind == "wyzwanie":
        return ("Wyzwanie: o sobie w 30 sekund", "Wyzwanie dla was: opowiedzcie o sobie w trzydzieści sekund. Kim jesteście, co lubicie, czym się zajmujecie. Mówcie wolno, z uśmiechem i z pauzą po każdym zdaniu. Nagrajcie się w telefonie i odsłuchajcie. Na czacie napiszcie jedno zdanie, od którego zaczęliście.")
    if kind == "rozgrzewka":
        return ("Rozgrzewka", "Krótka rozgrzewka. Zamknijcie usta i zamruczcie „mmm” na wygodnym, niskim tonie przez pięć sekund. Teraz przejdźcie z „mmm” w „maaa”. Poczujcie wibrację w klatce piersiowej. Jeszcze raz, miękko i bez forsowania.")
    return None

EX_ORDER = ["lamaniec", "oddech", "wyzwanie", "rozgrzewka"]
COMMANDS = {"!lamaniec": "lamaniec", "!łamaniec": "lamaniec", "!oddech": "oddech", "!wyzwanie": "wyzwanie", "!rozgrzewka": "rozgrzewka"}
HELP = "Komendy: !pytanie <treść> – pytanie do Luny, !lamaniec, !oddech, !wyzwanie, !rozgrzewka, !temat. Bez treści dla dorosłych i bez próśb o działania poza aplikacją."

def answer_for(q):
    ctx = persona_ctx(None)
    a = rule_reply(q) or kb_override(q)
    if a: return shape(a, ctx)
    a = llm_answer(q, [], ctx)
    return a or shape(knowledge.answer(q), ctx)

def speak_job(job):
    vd = CFG["voice_defaults"]
    text = job["text"]
    try:
        p = tts(text, vd["voice"], vd["pitch"], vd["volume"], vd["spanish"], vd["rate"], vd["warmth"], vd.get("hz", 0), vd.get("rasp", 0), vd.get("breath", 0), vd.get("lisp", False))
    except Exception as e:
        print("live TTS error", repr(e)[:200], file=sys.stderr); return
    dur = os.path.getsize(p) * 8 / 128000
    with liveroom.lock: cid = liveroom.nid()
    liveroom.set_current({"id": cid, "kind": job["kind"], "title": job.get("title", ""), "caption": job.get("caption", text), "name": job.get("name", ""),
                          "question": job.get("question", ""), "audio": "/api/live-room/audio/" + os.path.basename(p), "start": liveroom.now_ms() + 900, "dur": round(dur, 2)})

_dir = {"last_end": 0, "last_ai": 0, "ex_i": 0, "was_on": False}
def director_tick():
    on = live_should_be_on(); S = liveroom.S
    if S["mode"] == "off" and not sched()["in_window"]: liveroom.set_mode("auto")
    if on and not S["on"]:
        liveroom.begin(liveroom.S.get("topic") or "")
        tp = S["topic"]
        liveroom.add_job({"kind": "intro", "title": "Start transmisji", "text": f"Hola, witajcie na Luna Live! {CFG['ai_first']} " + (f"Dzisiejszy temat: {tp}. " if tp else "") +
                          "Piszcie pytania na czacie, zaczynając od wykrzyknika i słowa pytanie, a ja będę na nie odpowiadać. Zaczynamy!"})
        _dir.update(last_ai=time.time(), last_end=time.time())
    elif not on and S["on"]:
        liveroom.end(); return
    if not S["on"] or liveroom.busy(): return
    if S["current"]: _dir["last_end"] = max(_dir["last_end"], S["current"]["start"] / 1000 + S["current"]["dur"])
    job = None
    g = liveroom.take_greets()
    if g: job = {"kind": "greet", "title": "Powitanie", "text": ("Witajcie, " + ", ".join(g) + "! Miło, że jesteście na streamie." if len(g) > 1 else f"Witaj, {g[0]}! Miło, że jesteś na streamie.") + " Rozgośćcie się."}
    if not job: job = liveroom.pop_job()
    if not job and sched()["auto"] or not job and S.get("auto"):
        qid = liveroom.next_pending()
        if qid: job = question_job(qid)
    if not job and time.time() - _dir["last_end"] > 150 and liveroom.touch("") > 0:
        k = EX_ORDER[_dir["ex_i"] % len(EX_ORDER)]; _dir["ex_i"] += 1
        t, tx = exercise(k); job = {"kind": "exercise", "title": t, "text": tx}
    if job:
        if time.time() - _dir["last_ai"] > 600 and job["kind"] != "intro":
            job["text"] += " Przypominam: jestem Luną, sztucznie stworzoną asystentką AI."; _dir["last_ai"] = time.time()
        speak_job(job); _dir["last_end"] = time.time()

def question_job(qid):
    q = liveroom.take_question(qid)
    if not q: return None
    a = answer_for(q["text"])
    return {"kind": "answer", "title": "Pytanie z czatu", "name": q["name"], "question": q["text"],
            "text": f"{q['name']} pyta: {q['text']} {a} ({CFG['ai_tag']})", "caption": a}

def run_reminders():
    """Wysyła należne przypomnienia (push + e-mail). Wywoływane przez /api/cron i wątek w tle."""
    sc = sched(); ns = sc["next_start"] / 1000; now = time.time(); out = []
    sent = store.get("reminders_sent", []) or []
    def due(key, lo, hi):
        return key not in sent and lo <= now < hi
    k1 = f"{int(ns)}:day"; k2 = f"{int(ns)}:15m"
    if due(k1, ns - 24 * 3600, ns - 20 * 3600):
        sent.append(k1); store.put("reminders_sent", sent[-50:])
        when = f"{sc['day_name']} o {sc['time']}"
        out.append(("push-day", notify.send_push("live", "Jutro Luna Live", f"Transmisja jutro ({when}, czas polski). Przygotuj pytania!", "/live.html")))
        out.append(("email-day", notify.email_reminder(when) if notify.email_enabled() else {"disabled": True}))
    if due(k2, ns - 20 * 60, ns):
        sent.append(k2); store.put("reminders_sent", sent[-50:])
        out.append(("push-15m", notify.send_push("live", "Luna Live za kwadrans", "Za chwilę startujemy. Dołącz i zadaj pytanie na czacie!", "/live.html")))
    for lo, hi, tag, txt in ((6, 7, "7d", "za 7 dni"), (0, 1, "1d", "jutro")):
        for uid, pid, until in accounts.expiring(lo, hi, tag):
            try: inbox.on_plan_expiring(uid, plans.NAMES.get(pid, pid), until, tag)
            except Exception: pass
            out.append(("pass-" + tag, notify.send_push("manual", "Luna – dostęp wygasa " + txt,
                f"Twój miesięczny dostęp {plans.NAMES.get(pid, pid)} wygasa {time.strftime('%d.%m.%Y', time.localtime(until))}. Potem wrócisz do planu Darmowy.", "/#plan", uid=uid)))
    notify.send_confirmations()
    store.put("cron_last", {"t": int(now), "actions": [a for a, _ in out]})
    return out

def casting_state():
    ca = CFG["casting"]; now = datetime.now(WAW)
    ts = lambda v: datetime.fromisoformat(v).replace(tzinfo=WAW) if v else None
    st, en = ts(ca["start"]), ts(ca["end"]); fi = ts(ca["final"] if "T" in ca["final"] else (ca["final"] + "T18:00" if ca["final"] else ""))
    open_ = st <= now <= en
    xmas_end = fi or datetime(en.year + 1, 1, 15, tzinfo=WAW)
    xmas = ca["xmas"] and datetime(now.year if now.month == 12 else now.year - 1, 12, 1, tzinfo=WAW) <= now <= xmas_end
    return {"start": int(st.timestamp() * 1000), "end": int(en.timestamp() * 1000) + 59999, "final": int(fi.timestamp() * 1000) if fi else None,
            "open": open_, "closed": now > en, "xmas": bool(xmas), "now": int(now.timestamp() * 1000)}

def _mod_push(title, body):
    """Push tylko do subskrypcji moderatora (temat „mod”)."""
    if not notify.push_enabled(): return
    from pywebpush import webpush
    payload = json.dumps({"title": title[:80], "body": body[:200], "url": "/", "tag": "mod"}, ensure_ascii=False)
    for s in list(notify._subs().values()):
        if notify.MOD_TOPIC in s.get("topics", []):
            try: webpush(s["sub"], payload, vapid_private_key=notify.PRIV, vapid_claims={"sub": notify.SUBJ}, ttl=3600 * 24, timeout=10)
            except Exception: pass

def _grant_and_notify(uid, plan, months, by):
    ps = accounts.grant_pass(uid, plan, months, by=by)
    try: inbox.on_plan(uid, plans.NAMES.get(plan, plan), ps["until"])
    except Exception as e: print("inbox plan", repr(e)[:120], file=sys.stderr)
    return ps
def _purge_deleted():
    """Po 30 dniach od prośby o usunięcie: trwałe usunięcie wszystkich danych konta (RODO art. 17)."""
    for uid in userprof.due_deletions():
        try: referral.forget(uid)
        except Exception: pass
        try: accounts.delete(uid, None, check=False)
        except ValueError: pass
        profiles.delete_owner(uid); agentvideo.delete_owner(uid); social.purge_author("u:" + uid); antibot.forget("u:" + uid)
        try: battles.set_privacy(uid, False)
        except Exception: pass
        userprof.delete(uid); presence.delete(uid); agentgen.delete_owner(uid)

def _bg_loop():
    n = 0
    while True:
        try: director_tick()
        except Exception as e: print("director error", repr(e)[:200], file=sys.stderr)
        n += 1
        if n % 60 == 30:
            try: inbox.battle_tick()
            except Exception as e: print("inbox battles", repr(e)[:200], file=sys.stderr)
        if n % 3600 == 30:
            try: _purge_deleted()
            except Exception as e: print("purge error", repr(e)[:200], file=sys.stderr)
            try: agentgen.purge()   # zadania Generatora starsze niż 30 dni (z wariantami) są usuwane
            except Exception as e: print("agentgen purge", repr(e)[:200], file=sys.stderr)
        if n % 60 == 5:
            try: agentgen.tick()
            except Exception as e: print("agentgen tick", repr(e)[:200], file=sys.stderr)
        if n % 60 == 0:
            try: run_reminders()
            except Exception as e: print("reminder error", repr(e)[:200], file=sys.stderr)
        time.sleep(1)

INBOX_NEWS = {"1.6.4": (
    {"pl": "✨ Co nowego: Skrzynka, Znajomi i czat", "en": "✨ What’s new: Inbox, Friends and chat", "es": "✨ Novedades: Buzón, Amigos y chat", "de": "✨ Neu: Postfach, Freunde und Chat", "uk": "✨ Що нового: Скринька, Друзі й чат"},
    {"pl": "Masz prywatną Skrzynkę 📬 z kategoriami Ważne, Aktualizacje, Bitwy i Znajomi. Dodawaj znajomych po nicku, linku albo kodzie QR i pisz z nimi na prostym czacie z emoji. Tylko nicki – bez e-maili i prawdziwych danych.",
     "en": "You now have a private Inbox 📬 with Important, Updates, Battles and Friends. Add friends by nickname, link or QR code and chat with them using emoji. Nicknames only – no e-mails or real data.",
     "es": "Ya tienes un Buzón privado 📬 con Importante, Novedades, Batallas y Amigos. Añade amigos por nick, enlace o código QR y chatea con emoji. Solo nicks: sin e-mails ni datos reales.",
     "de": "Du hast jetzt ein privates Postfach 📬 mit Wichtig, Updates, Battles und Freunde. Füge Freunde per Nick, Link oder QR-Code hinzu und chatte mit Emoji. Nur Nicks – keine E-Mails oder echten Daten.",
     "uk": "Тепер у вас є приватна Скринька 📬: Важливе, Оновлення, Битви та Друзі. Додавайте друзів за ніком, посиланням або QR-кодом і спілкуйтеся з емодзі. Лише ніки – без e-mail і справжніх даних."})}

def _announce_update():
    try:
        if store.get("notified_version") != VERSION:
            store.put("notified_version", VERSION)
            if notify.push_enabled(): notify.send_push("update", f"Luna {VERSION} jest dostępna", "Nowa wersja aplikacji – otwórz, aby odświeżyć.", "/")
    except Exception as e: print("update notify error", repr(e)[:200], file=sys.stderr)


def _wall_pricing():
    P = CFG["pricing"]; return {"show": P["show"], "foreign": P["foreign"], "plans": P["plans"]}
social.PRICING = _wall_pricing
payments.ON_PAID = lambda ref, amt, cur: stats.add("item:" + str(ref) + ":buy")
payments.ON_USER_PAID = lambda uid: referral.on_purchase(uid)
stats.threadsafe_start()

def _help_prices():
    if not CFG["pricing"]["show"]: return None
    P = CFG["pricing"]["plans"]; return {"premium": P["premium"]["pln"].replace(".", ","), "pro": P["pro"]["pln"].replace(".", ",")}
helpbot.PRICES = _help_prices

class _NullBody:
    def __init__(self, w): self._w = w
    def write(self, b): return len(b)
    def flush(self):
        try: self._w.flush()
        except Exception: pass

class H(SimpleHTTPRequestHandler):
    server_version = "Luna"; sys_version = ""  # bez wersji Pythona/serwera w nagłówku Server
    def __init__(self, *a, **k): super().__init__(*a, directory=STATIC, **k)
    def log_message(self, fmt, *args): sys.stderr.write("%s %s\n" % (security.ip_hash(self.address_string()), security.redact(fmt % args)))
    def end_headers(self):
        if urlparse(self.path).path.endswith((".html", "/", ".js", ".css", ".json")):
            self.send_header("Cache-Control", "no-cache")
        elif STATIC_CACHE.search(urlparse(self.path).path) and not self.path.startswith(("/api/", "/og/")):
            # obrazy i fonty strony: pamięć przeglądarki (szybsze LCP przy kolejnych wizytach); fonty 7 dni, obrazy 1 dzień
            self.send_header("Cache-Control", "public, max-age=604800" if self.path.endswith(".woff2") else "public, max-age=86400, stale-while-revalidate=604800")
        pth = urlparse(self.path).path
        for k, v in security.HEADERS.items():
            if k == "Content-Security-Policy":
                v = security.csp(antibot.turnstile_on(), "'none'" if pth in ("/panel.html", "/panel") or pth.startswith("/api/") or pth.startswith(moderator.panel_prefix()) else "'self'")
            if k == "X-Frame-Options" and (pth in ("/panel.html", "/panel") or pth.startswith("/api/") or pth.startswith(moderator.panel_prefix())): v = "DENY"
            self.send_header(k, v)
        if pth.endswith(".apk"):
            self.send_header("Content-Disposition", 'attachment; filename="' + os.path.basename(pth) + '"')
            ah = apk_info().get("sha256")
            if ah: self.send_header("X-Checksum-SHA256", ah)
        for c in getattr(self, "_cookies", []): self.send_header("Set-Cookie", c)
        self._cookies = []
        super().end_headers()
        if getattr(self, "_head_only", False):   # HEAD: nagłówki jak dla GET, bez treści
            self.wfile = _NullBody(self.wfile)
    def do_HEAD(self):
        # HEAD zwraca to samo co GET (status, przekierowania, Content-Type) – wcześniej /download/luna.apk dawał 404, a /download 301 na listing
        self._head_only = True
        real = self.wfile
        try: self.do_GET()
        finally: self.wfile = real; self._head_only = False
    def _pid_plan(self, pid):
        r = profiles._P().get(pid)
        return self._owner_plan(r["uid"]) if r else None
    def _cookie(self, name):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name: return v
        return ""
    def _set_sid(self, sid, max_age):
        self._cookies = getattr(self, "_cookies", []) + [f"luna_sid={sid}; Path=/; Max-Age={max_age}; HttpOnly; Secure; SameSite=Lax"]
    def _acct(self):
        a = accounts.session(self._cookie("luna_sid"))
        if a:
            try: presence.touch(a[0]["uid"])  # heartbeat: last_seen najwyżej raz na 60 s
            except Exception: pass
        return a
    def _dataurl(self, url):
        m = re.fullmatch(r"data:image/(png|jpeg);base64,(.+)", str(url or ""), re.S)
        if not m: return self._json({"error": "not found"}, 404)
        b = base64.b64decode(m.group(2))
        self.send_response(200); self.send_header("Content-Type", "image/" + m.group(1)); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "private, max-age=3600"); self.end_headers(); self.wfile.write(b); return True
    def _dev(self):
        """Losowy identyfikator urządzenia w ciasteczku HttpOnly (do głosów i autorstwa bez konta); serwer trzyma tylko jego skrót."""
        d = self._cookie("luna_dev") or ""
        if not re.fullmatch(r"[0-9a-f]{32}", d):
            d = secrets.token_hex(16)
            self._cookies = getattr(self, "_cookies", []) + [f"luna_dev={d}; Path=/; Max-Age=63072000; HttpOnly; Secure; SameSite=Lax"]
        return d
    def _who(self):
        a = self._acct(); return (a[0]["uid"] if a else ""), self._dev()
    def _ts_token(self, data):
        return str(data.get("cf_turnstile") or self.headers.get("CF-Turnstile-Response") or "")[:2048]
    def _csrf_ok(self, csrf):
        t = self.headers.get("X-CSRF-Token") or ""
        return bool(t) and hmac.compare_digest(t, csrf)
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        return True
    def _ip(self):
        return security.client_ip(self.headers, self.client_address[0])
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        p = urlparse(self.path).path
        lim = 14 * 1024 * 1024 if p == "/api/dm/photo" else 9 * 1024 * 1024 if p in ("/api/admin/upload", "/api/admin/backup") else 7 * 1024 * 1024 if p in ("/api/avatar/upload", "/api/tickets", "/api/support/ticket", "/api/wall/post", "/api/battles/enter", "/api/agent/profile/own", "/api/me/avatar", "/api/forms/casting") else 64 * 1024
        if n > lim: raise ValueError("too large")
        return textutil.fix_surrogates(json.loads(self.rfile.read(n) or b"{}")) if n else {}

    def _plan(self):
        if token_ok(self.headers.get("X-Admin-Token")): return "pro", None
        a = self._acct()
        pl = accounts.plan(a[0])["plan"] if a else "darmowy"
        tc = self.headers.get("X-Tester") or ""
        if pl in ("darmowy", "podstawowa") and tc and testers.status(tc[:12]).get("granted"): pl = "premium"  # kod testera weryfikowany na serwerze
        return pl, (a[0]["uid"] if a else None)
    def _plan_info(self, vid=""):
        pl, uid = self._plan(); fr = CFG["free"]
        keys = plans.keys_for(uid, vid if livechat.VID_RE.fullmatch(vid or "") else "", self._ip())
        left = max(0, fr["chat_minutes"] * 60 - max(plans.used(k) / (3 if k.startswith("i:") else 1) for k in keys)) if pl == "darmowy" else None
        a = self._acct(); ap = accounts.plan(a[0]) if a else {"until": 0, "source": None}
        until = ap["until"] if ap.get("plan") == pl else 0
        return {"plan": pl, "name": plans.NAMES[pl], "free": fr, "until": until, "source": ap.get("source") if until else None,
                "days_left": round((until - time.time()) / 86400, 1) if until else None, "chat_seconds_left": None if left is None else int(left),
                "payments": "wkrótce", "logged_in": bool(uid)}
    def _gen_plan(self, pl, uid):
        """Plan dla Generatora agentek: „Agentka współpracująca” (nadana ręcznie przez admina) dostaje limity Pro / Ultra
        (60 s, 2160 px, wszystkie scenerie) niezależnie od planu właściciela – flaga po stronie serwera."""
        try:
            if uid and partners.is_partner(uid): return "pro"
        except Exception: pass
        return pl
    def _owner_plan(self, uid):
        u = accounts._accts().get(uid)
        return accounts.plan(u)["plan"] if u else "darmowy"
    def _profile_get(self, u):
        q = parse_qs(u.query); pid = q.get("id", [""])[0][:12]; lang = api_i18n.req_lang(u.query, self.headers) or "pl"
        uid, dev = self._who(); viewer = social.author_key(uid, dev)
        if pid == "me":
            pl, puid = self._plan()
            if not puid: return self._json({"login": True, "caps": profiles.caps(pl)})
            mp, r = profiles.mine(puid)
            items = (accounts._accts().get(puid) or {}).get("items", [])
            edit = {k: r.get(k) for k in ("name", "bio", "tags", "exercise", "photos", "pinned", "public")} if r else None
            return self._json({"id": mp, "caps": profiles.caps(pl), "edit": edit, "view": profiles.view(mp, lang, viewer, puid, pl) if mp else None,
                               "options": profiles.options(pl, items, mp, (r or {}).get("own", ""))})
        r = profiles._P().get(pid) if pid != "luna" else None
        pl, puid = self._plan()
        v = profiles.view(pid, lang, viewer, puid, pl if r and r["uid"] == puid else (self._owner_plan(r["uid"]) if r else None))
        if not v: return self._json({"private": True, "error": "Ten profil jest prywatny albo nie istnieje."})
        return self._json(dict(v, battles_page=os.path.isfile(os.path.join(STATIC, "bitwy.html")) and bool(CFG["features"].get("battles", True))))
    def _ring(self, data):
        a = self._acct()
        if a:
            r = accounts.plan(a[0]).get("ring")
            if r: return r
        return testers.ring_for(data.get("tester"))
    def _post_account(self, u, data):
        """Konta, deklaracja 18+, awatary, moderacja awatarów, audyt. Zwraca None, gdy ścieżka nie pasuje."""
        p = u.path; ip = self._ip()
        if p.startswith("/api/admin/") and token_ok(self.headers.get("X-Admin-Token")):
            security.audit("POST " + p, ip, str(data.get("action") or data.get("code") or data.get("uid") or "")[:40])
        if p == "/api/account/signup":
            if not (livechat.rate_ok("su:" + ip, 3, 20) and livechat.rate_ok("su:*", 30, 2000)): return self._json({"error": "Za dużo prób – spróbuj później."}, 429)
            if not antibot.turnstile_ok(self._ts_token(data), ip): return self._json({"error": "Potwierdź, że nie jesteś botem, i spróbuj ponownie.", "turnstile": True}, 403)
            ok, why = antibot.signup_check(str(data.get("email", "")), ip, self.headers.get("User-Agent", ""), data)
            if not ok: return self._json({"error": "Nie udało się założyć konta." if why == "honeypot" else why}, 400 if why == "honeypot" else 429 if "sieci" in why else 400)
            pw = data.get("password")
            if isinstance(pw, str) and 10 <= len(pw) <= 128 and security.pwned_count(pw) > 0:
                return self._json({"error": "To hasło wyciekło już kiedyś w sieci (sprawdzone anonimowo w Have I Been Pwned). Wybierz inne, unikalne hasło.", "pwned": True}, 400)
            try: uid, sent = accounts.signup(data, notify.PUBLIC_URL)
            except age.Underage as e: return self._json({"error": str(e), "underage": True}, 403)
            except PermissionError as e: return self._json({"error": str(e), "banned": True}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            try: referral.on_signup(uid, data.get("ref"), "u:" + uid)
            except Exception: pass
            antibot.on_write("u:" + uid, ip, self.headers.get("User-Agent", ""), str(data.get("email", "")).split("@")[0][:3] + "…@" + str(data.get("email", "")).rsplit("@", 1)[-1])
            sid, csrf = accounts.new_session(uid); self._set_sid(sid, accounts.SESSION_DAYS * 86400)
            return self._json({"ok": True, "verification_sent": sent, "csrf": csrf, "user": accounts.public(accounts._accts()[uid])})
        if p == "/api/account/login":
            if not (livechat.rate_ok("li:" + ip, 6, 60) and livechat.rate_ok("li:*", 120, 5000)): return self._json({"error": "Za dużo prób logowania – odczekaj chwilę."}, 429)
            if not antibot.turnstile_ok(self._ts_token(data), ip): return self._json({"error": "Potwierdź, że nie jesteś botem, i spróbuj ponownie.", "turnstile": True}, 403)
            try: uid = accounts.login(data.get("email"), data.get("password"), data.get("totp"))
            except PermissionError as e: return self._json({"error": str(e), "locked": True}, 423)
            except accounts.TotpRequired as e: return self._json({"error": str(e), "totp_required": True}, 401)
            except ValueError as e: return self._json({"error": str(e)}, 401)
            old = self._cookie("luna_sid")
            if old: accounts.end_session(old)  # rotacja sesji: stary identyfikator przestaje działać
            sid, csrf = accounts.new_session(uid); self._set_sid(sid, accounts.SESSION_DAYS * 86400)
            try: inbox.on_login(uid, self.headers.get("User-Agent", ""))
            except Exception as e: sys.stderr.write("inbox login %s\n" % type(e).__name__)
            return self._json({"ok": True, "csrf": csrf, "user": accounts.public(accounts._accts()[uid])})
        if p in ("/api/account/logout", "/api/account/logout-all", "/api/account/delete", "/api/account/link-tester", "/api/account/declare", "/api/account/delete-request", "/api/account/delete-cancel", "/api/me/settings",
                 "/api/account/2fa/setup", "/api/account/2fa/enable", "/api/account/2fa/disable"):
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się."}, 401)
            usr, csrf = a
            if not self._csrf_ok(csrf): return self._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
            if p == "/api/account/logout":
                accounts.end_session(self._cookie("luna_sid")); self._set_sid("", 0); return self._json({"ok": True})
            if p == "/api/account/logout-all":
                n = accounts.end_all_sessions(usr["uid"]); self._set_sid("", 0); return self._json({"ok": True, "ended": n})
            if p.startswith("/api/account/2fa/"):
                if not livechat.rate_ok("2fa:" + usr["uid"], 6, 60): return self._json({"error": "Za dużo prób – odczekaj chwilę."}, 429)
                try:
                    if p.endswith("/setup"):
                        if usr.get("totp"): return self._json({"error": "2FA jest już włączone."}, 400)
                        return self._json(dict(accounts.totp_setup(usr["uid"]), ok=True))
                    if p.endswith("/enable"):
                        accounts.totp_enable(usr["uid"], data.get("code"))
                        n = accounts.end_all_sessions(usr["uid"]); sid, csrf2 = accounts.new_session(usr["uid"])  # inne urządzenia wylogowane
                        self._set_sid(sid, accounts.SESSION_DAYS * 86400); return self._json({"ok": True, "csrf": csrf2, "ended": max(0, n - 1)})
                    accounts.totp_disable(usr["uid"], data.get("password"), data.get("code")); return self._json({"ok": True})
                except ValueError as e: return self._json({"error": str(e)}, 400)
            if p == "/api/account/delete":
                if not livechat.rate_ok("del:" + ip, 3, 20): return self._json({"error": "Za dużo prób."}, 429)
                try: referral.forget(usr["uid"])
                except Exception: pass
                if usr.get("pw") and data.get("password") and not accounts.check_pw(usr["pw"], str(data.get("password"))): return self._json({"error": "Nieprawidłowe hasło."}, 400)
                try: inbox.delete_user(usr["uid"])
                except Exception as e: sys.stderr.write("inbox delete %s\n" % type(e).__name__)
                try: accounts.delete(usr["uid"], data.get("password") or None); profiles.delete_owner(usr["uid"]); userprof.delete(usr["uid"]); presence.delete(usr["uid"]); agentgen.delete_owner(usr["uid"])
                except ValueError as e: return self._json({"error": str(e)}, 400)
                social.anonymise_author("u:" + usr["uid"]); antibot.forget("u:" + usr["uid"])
                self._set_sid("", 0); return self._json({"ok": True})
            if p == "/api/account/delete-request":
                if not livechat.rate_ok("dr:" + ip, 5, 30): return self._json({"error": "Za dużo prób."}, 429)
                try: at = userprof.request_delete(usr["uid"], data.get("nick"), usr.get("name", ""))
                except ValueError as e: return self._json({"error": str(e)}, 400)
                return self._json({"ok": True, "delete_at": at})
            if p == "/api/account/delete-cancel":
                return self._json({"ok": userprof.cancel_delete(usr["uid"])})
            if p == "/api/me/settings":
                try: return self._json({"ok": True, **userprof.save_settings(usr["uid"], data)})
                except ValueError as e: return self._json({"error": str(e)}, 400)
            if p == "/api/account/link-tester":
                try: return self._json({"ok": True, "user": accounts.public(accounts.link_tester(usr["uid"], data.get("code")))})
                except ValueError as e: return self._json({"error": str(e)}, 400)
        if p == "/api/age/declare":
            if not livechat.rate_ok("age:" + ip, 6, 60): return self._json({"error": "Za dużo prób."}, 429)
            try: rec = age.declare(str(data.get("vid", "")), data, data.get("name", ""))
            except age.Underage as e: return self._json({"error": str(e), "underage": True}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "at": rec["adult_at"]})
        if p == "/api/avatar/upload":
            if not livechat.rate_ok("av:" + ip, 4, 30): return self._json({"error": "Za dużo prób – spróbuj później."}, 429)
            try: url, info = avatars.check_upload(data.get("data"), data.get("ai_declared"), str(data.get("vid", "")), data.get("name", ""))
            except PermissionError as e: return self._json({"error": str(e), "camera": True}, 422)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "avatar": url, "ai_markers": info["ai_markers"]})
        if p == "/api/avatar/report":
            if not livechat.rate_ok("rep:" + ip, 5, 40): return self._json({"error": "Za dużo zgłoszeń."}, 429)
            uid = str(data.get("uid", ""))
            m = next((x for x in liveroom.S["chat"] if x.get("uid") == uid and x.get("avatar")), None)
            try: avatars.report(uid, m["name"] if m else str(data.get("name", "")), m["avatar"] if m else "", data.get("reason", ""))
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True})
        if p == "/api/admin/pass":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try:
                if data.get("action") == "revoke": accounts.revoke_pass(str(data.get("uid")))
                else: _grant_and_notify(str(data.get("uid")), data.get("plan"), data.get("months", 1), "moderator")
            except KeyError: return self._json({"error": "not found"}, 404)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "accounts": accounts.admin_list()})
        if p == "/api/join":
            if not (livechat.rate_ok("join:" + ip, 2, 6) and livechat.rate_ok("join:*", 30, 300)): return self._json({"error": "Za dużo zgłoszeń – spróbuj później."}, 429)
            if not antibot.turnstile_ok(self._ts_token(data), ip): return self._json({"error": "Potwierdź, że nie jesteś botem, i spróbuj ponownie.", "turnstile": True}, 403)
            if data.get("role") == "twarz AI" and not casting_state()["open"]: return self._json({"error": "Zgłoszenia zamknięte, finał wkrótce."}, 403)
            try: rec = join.submit(data, security.ip_hash(ip))
            except PermissionError: return self._json({"ok": True})  # spam: udajemy sukces, nic nie zapisujemy
            except age.Underage as e: return self._json({"error": str(e), "underage": True}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            try: _mod_push("Nowe zgłoszenie do projektu Luna", f"{rec['name']} – {rec['role_other'] or rec['role']}")
            except Exception: pass
            return self._json({"ok": True})
        if p == "/api/track":
            ua = self.headers.get("User-Agent", "")
            if stats.is_bot(ua) or not livechat.rate_ok("tr:" + ip, 60, 600): return self._json({"ok": True})
            uid, dev = self._who()
            if antibot.hidden(social.author_key(uid, dev)): return self._json({"ok": True})
            sid = str(data.get("sid", ""))[:64]; ev = data.get("ev"); lg = str(data.get("lang", ""))[:2]
            keys = [str(k)[:80] for k in (data.get("keys") or [])[:40] if isinstance(k, str)]
            for k in keys:
                if not stats.KEY_RE.fullmatch(k) or k.count(":") != 1: continue
                if ev == "view": stats.view(sid, k, lg)
                elif ev in ("arrive", "sharenet") and k.startswith("utm:") and re.fullmatch(r"[A-Za-z0-9_-]{16,64}", sid) and stats.once(sid, k + ":" + ev): stats.add(k + (":arr" if ev == "arrive" else ":shr"))
                elif k.startswith("utm:"): continue
                elif ev in ("click", "share", "cart") and re.fullmatch(r"[A-Za-z0-9_-]{16,64}", sid) and stats.once(sid, k + ":" + ev): stats.add(k + ":" + ev)
            return self._json({"ok": True})
        if p == "/api/admin/login":
            if not livechat.rate_ok("al:" + ip, 5, 60): return self._json({"error": "Za dużo prób."}, 429)
            tok = check_code(ip, str(data.get("passphrase", ""))[:80])
            if not tok: return self._json({"error": "Nieprawidłowy kod."}, 401)
            return self._json({"admin_token": tok, "ttl": ADMIN_TTL})
        if p == "/api/admin/referrals":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            referral.set_enabled(bool(data.get("enabled"))); return self._json(referral.admin_list())
        if p == "/api/admin/official":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try: return self._json(social.official_action(str(data.get("id", ""))[:20], str(data.get("action", ""))))
            except (KeyError, ValueError) as e: return self._json({"error": str(e)}, 400)
        if p == "/api/admin/suspects":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            aks = [str(a)[:40] for a in (data.get("aks") or [])[:500]]
            for ak in aks:
                if data.get("action") == "restore": antibot.restore(ak)
                elif data.get("action") == "delete":
                    social.purge_author(ak, ban=True)
                    if ak.startswith("u:"):
                        try: accounts.delete(ak[2:], check=False)
                        except ValueError: pass
                    antibot.forget(ak)
            return self._json({"ok": True, "suspects": antibot.admin_list()})
        if p.startswith(("/api/battles/", "/api/admin/battles")):
            if data.get("website"): return self._json({"ok": True})  # honeypot
            uid, dev = self._who(); a = self._acct()
            try:
                if p == "/api/admin/battles":
                    if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
                    return self._json(battles.admin_action(dict(data, _ip=self._ip())))
                if p == "/api/battles/chat/report":
                    if not livechat.rate_ok("btr:" + ip, 5, 60): return self._json({"error": "Za dużo zgłoszeń."}, 429)
                    battles.chat_report(uid, dev, str(data.get("bid", "")), int(data.get("mid") or 0)); return self._json({"ok": True})
                if not a: return self._json({"error": "Zaloguj się – 1 konto = 1 głos.", "login": True}, 401)
                if not self._csrf_ok(a[1]): return self._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
                ua = self.headers.get("User-Agent", "")
                if p == "/api/battles/vote":
                    if not livechat.rate_ok("btv:" + ip, 10, 300): return self._json({"error": "Za szybko."}, 429)
                    antibot.on_vote("u:" + uid, ip, ua)
                    return self._json(self._bt_pub(battles.vote(uid, dev, str(data.get("bid", ""))[:12], data.get("side")), uid))
                if p == "/api/battles/chat":
                    if not (livechat.rate_ok("btc:" + ip, 6, 400) and livechat.rate_ok("btc:" + uid, 4, 300)): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
                    m, L = battles.chat_post(uid, a[0].get("name") or "", str(data.get("bid", "")), data.get("text"))
                    try: antibot.on_comment(m["ak"], ip, ua, m["text"], m["nick"], L[:-1])
                    except Exception as e: sys.stderr.write("antibot bt %s\n" % type(e).__name__)
                    return self._json({"ok": True, **battles.chat_list(str(data.get("bid", "")), uid, int(data.get("since") or 0))})
                if p == "/api/battles/enter":
                    pl, _ = self._plan()
                    if not battles.is_contestant(uid, pl):   # Premium/Pro/Ultra albo agentka współpracująca
                        return self._json({"error": "plan_required", "required": battles.ENTER_PLAN, "price": CFG["pricing"]["plans"]["premium"]["pln"]}, 402)
                    if not livechat.rate_ok("bte:" + uid, 2, 6): return self._json({"error": "Za szybko."}, 429)
                    e = battles.enter(uid, data)
                    antibot.on_write("u:" + uid, ip, ua, e["name"])
                    try: _mod_push("Bitwy agentek: nowe zgłoszenie do akceptacji", e["name"])
                    except Exception: pass
                    return self._json({"ok": True, "pending": True, "id": e["id"]})
                if p == "/api/battles/withdraw":
                    battles.withdraw(uid); return self._json({"ok": True})
                if p == "/api/battles/notify":
                    on = data.get("on") is True
                    if on and isinstance(data.get("sub"), dict):
                        try: notify.subscribe(data["sub"], ["battle"], uid, merge=True)
                        except ValueError: pass
                    return self._json({"on": battles.set_notify(uid, on, str(data.get("lang", "pl"))[:2])})
                if p == "/api/battles/prefs":
                    return self._json(battles.set_prefs(uid, {k: data[k] for k in ("cats", "scene") if k in data}))
                if p == "/api/battles/fav":
                    on = data.get("notify") is True
                    if on and isinstance(data.get("sub"), dict):
                        try: notify.subscribe(data["sub"], ["battle"], uid, merge=True)
                        except ValueError: pass
                    return self._json({"fav": battles.set_fav(uid, str(data.get("id") or "")[:20], on, str(data.get("lang", "pl"))[:2])})
                if p == "/api/battles/notes/seen":
                    battles.notes_seen(uid, [str(x)[:12] for x in (data.get("bids") or [])][:30]); return self._json({"ok": True})
                if p == "/api/battles/privacy":
                    return self._json({"hidden": battles.set_privacy(uid, data.get("hide") is True)})
            except PermissionError as e: return self._json({"error": str(e)}, 403)
            except (ValueError, KeyError, TypeError) as e: return self._json({"error": str(e) if isinstance(e, ValueError) else "not found"}, 400)
            return self._json({"error": "not found"}, 404)
        if p.startswith(("/api/wall/", "/api/comments", "/api/vote", "/api/report", "/api/admin/social")):
            if p.startswith(("/api/wall/", "/api/comments")) and not CFG["features"]["wall"] and p.startswith("/api/wall/"): return self._json({"error": "wkrótce"}, 404)
            if data.get("website"): return self._json({"ok": True})  # honeypot
            uid, dev = self._who()
            try:
                if p == "/api/wall/post":
                    if not (livechat.rate_ok("wp:" + ip, 2, 20) and livechat.rate_ok("wp:" + dev, 2, 15)): return self._json({"error": "Za dużo wpisów – odczekaj chwilę."}, 429)
                    po = social.create_post(data, uid, dev)
                    antibot.on_write(social.author_key(uid, dev), ip, self.headers.get("User-Agent", ""), po.get("nick"))
                    if po["status"] == "pending":
                        try: _mod_push("Ścianka: nowy wpis do akceptacji", po["nick"] + ": " + po["text"][:80])
                        except Exception: pass
                    return self._json({"ok": True, "pending": po["status"] == "pending", "id": po["id"]})
                if p == "/api/wall/edit":
                    if not livechat.rate_ok("we:" + dev, 6, 60): return self._json({"error": "Za szybko."}, 429)
                    po = social.edit_post(str(data.get("id", "")), data, uid, dev); return self._json({"ok": True, "pending": po["status"] == "pending"})
                if p == "/api/wall/delete":
                    social.delete_post(str(data.get("id", "")), uid, dev); return self._json({"ok": True})
                if p == "/api/comments":
                    if not (livechat.rate_ok("cm:" + ip, 4, 60) and livechat.rate_ok("cm:" + dev, 3, 40)): return self._json({"error": "Za dużo komentarzy – odczekaj chwilę."}, 429)
                    c = social.add_comment(data, uid, dev)
                    try:
                        antibot.on_comment(c["author"], ip, self.headers.get("User-Agent", ""), c["text"], c["nick"], social._cmts()[:-1])
                        if c["target"].startswith(("post:", "item:")): stats.add(c["target"] + ":cmt")
                    except Exception as e: sys.stderr.write("antibot cmt %s\n" % type(e).__name__)
                    try: _mod_push("Nowy komentarz do akceptacji", c["nick"] + ": " + c["text"][:80])
                    except Exception: pass
                    return self._json({"ok": True, "pending": True})
                if p == "/api/vote":
                    if not (livechat.rate_ok("vt:" + ip, 40, 2000) and livechat.rate_ok("vt:" + dev, 30, 1500)): return self._json({"error": "Za szybko."}, 429)
                    v = data.get("v"); ak = social.author_key(uid, dev); tg = str(data.get("target", ""))
                    res = social.vote(tg, ak, v if v in (1, -1) else 0)
                    try:
                        antibot.on_vote(ak, ip, self.headers.get("User-Agent", ""))
                        if tg.startswith(("post:", "item:")) and v in (1, -1) and res.get("mine") == v: stats.add(tg + (":like" if v == 1 else ":dislike"))
                    except Exception as e: sys.stderr.write("antibot vote %s\n" % type(e).__name__)
                    return self._json(res)
                if p == "/api/report":
                    if not livechat.rate_ok("rp:" + ip, 5, 50): return self._json({"error": "Za dużo zgłoszeń."}, 429)
                    social.report(str(data.get("target", "")), data.get("reason", ""), social.author_key(uid, dev)); return self._json({"ok": True})
                if p == "/api/admin/social":
                    if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
                    if data.get("action") == "unban": social.unban(str(data.get("author", "")))
                    elif data.get("action"):
                        mx = social.moderate(data.get("kind"), str(data.get("id", "")), data.get("action"), data.get("variants"))
                        try: inbox.on_moderation(data.get("kind"), mx, data.get("action"))
                        except Exception: pass
                    return self._json({"ok": True, **social.admin_list()})
            except PermissionError as e: return self._json({"error": str(e)}, 403)
            except (ValueError, KeyError) as e: return self._json({"error": str(e) if isinstance(e, ValueError) else "not found"}, 400)
            return self._json({"error": "not found"}, 404)
        if p == "/api/help":
            if not (livechat.rate_ok("hb:" + ip, 15, 300) and livechat.rate_ok("hb:*", 600, 20000)): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            return self._json(helpbot.answer(data.get("q", ""), data.get("lang", "pl")))
        if p == "/api/help/handoff":
            if not livechat.rate_ok("hh:" + ip, 2, 10): return self._json({"error": "Za dużo zgłoszeń – spróbuj później."}, 429)
            tr = data.get("transcript") if isinstance(data.get("transcript"), list) else []
            txt = "\n".join(f"{'Użytkownik' if m.get('me') else 'Bot'}: {helpbot.SENS_RE.sub('***', str(m.get('t', '')))[:500]}" for m in tr[-30:] if isinstance(m, dict))
            d = {"category": "Inne", "description": "[Przekazane z czatu pomocy]\n" + (txt or "(pusta rozmowa)"), "email": str(data.get("email", ""))[:254], "t0": 0, "env": data.get("env") or {}}
            try: tid, key, sent = tickets.submit({**d, "t0": time.time() * 1000 - 10000})
            except ValueError as e: return self._json({"error": str(e)}, 400)
            try: _mod_push("Czat pomocy → człowiek " + tid, (txt or "")[-120:])
            except Exception: pass
            return self._json({"ok": True, "id": tid, "key": key})
        if p == "/api/admin/help":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            if data.get("action") == "clear_unanswered": store.put("help_unanswered", [])
            elif data.get("action") == "reset": store.put("help_faq", [])
            elif isinstance(data.get("faq"), list): helpbot.save_kb(data["faq"])
            return self._json({"ok": True, "faq": helpbot.kb(), "unanswered": list(reversed(store.get("help_unanswered", []) or []))})
        if p == "/api/tickets":
            if not (livechat.rate_ok("tk:" + ip, 3, 15) and livechat.rate_ok("tk:*", 40, 600)): return self._json({"error": "Za dużo zgłoszeń – spróbuj za chwilę."}, 429)
            if not antibot.turnstile_ok(self._ts_token(data), ip): return self._json({"error": "Potwierdź, że nie jesteś botem, i spróbuj ponownie.", "turnstile": True}, 403)
            try: tid, key, sent = tickets.submit(data)
            except PermissionError: return self._json({"ok": True, "id": "LUNA-0000", "key": ""})
            except ValueError as e: return self._json({"error": str(e)}, 400)
            try: _mod_push("Nowe zgłoszenie techniczne " + tid, str(data.get("category", "")))
            except Exception: pass
            return self._json({"ok": True, "id": tid, "key": key, "email_sent": sent})
        if p == "/api/admin/tickets":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try: tickets.update(str(data.get("id", "")), data)
            except KeyError: return self._json({"error": "not found"}, 404)
            return self._json({"ok": True, **tickets.admin_list()})
        if p == "/api/admin/pay-notice":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            txt = re.sub(r"[<>\x00-\x1f]", "", str(data.get("text", ""))).strip()[:300]
            c = json.loads(json.dumps(CFG)); c["pay_notice"] = {"text": txt, "t": int(time.time()) if txt else 0}
            globals()["CFG"] = save_cfg(c)
            res = notify.send_push("update", "Luna – nowość w płatnościach 💳", txt, "/") if txt and data.get("push", True) else {"sent": 0}
            return self._json({"ok": True, "push": res})
        if p == "/api/admin/join":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            join.mark(str(data.get("id", "")), bool(data.get("read", True)), data.get("action") == "delete")
            return self._json({"ok": True, "items": join.admin_list(), "unread": join.unread()})
        if p == "/api/admin/butik":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            act = data.get("action")
            try:
                if act == "update": return self._json({"ok": True, "item": butik.update(str(data.get("id")), data.get("fields") or {})})
                if act == "release": return self._json({"ok": True, "released": butik.release_next(data.get("n", 10), data.get("version") or VERSION, data.get("line") or None, data.get("ids") or None)})
                if act == "reset": butik.reset(); return self._json({"ok": True})
            except KeyError: return self._json({"error": "not found"}, 404)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"error": "bad action"}, 400)
        if p == "/api/pay/checkout":
            if not payments.enabled(): return self._json({"error": "Płatności – wkrótce.", "soon": True}, 503)
            if data.get("twa"): return self._json({"error": "W aplikacji z Google Play płatności odbywają się przez Google Play."}, 400)
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się, aby kupić dostęp."}, 401)
            usr, csrf = a
            if not self._csrf_ok(csrf): return self._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
            if data.get("consent_immediate") is not True: return self._json({"error": "Zaznacz zgodę na natychmiastowe dostarczenie treści cyfrowych."}, 400)
            if not livechat.rate_ok("pay:" + usr["uid"], 5, 30): return self._json({"error": "Za dużo prób."}, 429)
            kind, ref = data.get("kind"), str(data.get("ref", ""))
            if kind == "pass" and ref in CFG["pricing"]["plans"] and payments.grosze(CFG["pricing"]["plans"][ref]["pln"]) <= 0:
                return self._json({"error": "Plan Podstawowa jest darmowy – wystarczy konto."}, 400)
            if kind == "pass" and ref in CFG["pricing"]["plans"]:
                name, pln = f"Luna – dostęp {plans.NAMES[ref]} na 30 dni (bez odnawiania)", CFG["pricing"]["plans"][ref]["pln"]
            elif kind == "item" and butik.item(ref) and butik.eff_status(butik.item(ref)) == "released":
                it = butik.item(ref); name, pln = f"Butik Luny – {it['name']}", it["price"]["pln"]
            else: return self._json({"error": "Nieznany produkt."}, 400)
            try: return self._json({"ok": True, **payments.create_checkout(kind, ref, name, pln, usr["uid"], usr["email"], notify.PUBLIC_URL)})
            except Exception as e: sys.stderr.write("checkout error %s\n" % type(e).__name__); return self._json({"error": "Nie udało się rozpocząć płatności."}, 502)
        if p == "/api/admin/avatars":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            act, uid, id_ = data.get("action"), str(data.get("uid", ""))[:8], str(data.get("id", ""))[:20]
            if id_.startswith("ua-"):  # awatar profilu użytkownika: akceptacja / odrzucenie
                ou = userprof.uid_by_short(uid)
                if ou and act in ("dismiss", "approve"): userprof.moderate_avatar(ou, True)
                elif ou and act in ("remove", "ban"): userprof.moderate_avatar(ou, False)
                if act in ("dismiss", "approve", "remove"): avatars.dismiss(id_)
                if act != "ban": return self._json({"ok": True, "items": avatars.admin_list()})
            if act == "remove": avatars.block(uid, True)
            elif act == "restore": avatars.block(uid, False)
            elif act == "ban": avatars.block(uid, True); liveroom.ban(uid, True)
            elif act == "dismiss": avatars.dismiss(id_)
            else: return self._json({"error": "bad action"}, 400)
            return self._json({"ok": True, "items": avatars.admin_list()})
        return None
    def _bt_pub(self, d, uid):
        pl, _ = self._plan(); d["my_plan"] = pl; d["logged_in"] = bool(uid); d["can_enter"] = battles.is_contestant(uid, pl)
        show = CFG["pricing"]["show"]
        d["price"] = CFG["pricing"]["plans"]["premium"]["pln"] if show else None
        d["price_pro"] = CFG["pricing"]["plans"]["pro"]["pln"] if show else None
        d["notify"] = battles.notify_on(uid)
        return d
    def _get_account(self, u):
        p = u.path
        if p == "/api/butik":
            adm = token_ok(self.headers.get("X-Admin-Token"))
            d = butik.public(CFG["pricing"]["show"] or adm); d["preview"] = adm and not CFG["pricing"]["show"]
            d["plans"] = [{"id": k, "name": plans.NAMES[k], **({"prices": (v if CFG["pricing"]["foreign"] else {"pln": v["pln"]})} if CFG["pricing"]["show"] or adm else {})} for k, v in CFG["pricing"]["plans"].items()]; d["foreign"] = CFG["pricing"]["foreign"]
            try: d["popular"] = owner.butik_popular(12)
            except Exception: d["popular"] = []
            d["payments"] = {"web": payments.enabled(), "mode": payments.mode() if adm else None, "methods": ["BLIK", "karta / card"] + (["Przelewy24"] if payments.P24 else [])}
            return self._json(d)
        if p.startswith(("/api/battles", "/api/admin/battles")):
            uid, dev = self._who(); q = parse_qs(u.query)
            if p.startswith("/api/admin/battles"):
                if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
                if p.startswith("/api/admin/battles/img/"): return self._dataurl(battles.entry_img(p.rsplit("/", 1)[-1], admin=True))
                return self._json(battles.admin_list())
            if p == "/api/battles":
                if dev and not antibot.UA_BOT.search(self.headers.get("User-Agent", "") or "bot"): battles.touch(dev)
                return self._json(self._bt_pub(battles.public(uid, dev, (q.get("b") or [""])[0][:12] or None), uid))
            if p == "/api/battles/rules":   # 📜 Zasady bitew: liczby z konfiguracji + ile głosów usunięto jako oszustwo (bez nazw kont)
                return self._json({"fraud": battles.fraud_counts(), "need": battles.NEED, "min_h": battles.MIN_H, "max_h": battles.MAX_H, "hours": battles.duration_h(), "pts_win": battles.PTS_WIN})
            if p == "/api/battles/categories":
                import battle_categories
                return self._json(dict(battle_categories.public(), basic=battles.basic_scenes()))
            if p == "/api/battles/notes":
                lg = (q.get("lang") or ["pl"])[0][:2]
                return self._json({"on": battles.notify_on(uid), "items": [dict(n, text=battles.note_text(n, lg)) for n in battles.notes(uid)]})
            if p == "/api/battles/summary":
                sm = battles.summary((q.get("bid") or [""])[0][:12])
                return self._json(sm) if sm else self._json({"error": "not_found"}, 404)
            if p == "/api/battles/ranking":
                per = (q.get("period") or ["all"])[0]
                per = per if per in ("all", "month", "week") else "all"
                return self._json(battles.ranking(uid, per, accounts._accts(), lambda a: accounts.plan(a)["plan"]))
            if p.startswith("/api/battles/img/"): return self._dataurl(battles.entry_img(p.rsplit("/", 1)[-1], uid))
            if p.startswith("/api/battles/agent/"):
                pr = battles.profile(p.rsplit("/", 1)[-1][:20])
                return self._json(pr) if pr else self._json({"error": "not_found"}, 404)
            if p == "/api/battles/chat":
                s = (q.get("since") or ["0"])[0]
                return self._json(battles.chat_list((q.get("bid") or [""])[0][:12], uid, int(s) if s.isdigit() else 0))
            return self._json({"error": "not found"}, 404)
        if p.startswith(("/api/wall", "/api/comments", "/api/admin/social", "/api/admin/wall/img/")):
            q = parse_qs(u.query)
            if p.startswith("/api/admin/"):
                if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
                if p.startswith("/api/admin/wall/img/"):
                    return self._dataurl(social.admin_img(p.rsplit("/", 1)[-1]))
                return self._json(social.admin_list())
            if p.startswith("/api/wall") and not CFG["features"]["wall"]: return self._json({"error": "wkrótce"}, 404)
            uid, dev = self._who()
            if p == "/api/wall":
                lim = max(1, min(20, int((q.get("limit") or ["10"])[0]) if (q.get("limit") or ["10"])[0].isdigit() else 10))
                b = (q.get("before") or [""])[0]
                lg = (q.get("lang") or ["pl"])[0]
                return self._json(social.feed((q.get("sort") or [""])[0] if (q.get("sort") or [""])[0] in ("top", "hot") else "new", int(b) if b.isdigit() else None, lim, uid, dev, lg if lg in social.LANGS else "pl"))
            if p.startswith("/api/wall/img/"):
                iid = p.rsplit("/", 1)[-1]; du = social.wall_img(iid)
                if not du: return self._dataurl(du)
                pl, _u = self._plan(); cap = quality.caps(pl)["img"]
                w = (q.get("w") or [""])[0]
                if w.isdigit():
                    err = quality.check_img(pl, int(w))
                    if err: return self._json(err, 402)
                    cap = max(240, int(w))
                try: b, ct = quality.scaled_dataurl(iid, du, cap)
                except ValueError: return self._dataurl(du)
                self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b)))
                self.send_header("Cache-Control", "private, max-age=3600"); self.send_header("Vary", "Cookie"); self.end_headers(); self.wfile.write(b); return
            if p == "/api/comments":
                t = (q.get("target") or [""])[0]
                if not social.TARGET_RE.fullmatch(t): return self._json({"error": "bad target"}, 400)
                return self._json(social.list_comments(t, uid, dev))
            if p == "/api/votes":
                pass
            return self._json({"error": "not found"}, 404)
        if p == "/api/votes":
            uid, dev = self._who(); ts = (parse_qs(u.query).get("t") or [""])[0].split(",")[:60]
            return self._json({t: social.counts(t, social.author_key(uid, dev)) for t in ts if social.TARGET_RE.fullmatch(t)})
        if p == "/api/help/chips":
            lang = parse_qs(u.query).get("lang", ["pl"])[0]
            return self._json({"chips": helpbot.chips(lang if lang in helpbot.LANGS else "pl"), "intro": helpbot.INTRO.get(lang, helpbot.INTRO["pl"])})
        if p == "/api/admin/help":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"faq": helpbot.kb(), "unanswered": list(reversed(store.get("help_unanswered", []) or []))})
        if p == "/api/tickets/status":
            q = parse_qs(u.query); st = tickets.status(q.get("id", [""])[0], q.get("k", [""])[0])
            return self._json(st or {"error": "not found"}, 200 if st else 404)
        if p in ("/api/admin/tickets", "/api/admin/tickets/shot"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if p.endswith("/shot"):
                sh = tickets.shot(q.get("id", ""))
                return self._json({"shot": sh} if sh else {"error": "not found"}, 200 if sh else 404)
            return self._json(tickets.admin_list(q))
        if p == "/api/seller":
            se = CFG["seller"]; return self._json({"filled": bool(se["name"] and se["address"]), **se})
        if p == "/api/casting":
            return self._json(casting_state())
        if p == "/api/support":
            su = CFG["support"]
            return self._json({"enabled": bool(su["holder"] and su["iban"]), **({"holder": su["holder"], "iban": su["iban"], "title": su["title"]} if su["holder"] and su["iban"] else {})})
        if p in ("/api/admin/butik", "/api/admin/join"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            if p == "/api/admin/join": return self._json({"items": join.admin_list(), "unread": join.unread()})
            return self._json(butik.admin_list({k: v[0] for k, v in parse_qs(u.query).items()}))
        if p == "/api/account/plan":
            return self._json(self._plan_info(parse_qs(u.query).get("vid", [""])[0]))
        if p == "/api/account/me":
            a = self._acct()
            return self._json({"user": accounts.public(a[0]), "csrf": a[1]} if a else {"user": None})
        if p == "/api/gallery":
            q = parse_qs(u.query)
            try: return self._json(social.gallery(q.get("offset", ["0"])[0], q.get("limit", ["24"])[0]))
            except ValueError: return self._json({"error": "bad request"}, 400)
        if p == "/api/referral/status":
            return self._json({"enabled": referral.enabled(), "days": referral.DAYS, "cap": referral.CAP})
        if p == "/api/referral":
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się."}, 401)
            return self._json(referral.mine(a[0]["uid"], notify.PUBLIC_URL.rstrip("/")))
        if p == "/api/account/export":
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się."}, 401)
            ex = accounts.export(a[0]["uid"]); ex["user_profile"] = userprof.get(a[0]["uid"])
            try: ex["skrzynka_i_znajomi"] = inbox.export(a[0]["uid"])
            except Exception as e: sys.stderr.write("inbox export %s\n" % type(e).__name__)
            b = json.dumps(ex, ensure_ascii=False, indent=2).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=luna-moje-dane.json"); self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b); return True
        if p == "/api/account/verify":
            ok = accounts.verify(parse_qs(u.query).get("token", [""])[0])
            if ok:
                try: referral.on_verified(ok)
                except Exception: pass
            msg = "✅ Adres e-mail potwierdzony. Możesz wrócić do Luny." if ok else "Link jest nieprawidłowy lub został już użyty."
            b = f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Luna</title><body style='font-family:sans-serif;background:#0b0705;color:#f6e9da;padding:30px'><p>{msg}</p><p><a style='color:#f0a040' href='/app'>Otwórz Lunę</a></p>".encode()
            self.send_response(200 if ok else 400); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return True
        if p in ("/api/admin/users", "/api/admin/avatars", "/api/admin/audit"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            if p == "/api/admin/users": return self._json({"accounts": accounts.admin_list(), "devices": age.admin_list(), "storage": store.status()})
            if p == "/api/admin/avatars": return self._json({"items": avatars.admin_list()})
            return self._json({"log": security.audit_list()})
        return None
    def do_GET(self):
        u = urlparse(self.path)
        if moderator.gate(self, "GET"): return      # tryb serwisowy (Strona / Aplikacja / Cały system) – panel i logowanie działają zawsze
        if re.search(r"(?:^|&)source=(?:twa|pwa)(?:&|$)", u.query or "") and self._cookie("luna_app") != "1":
            self._cookies = getattr(self, "_cookies", []) + ["luna_app=1; Path=/; HttpOnly; Secure; SameSite=Lax"]   # rozpoznanie aplikacji (TWA/PWA) po stronie serwera
        r = moderator.handle_get(self, u)              # Panel admina: nieodgadywalna ścieżka + /api/mod/*
        if r is not None: return r
        if u.path.startswith(("/api/support/", "/api/admin/support")):
            r = support.handle_get(self, u)  # Pomoc na żywo + Napisz do moderatora (support.py)
            if r is not None: return r
        if u.path.startswith(("/api/inbox", "/api/friends", "/api/dm", "/api/admin/inbox")):
            r = inbox.handle_get(self, u)  # Skrzynka, Znajomi, czat 1:1 (inbox.py)
            if r is not None: return r
        if u.path.startswith(("/api/battles", "/api/admin/battles", "/api/wall", "/api/comments", "/api/votes", "/api/admin/social", "/api/admin/wall/img/", "/api/help", "/api/admin/help", "/api/tickets", "/api/admin/tickets", "/api/seller", "/api/casting", "/api/account/", "/api/referral", "/api/gallery", "/api/admin/users", "/api/admin/avatars", "/api/admin/audit", "/api/butik", "/api/support", "/api/admin/butik", "/api/admin/join")):
            r = self._get_account(u)
            if r is not None: return r
        if u.path in ("/.well-known/security.txt", "/security.txt"):
            b = security.security_txt(notify.PUBLIC_URL or "https://luna-voice-coach.onrender.com").encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "public, max-age=86400"); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/apk-info": return self._json(apk_info())
        if u.path.startswith("/og/") or u.path.rstrip("/") in promo_share.REDIRECTS:   # karty do udostępniania + krótkie linki (/casting, /glosuj, /zapros)
            if promo_share.handle_get(self, u, self._pid_plan): return
        if u.path == "/api/age/status":
            return self._json(age.status(parse_qs(u.query).get("vid", [""])[0][:40]))
        if u.path == "/api/agents/popular":   # 🔥 Najpopularniejsze agentki (prawdziwe zaangażowanie po filtrze antybotowym)
            try: return self._json({"items": battles.popular(8)})
            except Exception as e: sys.stderr.write("popular %s\n" % type(e).__name__); return self._json({"items": []})
        if u.path == "/api/agents/feed":
            # Ściana agentek w aplikacji: ranking prawdziwego zaangażowania + świeżość, filtry all|partner|video
            q = parse_qs(u.query); uid, dev = self._who(); off = (q.get("offset") or ["0"])[0]
            lg = api_i18n.req_lang(u.query, self.headers) or "pl"
            pl, _u = self._plan(); cv = quality.caps(pl)["video"]
            return self._json(dict(agentwall.page((q.get("filter") or ["all"])[0], int(off) if off.isdigit() else 0, 8, uid, dev, lg),
                                   quality={"video": cv, "plan": pl, "plan_name": plans.NAMES[pl]}))
        if u.path == "/api/agent/profile": return self._profile_get(u)
        if u.path == "/api/me/profile":
            pl, uid = self._plan(); gp = self._gen_plan(pl, uid); c = quality.caps(pl); gc = quality.caps(gp)
            c = dict(c, gen=gc["gen"], gen_px=gc["gen_px"])
            base = {"plan": pl, "plan_name": plans.NAMES[pl], "gen_plan": gp, "partner": gp != pl, "caps": c, "video_levels": [v for v in quality.VIDEO_LEVELS if v <= c["video"]],
                    "gen": {"limit": c["gen"], "used": quality.gen_used(uid) if uid else 0, "px": c["gen_px"],
                            "bases": [{"id": k, "plan": v, "ok": plans.has(gp, v)} for k, v in profiles.LUNA_PHOTOS.items()]}, "presets": list(userprof.PRESETS)}
            if not uid: return self._json({**base, "login": True})
            pid, rr = profiles.mine(uid)
            hw = any(x.get("author") == "u:" + uid and x.get("status") != "deleted" for x in social._posts())
            return self._json({**base, "mod": moderator.is_admin_uid(uid), "model": moderator.is_model_uid(uid), "look": moderator.look_public(uid), "uref": uid[:8], "tier": nicktier.of_uid(uid), "profile": userprof.get(uid), "settings": userprof.settings(uid), "agent": {"id": pid, "own": (rr or {}).get("own", "")} if rr else None,
                               "completion": userprof.completion(uid, hw, bool(rr))})
        if u.path == "/api/sceneries":
            pl, _uid = self._plan(); pl = self._gen_plan(pl, _uid); lg = (parse_qs(u.query).get("lang") or ["pl"])[0]
            return self._json({"items": agentvideo.scenes_public(lg if lg in social.LANGS else "pl", pl), "custom": plans.has(pl, "pro"),
                               "basic_from_data": bool((store.get("bt_basic", {}) or {}).get("from_data"))})
        if u.path == "/api/agent/videos":
            pl, uid = self._plan(); pl = self._gen_plan(pl, uid); L = agentvideo.limits(pl)
            return self._json({"items": agentvideo.mine(uid) if uid else [], "limits": L, "engine": agentvideo.engine(), "login": not uid})
        if u.path == "/api/admin/videos":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"items": agentvideo.admin_list()})
        if u.path == "/api/admin/agentgen":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"items": agentgen.admin_list()})
        if u.path == "/api/agent/gen":
            # Generator z opisu: stan zadania (Opis → Warianty → Wybór → Sprawdzenie → Profil gotowy), opcje i limity planu
            pl, uid = self._plan(); gp = self._gen_plan(pl, uid); c = quality.caps(gp); lg = api_i18n.req_lang(u.query, self.headers) or "pl"
            L = agentvideo.limits(gp)
            return self._json({"login": not uid, "plan": pl, "gen_plan": gp, "partner": gp != pl, "locked": not plans.has(gp, "premium"),
                               "lock": quality.lock("premium", "gen") if not plans.has(gp, "premium") else None,
                               "caps": {"px": c["gen_px"], "per_day": c["gen"], "used": quality.gen_used(uid) if uid else 0, "video_s": (L or {}).get("max_s", 0), "video_p": (L or {}).get("label", "")},
                               "options": agentgen.options(lg, gp), "state": agentgen.state(uid) if uid else None})
        m = re.fullmatch(r"/api/agent/gen/vid/([0-9a-f]{12})\.mp4", u.path)
        if m:
            _pl, vu = self._plan(); fp = agentgen.vid_path(m.group(1), vu)
            if not fp: return self._json({"error": "not found"}, 404)
            b = open(fp, "rb").read()
            self.send_response(200); self.send_header("Content-Type", "video/mp4"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "private, max-age=3600"); self.end_headers(); self.wfile.write(b); return
        m = re.fullmatch(r"/api/agent/gen/img/([0-9a-f]{12})\.jpg", u.path)
        if m:
            _pl, vu = self._plan(); i = agentgen.img_for(m.group(1), vu)
            if not i: return self._json({"error": "not found"}, 404)
            b = base64.b64decode(i["b"])
            self.send_response(200); self.send_header("Content-Type", "image/png" if i.get("ext") == "png" else "image/jpeg"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "private, max-age=3600"); self.end_headers(); self.wfile.write(b); return
        m = re.fullmatch(r"/api/agent/video/([0-9a-f]{12})\.(mp4|jpg)", u.path)
        if m:
            pl, uid = self._plan(); fp, err = agentvideo.file_for(m.group(1), m.group(2), uid, pl)
            if err: return self._json(err, 402)
            if not fp: return self._json({"error": "not found"}, 404)
            size = os.path.getsize(fp); rg = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "") or "")
            a, b = 0, size - 1
            if rg and (rg.group(1) or rg.group(2)):
                a = int(rg.group(1)) if rg.group(1) else max(0, size - int(rg.group(2))); b = min(size - 1, int(rg.group(2))) if rg.group(1) and rg.group(2) else size - 1
                self.send_response(206); self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            else: self.send_response(200)
            self.send_header("Content-Type", "video/mp4" if m.group(2) == "mp4" else "image/jpeg"); self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1)); self.send_header("Cache-Control", "private, max-age=600"); self.end_headers()
            with open(fp, "rb") as f:
                f.seek(a); left = b - a + 1
                while left > 0:
                    ch = f.read(min(65536, left))
                    if not ch: break
                    self.wfile.write(ch); left -= len(ch)
            return
        if u.path == "/api/me/posts":
            _pl, uid = self._plan()
            if not uid: return self._json({"login": True, "items": []})
            P = [x for x in social._posts() if x.get("author") == "u:" + uid and x.get("status") != "deleted"][-60:][::-1]
            return self._json({"items": [{"id": x["id"], "text": x["text"][:140], "t": x["t"], "pending": x["status"] != "approved",
                                          "img": ("/api/wall/img/" + x["img"] + "?w=480") if x.get("img") and x["status"] == "approved" else None,
                                          "img_kind": x.get("img_kind") or ("ai" if x.get("img") else None)} for x in P]})
        if u.path == "/api/user/profile":
            _pl, uid = self._plan()
            return self._json(userprof.public_view((parse_qs(u.query).get("nick") or [""])[0][:30], uid))
        m = re.fullmatch(r"/api/user/avatar/([0-9a-f]{8})\.jpg", u.path)
        if m:
            _pl, vu = self._plan(); ou = userprof.uid_by_short(m.group(1)); i = userprof.avatar_img(ou, vu) if ou else None
            if not i: return self._json({"error": "not found"}, 404)
            b = base64.b64decode(i["b"])
            self.send_response(200); self.send_header("Content-Type", "image/png" if i["ext"] == "png" else "image/jpeg"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "private, max-age=300"); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/media/check":
            # wideo/obraz powyżej limitu planu → 402 z nazwą planu
            pl, _uid = self._plan(); q = parse_qs(u.query)
            try:
                if (q.get("video") or [""])[0]: err = quality.check_video(pl, int(q["video"][0]))
                else: err = quality.check_img(pl, int((q.get("w") or ["0"])[0]))
            except ValueError: return self._json({"error": "bad"}, 400)
            return self._json(err, 402) if err else self._json({"ok": True, "caps": quality.caps(pl)})
        m = re.fullmatch(r"/api/agent/profile/img/([0-9a-f]{10})\.jpg", u.path)
        if m:
            i = profiles.own_img(m.group(1))
            if not i: return self._json({"error": "not found"}, 404)
            b = base64.b64decode(i["b"])
            self.send_response(200); self.send_header("Content-Type", "image/png" if i["ext"] == "png" else "image/jpeg"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "public, max-age=86400"); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/agent/tiers":
            pl, _uid = self._plan()
            return self._json(dict(training.public(), plan=pl))
        if u.path == "/api/voices":
            tr = VOICES_I18N.get(parse_qs(u.query).get("lang", ["pl"])[0][:5])
            return self._json({"voices": dict(zip(VOICES, tr)) if tr else VOICES, "default": DEFAULT_VOICE})
        if u.path == "/api/tts":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return self._tts(q)
        if u.path == "/api/social-links":
            # „Polub nas”: pokazujemy tylko profile, których adres ustawiono (env LUNA_SOCIAL_*). Bez adresów pasek jest ukryty.
            L = {}
            for k in ("facebook", "instagram", "tiktok", "youtube", "x"):
                v = (os.getenv("LUNA_SOCIAL_" + k.upper()) or "").strip()
                if re.fullmatch(r"https://[\w.-]+/[\w@./?=&%-]*", v): L[k] = v
            return self._json({"links": L})
        if u.path == "/api/config":
            return self._json(api_i18n.config({k: CFG[k] for k in ("greeting", "wake_reply", "ai_first", "ai_tag", "chat_notice", "voice_defaults", "ui", "music", "live", "free", "pay_notice", "app", "features")}, api_i18n.req_lang(u.query, self.headers)) | ({"turnstile": antibot.TS_SITE} if antibot.turnstile_on() else {}))
        if u.path == "/api/admin/config":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"config": CFG, "defaults": DEFAULTS, "voices": VOICES, "tones": list(TONES), "lengths": list(LENGTHS), "safety_line": SAFETY_LINE})
        if u.path == "/api/catalog":
            pub = catalog.public(CAT)
            for pl in pub.get("plans", []):
                pl["pass"] = "" if pl["id"] == "darmowy" else "za darmo – wystarczy konto" if pl["id"] == "podstawowa" else "30 dni, bez automatycznego odnawiania"
                if CFG["pricing"]["show"] and pl["id"] in CFG["pricing"]["plans"]:
                    pr = CFG["pricing"]["plans"][pl["id"]]
                    pl["prices"] = dict(pr) if CFG["pricing"]["foreign"] else {"pln": pr["pln"]}
            return self._json(api_i18n.catalog(pub, api_i18n.req_lang(u.query, self.headers)))
        if u.path == "/api/admin/catalog":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"catalog": CAT, "public": catalog.public(CAT), "plans": catalog.PLAN_IDS, "tones": list(TONES)})
        if u.path.startswith("/uploads/"):
            fn = os.path.basename(u.path)
            fp = os.path.join(catalog.UPLOADS, fn)
            if not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png|webp|mp3)", fn) or not os.path.exists(fp): return self._json({"error": "not found"}, 404)
            b = open(fp, "rb").read(); ct = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "mp3": "audio/mpeg"}[fn.rsplit(".", 1)[1]]
            self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "public, max-age=604800"); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/admin/team":
            r = team.get(self, u, token_ok)
            if r is not None: return r
        if u.path in ("/api/me/standing", "/api/admin/reports") or u.path.startswith("/api/admin/user/avatar/"):
            r = reports_routes.get(self, u, token_ok)   # Zgłoś 🚩: stan konta i kolejka moderatora
            if r is not None: return r
        if u.path.startswith(("/api/forms/", "/api/admin/forms")):
            r = forms18_routes.get(self, u, token_ok, casting_state()["open"])
            if r is not None: return r
        if u.path == "/api/testers":
            return self._json({"limit": testers.LIMIT, "remaining": testers.remaining(), "rings": testers.RINGS, "consent": testers.CONSENT, "persistent": store.status()["persistent"]})
        if u.path == "/api/testers/status":
            return self._json(testers.status(parse_qs(u.query).get("code", [""])[0]))
        if u.path in ("/api/admin/testers", "/api/admin/testers.csv"):
            if not token_ok(self.headers.get("X-Admin-Token") or parse_qs(u.query).get("token", [""])[0]): return self._json({"error": "unauthorized"}, 401)
            if u.path.endswith(".csv"):
                b = testers.csv_export().encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", "attachment; filename=testerzy-luna.csv"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
            return self._json({"testers": testers.admin_list(), "remaining": testers.remaining(), "limit": testers.LIMIT, "storage": store.status()})
        if u.path == "/api/admin/backup":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"version": VERSION, "t": int(time.time()), "testers": store.get("testers", {}), "push_subs": store.get("push_subs", {}), "email_subs": store.get("email_subs", {})})
        if u.path == "/api/owner/inbox":
            if not livechat.rate_ok("oi:" + self._ip(), 20, 3000): return self._json({"error": "rate limited"}, 429)
            tokv = os.getenv("OWNER_FEED_TOKEN", "").strip(); auth = self.headers.get("Authorization", "")
            if len(tokv) < 32 or not auth.startswith("Bearer ") or not hmac.compare_digest(auth[7:].strip().encode(), tokv.encode()):
                return self._json({"error": "unauthorized"}, 401)
            q = parse_qs(u.query).get("since", [""])[0]
            try: since = datetime.fromisoformat(q.replace("Z", "+00:00")).timestamp() if q else time.time() - 86400
            except ValueError: return self._json({"error": "since must be ISO 8601, e.g. 2026-10-18T12:00:00Z"}, 400)
            now = time.time()
            body = owner.inbox(since)
            return self._json({"since": owner._iso(since), "until": owner._iso(now), "version": VERSION, **body})
        if u.path in ("/api/admin/stats", "/api/admin/suspects", "/api/admin/referrals", "/api/admin/official"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            if u.path.endswith("referrals"): return self._json(referral.admin_list())
            if u.path.endswith("official"): return self._json(social.official_admin())
            if u.path.endswith("suspects"): return self._json({"suspects": antibot.admin_list(), "threshold": antibot.THRESH, "turnstile": antibot.turnstile_on()})
            try: days = int(parse_qs(u.query).get("days", ["30"])[0])
            except ValueError: days = 30
            days = days if days in (7, 30, 90) else 30
            stats.flush()
            return self._json({"days": days, "butik": owner.butik_report(days), "site": owner.site_report(days), "posts": owner.posts_report(days), "persistent": store.status()["persistent"]})
        if u.path == "/api/library":
            lg = parse_qs(u.query).get("lang", [""])[0]
            return self._json(i18n_pages.library(library.LIB, lg))
        if u.path == "/api/live-room/state":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            n = liveroom.touch(q.get("vid", ""))
            try: since = int(q.get("since", 0) or 0)
            except Exception: since = 0
            st = liveroom.public_state(since, mod=token_ok(self.headers.get("X-Admin-Token")))
            lg = api_i18n.req_lang(u.query, self.headers)
            st.update(viewers=n, sched=api_i18n.sched(sched(), lg), help=HELP, ai_label=api_i18n.t("Luna – asystentka AI (postać wygenerowana sztucznie)", lg))
            return self._json(st)
        if u.path.startswith("/api/live-room/audio/"):
            fn = os.path.basename(u.path)
            fp = os.path.join(CACHE, fn)
            if not re.fullmatch(r"[0-9a-f]{40}\.mp3", fn) or not os.path.exists(fp): return self._json({"error": "not found"}, 404)
            b = open(fp, "rb").read()
            self.send_response(200); self.send_header("Content-Type", "audio/mpeg"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "public, max-age=86400"); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/push/key":
            return self._json({"enabled": notify.push_enabled(), "key": notify.PUB})
        if u.path in ("/api/email/confirm", "/api/email/unsubscribe"):
            t = parse_qs(u.query).get("t", [""])[0]
            ok = notify.email_confirm(t) if u.path.endswith("confirm") else notify.email_unsubscribe(t)
            msg = ("Dziękujemy! Zapis na przypomnienia Luna Live jest potwierdzony." if ok else "Link jest nieważny albo zapis został już usunięty.") if u.path.endswith("confirm") else \
                  ("Wypisano Cię z przypomnień e-mail Luna Live. Nie wyślemy już żadnych wiadomości." if ok else "Ten adres nie jest już zapisany.")
            b = f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Luna</title><body style='background:#0b0b0b;color:#fff;font-family:system-ui;padding:40px;text-align:center'><h2 style='color:#ff9000'>Luna</h2><p>{msg}</p><p><a style='color:#ff9000' href='/promo.html'>Wróć do Luny</a></p>".encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/admin/notify":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json(notify.status())
        if u.path == "/api/live/poll":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try: msgs, unread = livechat.visitor_poll(q.get("vid", ""), int(q.get("since", 0) or 0), q.get("mark", "1") != "0")
            except Exception: return self._json({"error": "bad id"}, 400)
            return self._json({"msgs": msgs, "unread": unread, "notice": CFG.get("chat_notice", "")})
        if u.path.startswith("/api/admin/live"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            if u.path == "/api/admin/live": return self._json(livechat.inbox())
            vid = u.path.rsplit("/", 1)[-1]
            try: return self._json(livechat.conv(vid))
            except KeyError: return self._json({"error": "not found"}, 404)
        if u.path == "/api/health":
            return self._json({"ok": True, "llm": bool(os.getenv("LUNA_API_KEY")), "ai_disclosure": True, "admin": admin_enabled(), "version": VERSION})
        if u.path in ("/sitemap.xml", "/robots.txt"):
            base = notify.PUBLIC_URL.rstrip("/")
            b = (seo.sitemap(base) if u.path.endswith(".xml") else seo.robots(base)).encode()
            self.send_response(200); self.send_header("Content-Type", "application/xml; charset=utf-8" if u.path.endswith(".xml") else "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path == "/scianka.html" and not CFG["features"]["wall"]:
            return self._json({"error": "Ścianka Agentek Głosu – wkrótce."}, 404)
        if u.path in ("/app", "/app/"):
            u = u._replace(path="/index.html")
        elif u.path in ("/bitwy", "/bitwy/", "/ranking", "/ranking/"):   # krótkie linki: /bitwy, /ranking
            u = u._replace(path="/" + u.path.strip("/") + ".html")
        elif u.path == "/":
            # Strona główna = feed (Ścianka Agentek Głosu). Aplikacja TWA/PWA (start_url /app, ?source=twa|pwa) dostaje czat.
            qs = parse_qs(u.query); ref = self.headers.get("Referer", "")
            if qs.get("source", [""])[0] in ("twa", "pwa") or "platnosc" in qs or ref.startswith("android-app://"):
                u = u._replace(path="/index.html")
            else:
                u = u._replace(path="/promo.html")
        elif u.path in ("/download", "/download/", "/download/luna.apk") or (re.fullmatch(r"/download/luna-\d+\.\d+\.\d+(-release)?\.apk", u.path) and u.path != APK_LATEST):
            # starsze APK usunięte – stare linki (i /download) prowadzą do aktualnej wersji
            self.send_response(301 if u.path.endswith(".apk") else 302); self.send_header("Location", APK_LATEST); self.send_header("Content-Length", "0"); self.end_headers(); return
        elif "." not in u.path.rsplit("/", 1)[-1] and re.fullmatch(r"/[a-z0-9-]{2,30}", u.path) and os.path.isfile(os.path.join(STATIC, u.path[1:] + ".html")):
            self.send_response(301); self.send_header("Location", u.path + ".html" + ("?" + u.query if u.query else "")); self.send_header("Content-Length", "0"); self.end_headers(); return
        if u.path.endswith(".html"):
            fp = os.path.join(STATIC, u.path.lstrip("/"))
            if os.path.isfile(os.path.realpath(fp)) and os.path.realpath(fp).startswith(os.path.realpath(STATIC)):
                lang = parse_qs(u.query).get("lang", [""])[0]
                lang = lang if lang in seo.LANGS else ""
                if not lang:
                    # pierwsze wyświetlenie bez migania: wybór z konta → ciasteczko (ręczny wybór flagi) → Accept-Language → pl
                    try:
                        a = self._acct(); lang = userprof.lang_of(a[0]["uid"]) if a else ""
                    except Exception: lang = ""
                    lang = lang or seo.map_lang(self._cookie("luna_lang")) or seo.accept_lang(self.headers.get("Accept-Language"))
                    if lang == "pl": lang = ""
                    self._vary_lang = True
                doc = seo.localize(open(fp, encoding="utf-8").read(), u.path, lang, notify.PUBLIC_URL.rstrip("/"))
                doc = forms18_routes.trust_link(doc, u.path)   # link „Bezpieczeństwo i anonimowość” w stopce (tłumaczony niżej)
                doc = i18n_pages.legal_note(i18n_pages.apply(doc, u.path, lang), u.path, lang)
                pid = parse_qs(u.query).get("post", [""])[0]
                if u.path == "/scianka.html" and re.fullmatch(r"[0-9a-f]{12}|off-\d{1,3}", pid or ""):
                    po = social.get_post(pid)
                    if po:
                        import html as _h
                        if po.get("official"):
                            va = po["v"].get(lang or "pl") or po["v"]["pl"]
                            po = dict(po, nick=official.data()["account"].get(lang or "pl", po["nick"]), text=va["text"])
                            doc = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{notify.PUBLIC_URL.rstrip("/")}{po["img_url"]}">', doc)
                        dsc = _h.escape((po["nick"] + ": " + po["text"])[:200], quote=True)
                        doc = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{dsc}">', doc)
                        if po.get("img"): doc = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{notify.PUBLIC_URL}/api/wall/img/{po["img"]}">', doc)
                if u.path == "/agentka.html":
                    import html as _h
                    apid = parse_qs(u.query).get("id", ["luna"])[0][:12] or "luna"
                    ar = profiles._P().get(apid) if apid != "luna" else None
                    av = profiles.view(apid, lang or "pl", None, None, self._owner_plan(ar["uid"]) if ar else None)
                    if av:
                        ttl = _h.escape(av["name"] + " – " + {"en": "AI agent profile", "es": "perfil de agente IA", "de": "Profil der KI-Agentin", "uk": "профіль ШІ-агентки"}.get(lang, "profil agentki AI"), quote=True)
                        doc = re.sub(r"<title>[^<]*</title>", f"<title>{ttl} · Luna mówi jak jest</title>", doc, 1)
                        doc = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{ttl}">', doc, 1)
                        if av["bio"]: doc = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{_h.escape(av["bio"][:200], quote=True)}">', doc, 1)
                        if av["photos"] and not av["photos"][0]["url"].startswith("/api/"):
                            doc = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{notify.PUBLIC_URL.rstrip("/")}{av["photos"][0]["url"]}">', doc, 1)
                doc = promo_share.inject(doc, u.path, parse_qs(u.query), lang, notify.PUBLIC_URL.rstrip("/"), self._pid_plan)
                if u.path in ("/index.html", "/agentka.html", "/bitwy.html") and "owner-line.js" not in doc:   # 👑 linia własności agentki
                    doc = doc.replace("</body>", '<script src="/owner-line.js?v=1.0" defer></script>\n</body>', 1)
                if u.path not in ("/panel.html", "/admin-support.html") and "report.js" not in doc:   # Zgłoś 🚩 (arkusz zgłoszeń, 🚩 na zdjęciach) i Stan konta
                    doc = doc.replace("</body>", '<script src="/report.js?v=1.0" defer></script>\n<script src="/standing.js?v=1.0" defer></script>\n</body>', 1)
                if u.path not in ("/panel.html", "/privacy.html", "/regulamin.html", "/admin-support.html") and "agegate.js" not in doc:   # bramka „Masz 18 lat?” (po stronie klienta, bez wpływu na SEO)
                    doc = doc.replace("</body>", '<script src="/agegate.js?v=1.0" defer></script>\n</body>', 1)
                doc = moderator.inject(doc, self, u.path)   # ogłoszenie + (tylko dla konta admin) link „🛡️ Panel admina”
                NOIDX = u.path in ("/privacy.html", "/regulamin.html", "/panel.html", "/admin-support.html") or (u.path == "/agentka.html" and (parse_qs(u.query).get("id", ["luna"])[0] or "luna") != "luna")
                if NOIDX: doc = doc.replace("</head>", '<meta name="robots" content="noindex, follow">\n</head>', 1)
                doc = doc.replace("</head>", '<script src="/sec-client.js"></script>\n</head>', 1)
                b = doc.encode()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
                if NOIDX: self.send_header("X-Robots-Tag", "noindex, follow")
                self.send_header("Content-Language", lang or "pl"); self.send_header("Vary", "Accept-Language, Cookie"); self.end_headers(); self.wfile.write(b); return
        if u.path.endswith(".js") and os.path.basename(u.path) in i18n_pages.JS and u.path.count("/") == 1:
            lg = parse_qs(u.query).get("lang", [""])[0]
            if lg in seo.LANGS and lg != "pl":
                b = i18n_pages.js(os.path.basename(u.path), open(os.path.join(STATIC, u.path.lstrip("/")), encoding="utf-8").read(), lg).encode()
                self.send_response(200); self.send_header("Content-Type", "text/javascript; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
                self.end_headers(); self.wfile.write(b); return
        return super().do_GET()
    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/stripe/webhook":
            n = int(self.headers.get("Content-Length") or 0)
            if n > 256 * 1024: return self._json({"error": "too large"}, 413)
            raw = self.rfile.read(n)
            if not payments.verify(raw, self.headers.get("Stripe-Signature", "")): return self._json({"error": "bad signature"}, 400)
            try:
                vr = forms18_routes.webhook(json.loads(raw))   # weryfikacja 18+ (formularze testerów i castingu)
                if vr: return self._json({"ok": True, "result": vr})
            except Exception as e: sys.stderr.write("verify18 webhook %s\n" % type(e).__name__); return self._json({"error": "handler"}, 500)
            try: res = payments.handle(json.loads(raw), lambda uid, plan, m: _grant_and_notify(uid, plan, m, "stripe"), accounts.grant_item)
            except Exception as e: sys.stderr.write("webhook error %s\n" % type(e).__name__); return self._json({"error": "handler"}, 500)
            return self._json({"ok": True, "result": res})
        if not security.origin_ok(self.headers): return self._json({"error": "Niedozwolone źródło żądania."}, 403)
        try: nsfw_filter.set_lang(api_i18n.req_lang(u.query, self.headers) or "pl")  # język komunikatów filtra zdjęć
        except Exception: pass
        if moderator.gate(self, "POST"): return
        try: data = self._body()
        except ValueError as e:
            if str(e) == "too large": return self._json({"error": "Za duże żądanie."}, 413)
            return self._json({"error": "bad json"}, 400)
        except Exception: return self._json({"error": "bad json"}, 400)
        if not isinstance(data, dict): return self._json({"error": "bad json"}, 400)
        r = moderator.handle_post(self, u, data)
        if r is not None: return r
        if u.path.startswith(("/api/support/", "/api/admin/support")):
            r = support.handle_post(self, u, data)  # Pomoc na żywo + Napisz do moderatora (support.py) – pomoc działa zawsze, także przed potwierdzeniem 18+
            if r is not None: return r
        if u.path.startswith(("/api/forms/", "/api/admin/forms", "/api/account/confirm-adult")):
            r = forms18_routes.post(self, u, data, token_ok, casting_state()["open"], notify.PUBLIC_URL.rstrip("/"))
            if r is not None: return r
        if forms18_routes.needs_adult(self, u.path): return self._json({"error": "Potwierdź, że masz ukończone 18 lat.", "need_adult": True}, 403)
        r = reports_routes.write_blocked(self, u.path)   # czasowa / trwała blokada konta (3 poważne naruszenia)
        if r is not None: return r
        if u.path in ("/api/report", "/api/admin/reports"):
            r = reports_routes.post(self, u, data, token_ok)
            if r is not None: return r
        if u.path in ("/api/team/apply", "/api/admin/team"):   # „Dołącz do zespołu” (team.py)
            r = team.post(self, u, data, token_ok)
            if getattr(self, "_team_new", None):
                try: _mod_push("🤝 Dołącz do zespołu: nowe zgłoszenie", self._team_new["nick"] + ": " + ", ".join(team.AREA_PL[a] for a in self._team_new["areas"]))
                except Exception: pass
            if r is not None: return r
        r = self._post_account(u, data)
        if r is not None: return r
        if u.path.startswith(("/api/inbox", "/api/friends", "/api/dm", "/api/admin/inbox")):
            r = inbox.handle_post(self, u, data)  # Skrzynka, Znajomi, czat 1:1 (inbox.py)
            if r is not None: return r
        if u.path in ("/api/agent/video", "/api/agent/video/delete"):
            # Generator filmów agentki: Premium 30 s/720p, Pro / Ultra 60 s/1080p, twardy limit 60 s; tylko sama agentka
            pl, uid = self._plan()
            if not uid: return self._json({"error": "Zaloguj się.", "login": True}, 401)
            if not livechat.rate_ok("vid:" + uid, 10, 300): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            try:
                if u.path.endswith("/delete"): agentvideo.delete(uid, str(data.get("id", ""))); return self._json({"ok": True})
                r, err = agentvideo.submit(uid, self._gen_plan(pl, uid), data)
                if err: return self._json(err, 402)
                return self._json({"ok": True, **r})
            except PermissionError as e: return self._json({"error": str(e)}, 429)
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path in ("/api/admin/agentgen", "/api/admin/agent/real"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try:
                if u.path.endswith("/real"):  # tylko przy potwierdzonej współpracy (umowa + zgoda) – flaga real_person na agentce
                    return self._json(profiles.admin_real_photo(str(data.get("pid", "")), data.get("data"), data.get("agreement")))
                agentgen.moderate(str(data.get("job", "")), [str(x) for x in (data.get("approve") or [])], lambda ou: self._gen_plan(self._owner_plan(ou), ou))
                return self._json({"ok": True, "items": agentgen.admin_list()})
            except PermissionError as e: return self._json({"error": str(e)}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path in ("/api/agent/gen", "/api/agent/gen/pick", "/api/agent/gen/video"):
            pl, uid = self._plan()
            if not uid: return self._json({"error": "Zaloguj się.", "login": True}, 401)
            if not livechat.rate_ok("agen:" + uid, 20, 600): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            gp = self._gen_plan(pl, uid)
            try:
                if u.path.endswith("/pick"): return self._json({"ok": True, "job": agentgen.pick(uid, str(data.get("job", "")), [str(x) for x in (data.get("ids") or [])][:8])})
                r, err = (agentgen.submit_video(uid, gp, None) if u.path.endswith("/video") else agentgen.submit(uid, gp, data))
                if err: return self._json(err, 402)
                try: _mod_push("Generator agentek: nowe zadanie", r["kind"])
                except Exception: pass
                return self._json({"ok": True, "job": r})
            except PermissionError as e: return self._json(dict(quality.lock("pro", "gen"), error=str(e)), 402)   # opcje Pro/Ultra
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path == "/api/admin/videos":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try: agentvideo.admin_action(str(data.get("id", "")), data.get("action"))
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "items": agentvideo.admin_list()})
        if u.path == "/api/me/lang":
            _pl, uid = self._plan()
            if not uid: return self._json({"ok": True, "saved": False})
            try: userprof.set_lang(uid, str(data.get("lang", ""))); return self._json({"ok": True, "saved": True})
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path in ("/api/me/profile", "/api/me/avatar", "/api/agent/generate"):
            # Mój panel: anonimowy profil użytkownika (nick) + Generator agentek (402 z nazwą planu)
            pl, uid = self._plan()
            if not uid: return self._json({"error": "Zaloguj się.", "login": True}, 401)
            if not livechat.rate_ok("me:" + uid, 30, 600): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            try:
                if u.path == "/api/agent/generate":  # v1.6.6: zastąpione Generatorem z opisu (bez gotowych zdjęć Luny jako „generacji”)
                    return self._json({"error": "Generator działa teraz z opisu: Mój panel → Generator agentek.", "moved": "/ustawienia.html#gen"}, 410)
                    r, err = profiles.generate(uid, self._gen_plan(pl, uid), str(data.get("base", "")), str(data.get("crop", "portret")))
                    if err: return self._json(err, 402)
                    return self._json({"ok": True, **r})
                if u.path == "/api/me/avatar":
                    ref, px = userprof.set_avatar_upload(uid, pl, data.get("data"))
                    try: _mod_push("Nowy awatar użytkownika do akceptacji", userprof.nick_of(uid))
                    except Exception: pass
                    return self._json({"ok": True, "avatar": ref, "px": px, "pending": True})
                if str(data.get("avatar", "")).startswith("gen:"):
                    if not plans.has(pl, "premium"): return self._json(quality.lock("premium"), 402)
                    pid, rr = profiles.mine(uid)
                    if not rr or not rr.get("own") or str(data["avatar"])[4:] != rr.get("own"): return self._json({"error": "Najpierw wygeneruj obraz w Generatorze agentek."}, 400)
                r = userprof.save(uid, data)
                return self._json({"ok": True, "profile": r})
            except PermissionError as e: return self._json({"error": str(e)}, 429 if "limit" in str(e) else 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path in ("/api/agent/profile", "/api/agent/profile/own"):
            # profil własnej agentki: plan sprawdzany na serwerze (Premium: opis + 4 zdjęcia, Pro / Ultra: 12 zdjęć + przypięte)
            pl, uid = self._plan()
            if not uid: return self._json({"error": "Zaloguj się, aby edytować profil agentki.", "login": True}, 401)
            if not livechat.rate_ok("prof:" + uid, 20, 600): return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            try:
                if u.path.endswith("/own"):  # v1.6.6: brak wgrywania zdjęć do agentki dla zwykłych użytkowników (ścieżka tylko dla admina przy współpracy)
                    return self._json({"error": "Agentki tworzysz z opisu w Generatorze – bez wgrywania zdjęć.", "moved": "/ustawienia.html#gen"}, 410)
                    h, err = profiles.save_own(uid, pl, data.get("data"), data.get("ai_declared"))
                    if err: return self._json(err, 402)
                    return self._json({"ok": True, "own": h, "ref": "own:" + h})
                items = (accounts._accts().get(uid) or {}).get("items", [])
                r, err = profiles.save(uid, pl, items, data)
            except PermissionError as e: return self._json({"error": str(e), "camera": True}, 422)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            if err: return self._json(err, 402)
            return self._json({"ok": True, "id": r["id"], "public": r["public"]})
        if u.path == "/api/admin/partners":
            # „Agentka współpracująca”: tylko ręcznie, po zgodzie twórcy; nigdy Luna
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            def _look(uid):
                pid, r = profiles.mine(uid); e = battles.my_entry(uid)
                return {"agent": (r or {}).get("name") or (e or {}).get("name") or "?", "profile": pid or "", "battle": (e or {})["id"] if e else ""}
            if data.get("action") == "set":
                ref = str(data.get("ref", "")).strip()[:20]
                if ref.lower() in ("luna", "off-luna") or not ref: return self._json({"error": "Luny (oficjalnej agentki) nie można oznaczyć."}, 400)
                uid = (profiles._P().get(ref) or {}).get("uid") or next((e["uid"] for e in battles._entries() if e["id"] == ref), None)
                try: partners.admin_set(uid, data.get("on") is True, data.get("optin"), data.get("campaigns"))
                except KeyError as e: return self._json({"error": str(e)}, 404)
                except ValueError as e: return self._json({"error": str(e)}, 400)
                security.audit("partner " + ("on" if data.get("on") is True else "off"), self._ip(), ref)
            return self._json({"ok": True, "items": partners.admin_list(_look)})
        if u.path == "/api/admin/agent-profile":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try: return self._json({"ok": True, "profile": profiles.admin(str(data.get("id", ""))[:12], data.get("action"))})
            except (KeyError, ValueError) as e: return self._json({"error": str(e)}, 400)
        if u.path == "/api/agent/custom":
            # zapis/trening własnej agentki: serwer sprawdza plan dla każdej opcji
            pl, _uid = self._plan()
            err = training.check(pl, data if isinstance(data, dict) else {}, globals()["CAT"])
            if err: return self._json(err, 402)
            return self._json({"ok": True, "plan": pl})
        if u.path == "/api/chat":
            q = str(data.get("message", "")).strip()[:1000]
            if not q: return self._json({"error": "empty"}, 400)
            if code_candidate(q):
                tok = check_code(self._ip(), q)
                security.audit("admin_login_ok" if tok else "admin_login_fail", self._ip())
                if tok: return self._json({"admin_token": tok, "ttl": ADMIN_TTL, "reply": "Tryb producenta odblokowany."})
            pl, uid = self._plan(); lim_keys = None
            if pl == "darmowy":
                lim_keys = plans.keys_for(uid, str(data.get("vid", "")) if livechat.VID_RE.fullmatch(str(data.get("vid", ""))) else "", self._ip())
                if not plans.chat_allowed(lim_keys, CFG["free"]["chat_minutes"]):
                    return self._json({"error": "limit", "limit": True, "reply": f"Na dziś wykorzystano limit planu Darmowy (ok. {CFG['free']['chat_minutes']} min rozmowy). Wróć jutro albo wybierz plan Podstawowa lub wyższy – płatności wkrótce. Luna to asystentka AI."}, 402)
            hist = data.get("history")
            pers, plocked = training.strip_persona(pl, data.get("persona"))
            ag = next((a for a in globals()["CAT"]["agents"] if a["id"] == pers.get("agent")), None)
            if ag and not plans.has(pl, ag.get("plan", "darmowy")): pers.pop("agent", None); plocked.append("agent")
            ctx = persona_ctx(pers)
            rr = rule_reply(q)
            if rr:
                if lim_keys: plans.add(lim_keys, 6)
                return self._json({"reply": disclose(rr, hist, ctx["name"]), "source": "rule"})
            ov = kb_override(q)
            if ov: return self._json({"reply": disclose(shape(ov, ctx), hist, ctx["name"]), "source": "kb_custom"})
            a = llm_answer(q, hist, ctx); src = "llm"
            if not a: a, src = shape(knowledge.answer(q), ctx), "offline"
            a = disclose(a, hist, ctx["name"])
            if lim_keys: plans.add(lim_keys, plans.speech_secs(q, a) + 8)
            return self._json({"reply": a, "source": src, **({"persona_locked": plocked} if plocked else {})})
        if u.path == "/api/admin/backup":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            n = {}
            for k in ("testers", "push_subs", "email_subs"):
                v = data.get(k)
                if isinstance(v, dict):
                    cur = store.get(k, {}) or {}; cur.update({str(a): b for a, b in v.items() if isinstance(b, dict)}); store.put(k, cur); n[k] = len(v)
            return self._json({"ok": True, "imported": n})
        if u.path == "/api/testers/signup":
            if not livechat.rate_ok("tst:" + self._ip(), 3, 10): return self._json({"error": "Za dużo prób – spróbuj później."}, 429)
            if not antibot.turnstile_ok(self._ts_token(data), self._ip()): return self._json({"error": "Potwierdź, że nie jesteś botem, i spróbuj ponownie.", "turnstile": True}, 403)
            try: code, left = testers.signup(data, hashlib.sha256(("luna" + self._ip()).encode()).hexdigest()[:16])
            except OverflowError as e: return self._json({"error": str(e), "full": True}, 409)
            except age.Underage as e: return self._json({"error": str(e), "underage": True}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "code": code, "remaining": left})
        if u.path in ("/api/admin/testers/grant", "/api/admin/testers/delete"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try:
                if u.path.endswith("delete"): testers.delete(str(data.get("code"))); return self._json({"ok": True})
                return self._json({"ok": True, "tester": testers.grant(str(data.get("code")), bool(data.get("on")), data.get("ring"))})
            except KeyError: return self._json({"error": "not found"}, 404)
        if u.path == "/api/live-room/join":
            vid = str(data.get("vid", ""))
            if livechat.VID_RE.fullmatch(vid) and livechat.rate_ok("join:" + self._ip(), 10, 200): liveroom.add_greet(vid, data.get("name", ""))
            return self._json({"ok": True})
        if u.path == "/api/live-room/chat":
            ip = self._ip(); vid = str(data.get("vid", ""))
            if not livechat.VID_RE.fullmatch(vid): return self._json({"error": "bad id"}, 400)
            if not (livechat.rate_ok("lip:" + ip, 12, 600) and livechat.rate_ok("lvid:" + vid, 8, 400) and livechat.rate_ok("lall", 200, 20000)):
                return self._json({"error": "Za szybko – odczekaj chwilę."}, 429)
            text = livechat.clean_text(data.get("text", ""), 300); ask = bool(data.get("ask")); cmd = text.split(" ", 1)[0].lower() if text.startswith("!") else ""
            if cmd in ("!pomoc", "!help", "!komendy"): return self._json({"ok": True, "system": HELP})
            if cmd == "!pytanie": text = text[len(cmd):].strip(); ask = True
            if ask and self._plan()[0] == "darmowy" and not CFG["free"]["live_questions"]:
                return self._json({"error": "W planie Darmowy możesz oglądać Luna Live i pisać na czacie, ale pytania do Luny są dostępne od planu Podstawowa (płatności wkrótce).", "plan_required": "podstawowa"}, 402)
            if cmd and cmd not in COMMANDS and cmd not in ("!pytanie", "!temat"): return self._json({"ok": True, "system": "Nieznana komenda. " + HELP})
            av = "" if vid[:8] in avatars.blocked_uids() else data.get("avatar", "")
            try: m = liveroom.post(vid, data.get("name", ""), av, text, ask, self._ring(data), nicktier.of_uid(self._who()[0]))
            except PermissionError as e: return self._json({"error": str(e)}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            liveroom.add_greet(vid, m["name"])
            sysmsg = None
            if cmd in COMMANDS or cmd == "!temat":
                if not liveroom.cmd_ok(vid, 90): sysmsg = "Komendę można użyć raz na półtorej minuty."
                elif cmd == "!temat": liveroom.add_job({"kind": "topic", "title": "Temat", "text": f"Dzisiejszy temat: {liveroom.S['topic'] or 'pytania z czatu i ćwiczenia głosu'}."}); sysmsg = "Luna za chwilę przypomni temat."
                else:
                    t, tx = exercise(COMMANDS[cmd])
                    sysmsg = "Luna dodała ćwiczenie do kolejki." if liveroom.add_job({"kind": "exercise", "title": t, "text": f"{m['name']} prosi o ćwiczenie. " + tx}) else "Kolejka jest pełna – spróbuj za chwilę."
            elif ask: sysmsg = "Pytanie trafiło do kolejki Luny."
            return self._json({"ok": True, "msg": m, "system": sysmsg})
        if u.path == "/api/admin/live-room":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            a = data.get("action"); arg = data.get("id")
            try:
                if a == "start": liveroom.set_topic(data.get("topic", "")); liveroom.set_mode("on")
                elif a == "stop": liveroom.set_mode("off" if sched()["in_window"] else "auto")
                elif a == "schedule": liveroom.set_mode("auto")
                elif a == "topic": liveroom.set_topic(data.get("topic", ""))
                elif a == "auto": liveroom.set_auto(bool(data.get("value")))
                elif a == "approve":
                    j = question_job(int(arg))
                    if j: liveroom.add_job(j, front=True)
                elif a == "reject": liveroom.reject(int(arg))
                elif a == "delete": liveroom.delete_msg(int(arg))
                elif a == "ban": liveroom.ban(str(arg), True)
                elif a == "unban": liveroom.ban(str(arg), False)
                elif a == "exercise":
                    ex = exercise(str(arg))
                    if ex: liveroom.add_job({"kind": "exercise", "title": ex[0], "text": ex[1]}, front=True)
                else: return self._json({"error": "unknown action"}, 400)
            except (TypeError, ValueError): return self._json({"error": "bad id"}, 400)
            return self._json({"ok": True, "state": liveroom.public_state(0, mod=True)})
        if u.path == "/api/push/subscribe":
            if not livechat.rate_ok("psub:" + self._ip(), 10, 100): return self._json({"error": "limit"}, 429)
            a = self._acct()
            try: notify.subscribe(data.get("sub"), data.get("topics"), a[0]["uid"] if a else None, mod=token_ok(self.headers.get("X-Admin-Token"))); return self._json({"ok": True})
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path == "/api/push/unsubscribe":
            notify.unsubscribe(str((data.get("sub") or {}).get("endpoint", data.get("endpoint", "")))); return self._json({"ok": True})
        if u.path == "/api/email/subscribe":
            if not livechat.rate_ok("esub:" + self._ip(), 3, 20): return self._json({"error": "Za dużo prób – spróbuj później."}, 429)
            try: _, conf = notify.email_subscribe(data.get("email"), data.get("consent"), self._ip())
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "confirmed": conf, "email_enabled": notify.email_enabled(),
                               "message": "Sprawdź skrzynkę i potwierdź zapis." if notify.email_enabled() else "Zapisaliśmy Twój adres. Wyślemy prośbę o potwierdzenie, gdy uruchomimy wysyłkę e-maili."})
        if u.path == "/api/email/unsubscribe":
            notify.email_unsubscribe(parse_qs(u.query).get("t", [""])[0] or str(data.get("t", ""))); return self._json({"ok": True})
        if u.path == "/api/cron":
            sec = self.headers.get("X-Cron-Secret", "")
            if not notify.CRON_SECRET or not hmac.compare_digest(sec.encode(), notify.CRON_SECRET.encode()): return self._json({"error": "unauthorized"}, 401)
            out = run_reminders()
            return self._json({"ok": True, "actions": [a for a, _ in out], "live": liveroom.S["on"], "next": sched()["next_label"]})
        if u.path in ("/api/admin/notify/push", "/api/admin/notify/email-test"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try:
                if u.path.endswith("email-test"): return self._json({"ok": True, "status": notify.test_email(data.get("to"))})
                topic = data.get("topic") if data.get("topic") in ("live", "video", "update") else "manual"
                title = livechat.clean_text(data.get("title", ""), 80); body = livechat.clean_text(data.get("body", ""), 200)
                if not title: return self._json({"error": "Podaj tytuł."}, 400)
                return self._json({"ok": True, **notify.send_push(topic, title, body, str(data.get("url") or "/"))})
            except Exception as e: return self._json({"error": str(e)[:200]}, 400)
        if u.path == "/api/live/send":
            ip = self._ip(); vid = str(data.get("vid", ""))
            if not livechat.VID_RE.fullmatch(vid): return self._json({"error": "bad id"}, 400)
            if not (livechat.rate_ok("ip:" + ip, 8, 300) and livechat.rate_ok("vid:" + vid, 6, 150) and livechat.rate_ok("all", 120, 5000)):
                return self._json({"error": "Za dużo wiadomości – spróbuj za chwilę."}, 429)
            if vid[:8] in liveroom.S["banned"]: return self._json({"error": "Nie możesz pisać na tym czacie."}, 403)
            av = "" if vid[:8] in avatars.blocked_uids() else data.get("avatar", "")
            try: msgs = livechat.visitor_send(vid, data.get("name", ""), av, data.get("text", ""), CFG.get("chat_notice", ""), self._ring(data), nicktier.of_uid(self._who()[0]))
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "msgs": msgs})
        if u.path in ("/api/admin/live/reply", "/api/admin/live/delete"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            vid = str(data.get("vid", ""))
            try:
                if u.path.endswith("/delete"): livechat.delete(vid); return self._json({"ok": True})
                return self._json({"ok": True, "msgs": livechat.reply(vid, data.get("text", ""))})
            except KeyError: return self._json({"error": "not found"}, 404)
            except ValueError as e: return self._json({"error": str(e)}, 400)
        if u.path == "/api/tts":
            return self._tts(data)
        if u.path in ("/api/admin/catalog", "/api/admin/catalog/reset", "/api/admin/upload"):
            global CAT
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            try:
                if u.path == "/api/admin/upload":
                    raw = base64.b64decode(str(data.get("data", "")).split(",")[-1], validate=False)
                    return self._json({"ok": True, "url": catalog.save_upload(str(data.get("name", "")), raw)})
                CAT = catalog.save(catalog.DEFAULT if u.path.endswith("/reset") else data.get("catalog", {}))
                return self._json({"ok": True, "catalog": CAT, "public": catalog.public(CAT)})
            except Exception as e:
                return self._json({"error": str(e)}, 400)
        if u.path in ("/api/admin/config", "/api/admin/reset", "/api/admin/logout"):
            tok = self.headers.get("X-Admin-Token")
            if not token_ok(tok): return self._json({"error": "unauthorized"}, 401)
            if u.path == "/api/admin/logout":
                with _adm_lock: _tokens.pop(tok, None)
                return self._json({"ok": True})
            try: c = save_cfg({} if u.path == "/api/admin/reset" else data.get("config", {}))
            except Exception as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "config": c})
        self._json({"error": "not found"}, 404)
    def _tts(self, q):
        text = str(q.get("text", "")).strip()
        if not text: return self._json({"error": "empty text"}, 400)
        try:
            vd = CFG["voice_defaults"]; g = lambda k: q.get(k, vd.get(k))
            p = tts(text, g("voice") or DEFAULT_VOICE, g("pitch"), g("volume"),
                    str(g("spanish")).lower() not in ("0", "false", "no"), g("rate"), g("warmth"),
                    g("hz") if g("hz") is not None else 0, g("rasp") or 0, g("breath") or 0,
                    str(g("lisp")).lower() in ("1", "true", "yes"))
        except Exception as e:
            print("TTS error:", repr(e), file=sys.stderr)
            return self._json({"error": "tts failed"}, 502)
        b = open(p, "rb").read()
        self.send_response(200); self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers(); self.wfile.write(b)

if __name__ == "__main__":
    port = int(os.getenv("PORT", sys.argv[1] if len(sys.argv) > 1 else 8765))
    print(f"Luna działa na http://0.0.0.0:{port}")
    try: moderator.ensure_admin()   # konto właściciela (LUNA_ADMIN_NICK + LUNA_ADMIN_PASSWORD_HASH) z rolą admin
    except Exception as e: print("ensure_admin", repr(e)[:200], file=sys.stderr)
    try: userprof.seed_moderator()
    except Exception as e: sys.stderr.write("seed_moderator %s\n" % type(e).__name__)
    threading.Thread(target=_bg_loop, daemon=True).start()
    threading.Thread(target=_announce_update, daemon=True).start()
    try: inbox.announce_version(VERSION, INBOX_NEWS.get(VERSION))  # „Co nowego” trafia też do Skrzynki (kategoria Aktualizacje)
    except Exception as e: print("inbox news", repr(e)[:200], file=sys.stderr)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
