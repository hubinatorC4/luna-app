/* Luna – aplikacja v1.4: dolne menu (Ścianka, Luna, Butik, Premium, Więcej), wprowadzenie, wskazówki, ceny i płatności.
   Ścianka (strona główna), Luna i Butik to te same strony co w serwisie (to samo API, te same polubienia, komentarze i liczniki) – osadzone bez nagłówka strony. */
(() => {
const LS = ['pl', 'en', 'es', 'de', 'uk'];
const qs = new URLSearchParams(location.search);
let lang = qs.get('lang') || (() => { try { return localStorage.getItem('luna.lang'); } catch(e){ return null; } })() || (navigator.language || 'pl').slice(0, 2).toLowerCase();
if (!LS.includes(lang)) lang = 'pl';
try { localStorage.setItem('luna.lang', lang); } catch(e){}
const T = Object.assign({}, window.LUNA_APP_T.pl, window.LUNA_APP_T[lang]);
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const TWA = document.documentElement.classList.contains('twa');
const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch(e){ return null; } };
document.documentElement.lang = lang;
document.querySelectorAll('[data-t]').forEach(el => { const v = T[el.dataset.t]; if (typeof v === 'string') el.textContent = v; });
document.querySelectorAll('[data-t-aria]').forEach(el => { el.setAttribute('aria-label', T[el.dataset.tAria]); el.title = T[el.dataset.tAria]; });
const withLang = p => { const u = new URL(p, location.origin); if (lang !== 'pl') u.searchParams.set('lang', lang); return u.pathname + u.search + u.hash; };
const toast = t => { const el = $('#toast'); el.textContent = t; el.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(() => el.hidden = true, 2600); };

/* ---------- osadzone strony ---------- */
const SITE_CSS = `header.top{display:none!important}`;
const FRAME_CSS = `.sitefoot,footer.sitefoot,.hb-fab,.hb-win,.lswitch,.apk-btn,.apk-hint,.dl-sec,#pobierz,.wallpage>.hero,.appfoot .fan,.appfoot>p:last-child{display:none!important}
body{padding-bottom:24px!important;font-size:17px}body.site{padding-top:0!important}
.app-sup{margin:0 0 16px}.app-sup .acts{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.app-sup .acts .btn{flex:1 1 140px;width:auto}.app-sup .x{float:right;background:none;border:0;color:inherit;opacity:.6;font-size:18px;cursor:pointer}`;
function route(href){
  let u; try { u = new URL(href, location.origin); } catch(e){ return false; }
  if (u.origin !== location.origin) return false;
  const p = u.pathname;
  if (p === '/' || p === '/index.html'){ show('luna'); if (u.hash === '#live') frameOf('luna', '#live'); return true; }
  if (p === '/butik.html'){ show('butik'); if (u.hash) frameOf('butik', u.hash); return true; }
  if (p === '/scianka.html' && !u.searchParams.get('post')){ show('feed'); return true; }
  if (p === '/promo.html' && /^#(plany|cennik|plans)$/.test(u.hash)){ show('plans'); return true; }
  if (p === '/promo.html' && !u.hash){ show('feed'); return true; }
  if (p === '/app.html'){ const t = (u.hash || '').slice(1); if (TABS.includes(t)) show(t); return true; }
  if (/\.html$/.test(p) && !p.startsWith('/api/')){ openPage(p + u.search + u.hash); return true; }
  return false;
}
function prep(fr, tab){
  let d; try { d = fr.contentDocument; } catch(e){ return; }
  if (!d || !d.documentElement || d.documentElement.dataset.appShell) return;
  d.documentElement.dataset.appShell = '1'; d.documentElement.classList.add('in-app');
  try { /* płatność Stripe zawsze w głównym oknie (Stripe nie działa w ramce) */
    const w = fr.contentWindow, f0 = w.fetch.bind(w);
    w.fetch = async (u, o) => { const r = await f0(u, o); if (String(u).includes('/api/pay/checkout') && r.ok){ const d = await r.clone().json().catch(() => ({})); if (d.url){ location.assign(d.url); return new Promise(() => {}); } } return r; };
  } catch(e){}
  const isLuna = ['/', '/index.html', '/live.html'].includes(fr.contentWindow.location.pathname);
  const st = d.createElement('style'); st.textContent = FRAME_CSS + (isLuna ? '' : SITE_CSS); (d.head || d.documentElement).appendChild(st);
  d.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href]'); if (!a || e.defaultPrevented || a.target === '_blank' || a.hasAttribute('download')) return;
    const h = a.getAttribute('href'); if (!h || h.startsWith('#') || h.startsWith('javascript:')) return;
    const u = new URL(a.href, location.origin);
    if (u.origin === location.origin && u.pathname === fr.contentWindow.location.pathname && u.hash) return;
    if (route(a.href)) e.preventDefault();
  }, true);
  if (tab === 'feed') supportCard(d);
}
function frameOf(tab, hash){
  const host = $('#p-' + tab); let fr = host.querySelector('iframe');
  if (!fr){
    fr = document.createElement('iframe'); fr.title = T['tab_' + tab] || 'Luna';
    fr.setAttribute('allow', 'microphone; autoplay; clipboard-write; web-share');
    fr.addEventListener('load', () => prep(fr, tab));
    let src = withLang(host.dataset.frame);
    if (tab === 'luna' && qs.get('platnosc')) src += '&platnosc=' + encodeURIComponent(qs.get('platnosc')) + (qs.get('session_id') ? '&session_id=' + encodeURIComponent(qs.get('session_id')) : '');
    fr.src = src + (hash || ''); host.appendChild(fr);
    const iv = setInterval(() => { prep(fr, tab); if (fr.contentDocument && fr.contentDocument.readyState === 'complete') clearInterval(iv); }, 120);
    setTimeout(() => clearInterval(iv), 15000);
  } else if (hash){ try { fr.contentWindow.location.hash = hash; } catch(e){} }
  return fr;
}
function openPage(path){
  const host = $('#p-page'); host.innerHTML = `<div class="backbar"><button type="button" id="pgBack">${esc(T.back)}</button></div>`;
  const fr = document.createElement('iframe'); fr.title = 'Luna'; fr.setAttribute('allow', 'microphone; autoplay; clipboard-write; web-share');
  fr.addEventListener('load', () => prep(fr, 'page')); fr.src = withLang(path); host.appendChild(fr);
  $('#pgBack').onclick = () => show(prevTab || 'more');
  show('page');
}

