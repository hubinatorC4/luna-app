/* Galeria agentek: nieskończone przewijanie, prawdziwe polubienia (ta sama ochrona antybotowa co na Ściance), Agentka tygodnia. */
(() => {
const $ = s => document.querySelector(s); const S = window.LunaSocial || {}; const esc = S.esc || (x => String(x).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])));
const D = JSON.parse(document.getElementById('i18n').textContent); const L = (document.documentElement.lang || 'pl').slice(0, 2); const t = Object.assign({}, D.pl, D[L] || {});
const lq = L === 'pl' ? '' : '?lang=' + L;
let next = 0, busy = false;
const href = x => x.id.startsWith('luna-') ? '/promo.html' + lq + '#luna' : '/scianka.html' + (lq ? lq + '&' : '?') + 'post=' + encodeURIComponent(x.id);
const card = x => `<figure class="galitem card" data-track="${esc(x.target)}"><a href="${href(x)}"><img src="${esc(x.img)}" alt="${esc(x.agent || x.nick)}" loading="lazy" width="480" height="360"></a>
  <figcaption><b>${esc(x.agent || x.nick)}</b>${x.agent && x.nick !== x.agent ? `<small> · ${esc(x.nick)}</small>` : ''}<span data-votes="${esc(x.target)}"></span></figcaption></figure>`;
async function more(){
  if (busy || next === null) return; busy = true;
  try {
    const d = await (await fetch('/api/gallery?offset=' + next + '&limit=18')).json();
    if (next === 0 && d.week){ const w = d.week; const el = $('#galWeek'); el.hidden = false;
      el.innerHTML = `<a href="${href(w)}"><img src="${esc(w.img)}" alt="" width="640" height="420"></a><div><span class="lskick">${esc(t.week)}</span><h2>${esc(w.agent || w.nick)}</h2><p>❤️ <b>${w.likes}</b> ${esc(t.likes)}</p><a class="pill primary" href="${href(w)}">${esc(t.open)}</a></div>`; }
    $('#galGrid').insertAdjacentHTML('beforeend', d.items.map(card).join(''));
    if (next === 0 && !d.items.length) $('#galGrid').innerHTML = `<p class="empty">${esc(t.empty)}</p>`;
    next = d.next; $('#galMore').textContent = next === null ? '' : '…';
    if (S.auto) S.auto(); if (S.observe) S.observe($('#galGrid'));
  } catch(e){} busy = false;
}
new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) more(); }, {rootMargin: '800px'}).observe($('#galMore'));
more();
})();
