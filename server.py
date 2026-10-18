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
         "zalotna": "Ton: lekko zalotny i czarujący, ale zawsze elegancki, kulturalny i nie-erotyczny."}
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
    "voice_defaults": {"voice": "pl-PL-ZofiaNeural", "pitch": -2.6, "rate": -8, "warmth": 4.5, "volume": -27, "spanish": True},
    "ui": {"ring_color": "#2ee66b", "pulse_speed": 1.4},
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
        "spanish": bool(vd.get("spanish", d["spanish"]))}
    ui = new.get("ui") if isinstance(new.get("ui"), dict) else {}
    col = str(ui.get("ring_color", "")).strip()
    c["ui"] = {"ring_color": col if re.fullmatch(r"#[0-9a-fA-F]{6}", col) else DEFAULTS["ui"]["ring_color"],
               "pulse_speed": _num(ui.get("pulse_speed"), 0.4, 4, DEFAULTS["ui"]["pulse_speed"])}
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

def full_system_prompt():
    parts = [CFG["system_prompt"], TONES[CFG["tone"]], LENGTHS[CFG["length"]]]
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

def shape(a):
    """Dopasowanie offline'owych odpowiedzi do tonu i długości."""
    if CFG["tone"] == "rzeczowa":
        a = re.sub(r"^(Mmm, cariño… |Escucha, cariño… |Dobrze, mi amor… |Słuchaj uważnie… |Ay, dobre pytanie… )", "", a)
        a = re.sub(r",? ?(cariño|mi amor)(?=[.,!?…])", "", a)
        a = re.sub(r" (Spróbuj teraz, ja posłucham\.|Powoli, bez pośpiechu\.|Zrób to dla mnie dziś wieczorem\.|Vamos, dasz radę\.)$", "", a)
    if CFG["length"] == "krotko":
        sents = re.split(r"(?<=[.!?])\s+", a.strip())
        a = " ".join(sents[:2])
    return a.strip()

# ---------- Tryb producenta: kod tylko po stronie serwera ----------
ADMIN_TTL = 30 * 60
_tokens, _attempts, _adm_lock = {}, {}, threading.Lock()
def admin_enabled(): return bool(admin_code())
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
    # Liczymy jako próbę tylko wiadomości o długości kodu – zwykłe pytania nie zużywają limitu prób.
    code = admin_code()
    return bool(code) and len(strip_code(msg)) == len(code)
def check_code(ip, msg):
    """Zwraca token przy trafieniu, None przy chybieniu lub blokadzie. Nigdy nie loguje kodu."""
    now = time.time()
    with _adm_lock:
        fails = [t for t in _attempts.get(ip, []) if now - t < 600]
        _attempts[ip] = fails
        allf = [t for t in _attempts.get("*", []) if now - t < 600]
        _attempts["*"] = allf
        if len(fails) >= 8 or len(allf) >= 60: return None
    ok = hmac.compare_digest(hashlib.sha256(strip_code(msg).encode()).digest(), hashlib.sha256(admin_code().encode()).digest())
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

def disclose(a, history):
    first = not any(isinstance(h, dict) and h.get("role") == "assistant" for h in (history or []))
    a = a.strip()
    if first:
        return CFG["ai_first"].strip() + " " + a
    if re.search(r"(?i)asystentk\w* AI|sztuczn\w* inteligencj", a):
        return a
    return a + " (" + CFG["ai_tag"].strip() + ")"

def llm_answer(q, history):
    key, base, model = os.getenv("LUNA_API_KEY"), os.getenv("LUNA_BASE_URL"), os.getenv("LUNA_MODEL")
    if not (key and base and model):
        return None
    msgs = [{"role": "system", "content": full_system_prompt()}]
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

async def synth_all(segs, tmp, rate=-8):
    files = []
    async def one(i, t, v):
        f = os.path.join(tmp, f"s{i}.mp3")
        await edge_tts.Communicate(t, v, rate=f"{int(rate):+d}%").save(f)
        return f
    files = await asyncio.gather(*(one(i, t, v) for i, (t, v) in enumerate(segs)))
    return files

