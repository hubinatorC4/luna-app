/* Luna – wersja na komputer (desktop d1): tylko ≥1024 px. Na telefonie nic nie robi (i cofa zmiany przy zwężeniu okna).
   1) nagłówek: język i link do aplikacji w „Więcej ▾”, stan powiadomień w dymku dzwonka;
   2) zakładki: to, co się nie mieści, trafia do „Więcej ▾” (nic nie jest ucinane);
   3) strona główna: boczna kolumna (testerzy, na skróty, aplikacja). */
(() => {
if (document.documentElement.hasAttribute('data-app') || ['/app', '/index.html', '/app.html', '/panel.html', '/admin-support.html'].includes(location.pathname)) return;
const header = document.querySelector('header.top');
if (!header || !header.querySelector('.bar')) return;
const mq = matchMedia('(min-width:1024px)');
const lang = (document.documentElement.lang || 'pl').slice(0, 2);
const T = {
  pl: {more: 'Więcej', lang: 'Język', menu: 'Więcej opcji', quick: 'Na skróty', quickP: 'Wszystko pod ręką – bez przewijania do końca świata.',
       bitwy: '⚔️ Bitwy', rank: '🏆 Ranking', butik: '👗 Butik', gal: '🖼️ Galeria', wall: '🧱 Ścianka', help: '💬 Pomoc',
       appH: '📲 Luna w kieszeni', appP: 'Na telefonie gada się jeszcze lepiej. Bez reklam, bo Luna i tak by je przegadała 😄', appB: 'Pobierz aplikację', appS: 'Za darmo · Android, iPhone i komputer',
       notif: 'Powiadomienia'},
  en: {more: 'More', lang: 'Language', menu: 'More options', quick: 'Shortcuts', quickP: 'Everything at hand – no scrolling to the end of the world.',
       bitwy: '⚔️ Battles', rank: '🏆 Ranking', butik: '👗 Boutique', gal: '🖼️ Gallery', wall: '🧱 Wall', help: '💬 Help',
       appH: '📲 Luna in your pocket', appP: 'Talking is even better on your phone. No ads – Luna would talk over them anyway 😄', appB: 'Get the app', appS: 'Free · Android, iPhone and desktop',
       notif: 'Notifications'},
  es: {more: 'Más', lang: 'Idioma', menu: 'Más opciones', quick: 'Accesos rápidos', quickP: 'Todo a mano, sin desplazarte hasta el fin del mundo.',
       bitwy: '⚔️ Batallas', rank: '🏆 Ranking', butik: '👗 Boutique', gal: '🖼️ Galería', wall: '🧱 Muro', help: '💬 Ayuda',
       appH: '📲 Luna en tu bolsillo', appP: 'En el móvil se habla aún mejor. Sin anuncios: Luna hablaría más que ellos 😄', appB: 'Descargar la app', appS: 'Gratis · Android, iPhone y ordenador',
       notif: 'Notificaciones'},
  de: {more: 'Mehr', lang: 'Sprache', menu: 'Weitere Optionen', quick: 'Schnellzugriff', quickP: 'Alles griffbereit – ohne bis ans Ende der Welt zu scrollen.',
       bitwy: '⚔️ Battles', rank: '🏆 Ranking', butik: '👗 Boutique', gal: '🖼️ Galerie', wall: '🧱 Pinnwand', help: '💬 Hilfe',
       appH: '📲 Luna für die Tasche', appP: 'Am Handy redet es sich noch besser. Ohne Werbung – Luna würde sie eh übertönen 😄', appB: 'App holen', appS: 'Kostenlos · Android, iPhone und Computer',
       notif: 'Benachrichtigungen'},
  uk: {more: 'Ще', lang: 'Мова', menu: 'Більше опцій', quick: 'Швидкий доступ', quickP: 'Усе під рукою – без прокручування до краю світу.',
       bitwy: '⚔️ Битви', rank: '🏆 Рейтинг', butik: '👗 Бутик', gal: '🖼️ Галерея', wall: '🧱 Стіна', help: '💬 Допомога',
       appH: '📲 Луна в кишені', appP: 'На телефоні говориться ще краще. Без реклами – Луна все одно її перебалакала б 😄', appB: 'Завантажити застосунок', appS: 'Безкоштовно · Android, iPhone і комп’ютер',
       notif: 'Сповіщення'}}[lang] || null;
const t = T || {};
const L = k => (T && T[k]) || ({more: 'Więcej', lang: 'Język', menu: 'Więcej opcji'})[k] || k;
const q = lang !== 'pl' ? '?lang=' + lang : '';
let busy = false, on = false;

function dropdown(cls){
  const w = document.createElement('div'); w.className = 'dsk-more ' + cls;
  const id = 'dskm' + Math.random().toString(36).slice(2, 7);
  w.innerHTML = `<button type="button" aria-haspopup="true" aria-expanded="false" aria-controls="${id}"><span>${L('more')}</span><span class="car" aria-hidden="true">▾</span></button><div class="dsk-menu" id="${id}" role="menu" aria-label="${L('menu')}"></div>`;
  const b = w.firstElementChild;
  const set = v => { if (v) w.setAttribute('data-open', ''); else w.removeAttribute('data-open'); b.setAttribute('aria-expanded', v ? 'true' : 'false'); };
  b.addEventListener('click', e => { e.stopPropagation(); const v = !w.hasAttribute('data-open'); document.querySelectorAll('.dsk-more[data-open]').forEach(x => x !== w && x.removeAttribute('data-open')); set(v); if (v){ const f = w.querySelector('.dsk-menu a,.dsk-menu select,.dsk-menu button'); f && f.focus({preventScroll: true}); } });
  w.addEventListener('keydown', e => { if (e.key === 'Escape' && w.hasAttribute('data-open')){ set(false); b.focus(); } });
  w.addEventListener('focusout', e => { if (!w.contains(e.relatedTarget) && e.relatedTarget) set(false); });
  w.menu = w.lastElementChild; w.close = () => set(false);
  return w;
}
document.addEventListener('click', e => { document.querySelectorAll('.dsk-more[data-open]').forEach(w => { if (!w.contains(e.target) || e.target.closest('.dsk-menu a')) w.close(); }); });

/* ---------- 1) nagłówek ---------- */
const acts = header.querySelector('.bar .acts');
const hMore = acts ? dropdown('dsk-hmore') : null;
const KEEP = el => el === hMore || el.matches('[data-push],.dlhead,.pill.primary,.ah-ib,#ibBtn');
let adopted = [];
function adopt(el){
  if (el.matches('select')){ const r = document.createElement('label'); r.className = 'dsk-row'; r.innerHTML = `<span>🌐 ${L('lang')}</span>`; r.appendChild(el); hMore.menu.prepend(r); el.dataset.dskWrap = '1'; }
  else { el.setAttribute('role', 'menuitem'); hMore.menu.appendChild(el); }
  adopted.push(el);
}
function headerOn(){
  if (!acts) return;
  busy = true;
  const prim = acts.querySelector('.pill.primary');
  if (!hMore.isConnected){ if (prim) acts.insertBefore(hMore, prim); else acts.appendChild(hMore); }
  [...acts.children].forEach(el => { if (!KEEP(el)) adopt(el); });
  hMore.hidden = !hMore.menu.children.length;
  acts.querySelectorAll('[data-push]').forEach(bell);
  if (actsObs) actsObs.takeRecords();
  busy = false;
}
function headerOff(){
  if (!acts) return;
  busy = true;
  const first = acts.firstElementChild;
  adopted.forEach(el => { el.removeAttribute('role'); acts.insertBefore(el, first); });
  adopted = []; hMore.menu.querySelectorAll('.dsk-row').forEach(r => r.remove()); hMore.remove();
  acts.querySelectorAll('[data-push]').forEach(b => { b.querySelector('.dsk-tip')?.remove(); b.removeAttribute('data-dsk-state'); });
  if (actsObs) actsObs.takeRecords();
  busy = false;
}
function bell(b){
  const txt = (b.childNodes.length ? [...b.childNodes].filter(n => !(n.nodeType === 1 && n.classList.contains('dsk-tip'))).map(n => n.textContent).join('') : b.textContent).trim();
  if (!txt) return;
  const clean = txt.replace(/^[🔔🔕✓\s]+/u, '');
  b.title = ''; b.setAttribute('aria-label', clean || L('notif'));
  b.setAttribute('data-dsk-state', /zablok|blocked|bloque|blockiert|заблок|niedost|unavailable|no disp|nicht verf|недоступ/i.test(txt) ? 'off' : 'ok');
  let tip = b.querySelector('.dsk-tip');
  if (!tip){ tip = document.createElement('span'); tip.className = 'dsk-tip'; tip.setAttribute('aria-hidden', 'true'); b.appendChild(tip); }
  if (tip.textContent !== clean) tip.textContent = clean;
}
let actsObs = null;
if (acts){
  actsObs = new MutationObserver(ms => {
    if (busy || !on) return;
    busy = true;
    for (const m of ms){
      if (m.target === acts) m.addedNodes.forEach(n => { if (n.nodeType === 1 && !KEEP(n)) adopt(n); });
      const b = m.target.closest && m.target.closest('[data-push]') || (m.target.parentElement && m.target.parentElement.closest('[data-push]'));
      if (b && !(m.addedNodes.length === 1 && m.addedNodes[0].classList && m.addedNodes[0].classList.contains('dsk-tip'))) bell(b);
    }
    if (hMore) hMore.hidden = !hMore.menu.children.length;
    actsObs.takeRecords();
    busy = false;
  });
  actsObs.observe(acts, {childList: true, subtree: true, characterData: true});
}

/* ---------- 2) zakładki: priorytet + „Więcej” ---------- */
const nav = header.querySelector('nav.tabs');
const nMore = nav ? dropdown('dsk-nmore') : null;
let order = [], navObs = null;
function navRestore(){
  if (!nav) return;
  if (!order.length) order = [...nav.children].filter(el => el !== nMore);
  else { const known = new Set(order); [...nav.children, ...nMore.menu.children].forEach(el => { if (el !== nMore && !known.has(el) && el.matches('a')) order.splice(order.length, 0, el); }); }
  order.forEach(el => { el.removeAttribute('role'); nav.insertBefore(el, nMore.isConnected ? nMore : null); });
}
function fit(){
  if (!nav || !on) return;
  busy = true;
  // nowe elementy (np. zakładka Bitew dokładana przez inny skrypt) – zachowaj ich miejsce w kolejności
  [...nav.children].forEach(el => { if (el !== nMore && !order.includes(el)) { const prev = el.previousElementSibling; const i = prev ? order.indexOf(prev) : -1; order.splice(i + 1, 0, el); } });
  navRestore();
  if (!nMore.isConnected) nav.appendChild(nMore);
  nMore.hidden = true;
  const over = () => { const r = nav.getBoundingClientRect(); const cs = getComputedStyle(nav); const right = r.right - parseFloat(cs.paddingRight || 0); return [...nav.children].some(el => !el.hidden && el.getBoundingClientRect().right > right + 1); };
  if (over()){
    nMore.hidden = false;
    const items = [...nav.children].filter(el => el !== nMore);
    for (let i = items.length - 1; i >= 0 && over(); i--){
      const el = items[i]; if (el.classList.contains('on') && i > 0) continue;
      el.setAttribute('role', 'menuitem'); nMore.menu.prepend(el);
    }
    // aktywna zakładka zawsze widoczna (jeśli trafiła do menu)
  }
  nMore.querySelector('button').classList.toggle('on', !!nMore.menu.querySelector('a.on'));
  if (navObs) navObs.takeRecords();   // własne przesunięcia nie wywołują ponownego dopasowania
  busy = false;
}
function navOff(){ if (!nav) return; busy = true; navRestore(); nMore.remove(); if (navObs) navObs.takeRecords(); busy = false; }
if (nav){
  navObs = new MutationObserver(() => { if (!busy && on) requestAnimationFrame(fit); }); navObs.observe(nav, {childList: true});
  new MutationObserver(() => { if (!busy && on && nMore) nMore.querySelector('button').classList.toggle('on', !!nMore.menu.querySelector('a.on')); }).observe(nav, {subtree: true, attributes: true, attributeFilter: ['class']});
}

/* ---------- 3) strona główna: boczna kolumna ---------- */
const hf = document.querySelector('.homebody main.hf');
let rail = null, tb = null, tbAnchor = null;
function railOn(){
  if (!hf || !T) return;
  if (!rail){
    rail = document.createElement('aside'); rail.className = 'dsk-rail'; rail.setAttribute('aria-label', t.quick);
    const dl = (document.querySelector('header .dlhead') || {}).getAttribute ? document.querySelector('header .dlhead').getAttribute('href') : '#pobierz';
    rail.innerHTML = `<div class="dsk-card"><h3>${t.quick}</h3><p>${t.quickP}</p><nav class="dsk-links" aria-label="${t.quick}">
      <a href="/bitwy.html${q}">${t.bitwy}</a><a href="/ranking.html${q}">${t.rank}</a><a href="/butik.html${q}">${t.butik}</a>
      <a href="/galeria.html${q}">${t.gal}</a><a href="/scianka.html${q}">${t.wall}</a><a href="/problemy.html${q}">${t.help}</a></nav></div>
      <div class="dsk-card no-twa"><h3>${t.appH}</h3><p>${t.appP}</p><a class="pill primary" href="${dl || '#pobierz'}">${t.appB}</a><small>${t.appS}</small></div>`;
  }
  tb = hf.querySelector(':scope > .tester-banner');
  if (tb && !tb.hidden){ tbAnchor = tb.nextElementSibling; rail.prepend(tb); }
  const hero = hf.querySelector(':scope > .sc') || hf.querySelector(':scope > .star-hero');   /* v1.7: kolumna obok Ścianki, pod wizytówką */
  hf.insertBefore(rail, hero ? hero.nextElementSibling : hf.firstElementChild);
  span();
}
function span(){
  if (!rail || !rail.isConnected) return;
  let n = 0, before = 0, seen = false;
  [...hf.children].forEach(el => { if (el === rail){ seen = true; return; } const vis = getComputedStyle(el).display !== 'none'; if (!vis) return; if (seen) n++; else before++; });
  rail.style.gridRow = `${before + 1} / span ${Math.max(1, n)}`;
}
function railOff(){
  if (!rail) return;
  if (tb && rail.contains(tb)){ hf.insertBefore(tb, tbAnchor && tbAnchor.parentNode === hf ? tbAnchor : hf.querySelector(':scope > .star-hero')); }
  rail.remove();
}
if (hf) new MutationObserver(() => { if (on) span(); }).observe(hf, {childList: true});

/* ---------- przełączanie ---------- */
const hdrVar = () => document.documentElement.style.setProperty('--dsk-hdr', header.offsetHeight + 'px');
function apply(){
  if (mq.matches){ on = true; headerOn(); fit(); railOn(); hdrVar(); }
  else if (on){ on = false; headerOff(); navOff(); railOff(); document.documentElement.style.removeProperty('--dsk-hdr'); }
}
let rt = 0;
addEventListener('resize', () => { cancelAnimationFrame(rt); rt = requestAnimationFrame(() => { if (on){ fit(); hdrVar(); } }); });
mq.addEventListener ? mq.addEventListener('change', apply) : mq.addListener(apply);
const refit = () => { if (on){ fit(); hdrVar(); span(); } };
if (document.fonts && document.fonts.addEventListener) document.fonts.addEventListener('loadingdone', refit);
const start = () => { apply(); [400, 1500, 3500].forEach(ms => setTimeout(refit, ms)); if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => on && (fit(), hdrVar())); addEventListener('load', () => on && (fit(), hdrVar(), span())); };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
