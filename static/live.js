/* Luna Live – pokój transmisji: stan, odliczanie, czat, synchroniczne odtwarzanie głosu Luny, panel moderatora. */
(() => {
const $ = s => document.querySelector(s);
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
let vid = localStorage.getItem('luna.live.vid');
if (!vid || !/^[0-9a-f]{32}$/.test(vid)){ const a = new Uint8Array(16); crypto.getRandomValues(a); vid = [...a].map(b => b.toString(16).padStart(2, '0')).join(''); localStorage.setItem('luna.live.vid', vid); }
const tok = () => sessionStorage.getItem('luna.admin') || '';
const user = JSON.parse(localStorage.getItem('luna.user') || '{}');
const LS = JSON.parse(localStorage.getItem('luna.liveui') || '{}');
const saveLS = () => localStorage.setItem('luna.liveui', JSON.stringify(LS));
$('#nick').value = LS.nick || user.name || '';
let st = null, offset = 0, lastId = 0, chatIds = new Set(), playedId = null, joined = false, poolSet = false;
const au = $('#lvAudio');
const GUEST = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#333"/><circle cx="32" cy="25" r="11" fill="#bbb"/><path d="M12 58c2-12 10-18 20-18s18 6 20 18" fill="#bbb"/></svg>');

/* ---------- scena ---------- */
function setPool(on){ $('#stage').classList.toggle('pool', on); $('#poolChk').checked = on; }
function setHolo(on){ document.body.classList.toggle('holo', on); $('#holoChk').checked = on; }
$('#poolChk').onchange = e => { LS.pool = e.target.checked; saveLS(); setPool(LS.pool); };
$('#holoChk').onchange = e => { LS.holo = e.target.checked; saveLS(); setHolo(LS.holo); };
setHolo(!!LS.holo);

/* ---------- odliczanie ---------- */
const pad = n => String(n).padStart(2, '0');
function tick(){
  if (!st) return;
  const now = Date.now() + offset;
  if (!st.on){
    let ms = Math.max(0, st.sched.next_start - now); const d = Math.floor(ms / 864e5); ms -= d * 864e5;
    const h = Math.floor(ms / 36e5); ms -= h * 36e5; const m = Math.floor(ms / 6e4); const s = Math.floor((ms - m * 6e4) / 1000);
    $('#cdD').textContent = d; $('#cdH').textContent = pad(h); $('#cdM').textContent = pad(m); $('#cdS').textContent = pad(s);
  }
  const c = st.current; const speaking = !!(c && now >= c.start && now < c.start + c.dur * 1000 && !au.paused);
  document.body.classList.toggle('speaking', speaking);
}
setInterval(tick, 250);

/* ---------- głos Luny (synchronizacja) ---------- */
function syncAudio(){
  const c = st && st.current; if (!st || !st.on || !c || !joined) return;
  const now = Date.now() + offset, end = c.start + c.dur * 1000;
  if (c.id === playedId || now > end - 300) return;
  playedId = c.id; au.src = c.audio;
  const go = () => { const pos = Math.max(0, (Date.now() + offset - c.start) / 1000); if (pos > 0.3) au.currentTime = pos; au.play().catch(() => { $('#joinBtn').hidden = false; joined = false; playedId = null; }); };
  const wait = c.start - now; if (wait > 0) setTimeout(go, wait); else go();
}
$('#joinBtn').onclick = () => {
  joined = true; $('#joinBtn').hidden = true;
  au.src = 'data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYYoRBqpAAAAAAAAAAAAAAAAAAAA';
  au.play().catch(() => {}).finally(() => { const nick = $('#nick').value.trim(); if (nick) fetch('/api/live-room/join', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({vid, name: nick})}); syncAudio(); });
};

/* ---------- czat ---------- */
function msgEl(m){
  const r = el('div', 'cm' + (m.ask ? ' ask' : '')); r.dataset.id = m.id;
  const im = el('img', 'cav'); im.alt = ''; im.src = m.avatar || GUEST; if (m.ring){ im.style.borderColor = m.ring; im.style.boxShadow = '0 0 6px ' + m.ring; }
  const b = el('div', 'cb'); const n = el('b', 'nk' + (m.tier ? ' nk-' + m.tier : ''), m.name); const t = el('span', null, ' ' + m.text);
  b.append(n); if (m.ask) b.append(el('span', 'qtag', 'PYTANIE')); b.append(t);
  r.append(im, b);
  if (tok()){
    const x = el('div', 'cmod');
    const d = el('button', null, '🗑'); d.title = 'Usuń wiadomość'; d.type = 'button'; d.onclick = () => mod('delete', m.id);
    const bn = el('button', null, '⛔'); bn.title = 'Zablokuj użytkownika ' + m.uid; bn.type = 'button'; bn.onclick = () => { if (confirm('Zablokować ' + m.name + ' (#' + m.uid + ')?')) mod('ban', m.uid); };
    x.append(d, bn); r.appendChild(x);
  }
  return r;
}
function renderChat(s){
  const L = $('#chatList'); const atEnd = L.scrollHeight - L.scrollTop - L.clientHeight < 60;
  const keep = new Set(s.ids); [...L.querySelectorAll('.cm')].forEach(e => { if (!keep.has(+e.dataset.id)){ e.remove(); chatIds.delete(+e.dataset.id); } });
  s.chat.forEach(m => { if (!chatIds.has(m.id)){ chatIds.add(m.id); L.appendChild(msgEl(m)); } });
  if (s.last_id) lastId = Math.max(lastId, s.last_id);
  if (!s.on && !L.children.length) L.appendChild(el('p', 'hint empty', 'Czat ruszy razem z transmisją.'));
  if (s.on) L.querySelectorAll('.empty').forEach(e => e.remove());
  if (atEnd) L.scrollTop = L.scrollHeight;
}
function sysMsg(t){ const L = $('#chatList'); L.appendChild(el('p', 'csys', 'ℹ️ ' + t)); L.scrollTop = L.scrollHeight; }
let avCache = null;
function smallAvatar(){
  if (avCache !== null) return Promise.resolve(avCache);
  const src = user.avatar; if (!src) return Promise.resolve(avCache = '');
  return new Promise(res => { const im = new Image(); im.onload = () => { try { const c = document.createElement('canvas'); c.width = c.height = 64; const s = Math.min(im.width, im.height); c.getContext('2d').drawImage(im, (im.width - s) / 2, (im.height - s) / 2, s, s, 0, 0, 64, 64); avCache = c.toDataURL('image/webp', .8); } catch(e){ avCache = ''; } res(avCache); }; im.onerror = () => res(avCache = ''); im.src = src; });
}
$('#chatForm').onsubmit = async e => {
  e.preventDefault(); const nick = $('#nick').value.trim(), text = $('#chatInput').value.trim(); if (!nick || !text) return;
  LS.nick = nick; saveLS(); $('#chatSend').disabled = true; $('#chatMsg').textContent = '';
  try {
    const r = await fetch('/api/live-room/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({vid, name: nick, avatar: await smallAvatar(), text, ask: $('#askChk').checked, tester: window.LunaTesterCode ? window.LunaTesterCode() : ''})});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    $('#chatInput').value = ''; $('#askChk').checked = false; if (d.system) sysMsg(d.system); poll();
  } catch(x){ $('#chatMsg').textContent = '⚠️ ' + x.message; }
  $('#chatSend').disabled = false;
};

/* ---------- moderator ---------- */
async function mod(action, id, extra = {}){
  const r = await fetch('/api/admin/live-room', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: JSON.stringify(Object.assign({action, id}, extra))});
  if (r.status === 401){ sessionStorage.removeItem('luna.admin'); $('#modPanel').hidden = true; alert('Sesja moderatora wygasła.'); }
  poll();
}
$('#modStart').onclick = () => mod('start', null, {topic: $('#modTopic').value});
$('#modStop').onclick = () => { if (confirm('Zakończyć transmisję?')) mod('stop'); };
$('#modSched').onclick = () => mod('schedule');
$('#modAuto').onchange = e => mod('auto', null, {value: e.target.checked});
document.querySelectorAll('[data-ex]').forEach(b => b.onclick = () => mod('exercise', b.dataset.ex));
function renderMod(s){
  if (!s.queue){ $('#modPanel').hidden = true; return; }
  $('#modPanel').hidden = false; $('#modAuto').checked = s.auto; if (document.activeElement !== $('#modTopic')) $('#modTopic').value = s.topic || '';
  const Q = $('#modQueue'); Q.textContent = '';
  if (!s.queue.length) Q.appendChild(el('p', 'hint', 'Brak pytań w kolejce.'));
  s.queue.forEach(q => { const d = el('div', 'mq'); d.append(el('b', null, q.name + ': '), el('span', null, q.text));
    const a = el('button', 'pill primary sm', '✓ Odpowiedz'); a.type = 'button'; a.onclick = () => mod('approve', q.id);
    const x = el('button', 'pill ghost sm', '✕'); x.type = 'button'; x.onclick = () => mod('reject', q.id); d.append(a, x); Q.appendChild(d); });
  const B = $('#modBanned'); B.textContent = s.banned.length ? '' : 'nikt';
  s.banned.forEach(u => { const b = el('button', 'pill ghost sm', '#' + u + ' ✕'); b.type = 'button'; b.title = 'Odblokuj'; b.onclick = () => mod('unban', u); B.appendChild(b); });
}

/* ---------- stan ---------- */
function render(s){
  $('#liveBadge').hidden = !s.on; $('#viewers').hidden = !s.on;
  $('#viewers').textContent = '👁 ' + s.viewers + (s.viewers === 1 ? ' widz' : ' widzów');
  $('#topic').textContent = s.on ? (s.topic ? 'Temat: ' + s.topic : 'Pytania z czatu i ćwiczenia głosu') : '';
  $('#offline').hidden = s.on; $('#stage').classList.toggle('isoff', !s.on);
  $('#joinBtn').hidden = !s.on || joined;
  $('#nextLabel').textContent = 'Następna transmisja: ' + s.sched.next_label + ' (czas polski)';
  $('#weekly').textContent = s.sched.weekly + ' · ' + s.sched.hours + ' h';
  $('#schedText').textContent = s.sched.weekly + '. Następna: ' + s.sched.next_label + '.';
  $('#schedNote').textContent = s.sched.note || '';
  $('#chatInfo').textContent = s.on ? (s.queue_len ? `· ${s.queue_len} pytań w kolejce` : '') : '· offline';
  $('#chatForm').classList.toggle('disabled', !s.on);
  if (!poolSet){ poolSet = true; setPool(LS.pool ?? s.sched.pool); }
  const c = s.current, now = Date.now() + offset;
  if (s.on && c && now < c.start + c.dur * 1000 + 8000){
    $('#caption').hidden = false; $('#capTitle').textContent = (c.title || 'Luna') + ' · Luna, asystentka AI';
    $('#capQ').textContent = c.question ? `${c.name} pyta: ${c.question}` : ''; $('#capQ').hidden = !c.question; $('#capText').textContent = c.caption;
  } else $('#caption').hidden = true;
  renderChat(s); renderMod(s); syncAudio();
}
async function poll(){
  try {
    const t0 = Date.now();
    const r = await fetch('/api/live-room/state?vid=' + vid + '&since=' + lastId, {headers: tok() ? {'X-Admin-Token': tok()} : {}});
    const s = await r.json(); offset = s.now - (t0 + Date.now()) / 2; st = s; render(s);
  } catch(e){}
}
poll(); setInterval(poll, 2000);

/* ---------- e-mail ---------- */
$('#mailForm').onsubmit = async e => {
  e.preventDefault(); $('#mailMsg').textContent = '';
  try {
    const r = await fetch('/api/email/subscribe', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: $('#mailInput').value.trim(), consent: $('#mailConsent').checked})});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    $('#mailMsg').textContent = '✅ ' + d.message; $('#mailInput').value = ''; $('#mailConsent').checked = false;
  } catch(x){ $('#mailMsg').textContent = '⚠️ ' + x.message; }
};
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
})();