/* ---------- zakładki ---------- */
const TABS = ['feed', 'luna', 'butik', 'plans', 'more'];
let cur = null, prevTab = null;
function show(tab){
  if (tab !== 'page' && !TABS.includes(tab)) tab = 'feed';
  if (cur && cur !== 'page') prevTab = cur;
  cur = tab;
  document.querySelectorAll('.panel').forEach(p => p.hidden = p.id !== 'p-' + tab);
  document.querySelectorAll('#tabbar button').forEach(b => { const on = b.dataset.tab === tab; b.classList.toggle('on', on); b.setAttribute('aria-current', on ? 'page' : 'false'); });
  const host = $('#p-' + tab);
  if (host.dataset.frame) frameOf(tab);
  if (tab === 'plans' && !host.dataset.ready) renderPlans();
  if (tab === 'more' && !host.dataset.ready) renderMore();
  if (tab !== 'page') { history.replaceState(null, '', location.pathname + location.search + '#' + tab); tip(tab); }
}
document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); show(b.dataset.tab); }));
$('#helpBtn').onclick = () => { show('more'); setTimeout(() => { const h = $('#howH'); if (h) h.scrollIntoView({behavior: 'smooth'}); }, 50); };

/* ---------- wskazówki (małe, do zamknięcia, raz na zakładkę) ---------- */
function tip(tab){
  const host = $('#p-' + tab); if (tab === 'plans' || !T.tip[tab] || store('luna.app.tip.' + tab) || host.querySelector('.tip[role=note]') || !store('luna.app.onb')) return;
  const el = document.createElement('div'); el.className = host.dataset.frame ? 'tip float' + (tab === 'luna' ? ' bottom' : '') : 'tip'; el.setAttribute('role', 'note');
  el.innerHTML = `<span>💡</span><span>${esc(T.tip[tab])}</span><button type="button" aria-label="${esc(T.close)}">✕</button>`;
  el.querySelector('button').onclick = () => { store('luna.app.tip.' + tab, '1'); el.remove(); };
  if (host.dataset.frame) host.prepend(el); else (host.querySelector('.wrapc') || host).prepend(el);
}

