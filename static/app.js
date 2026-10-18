(() => {
const $ = s => document.querySelector(s);
const chat = $('#chat'), input = $('#input'), player = $('#player'), statusEl = $('#status');
const PRESETS = {
  chrypka:{pitch:-1.6, hz:-14, rate:-10, warmth:6, volume:-31, rasp:4, breath:5, lisp:true},
  niska:{pitch:-2.6, hz:0, rate:-8, warmth:4.5, volume:-27, rasp:0, breath:0, lisp:false},
  szept:{pitch:-1.5, hz:0, rate:-18, warmth:2, volume:-33, rasp:0, breath:3, lisp:false},
  jasna:{pitch:0.5, hz:0, rate:-4, warmth:1.5, volume:-24, rasp:0, breath:0, lisp:false},
  gleboka:{pitch:-4.8, hz:0, rate:-14, warmth:8, volume:-26, rasp:1, breath:0, lisp:false}
};
const DEF = {voice:'pl-PL-ZofiaNeural', pitch:-1.6, hz:-14, rate:-10, warmth:6, volume:-31, rasp:4, breath:5, lisp:true, vver:13, preset:'chrypka', spanish:true, autoSpeak:true, wake:false, convo:true};
let S = Object.assign({}, DEF, JSON.parse(localStorage.getItem('luna.settings') || '{}'));
const save = () => localStorage.setItem('luna.settings', JSON.stringify(S));
// v1.3: nowy domyślny głos „Ciepła chrypka” – migracja ustawień sprzed 1.3
if (!S.vver){ Object.assign(S, PRESETS.chrypka, {preset:'chrypka', vver:13}); save(); }
let history = JSON.parse(sessionStorage.getItem('luna.history') || '[]');
let speaking = false;

function setStatus(t){ statusEl.textContent = t; }
function scroll(){ chat.scrollTop = chat.scrollHeight; }
function addMsg(text, who){
  const d = document.createElement('div'); d.className = 'msg ' + who; d.textContent = text;
  if (who === 'luna'){ const b = document.createElement('button'); b.className='play'; b.textContent='▶ odsłuchaj'; b.onclick=()=>speak(text); d.appendChild(b); }
  const side = who.split(' ')[0], row = document.createElement('div'); row.className = 'msgrow ' + side;
  const av = document.createElement('img'); av.className = 'mav ' + side; av.alt = '';
  const src = side === 'luna' ? (window.LunaAvatarSrc ? window.LunaAvatarSrc() : 'avatar-256.jpg') : (window.UserAvatarSrc ? window.UserAvatarSrc() : '');
  if (src) av.src = src; else av.style.visibility = 'hidden';
  row.append(av, d); chat.appendChild(row); scroll(); return row;
}
window.LunaRefreshAvatars = () => document.querySelectorAll('.mav').forEach(im => {
  const src = im.classList.contains('luna') ? (window.LunaAvatarSrc ? window.LunaAvatarSrc() : 'avatar-256.jpg') : (window.UserAvatarSrc ? window.UserAvatarSrc() : '');
  if (src){ im.src = src; im.style.visibility = ''; } else im.style.visibility = 'hidden';
});

/* ---------- Głos ---------- */
function setSpeaking(on){ speaking = on; document.body.classList.toggle('speaking', on); if (on && typeof convo !== 'undefined' && convo) convoState('Luna mówi… (mikrofon wstrzymany)'); if(on) setStatus('Luna mówi…'); else if (convo) setStatus('Rozmowa na żywo'); else setStatus(wakeOn ? 'Nasłuchuję słowa „Luna”…' : 'Twoja trenerka głosu'); }
function ttsUrl(text){
  const p = new URLSearchParams({text, voice:S.voice, pitch:S.pitch, hz:S.hz ?? 0, rate:S.rate, warmth:S.warmth, volume:S.volume, rasp:S.rasp ?? 0, breath:S.breath ?? 0, lisp:S.lisp?1:0, spanish:S.spanish?1:0});
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
async function ask(q, force){
  q = q.trim(); if (!q) return;
  const mine = addMsg(q, 'me');
  const t = addMsg('Luna myśli…', 'luna typing'); t.querySelector('.play')?.remove();
  let reply;
  try {
    const hd = {'Content-Type':'application/json'}; const at = sessionStorage.getItem('luna.admin'); if (at) hd['X-Admin-Token'] = at; const tc = localStorage.getItem('luna.tester'); if (tc) hd['X-Tester'] = tc;
    const r = await fetch('/api/chat', {method:'POST', headers:hd, body:JSON.stringify({message:q, history, vid: lunaVid(), persona: window.LunaPersona ? window.LunaPersona() : undefined})});
    const d = await r.json();
    if (d.limit){ t.remove(); addMsg(d.reply, 'luna'); window.LunaPlanRefresh && window.LunaPlanRefresh(); if (convo) endConvo(); return; }
    if (d.admin_token){ // kod producenta: nie zapisujemy wiadomości, nie pokazujemy jej
      mine.remove(); t.remove();
      sessionStorage.setItem('luna.admin', d.admin_token); openAdmin(); return;
    }
    reply = d.reply;
  } catch(e){ reply = 'Ay, cariño, straciłam połączenie z serwerem. Spróbuj za chwilę. (' + CFG.ai_tag + ')'; }
  t.remove(); addMsg(reply, 'luna');
  history.push({role:'user', content:q}, {role:'assistant', content:reply}); history = history.slice(-20);
  sessionStorage.setItem('luna.history', JSON.stringify(history));
  if (S.autoSpeak || force) await speak(reply);
}
$('#composer').addEventListener('submit', e => { e.preventDefault(); const q = input.value; input.value=''; ask(q); });

/* ---------- Rozpoznawanie mowy / słowo „Luna” ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
function lunaVid(){ let v = localStorage.getItem('luna.live.vid'); if (!v || !/^[0-9a-f]{32}$/.test(v)){ const a = new Uint8Array(16); crypto.getRandomValues(a); v = [...a].map(b => b.toString(16).padStart(2, '0')).join(''); localStorage.setItem('luna.live.vid', v); } return v; }
window.LunaVid = lunaVid;
const IOS = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
let convo = false, silenceTimer = null, wakeLock = null, micGranted = false;
let rec = null, wakeOn = false, mode = 'idle', recRunning = false, paused = false, awaitTimer = null;
let WAKE = /(^|[^a-ząćęłńóśźż])(ł|l)un(a|o|ie|y)?(?![a-ząćęłńóśźż])/i;
window.LunaSetWake = word => {
  word = (word || 'Luna').trim().toLowerCase();
  if (word === 'luna') { WAKE = /(^|[^a-ząćęłńóśźż])(ł|l)un(a|o|ie|y)?(?![a-ząćęłńóśźż])/i; return; }
  const esc = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const stem = esc.length > 3 && /[aeiouy]$/.test(esc) ? esc.slice(0, -1) + '[a-ząęóy]?' : esc;
  WAKE = new RegExp('(^|[^a-ząćęłńóśźż])' + stem + '(?![a-ząćęłńóśźż])', 'i');
};

function makeRec(){
  const r = new SR(); r.lang = 'pl-PL'; r.continuous = !IOS; r.interimResults = true; r.maxAlternatives = 1;
  r.onstart = () => { recRunning = true; };
  r.onend = () => { recRunning = false; if ((wakeOn || mode === 'question' || (convo && mode !== 'thinking')) && !paused) setTimeout(startRec, 250); else if (!convo) micBtn.classList.remove('on'); };
  r.onerror = e => { if (e.error === 'not-allowed' || e.error === 'service-not-allowed'){ if (convo && IOS && micGranted){ showTap(true); return; } wakeOn=false; $('#wakeToggle').checked=false; S.wake=false; save(); micHelp(); if (convo) endConvo(); } };
  r.onresult = onResult; return r;
}
function startRec(){ if (!SR || recRunning || paused) return; try { rec = rec || makeRec(); rec.start(); if (convo) showTap(false); } catch(e){ if (convo && IOS) showTap(true); } }
function stopRec(){ try { rec && rec.stop(); } catch(e){} }
function pauseRecognition(){ paused = true; try { rec && rec.abort(); } catch(e){} }
function resumeRecognition(){ paused = false; if (wakeOn || mode === 'question' || convo) setTimeout(startRec, 350); }

function setAwaitQuestion(){
  mode = 'question'; document.body.classList.add('listening'); setStatus(convo ? 'Rozmowa na żywo – słucham…' : 'Słucham Twojego pytania…');
  if (convo){ convoState('Słucham… mów śmiało'); armSilence(); return; }
  clearTimeout(awaitTimer); awaitTimer = setTimeout(() => { if (mode === 'question'){ mode = 'idle'; document.body.classList.remove('listening'); micBtn.classList.remove('on'); if(!wakeOn) stopRec(); setSpeaking(false);} }, 12000);
}
function endQuestion(){ mode = 'idle'; clearTimeout(awaitTimer); document.body.classList.remove('listening'); micBtn.classList.remove('on'); if (!wakeOn) { stopRec(); } }

async function onResult(ev){
  for (let i = ev.resultIndex; i < ev.results.length; i++){
    const res = ev.results[i]; if (!res.isFinal) { if (mode==='question'){ input.placeholder = res[0].transcript; if (convo) armSilence(); } continue; }
    const text = res[0].transcript.trim(); input.placeholder = 'Zapytaj Lunę o głos…';
    if (!text) continue;
    if (convo && mode === 'question'){ await convoTurn(text); continue; }
    if (mode === 'question'){ endQuestion(); await ask(text.replace(WAKE, ' ').trim() || text); continue; }
    if (wakeOn){
      const m = text.match(WAKE);
      if (!m) continue;
      const rest = text.slice(m.index + m[0].length).replace(/^[\s,.!?:;-]+/, '').trim();
      if (S.convo && !convo){ await startConvo(true); if (rest.split(/\s+/).filter(Boolean).length >= 2) await convoTurn(rest); continue; }
      if (rest.split(/\s+/).filter(Boolean).length >= 2){ await ask(rest); }
      else { const ack = window.LunaName && window.LunaName() !== 'Luna' ? CFG.wake_reply.replace(/Luna/g, window.LunaName()) : CFG.wake_reply; addMsg(ack, 'luna'); await speak(ack); setAwaitQuestion(); }
    }
  }
}


/* ---------- Rozmowa ciągła („Rozmowa na żywo”) ---------- */
const END_RE = /(^|\s)(ł|l)un[aoy]?[,.!\s]+koniec|dzi[eę]kuj[eę][,.!\s]+to wszystko|koniec rozmowy|zako[nń]cz rozmow[eę]/i;
const SILENCE_MS = 30000;
function convoState(t){ const e = $('#convoState'); if (e) e.textContent = t; }
function armSilence(){ clearTimeout(silenceTimer); silenceTimer = setTimeout(() => { if (convo && mode === 'question') endConvo('Cisza przez 30 sekund – kończę rozmowę. Powiedz „Luna”, gdy będziesz chcieć porozmawiać.'); }, SILENCE_MS); }
function showTap(on){ const b = $('#convoTap'); if (b) b.hidden = !on; if (on) convoState('Stuknij „Mów”, aby odpowiedzieć'); }
async function lockScreen(){ try { if ('wakeLock' in navigator && !wakeLock) { wakeLock = await navigator.wakeLock.request('screen'); wakeLock.addEventListener('release', () => { wakeLock = null; }); } } catch(e){} }
document.addEventListener('visibilitychange', () => { if (convo && document.visibilityState === 'visible') lockScreen(); });
function micHelp(){
  const twa = document.documentElement.classList.contains('twa');
  addMsg('🎙️ Potrzebuję dostępu do mikrofonu, cariño. ' + (twa
    ? 'W aplikacji Luna: Ustawienia telefonu → Aplikacje → Chrome (lub Luna) → Uprawnienia → Mikrofon → Zezwól, a potem stuknij ponownie „Rozmowa na żywo”.'
    : IOS ? 'Na iPhonie: Ustawienia → Safari → Mikrofon → Zezwól (albo „aA” w pasku adresu → Ustawienia witryny). Możesz też pisać i dyktować z klawiatury (🎤).'
          : 'W Chrome stuknij ikonę kłódki obok adresu → Uprawnienia → Mikrofon → Zezwól, a potem odśwież stronę.'), 'luna');
}
async function askMic(){
  if (micGranted) return true;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return true;
  try {
    const st = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
    st.getTracks().forEach(t => t.stop()); micGranted = true; return true;
  } catch(e){ micHelp(); return false; }
}
async function startConvo(fromWake){
  if (!SR){
    addMsg('Ta przeglądarka nie obsługuje rozmowy głosowej. Stuknij pole tekstowe i użyj dyktowania z klawiatury (🎤) – odpowiem głosem. ' + (IOS ? 'Na iPhonie najlepiej działa Safari w iOS 14.5+.' : 'Najlepiej działa Chrome na Androidzie.'), 'luna');
    S.autoSpeak = true; save(); input.focus(); return;
  }
  if (!fromWake){ const ok = await askMic(); if (!ok) return; } else micGranted = true;
  convo = true; document.body.classList.add('convo'); $('#convoBar').hidden = false; $('#convoBtn').classList.add('on'); $('#convoBtn').textContent = '■ Zakończ rozmowę';
  micBtn.classList.add('on'); player.pause(); window.speechSynthesis && speechSynthesis.cancel();
  lockScreen(); paused = false;
  if (!fromWake){ const hi = 'Słucham cię, cariño. Mów śmiało – odpowiem i będę słuchać dalej. Powiedz „Luna, koniec”, aby zakończyć.'; addMsg(hi, 'luna'); await speak(hi); }
  setAwaitQuestion(); startRec();
}
async function convoTurn(text){
  clearTimeout(silenceTimer);
  if (END_RE.test(text)){ return endConvo('Dziękuję za rozmowę, cariño. Wracam do nasłuchiwania słowa „Luna”.', true); }
  mode = 'thinking'; document.body.classList.remove('listening'); convoState('Luna myśli…');
  pauseRecognition();
  await ask(text.replace(WAKE, ' ').trim() || text, true);
  if (!convo) return;
  paused = false; setAwaitQuestion(); startRec();
}
async function endConvo(msg, speakIt){
  if (!convo) return;
  convo = false; clearTimeout(silenceTimer); mode = 'idle';
  document.body.classList.remove('convo', 'listening'); $('#convoBar').hidden = true; showTap(false);
  $('#convoBtn').classList.remove('on'); $('#convoBtn').textContent = '🎙️ Rozmowa na żywo'; micBtn.classList.remove('on');
  try { wakeLock && wakeLock.release(); } catch(e){} wakeLock = null;
  if (msg){ addMsg(msg, 'luna'); if (speakIt) await speak(msg); }
  if (wakeOn){ paused = false; startRec(); setStatus('Nasłuchuję słowa „Luna”…'); } else { stopRec(); setStatus('Twoja trenerka głosu'); }
}
$('#convoBtn').onclick = () => convo ? endConvo('Rozmowa zakończona.') : startConvo(false);
$('#convoStop').onclick = () => endConvo('Rozmowa zakończona.');
$('#convoTap').onclick = () => { showTap(false); paused = false; setAwaitQuestion(); startRec(); };
window.LunaConvo = {start: startConvo, end: endConvo, active: () => convo};

const micBtn = $('#micBtn');
micBtn.onclick = () => {
  if (!SR){ addMsg('Ta przeglądarka nie obsługuje rozpoznawania mowy. Spróbuj w Chrome, cariño.', 'luna'); return; }
  if (convo){ endConvo('Rozmowa zakończona.'); return; }
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
const dlg = $('#settings'), voiceSel = $('#voiceSel'), pitch = $('#pitch'), vol = $('#volume'), rate = $('#rate'), warmth = $('#warmth'), rasp = $('#rasp'), breath = $('#breath');
function renderSettings(){
  voiceSel.value = S.voice; pitch.value = S.pitch; vol.value = S.volume; rate.value = S.rate; warmth.value = S.warmth;
  $('#rateVal').textContent = (S.rate > 0 ? '+' : '') + S.rate + '%';
  $('#warmVal').textContent = Math.round(S.warmth * 10) + '%';
  document.querySelectorAll('#presets button').forEach(b => b.classList.toggle('on', b.dataset.p === S.preset));
  $('#spanishChk').checked = S.spanish; $('#autoSpeak').checked = S.autoSpeak; $('#convoChk').checked = !!S.convo;
  $('#pitchVal').textContent = (S.pitch > 0 ? '+' : '') + S.pitch + ' półt.'; 
  $('#volVal').textContent = Math.round((S.volume + 36) / 20 * 100) + '%';
  rasp.value = S.rasp ?? 0; breath.value = S.breath ?? 0; $('#raspVal').textContent = Math.round((S.rasp ?? 0) * 10) + '%'; $('#breathVal').textContent = Math.round((S.breath ?? 0) * 10) + '%'; $('#lispChk').checked = !!S.lisp;
}
fetch('/api/voices?lang=' + encodeURIComponent((new URLSearchParams(location.search).get('lang') || document.documentElement.lang || 'pl').slice(0, 2))).then(r => r.json()).then(d => {
  for (const [k, v] of Object.entries(d.voices)){ const o = document.createElement('option'); o.value = k; o.textContent = v; voiceSel.appendChild(o); }
  renderSettings();
}).catch(()=>{});
$('#settingsBtn').onclick = () => { renderSettings(); dlg.showModal(); };
voiceSel.onchange = () => { S.voice = voiceSel.value; save(); };
const slider = (el, k) => el.oninput = () => { S[k] = parseFloat(el.value); S.preset = ''; save(); renderSettings(); };
slider(pitch, 'pitch'); slider(vol, 'volume'); slider(rate, 'rate'); slider(warmth, 'warmth'); slider(rasp, 'rasp'); slider(breath, 'breath');
$('#lispChk').onchange = e => { S.lisp = e.target.checked; S.preset = ''; save(); renderSettings(); };
document.querySelectorAll('#presets button').forEach(b => b.onclick = () => { Object.assign(S, PRESETS[b.dataset.p], {preset:b.dataset.p}); save(); renderSettings(); $('#testVoice').click(); });
$('#spanishChk').onchange = e => { S.spanish = e.target.checked; save(); };
$('#autoSpeak').onchange = e => { S.autoSpeak = e.target.checked; save(); };
$('#convoChk').onchange = e => { S.convo = e.target.checked; save(); };
$('#resetBtn').onclick = () => { const w = S.wake; S = Object.assign({}, DEF, {wake:w}); save(); renderSettings(); };
$('#testVoice').onclick = () => speak('Hola, cariño. Słyszę cię. Mów szczerze, cicho i powoli – szczególnie wtedy, gdy czujesz stres.');

function openAdmin(){ window.LunaAdmin && window.LunaAdmin.open(); }

/* ---------- Start ---------- */
const CFG = {greeting:'Hola, cariño. Jestem Luna, sztucznie stworzona asystentka AI. Pomagam mężczyznom i kobietom lepiej się rozmawiać – przez samą mowę: głośność, barwę, ton, tempo i intonację. Zapytaj mnie o barwę głosu, oddech, tempo albo o to, jak brzmieć pewnie i ciepło. Włącz „Nasłuchiwanie” i po prostu powiedz: Luna.', wake_reply:'Słyszę cię, cariño. Jestem Luna, sztucznie stworzona asystentka AI.', ai_tag:'Luna, asystentka AI', chat_notice:'Czas odpowiedzi na każde pytanie zależy od dostępności osób w biurze, ale nie będzie dłuższy niż 30 dni.'};
window.LunaApplyConfig = c => {
  Object.assign(CFG, c);
  const g = document.querySelector('.msg.greet'); if (g) g.firstChild.textContent = CFG.greeting;
  const n = $('#chatNotice'); if (n){ n.textContent = CFG.chat_notice || ''; n.hidden = !CFG.chat_notice; }
  if (CFG.ui){ document.documentElement.style.setProperty('--ring', CFG.ui.ring_color); document.documentElement.style.setProperty('--pulse', CFG.ui.pulse_speed + 's'); }
  window.LunaCustomApply && window.LunaCustomApply();
  if (CFG.voice_defaults && (!localStorage.getItem('luna.settings') || S.preset === 'chrypka' && !S.custom)){ Object.assign(DEF, CFG.voice_defaults); Object.assign(S, CFG.voice_defaults); }
};
fetch('/api/config').then(r => r.json()).then(window.LunaApplyConfig).catch(()=>{});
if (history.length){ history.forEach(h => addMsg(h.content, h.role === 'user' ? 'me' : 'luna')); }
else addMsg(CFG.greeting, 'luna greet');
/* ---------- Aktualizacje (PWA) ---------- */
function updateToast(reg){
  if (document.getElementById('updToast')) return;
  const t = document.createElement('div'); t.id = 'updToast'; t.className = 'toast';
  t.innerHTML = '✨ Dostępna nowa wersja – <button type="button">odśwież</button>';
  t.querySelector('button').onclick = () => { window.__lunaUpd = true; if (reg.waiting) reg.waiting.postMessage('SKIP_WAITING'); else location.reload(); };
  document.body.appendChild(t);
}
if ('serviceWorker' in navigator){
  let reloading = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (window.__lunaUpd && !reloading){ reloading = true; location.reload(); } });
  navigator.serviceWorker.register('sw.js').then(reg => {
    if (reg.waiting && navigator.serviceWorker.controller) updateToast(reg);
    reg.addEventListener('updatefound', () => { const w = reg.installing; w && w.addEventListener('statechange', () => { if (w.state === 'installed' && navigator.serviceWorker.controller) updateToast(reg); }); });
    const check = () => reg.update().catch(() => {});
    setInterval(check, 30 * 60 * 1000); document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
  }).catch(() => {});
}
/* /app#konto – otwiera Ustawienia na sekcji konta (np. z Bitew agentek: „Zaloguj się, aby głosować”) */
if (location.hash === '#konto') setTimeout(() => { const b = document.getElementById('settingsBtn'); if (b) b.click(); const a = document.getElementById('acctSection'); if (a) a.scrollIntoView({block: 'start'}); }, 700);
})();
