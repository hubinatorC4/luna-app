/* Strona główna jako jeden długi kanał: kompaktowe intro → Ścianka Agentek Głosu (nieskończone przewijanie),
   a między wpisami karty: Butik (zdjęcie + cena), porady, plany, testerzy, casting, pobieranie, FAQ. Tylko prawdziwe dane. */
(() => {
const S = window.LunaSocial || {}; const L = S.lang || 'pl'; const esc = S.esc || (x => String(x));
const host = document.getElementById('feedHost'), Qbox = document.getElementById('hfQueue');
if (!host || !Qbox) return;
const T = {pl: {share: 'Udostępnij', copied: 'Link skopiowany! 📋', les: 'Lekcje głosu z Luną', lessub: 'Krótkie ćwiczenia, które Luna czyta na głos. Wybierz temat i posłuchaj.', today: 'Lekcja dnia', listen: '▶ Posłuchaj Luny', ex: 'ćwiczeń', min: 'min', allles: 'Wszystkie lekcje →', ph: 'zdjęcie wkrótce', shop: 'Butik Luny', all: 'Wszystkie kolory w cenie', see: 'Zobacz w Butiku', soon: 'Premiera', free: 'W cenie planu', more: 'Pokaż więcej', less: 'Zwiń', colors: 'kolory'},
 en: {share: 'Share', copied: 'Link copied! 📋', les: 'Voice lessons with Luna', lessub: 'Short exercises Luna reads aloud. Pick a topic and listen.', today: 'Lesson of the day', listen: '▶ Listen to Luna', ex: 'exercises', min: 'min', allles: 'All lessons →', ph: 'photo coming soon', shop: 'Luna’s Boutique', all: 'All colours included', see: 'See in the Boutique', soon: 'Release', free: 'Included in plan', more: 'See more', less: 'See less', colors: 'colours'},
 es: {share: 'Compartir', copied: '¡Enlace copiado! 📋', les: 'Clases de voz con Luna', lessub: 'Ejercicios cortos que Luna lee en voz alta. Elige un tema y escucha.', today: 'Lección del día', listen: '▶ Escucha a Luna', ex: 'ejercicios', min: 'min', allles: 'Todas las lecciones →', ph: 'foto próximamente', shop: 'Boutique de Luna', all: 'Todos los colores incluidos', see: 'Ver en la Boutique', soon: 'Estreno', free: 'Incluido en el plan', more: 'Ver más', less: 'Ver menos', colors: 'colores'},
 de: {share: 'Teilen', copied: 'Link kopiert! 📋', les: 'Stimmlektionen mit Luna', lessub: 'Kurze Übungen, die Luna vorliest. Thema wählen und zuhören.', today: 'Lektion des Tages', listen: '▶ Luna anhören', ex: 'Übungen', min: 'Min.', allles: 'Alle Lektionen →', ph: 'Foto folgt', shop: 'Lunas Boutique', all: 'Alle Farben inklusive', see: 'In der Boutique ansehen', soon: 'Release', free: 'Im Plan enthalten', more: 'Mehr anzeigen', less: 'Weniger anzeigen', colors: 'Farben'},
 uk: {share: 'Поділитися', copied: 'Посилання скопійовано! 📋', les: 'Уроки голосу з Луною', lessub: 'Короткі вправи, які Луна читає вголос. Оберіть тему й слухайте.', today: 'Урок дня', listen: '▶ Послухати Луну', ex: 'вправ', min: 'хв', allles: 'Усі уроки →', ph: 'фото незабаром', shop: 'Бутик Луни', all: 'Усі кольори в ціні', see: 'Переглянути в Бутику', soon: 'Прем’єра', free: 'Входить у план', more: 'Показати більше', less: 'Згорнути', colors: 'кольори'}}[L] || {};
const lq = L === 'pl' ? '' : '?lang=' + L;
const sections = [...Qbox.children];
const Q = []; let butik = []; let lessons = null;
function build(){
  const order = ['porady', 'plany', 'testerzy', 'dolacz', 'pobierz', 'faq', 'komentarze'];
  const secs = order.map(id => sections.find(s => s.id === id)).filter(Boolean);
  sections.filter(s => !secs.includes(s)).forEach(s => secs.push(s));
  if (lessons) Q.push(lessons);
  let b = 0;
  secs.forEach((s, i) => { if (butik[b] && i > 0) Q.push(butik[b++]); Q.push(s); });
  while (butik[b]) Q.push(butik[b++]);
}
const pln = n => String(n).replace('.', ',') + ' zł';
function card(i, show){
  const nm = L === 'pl' ? i.name : (i.name_en || i.name); const v = (i.variants || []).filter(x => x.hex);
  const real = i.image || (v.find(x => x.image) || {}).image; const img = real || '/catalog/butik/placeholder.svg';
  const price = i.price && show ? `<b class="hfprice">${pln(i.price.pln)}</b>` : i.tier === 'free' ? `<b class="hfprice">${esc(T.free)}</b>` : '';
  const sw = v.length ? `<span class="hfsw" aria-label="${v.length} ${esc(T.colors)}">${v.slice(0, 5).map(x => `<i style="background:${esc(x.hex)}" title="${esc(L === 'pl' ? x.color_name_pl : x.color_name_en)}"></i>`).join('')}${v.length > 5 ? `<small>+${v.length - 5}</small>` : ''}</span>` : '';
  const soon = i.upcoming && i.release_date ? `<span class="hfsoon">📅 ${esc(T.soon)} ${esc(new Date(i.release_date + 'T12:00:00').toLocaleDateString(L === 'uk' ? 'uk-UA' : L, {day: 'numeric', month: 'long'}))}</span>` : '';
  const el = document.createElement('a'); el.className = 'hfshop'; el.href = '/butik.html' + lq + '#' + encodeURIComponent(i.id); el.dataset.track = 'item:' + i.id;
  el.innerHTML = `<span class="hfkick">🛍️ ${esc(T.shop)}</span><span class="hfimg"><img src="${esc(img)}" alt="${esc(nm)}" loading="lazy" width="800" height="600">${real ? '' : `<span class="hfph">📷 ${esc(T.ph)}</span>`}</span><span class="hfbody"><span class="hfname">${esc(nm)}</span>${soon}<span class="hfrow">${price}${sw}</span>${v.length > 1 ? `<span class="hfall2">🎨 ${esc(T.all)}</span>` : ''}<span class="hfcta">${esc(T.see)} →</span><span class="hfshare" role="button" tabindex="0" data-hfshare="${esc(i.id)}" data-text="${esc(nm)}" aria-label="${esc(T.share)}">↗ ${esc(T.share)}</span></span>`;
  return el;
}

/* Lekcje głosu z Luną – z prawdziwej biblioteki porad (/api/library); każda porada ma nagranie głosem Luny (▶ w karcie porady). */
const LIMG = {barwa: 'outfit_sweter', oddech: 'pose_siedzaca', dykcja: 'outfit_biznes', tempo: 'pose_zamyslona', pewnosc: 'outfit_koktajlowa', wystapienia: 'pose_prosto', rozgrzewka: 'pose_polobrot', zdrowie: 'outfit_wieczorowa'};
const limg = (c, i) => '/catalog/luna/' + (LIMG[c] || Object.values(LIMG)[i % 8]) + '.webp';
function lessonsCard(lib){
  const tips = (lib.items || []).filter(i => i.kind !== 'faq'); if (!tips.length || !(lib.cats || []).length) return null;
  const day = Math.floor(Date.now() / 864e5); const t = tips[day % tips.length]; const ci = lib.cats.findIndex(c => c.id === t.cat);
  const el = document.createElement('section'); el.className = 'hfcard hflessons'; el.id = 'lekcje'; el.dataset.track = 'sec:lekcje';
  const tiles = lib.cats.map((c, i) => { const its = tips.filter(x => x.cat === c.id); if (!its.length) return '';
    const m = Math.max(1, Math.round(its.reduce((a, x) => a + (x.secs || 0), 0) / 60));
    return `<a class="lstile" href="#kategoria/${esc(c.id)}"><img src="${limg(c.id, i)}" alt="" loading="lazy" width="320" height="180"><span class="lsic">${esc(c.icon || '🎙️')}</span><b>${esc(c.name)}</b><small>${its.length} ${esc(T.ex)} · ~${m} ${esc(T.min)}</small></a>`; }).join('');
  el.innerHTML = `<h2>🎙️ ${esc(T.les)}</h2><p class="hfsub">${esc(T.lessub)}</p>
    <a class="lsday" href="#porada/${esc(t.id)}"><span class="lsimg"><img src="${limg(t.cat, ci)}" alt="Luna" loading="lazy" width="640" height="360"></span><span class="lsbody"><span class="lskick">⭐ ${esc(T.today)} · ${esc((lib.cats[ci] || {}).name || '')}</span><b>${esc(t.title)}</b><span class="lstxt">${esc(t.text)}</span><span class="pill primary">${esc(T.listen)}</span></span></a>
    <div class="lsrow">${tiles}</div><a class="hfall" href="#kategorie">${esc(T.allles)}</a>`;
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
  requestAnimationFrame(() => { if (el.scrollHeight < 900 || el.querySelector('form')) return; el.classList.add('hfclamp');
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
  if (sections.some(s => s.id === id) || ['popularne', 'najnowsze', 'kategorie', 'kategoria', 'porada'].includes(id)) placeAll(); }, true);
Promise.all([fetch('/api/library' + (L === 'pl' ? '' : '?lang=' + L)).then(r => r.json()).then(l => { lessons = lessonsCard(l); }).catch(() => {}), fetch('/api/butik').then(r => r.json()).then(b => { const its = (b.items || []).slice(); const ph = i => (i.image || (i.variants || []).some(x => x.image)) ? 1 : 0; const pr = id => { const k = (b.popular || []).indexOf(id); return k < 0 ? 999 : k; }; its.sort((x, y) => (ph(y) - ph(x)) || (pr(x.id) - pr(y.id)) || ((y.upcoming ? 1 : 0) - (x.upcoming ? 1 : 0))); const seen = {}, pick = []; its.forEach(i => { const c = i.category || ''; if ((seen[c] = (seen[c] || 0) + 1) <= 2 && pick.length < 14) pick.push(i); }); butik = pick.map(i => card(i, b.prices_visible)); }).catch(() => {})]).finally(go);

/* udostępnianie karty Butiku w kanale: Web Share API albo kopiowanie linku (z UTM), liczone w statystykach właściciela */
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-hfshare]'); if (!b) return; e.preventDefault(); e.stopPropagation();
  const S2 = window.LunaSocial || {}, base = location.origin + '/butik.html#' + encodeURIComponent(b.dataset.hfshare);
  const mk = src => S2.utm ? S2.utm(base, src, 'butik') : base;
  if (S2.track) S2.track('share', 'item:' + b.dataset.hfshare);
  if (navigator.share){ try { await navigator.share({url: mk('native'), text: b.dataset.text}); S2.track && S2.track('sharenet', 'utm:native'); return; } catch(x){ if (x && x.name === 'AbortError') return; } }
  try { await navigator.clipboard.writeText(mk('copy')); } catch(x){ prompt('', mk('copy')); }
  S2.track && S2.track('sharenet', 'utm:copy'); const o = b.textContent; b.textContent = T.copied; setTimeout(() => b.textContent = o, 1800);
}, true);
})();