/* ---------- wprowadzenie (3–4 kroki, do pominięcia) ---------- */
function onboarding(){
  let i = 0; const box = $('#onb'); box.hidden = false;
  const draw = () => { const [ico, h, p] = T.onb[i]; $('#onbIco').textContent = ico; $('#onbH').textContent = h; $('#onbP').textContent = p;
    $('#onbDots').innerHTML = T.onb.map((_, k) => `<i class="${k === i ? 'on' : ''}"></i>`).join(''); $('#onbNext').textContent = i === T.onb.length - 1 ? T.start : T.next; };
  const done = () => { store('luna.app.onb', '1'); box.hidden = true; tip(cur); };
  $('#onbSkip').onclick = done; $('#onbNext').onclick = () => { if (++i >= T.onb.length) done(); else draw(); };
  document.addEventListener('keydown', function k(e){ if (e.key === 'Escape' && !box.hidden){ done(); document.removeEventListener('keydown', k); } });
  draw(); $('#onbNext').focus();
}

/* ---------- jedna karta wsparcia w kanale (do zamknięcia) ---------- */
function shareLuna(){
  const url = location.origin + '/' + (lang !== 'pl' ? '?lang=' + lang : '');
  if (navigator.share) navigator.share({title: 'Luna', text: T.share_t, url}).catch(() => {});
  else if (navigator.clipboard) navigator.clipboard.writeText(T.share_t + ' ' + url).then(() => toast(T.copied)).catch(() => {});
}
function supportCard(d){
  if (store('luna.app.sup') || d.querySelector('.app-sup')) return;
  const feed = d.getElementById('feedHost') || d.getElementById('feed'); if (!feed) return;
  const place = () => {
    if (d.querySelector('.app-sup')) return true;
    const posts = [...feed.children].filter(c => !c.classList.contains('app-sup'));
    if (posts.length < 3) return false;
    const c = d.createElement('article'); c.className = 'card post app-sup';
    c.innerHTML = `<button type="button" class="x" aria-label="${esc(T.close)}">✕</button><h3 style="margin:0 0 4px">${esc(T.sup_h)}</h3><p style="margin:0">${esc(T.sup_p)}</p>
      <div class="acts"><button type="button" class="btn sm primary" data-a="plans">${esc(T.sup_plans)}</button><button type="button" class="btn sm" data-a="share">${esc(T.sup_share)}</button></div>`;
    c.querySelector('.x').onclick = () => { store('luna.app.sup', '1'); c.remove(); };
    c.querySelector('[data-a=plans]').onclick = () => show('plans');
    c.querySelector('[data-a=share]').onclick = shareLuna;
    posts[2].after(c); return true;
  };
  if (!place()){ const mo = new MutationObserver(() => { if (place()) mo.disconnect(); }); mo.observe(feed, {childList: true}); }
}

