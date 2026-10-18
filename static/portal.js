/* Luna – portal porad: wyszukiwarka z podpowiedziami, zakładki, filtry, karty z odpowiedzią i głosem Luny. */
(() => {
const $ = s => document.querySelector(s);
const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ł/g, 'l');
const fmt = s => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
let LIB = {items: [], cats: []}, VOICE = {}, view = 'popularne', query = '';
const ICON = {}; const CATN = {};

function card(it){
  const a = document.createElement('a'); a.className = 'vcard'; a.href = '#porada/' + it.id;
  const th = document.createElement('div'); th.className = 'thumb';
  const im = document.createElement('img'); im.loading = 'lazy'; im.alt = ''; im.src = it.thumb; if (it.thumb.endsWith('.jpg')) im.srcset = it.thumb + ' 1x, ' + it.thumb.replace('.jpg', '@2x.jpg') + ' 2x';
  const ic = document.createElement('span'); ic.className = 'cic'; ic.textContent = it.kind === 'faq' ? '❓' : (ICON[it.cat] || '🎙️');
  const du = document.createElement('span'); du.className = 'dur'; du.textContent = '▶ ' + fmt(it.secs);
  const lv = document.createElement('span'); lv.className = 'lvl l' + it.level; lv.textContent = it.level_name;
  const pl = document.createElement('span'); pl.className = 'play'; pl.textContent = '▶';
  th.append(im, ic, du, lv, pl);
  const t = document.createElement('h3'); t.textContent = it.title;
  const m = document.createElement('p'); m.className = 'meta'; m.textContent = (it.kind === 'faq' ? 'FAQ' : CATN[it.cat]) + ' · Luna, asystentka AI';
  a.append(th, t, m); return a;
}
function filtered(){
  const c = $('#fCat').value, l = $('#fLen').value, v = $('#fLvl').value, q = norm(query).trim();
  $('#fClear').hidden = !(c || l || v || q);
  return LIB.items.filter(it => (!c || it.cat === c) && (!v || it.level === v) &&
    (!l || (l === 's' ? it.secs <= 15 : l === 'm' ? it.secs > 15 && it.secs <= 25 : it.secs > 25)) &&
    (!q || q.split(/\s+/).every(w => norm(it.title + ' ' + it.text + ' ' + it.keywords.join(' ') + ' ' + (CATN[it.cat] || '')).includes(w))));
}
function render(){
  const g = $('#grid'); g.textContent = ''; g.className = 'grid';
  document.querySelectorAll('#tabs a[data-tab]').forEach(a => a.classList.toggle('on', a.dataset.tab === view));
  let items = filtered();
  if (view === 'kategorie' && !$('#fCat').value && !query){
    $('#vtitle').textContent = 'Kategorie'; $('#vsub').textContent = 'Wybierz obszar, nad którym chcesz popracować.';
    g.className = 'grid cats';
    LIB.cats.forEach(c => { const n = LIB.items.filter(i => i.cat === c.id).length; if (!n) return;
      const a = document.createElement('a'); a.className = 'catcard'; a.href = '#kategoria/' + c.id;
      const i = document.createElement('span'); i.className = 'ci'; i.textContent = c.icon;
      const h = document.createElement('h3'); h.textContent = c.name; const p = document.createElement('p'); p.textContent = c.desc;
      const k = document.createElement('small'); k.textContent = n + (n === 1 ? ' porada' : n < 5 ? ' porady' : ' porad');
      a.append(i, h, p, k); g.appendChild(a); });
    return;
  }
  if (query){ $('#vtitle').textContent = `Wyniki: „${query}”`; $('#vsub').textContent = items.length ? `Znaleziono: ${items.length}` : 'Brak wyników – spróbuj innego słowa, np. „oddech” albo „trema”.'; }
  else if ($('#fCat').value){ $('#vtitle').textContent = CATN[$('#fCat').value] || 'FAQ'; $('#vsub').textContent = (LIB.cats.find(c => c.id === $('#fCat').value) || {}).desc || ''; }
  else if (view === 'najnowsze'){ $('#vtitle').textContent = 'Najnowsze'; $('#vsub').textContent = 'Ostatnio dodane do biblioteki porad.'; items = items.slice().reverse(); }
  else { $('#vtitle').textContent = 'Popularne'; $('#vsub').textContent = 'Polecane na start – krótkie porady, które możesz przećwiczyć od razu.'; items = items.slice().sort((a, b) => (a.kind === 'faq') - (b.kind === 'faq') || a.level.localeCompare(b.level) || a.order - b.order); }
  items.forEach(it => g.appendChild(card(it)));
}
function openCard(id){
  const it = LIB.items.find(i => i.id === id); if (!it) return;
  $('#cTitle').textContent = it.title; $('#cText').textContent = it.text;
  $('#cMeta').textContent = (it.kind === 'faq' ? 'FAQ' : CATN[it.cat]) + ' · ' + it.level_name + ' · ok. ' + fmt(it.secs);
  $('#cThumb').style.backgroundImage = `url(${it.thumb})`; $('#cDur').textContent = '▶ ' + fmt(it.secs);
  const au = $('#cAudio'); au.pause(); au.removeAttribute('src');
  $('#cPlay').textContent = '▶ Posłuchaj Luny'; $('#cPlay').disabled = false;
  $('#cPlay').onclick = () => {
    if (!au.paused){ au.pause(); $('#cPlay').textContent = '▶ Posłuchaj Luny'; return; }
    if (!au.src){ const p = new URLSearchParams(Object.assign({}, VOICE, {text: it.text})); au.src = '/api/tts?' + p; $('#cPlay').textContent = '⏳ Luna przygotowuje głos…'; }
    au.play().then(() => $('#cPlay').textContent = '⏸ Pauza').catch(() => $('#cPlay').textContent = '▶ Posłuchaj Luny');
  };
  au.onended = () => $('#cPlay').textContent = '▶ Posłuchaj jeszcze raz';
  const d = $('#card'); if (!d.open) d.showModal();
}
$('#cClose').onclick = () => $('#card').close();
$('#card').addEventListener('close', () => { $('#cAudio').pause(); if (location.hash.startsWith('#porada/')) history.replaceState(null, '', '#' + view); });
$('#card').addEventListener('click', e => { if (e.target === $('#card')) $('#card').close(); });

function route(){
  const h = decodeURIComponent(location.hash.slice(1));
  if (h.startsWith('porada/')) return openCard(h.slice(7));
  if (h.startsWith('kategoria/')){ view = 'kategorie'; $('#fCat').value = h.slice(10); query = ''; $('#q').value = ''; render(); return scrollToView(); }
  if (['popularne', 'najnowsze', 'kategorie'].includes(h)){ view = h; if (h === 'kategorie') $('#fCat').value = ''; render(); scrollToView(); }
}
function scrollToView(){ $('#view').scrollIntoView({behavior: 'smooth', block: 'start'}); }
window.addEventListener('hashchange', route);
['fCat', 'fLen', 'fLvl'].forEach(id => $('#' + id).onchange = render);
$('#fClear').onclick = () => { $('#fCat').value = $('#fLen').value = $('#fLvl').value = ''; query = ''; $('#q').value = ''; render(); };

/* ---------- wyszukiwarka z podpowiedziami ---------- */
const q = $('#q'), sg = $('#sugg'); let sel = -1, opts = [];
function suggest(){
  const v = norm(q.value).trim(); sel = -1;
  if (!v){ sg.hidden = true; return; }
  const sc = it => { const t = norm(it.title); return t.startsWith(v) ? 3 : t.includes(v) ? 2 : norm(it.keywords.join(' ') + ' ' + CATN[it.cat]).includes(v) ? 1.5 : norm(it.text).includes(v) ? 1 : 0; };
  opts = LIB.items.map(it => [sc(it), it]).filter(x => x[0]).sort((a, b) => b[0] - a[0]).slice(0, 8).map(x => x[1]);
  const cats = LIB.cats.filter(c => norm(c.name).includes(v)).slice(0, 2);
  sg.textContent = '';
  cats.forEach(c => { const li = document.createElement('li'); li.role = 'option'; li.textContent = c.icon + ' Kategoria: ' + c.name; li.onmousedown = e => { e.preventDefault(); sg.hidden = true; location.hash = 'kategoria/' + c.id; }; sg.appendChild(li); });
  opts.forEach((it, i) => { const li = document.createElement('li'); li.role = 'option';
    const b = document.createElement('b'); b.textContent = it.title; const s = document.createElement('small'); s.textContent = (it.kind === 'faq' ? 'FAQ' : CATN[it.cat]) + ' · ' + fmt(it.secs);
    li.append(b, s); li.onmousedown = e => { e.preventDefault(); sg.hidden = true; location.hash = 'porada/' + it.id; }; sg.appendChild(li); });
  if (!sg.children.length){ const li = document.createElement('li'); li.className = 'none'; li.textContent = 'Brak podpowiedzi – naciśnij Enter, aby szukać w treści.'; sg.appendChild(li); }
  sg.hidden = false;
}
q.addEventListener('input', suggest);
q.addEventListener('focus', suggest);
q.addEventListener('blur', () => setTimeout(() => sg.hidden = true, 120));
q.addEventListener('keydown', e => {
  const lis = [...sg.querySelectorAll('li[role=option]')];
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp'){ e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + lis.length) % lis.length; lis.forEach((l, i) => l.classList.toggle('sel', i === sel)); }
  else if (e.key === 'Enter' && sel >= 0 && lis[sel]){ e.preventDefault(); lis[sel].onmousedown(e); }
  else if (e.key === 'Escape') sg.hidden = true;
});
$('#searchForm').onsubmit = e => { e.preventDefault(); sg.hidden = true; query = q.value.trim(); if (view === 'kategorie') view = 'popularne'; render(); scrollToView(); };

/* ---------- dane ---------- */
Promise.all([fetch('/api/library').then(r => r.json()), fetch('/api/config').then(r => r.json()).catch(() => ({}))]).then(([lib, cfg]) => {
  LIB = lib; LIB.cats.forEach(c => { ICON[c.id] = c.icon; CATN[c.id] = c.name; const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; $('#fCat').appendChild(o); });
  const o = document.createElement('option'); o.value = 'faq'; o.textContent = 'FAQ'; $('#fCat').appendChild(o);
  VOICE = cfg.voice_defaults || {};
  const fl = $('#faqList'); LIB.items.filter(i => i.kind === 'faq').forEach(i => { const d = document.createElement('details'); const s = document.createElement('summary'); s.textContent = i.title; const p = document.createElement('p'); p.textContent = i.text; d.append(s, p); fl.appendChild(d); });
  render(); route();
});
fetch('/api/catalog').then(r => r.json()).then(c => {
  const pr = id => { const p = c.plans.find(x => x.id === id); return p && p.prices ? String(p.prices.pln).replace('.', ',') + ' zł' : null; };
  if (pr('premium') && pr('pro')){ const fl = $('#faqList'); const d = document.createElement('details'); const sm = document.createElement('summary'); sm.textContent = 'Ile kosztuje Luna?'; const pp = document.createElement('p');
    pp.textContent = `Aplikacja jest bezpłatna. Plan Darmowy działa bez konta (z dziennym limitem), Podstawowa jest za darmo – wystarczy konto. Premium kosztuje ${pr('premium')}, a Pro ${pr('pro')} za 30 dni – jednorazowo, bez automatycznego odnawiania, cena zawiera VAT. Testerzy dostają 2 miesiące Premium za darmo.`;
    d.append(sm, pp); fl.prepend(d); }
  const P = $('#plans'); P.textContent = '';
  c.plans.forEach((p, i) => { const d = document.createElement('div'); d.className = 'plan' + (p.id === 'premium' ? ' hl' : '');
    const h = document.createElement('h3'); h.textContent = p.name; const ul = document.createElement('ul');
    p.features.forEach(f => { const li = document.createElement('li'); li.textContent = f; if (/oraz:$/.test(f)) li.className = 'inc'; ul.appendChild(li); });
    d.append(h, ul);
    const t = document.createElement('p'); t.className = 'ptag';
    const free = p.id === 'darmowy' || p.id === 'podstawowa';
    if (p.prices || free){ const b = document.createElement('div'); b.className = 'pbig'; b.textContent = free ? '0 zł' : String(p.prices.pln).replace('.', ',') + ' zł';
      const s = document.createElement('small'); s.className = 'psub'; s.textContent = p.id === 'darmowy' ? 'bez konta, z limitem' : p.id === 'podstawowa' ? 'za darmo – wystarczy konto' : '30 dni · bez odnawiania · cena zawiera VAT';
      d.insertBefore(s, ul); d.insertBefore(b, s); }
    t.textContent = free ? '✓ Bez opłat' : p.id === 'premium' ? '🎁 Testerzy: Premium 2 miesiące za darmo' + (p.prices ? ' (wartość ' + (Math.round(parseFloat(String(p.prices.pln).replace(',', '.')) * 200) / 100).toFixed(2).replace('.', ',') + ' zł)' : '') : 'Płatności – wkrótce';
    d.appendChild(t); P.appendChild(d); });
}).catch(() => {});
function liveTab(){
  fetch('/api/live-room/state').then(r => r.json()).then(s => {
    const el = $('#liveTab');
    if (s.on){ el.textContent = '● NA ŻYWO'; el.className = 'lv on'; }
    else { const d = new Date(s.sched.next_start); el.textContent = d.toLocaleDateString('pl-PL', {weekday: 'short', timeZone: 'Europe/Warsaw'}) + ' ' + s.sched.time; el.className = 'lv'; }
  }).catch(() => {});
}
liveTab(); setInterval(liveTab, 60000);
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
})();
