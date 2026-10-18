/* „Problemy techniczne”: zgłoszenie z numerem LUNA-0001, opcjonalny zrzut ekranu, automatyczne dane środowiska. */
(() => {
const $ = s => document.querySelector(s);
const f = $('#tkForm'); const t0 = Date.now();
const dict = () => { try { const D = JSON.parse(document.getElementById('i18n').textContent); return Object.assign({}, D.pl, D[document.documentElement.lang] || {}); } catch(e){ return {}; } };
const readFile = file => new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(file); });
f.onsubmit = async e => {
  e.preventDefault(); const err = f.querySelector('.err'); err.textContent = '';
  const fd = new FormData(f); const file = f.shot.files[0];
  if (file && file.size > 5 * 1024 * 1024){ err.textContent = '⚠️ max 5 MB'; return; }
  const body = {category: fd.get('category'), description: fd.get('description'), email: fd.get('email') || '', website: fd.get('website') || '', t0,
    env: {version: '1.3.1', ua: navigator.userAgent, lang: document.documentElement.lang, screen: `${screen.width}x${screen.height}`, page: document.referrer || location.pathname, twa: document.documentElement.classList.contains('twa') ? '1' : '0'}};
  if (file) body.screenshot = await readFile(file);
  const btn = f.querySelector('[type=submit]'); btn.disabled = true;
  try {
    const r = await fetch('/api/tickets', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    $('#tkId').textContent = d.id; f.querySelector('.ok').hidden = false; btn.hidden = true;
    try { const k = JSON.parse(localStorage.getItem('luna.tickets') || '{}'); k[d.id] = d.key; localStorage.setItem('luna.tickets', JSON.stringify(k)); } catch(x){}
  } catch(x){ err.textContent = '⚠️ ' + x.message; btn.disabled = false; }
};
$('#stForm').onsubmit = async e => {
  e.preventDefault(); const id = e.target.id.value.trim().toUpperCase(); const out = $('#stOut');
  let k = ''; try { k = JSON.parse(localStorage.getItem('luna.tickets') || '{}')[id] || ''; } catch(x){}
  const r = await fetch('/api/tickets/status?id=' + encodeURIComponent(id) + '&k=' + encodeURIComponent(k));
  const d = await r.json(); out.textContent = r.ok ? `${d.id}: ${d.status}${d.reply ? ' – ' + d.reply : ''}` : dict().st_none;
};
})();
