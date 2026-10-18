/* Luna – Skrzynka (prywatne wiadomości), Znajomi i czat 1:1. Ładowany tylko na /skrzynka.html i /znajomi.html (leniwie, bez wpływu na stronę główną). */
(() => {
const LS = ['pl', 'en', 'es', 'de', 'uk'];
let lang = (new URLSearchParams(location.search).get('lang') || document.documentElement.lang || (() => { try { return localStorage.getItem('luna.lang'); } catch(e){ return ''; } })() || 'pl').slice(0, 2);
if (!LS.includes(lang)) lang = 'pl';
const T = Object.assign({}, window.LUNA_IB_T.pl, window.LUNA_IB_T[lang]);
T.cat_icon = window.LUNA_IB_T.pl.cat_icon;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const L = p => p + (lang !== 'pl' ? (p.includes('?') ? '&' : '?') + 'lang=' + lang : '');
let csrf = '', user = null, tab = document.body.dataset.tab || 'inbox', cat = '', box = 'inbox', FR = null, chat = null;
const root = $('#ib');

function toast(t){ let el = $('#ibToast'); if (!el){ el = document.createElement('div'); el.id = 'ibToast'; el.className = 'ib-toast'; el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite'); document.body.appendChild(el); }
  el.textContent = t; el.hidden = false; el.classList.remove('pop'); void el.offsetWidth; el.classList.add('pop'); clearTimeout(toast._t); toast._t = setTimeout(() => el.hidden = true, 2600); }
async function api(u, body){
  const o = {credentials: 'same-origin', headers: {}};
  if (body){ o.method = 'POST'; o.headers['Content-Type'] = 'application/json'; o.headers['X-CSRF-Token'] = csrf; o.body = JSON.stringify(body); }
  try { const at = sessionStorage.getItem('luna.admin'); if (at) o.headers['X-Admin-Token'] = at; } catch(e){}
  const r = await fetch(L(u), o); const d = await r.json().catch(() => ({}));
  if (!r.ok){ const e = new Error(d.error || T.err); e.status = r.status; e.data = d; throw e; }
  return d;
}
const fmtT = t => { const s = Date.now() / 1000 - t; const rtf = new Intl.RelativeTimeFormat(lang, {numeric: 'auto'});
  if (s < 60) return T.ago_now; if (s < 3600) return rtf.format(-Math.round(s / 60), 'minute'); if (s < 86400) return rtf.format(-Math.round(s / 3600), 'hour');
  if (s < 7 * 86400) return rtf.format(-Math.round(s / 86400), 'day'); return new Date(t * 1000).toLocaleDateString(lang); };
const clock = t => new Date(t * 1000).toLocaleTimeString(lang, {hour: '2-digit', minute: '2-digit'});
const MODB = p => (p.mod ? ' <span class="mod-badge">🛡️ Moderator</span>' : '') + (p.model ? ' <span class="mdl-badge">💗 Modelka Luny</span>' : '');
const nk = p => `<span class="nk${p.tier ? ' nk-' + p.tier : ''}">${esc(p.nick)}</span>${MODB(p)}${p.partner ? ` <span class="ib-pt" title="${esc(T.partner)}" aria-label="${esc(T.partner)}">💖</span>` : ''}`;
const av = p => p.mod ? ((S) => `<span class="mod-av" style="--s:${S}px" aria-hidden="true"><img src="/mod-av/mustang-512.webp" alt="" width="${S}" height="${S}" decoding="async"></span>`)(40) : `<span class="ib-av${p.model ? ' mdl-ring' : ''}${p.partner ? ' partner' : ''}${p.tier ? ' t-' + p.tier : ''}${p.pr && p.pr.on ? ' on' : ''}" aria-hidden="true">${esc(p.ini || '?')}</span>`;
// status online (serwer zwraca pr tylko gdy osoba na to pozwala): {on:true} albo {min:X} ≤ 60
const prTxt = p => !p.pr ? '' : p.pr.on ? T.online : T.ago.replace('{n}', p.pr.min);
const idHtml = p => { const d = p.ident || {}, x = [];
  if (d.g) x.push(d.g === 'other' && d.gx ? d.gx : T['g_' + d.g]);
  if (d.pn) x.push(d.pn === 'custom' ? d.pnx : T['p_' + d.pn]);
  if (d.age) x.push(String(T.id_age || '{n}').replace('{n}', d.age));
  const y = x.filter(Boolean); return y.length ? `<small class="ib-id">${esc(y.join(' · '))}</small>` : ''; };
const prHtml = p => p.pr ? `<small class="ib-pr${p.pr.on ? ' on' : ''}">${p.pr.on ? '<i class="on-dot" aria-hidden="true"></i>' : ''}${esc(prTxt(p))}</small>` : '';

/* ---------- szkielet ---------- */
function frame(){
  root.innerHTML = `<div class="ib-tabs" role="tablist" aria-label="${esc(T.h1)}">
    ${['inbox', 'friends', 'privacy'].map(k => `<button type="button" role="tab" id="tb-${k}" aria-controls="pn-${k}" data-tab="${k}">${esc(T['tab_' + k])}<b class="ib-badge" data-badge="${k}" hidden></b></button>`).join('')}</div>
    <section id="pn-inbox" role="tabpanel" aria-labelledby="tb-inbox" hidden></section>
    <section id="pn-friends" role="tabpanel" aria-labelledby="tb-friends" hidden></section>
    <section id="pn-privacy" role="tabpanel" aria-labelledby="tb-privacy" hidden></section>
    <div class="ib-chat" id="ibChat" hidden role="dialog" aria-modal="true" aria-labelledby="chatPeer"></div>`;
  root.querySelectorAll('[role=tab]').forEach(b => { b.onclick = () => go(b.dataset.tab); b.onkeydown = e => {
    const tabs = [...root.querySelectorAll('[role=tab]')], i = tabs.indexOf(b);
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft'){ const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length]; n.focus(); n.click(); } }; });
}
function go(t){
  tab = t;
  root.querySelectorAll('[role=tab]').forEach(b => { const on = b.dataset.tab === t; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; });
  root.querySelectorAll('[role=tabpanel]').forEach(p => p.hidden = p.id !== 'pn-' + t);
  if (t === 'inbox') renderInbox(); else if (t === 'friends') renderFriends(); else renderPrivacy();
  history.replaceState(null, '', location.pathname + location.search + (t === 'privacy' ? '#prywatnosc' : t === 'friends' && document.body.dataset.tab !== 'friends' ? '#znajomi' : t === 'inbox' && document.body.dataset.tab !== 'inbox' ? '#skrzynka' : ''));
}
function badges(u){
  if (!u) return;
  const set = (k, n) => { const b = root.querySelector(`[data-badge="${k}"]`); if (!b) return; b.hidden = !n; b.textContent = n > 99 ? '99+' : n; b.setAttribute('aria-label', T.unread_aria.replace('{n}', n)); };
  set('inbox', u.inbox); set('friends', (u.chat || 0) + (u.requests || 0));
  try { parent !== window && parent.postMessage({luna: 'inbox-unread', total: u.total}, location.origin); } catch(e){}
  try { localStorage.setItem('luna.ib.unread', String(u.total || 0)); } catch(e){}
}

/* ---------- Skrzynka ---------- */
async function renderInbox(){
  const host = $('#pn-inbox');
  const chips = ['', 'important', 'updates', 'battles', 'friends'];
  if (!host.dataset.ready){
    host.dataset.ready = 1;
    host.innerHTML = `<div class="ib-chips" role="group" aria-label="${esc(T.all)}">${chips.map(c => `<button type="button" class="ib-chip" data-cat="${c}">${c ? T.cat_icon[c] + ' ' : ''}${esc(c ? T[c] : T.all)} <b data-cc="${c}"></b></button>`).join('')}
      <button type="button" class="ib-chip" data-box="archive">🗂️ ${esc(T.archive)}</button></div>
      <div class="ib-bar"><button type="button" class="ib-link" id="readAll">✓ ${esc(T.read_all)}</button></div><ul class="ib-list" id="ibList" aria-live="polite"></ul>`;
    host.querySelectorAll('[data-cat]').forEach(b => b.onclick = () => { cat = b.dataset.cat; box = 'inbox'; renderInbox(); });
    host.querySelector('[data-box]').onclick = () => { box = 'archive'; cat = ''; renderInbox(); };
    $('#readAll').onclick = async () => { try { badges((await api('/api/inbox/act', {action: 'read_all'})).unread); renderInbox(); } catch(e){ toast(e.message); } };
  }
  host.querySelectorAll('[data-cat]').forEach(b => b.setAttribute('aria-pressed', box === 'inbox' && b.dataset.cat === cat));
  host.querySelector('[data-box]').setAttribute('aria-pressed', box === 'archive');
  let d; try { d = await api('/api/inbox?cat=' + cat + '&box=' + box); } catch(e){ $('#ibList').innerHTML = `<li class="ib-empty">${esc(e.message)}</li>`; return; }
  badges(d.unread);
  host.querySelectorAll('[data-cc]').forEach(b => { const n = b.dataset.cc ? d.unread.cats[b.dataset.cc] : d.unread.inbox; b.textContent = n ? n : ''; });
  const ul = $('#ibList');
  if (!d.items.length){ ul.innerHTML = `<li class="ib-empty">${esc(box === 'archive' ? T.empty_arch : T.empty)}</li>`; return; }
  ul.innerHTML = d.items.map(m => `<li class="ib-msg cat-${m.cat}${m.read ? '' : ' unread'}" data-id="${m.id}">
    <button type="button" class="ib-mh" aria-expanded="false"><span class="ib-ic" aria-hidden="true">${T.cat_icon[m.cat]}</span>
      <span class="ib-mt"><b>${esc(m.title)}</b><small>${esc(T[m.cat])} · ${esc(fmtT(m.t))}${m.read ? '' : `<em class="ib-new"> · ${esc(T.new_lbl)}</em>`}</small></span></button>
    <div class="ib-mb" hidden><p>${esc(m.body)}</p><div class="ib-acts">
      ${m.link ? `<a class="ib-btn primary" href="${esc(L(m.link))}" target="_top">${esc(T.open_b)}</a>` : ''}
      <button type="button" class="ib-btn" data-a="${m.archived ? 'unarchive' : 'archive'}">${esc(m.archived ? T.unarchive_b : T.archive_b)}</button>
      <button type="button" class="ib-btn" data-a="unread">${esc(T.mark_unread)}</button>
      <button type="button" class="ib-btn danger" data-a="delete">${esc(T.delete_b)}</button></div></div></li>`).join('');
  ul.querySelectorAll('.ib-msg').forEach(li => {
    const h = li.querySelector('.ib-mh'), b = li.querySelector('.ib-mb');
    h.onclick = async () => { const open = b.hidden; b.hidden = !open; h.setAttribute('aria-expanded', open);
      if (open && li.classList.contains('unread')){ li.classList.remove('unread'); const n = li.querySelector('.ib-new'); if (n) n.remove();
        try { badges((await api('/api/inbox/act', {ids: [li.dataset.id], action: 'read'})).unread); } catch(e){} } };
    li.querySelectorAll('[data-a]').forEach(x => x.onclick = async () => {
      try { const r = await api('/api/inbox/act', {ids: [li.dataset.id], action: x.dataset.a}); badges(r.unread);
        toast({delete: T.deleted, archive: T.archived, unarchive: T.restored}[x.dataset.a] || '✓'); renderInbox(); } catch(e){ toast(e.message); } });
  });
}

/* ---------- Znajomi ---------- */
async function loadFriends(){ FR = await api('/api/friends'); return FR; }
function rowBtns(p, kind){
  if (kind === 'in') return `<button class="ib-btn primary" data-f="accept">${esc(T.accept)}</button><button class="ib-btn" data-f="decline">${esc(T.decline)}</button><button class="ib-btn danger" data-f="block">${esc(T.block)}</button>`;
  if (kind === 'out') return `<button class="ib-btn" data-f="cancel">${esc(T.cancel)}</button>`;
  if (kind === 'blocked') return `<button class="ib-btn" data-f="unblock">${esc(T.unblock)}</button>`;
  return `<button class="ib-btn ib-star${p.close ? ' on' : ''}" data-f="${p.close ? 'unclose' : 'close'}" aria-pressed="${p.close ? 'true' : 'false'}" aria-label="${esc(p.close ? T.close_rm : T.close_add)}" title="${esc(T.close_h)}">${p.close ? '★' : '☆'}</button><button class="ib-btn primary" data-f="chat">💬 ${esc(T.write)}${p.unread ? ` <b class="ib-badge">${p.unread}</b>` : ''}</button>
    <details class="ib-more"><summary aria-label="${esc(T.more)}">⋯</summary><div><button class="ib-btn" data-f="remove">${esc(T.remove)}</button><button class="ib-btn danger" data-f="block">${esc(T.block)}</button><button class="ib-btn danger" data-f="report" data-report="user:${p.pid}">🚩 ${esc(T.report)}</button></div></details>`;
}
const row = (p, kind) => `<li class="ib-fr" data-pid="${p.pid}">${av(p)}<span class="ib-fn">${nk(p)}${kind === 'friends' ? `${idHtml(p)}${prHtml(p)}<small>${p.last ? esc(p.last.x) : esc(T.since) + ' ' + new Date(p.since * 1000).toLocaleDateString(lang)}</small>` : ''}</span><span class="ib-fa">${rowBtns(p, kind)}</span></li>`;
async function renderFriends(){
  const host = $('#pn-friends');
  let f; try { f = await loadFriends(); } catch(e){ host.innerHTML = `<p class="ib-empty">${esc(e.message)}</p>`; return; }
  host.innerHTML = `
    <div class="ib-card ib-me">${av(f.me)}<div><small>${esc(T.me_h)}</small><div class="ib-mynick">${nk(f.me)}</div></div></div>
    ${f.has_nick ? '' : `<form class="ib-card ib-form" id="nickForm"><label for="nickIn">${esc(T.nick_need)}</label><div class="ib-row"><input id="nickIn" maxlength="30" minlength="2" required autocomplete="nickname" placeholder="${esc(T.nick_ph)}"><button class="ib-btn primary">${esc(T.nick_save)}</button></div></form>`}
    <form class="ib-card ib-form" id="addForm"><h2>👋 ${esc(T.add_h)}</h2><label class="sr" for="addIn">${esc(T.add_ph)}</label><div class="ib-row"><input id="addIn" maxlength="30" minlength="2" required autocomplete="off" placeholder="${esc(T.add_ph)}"><button class="ib-btn primary">${esc(T.add_b)}</button></div></form>
    <div class="ib-card"><h2>🔗 ${esc(T.inv_h)}</h2><p class="ib-mut">${esc(T.inv_p)}</p><div class="ib-inv"><input id="invUrl" readonly value="${esc(f.invite.url)}" aria-label="${esc(T.inv_h)}"></div>
      <div class="ib-acts"><button class="ib-btn primary" id="invCopy">${esc(T.copy)}</button>${navigator.share ? `<button class="ib-btn" id="invShare">${esc(T.share)}</button>` : ''}<button class="ib-btn" id="invQr" aria-expanded="false">▦ ${esc(T.qr_b)}</button><button class="ib-btn ib-link" id="invReset">${esc(T.inv_reset)}</button></div>
      <div class="ib-qr" id="qrBox" hidden></div></div>
    ${f.incoming.length ? `<div class="ib-card"><h2>💌 ${esc(T.req_in)} <b class="ib-badge">${f.incoming.length}</b></h2><ul class="ib-frs">${f.incoming.map(p => row(p, 'in')).join('')}</ul></div>` : ''}
    <div class="ib-card"><h2>💚 ${esc(T.list_h)} <small class="ib-mut">${f.friends.length}</small></h2>${f.friends.length ? `<ul class="ib-frs">${f.friends.map(p => row(p, 'friends')).join('')}</ul>` : `<p class="ib-empty">${esc(T.no_friends)}</p>`}</div>
    ${f.outgoing.length ? `<div class="ib-card"><h2>📤 ${esc(T.req_out)}</h2><ul class="ib-frs">${f.outgoing.map(p => row(p, 'out')).join('')}</ul></div>` : ''}`;
  const nf = $('#nickForm'); if (nf) nf.onsubmit = async e => { e.preventDefault(); try { await api('/api/friends/nick', {nick: $('#nickIn').value}); toast(T.nick_saved); renderFriends(); } catch(er){ toast(er.message); } };
  $('#addForm').onsubmit = async e => { e.preventDefault(); try { const r = await api('/api/friends/request', {nick: $('#addIn').value}); toast(r.status === 'friends' ? '💚' : T.add_sent); renderFriends(); } catch(er){ toast(er.message); } };
  $('#invCopy').onclick = () => { const i = $('#invUrl'); i.select(); (navigator.clipboard ? navigator.clipboard.writeText(i.value) : Promise.reject()).then(() => toast(T.copied)).catch(() => { try { document.execCommand('copy'); toast(T.copied); } catch(e){} }); };
  const sh = $('#invShare'); if (sh) sh.onclick = () => navigator.share({title: 'Luna', text: T.inv_land_p.replace('{nick}', f.me.nick), url: f.invite.url}).catch(() => {});
  $('#invQr').onclick = () => { const q = $('#qrBox'), b = $('#invQr'); q.hidden = !q.hidden; b.setAttribute('aria-expanded', !q.hidden);
    if (!q.hidden && !q.firstChild) q.innerHTML = `<img src="/api/friends/qr.svg?t=${Date.now()}" width="220" height="220" alt="${esc(T.qr_alt)}">`; };
  $('#invReset').onclick = async () => { try { await api('/api/friends/invite/reset', {}); toast(T.inv_reset_ok); renderFriends(); } catch(e){ toast(e.message); } };
  host.querySelectorAll('[data-f]').forEach(b => b.onclick = () => fAct(b.closest('[data-pid]').dataset.pid, b.dataset.f));
}
async function fAct(pid, a){
  if (a === 'chat') return openChat(pid);
  let reason = '';
  if (a === 'remove' && !confirm(T.q_remove)) return;
  if (a === 'block' && !confirm(T.q_block)) return;
  if (a === 'report'){ if (!confirm(T.q_report)) return; reason = prompt(T.reason_ph) || ''; }
  try { await api('/api/friends/act', {pid, action: a, reason});
    toast({report: T.reported, block: T.blocked_ok, remove: T.removed_ok, close: '★ ' + T.close_h, unclose: '☆ ' + T.close_off}[a] || '✓'); refreshUnread();
    if (tab === 'privacy') renderPrivacy(); else renderFriends(); } catch(e){ toast(e.message); }
}

/* ---------- czat ---------- */
async function openChat(pid){
  const box = $('#ibChat'); chat = {pid, last: 0, timer: null, opener: document.activeElement};
  box.hidden = false; document.body.classList.add('ib-chatting');
  box.innerHTML = `<header class="ib-ch"><button type="button" class="ib-back" id="chatBack" aria-label="${esc(T.back)}">‹</button><span id="chatPeer" class="ib-peer"></span></header>
    <p class="ib-note">🔒 ${esc(T.chat_note)}</p><p class="ib-note ib-phq" id="phQuota" hidden></p><ol class="ib-msgs" id="chatLog" role="log" aria-live="polite" aria-relevant="additions"></ol><p class="ib-seen" id="chatSeen" hidden></p>
    <form class="ib-say" id="chatForm"><button type="button" class="ib-phb" id="phBtn" aria-label="${esc(T.ph_btn)}" title="${esc(T.ph_btn)}">📷</button><input type="file" id="phFile" accept="image/jpeg,image/png,image/webp" hidden><label class="sr" for="chatInput">${esc(T.chat_ph)}</label><textarea id="chatInput" data-emoji rows="1" maxlength="1000" placeholder="${esc(T.chat_ph)}" autocomplete="off"></textarea><button class="ib-send" aria-label="${esc(T.send)}">➤</button></form>`;
  $('#chatBack').onclick = closeChat;
  box.onkeydown = e => { if (e.key === 'Escape' && !document.getElementById('emjPanel')?.matches(':not([hidden])')) closeChat(); };
  const inp = $('#chatInput');
  inp.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); $('#chatForm').requestSubmit(); } });
  inp.addEventListener('input', () => { inp.style.height = 'auto'; inp.style.height = Math.min(120, inp.scrollHeight) + 'px'; });
  $('#chatForm').onsubmit = async e => { e.preventDefault(); const t = inp.value.trim(); if (!t) return;
    const btn = e.target.querySelector('button'); btn.disabled = true;
    try { const d = await api('/api/dm', {pid, text: t, since: chat.last}); inp.value = ''; inp.style.height = ''; draw(d); } catch(er){ toast(er.message); }
    btn.disabled = false; inp.focus(); };
  if (window.LunaEmoji && LunaEmoji.attach) try { LunaEmoji.attach(inp); } catch(e){}
  $('#phBtn').onclick = () => $('#phFile').click();
  $('#phFile').onchange = e => { const f = e.target.files[0]; e.target.value = ''; if (f) sendPhoto(f); };
  phQuota();
  location.hash = 'c=' + pid;
  await poll(true); inp.focus();
}
function draw(d){
  if (!chat) return;
  $('#chatPeer').innerHTML = av(d.peer) + `<span class="ib-pn">${nk(d.peer)}${idHtml(d.peer)}${prHtml(d.peer)}</span>`;
  const log = $('#chatLog');
  if (!chat.last && !d.items.length) log.innerHTML = `<li class="ib-empty">${esc(T.chat_empty)}</li>`;
  if (d.items.length){ const e = log.querySelector('.ib-empty'); if (e) e.remove(); }
  d.items.forEach(m => { if (log.querySelector(`[data-mid="${m.id}"]`)) return;
    const li = document.createElement('li'); li.className = 'ib-bub ' + (m.mine ? 'me' : 'them'); li.dataset.mid = m.id;
    if (m.photo){ photoBubble(li, m); log.appendChild(li); return; }
    li.innerHTML = `<span class="ib-tx">${esc(m.text)}</span><time datetime="${new Date(m.t * 1000).toISOString()}">${esc(clock(m.t))}</time>${m.mine ? '' : `<button type="button" class="ib-rep" data-report="dm:${esc(chat.pid)}:${m.id}" aria-label="${esc(T.report_msg)}" title="${esc(T.report_msg)}">⚑</button>`}`;
    const r = li.querySelector('.ib-rep'); if (r) r.onclick = async () => { if (!confirm(T.q_report_msg)) return;
      try { await api('/api/dm/report', {pid: chat.pid, mid: m.id}); li.remove(); toast(T.reported); } catch(e){ toast(e.message); } };
    log.appendChild(li); });
  chat.last = Math.max(chat.last, d.last || 0);
  const mine = [...log.querySelectorAll('.ib-bub.me')].pop(), s = $('#chatSeen');
  s.hidden = !(d.receipts && mine && d.seen >= +mine.dataset.mid); s.textContent = '✓✓ ' + T.seen;
  if (d.items.length) log.scrollTop = log.scrollHeight;
}
/* ---------- zdjęcia w czacie (v1.6.7): rozmyte u odbiorcy do stuknięcia, Zgłoś / Zablokuj, limity planu na serwerze ---------- */
function photoBubble(li, m){
  li.classList.add('ib-phb-msg');
  const t = `<time datetime="${new Date(m.t * 1000).toISOString()}">${esc(clock(m.t))}</time>`;
  if (m.hold){ li.innerHTML = `<span class="ib-tx ib-hold">${esc(m.auto ? T.ph_check : T.ph_hold)}</span>${t}`; return; }
  const src = L('/api/dm/img?pid=' + encodeURIComponent(chat.pid) + '&mid=' + m.id);
  const wh = m.w && m.h ? ` width="${m.w}" height="${m.h}"` : '';
  li.innerHTML = `<figure class="ib-ph${m.mine ? '' : ' blur'}"><img src="${src}" alt="${esc(m.mine ? T.ph_mine : T.ph_alt)}" loading="lazy" decoding="async"${wh}>
    ${m.mine ? '' : `<button type="button" class="ib-phshow"><span>👁️ ${esc(T.ph_show)}</span><small>${esc(T.ph_hint)}</small></button>`}</figure>
    ${m.mine ? '' : `<div class="ib-phact"><button type="button" class="ib-btn" data-a="report" data-report="dm:${esc(chat.pid)}:${m.id}">🚩 ${esc(T.ph_report)}</button><button type="button" class="ib-btn danger" data-a="block">⛔ ${esc(T.ph_block)}</button></div>`}${t}`;
  const sh = li.querySelector('.ib-phshow'); if (sh) sh.onclick = () => { li.querySelector('.ib-ph').classList.remove('blur'); sh.remove(); };
  const rp = li.querySelector('[data-a=report]'); if (rp) rp.onclick = async () => { if (!confirm(T.q_ph_report)) return;
    try { await api('/api/dm/report', {pid: chat.pid, mid: m.id}); li.remove(); toast(T.reported); } catch(e){ toast(e.message); } };
  const bl = li.querySelector('[data-a=block]'); if (bl) bl.onclick = async () => { const p = chat.pid; if (!confirm(T.q_block)) return;
    try { await api('/api/friends/act', {pid: p, action: 'block'}); toast(T.blocked_ok); closeChat(); } catch(e){ toast(e.message); } };
}
async function phQuota(st){
  try { st = st || await api('/api/dm/photo/status'); const q = $('#phQuota'); if (!q) return;
    q.textContent = st.limit == null ? T.ph_unl : T.ph_left.replace('{u}', st.used).replace('{l}', st.limit).replace('{px}', st.px); q.hidden = false; chat && (chat.ack = st.ack); } catch(e){}
}
const readURL = f => new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = no; r.readAsDataURL(f); });
async function sendPhoto(f, ack){
  if (!chat) return;
  if (!/^image\/(jpeg|png|webp)$/.test(f.type)) return toast(T.ph_type);
  if (f.size > 10 * 1024 * 1024) return toast(T.ph_big);
  if (!chat.ack && !ack){ if (!confirm(T.ph_rules)) return; ack = true; }
  const b = $('#phBtn'); b.disabled = true; toast(T.ph_sending);
  try { const d = await api('/api/dm/photo', {pid: chat.pid, image: await readURL(f), since: chat.last, ack: !!ack}); chat.ack = true; draw(d); phQuota(d.photo); if (d.review) toast(d.review); }
  catch(e){ if (e.status === 409 && e.data && e.data.need_ack){ chat.ack = false; b.disabled = false; return sendPhoto(f); }
    toast(e.message); if (e.data && e.data.limit != null) phQuota(e.data); }
  if (b) b.disabled = false;
}
async function poll(first){
  if (!chat) return; clearTimeout(chat.timer);
  if (!document.hidden || first){ try { draw(await api('/api/dm?pid=' + chat.pid + '&since=' + chat.last)); } catch(e){ if (e.status === 403){ toast(e.message); closeChat(); return; } } }
  chat.timer = setTimeout(poll, document.hidden ? 15000 : 3000);
}
function closeChat(){
  if (!chat) return; clearTimeout(chat.timer); const op = chat.opener; chat = null;
  $('#ibChat').hidden = true; $('#ibChat').innerHTML = ''; document.body.classList.remove('ib-chatting');
  history.replaceState(null, '', location.pathname + location.search); refreshUnread(); if (tab === 'friends') renderFriends(); if (op && op.focus) try { op.focus(); } catch(e){}
}
document.addEventListener('visibilitychange', () => { if (!document.hidden && chat) poll(); });

