(() => {
const $ = s => document.querySelector(s);
const chat = $('#chat'), input = $('#input'), player = $('#player'), statusEl = $('#status');
const PRESETS = {
  niska:{pitch:-2.6, rate:-8, warmth:4.5, volume:-27},
  szept:{pitch:-1.5, rate:-18, warmth:2, volume:-33},
  jasna:{pitch:0.5, rate:-4, warmth:1.5, volume:-24},
  gleboka:{pitch:-4.8, rate:-14, warmth:8, volume:-26}
};
const DEF = {voice:'pl-PL-ZofiaNeural', pitch:-2.6, rate:-8, warmth:4.5, volume:-27, preset:'niska', spanish:true, autoSpeak:true, wake:false};
let S = Object.assign({}, DEF, JSON.parse(localStorage.getItem('luna.settings') || '{}'));
const save = () => localStorage.setItem('luna.settings', JSON.stringify(S));
let history = JSON.parse(sessionStorage.getItem('luna.history') || '[]');
let speaking = false;

function setStatus(t){ statusEl.textContent = t; }
function scroll(){ chat.scrollTop = chat.scrollHeight; }
function addMsg(text, who){
  const d = document.createElement('div'); d.className = 'msg ' + who; d.textContent = text;
  if (who === 'luna'){ const b = document.createElement('button'); b.className='play'; b.textContent='▶ odsłuchaj'; b.onclick=()=>speak(text); d.appendChild(b); }
  chat.appendChild(d); scroll(); return d;
}

/* ---------- Głos ---------- */
function setSpeaking(on){ speaking = on; document.body.classList.toggle('speaking', on); if(on) setStatus('Luna mówi…'); else setStatus(wakeOn ? 'Nasłuchuję słowa „Luna”…' : 'Twoja trenerka głosu'); }
function ttsUrl(text){
  const p = new URLSearchParams({text, voice:S.voice, pitch:S.pitch, rate:S.rate, warmth:S.warmth, volume:S.volume, spanish:S.spanish?1:0});
  return '/api/tts?' + p.toString();
}
function fallbackSpeak(text){
  return new Promise(res => {
    if (!('speechSynthesis' in window)) return res();
    const u = new SpeechSynthesisUtterance(text.replace(/[„”…]/g,' '));
    u.lang = 'pl-PL'; u.pitch = 0.6; u.rate = 0.9; u.volume = 0.5;
    const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.toLowerCase().startsWith('pl')); if (v) u.voice = v;
    u.onstart = () => setSpeaking(true);
    u.onend = u.onerror = () => { setSpeaking(false); res(); };
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  });
}
async function speak(text){
  pauseRecognition();
  try {
    player.pause();
    const r = await fetch(ttsUrl(text));
    if (!r.ok) throw new Error('tts ' + r.status);
    const blob = await r.blob();
    if (player.dataset.url) URL.revokeObjectURL(player.dataset.url);
    player.dataset.url = player.src = URL.createObjectURL(blob);
    await new Promise((res, rej) => {
      player.onplay = () => setSpeaking(true);
      player.onended = () => res();
      player.onerror = () => rej(new Error('audio'));
      player.play().catch(rej);
    });
  } catch (e) {
    console.warn('Backend TTS niedostępny, używam głosu przeglądarki', e);
    await fallbackSpeak(text);
  } finally { setSpeaking(false); resumeRecognition(); }
}
// odblokowanie audio na telefonach przy pierwszym dotknięciu
document.addEventListener('pointerdown', function unlock(){ player.muted = true; player.play().catch(()=>{}).finally(()=>{player.pause(); player.muted=false;}); document.removeEventListener('pointerdown', unlock); }, {once:true});

/* ---------- Czat ---------- */
async function ask(q){
  q = q.trim(); if (!q) return;
  addMsg(q, 'me'); history.push({role:'user', content:q});
  const t = addMsg('Luna myśli…', 'luna typing'); t.querySelector('.play')?.remove();
  let reply;
  try {
    const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:q, history})});
    reply = (await r.json()).reply;
  } catch(e){ reply = 'Ay, cariño, straciłam połączenie z serwerem. Spróbuj za chwilę.'; }
  t.remove(); addMsg(reply, 'luna');
  history.push({role:'assistant', content:reply}); history = history.slice(-20);
  sessionStorage.setItem('luna.history', JSON.stringify(history));
  if (S.autoSpeak) await speak(reply);
}
$('#composer').addEventListener('submit', e => { e.preventDefault(); const q = input.value; input.value=''; ask(q); });

