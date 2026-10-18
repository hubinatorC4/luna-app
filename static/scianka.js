/* Ścianka Agentek Głosu – kanał wpisów (Nowe / Popularne), kompozytor, nieskończone przewijanie. Tylko prawdziwe dane z serwera. */
(() => {
const S = window.LunaSocial; const {T, esc, ago, api, ava} = S;
const D = JSON.parse((document.getElementById('wall-i18n') || document.getElementById('i18n')).textContent); const W = Object.assign({}, D.pl, D[S.lang] || {});
const X = {pl: {other: 'Zobacz w innym języku:', newp: 'Nowe posty', top: 'Do góry', write: 'Napisz wpis', edit: 'Edytuj', del: 'Usuń', delq: 'Usunąć ten wpis?', save: 'Zapisz', pend: 'Dziękujemy! Wpis pojawi się po sprawdzeniu przez moderatora. 💚', ok: 'Opublikowano! 🎉', edited: 'edytowano', waiting: 'czeka na moderację', big: 'Obraz jest za duży (maks. 5 MB).', short: 'Napisz coś. 🙂'},
 en: {other: 'See in another language:', newp: 'New posts', top: 'Back to top', write: 'Write a post', edit: 'Edit', del: 'Delete', delq: 'Delete this post?', save: 'Save', pend: 'Thank you! Your post will appear once a moderator has reviewed it. 💚', ok: 'Posted! 🎉', edited: 'edited', waiting: 'awaiting moderation', big: 'The image is too large (max 5 MB).', short: 'Write something. 🙂'},
 es: {other: 'Ver en otro idioma:', newp: 'Nuevas publicaciones', top: 'Arriba', write: 'Escribir', edit: 'Editar', del: 'Eliminar', delq: '¿Eliminar esta publicación?', save: 'Guardar', pend: '¡Gracias! Tu publicación aparecerá cuando la revise un moderador. 💚', ok: '¡Publicado! 🎉', edited: 'editado', waiting: 'pendiente de moderación', big: 'La imagen es demasiado grande (máx. 5 MB).', short: 'Escribe algo. 🙂'},
 de: {other: 'In einer anderen Sprache ansehen:', newp: 'Neue Beiträge', top: 'Nach oben', write: 'Beitrag schreiben', edit: 'Bearbeiten', del: 'Löschen', delq: 'Diesen Beitrag löschen?', save: 'Speichern', pend: 'Danke! Dein Beitrag erscheint, sobald ein Moderator ihn geprüft hat. 💚', ok: 'Veröffentlicht! 🎉', edited: 'bearbeitet', waiting: 'wartet auf Freigabe', big: 'Das Bild ist zu groß (max. 5 MB).', short: 'Schreib etwas. 🙂'},
 uk: {other: 'Переглянути іншою мовою:', newp: 'Нові дописи', top: 'Угору', write: 'Написати допис', edit: 'Редагувати', del: 'Видалити', delq: 'Видалити цей допис?', save: 'Зберегти', pend: 'Дякуємо! Допис з’явиться після перевірки модератором. 💚', ok: 'Опубліковано! 🎉', edited: 'відредаговано', waiting: 'очікує модерації', big: 'Зображення завелике (макс. 5 МБ).', short: 'Напишіть щось. 🙂'}}[S.lang];
const $ = s => document.querySelector(s);
document.querySelectorAll('[data-wi18n]').forEach(e => { if (W[e.dataset.wi18n] != null) e.innerHTML = W[e.dataset.wi18n]; });
document.querySelectorAll('[data-wi18n-ph]').forEach(e => { if (W[e.dataset.wi18nPh] != null){ e.placeholder = W[e.dataset.wi18nPh]; e.setAttribute('aria-label', W[e.dataset.wi18nPh]); } });
const MORE = {pl: ['Pokaż więcej', 'Zwiń'], en: ['See more', 'See less'], es: ['Ver más', 'Ver menos'], de: ['Mehr anzeigen', 'Weniger anzeigen'], uk: ['Показати більше', 'Згорнути']}[S.lang] || ['Pokaż więcej', 'Zwiń'];
function clampAll(root){ root.querySelectorAll('.ptext:not([data-cl]), .rbody:not([data-cl])').forEach(el => { el.dataset.cl = 1;
  if (el.scrollHeight > (el.classList.contains('rbody') ? 560 : 300)){ el.classList.add('clamp'); const b = document.createElement('button'); b.type = 'button'; b.className = 'seemore'; b.textContent = MORE[0]; b.setAttribute('aria-expanded', 'false');
    b.onclick = () => { const open = el.classList.toggle('open'); b.textContent = MORE[open ? 1 : 0]; b.setAttribute('aria-expanded', open); if (!open) el.closest('article').scrollIntoView({block: 'nearest'}); }; el.after(b); } }); }
window.LunaClamp = clampAll;
const cmio = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; const box = e.target; cmio.unobserve(box); openCm(box.closest('article')); }), {rootMargin: '300px'}) : null;
function openCm(art){ if (!art) return; const box = art.querySelector('.comments'); if (!box || box.dataset.ready) return; const b = art.querySelector('[data-cm]'); box.hidden = false; box.dataset.ready = 1; if (b) b.setAttribute('aria-expanded', 'true');
  S.comments(box, 'post:' + art.dataset.id, {onCount: n => { if (b) b.querySelector('em').textContent = n; const c = art.querySelector('[data-cnt-cm] b'); if (c) c.textContent = S.NUM(n); }}); }