/* ---------- Prywatność ---------- */
async function renderPrivacy(){
  const host = $('#pn-privacy');
  let f; try { f = await loadFriends(); } catch(e){ host.innerHTML = `<p class="ib-empty">${esc(e.message)}</p>`; return; }
  const P = f.prefs;
  const tg = (k, h, s) => `<label class="ib-tg"><span><b>${esc(h)}</b>${s ? `<small>${esc(s)}</small>` : ''}</span><input type="checkbox" role="switch" data-p="${k}" ${P[k] ? 'checked' : ''}><i aria-hidden="true"></i></label>`;
  host.innerHTML = `<div class="ib-card ib-anon"><p>🕶️ ${esc(T.pv_anon)}</p></div>
    <fieldset class="ib-card"><legend>${esc(T.pv_inv)}</legend>
      <label class="ib-rad"><input type="radio" name="inv" value="all" ${P.invites === 'all' ? 'checked' : ''}> ${esc(T.pv_all)}</label>
      <label class="ib-rad"><input type="radio" name="inv" value="none" ${P.invites === 'none' ? 'checked' : ''}> ${esc(T.pv_none)}</label></fieldset>
    <fieldset class="ib-card"><legend>🟢 ${esc(T.pv_online)}</legend>
      ${['all', 'close', 'nobody'].map(v => `<label class="ib-rad"><input type="radio" name="onl" value="${v}" ${P.online === v ? 'checked' : ''}> ${esc(T['pv_on_' + v])}</label>`).join('')}
      <p class="ib-mut">${esc(T.pv_on_s)}</p></fieldset>
    <div class="ib-card">${tg('receipts', T.pv_receipts, T.pv_receipts_s)}${tg('battles', T.pv_battles, T.pv_battles_s)}${tg('security', T.pv_security)}${tg('push', T.pv_push)}</div>
    <div class="ib-card"><h2>🚫 ${esc(T.pv_blocked)}</h2>${f.blocked.length ? `<ul class="ib-frs">${f.blocked.map(p => row(p, 'blocked')).join('')}</ul>` : `<p class="ib-empty">${esc(T.pv_noblocked)}</p>`}</div>
    <div class="ib-card"><h2>📦 ${esc(T.pv_data)}</h2><p class="ib-mut">${esc(T.pv_data_p)}</p><a class="ib-btn" href="/api/account/export" download>${esc(T.pv_export)}</a></div>`;
  const save = async d => { try { await api('/api/friends/prefs', d); toast(T.pv_saved); } catch(e){ toast(e.message); } };
  host.querySelectorAll('[name=inv]').forEach(r => r.onchange = () => save({invites: r.value}));
  host.querySelectorAll('[name=onl]').forEach(r => r.onchange = () => save({online: r.value}));
  host.querySelectorAll('[data-p]').forEach(c => c.onchange = () => save({[c.dataset.p]: c.checked}));
  host.querySelectorAll('[data-f]').forEach(b => b.onclick = () => fAct(b.closest('[data-pid]').dataset.pid, b.dataset.f));
}

