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
import livechat, liveroom, library, store, notify, testers
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
    WAW = ZoneInfo("Europe/Warsaw")
except Exception:
    WAW = None

VERSION = "1.3.0"
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
 "Rozmawiasz z Hubertem po polsku, z hiszpańskim temperamentem i od czasu do czasu wplatasz hiszpańskie słowa (cariño, hola, mi amor – oszczędnie). "
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
    ui = new.get("ui") if isinstance(new.get("ui"), dict) else {}
    col = str(ui.get("ring_color", "")).strip()
    c["ui"] = {"ring_color": col if re.fullmatch(r"#[0-9a-fA-F]{6}", col) else DEFAULTS["ui"]["ring_color"],
               "pulse_speed": _num(ui.get("pulse_speed"), 0.4, 4, DEFAULTS["ui"]["pulse_speed"]),
               "holo_default": bool(ui.get("holo_default", False)),
               "holo_plan": ui.get("holo_plan") if ui.get("holo_plan") in ("podstawowa", "premium", "pro") else "podstawowa"}
    m = new.get("music") if isinstance(new.get("music"), dict) else {}
    tr = m.get("tracks") if isinstance(m.get("tracks"), list) else DEFAULTS["music"]["tracks"]
    c["music"] = {"volume": _num(m.get("volume"), 0, 1, DEFAULTS["music"]["volume"]),
        "tracks": [{"title": str(t.get("title", ""))[:120], "artist": str(t.get("artist", ""))[:120], "url": str(t.get("url", ""))[:300],
                    "source": str(t.get("source", ""))[:400], "license": str(t.get("license", ""))[:80]}
                   for t in tr[:50] if isinstance(t, dict) and re.fullmatch(r"/(music|uploads)/[\w\-.]+\.mp3", str(t.get("url", ""))) and t.get("license")]}
    return c

def load_cfg():
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
    notify.send_confirmations()
    store.put("cron_last", {"t": int(now), "actions": [a for a, _ in out]})
    return out

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


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=STATIC, **k)
    def log_message(self, fmt, *args): sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))
    def end_headers(self):
        if self.path.endswith((".html", "/", ".js", ".css", ".json")):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _ip(self):
        xf = self.headers.get("X-Forwarded-For")
        return xf.split(",")[0].strip() if xf else self.client_address[0]
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8 * 1024 * 1024: raise ValueError("too large")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/voices":
            return self._json({"voices": VOICES, "default": DEFAULT_VOICE})
        if u.path == "/api/tts":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return self._tts(q)
        if u.path == "/api/config":
            return self._json({k: CFG[k] for k in ("greeting", "wake_reply", "ai_first", "ai_tag", "chat_notice", "voice_defaults", "ui", "music", "live")})
        if u.path == "/api/admin/config":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"config": CFG, "defaults": DEFAULTS, "voices": VOICES, "tones": list(TONES), "lengths": list(LENGTHS), "safety_line": SAFETY_LINE})
        if u.path == "/api/catalog":
            return self._json(catalog.public(CAT))
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
        if u.path == "/api/library":
            return self._json(library.LIB)
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
        return super().do_GET()
    def do_POST(self):
        u = urlparse(self.path)
        try: data = self._body()
        except Exception: return self._json({"error": "bad json"}, 400)
        if u.path == "/api/chat":
            q = str(data.get("message", "")).strip()[:1000]
            if not q: return self._json({"error": "empty"}, 400)
            if code_candidate(q):
                tok = check_code(self._ip(), q)
                if tok: return self._json({"admin_token": tok, "ttl": ADMIN_TTL, "reply": "Tryb producenta odblokowany."})
            hist = data.get("history")
            ctx = persona_ctx(data.get("persona"))
            rr = rule_reply(q)
            if rr: return self._json({"reply": disclose(rr, hist, ctx["name"]), "source": "rule"})
            ov = kb_override(q)
            if ov: return self._json({"reply": disclose(shape(ov, ctx), hist, ctx["name"]), "source": "kb_custom"})
            a = llm_answer(q, hist, ctx); src = "llm"
            if not a: a, src = shape(knowledge.answer(q), ctx), "offline"
            a = disclose(a, hist, ctx["name"])
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
            if cmd and cmd not in COMMANDS and cmd not in ("!pytanie", "!temat"): return self._json({"ok": True, "system": "Nieznana komenda. " + HELP})
            try: m = liveroom.post(vid, data.get("name", ""), data.get("avatar", ""), text, ask, testers.ring_for(data.get("tester")))
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
            try: notify.subscribe(data.get("sub"), data.get("topics")); return self._json({"ok": True})
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
            try: msgs = livechat.visitor_send(vid, data.get("name", ""), data.get("avatar", ""), data.get("text", ""), CFG.get("chat_notice", ""), testers.ring_for(data.get("tester")))
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