let sort = 'hot', next = null, loading = false, done = false, img = null, ME = null; const t0 = Date.now();
let feed = $('#feed'); const host = document.getElementById('feedHost');
function chunk(){ if (!host || !feed.querySelector('article')) return; const c = document.createElement('div'); c.className = 'wallpage chunk'; host.appendChild(c); feed = c; }
const posts = () => (host || feed).querySelectorAll('article.post');
const VAR = {};
const fmt = t => esc(t).split(/\n{2,}/).map(x => `<p>${x.replace(/\n/g, '<br>')}</p>`).join('');
const RICH = {};
function postHTML(p){
  if (p.rich) RICH[p.id] = p;
  const url = location.origin + '/scianka.html?post=' + p.id + (S.lang !== 'pl' ? '&lang=' + S.lang : '');
  const text = fmt(p.text); if (p.variants) VAR[p.id] = p.variants;
  const lsw = p.variants ? `<div class="langsw">🌐 <span>${X.other}</span> ${Object.keys(p.variants).map(l => `<button type="button" data-vl="${l}" class="${l === p.lang ? 'on' : ''}">${l.toUpperCase()}</button>`).join('')}</div>` : '';
  return `<article class="post card${p.pinned ? ' pinned' : ''}" id="p-${esc(p.id)}" data-id="${esc(p.id)}"${p.pending ? '' : ` data-track="post:${esc(p.id)}"`}>${p.pinned ? '<span class="pinb">📌</span>' : ''}
<header class="phead">${p.avatar ? `<span class="offava"><img src="${esc(p.avatar)}" alt="" width="44" height="44"></span>` : ava(p.nick, 48)}<div class="pmeta"><div><b class="nick nk${p.tier ? ' nk-' + p.tier : ''}">${esc(p.nick)}</b>${p.official ? (p.verified_label ? ` <span class="badge-ver" title="${esc(p.verified_label)}" aria-label="${esc(p.verified_label)}">✓</span>` : ' <span class="verified">✓ Oficjalne</span>') : ''}${p.pending ? `<span class="pend">${X.waiting}</span>` : ''}</div><time datetime="${new Date(p.t * 1000).toISOString()}">${ago(p.t)}${p.edited ? ' · ' + X.edited : ''}</time></div>
${p.mine ? `<div class="menu"><button type="button" data-edit>${X.edit}</button><button type="button" data-del>${X.del}</button></div>` : ''}${p.pending ? '' : `<button type="button" class="report" data-report="post:${esc(p.id)}">⋯ ${T.report}</button>`}</header>
${p.rich ? lsw : ''}${p.rich ? `<div class="rbody" lang="${esc(p.lang)}">${window.LunaOfficial.render(p, p.lang)}</div>` : `<div class="ptext" lang="${esc(p.lang)}">${text}</div>${lsw}`}
${p.img && !p.rich ? `<figure class="media"><img src="${esc(p.img)}" alt="" loading="lazy"><span class="ai-badge">✦ AI</span></figure>` : ''}
${p.pending ? '' : S.counterRow(p)}${p.pending ? '' : `<div class="acts">${S.voteButtons('post:' + p.id, p.votes)}<button type="button" class="act" data-cm aria-expanded="false">💬 ${T.cm} <em>${p.ncomments}</em></button><button type="button" class="act share" data-share="${esc(url)}" data-text="${esc(p.text.slice(0, 90))}">↗ ${T.share}</button></div>
<div class="comments"></div>`}</article>`;
}
const SK = '<div class="post card skel" aria-hidden="true"><div class="phead"><span class="sk sk-ava"></span><div class="pmeta"><span class="sk sk-l"></span><span class="sk sk-s"></span></div></div><span class="sk sk-t"></span><span class="sk sk-t"></span><span class="sk sk-t short"></span></div>';
let newest = 0;
async function load(reset, want){
  if (loading || (done && !reset)) return; loading = true;
  if (reset && host){ host.querySelectorAll('.chunk').forEach((c, i) => { if (i) c.remove(); }); feed = host.querySelector('.chunk'); }
  if (!reset) chunk();
  if (reset){ next = null; done = false; feed.innerHTML = ''; $('#endnote').hidden = true; $('#empty').hidden = true; hidePill(); }
  feed.insertAdjacentHTML('beforeend', '<div class="skels">' + SK + SK + '</div>');
  try {
    const d = await api('/api/wall?lang=' + S.lang + '&sort=' + sort + '&limit=' + (want || 10) + (next != null ? '&before=' + next : ''));
    feed.querySelectorAll('.skels').forEach(x => x.remove());
    if (reset && d.items.length) newest = Math.max(newest, ...d.items.map(p => p.t || 0));
    const before = feed.children.length;
    feed.insertAdjacentHTML('beforeend', d.items.map(postHTML).join(''));
    next = d.next; done = d.next == null;
    [...feed.children].slice(before).forEach(a => { clampAll(a); const c = a.querySelector('.comments'); if (c && cmio) cmio.observe(c); });
    S.observe(feed);
    const det = {done, n: d.items.length, feed}; (window.LunaFeedBatches = window.LunaFeedBatches || []).push(det); window.dispatchEvent(new CustomEvent('luna-feed-batch', {detail: det}));
    if (!posts().length) $('#empty').hidden = false; else if (done) $('#endnote').hidden = false;
    const pid = new URLSearchParams(location.search).get('post');
    if (reset && pid){ const el = document.getElementById('p-' + pid); if (el){ el.scrollIntoView({block: 'start'}); el.style.boxShadow = '0 0 0 2px var(--acc2), var(--shadow)'; } }
  } catch(e){ feed.querySelectorAll('.skels').forEach(x => x.remove()); feed.insertAdjacentHTML('beforeend', `<p class="endnote">${esc(e.message)}</p>`); done = true; }
  loading = false;
}
new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) load(false); }, {rootMargin: '600px'}).observe($('#sentinel'));
document.querySelectorAll('.tabs [data-sort]').forEach(b => b.onclick = () => { document.querySelectorAll('.tabs [data-sort]').forEach(x => x.classList.toggle('on', x === b)); sort = b.dataset.sort; load(true); });
(host || feed).addEventListener('click', async e => {
  const art = e.target.closest('article'); if (!art) return; const id = art.dataset.id;
  const vl = e.target.closest('[data-vl]');
  if (vl && RICH[id]){ const rb = art.querySelector('.rbody'); rb.lang = vl.dataset.vl; rb.innerHTML = window.LunaOfficial.render(RICH[id], vl.dataset.vl); art.querySelectorAll('[data-vl]').forEach(b => b.classList.toggle('on', b === vl)); return; }
  if (vl){ const v = (VAR[id] || {})[vl.dataset.vl]; if (v != null){ const pt = art.querySelector('.ptext'); pt.lang = vl.dataset.vl; pt.innerHTML = fmt(v); art.querySelectorAll('[data-vl]').forEach(b => b.classList.toggle('on', b === vl)); } return; }
  if (e.target.closest('[data-cm]')){ const box = art.querySelector('.comments'); if (!box.dataset.ready) openCm(art); const inp = box.querySelector('input[name=text]'); if (inp) inp.focus(); else setTimeout(() => { const i = box.querySelector('input[name=text]'); if (i) i.focus(); }, 600); }
  if (e.target.closest('[data-del]')){ if (!confirm(X.delq)) return; try { await api('/api/wall/delete', {id}); art.remove(); } catch(err){ alert(err.message); } }
  if (e.target.closest('[data-edit]')){ const pt = art.querySelector('.ptext'); if (pt.querySelector('textarea')) return;
    const cur = [...pt.querySelectorAll('p')].map(p => p.innerText).join('\n\n');
    pt.innerHTML = `<textarea class="cfield" maxlength="2000" rows="4"></textarea><div class="crow"><button type="button" class="primary" data-save>${X.save}</button></div>`; pt.querySelector('textarea').value = cur; }
  if (e.target.closest('[data-save]')){ const v = art.querySelector('.ptext textarea').value;
    try { const d = await api('/api/wall/edit', {id, text: v}); if (d.pending) alert(X.pend); load(true); } catch(err){ alert(err.message); } }
});
/* kompozytor */
const f = $('#composer'), msg = $('#cMsg');
f.text.addEventListener('focus', () => { $('#cExtra').hidden = false; });
f.nick.value = S.nickGet();
$('#imgBtn').onclick = () => $('#imgFile').click();
$('#imgFile').onchange = () => { const file = $('#imgFile').files[0]; if (!file) return; if (file.size > 5 * 1024 * 1024){ alert(X.big); return; }
  const r = new FileReader(); r.onload = () => { img = r.result; $('#cExtra').hidden = false; $('#imgDeclRow').hidden = false; $('#imgPrev').innerHTML = `<figure class="media" style="aspect-ratio:auto;max-height:260px"><img src="${img}" alt=""><span class="ai-badge">✦ AI</span></figure>`; }; r.readAsDataURL(file); };
