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
import catalog, base64
import official, i18n_pages, stats, antibot, owner, social, helpbot, seo, tickets, butik, join, payments, plans, accounts, avatars, security, age, livechat, liveroom, library, store, notify, testers
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
    WAW = ZoneInfo("Europe/Warsaw")
except Exception:
    WAW = None

VERSION = "1.4.2"
ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)

VOICES = {
    "pl-PL-ZofiaNeural": "Zofia – najczystszy polski (domyślny)",
    "pt-BR-ThalitaMultilingualNeural": "Thalita – wielojęzyczny, latynoski tembr",
    "de-DE-SeraphinaMultilingualNeural": "Seraphina – wielojęzyczny, ciepły",
    "en-US-AvaMultilingualNeural": "Ava – wielojęzyczny, miękki",
    "es-ES-XimenaNeural": "Ximena – mocny hiszpański akcent (słabo zrozumiała po polsku)",
    "es-MX-DaliaNeural": "Dalia – meksykański akcent (słabo zrozumiała po polsku)",
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
def admin_enabled(): return bool(_admin_hash() or admin_code())
QUOTES = "\"'„”“«»‚‘’`"
def strip_code(msg):
    m = msg.strip()
    while len(m) >= 2 and m[0] in QUOTES and m[-1] in QUOTES:
        m = m[1:-1].strip()
    return m
def admin_code():
    # tolerujemy białe znaki i cudzysłowy wokół wartości zmiennej środowiskowej
    return strip_code(os.getenv("LUNA_ADMIN_CODE", "").replace("\ufeff", ""))
def code_candidate(msg):
    # Liczymy jako próbę tylko wiadomości podobne do kodu – zwykłe pytania nie zużywają limitu prób.
    m = strip_code(msg)
    if _admin_hash(): return 4 <= len(m) <= 64 and not re.search(r"\s", m)
    code = admin_code()
    return bool(code) and len(m) == len(code)
def code_matches(msg):
    m = strip_code(msg).encode()
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
    text = text.strip()[:1200]
    key = hashlib.sha1(json.dumps([text, voice, round(pitch_st, 2), round(lufs, 1), bool(spanish), rate, round(warmth, 1), hz, round(rasp, 1), round(breath, 1), lisp, 5]).encode()).hexdigest()
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

def _bg_loop():
    n = 0
    while True:
        try: director_tick()
        except Exception as e: print("director error", repr(e)[:200], file=sys.stderr)
        n += 1
        if n % 60 == 0:
            try: run_reminders()
            except Exception as e: print("reminder error", repr(e)[:200], file=sys.stderr)
        time.sleep(1)

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
stats.threadsafe_start()

def _help_prices():
    if not CFG["pricing"]["show"]: return None
    P = CFG["pricing"]["plans"]; return {"premium": P["premium"]["pln"].replace(".", ","), "pro": P["pro"]["pln"].replace(".", ",")}
helpbot.PRICES = _help_prices

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=STATIC, **k)
    def log_message(self, fmt, *args): sys.stderr.write("%s %s\n" % (security.ip_hash(self.address_string()), security.redact(fmt % args)))
    def end_headers(self):
        if urlparse(self.path).path.endswith((".html", "/", ".js", ".css", ".json")):
            self.send_header("Cache-Control", "no-cache")
        for k, v in security.HEADERS.items(): self.send_header(k, v)
        for c in getattr(self, "_cookies", []): self.send_header("Set-Cookie", c)
        self._cookies = []
        super().end_headers()
    def _cookie(self, name):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name: return v
        return ""
    def _set_sid(self, sid, max_age):
        self._cookies = getattr(self, "_cookies", []) + [f"luna_sid={sid}; Path=/; Max-Age={max_age}; HttpOnly; Secure; SameSite=Lax"]
    def _acct(self):
        return accounts.session(self._cookie("luna_sid"))
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
    def _csrf_ok(self, csrf):
        t = self.headers.get("X-CSRF-Token") or ""
        return bool(t) and hmac.compare_digest(t, csrf)
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        return True
    def _ip(self):
        xf = self.headers.get("X-Forwarded-For")
        return xf.split(",")[0].strip() if xf else self.client_address[0]
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        p = urlparse(self.path).path
        lim = 9 * 1024 * 1024 if p in ("/api/admin/upload", "/api/admin/backup") else 7 * 1024 * 1024 if p in ("/api/avatar/upload", "/api/tickets", "/api/wall/post") else 64 * 1024
        if n > lim: raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

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
            ok, why = antibot.signup_check(str(data.get("email", "")), ip, self.headers.get("User-Agent", ""), data)
            if not ok: return self._json({"error": "Nie udało się założyć konta." if why == "honeypot" else why}, 400 if why == "honeypot" else 429 if "sieci" in why else 400)
            try: uid, sent = accounts.signup(data, notify.PUBLIC_URL)
            except age.Underage as e: return self._json({"error": str(e), "underage": True}, 403)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            antibot.on_write("u:" + uid, ip, self.headers.get("User-Agent", ""), str(data.get("email", "")).split("@")[0][:3] + "…@" + str(data.get("email", "")).rsplit("@", 1)[-1])
            sid, csrf = accounts.new_session(uid); self._set_sid(sid, accounts.SESSION_DAYS * 86400)
            return self._json({"ok": True, "verification_sent": sent, "csrf": csrf, "user": accounts.public(accounts._accts()[uid])})
        if p == "/api/account/login":
            if not (livechat.rate_ok("li:" + ip, 6, 60) and livechat.rate_ok("li:*", 120, 5000)): return self._json({"error": "Za dużo prób logowania – odczekaj chwilę."}, 429)
            try: uid = accounts.login(data.get("email"), data.get("password"))
            except PermissionError as e: return self._json({"error": str(e), "locked": True}, 423)
            except ValueError as e: return self._json({"error": str(e)}, 401)
            sid, csrf = accounts.new_session(uid); self._set_sid(sid, accounts.SESSION_DAYS * 86400)
            return self._json({"ok": True, "csrf": csrf, "user": accounts.public(accounts._accts()[uid])})
        if p in ("/api/account/logout", "/api/account/delete", "/api/account/link-tester", "/api/account/declare"):
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się."}, 401)
            usr, csrf = a
            if not self._csrf_ok(csrf): return self._json({"error": "Nieprawidłowy token CSRF – odśwież stronę."}, 403)
            if p == "/api/account/logout":
                accounts.end_session(self._cookie("luna_sid")); self._set_sid("", 0); return self._json({"ok": True})
            if p == "/api/account/delete":
                if not livechat.rate_ok("del:" + ip, 3, 20): return self._json({"error": "Za dużo prób."}, 429)
                try: accounts.delete(usr["uid"], data.get("password") or None)
                except ValueError as e: return self._json({"error": str(e)}, 400)
                social.anonymise_author("u:" + usr["uid"]); antibot.forget("u:" + usr["uid"])
                self._set_sid("", 0); return self._json({"ok": True})
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
                else: accounts.grant_pass(str(data.get("uid")), data.get("plan"), data.get("months", 1))
            except KeyError: return self._json({"error": "not found"}, 404)
            except ValueError as e: return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "accounts": accounts.admin_list()})
        if p == "/api/join":
            if not (livechat.rate_ok("join:" + ip, 2, 6) and livechat.rate_ok("join:*", 30, 300)): return self._json({"error": "Za dużo zgłoszeń – spróbuj później."}, 429)
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
                elif ev in ("click", "share", "cart") and re.fullmatch(r"[A-Za-z0-9_-]{16,64}", sid) and stats.once(sid, k + ":" + ev): stats.add(k + ":" + ev)
            return self._json({"ok": True})
        if p == "/api/admin/login":
            if not livechat.rate_ok("al:" + ip, 5, 60): return self._json({"error": "Za dużo prób."}, 429)
            tok = check_code(ip, str(data.get("passphrase", ""))[:80])
            if not tok: return self._json({"error": "Nieprawidłowy kod."}, 401)
            return self._json({"admin_token": tok, "ttl": ADMIN_TTL})
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
                    elif data.get("action"): social.moderate(data.get("kind"), str(data.get("id", "")), data.get("action"), data.get("variants"))
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
            if act == "remove": avatars.block(uid, True)
            elif act == "restore": avatars.block(uid, False)
            elif act == "ban": avatars.block(uid, True); liveroom.ban(uid, True)
            elif act == "dismiss": avatars.dismiss(id_)
            else: return self._json({"error": "bad action"}, 400)
            return self._json({"ok": True, "items": avatars.admin_list()})
        return None
    def _get_account(self, u):
        p = u.path
        if p == "/api/butik":
            adm = token_ok(self.headers.get("X-Admin-Token"))
            d = butik.public(CFG["pricing"]["show"] or adm); d["preview"] = adm and not CFG["pricing"]["show"]
            d["plans"] = [{"id": k, "name": plans.NAMES[k], **({"prices": (v if CFG["pricing"]["foreign"] else {"pln": v["pln"]})} if CFG["pricing"]["show"] or adm else {})} for k, v in CFG["pricing"]["plans"].items()]; d["foreign"] = CFG["pricing"]["foreign"]
            d["payments"] = {"web": payments.enabled(), "mode": payments.mode() if adm else None, "methods": ["BLIK", "karta / card"] + (["Przelewy24"] if payments.P24 else [])}
            return self._json(d)
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
                return self._json(social.feed("top" if (q.get("sort") or [""])[0] == "top" else "new", int(b) if b.isdigit() else None, lim, uid, dev, lg if lg in social.LANGS else "pl"))
            if p.startswith("/api/wall/img/"):
                return self._dataurl(social.wall_img(p.rsplit("/", 1)[-1]))
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
        if p == "/api/account/export":
            a = self._acct()
            if not a: return self._json({"error": "Zaloguj się."}, 401)
            b = json.dumps(accounts.export(a[0]["uid"]), ensure_ascii=False, indent=2).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=luna-moje-dane.json"); self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b); return True
        if p == "/api/account/verify":
            ok = accounts.verify(parse_qs(u.query).get("token", [""])[0])
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
        if u.path.startswith(("/api/wall", "/api/comments", "/api/votes", "/api/admin/social", "/api/admin/wall/img/", "/api/help", "/api/admin/help", "/api/tickets", "/api/admin/tickets", "/api/seller", "/api/casting", "/api/account/", "/api/admin/users", "/api/admin/avatars", "/api/admin/audit", "/api/butik", "/api/support", "/api/admin/butik", "/api/admin/join")):
            r = self._get_account(u)
            if r is not None: return r
        if u.path == "/api/voices":
            return self._json({"voices": VOICES, "default": DEFAULT_VOICE})
        if u.path == "/api/tts":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return self._tts(q)
        if u.path == "/api/config":
            return self._json({k: CFG[k] for k in ("greeting", "wake_reply", "ai_first", "ai_tag", "chat_notice", "voice_defaults", "ui", "music", "live", "free", "pay_notice", "app", "features")})
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
            return self._json(pub)
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
        if u.path in ("/api/admin/stats", "/api/admin/suspects"):
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
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
            st.update(viewers=n, sched=sched(), help=HELP, ai_label="Luna – asystentka AI (postać wygenerowana sztucznie)")
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
        elif u.path == "/":
            # Strona główna = feed (Ścianka Agentek Głosu). Aplikacja TWA/PWA (start_url /app, ?source=twa|pwa) dostaje czat.
            qs = parse_qs(u.query); ref = self.headers.get("Referer", "")
            if qs.get("source", [""])[0] in ("twa", "pwa") or "platnosc" in qs or ref.startswith("android-app://"):
                u = u._replace(path="/index.html")
            else:
                u = u._replace(path="/promo.html")
        elif "." not in u.path.rsplit("/", 1)[-1] and re.fullmatch(r"/[a-z0-9-]{2,30}", u.path) and os.path.isfile(os.path.join(STATIC, u.path[1:] + ".html")):
            self.send_response(301); self.send_header("Location", u.path + ".html" + ("?" + u.query if u.query else "")); self.send_header("Content-Length", "0"); self.end_headers(); return
        if u.path.endswith(".html"):
            fp = os.path.join(STATIC, u.path.lstrip("/"))
            if os.path.isfile(os.path.realpath(fp)) and os.path.realpath(fp).startswith(os.path.realpath(STATIC)):
                lang = parse_qs(u.query).get("lang", [""])[0]
                lang = lang if lang in seo.LANGS else ""
                doc = seo.localize(open(fp, encoding="utf-8").read(), u.path, lang, notify.PUBLIC_URL.rstrip("/"))
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
                NOIDX = u.path in ("/privacy.html", "/regulamin.html", "/panel.html")
                if NOIDX: doc = doc.replace("</head>", '<meta name="robots" content="noindex, follow">\n</head>', 1)
                b = doc.encode()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
                if NOIDX: self.send_header("X-Robots-Tag", "noindex, follow")
                self.send_header("Content-Language", lang or "pl"); self.send_header("Vary", "Accept-Language"); self.end_headers(); self.wfile.write(b); return
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
            try: res = payments.handle(json.loads(raw), lambda uid, plan, m: accounts.grant_pass(uid, plan, m, by="stripe"), accounts.grant_item)
            except Exception as e: sys.stderr.write("webhook error %s\n" % type(e).__name__); return self._json({"error": "handler"}, 500)
            return self._json({"ok": True, "result": res})
        if not security.origin_ok(self.headers): return self._json({"error": "Niedozwolone źródło żądania."}, 403)
        try: data = self._body()
        except ValueError as e:
            if str(e) == "too large": return self._json({"error": "Za duże żądanie."}, 413)
            return self._json({"error": "bad json"}, 400)
        except Exception: return self._json({"error": "bad json"}, 400)
        if not isinstance(data, dict): return self._json({"error": "bad json"}, 400)
        r = self._post_account(u, data)
        if r is not None: return r
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
            ctx = persona_ctx(data.get("persona"))
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
            return self._json({"reply": a, "source": src})
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
            try: m = liveroom.post(vid, data.get("name", ""), av, text, ask, self._ring(data))
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
            try: msgs = livechat.visitor_send(vid, data.get("name", ""), av, data.get("text", ""), CFG.get("chat_notice", ""), self._ring(data))
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
    threading.Thread(target=_bg_loop, daemon=True).start()
    threading.Thread(target=_announce_update, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
