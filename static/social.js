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
  } catch(err){ alert(err.message); }
});
/* ---------- zgłoś ---------- */
async function report(target){ const reason = prompt(T.reason); if (reason === null) return; try { await api('/api/report', {target, reason}); alert(T.reported); } catch(e){ alert(e.message); } }
document.addEventListener('click', e => { const b = e.target.closest('[data-report]'); if (b) report(b.dataset.report); });
/* ---------- udostępnij ---------- */
function shareBox(url, text){
  const u = encodeURIComponent(url), tx = encodeURIComponent(text || 'Luna mówi jak jest');
  return `<div class="sharebox"><a href="https://www.facebook.com/sharer/sharer.php?u=${u}" target="_blank" rel="noopener">Facebook</a><a href="https://twitter.com/intent/tweet?url=${u}&text=${tx}" target="_blank" rel="noopener">X</a><a href="https://wa.me/?text=${tx}%20${u}" target="_blank" rel="noopener">WhatsApp</a><a href="fb-messenger://share/?link=${u}" rel="noopener">Messenger</a><a href="https://t.me/share/url?url=${u}&text=${tx}" target="_blank" rel="noopener">Telegram</a><button type="button" data-copy="${esc(url)}">📋 ${T.copy}</button></div>`;
}
document.addEventListener('click', async e => {
  const c = e.target.closest('[data-copy]'); if (c){ try { await navigator.clipboard.writeText(c.dataset.copy); c.textContent = T.copied; } catch(x){ prompt(T.copy, c.dataset.copy); } return; }
  const s = e.target.closest('[data-share]'); if (!s) return;
  const url = s.dataset.share, text = s.dataset.text || '';
  if (navigator.share && matchMedia('(pointer:coarse)').matches){ try { await navigator.share({url, text}); return; } catch(x){ if (x && x.name === 'AbortError') return; } }
  const host = s.closest('article, .cmtbox, .item, section') || s.parentElement; const old = host.querySelector(':scope > .sharebox');
  if (old) old.remove(); else s.closest('.acts').insertAdjacentHTML('afterend', shareBox(url, text));
});
/* ---------- komentarze ---------- */
function cmtHTML(c, target, replies){
  const stars = c.rating ? ' ' + '★'.repeat(c.rating) + '☆'.repeat(5 - c.rating) : '';
  return `<div class="cmt" data-cid="${esc(c.id)}">${ava(c.nick, 36)}<div class="cbody"><div class="bubble"><b class="nick">${esc(c.nick)}</b>${c.pending ? `<span class="pend">${T.waiting}</span>` : ''}<span class="stars" aria-label="${c.rating || ''}/5">${stars}</span><p>${esc(c.text)}</p></div>
  <div class="cmeta"><span>${ago(c.t)}</span>${c.pending ? '' : `<button type="button" data-vote="1" data-target="cmt:${esc(c.id)}" class="${c.votes.mine === 1 ? 'on' : ''}">👍 <em>${c.votes.up}</em></button><button type="button" data-vote="-1" data-target="cmt:${esc(c.id)}" class="${c.votes.mine === -1 ? 'on' : ''}">👎 <em>${c.votes.down}</em></button>`}${replies ? `<button type="button" data-replyto="${esc(c.id)}">${T.reply}</button>` : ''}${c.pending ? '' : `<button type="button" data-report="cmt:${esc(c.id)}">${T.report}</button>`}</div>
  ${replies ? `<div class="replies">${replies.map(r => `<div class="reply">${cmtHTML(r, target, null)}</div>`).join('')}</div>` : ''}</div></div>`;
}
async function comments(el, target, opts){
  opts = opts || {};
  el.classList.add('cmtbox');
  el.innerHTML = '<p class="cmsg">…</p>';
  let d; try { d = await api('/api/comments?target=' + encodeURIComponent(target)); } catch(e){ el.innerHTML = `<p class="cmsg err">${esc(e.message)}</p>`; return; }
  const top = d.items.filter(c => !c.parent), rep = id => d.items.filter(c => c.parent === id);
  const avg = d.rating ? `<p class="cmsg">${T.avg}: <b>${String(d.rating).replace('.', lang === 'en' ? '.' : ',')}</b> / 5 (${d.nratings})</p>` : '';
  el.innerHTML = avg + (top.length ? top.map(c => cmtHTML(c, target, rep(c.id))).join('') : `<p class="cmsg">${T.none}</p>`) + formHTML(opts.rating, null);
  bindForm(el.querySelector('.cform'), el, target, null, opts);
  el.querySelectorAll('[data-replyto]').forEach(b => b.onclick = () => {
    const box = b.closest('.cbody'); if (box.querySelector('.cform')) return;
    box.insertAdjacentHTML('beforeend', formHTML(false, b.dataset.replyto)); bindForm(box.querySelector('.cform'), el, target, b.dataset.replyto, opts); box.querySelector('.cform input[name=text]').focus(); });
  if (opts.onCount) opts.onCount(d.items.filter(c => !c.pending).length);
}
function formHTML(rating, parent){
  return `<form class="cform" novalidate>${parent ? '' : ''}<input class="cn" name="nick" maxlength="30" placeholder="${T.nick}" aria-label="${T.nick}" value="${esc(nickGet())}" required>
  <input name="text" maxlength="1000" placeholder="${T.write}" aria-label="${T.write}" required>${rating ? `<select name="rating" aria-label="${T.rating}"><option value="">${T.rating}</option>${[5, 4, 3, 2, 1].map(n => `<option value="${n}">${'★'.repeat(n)}</option>`).join('')}</select>` : ''}
  <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><button type="submit">${T.send}</button><p class="cmsg" role="status" style="flex-basis:100%;margin:0"></p></form>`;
}
function bindForm(f, el, target, parent, opts){
  f.onsubmit = async e => { e.preventDefault(); const fd = new FormData(f), msg = f.querySelector('.cmsg');
    if (Date.now() - t0 < 2500){ msg.textContent = '…'; return; }
    try { nickSet(fd.get('nick')); await api('/api/comments', {target, parent, nick: fd.get('nick'), text: fd.get('text'), rating: fd.get('rating') || null, website: fd.get('website')});
      msg.className = 'cmsg ok'; msg.textContent = T.pending; f.querySelector('input[name=text]').value = ''; setTimeout(() => comments(el, target, opts), 1800);
    } catch(err){ msg.className = 'cmsg err'; msg.textContent = err.message; } };
}
async function votesFor(targets){ if (!targets.length) return {}; try { return await api('/api/votes?t=' + targets.map(encodeURIComponent).join(',')); } catch(e){ return {}; } }
window.LunaSocial = {T, lang, esc, ago, api, ava, voteButtons, comments, shareBox, report, votesFor, nickGet, nickSet};
/* auto: [data-comments="target"] i [data-votes="target"] */
function auto(){
  document.querySelectorAll('[data-comments]').forEach(el => { if (!el.dataset.ready){ el.dataset.ready = 1; comments(el, el.dataset.comments, {rating: el.dataset.rating === '1'}); } });
  const vs = [...document.querySelectorAll('[data-votes]')].filter(el => !el.dataset.ready);
  votesFor(vs.map(el => el.dataset.votes)).then(m => vs.forEach(el => { el.dataset.ready = 1; el.innerHTML = voteButtons(el.dataset.votes, m[el.dataset.votes]); }));
}
window.LunaSocial.auto = auto;
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();
})();
