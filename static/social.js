/* Wspólne komponenty społeczności: 👍/👎, komentarze (moderowane, 1 poziom odpowiedzi, ocena 1–5 dla produktów), Udostępnij, Zgłoś.
   Liczniki pochodzą wyłącznie z serwera – nigdy nie są zasiewane. */
(() => {
const LS = ['pl', 'en', 'es', 'de', 'uk'];
let lang = 'pl'; try { lang = (new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2).toLowerCase(); } catch(e){}
if (!LS.includes(lang)) lang = 'pl';
const T = {
 pl: {cm: 'Komentarze', reply: 'Odpowiedz', write: 'Napisz komentarz…', nick: 'Nick', send: 'Wyślij', share: 'Udostępnij', report: 'Zgłoś', copied: 'Link skopiowany! 📋', copy: 'Kopiuj link',
      pending: 'Dziękujemy! Komentarz pojawi się po sprawdzeniu przez moderatora. 💚', reported: 'Dziękujemy za zgłoszenie – moderator się temu przyjrzy.', reason: 'Co jest nie tak? (opcjonalnie)', none: 'Jeszcze nikt nie skomentował. Napisz pierwszy komentarz!',
      waiting: 'czeka na moderację', rating: 'Ocena (opcjonalnie)', avg: 'Średnia ocen', err: 'Ups, coś poszło nie tak.', more: 'Pokaż komentarze', now: 'przed chwilą', min: 'min temu', h: 'godz. temu', d: 'dni temu'},
 en: {cm: 'Comments', reply: 'Reply', write: 'Write a comment…', nick: 'Nickname', send: 'Send', share: 'Share', report: 'Report', copied: 'Link copied! 📋', copy: 'Copy link',
      pending: 'Thank you! Your comment will appear once a moderator has reviewed it. 💚', reported: 'Thanks for reporting – a moderator will take a look.', reason: 'What’s wrong? (optional)', none: 'No comments yet. Be the first to comment!',
      waiting: 'awaiting moderation', rating: 'Rating (optional)', avg: 'Average rating', err: 'Oops, something went wrong.', more: 'Show comments', now: 'just now', min: 'min ago', h: 'h ago', d: 'days ago'},
 es: {cm: 'Comentarios', reply: 'Responder', write: 'Escribe un comentario…', nick: 'Apodo', send: 'Enviar', share: 'Compartir', report: 'Denunciar', copied: '¡Enlace copiado! 📋', copy: 'Copiar enlace',
      pending: '¡Gracias! Tu comentario aparecerá cuando lo revise un moderador. 💚', reported: 'Gracias por avisar: un moderador lo revisará.', reason: '¿Qué ocurre? (opcional)', none: 'Aún no hay comentarios. ¡Escribe el primero!',
      waiting: 'pendiente de moderación', rating: 'Valoración (opcional)', avg: 'Valoración media', err: 'Vaya, algo ha fallado.', more: 'Ver comentarios', now: 'ahora mismo', min: 'min', h: 'h', d: 'días'},
 de: {cm: 'Kommentare', reply: 'Antworten', write: 'Schreib einen Kommentar…', nick: 'Nickname', send: 'Senden', share: 'Teilen', report: 'Melden', copied: 'Link kopiert! 📋', copy: 'Link kopieren',
      pending: 'Danke! Dein Kommentar erscheint, sobald ein Moderator ihn geprüft hat. 💚', reported: 'Danke für die Meldung – ein Moderator sieht sich das an.', reason: 'Was stimmt nicht? (optional)', none: 'Noch keine Kommentare. Schreib den ersten!',
      waiting: 'wartet auf Freigabe', rating: 'Bewertung (optional)', avg: 'Durchschnittsbewertung', err: 'Hoppla, da ist etwas schiefgelaufen.', more: 'Kommentare anzeigen', now: 'gerade eben', min: 'Min.', h: 'Std.', d: 'Tage'},
 uk: {cm: 'Коментарі', reply: 'Відповісти', write: 'Напишіть коментар…', nick: 'Нік', send: 'Надіслати', share: 'Поділитися', report: 'Поскаржитися', copied: 'Посилання скопійовано! 📋', copy: 'Копіювати посилання',
      pending: 'Дякуємо! Коментар з’явиться після перевірки модератором. 💚', reported: 'Дякуємо за скаргу — модератор перевірить.', reason: 'Що не так? (необов’язково)', none: 'Коментарів ще немає. Напишіть перший!',
      waiting: 'очікує модерації', rating: 'Оцінка (необов’язково)', avg: 'Середня оцінка', err: 'Ой, щось пішло не так.', more: 'Показати коментарі', now: 'щойно', min: 'хв тому', h: 'год тому', d: 'дн. тому'}}[lang];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const t0 = Date.now();
function ago(ts){ const s = Date.now() / 1000 - ts; if (s < 60) return T.now; if (s < 3600) return Math.floor(s / 60) + ' ' + T.min; if (s < 86400) return Math.floor(s / 3600) + ' ' + T.h; if (s < 86400 * 14) return Math.floor(s / 86400) + ' ' + T.d; return new Date(ts * 1000).toLocaleDateString(lang); }
async function api(path, body){
  const r = await fetch(path, body ? {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify(body)} : {credentials: 'same-origin'});
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || T.err); return d;
}
const COLORS = [['#ff9a3c', '#ff5f6d'], ['#2ee66b', '#1a9e8f'], ['#c084fc', '#7c3aed'], ['#ffcf8a', '#e07a1f'], ['#60a5fa', '#2563eb'], ['#f472b6', '#be185d']];
function ava(nick, size){ let h = 0; for (const c of String(nick)) h = (h * 31 + c.charCodeAt(0)) >>> 0; const [a, b] = COLORS[h % COLORS.length];
  return `<span class="ava" aria-hidden="true" style="width:${size}px;height:${size}px;background:linear-gradient(135deg,${a},${b});font-size:${Math.round(size * .42)}px">${esc((String(nick).trim()[0] || '?').toUpperCase())}</span>`; }
function nickGet(){ try { return localStorage.getItem('luna.nick') || ''; } catch(e){ return ''; } }
function nickSet(n){ try { localStorage.setItem('luna.nick', n); } catch(e){} }
/* ---------- głosy ---------- */
function voteButtons(target, v){
  v = v || {up: 0, down: 0, mine: 0};
  return `<button type="button" class="act up${v.mine === 1 ? ' on' : ''}" data-vote="1" data-target="${esc(target)}" aria-pressed="${v.mine === 1}">👍 <em>${v.up}</em></button><button type="button" class="act down${v.mine === -1 ? ' on' : ''}" data-vote="-1" data-target="${esc(target)}" aria-pressed="${v.mine === -1}">👎 <em>${v.down}</em></button>`;
}
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-vote]'); if (!b) return;
  const target = b.dataset.target, v = Number(b.dataset.vote);
  try { const d = await api('/api/vote', {target, v});
    document.querySelectorAll(`[data-target="${CSS.escape(target)}"][data-vote]`).forEach(x => { const up = x.dataset.vote === '1'; x.querySelector('em').textContent = up ? d.up : d.down; const on = d.mine === Number(x.dataset.vote); x.classList.toggle('on', on); x.setAttribute('aria-pressed', on); });
    if (target.startsWith('post:')) document.querySelectorAll(`[data-cnt-like="${CSS.escape(target.slice(5))}"] b`).forEach(x => x.textContent = Number(d.up).toLocaleString(lang === 'uk' ? 'uk-UA' : lang));
  } catch(err){ alert(err.message); }
});
/* ---------- zgłoś ---------- */
async function report(target){ const reason = prompt(T.reason); if (reason === null) return; try { await api('/api/report', {target, reason}); alert(T.reported); } catch(e){ alert(e.message); } }
document.addEventListener('click', e => { const b = e.target.closest('[data-report]'); if (b) report(b.dataset.report); });
/* ---------- udostępnij ---------- */
function utm(url, src, camp){ try { const x = new URL(url, location.origin); x.searchParams.set('utm_source', src); x.searchParams.set('utm_medium', 'share'); x.searchParams.set('utm_campaign', camp || (/butik/.test(x.pathname) ? 'butik' : 'wall'));
  const h = x.hash; x.hash = ''; return x.toString() + h; } catch(e){ return url; } }
