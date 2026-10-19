/* Publiczny numer wersji (5 języków): do końca testów aplikacja jest przedstawiana jako „wersja 0.02 (testy)”.
   Wewnętrzny numer wydania (VERSION w server.py, /api/health) się nie zmienia i nie jest pokazywany użytkownikom.
   Wstawiane: stopka strony (pod ©), stopka aplikacji i karta „O aplikacji” w ustawieniach (obok „Co nowego”). */
(() => {
if (window.LunaPublicVersion) return;
const V = '0.02';
const T = {pl: `wersja ${V} (testy)`, en: `version ${V} (beta testing)`, es: `versión ${V} (fase de pruebas)`, de: `Version ${V} (Testphase)`, uk: `версія ${V} (тестування)`};
const lang = () => { let l = document.documentElement.lang || 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || l; } catch(e){} l = String(l).slice(0, 2); return T[l] ? l : 'pl'; };
const label = () => T[lang()];
window.LunaPublicVersion = {v: V, label};
if (!document.getElementById('pubVerCss')){ const st = document.createElement('style'); st.id = 'pubVerCss';
  st.textContent = '.pubver{display:inline-block;margin:6px 0 0;padding:1px 9px;border-radius:999px;border:1px solid rgba(255,255,255,.16);color:#cfcfcf;font-size:11.5px;line-height:1.5;letter-spacing:.02em;font-variant-numeric:tabular-nums}'
  + 'p.pubver-row{margin:4px 0 0;text-align:center}.appfoot p.pubver-row{margin:2px 0 0}#settings p.pubver-row{text-align:left}';
  document.head.appendChild(st); }
function row(){ const p = document.createElement('p'); p.className = 'pubver-row'; p.innerHTML = '<span class="pubver"></span>'; p.firstChild.textContent = label(); return p; }
function place(){
  const sf = document.querySelector('footer.sitefoot'); if (sf && !sf.querySelector('.pubver')) sf.appendChild(row());
  const af = document.querySelector('footer.appfoot'); if (af && !af.querySelector('.pubver')) af.appendChild(row());
  const nl = document.querySelector('#settings [data-news]'); const fs = nl && nl.closest('fieldset');
  if (fs && !fs.querySelector('.pubver')) fs.appendChild(row());
  if (!sf && !af && !document.querySelector('.pubver')){ const f = document.querySelector('footer'); if (f) f.appendChild(row()); }
}
const go = () => place();
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
window.addEventListener('luna-lang', () => document.querySelectorAll('.pubver').forEach(e => { e.textContent = label(); }));
})();
