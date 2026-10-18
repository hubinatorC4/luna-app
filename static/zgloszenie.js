/* Strona /zgloszenie.html: przełącznik Testerzy / Casting (?f=tester|casting) i nagłówek w 5 językach. */
(() => {
const H = {pl: ['Zgłoszenie', 'Testerzy', 'Casting'], en: ['Application', 'Testers', 'Casting'], es: ['Solicitud', 'Testers', 'Casting'], de: ['Bewerbung', 'Tester', 'Casting'], uk: ['Заявка', 'Тестувальники', 'Кастинг']};
let l = 'pl'; try { l = (new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2); } catch(e){}
const h = H[l] || H.pl; document.documentElement.lang = H[l] ? l : 'pl';
document.getElementById('f18h').textContent = h[0];
document.querySelector('[data-f18t=tester]').textContent = h[1]; document.querySelector('[data-f18t=casting]').textContent = h[2];
const pick = k => { document.querySelectorAll('.f18tabs button').forEach(b => { b.classList.toggle('on', b.dataset.tab === k); b.setAttribute('aria-selected', String(b.dataset.tab === k)); });
  document.getElementById('f18tester').hidden = k !== 'tester'; document.getElementById('f18casting').hidden = k !== 'casting'; };
document.querySelectorAll('.f18tabs button').forEach(b => b.onclick = () => { pick(b.dataset.tab); const u = new URL(location.href); u.searchParams.set('f', b.dataset.tab); history.replaceState(null, '', u); });
pick(new URLSearchParams(location.search).get('f') === 'casting' ? 'casting' : 'tester');
})();
