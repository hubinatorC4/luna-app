fetch('/api/seller').then(r => r.json()).then(s => {
  if (!s.filled) return;
  const $ = id => document.getElementById(id);
  $('sellerName').textContent = s.name; $('sellerAddr').textContent = ', ' + s.address;
  if (s.nip) $('sellerNip').textContent = ', NIP: ' + s.nip;
  if (s.vat) $('sellerVat').textContent = s.vat === 'czynny' ? ' (czynny podatnik VAT)' : ' (podmiot zwolniony z VAT)';
}).catch(() => {});
/* Ceny planów w regulaminie – tylko gdy włączono „Pokaż ceny” (z /api/catalog). */
fetch('/api/catalog').then(r => r.json()).then(c => {
  const f = v => String(v).replace('.', ',');
  (c.plans || []).forEach(p => { if (!p.prices) return;
    document.querySelectorAll(`[data-price="${p.id}"]`).forEach(e => e.textContent = `${f(p.prices.pln)} zł za 30 dni, z VAT`);
    if (p.id === 'premium') document.querySelectorAll('[data-tester-value]').forEach(e => e.textContent = ` (wartość ${(Math.round(parseFloat(String(p.prices.pln).replace(',', '.')) * 200) / 100).toFixed(2).replace('.', ',')} zł)`); });
}).catch(() => {});
