/* „🛡️ Panel admina” / „🛡️ Panel moderatora” – serwer dołącza ten skrypt WYŁĄCZNIE do stron kont z rolą admin lub moderator (inni: 404). */
(() => {
const P = '__P__';
const app = (() => { try { return document.documentElement.classList.contains('twa') || sessionStorage.getItem('luna.twa') === '1' || (matchMedia && matchMedia('(display-mode: standalone)').matches); } catch (e) { return false; } })();
const href = P + (app ? '/app' : '/');
const ROLE = '__ROLE__';   /* rola z serwera: admin albo moderator */
const TX = ROLE === 'moderator' ? {
  pl: ['Panel moderatora', 'Czat, użytkownicy, Butik i wsparcie – widoczne tylko dla ekipy'],
  en: ['Moderator panel', 'Chat, users, shop and support – visible to the team only'],
  es: ['Panel de moderación', 'Chat, usuarios, tienda y soporte – solo para el equipo'],
  de: ['Moderations-Panel', 'Chat, Nutzer, Shop und Support – nur fürs Team sichtbar'],
  uk: ['Панель модератора', 'Чат, користувачі, магазин і підтримка – бачить лише команда'],
} : {
  pl: ['Panel admina', 'Przełączniki, kolejka, użytkownicy, komunikaty – widoczne tylko dla Ciebie'],
  en: ['Admin panel', 'Switches, queue, users, announcements – visible only to you'],
  es: ['Panel de admin', 'Interruptores, cola, usuarios, avisos – solo lo ves tú'],
  de: ['Admin-Panel', 'Schalter, Warteschlange, Nutzer, Mitteilungen – nur für dich sichtbar'],
  uk: ['Панель адміна', 'Перемикачі, черга, користувачі, оголошення – бачиш лише ти'],
};
const tx = () => TX[(document.documentElement.lang || 'pl').slice(0, 2)] || TX.pl;
const LBL = '🛡️ ' + tx()[0];
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
  head.insertAdjacentHTML('afterend', `<section class="st-g" id="stModRow"><div class="st-list"><a class="st-row" href="${href}"><span class="st-ic" aria-hidden="true">🛡️</span><span class="st-tx"><b>${tx()[0]}</b><small>${tx()[1]}</small></span><span class="st-chev" aria-hidden="true">›</span></a></div></section>`);
}
function run(){ nav(); panelRow(); }
window.addEventListener('luna-lang', () => { document.querySelectorAll('.mod-tab').forEach(a => a.textContent = '🛡️ ' + tx()[0]); const r = document.getElementById('stModRow'); if (r) { r.remove(); panelRow(); } });
const go = () => { run(); const st = document.getElementById('stApp'); if (st) new MutationObserver(panelRow).observe(st, {childList: true}); };
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', go) : go();
})();