function shareBox(url0, text){
  const U = n => encodeURIComponent(utm(url0, n)), url = utm(url0, 'copy'), tx = encodeURIComponent(text || 'Luna mówi jak jest');
  return `<div class="sharebox"><a data-net="facebook" href="https://www.facebook.com/sharer/sharer.php?u=${U('facebook')}" target="_blank" rel="noopener">Facebook</a><a data-net="x" href="https://twitter.com/intent/tweet?url=${U('x')}&text=${tx}" target="_blank" rel="noopener">X</a><a data-net="whatsapp" href="https://wa.me/?text=${tx}%20${U('whatsapp')}" target="_blank" rel="noopener">WhatsApp</a><a data-net="messenger" href="fb-messenger://share/?link=${U('messenger')}" rel="noopener">Messenger</a><a data-net="telegram" href="https://t.me/share/url?url=${U('telegram')}&text=${tx}" target="_blank" rel="noopener">Telegram</a><button type="button" data-net="copy" data-copy="${esc(url)}">📋 ${T.copy}</button></div>`;
}
document.addEventListener('click', async e => {
  const c = e.target.closest('[data-copy]'); if (c){ try { await navigator.clipboard.writeText(c.dataset.copy); c.textContent = T.copied; } catch(x){ prompt(T.copy, c.dataset.copy); } return; }
  const s = e.target.closest('[data-share]'); if (!s) return;
  const url = s.dataset.share, text = s.dataset.text || '';
  if (navigator.share && matchMedia('(pointer:coarse)').matches){ try { await navigator.share({url: utm(url, 'native'), text}); track('sharenet', 'utm:native'); return; } catch(x){ if (x && x.name === 'AbortError') return; } }
  const host = s.closest('article, .cmtbox, .item, section') || s.parentElement; const old = host.querySelector(':scope > .sharebox');
  if (old) old.remove(); else s.closest('.acts').insertAdjacentHTML('afterend', shareBox(url, text));
});
/* ---------- komentarze: mały czat pod wpisem (najnowsze na dole, moderacja przed publikacją) ---------- */
const X2 = {pl: {more: 'Pokaż wcześniejsze komentarze', ph: 'Napisz komentarz…', del: 'Usunięty użytkownik', you: 'Ty'}, en: {more: 'Show earlier comments', ph: 'Write a comment…', del: 'Deleted user', you: 'You'},
 es: {more: 'Ver comentarios anteriores', ph: 'Escribe un comentario…', del: 'Usuario eliminado', you: 'Tú'}, de: {more: 'Frühere Kommentare anzeigen', ph: 'Schreib einen Kommentar…', del: 'Gelöschter Nutzer', you: 'Du'},
 uk: {more: 'Показати попередні коментарі', ph: 'Напишіть коментар…', del: 'Видалений користувач', you: 'Ви'}}[lang];
