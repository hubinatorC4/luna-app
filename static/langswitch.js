/* Przełącznik języka z flagami w nagłówku każdej strony; wybór zapamiętany, adres ?lang=xx (indeksowalny). */
(() => {
const L = [['pl', '🇵🇱', 'Polski'], ['en', '🇬🇧', 'English'], ['es', '🇪🇸', 'Español'], ['de', '🇩🇪', 'Deutsch'], ['uk', '🇺🇦', 'Українська']];
const APP = location.pathname === '/' || location.pathname === '/index.html';
const q = new URLSearchParams(location.search).get('lang');
let saved = null; try { saved = localStorage.getItem('luna.lang'); } catch(e){}
if (q && L.some(x => x[0] === q)){ try { localStorage.setItem('luna.lang', q); } catch(e){} }
else if (APP){ /* aplikacja: język w Ustawieniach (pełne tłumaczenie UI – v1.4) */ }
else if (!saved){ const nav = (navigator.language || 'pl').slice(0, 2).toLowerCase(); const pick = L.some(x => x[0] === nav) ? nav : 'pl'; try { localStorage.setItem('luna.lang', pick); } catch(e){}
  if (pick !== 'pl' && !location.pathname.startsWith('/api')){ const u = new URL(location.href); u.searchParams.set('lang', pick); location.replace(u); return; } }
else if (saved && saved !== 'pl' && !q){ const u = new URL(location.href); u.searchParams.set('lang', saved); location.replace(u); return; }
const cur = q || saved || 'pl';
function mount(){
  if (APP) return;
  if (document.querySelector('.lswitch')) return;
  const host = document.querySelector('header .bar .acts') || document.querySelector('header .bar') || document.querySelector('header.top') || document.querySelector('header');
  const s = document.createElement('select'); s.className = 'lswitch'; s.setAttribute('aria-label', 'Język / Language');
  L.forEach(([c, f, n]) => { const o = document.createElement('option'); o.value = c; o.textContent = `${f} ${n}`; if (c === cur) o.selected = true; s.appendChild(o); });
  s.onchange = () => { try { localStorage.setItem('luna.lang', s.value); } catch(e){} const u = new URL(location.href); u.searchParams.set('lang', s.value); location.href = u; };
  if (host) host.prepend(s); else { s.classList.add('floating'); document.body.appendChild(s); }
  document.querySelectorAll('.langtabs').forEach(t => t.hidden = true);
  document.querySelectorAll('a[href^="/"]').forEach(a => { if (cur === 'pl' || /^\/(api|music|uploads)\//.test(a.getAttribute('href'))) return; try { const u = new URL(a.href); if (u.origin === location.origin && /\.html$|\/$/.test(u.pathname) && !u.searchParams.get('lang')){ u.searchParams.set('lang', cur); a.href = u.pathname + u.search + u.hash; } } catch(e){} });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
