# Luna – trenerka głosu (PWA)
Uruchomienie:  pip install edge-tts  (+ ffmpeg w systemie)  →  python3 server.py 8765  →  http://localhost:8765
Mikrofon/nasłuchiwanie wymaga HTTPS (np. tunel cloudflared: cloudflared tunnel --protocol http2 --url http://localhost:8765).
Opcjonalny LLM (OpenAI-compatible): LUNA_API_KEY, LUNA_BASE_URL, LUNA_MODEL.
API: POST /api/chat {message,history} · GET/POST /api/tts?text=&voice=&pitch=-2.6&volume=-27&spanish=1 · GET /api/voices
Pliki: server.py, knowledge.py (37 tematów offline), static/ (index.html, app.js, style.css, manifest.json, sw.js, ikony), samples/, assets/.