const nickShow = n => n === 'Usunięty użytkownik' ? X2.del : n;
function clock(ts){ const d = new Date(ts * 1000), now = new Date(); const hm = d.toLocaleTimeString(lang === 'uk' ? 'uk-UA' : lang, {hour: '2-digit', minute: '2-digit'});
  return d.toDateString() === now.toDateString() ? hm : d.toLocaleDateString(lang === 'uk' ? 'uk-UA' : lang, {day: 'numeric', month: 'short'}) + ' · ' + hm; }
function cmtHTML(c, target, replies){
  const stars = c.rating ? ' ' + '★'.repeat(c.rating) + '☆'.repeat(5 - c.rating) : ''; const nk = nickShow(c.nick);
  return `<div class="cmt chat${c.mine ? ' mine' : ''}${c.pending ? ' pend' : ''}" data-cid="${esc(c.id)}">${ava(nk, 34)}<div class="cbody"><div class="bubble"><b class="nick nk${c.tier ? ' nk-' + c.tier : ''}">${esc(nk)}</b>${c.pending ? ` <span class="pend">⏳ ${T.waiting}</span>` : ''}<span class="stars" aria-label="${c.rating || ''}/5">${stars}</span><p>${esc(c.text)}</p></div>
  <div class="cmeta"><time datetime="${new Date(c.t * 1000).toISOString()}" title="${esc(new Date(c.t * 1000).toLocaleString(lang))}">${clock(c.t)}</time>${c.pending ? '' : `<button type="button" data-vote="1" data-target="cmt:${esc(c.id)}" class="${c.votes.mine === 1 ? 'on' : ''}" aria-label="👍">👍 <em>${c.votes.up}</em></button><button type="button" data-vote="-1" data-target="cmt:${esc(c.id)}" class="${c.votes.mine === -1 ? 'on' : ''}" aria-label="👎">👎 <em>${c.votes.down}</em></button><button type="button" data-replyto="${esc(c.id)}">${T.reply}</button><button type="button" data-report="cmt:${esc(c.id)}">${T.report}</button>`}</div>
  ${replies && replies.length ? `<div class="replies">${replies.map(r => `<div class="reply">${cmtHTML(r, target, null)}</div>`).join('')}</div>` : ''}</div></div>`;
}
const SHOW = 3;
async function comments(el, target, opts){
  opts = opts || {};
  el.classList.add('cmtbox', 'chatbox');
  if (!el.innerHTML) el.innerHTML = '<p class="cmsg">…</p>';
  let d; try { d = await api('/api/comments?target=' + encodeURIComponent(target)); } catch(e){ el.innerHTML = `<p class="cmsg err">${esc(e.message)}</p>`; return; }
  const top = d.items.filter(c => !c.parent), rep = id => d.items.filter(c => c.parent === id);
  const avg = d.rating ? `<p class="cmsg">${T.avg}: <b>${String(d.rating).replace('.', lang === 'en' ? '.' : ',')}</b> / 5 (${d.nratings})</p>` : '';
  const hiddenN = el.dataset.all ? 0 : Math.max(0, top.length - SHOW);
  const shown = top.slice(hiddenN);
  el.innerHTML = avg + (hiddenN ? `<button type="button" class="cmore" data-cmore>💬 ${X2.more} (${hiddenN})</button>` : '') +
    `<div class="clist">${shown.length ? shown.map(c => cmtHTML(c, target, rep(c.id))).join('') : `<p class="cmsg">${T.none}</p>`}</div>` + formHTML(opts.rating, null);
  const mc = el.querySelector('[data-cmore]'); if (mc) mc.onclick = () => { el.dataset.all = 1; comments(el, target, opts); };
  bindForm(el.querySelector('.cform'), el, target, null, opts);
  el.querySelectorAll('[data-replyto]').forEach(b => b.onclick = () => {
    const box = b.closest('.cbody'); if (box.querySelector('.cform')) return;
    box.insertAdjacentHTML('beforeend', formHTML(false, b.dataset.replyto)); bindForm(box.querySelector('.cform'), el, target, b.dataset.replyto, opts); box.querySelector('.cform input[name=text]').focus(); });
  if (opts.onCount) opts.onCount(d.items.filter(c => !c.pending).length);
}
function formHTML(rating, parent){
  const nk = nickGet();
  return `<form class="cform chatform" novalidate>${ava(nk || '✦', 30)}<input class="cn" name="nick" maxlength="30" placeholder="${T.nick}" aria-label="${T.nick}" value="${esc(nk)}" required${nk ? ' hidden' : ''}>
  <input name="text" maxlength="1000" placeholder="${parent ? T.reply + '…' : X2.ph}" aria-label="${X2.ph}" required enterkeyhint="send">${rating ? `<select name="rating" aria-label="${T.rating}"><option value="">${T.rating}</option>${[5, 4, 3, 2, 1].map(n => `<option value="${n}">${'★'.repeat(n)}</option>`).join('')}</select>` : ''}
  <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><button type="submit" class="csend" aria-label="${T.send}" title="${T.send}">➤</button><p class="cmsg" role="status" style="flex-basis:100%;margin:0"></p></form>`;
}
function bindForm(f, el, target, parent, opts){
  const nickIn = f.querySelector('input[name=nick]'), txt = f.querySelector('input[name=text]');
  txt.addEventListener('focus', () => { if (!nickIn.value) nickIn.hidden = false; });
  f.onsubmit = async e => { e.preventDefault(); const fd = new FormData(f), msg = f.querySelector('.cmsg');
    if (!fd.get('nick')){ nickIn.hidden = false; nickIn.focus(); return; }
    if (Date.now() - t0 < 2500){ msg.textContent = '…'; return; }
    try { nickSet(fd.get('nick')); await api('/api/comments', {target, parent, nick: fd.get('nick'), text: fd.get('text'), rating: fd.get('rating') || null, website: fd.get('website')});
      msg.className = 'cmsg ok'; msg.textContent = T.pending; txt.value = ''; setTimeout(() => comments(el, target, opts), 1200);
    } catch(err){ msg.className = 'cmsg err'; msg.textContent = err.message; } };
}
/* ---------- liczniki pod wpisem i anonimowe statystyki ---------- */
const NUM = n => Number(n || 0).toLocaleString(lang === 'uk' ? 'uk-UA' : lang);
const CL = {pl: ['polubień', 'wyświetleń', 'komentarzy'], en: ['likes', 'views', 'comments'], es: ['me gusta', 'vistas', 'comentarios'], de: ['Likes', 'Aufrufe', 'Kommentare'], uk: ['вподобань', 'переглядів', 'коментарів']}[lang];
function counterRow(p){
  const up = (p.votes || {}).up || 0;
  return `<div class="counters" aria-label="${NUM(up)} ${CL[0]} · ${NUM(p.views)} ${CL[1]} · ${NUM(p.ncomments)} ${CL[2]}"><span data-cnt-like="${esc(p.id)}">👍 <b>${NUM(up)}</b> ${CL[0]}</span><span>👁 <b>${NUM(p.views)}</b> ${CL[1]}</span><span data-cnt-cm="${esc(p.id)}">💬 <b>${NUM(p.ncomments)}</b> ${CL[2]}</span></div>`;
}
let SID = ''; try { SID = sessionStorage.getItem('luna.vsid') || ''; if (!SID){ SID = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join(''); sessionStorage.setItem('luna.vsid', SID); } } catch(e){}
const Q = {view: new Set()}; let qT = null; const sent = new Set();
function track(ev, key){
  if (!SID || navigator.webdriver) return;
  const k = ev + '|' + key; if (sent.has(k)) return; sent.add(k);
  if (ev !== 'view'){ navigator.sendBeacon ? navigator.sendBeacon('/api/track', new Blob([JSON.stringify({sid: SID, ev, keys: [key], lang})], {type: 'application/json'})) : api('/api/track', {sid: SID, ev, keys: [key], lang}).catch(() => {}); return; }
  Q.view.add(key); clearTimeout(qT); qT = setTimeout(() => { const keys = [...Q.view]; Q.view.clear(); if (keys.length) api('/api/track', {sid: SID, ev: 'view', keys, lang}).catch(() => {}); }, 1500);
}
const timers = new WeakMap();
const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => {
  const el = e.target;
  if (e.isIntersecting && e.intersectionRatio >= .5){ if (!timers.has(el)) timers.set(el, setTimeout(() => { track('view', el.dataset.track); io.unobserve(el); }, 1000)); }
  else { clearTimeout(timers.get(el)); timers.delete(el); }
}), {threshold: [0, .5, 1]}) : null;
function observe(root){ if (!io) return; (root || document).querySelectorAll('[data-track]:not([data-tracked])').forEach(el => { el.dataset.tracked = 1; io.observe(el); }); }
document.addEventListener('click', e => {
  const a = e.target.closest('a[href]'); const host = e.target.closest('[data-track]');
  if (a && host && /^post:/.test(host.dataset.track) && !a.closest('.acts')) track('click', host.dataset.track);
  const sh = e.target.closest('[data-share]'); if (sh && host) track('share', host.dataset.track);
  const nt = e.target.closest('.sharebox [data-net]'); if (nt) track('sharenet', 'utm:' + nt.dataset.net);
}, true);
async function votesFor(targets){ if (!targets.length) return {}; try { return await api('/api/votes?t=' + targets.map(encodeURIComponent).join(',')); } catch(e){ return {}; } }
try { const q = new URLSearchParams(location.search), src = (q.get('utm_source') || '').toLowerCase().replace(/[^a-z0-9_-]/g, '').slice(0, 30); if (src) setTimeout(() => track('arrive', 'utm:' + src), 800); } catch(e){}
window.LunaSocial = {utm, T, lang, esc, ago, api, ava, voteButtons, comments, shareBox, report, votesFor, nickGet, nickSet, counterRow, track, observe, nickShow, NUM};
/* auto: [data-comments="target"] i [data-votes="target"] */
function auto(){
  document.querySelectorAll('[data-comments]').forEach(el => { if (!el.dataset.ready){ el.dataset.ready = 1; comments(el, el.dataset.comments, {rating: el.dataset.rating === '1'}); } });
  const vs = [...document.querySelectorAll('[data-votes]')].filter(el => !el.dataset.ready);
  votesFor(vs.map(el => el.dataset.votes)).then(m => vs.forEach(el => { el.dataset.ready = 1; el.innerHTML = voteButtons(el.dataset.votes, m[el.dataset.votes]); }));
}
window.LunaSocial.auto = auto;
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();
})();
