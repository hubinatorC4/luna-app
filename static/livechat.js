/* Luna – czat na żywo („Napisz do twórcy”) i skrzynka moderatora. Cała treść wstawiana przez textContent (bez HTML). */
(() => {
const $ = s => document.querySelector(s);
const live = $('#live'), inbox = $('#inbox');
let vid = localStorage.getItem('luna.live.vid');
if (!vid || !/^[0-9a-f]{32}$/.test(vid)){ const a = new Uint8Array(16); crypto.getRandomValues(a); vid = [...a].map(b => b.toString(16).padStart(2, '0')).join(''); localStorage.setItem('luna.live.vid', vid); }
const userName = () => (window.UserName && window.UserName()) || '';
const fmt = t => new Date(t).toLocaleString('pl-PL', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
const MOD_AV = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#2a1c12"/><circle cx="32" cy="25" r="11" fill="#f0a040"/><path d="M12 58c2-12 10-18 20-18s18 6 20 18" fill="#f0a040"/></svg>');
const GUEST_AV = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#3a4a5a"/><circle cx="32" cy="25" r="11" fill="#cfe"/><path d="M12 58c2-12 10-18 20-18s18 6 20 18" fill="#cfe"/></svg>');

function row(list, m, mine, avSrc, label){
  if (m.from === 'system'){ const n = document.createElement('div'); n.className = 'msg sys'; n.textContent = 'ℹ️ ' + m.text; list.appendChild(n); return; }
  const r = document.createElement('div'); r.className = 'msgrow ' + (mine ? 'me' : 'luna');
  const im = document.createElement('img'); im.className = 'mav' + (mine && m.from === 'visitor' ? ' me' : ''); im.alt = ''; im.src = avSrc || GUEST_AV;
  const b = document.createElement('div'); b.className = 'msg ' + (mine ? 'me' : 'luna');
  const sm = document.createElement('small'); sm.className = 'meta'; const nm = document.createElement('span'); nm.className = 'nk' + (m.from === 'visitor' && m.tier ? ' nk-' + m.tier : ''); nm.textContent = label; sm.append(nm, ' · ' + fmt(m.t));
  const tx = document.createElement('div'); tx.textContent = m.text;
  b.append(sm, tx); r.append(im, b); list.appendChild(r);
}
// mały awatar (64 px) do wysłania z wiadomością
let avCache = {src: null, out: ''};
function smallAvatar(){
  const src = window.UserAvatarSrc ? window.UserAvatarSrc() : '';
  if (!src) return Promise.resolve('');
  if (avCache.src === src) return Promise.resolve(avCache.out);
  return new Promise(res => { const im = new Image(); im.onload = () => { try { const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'); const s = Math.min(im.width, im.height) || 64; x.drawImage(im, (im.width - s) / 2, (im.height - s) / 2, s, s, 0, 0, 64, 64); let out = c.toDataURL('image/webp', .8); if (!out.startsWith('data:image/webp')) out = c.toDataURL('image/jpeg', .8); avCache = {src, out}; res(out); } catch(e){ res(''); } }; im.onerror = () => res(''); im.src = src; });
}
/* ---------- odwiedzający ---------- */
let msgs = [], timer = null;
function renderLive(){
  const L = $('#liveList'); L.textContent = '';
  if (!msgs.length){ const e = document.createElement('p'); e.className = 'hint'; e.textContent = 'Zadaj pytanie, zgłoś pomysł albo problem. Wiadomość trafi do skrzynki twórcy.'; L.appendChild(e); }
  const me = window.UserAvatarSrc ? window.UserAvatarSrc() : '';
  msgs.forEach(m => row(L, m, m.from === 'visitor', m.from === 'visitor' ? me : MOD_AV, m.from === 'visitor' ? (m.name || 'Ty') : 'Zespół Luny'));
  L.scrollTop = L.scrollHeight;
  $('#liveWho').textContent = 'Piszesz jako: ' + (userName() || 'Gość') + ' (nick i awatar zmienisz w Ustawieniach → Twój profil).';
}
function badge(el, n){ el.hidden = !n; el.textContent = n > 9 ? '9+' : String(n || ''); }
async function poll(){
  const open = live.open;
  try {
    const r = await fetch('/api/live/poll?vid=' + vid + '&since=0&mark=' + (open ? 1 : 0)); const d = await r.json();
    if (r.ok){ const changed = d.msgs.length !== msgs.length; msgs = d.msgs; if (open && changed) renderLive(); badge($('#liveBadge'), open ? 0 : d.unread); }
  } catch(e){}
}
function schedule(){ clearInterval(timer); timer = setInterval(poll, live.open ? 5000 : 45000); }
function openLive(){ live.showModal(); renderLive(); poll().then(renderLive); schedule(); setTimeout(() => $('#liveInput').focus(), 50); }
$('#liveBtn').onclick = openLive; $('#liveCta').onclick = openLive;
$('#liveClose').onclick = () => live.close();
live.addEventListener('close', () => { schedule(); if (location.hash === '#live') history.replaceState(null, '', location.pathname); });
$('#liveForm').onsubmit = async e => {
  e.preventDefault(); const t = $('#liveInput').value.trim(); if (!t) return;
  $('#liveSend').disabled = true; $('#liveErr').textContent = '';
  try {
    const r = await fetch('/api/live/send', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({vid, name: userName(), avatar: await smallAvatar(), text: t, tester: window.LunaTesterCode ? window.LunaTesterCode() : ''})});
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || r.status);
    msgs = d.msgs; $('#liveInput').value = ''; renderLive();
  } catch(err){ $('#liveErr').textContent = '⚠️ ' + (err.message === 'empty' ? 'Wiadomość jest pusta.' : err.message); }
  $('#liveSend').disabled = false;
};
$('#liveInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); $('#liveForm').requestSubmit(); } });
if (location.hash === '#live') setTimeout(openLive, 300);
window.addEventListener('hashchange', () => { if (location.hash === '#live' && !live.open) openLive(); });
poll(); schedule();

/* ---------- moderator ---------- */
const tok = () => sessionStorage.getItem('luna.admin') || '';
async function api(path, body){
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers:{'Content-Type':'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify(body) : undefined});
  if (r.status === 401){ sessionStorage.removeItem('luna.admin'); $('#inboxBtn').hidden = true; if (inbox.open) inbox.close(); throw new Error('401'); }
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
let cur = null, itimer = null;
async function refreshInbox(){
  if (!tok()){ $('#inboxBtn').hidden = true; return; }
  try {
    const d = await api('/api/admin/live');
    $('#inboxBtn').hidden = false; badge($('#inboxBadge'), d.unread); $('#admInboxN').textContent = d.unread ? '(' + d.unread + ')' : '';
    if (inbox.open && !cur){
      const L = $('#inboxList'); L.textContent = ''; $('#inboxEmpty').hidden = d.convs.length > 0;
      d.convs.forEach(c => {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'conv' + (c.unread ? ' unread' : '');
        const im = document.createElement('img'); im.className = 'mav'; im.alt = ''; im.src = c.avatar || GUEST_AV; if (c.ring){ im.style.borderColor = c.ring; im.style.boxShadow = '0 0 8px ' + c.ring; }
        const t = document.createElement('span'); t.className = 'ct';
        const n = document.createElement('b'); n.textContent = c.name; const s = document.createElement('small'); s.textContent = fmt(c.updated) + ' · #' + c.vid.slice(0, 6);
        const l = document.createElement('span'); l.className = 'last'; l.textContent = (c.last_from === 'moderator' ? 'Ty: ' : '') + c.last;
        t.append(n, s, l); b.append(im, t);
        if (c.unread){ const u = document.createElement('span'); u.className = 'badge'; u.textContent = c.unread; b.appendChild(u); }
        b.onclick = () => openConv(c.vid); L.appendChild(b);
      });
    } else if (inbox.open && cur) loadConv();
  } catch(e){}
}
async function loadConv(){
  try {
    const d = await api('/api/admin/live/' + cur);
    $('#inboxName').textContent = d.name + ' · #' + d.vid.slice(0, 6); $('#inboxAv').src = d.avatar || GUEST_AV; $('#inboxAv').style.borderColor = d.ring || '';
    const T = $('#inboxThread'), atEnd = T.scrollHeight - T.scrollTop - T.clientHeight < 40; T.textContent = '';
    d.msgs.forEach(m => row(T, m, m.from === 'moderator', m.from === 'moderator' ? MOD_AV : (d.avatar || GUEST_AV), m.from === 'moderator' ? 'Ty (moderator)' : (m.name || d.name)));
    if (d.ring) T.querySelectorAll('.msgrow.luna .mav').forEach(im => { if (!im.src.includes('2a1c12')) { im.style.borderColor = d.ring; im.style.boxShadow = '0 0 8px ' + d.ring; } });
    if (atEnd || !T.dataset.v) T.scrollTop = T.scrollHeight; T.dataset.v = '1';
  } catch(e){ $('#inboxErr').textContent = '⚠️ ' + e.message; }
}
function openConv(v){ cur = v; $('#inboxListView').hidden = true; $('#inboxThreadView').hidden = false; $('#inboxThread').dataset.v = ''; $('#inboxErr').textContent = ''; loadConv().then(refreshInbox); }
function openInbox(){ cur = null; $('#inboxListView').hidden = false; $('#inboxThreadView').hidden = true; inbox.showModal(); refreshInbox(); clearInterval(itimer); itimer = setInterval(refreshInbox, 5000); }
$('#inboxBtn').onclick = openInbox;
$('#admInbox').onclick = () => { $('#admin').close(); openInbox(); };
$('#inboxClose').onclick = () => inbox.close();
inbox.addEventListener('close', () => { clearInterval(itimer); itimer = setInterval(refreshInbox, 30000); cur = null; });
$('#inboxBack').onclick = () => { cur = null; $('#inboxListView').hidden = false; $('#inboxThreadView').hidden = true; refreshInbox(); };
$('#inboxDel').onclick = async () => { if (!cur || !confirm('Usunąć tę rozmowę?')) return; try { await api('/api/admin/live/delete', {vid: cur}); $('#inboxBack').onclick(); } catch(e){} };
$('#inboxForm').onsubmit = async e => {
  e.preventDefault(); const t = $('#inboxInput').value.trim(); if (!t || !cur) return;
  try { await api('/api/admin/live/reply', {vid: cur, text: t}); $('#inboxInput').value = ''; $('#inboxThread').dataset.v = ''; loadConv(); } catch(err){ $('#inboxErr').textContent = '⚠️ ' + err.message; }
};
$('#inboxInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); $('#inboxForm').requestSubmit(); } });
window.LunaInboxRefresh = refreshInbox;
refreshInbox(); itimer = setInterval(refreshInbox, 30000);
const origSet = sessionStorage.setItem.bind(sessionStorage);
sessionStorage.setItem = (k, v) => { origSet(k, v); if (k === 'luna.admin') setTimeout(refreshInbox, 100); };
})();
