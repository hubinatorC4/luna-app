/* Ramka moderatora: błyskawica ⚡ co ~8–12 s (tylko transform/opacity), pauza poza ekranem, prefers-reduced-motion = statyczna poświata.
   Elementy .mod-av powstają wyłącznie z flagi serwera „mod” (konto z rolą admin). Ogłoszenie „Co nowego”: przeniesienie pod nagłówek i zamykanie. */
(() => {
const RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
const BOLT = '<svg class="mod-bolt" viewBox="0 0 40 90" aria-hidden="true"><defs><linearGradient id="mbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#bcd6ff"/><stop offset="1" stop-color="#3D7BFF"/></linearGradient></defs><path d="M24 2 6 50h13L12 88 35 34H22L30 2z" fill="url(#mbg)" stroke="#e8f0ff" stroke-width="1.2" stroke-linejoin="round"/></svg>';
const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => {
  const el = e.target, v = el.querySelector('video');
  el.classList.toggle('mod-off', !e.isIntersecting);
  if (v){ if (e.isIntersecting && !RM) { const p = v.play(); if (p && p.catch) p.catch(() => {}); } else v.pause(); }
}), {rootMargin: '60px'}) : null;
function enhance(el){
  if (el.dataset.mr) return; el.dataset.mr = '1';
  el.style.setProperty('--dur', (8 + Math.random() * 4).toFixed(2) + 's');
  el.style.setProperty('--d', (Math.random() * 6 + .5).toFixed(2) + 's');
  const img = el.querySelector('img');
  if (!RM && img){
    const v = document.createElement('video');
    v.muted = true; v.defaultMuted = true; v.loop = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.setAttribute('muted', ''); v.autoplay = true;
    v.preload = 'metadata'; v.poster = '/mod-av/mustang-512.jpg'; v.setAttribute('aria-hidden', 'true'); v.width = img.width || 40; v.height = img.height || 40;
    v.innerHTML = '<source src="/mod-av/mustang-512.webm" type="video/webm"><source src="/mod-av/mustang-512.mp4" type="video/mp4">';
    v.addEventListener('error', () => { if (v.parentNode) v.replaceWith(img); }, {once: true});
    img.replaceWith(v);
  }
  el.insertAdjacentHTML('beforeend', BOLT);
  if (io) io.observe(el);
}
let q = 0;
const scan = () => { q = 0; document.querySelectorAll('.mod-av:not([data-mr])').forEach(enhance); };
const later = () => { if (!q) q = requestAnimationFrame(scan); };
function ann(){
  const a = document.querySelector('.luna-ann'); if (!a) return;
  const k = 'luna.ann.' + a.dataset.t;
  try { if (localStorage.getItem(k)) { a.remove(); return; } } catch (e) {}
  const h = document.querySelector('header.top, header.nav, header.ah, header');
  if (h && h.parentNode) h.insertAdjacentElement('afterend', a); else document.body.prepend(a);
  a.querySelector('.luna-ann-x').onclick = () => { try { localStorage.setItem(k, '1'); } catch (e) {} a.remove(); };
}
function init(){ ann(); scan(); new MutationObserver(later).observe(document.body, {childList: true, subtree: true}); }
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
