/* „🛡️ Panel moderatora” – ten skrypt serwer dołącza WYŁĄCZNIE do stron konta z rolą admin (inni go nie dostają: 404). */
(() => {
const P = '__P__';
const app = (() => { try { return document.documentElement.classList.contains('twa') || sessionStorage.getItem('luna.twa') === '1' || (matchMedia && matchMedia('(display-mode: standalone)').matches); } catch (e) { return false; } })();
const href = P + (app ? '/app' : '/');
const LBL = '🛡️ Panel moderatora';
function nav(){
  if (document.querySelector('.mod-tab')) return true;
  const n = document.querySelector('header.top nav.tabs, header.nav .links, header .tabs, header nav');
  if (n){ const a = document.createElement('a'); a.className = 'mod-tab'; a.href = href; a.textContent = LBL; n.appendChild(a); return true; }
  const h = document.querySelector('header.ah, header.top, header');
  if (h){ const a = document.createElement('a'); a.className = 'mod-tab mod-tab-pill'; a.href = href; a.textContent = LBL; h.appendChild(a); return true; }
  return false;
}
function panelRow(){
  const head = document.getElementById('stHead');
  if (!head || document.getElementById('stModRow')) return;
  head.insertAdjacentHTML('afterend', `<section class="st-g" id="stModRow"><div class="st-list"><a class="st-row" href="${href}"><span class="st-ic" aria-hidden="true">🛡️</span><span class="st-tx"><b>Panel moderatora</b><small>Przełączniki, kolejka, użytkownicy, komunikaty – widoczne tylko dla Ciebie</small></span><span class="st-chev" aria-hidden="true">›</span></a></div></section>`);
}
function run(){ nav(); panelRow(); }
const go = () => { run(); const st = document.getElementById('stApp'); if (st) new MutationObserver(panelRow).observe(st, {childList: true}); };
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', go) : go();
})();
