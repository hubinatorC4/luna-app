/* Strona główna jako jeden długi kanał: kompaktowe intro → Ścianka Agentek Głosu (nieskończone przewijanie),
   a między wpisami karty: Butik (zdjęcie + cena), porady, plany, testerzy, casting, pobieranie, FAQ. Tylko prawdziwe dane. */
(() => {
const S = window.LunaSocial || {}; const L = S.lang || 'pl'; const esc = S.esc || (x => String(x));
const host = document.getElementById('feedHost'), Qbox = document.getElementById('hfQueue');
if (!host || !Qbox) return;
const T = {pl: {ph: 'zdjęcie wkrótce', shop: 'Butik Luny', all: 'Wszystkie kolory w cenie', see: 'Zobacz w Butiku', soon: 'Premiera', free: 'W cenie planu', more: 'Pokaż więcej', less: 'Zwiń', colors: 'kolory'},
 en: {ph: 'photo coming soon', shop: 'Luna’s Boutique', all: 'All colours included', see: 'See in the Boutique', soon: 'Release', free: 'Included in plan', more: 'See more', less: 'See less', colors: 'colours'},
 es: {ph: 'foto próximamente', shop: 'Boutique de Luna', all: 'Todos los colores incluidos', see: 'Ver en la Boutique', soon: 'Estreno', free: 'Incluido en el plan', more: 'Ver más', less: 'Ver menos', colors: 'colores'},
 de: {ph: 'Foto folgt', shop: 'Lunas Boutique', all: 'Alle Farben inklusive', see: 'In der Boutique ansehen', soon: 'Release', free: 'Im Plan enthalten', more: 'Mehr anzeigen', less: 'Weniger anzeigen', colors: 'Farben'},
 uk: {ph: 'фото незабаром', shop: 'Бутик Луни', all: 'Усі кольори в ціні', see: 'Переглянути в Бутику', soon: 'Прем’єра', free: 'Входить у план', more: 'Показати більше', less: 'Згорнути', colors: 'кольори'}}[L] || {};
const lq = L === 'pl' ? '' : '?lang=' + L;
const sections = [...Qbox.children];
const Q = []; let butik = [];
function build(){
  const order = ['porady', 'plany', 'testerzy', 'dolacz', 'pobierz', 'faq', 'komentarze'];
  const secs = order.map(id => sections.find(s => s.id === id)).filter(Boolean);
  sections.filter(s => !secs.includes(s)).forEach(s => secs.push(s));
  let b = 0;
  secs.forEach((s, i) => { if (butik[b] && i > 0) Q.push(butik[b++]); Q.push(s); });
  while (butik[b]) Q.push(butik[b++]);
}
const pln = n => String(n).replace('.', ',') + ' zł';
function card(i, show){
  const nm = L === 'pl' ? i.name : (i.name_en || i.name); const v = (i.variants || []).filter(x => x.hex);
  const real = i.image || (v.find(x => x.image) || {}).image; const img = real || '/wall/official/butik.webp';
  const price = i.price && show ? `<b class="hfprice">${pln(i.price.pln)}</b>` : i.tier === 'free' ? `<b class="hfprice">${esc(T.free)}</b>` : '';
  const sw = v.length ? `<span class="hfsw" aria-label="${v.length} ${esc(T.colors)}">${v.slice(0, 5).map(x => `<i style="background:${esc(x.hex)}" title="${esc(L === 'pl' ? x.color_name_pl : x.color_name_en)}"></i>`).join('')}${v.length > 5 ? `<small>+${v.length - 5}</small>` : ''}</span>` : '';
  const soon = i.upcoming && i.release_date ? `<span class="hfsoon">📅 ${esc(T.soon)} ${esc(new Date(i.release_date + 'T12:00:00').toLocaleDateString(L === 'uk' ? 'uk-UA' : L, {day: 'numeric', month: 'long'}))}</span>` : '';
  const el = document.createElement('a'); el.className = 'hfshop'; el.href = '/butik.html' + lq + '#' + encodeURIComponent(i.id); el.dataset.track = 'item:' + i.id;
  el.innerHTML = `<span class="hfkick">🛍️ ${esc(T.shop)}</span><span class="hfimg"><img src="${esc(img)}" alt="${esc(nm)}" loading="lazy" width="800" height="600">${real ? '' : `<span class="hfph">📷 ${esc(T.ph)}</span>`}</span><span class="hfbody"><span class="hfname">${esc(nm)}</span>${soon}<span class="hfrow">${price}${sw}</span>${v.length > 1 ? `<span class="hfall2">🎨 ${esc(T.all)}</span>` : ''}<span class="hfcta">${esc(T.see)} →</span></span>`;
  return el;
}
let placedAll = false;
function after(node){ host.appendChild(node); collapse(node); if (S.observe) S.observe(node.parentNode); }
function interleave(ch){
  if (!ch || !ch.isConnected) return;
  const arts = [...ch.querySelectorAll(':scope > article')]; let cur = ch, n = 0;
  for (let i = 0; i < arts.length; i++){
    n++;
    if (n === 2 && i < arts.length - 1 && Q.length){
      const c = Q.shift(); cur.after(c); collapse(c);
      const nc = document.createElement('div'); nc.className = 'wallpage chunk'; c.after(nc); arts.slice(i + 1).forEach(a => nc.appendChild(a)); cur = nc; n = 0;
    }
  }
  if (Q.length) { const c = Q.shift(); host.appendChild(c); collapse(c); }
  if (S.observe) S.observe(host);
}
function placeAll(){ if (placedAll) return; placedAll = true; while (Q.length) after(Q.shift()); }
window.LunaHomePlace = placeAll;
function collapse(el){
  if (!el.classList || !el.classList.contains('hfcard') || el.dataset.col) return; el.dataset.col = 1;
  requestAnimationFrame(() => { if (el.scrollHeight < 900) return; el.classList.add('hfclamp');
    const b = document.createElement('button'); b.type = 'button'; b.className = 'hfmore'; b.textContent = T.more; b.setAttribute('aria-expanded', 'false');
    b.onclick = () => { const o = el.classList.toggle('open'); b.textContent = o ? T.less : T.more; b.setAttribute('aria-expanded', o); if (!o) el.scrollIntoView({block: 'start'}); };
    el.appendChild(b); });
}
let pending = (window.LunaFeedBatches || []).slice();
window.addEventListener('luna-feed-batch', e => { if (!ready) { pending.push(e.detail); return; } interleave(e.detail.feed); if (e.detail.done) placeAll(); });
let ready = false;
function go(){ ready = true; build(); pending.forEach(d => { interleave(d.feed); if (d.done) placeAll(); }); pending = [];
  const h = location.hash.slice(1); if (h && !/^porada\//.test(h)){ placeAll(); const t = document.getElementById(h.split('/')[0]) || (/^(popularne|najnowsze|kategori)/.test(h) && document.getElementById('view')); if (t) setTimeout(() => t.scrollIntoView({block: 'start'}), 200); } }
document.addEventListener('click', e => { const a = e.target.closest('a[href^="#"]'); if (!a) return; const id = a.getAttribute('href').slice(1).split('/')[0]; if (!id) return;
  if (sections.some(s => s.id === id) || ['popularne', 'najnowsze', 'kategorie', 'kategoria'].includes(id)) placeAll(); }, true);
fetch('/api/butik').then(r => r.json()).then(b => { const its = (b.items || []).slice(); const ph = i => (i.image || (i.variants || []).some(x => x.image)) ? 1 : 0; its.sort((x, y) => (ph(y) - ph(x)) || ((y.upcoming ? 1 : 0) - (x.upcoming ? 1 : 0))); const seen = {}, pick = []; its.forEach(i => { const c = i.category || ''; if ((seen[c] = (seen[c] || 0) + 1) <= 2 && pick.length < 14) pick.push(i); }); butik = pick.map(i => card(i, b.prices_visible)); }).catch(() => {}).finally(go);
})();