/* ---------- Premium: ceny, porównanie, płatności ---------- */
const DEF = {podstawowa: '0', premium: '59,99', pro: '99,99'};
const NAMES = {pl: {podstawowa: 'Podstawowa', premium: 'Premium', pro: 'Pro'}, en: {podstawowa: 'Basic'}, es: {podstawowa: 'Básico'}, de: {podstawowa: 'Basis'}, uk: {podstawowa: 'Базовий'}};
const pname = id => (NAMES[lang] && NAMES[lang][id]) || NAMES.pl[id];
const zl = v => { const s = String(v).replace('.', ','); return lang === 'en' ? s.replace(',', '.') : s; };
async function getJSON(u){ const r = await fetch(u, {credentials: 'same-origin'}); if (!r.ok) throw new Error(r.status); return r.json(); }
async function renderPlans(){
  const host = $('#p-plans'); host.dataset.ready = '1';
  host.innerHTML = `<div class="wrapc"><p class="loading">${esc(T.loading)}</p></div>`;
  const [cat, me, bk] = await Promise.all([getJSON('/api/catalog').catch(() => ({})), getJSON('/api/account/me').catch(() => ({})), getJSON('/api/butik').catch(() => ({}))]);
  const pr = {}; (cat.plans || []).forEach(p => { if (p.prices && p.prices.pln != null) pr[p.id] = p.prices.pln; });
  const price = id => pr[id] != null ? pr[id] : DEF[id];
  const user = me.user || null, csrf = me.csrf || '', myPlan = user && user.plan;
  const web = !!(bk.payments && bk.payments.web);
  const card = (id, hl) => {
    const free = Number(String(price(id)).replace(',', '.')) <= 0;
    const isMine = myPlan === id;
    const act = isMine ? `<button class="btn full" disabled>✓ ${esc(T.cur_plan)}</button>`
      : free ? (user ? '' : `<button class="btn full" data-go="account">${esc(T.free_btn)}</button>`)
      : `<button class="btn ${hl ? 'primary' : ''} full" data-buy="${id}">${esc(T.choose)} ${esc(pname(id))}</button>`;
    return `<div class="plan ${hl ? 'hl' : ''}">${hl ? `<span class="badge">${esc(T.rec)}</span>` : ''}<h3>${esc(pname(id))}</h3>
      <div class="price">${free ? esc(T.free) : `${zl(price(id))} <small>zł</small>`}</div>
      <div class="pnote">${free ? esc(T.free_note) : `${esc(T.per)} · ${esc(T.pass_note)}`}</div>
      <ul>${T.feat[id].map(f => `<li>${esc(f)}</li>`).join('')}</ul>${act}</div>`;
  };
  const yn = v => v === 1 ? '<td class="y">✓</td>' : v === 0 ? '<td class="n">–</td>' : `<td>${esc(v)}</td>`;
  const status = TWA ? T.soon_twa : !web ? T.soon_web : !user ? T.login : '';
  host.innerHTML = `<div class="wrapc">
    <h1 class="t">${esc(T.plans_h)}</h1><p class="lead">${esc(T.plans_lead)}</p>
    <div class="chips">${T.chips.map(c => `<span class="chip">✓ ${esc(c)}</span>`).join('')}</div>
    <div class="plans">${card('podstawowa')}${card('premium', true)}${card('pro')}</div>
    <p class="small">${esc(T.nolog)}</p>
    <details class="more"><summary>${esc(T.cmp_sum)}</summary>
      <table class="cmp"><thead><tr><th></th><th>${esc(pname('podstawowa'))}</th><th>Premium</th><th>Pro</th></tr></thead>
      <tbody>${T.cmp.map(r => `<tr><td>${esc(r[0])}</td>${yn(r[1])}${yn(r[2])}${yn(r[3])}</tr>`).join('')}</tbody></table></details>
    <div class="card" id="payBox"><h2 class="t" style="font-size:22px">${esc(T.pay_h)}</h2>
      <ul style="list-style:none;padding:0;margin:0 0 10px">${T.pay.map(p => `<li style="margin:6px 0">${esc(p)}</li>`).join('')}</ul>
      ${status ? `<div class="tip" role="status"><span>ℹ️</span><span>${esc(status)}</span></div>${!TWA && web && !user ? `<button class="btn" data-go="account">${esc(T.go_login)}</button>` : ''}` :
        `<label style="display:flex;gap:10px;align-items:flex-start;font-size:15px"><input type="checkbox" id="payConsent" style="margin-top:4px;width:20px;height:20px"> <span>${esc(T.consent)}</span></label><p class="small" id="payMsg" role="status"></p>`}
    </div>
    <details class="more"><summary>${esc(T.pay_more)}</summary><p>${esc(T.pay_more_p)}</p>
      <p><a href="/regulamin.html" data-page>${esc(T.terms)}</a> · <a href="/privacy.html" data-page>${esc(T.privacy)}</a></p></details>
  </div>`;
  tip('plans');
  host.querySelectorAll('[data-go=account]').forEach(b => b.onclick = openAccount);
  host.querySelectorAll('a[data-page]').forEach(a => a.onclick = e => { e.preventDefault(); openPage(a.getAttribute('href')); });
  host.querySelectorAll('[data-buy]').forEach(b => b.onclick = async () => {
    if (status){ $('#payBox').scrollIntoView({behavior: 'smooth', block: 'center'}); return; }
    const msg = $('#payMsg');
    if (!$('#payConsent').checked){ msg.textContent = T.consent_need; $('#payConsent').focus(); return; }
    b.disabled = true;
    try {
      const r = await fetch('/api/pay/checkout', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify({kind: 'pass', ref: b.dataset.buy, consent_immediate: true, twa: TWA})});
      const d = await r.json().catch(() => ({}));
      if (r.ok && d.url){ location.href = d.url; return; }
      msg.textContent = d.error || T.pay_err;
    } catch(e){ msg.textContent = T.pay_err; }
    b.disabled = false;
  });
}
function openAccount(){
  show('luna');
  const fr = frameOf('luna');
  const go = () => { try { const d = fr.contentDocument; const s = d.getElementById('settings'); if (!s) return false;
    const sb = d.getElementById('settingsBtn'); if (!sb || !sb.onclick) return false; if (!s.open) sb.click();
    const a = d.getElementById('acctSection'); if (a) a.scrollIntoView({block: 'start'}); return true; } catch(e){ return false; } };
  if (!go()){ let n = 0; const iv = setInterval(() => { if (go() || ++n > 60) clearInterval(iv); }, 150); }
}

