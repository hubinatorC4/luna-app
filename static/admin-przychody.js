/* Przychody (moderator): dane wyłącznie z API dostawcy płatności (Paddle/Stripe). Eksport CSV na miesiąc. Token tylko w sessionStorage. */
(() => {
const $ = s => document.querySelector(s);
const tok = () => sessionStorage.getItem('luna.admin') || '';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const m2 = (v, cur) => v == null ? '–' : (v / 100).toLocaleString('pl-PL', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' ' + esc(cur || '');
function show(){ const on = !!tok(); $('#login').hidden = on; $('#app').hidden = !on; $('#logout').hidden = !on; if (on) load(); }
$('#lf').onsubmit = async e => { e.preventDefault(); $('#lerr').textContent = '';
  try { const r = await fetch('/api/admin/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({passphrase: $('#pass').value})}); const d = await r.json();
    $('#pass').value = ''; if (!r.ok) throw new Error(d.error || r.status); sessionStorage.setItem('luna.admin', d.admin_token); show(); } catch(x){ $('#lerr').textContent = '⚠️ ' + x.message; } };
$('#logout').onclick = async () => { try { await fetch('/api/admin/logout', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: '{}'}); } catch(e){} sessionStorage.removeItem('luna.admin'); show(); };
async function load(){
  $('#err').textContent = '';
  let d;
  try { const r = await fetch('/api/admin/revenue', {headers: {'X-Admin-Token': tok()}}); if (r.status === 401){ sessionStorage.removeItem('luna.admin'); show(); return; }
    d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); } catch(e){ $('#err').textContent = '⚠️ ' + e.message; return; }
  const c = d.config || {};
  const prov = d.provider_set === 'paddle' ? 'Paddle (Merchant of Record – rozlicza VAT za Ciebie)' : 'Stripe (sprzedawcą jesteś Ty – VAT rozliczasz sam/-a z księgowym)';
  $('#st').innerHTML = d.on ? `<p>✅ Płatności <b>włączone</b> · ${esc(prov)} · tryb: <b>${esc(d.mode)}</b>${d.mode === 'test' ? ' (testowy – to nie są prawdziwe pieniądze)' : ''}</p><p class="hint">Przyznane dostępy/zakupy z webhooków: ${d.granted}</p>`
    : `<p>💤 Płatności <b>wyłączone</b> – brak kluczy dostawcy (${esc(d.provider_set)}). Przyciski na stronie pokazują „płatności startują wkrótce”.</p><p class="hint">Instrukcja: PLATNOSCI_KROKI.md. Gdy klucze będą w zmiennych środowiskowych Render, tu pojawią się prawdziwe dane.</p>`;
  const M = d.months || [];
  $('#months').innerHTML = !M.length ? '<p class="hint">Brak transakcji – nic tu nie wymyślamy. 🌙</p>' :
    `<table class="tbl"><thead><tr><th>Miesiąc</th><th>Waluta</th><th>Liczba</th><th>Brutto</th><th>Opłaty pośrednika</th><th>VAT (pośrednik)</th><th>Netto do wypłaty</th><th></th></tr></thead><tbody>` +
    M.map(m => `<tr><td>${esc(m.month)}</td><td>${esc(m.cur)}</td><td>${m.n}</td><td>${m2(m.gross, m.cur)}</td><td>${m2(m.fee, m.cur)}</td><td>${m.tax_known ? m2(m.tax, m.cur) : 'n/d'}</td><td>${m2(m.net, m.cur)}</td><td><button type="button" data-csv="${esc(m.month)}">⬇️ CSV</button></td></tr>`).join('') + '</tbody></table>';
  document.querySelectorAll('[data-csv]').forEach(b => b.onclick = () => csv(b.dataset.csv));
  const R = d.recent || [];
  $('#recent').innerHTML = !R.length ? '<p class="hint">Brak.</p>' : `<table class="tbl"><thead><tr><th>Data</th><th>Co</th><th>Brutto</th><th>Opłata</th><th>VAT</th><th>Netto</th></tr></thead><tbody>` +
    R.map(r => `<tr><td>${esc(String(r.t).slice(0, 16).replace('T', ' '))}</td><td>${esc(r.what)}${r.sub ? ' 🔁' : ''}</td><td>${m2(r.gross, r.cur)}</td><td>${m2(r.fee, r.cur)}</td><td>${r.tax == null ? 'n/d' : m2(r.tax, r.cur)}</td><td>${m2(r.net, r.cur)}</td></tr>`).join('') + '</tbody></table>';
}
async function csv(month){
  try { const r = await fetch('/api/admin/revenue.csv?month=' + encodeURIComponent(month), {headers: {'X-Admin-Token': tok()}}); if (!r.ok) throw new Error(r.status);
    const b = await r.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = `luna-przychody-${month}.csv`; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  } catch(e){ $('#err').textContent = '⚠️ CSV: ' + e.message; }
}
show();
})();