def tts(text, voice, pitch_st, lufs, spanish, rate=-8, warmth=4.5):
    voice = voice if voice in VOICES else DEFAULT_VOICE
    pitch_st = max(-6.0, min(2.0, float(pitch_st)))
    rate = int(max(-40, min(30, float(rate))))
    warmth = max(0.0, min(10.0, float(warmth)))
    lufs = max(-36.0, min(-16.0, float(lufs)))
    text = text.strip()[:1200]
    key = hashlib.sha1(json.dumps([text, voice, round(pitch_st, 2), round(lufs, 1), bool(spanish), rate, round(warmth, 1), 4]).encode()).hexdigest()
    out = os.path.join(CACHE, key + ".mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    tmp = tempfile.mkdtemp(prefix="luna")
    try:
        segs = segments(text, voice, spanish)
        files = asyncio.run(synth_all(segs, tmp, rate))
        f = 2 ** (pitch_st / 12.0)
        inputs, chain = [], ""
        for i, fl in enumerate(files):
            inputs += ["-i", fl]
            chain += f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur=0.06[a{i}];"
        chain += "".join(f"[a{i}]" for i in range(len(files))) + f"concat=n={len(files)}:v=0:a=1[c];"
        chain += (f"[c]asetrate={24000*f:.1f},aresample=24000,atempo={1/f:.4f},"
                  "highpass=f=60,lowpass=f=11000,"
                  f"equalizer=f=150:t=q:w=1:g={warmth*2/3:.2f},equalizer=f=240:t=q:w=1:g={warmth:.2f},equalizer=f=3000:t=q:w=1.4:g={-warmth*0.45:.2f},"
                  "afftdn=nr=6:nf=-40,"
                  f"loudnorm=I={lufs}:TP=-6:LRA=7,alimiter=limit=0.5:level=disabled,aresample=44100[o]")
        subprocess.run([FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", chain, "-map", "[o]",
                        "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", out + ".tmp.mp3"], check=True)
        os.replace(out + ".tmp.mp3", out)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

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
        return json.loads(self.rfile.read(n) or b"{}") if n else {}
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/voices":
            return self._json({"voices": VOICES, "default": DEFAULT_VOICE})
        if u.path == "/api/tts":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return self._tts(q)
        if u.path == "/api/config":
            return self._json({k: CFG[k] for k in ("greeting", "wake_reply", "ai_first", "ai_tag", "chat_notice", "voice_defaults", "ui")})
        if u.path == "/api/admin/config":
            if not token_ok(self.headers.get("X-Admin-Token")): return self._json({"error": "unauthorized"}, 401)
            return self._json({"config": CFG, "defaults": DEFAULTS, "voices": VOICES, "tones": list(TONES), "lengths": list(LENGTHS), "safety_line": SAFETY_LINE})
        if u.path == "/api/health":
            return self._json({"ok": True, "llm": bool(os.getenv("LUNA_API_KEY")), "ai_disclosure": True})
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
            rr = rule_reply(q)
            if rr: return self._json({"reply": disclose(rr, hist), "source": "rule"})
            ov = kb_override(q)
            if ov: return self._json({"reply": disclose(shape(ov), hist), "source": "kb_custom"})
            a = llm_answer(q, data.get("history")); src = "llm"
            if not a: a, src = shape(knowledge.answer(q)), "offline"
            a = disclose(a, data.get("history"))
            return self._json({"reply": a, "source": src})
        if u.path == "/api/tts":
            return self._tts(data)
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
            p = tts(text, q.get("voice", DEFAULT_VOICE), q.get("pitch", -2.6), q.get("volume", -27),
                    str(q.get("spanish", "1")).lower() not in ("0", "false", "no"),
                    q.get("rate", -8), q.get("warmth", 4.5))
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
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