/* ---------- Więcej: Jak korzystać, pomoc i kontakt, linki ---------- */
function renderMore(){
  const host = $('#p-more'); host.dataset.ready = '1';
  host.innerHTML = `<div class="wrapc">
    <h1 class="t">${esc(T.more_h)}</h1>
    <ul class="menu"><li><button type="button" data-chat><span>${esc(T.help_h)}<small>${esc(T.help_s)}</small></span></button></li>
      <li><a href="/problemy.html" data-page>${esc(T.problems)}</a></li></ul>
    <h2 class="t" id="howH" style="font-size:22px">${esc(T.how_h)}</h2>
    ${T.how.map(([h, p]) => `<details class="more"><summary>${esc(h)}</summary><p>${esc(p)}</p></details>`).join('')}
    <ul class="menu"><li><button type="button" id="replay">${esc(T.replay)}</button></li></ul>
    <h2 class="t" style="font-size:22px">${esc(T.links_h)}</h2>
    <ul class="menu">${T.links.map(([h, l]) => `<li><a href="${h}" data-page>${esc(l)}</a></li>`).join('')}
      <li><a href="/regulamin.html" data-page>📄 ${esc(T.terms)}</a></li><li><a href="/privacy.html" data-page>🔒 ${esc(T.privacy)}</a></li></ul>
    <p class="small" style="text-align:center">${esc(T.foot)}</p></div>`;
  host.querySelectorAll('a[data-page]').forEach(a => a.onclick = e => { e.preventDefault(); openPage(a.getAttribute('href')); });
  host.querySelector('[data-chat]').onclick = () => route('/#live');
  $('#replay').onclick = () => { show('feed'); onboarding(); };
}

/* ---------- start ---------- */
const h = location.hash.slice(1);
show(qs.get('platnosc') ? 'luna' : TABS.includes(h) ? h : 'feed');
if (!store('luna.app.onb')) onboarding();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
})();
