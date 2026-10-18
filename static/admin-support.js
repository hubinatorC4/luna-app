/* Widok moderatora „Pomoc na żywo”: dostępność (heartbeat), rozmowy na żywo, zgłoszenia „Napisz do moderatora”.
   Token tylko w sessionStorage tej karty (jak panel.html). Odpowiedzi idą do Skrzynki użytkownika jako „Zespół Luny · Moderator”. */
(() => {
const $ = s => document.querySelector(s);
const tok = () => sessionStorage.getItem('luna.admin') || '';
const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
const when = t => new Date(t > 1e12 ? t : t * 1000).toLocaleString('pl-PL');
let CUR = '', DATA = null, pingT = 0, loadT = 0, convT = 0, lastHash = '';
async function api(path, body){
  const r = await fetch(path, body ? {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: JSON.stringify(body)} : {headers: {'X-Admin-Token': tok()}});
  if (r.status === 401){ sessionStorage.removeItem('luna.admin'); show(); throw new Error('Sesja wygasła – zaloguj się ponownie.'); }
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function show(){ const on = !!tok(); $('#login').hidden = on; $('#app').hidden = !on; $('#logout').hidden = !on; clearInterval(pingT); clearInterval(loadT);
  if (on){ $('#avail').checked = sessionStorage.getItem('luna.sup.avail') !== '0'; ping(); load(); pingT = setInterval(ping, 20000); loadT = setInterval(load, 8000); setTimeout(dmReports, 300); } }
$('#lf').onsubmit = async e => { e.preventDefault(); $('#lerr').textContent = '';
  try { const r = await fetch('/api/admin/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({passphrase: $('#pass').value})}); const d = await r.json();
    $('#pass').value = ''; if (!r.ok) throw new Error(d.error || r.status); sessionStorage.setItem('luna.admin', d.admin_token); show(); } catch(x){ $('#lerr').textContent = '⚠️ ' + x.message; } };
$('#logout').onclick = async () => { try { await api('/api/admin/support/ping', {available: false}); await api('/api/admin/logout', {}); } catch(e){} sessionStorage.removeItem('luna.admin'); show(); };
async function ping(){ try { const d = await api('/api/admin/support/ping', {available: $('#avail').checked}); const o = $('#onl'); o.textContent = d.online ? 'online – użytkownicy mogą pisać na żywo' : 'offline – użytkownicy zostawiają wiadomość'; o.classList.toggle('on', d.online); } catch(e){} }
$('#avail').onchange = () => { sessionStorage.setItem('luna.sup.avail', $('#avail').checked ? '1' : '0'); ping(); };
window.addEventListener('pagehide', () => { try { fetch('/api/admin/support/ping', {method: 'POST', keepalive: true, headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: '{"available":false}'}); } catch(e){} });
async function load(){
  try { const q = new URLSearchParams({status: $('#fSt').value, cat: $('#fCat').value, q: $('#fQ').value.trim()}); DATA = await api('/api/admin/support?' + q);
    if ($('#fCat').options.length === 1) Object.entries(DATA.cats).forEach(([k, v]) => $('#fCat').appendChild(Object.assign(el('option', '', v), {value: k})));
    renderLive(); const h = JSON.stringify(DATA.tickets.map(t => [t.id, t.status, t.updated])); if (h !== lastHash && !document.activeElement.closest('.tk')){ lastHash = h; renderTickets(); }
    document.title = (DATA.new ? `(${DATA.new}) ` : '') + 'Pomoc na żywo – moderator';
  } catch(e){} }
function renderLive(){ const L = $('#live'); L.textContent = ''; const open = DATA.live.filter(s => !s.closed); $('#liveN').textContent = `(${open.length} otwartych)`;
  if (!DATA.live.length) L.appendChild(el('p', 'hint', 'Cisza jak w bibliotece – nikt teraz nie czeka. 📚'));
  DATA.live.forEach(s => { const b = el('button', 'it' + (s.unread ? ' new' : '')); b.type = 'button'; if (s.unread) b.appendChild(el('span', 'u', s.unread));
    b.appendChild(el('b', '', `${s.who} · ${(s.lang || 'pl').toUpperCase()}${s.closed ? ' · zakończona' : ''}`)); b.appendChild(el('br')); b.appendChild(el('small', '', `${when(s.updated)} · ${s.last || '(jeszcze bez wiadomości)'}`));
    b.onclick = () => openConv(s.sid); L.appendChild(b); }); }
async function openConv(sid){ CUR = sid; $('#conv').hidden = false; clearInterval(convT); await loadConv(); convT = setInterval(loadConv, 3000); $('#cIn').focus(); }
async function loadConv(){ if (!CUR) return; try { const c = await api('/api/admin/support/live?sid=' + CUR); $('#cWho').textContent = `${c.who} · rozpoczęta ${when(c.created)}${c.closed ? ' · zakończona' : ''}`;
    $('#cCtxW').hidden = !c.ctx; $('#cCtx').textContent = c.ctx || ''; const L = $('#cLog'); const atEnd = L.scrollHeight - L.scrollTop - L.clientHeight < 40; L.textContent = '';
    if (!c.msgs.length) L.appendChild(el('div', 'm system', 'Użytkownik jeszcze nic nie napisał.'));
    c.msgs.forEach(m => L.appendChild(el('div', 'm ' + m.from, m.from === 'system' ? 'Rozmowa zakończona' : m.text))); if (atEnd) L.scrollTop = L.scrollHeight;
  } catch(e){ clearInterval(convT); $('#conv').hidden = true; CUR = ''; } }
$('#cf').onsubmit = async e => { e.preventDefault(); const t = $('#cIn').value.trim(); if (!t) return; $('#cErr').textContent = '';
  try { await api('/api/admin/support/reply', {sid: CUR, text: t}); $('#cIn').value = ''; loadConv(); } catch(x){ $('#cErr').textContent = '⚠️ ' + x.message; } };
$('#cClose').onclick = async () => { try { await api('/api/admin/support/close', {sid: CUR}); loadConv(); load(); } catch(e){} };
$('#cDel').onclick = async () => { if (!confirm('Usunąć tę rozmowę na stałe?')) return; try { await api('/api/admin/support/close', {sid: CUR, delete: true}); clearInterval(convT); $('#conv').hidden = true; CUR = ''; load(); } catch(e){} };
function renderTickets(){ const L = $('#tks'); L.textContent = ''; $('#tkN').textContent = `(${DATA.new} nowych)`;
  const T = DATA.tickets; if (!T.length){ L.appendChild(el('p', 'hint', 'Brak zgłoszeń. Albo wszyscy są szczęśliwi, albo jeszcze o nas nie wiedzą 😄')); return; }
  T.forEach(t => { const c = el('article', 'tk ' + (t.status === 'nowe' ? 'nowe' : '')); c.appendChild(el('h3', '', `${t.id} · ${t.title || '(bez tytułu – zgłoszenie techniczne)'}`));
    const reply = t.inbox ? 'odpowiedź → Skrzynka użytkownika' : (t.email ? 'odpowiedź → e-mail' + (DATA.email ? '' : ' (wysyłka e-mail wyłączona – brak klucza)') : 'odpowiedź → „Moje zgłoszenia” na urządzeniu użytkownika');
    c.appendChild(el('div', 'meta', `${t.category} · ${t.status} · ${when(t.t)} · ${(t.lang || t.env?.lang || '').toUpperCase()} · ${reply}${t.email ? ' · ' + t.email : ''}`));
    c.appendChild(el('div', 'desc', t.description));
    if (t.transcript){ const d = el('details'); d.appendChild(el('summary', '', 'Rozmowa z czatu (za zgodą)')); d.appendChild(el('pre', '', t.transcript)); c.appendChild(d); }
    if (t.has_shot){ const b = el('button', '', '🖼️ Pokaż zrzut ekranu'); b.type = 'button'; b.onclick = async () => { try { const d = await api('/api/admin/support/shot?id=' + t.id); const i = el('img'); i.src = d.shot; i.alt = 'Zrzut ekranu ' + t.id; b.replaceWith(i); } catch(e){ alert(e.message); } }; c.appendChild(b); }
    (t.thread || []).forEach(m => c.appendChild(el('div', 'thr', `Zespół Luny · Moderator (${when(m.t)}):\n${m.text}`)));
    const ta = el('textarea'); ta.placeholder = 'Odpowiedź jako Zespół Luny · Moderator'; ta.maxLength = 3000; ta.setAttribute('aria-label', 'Odpowiedź do ' + t.id); c.appendChild(ta);
    const row = el('div', 'row'); const sel = el('select'); DATA.statuses.forEach(s => sel.appendChild(Object.assign(el('option', '', s), {value: s, selected: s === t.status}))); sel.setAttribute('aria-label', 'Status');
    const send = el('button', '', 'Wyślij odpowiedź'); send.type = 'button'; const msg = el('span', 'hint');
    send.onclick = async () => { try { await api('/api/admin/support/ticket', {id: t.id, reply: ta.value, status: sel.value}); msg.textContent = '✅ Zapisano'; lastHash = ''; setTimeout(load, 300); } catch(e){ msg.textContent = '⚠️ ' + e.message; } };
    sel.onchange = async () => { try { await api('/api/admin/support/ticket', {id: t.id, status: sel.value}); msg.textContent = '✅ Status zmieniony'; } catch(e){ msg.textContent = '⚠️ ' + e.message; } };
    row.append(sel, send, msg); c.appendChild(row); L.appendChild(c); }); }
['#fSt', '#fCat'].forEach(s => $(s).onchange = () => { lastHash = ''; load(); }); let qT; $('#fQ').oninput = () => { clearTimeout(qT); qT = setTimeout(() => { lastHash = ''; load(); }, 300); };
/* ---------- zgłoszenia z czatu 1:1 (wiadomości i zdjęcia) ---------- */
async function dmReports(){ try { const d = await api('/api/admin/inbox'); const L = $('#dmr'); const open = d.reports.filter(r => r.status === 'open');
    $('#dmN').textContent = `(${open.length} otwartych)`; L.textContent = '';
    if (!d.reports.length){ L.appendChild(el('p', 'hint', 'Brak zgłoszeń – w czacie panuje sielanka 🌿')); return; }
    d.reports.slice(0, 60).forEach(r => { const c = el('article', 'tk ' + (r.status === 'open' ? 'nowe' : ''));
      c.appendChild(el('h3', '', `${r.photo ? '📷 Zdjęcie' : r.kind === 'message' ? '💬 Wiadomość' : '👤 Konto'} · ${r.reported} (zgłasza: ${r.reporter})`));
      c.appendChild(el('div', 'meta', `${when(r.t)} · status: ${({open: 'otwarte', remove: 'usunięte', dismiss: 'odrzucone', ban: 'ban'})[r.status] || r.status}${r.reason ? ' · powód: ' + r.reason : ''}`));
      if (r.message && !r.photo) c.appendChild(el('div', 'desc', r.message));
      if (r.img_url){ const i = el('img'); i.alt = 'Zgłoszone zdjęcie'; i.style.maxWidth = '320px'; fetch(r.img_url, {headers: {'X-Admin-Token': tok()}}).then(x => x.ok ? x.blob() : null).then(b => { if (b) i.src = URL.createObjectURL(b); }); c.appendChild(i); }
      if (r.status === 'open'){ const row = el('div', 'row');
        [['remove', r.photo ? 'Usuń zdjęcie' : 'Usuń wiadomość'], ['dismiss', 'Odrzuć zgłoszenie (przywróć)'], ['ban', 'Zbanuj autora']].forEach(([a, t]) => { if (a === 'remove' && r.kind !== 'message') return;
          const b = el('button', a === 'ban' ? 'danger' : '', t); b.type = 'button'; b.onclick = async () => { if (a === 'ban' && !confirm('Zbanować ' + r.reported + ' na czatach?')) return;
            try { await api('/api/admin/inbox/report', {id: r.id, action: a}); dmReports(); } catch(e){ alert(e.message); } }; row.appendChild(b); });
        c.appendChild(row); }
      L.appendChild(c); });
  } catch(e){} }
setInterval(() => { if (tok()) dmReports(); }, 30000);
show();
})();
