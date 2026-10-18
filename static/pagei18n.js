/* Proste przełączanie języka na stronach informacyjnych: <script type="application/json" id="i18n">{pl:{klucz:html},en:{…}}</script> */
(() => {
const el = document.getElementById('i18n'); if (!el) return;
const D = JSON.parse(el.textContent); const langs = Object.keys(D);
let l = 'pl'; try { l = (new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2).toLowerCase(); } catch(e){}
if (!D[l]) l = 'pl';
function apply(lang){
  const d = Object.assign({}, D.pl, D[lang] || {});
  document.querySelectorAll('[data-i18n]').forEach(e => { const k = e.dataset.i18n; if (d[k] != null) e.innerHTML = d[k]; });
  document.querySelectorAll('[data-i18n-ph]').forEach(e => { const k = e.dataset.i18nPh; if (d[k] != null) e.placeholder = d[k]; });
  document.querySelectorAll('.langtabs button').forEach(b => b.classList.toggle('on', b.dataset.lang === lang));
  document.documentElement.lang = lang;
  if (d._title) document.title = d._title;
  window.LunaDisclaimerLang && window.LunaDisclaimerLang(lang);
  window.dispatchEvent(new CustomEvent('luna-lang', {detail: lang}));
}
document.querySelectorAll('.langtabs button').forEach(b => b.onclick = () => { try { localStorage.setItem('luna.lang', b.dataset.lang); } catch(e){} apply(b.dataset.lang); });
apply(l);
window.LunaPageLang = () => document.documentElement.lang;
})();