/* ---------- zaproszenie z linku / QR ---------- */
async function inviteLanding(tok){
  const c = document.createElement('div'); c.className = 'ib-card ib-invite'; c.setAttribute('role', 'region'); c.setAttribute('aria-label', T.inv_land_h);
  root.prepend(c);
  try { const d = await api('/api/friends/invite?t=' + encodeURIComponent(tok));
    c.innerHTML = `<h2>💌 ${esc(T.inv_land_h)}</h2><div class="ib-me">${av(d.person)}<p>${T.inv_land_p.replace('{nick}', nk(d.person))}</p></div>` +
      (d.self ? `<p class="ib-mut">${esc(T.inv_self)}</p>` : d.status === 'friends' ? `<p class="ib-mut">${esc(T.inv_already)}</p>` : d.status === 'sent' ? `<p class="ib-mut">${esc(T.add_sent)}</p>` :
      `<div class="ib-acts"><button class="ib-btn primary" id="invYes">${esc(d.status === 'incoming' ? T.accept : T.inv_land_b)}</button><button class="ib-btn" id="invNo">${esc(T.cancel)}</button></div>`);
    const y = $('#invYes'); if (y) y.onclick = async () => { try { const r = await api('/api/friends/request', {invite: tok}); toast(r.status === 'friends' ? '💚' : T.add_sent); c.remove(); history.replaceState(null, '', location.pathname); go('friends'); } catch(e){ toast(e.message); } };
    const n = $('#invNo'); if (n) n.onclick = () => { c.remove(); history.replaceState(null, '', location.pathname); };
  } catch(e){ c.innerHTML = `<p>${esc(e.status === 404 ? T.inv_bad : e.message)}</p>`; }
}