/* ---------- Rozpoznawanie mowy / słowo „Luna” ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null, wakeOn = false, mode = 'idle', recRunning = false, paused = false, awaitTimer = null;
const WAKE = /(^|[^a-ząćęłńóśźż])(ł|l)un(a|o|ie|y)?(?![a-ząćęłńóśźż])/i;

function makeRec(){
  const r = new SR(); r.lang = 'pl-PL'; r.continuous = true; r.interimResults = true; r.maxAlternatives = 1;
  r.onstart = () => { recRunning = true; };
  r.onend = () => { recRunning = false; if ((wakeOn || mode === 'question') && !paused) setTimeout(startRec, 250); else micBtn.classList.remove('on'); };
  r.onerror = e => { if (e.error === 'not-allowed' || e.error === 'service-not-allowed'){ wakeOn=false; $('#wakeToggle').checked=false; S.wake=false; save(); addMsg('Potrzebuję dostępu do mikrofonu, cariño. Zezwól na niego w przeglądarce (strona musi być otwarta przez HTTPS).', 'luna'); } };
  r.onresult = onResult; return r;
}
function startRec(){ if (!SR || recRunning || paused) return; try { rec = rec || makeRec(); rec.start(); } catch(e){} }
function stopRec(){ try { rec && rec.stop(); } catch(e){} }
function pauseRecognition(){ paused = true; try { rec && rec.abort(); } catch(e){} }
function resumeRecognition(){ paused = false; if (wakeOn || mode === 'question') setTimeout(startRec, 300); }

function setAwaitQuestion(){
  mode = 'question'; document.body.classList.add('listening'); setStatus('Słucham Twojego pytania…');
  clearTimeout(awaitTimer); awaitTimer = setTimeout(() => { if (mode === 'question'){ mode = 'idle'; document.body.classList.remove('listening'); micBtn.classList.remove('on'); if(!wakeOn) stopRec(); setSpeaking(false);} }, 12000);
}
function endQuestion(){ mode = 'idle'; clearTimeout(awaitTimer); document.body.classList.remove('listening'); micBtn.classList.remove('on'); if (!wakeOn) { stopRec(); } }

async function onResult(ev){
  for (let i = ev.resultIndex; i < ev.results.length; i++){
    const res = ev.results[i]; if (!res.isFinal) { if (mode==='question') input.placeholder = res[0].transcript; continue; }
    const text = res[0].transcript.trim(); input.placeholder = 'Zapytaj Lunę o głos…';
    if (!text) continue;
    if (mode === 'question'){ endQuestion(); await ask(text.replace(WAKE, ' ').trim() || text); continue; }
    if (wakeOn){
      const m = text.match(WAKE);
      if (!m) continue;
      const rest = text.slice(m.index + m[0].length).replace(/^[\s,.!?:;-]+/, '').trim();
      if (rest.split(/\s+/).filter(Boolean).length >= 2){ await ask(rest); }
      else { addMsg('Słyszę cię, cariño.', 'luna'); await speak('Słyszę cię, cariño.'); setAwaitQuestion(); }
    }
  }
}

const micBtn = $('#micBtn');
micBtn.onclick = () => {
  if (!SR){ addMsg('Ta przeglądarka nie obsługuje rozpoznawania mowy. Spróbuj w Chrome, cariño.', 'luna'); return; }
  if (mode === 'question'){ endQuestion(); return; }
  player.pause(); speechSynthesis && speechSynthesis.cancel();
  micBtn.classList.add('on'); paused = false; setAwaitQuestion(); startRec();
};
const wakeToggle = $('#wakeToggle');
function setWake(on){
  if (on && !SR){ wakeToggle.checked = false; addMsg('Nasłuchiwanie wymaga przeglądarki z rozpoznawaniem mowy (najlepiej Chrome na Androidzie lub komputerze).', 'luna'); return; }
  wakeOn = on; S.wake = on; save(); wakeToggle.checked = on;
  if (on){ paused = false; startRec(); setStatus('Nasłuchuję słowa „Luna”…'); } else { if (mode!=='question') stopRec(); setStatus('Twoja trenerka głosu'); }
}
wakeToggle.onchange = () => setWake(wakeToggle.checked);
// Uwaga: nasłuchiwanie wymaga gestu użytkownika po przeładowaniu – przywracamy stan przełącznika przy pierwszym dotknięciu
if (S.wake){ document.addEventListener('pointerdown', () => setWake(true), {once:true}); setStatus('Dotknij ekranu, aby wznowić nasłuchiwanie'); }

/* ---------- Ustawienia ---------- */
const dlg = $('#settings'), voiceSel = $('#voiceSel'), pitch = $('#pitch'), vol = $('#volume'), rate = $('#rate'), warmth = $('#warmth');
function renderSettings(){
  voiceSel.value = S.voice; pitch.value = S.pitch; vol.value = S.volume; rate.value = S.rate; warmth.value = S.warmth;
  $('#rateVal').textContent = (S.rate > 0 ? '+' : '') + S.rate + '%';
  $('#warmVal').textContent = Math.round(S.warmth * 10) + '%';
  document.querySelectorAll('#presets button').forEach(b => b.classList.toggle('on', b.dataset.p === S.preset));
  $('#spanishChk').checked = S.spanish; $('#autoSpeak').checked = S.autoSpeak;
  $('#pitchVal').textContent = (S.pitch > 0 ? '+' : '') + S.pitch + ' półt.'; 
  $('#volVal').textContent = Math.round((S.volume + 36) / 20 * 100) + '%';
}
fetch('/api/voices').then(r => r.json()).then(d => {
  for (const [k, v] of Object.entries(d.voices)){ const o = document.createElement('option'); o.value = k; o.textContent = v; voiceSel.appendChild(o); }
  renderSettings();
}).catch(()=>{});
$('#settingsBtn').onclick = () => { renderSettings(); dlg.showModal(); };
voiceSel.onchange = () => { S.voice = voiceSel.value; save(); };
const slider = (el, k) => el.oninput = () => { S[k] = parseFloat(el.value); S.preset = ''; save(); renderSettings(); };
slider(pitch, 'pitch'); slider(vol, 'volume'); slider(rate, 'rate'); slider(warmth, 'warmth');
document.querySelectorAll('#presets button').forEach(b => b.onclick = () => { Object.assign(S, PRESETS[b.dataset.p], {preset:b.dataset.p}); save(); renderSettings(); $('#testVoice').click(); });
$('#spanishChk').onchange = e => { S.spanish = e.target.checked; save(); };
$('#autoSpeak').onchange = e => { S.autoSpeak = e.target.checked; save(); };
$('#resetBtn').onclick = () => { const w = S.wake; S = Object.assign({}, DEF, {wake:w}); save(); renderSettings(); };
$('#testVoice').onclick = () => speak('Hola, cariño. Mów szczerze, cicho i powoli, a twój głos będzie niższy i cieplejszy.');

/* ---------- Start ---------- */
if (history.length){ history.forEach(h => addMsg(h.content, h.role === 'user' ? 'me' : 'luna')); }
else addMsg('Hola, cariño. Jestem Luna. Zapytaj mnie o barwę głosu, oddech, tempo albo o to, jak brzmieć pewnie i ciepło. Włącz „Nasłuchiwanie” i po prostu powiedz: Luna.', 'luna');
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(()=>{});
})();
