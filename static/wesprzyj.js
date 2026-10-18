(() => {
const $ = s => document.querySelector(s);
const dict = () => { try { const D = JSON.parse(document.getElementById('i18n').textContent); return Object.assign({}, D.pl, D[document.documentElement.lang] || {}); } catch(e){ return {}; } };
if (document.documentElement.classList.contains('twa')) return;
fetch('/api/support').then(r => r.json()).then(d => {
  if (!d.enabled) return;
  $('#bHolder').textContent = d.holder; $('#bIban').textContent = d.iban; $('#bTitle').textContent = d.title;
  $('#bank').hidden = false; $('#bankSoon').hidden = true;
}).catch(() => {});
document.querySelectorAll('[data-copy]').forEach(b => b.onclick = async () => {
  const v = document.getElementById(b.dataset.copy).textContent;
  try { await navigator.clipboard.writeText(v); } catch(e){ const ta = document.createElement('textarea'); ta.value = v; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
  const d = dict(); b.textContent = d.copied || 'OK'; setTimeout(() => b.textContent = d.copy || 'Kopiuj', 1800);
});
})();