async function refreshUnread(){ try { badges(await api('/api/inbox/unread')); } catch(e){} }

/* ---------- start ---------- */
(async () => {
  document.title = T.h1.replace(/^\S+\s/, '') + ' – Luna';
  $('#ibH1').textContent = document.body.dataset.tab === 'friends' ? '💚 ' + T.tab_friends : T.h1; $('#ibLead').textContent = T.lead;
  let me = {}; try { me = await (await fetch('/api/account/me', {credentials: 'same-origin'})).json(); } catch(e){}
  user = me.user; csrf = me.csrf || '';
  if (!user){
    root.innerHTML = `<div class="ib-card ib-login"><div class="ib-moon" aria-hidden="true">🌙</div><h2>${esc(T.login_h)}</h2><p>${esc(T.login_p)}</p><a class="ib-btn primary" href="${esc(L('/app'))}#konto" target="_top">${esc(T.login_b)}</a></div>`;
    return;
  }
  frame();
  const h = location.hash, tok = new URLSearchParams(location.search).get('zapros');
  go(h === '#prywatnosc' ? 'privacy' : h === '#znajomi' || h.startsWith('#c=') ? 'friends' : h === '#skrzynka' ? 'inbox' : tab);
  refreshUnread();
  if (tok) inviteLanding(tok);
  if (h.startsWith('#c=')) openChat(h.slice(3, 15));
  setInterval(() => { if (!document.hidden && !chat) refreshUnread(); }, 60000);
})();
})();