f.onsubmit = async e => {
  e.preventDefault(); msg.className = 'cmsg'; msg.textContent = '';
  if (!f.text.value.trim()){ msg.className = 'cmsg err'; msg.textContent = X.short; return; }
  if (Date.now() - t0 < 2500) return;
  try { S.nickSet(f.nick.value);
    const d = await api('/api/wall/post', {lang: S.lang, text: f.text.value, nick: f.nick.value, adult: !!f.adult.checked || !!ME, image: img, img_decl: img ? !!f.img_decl.checked : undefined, website: f.website.value});
    msg.className = 'cmsg ok'; msg.textContent = d.pending ? X.pend : X.ok; f.text.value = ''; img = null; $('#imgPrev').innerHTML = ''; $('#imgDeclRow').hidden = true; load(true);
  } catch(err){ msg.className = 'cmsg err'; msg.textContent = err.message; }
};
fetch('/api/account/me', {credentials: 'same-origin'}).then(r => r.json()).then(m => { ME = m.user || null; if (ME && $('#adultRow')) $('#adultRow').hidden = true; }).catch(() => {});
if ($('#refCopy')) $('#refCopy').onclick = async () => { let u = location.origin + '/'; try { const r = await fetch('/api/referral', {credentials: 'same-origin'}); if (r.ok){ const d = await r.json(); if (d.link) u = d.link; } } catch(e){} try { await navigator.clipboard.writeText(u); $('#refCopy').textContent = T.copied; } catch(e){ prompt(T.copy, u); } };
/* „do góry”, szybki kompozytor, „Nowe posty (n)”, zapamiętanie pozycji przewinięcia */
document.body.insertAdjacentHTML('beforeend', `<button type="button" class="wall-top" hidden aria-label="${X.top}">↑</button><button type="button" class="wall-write" aria-label="${X.write}">✍️</button><button type="button" class="wall-pill" hidden></button>`);
const topB = $('.wall-top'), pill = $('.wall-pill');
addEventListener('scroll', () => { topB.hidden = scrollY < 900; document.body.classList.toggle('pasthero', scrollY > 650); }, {passive: true});
topB.onclick = () => scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
$('.wall-write').onclick = () => { f.scrollIntoView({block: 'center', behavior: 'smooth'}); setTimeout(() => f.text.focus(), 300); };
function hidePill(){ pill.hidden = true; }
pill.onclick = () => { hidePill(); const nb = document.querySelector('[data-sort=new]'); if (sort !== 'new' && nb) nb.click(); else load(true); scrollTo({top: (host || feed).offsetTop - 120, behavior: 'smooth'}); };
setInterval(async () => { if (document.hidden || !newest) return;
  try { const d = await api('/api/wall?sort=new&limit=20'); const n = d.items.filter(p => p.t > newest && !p.mine).length;
    if (n){ pill.textContent = `↑ ${X.newp} (${n})`; pill.hidden = false; } } catch(e){} }, 30000);
const KEY = 'luna.wallpos';
addEventListener('pagehide', () => { try { sessionStorage.setItem(KEY, JSON.stringify({y: scrollY, n: posts().length, sort})); } catch(e){} });
let saved = null; try { saved = JSON.parse(sessionStorage.getItem(KEY) || 'null'); sessionStorage.removeItem(KEY); } catch(e){}
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
if (saved && saved.n && !new URLSearchParams(location.search).get('post')){
  sort = ['top', 'hot', 'new'].includes(saved.sort) ? saved.sort : 'hot'; document.querySelectorAll('.tabs [data-sort]').forEach(x => x.classList.toggle('on', x.dataset.sort === sort));
  load(true, Math.min(20, Math.max(10, saved.n))).then(() => scrollTo(0, saved.y));
} else load(true);
})();

/* karta „Poleć Lunę” ukryta, gdy właściciel wyłączył program */
(() => { const c = document.getElementById("refCard"); if (c) fetch("/api/referral/status").then(r => r.json()).then(d => { if (!d.enabled) c.hidden = true; }).catch(() => {}); })();
