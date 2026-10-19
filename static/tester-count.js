/* Licznik testerów w stopce (5 języków): „🎟️ Testerzy: N / 1000”.
   Prawdziwe dane z tego samego źródła co pasek „Szukamy 1000 testerów” i przycisk w aplikacji: GET /api/testers
   (N = limit − remaining = zgłoszenia przyjęte do testów). Bez nowych endpointów; wynik w sessionStorage na 5 min,
   więc kolejne strony nie odpytują serwera. Przy błędzie licznik się nie pokazuje (żadnych zmyślonych liczb). */
(() => {
if (window.LunaTesterCount) return;
const T = {
  pl: {l: 'Testerzy', j: 'Dołącz', a: 'Testerzy Luny: {n} z {m} miejsc zajętych. Dołącz do testów'},
  en: {l: 'Testers', j: 'Join', a: 'Luna testers: {n} of {m} places taken. Join the tests'},
  es: {l: 'Testers', j: 'Únete', a: 'Testers de Luna: {n} de {m} plazas ocupadas. Únete a las pruebas'},
  de: {l: 'Tester', j: 'Mitmachen', a: 'Luna-Tester: {n} von {m} Plätzen vergeben. Jetzt mittesten'},
  uk: {l: 'Тестувальники', j: 'Долучитися', a: 'Тестувальники Luna: зайнято {n} з {m} місць. Долучитися до тестів'}
};
const lang = () => { let l = document.documentElement.lang || 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || l; } catch(e){} l = String(l).slice(0, 2); return T[l] ? l : 'pl'; };
const K = 'luna.tcnt', TTL = 5 * 60e3;
function load(){
  try { const c = JSON.parse(sessionStorage.getItem(K) || 'null'); if (c && Date.now() - c.at < TTL && c.limit > 0) return Promise.resolve(c); } catch(e){}
  return fetch('/api/testers', {credentials: 'same-origin'}).then(r => r.ok ? r.json() : Promise.reject(r.status)).then(d => {
    const limit = +d.limit, rem = +d.remaining; if (!(limit > 0) || !(rem >= 0)) throw 0;
    const c = {limit, n: Math.max(0, limit - rem), at: Date.now()}; try { sessionStorage.setItem(K, JSON.stringify(c)); } catch(e){} return c;
  });
}
if (!document.getElementById('tcountCss')){ const st = document.createElement('style'); st.id = 'tcountCss';
  st.textContent = '.tcount{display:flex;justify-content:center;margin:10px 0 6px}'
  + '.tcount a{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid rgba(255,179,92,.28);color:#e9e2d8!important;font-size:12.5px;line-height:1.3;text-decoration:none!important;font-variant-numeric:tabular-nums}'
  + '.tcount a:hover,.tcount a:focus-visible{border-color:#ffb35c;background:rgba(255,179,92,.1)}'
  + '.tcount b{color:#fff;font-weight:700}.tcount u{text-decoration:none;color:#ffb35c;font-weight:700}'
  + '.tcount i{display:inline-block;width:46px;height:4px;border-radius:4px;background:rgba(255,255,255,.14);overflow:hidden}.tcount i s{display:block;height:100%;min-width:2px;background:linear-gradient(90deg,#3DDC97,#ffb35c);text-decoration:none}'
  + '.appfoot .tcount{margin:0 0 3px;line-height:16px}.appfoot .tcount a{padding:0 9px;font-size:11px;line-height:16px;gap:5px}.appfoot .tcount i{display:none}'
  + '@media (max-width:600px){.appfoot .tcount{display:none}}'   /* w aplikacji na telefonie stopka jest ściśnięta – tam licznik pokazuje pasek testerów u góry */
  + '.tcount-solo{margin:18px auto 22px}';
  document.head.appendChild(st); }
function html(c){
  const t = T[lang()], q = lang() !== 'pl' ? '?lang=' + lang() : '', pct = Math.min(100, c.n / c.limit * 100);
  return `<a href="/testerzy.html${q}" aria-label="${t.a.replace('{n}', c.n).replace('{m}', c.limit)}"><span aria-hidden="true">🎟️</span><span>${t.l}: <b>${c.n}</b> / ${c.limit}</span><i aria-hidden="true"><s style="width:${pct.toFixed(1)}%"></s></i><u aria-hidden="true">${t.j} →</u></a>`;
}
function place(c){
  if (document.querySelector('.tcount')) { document.querySelectorAll('.tcount').forEach(e => e.innerHTML = html(c)); return; }
  const el = document.createElement('p'); el.className = 'tcount'; el.innerHTML = html(c);
  const sf = document.querySelector('footer.sitefoot'), af = document.querySelector('footer.appfoot');
  if (sf){ const anchor = sf.querySelector('.owner') || sf.querySelector('.copy'); anchor ? sf.insertBefore(el, anchor) : sf.appendChild(el); return; }
  if (af){ el.classList.add('tcount-app'); af.insertBefore(el, af.firstChild); return; }
  const f = document.querySelector('footer'); if (f){ f.appendChild(el); return; }
  el.classList.add('tcount-solo'); (document.querySelector('main') || document.body).appendChild(el);
}
let last = null;
const run = () => load().then(c => { last = c; place(c); }).catch(() => {});
window.LunaTesterCount = {refresh: () => { try { sessionStorage.removeItem(K); } catch(e){} return run(); }};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
window.addEventListener('luna-lang', () => { if (last) place(last); });
})();
