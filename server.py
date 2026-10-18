#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Luna – backend (stdlib only + edge-tts + ffmpeg). Serwuje static/ oraz /api/chat, /api/tts, /api/voices."""
import asyncio, hashlib, json, os, re, shutil, subprocess, sys, tempfile, threading, urllib.request
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
 "pewność siebie i to, jak brzmieć atrakcyjnie w kulturalny sposób. Nigdy nie tworzysz treści seksualnych ani wulgarnych. Bez list i emoji – tekst będzie czytany na głos.")

def llm_answer(q, history):
    key, base, model = os.getenv("LUNA_API_KEY"), os.getenv("LUNA_BASE_URL"), os.getenv("LUNA_MODEL")
    if not (key and base and model):
        return None
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
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

async def synth_all(segs, tmp):
    files = []
    async def one(i, t, v):
        f = os.path.join(tmp, f"s{i}.mp3")
        await edge_tts.Communicate(t, v, rate="-8%").save(f)
        return f
    files = await asyncio.gather(*(one(i, t, v) for i, (t, v) in enumerate(segs)))
    return files

def tts(text, voice, pitch_st, lufs, spanish):
    voice = voice if voice in VOICES else DEFAULT_VOICE
    pitch_st = max(-6.0, min(0.0, float(pitch_st)))
    lufs = max(-36.0, min(-16.0, float(lufs)))
    text = text.strip()[:1200]
    key = hashlib.sha1(json.dumps([text, voice, round(pitch_st, 2), round(lufs, 1), bool(spanish), 3]).encode()).hexdigest()
    out = os.path.join(CACHE, key + ".mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    tmp = tempfile.mkdtemp(prefix="luna")
    try:
        segs = segments(text, voice, spanish)
        files = asyncio.run(synth_all(segs, tmp))
        f = 2 ** (pitch_st / 12.0)
        inputs, chain = [], ""
        for i, fl in enumerate(files):
            inputs += ["-i", fl]
            chain += f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur=0.06[a{i}];"
        chain += "".join(f"[a{i}]" for i in range(len(files))) + f"concat=n={len(files)}:v=0:a=1[c];"
        chain += (f"[c]asetrate={24000*f:.1f},aresample=24000,atempo={1/f:.4f},"
                  "highpass=f=60,lowpass=f=11000,"
                  "equalizer=f=150:t=q:w=1:g=3,equalizer=f=240:t=q:w=1:g=4.5,equalizer=f=3000:t=q:w=1.4:g=-2,"
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
        if u.path == "/api/health":
            return self._json({"ok": True, "llm": bool(os.getenv("LUNA_API_KEY"))})
        return super().do_GET()
    def do_POST(self):
        u = urlparse(self.path)
        try: data = self._body()
        except Exception: return self._json({"error": "bad json"}, 400)
        if u.path == "/api/chat":
            q = str(data.get("message", "")).strip()[:1000]
            if not q: return self._json({"error": "empty"}, 400)
            a = llm_answer(q, data.get("history")); src = "llm"
            if not a: a, src = knowledge.answer(q), "offline"
            return self._json({"reply": a, "source": src})
        if u.path == "/api/tts":
            return self._tts(data)
        self._json({"error": "not found"}, 404)
    def _tts(self, q):
        text = str(q.get("text", "")).strip()
        if not text: return self._json({"error": "empty text"}, 400)
        try:
            p = tts(text, q.get("voice", DEFAULT_VOICE), q.get("pitch", -2.6), q.get("volume", -27),
                    str(q.get("spanish", "1")).lower() not in ("0", "false", "no"))
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
