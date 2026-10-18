/* Butik Luny: kolekcja (wydane stroje) + cennik (linie, plany 30-dniowe, ceny strojów). Ceny tylko przy „Pokaż ceny” lub w podglądzie moderatora.
   Płatność WWW: Stripe Checkout (BLIK + karta) – w aplikacji TWA wyłączona (Google Play). */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const D = JSON.parse(document.getElementById('i18n').textContent);
const T = () => Object.assign({}, D.pl, D[document.documentElement.lang] || {});
const twa = document.documentElement.classList.contains('twa');
const h = {}; const at = sessionStorage.getItem('luna.admin'); if (at) h['X-Admin-Token'] = at;
const LN = {ekonomiczna: 'l_eko', classic: 'l_cla', couture: 'l_cou'};
const money = p => !p ? '' : (B && B.foreign) ? `${pl(p.pln)} zł · ${pl(p.eur)} € · $${p.usd}` : `${pl(p.pln)} zł`;
const pl = n => String(n).replace('.', ',');
let B = null, ME = null, CSRF = '';
document.querySelectorAll('.tabsx button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tabsx button').forEach(x => x.classList.toggle('on', x === b));
  $('#tab-col').hidden = b.dataset.tab !== 'col'; $('#tab-price').hidden = b.dataset.tab !== 'price';
  if (b.dataset.tab === 'price') coach();
});
if (location.hash === '#cennik') document.querySelector('[data-tab=price]').click();
function render(){
  if (!B) return; const t = T(); const en = document.documentElement.lang !== 'pl';
  $('#items').innerHTML = B.items.map(i => `<div class="item"><img src="${esc(i.image || '/avatar-512.jpg')}" alt="" loading="lazy"><div class="b"><b>${esc(en ? i.name_en : i.name)}</b><br><small>${esc(t[LN[i.line]])} · ${esc(i.collection)}</small>${i.price ? `<div class="bprice">${money(i.price)}</div><small class="bvat">${esc(t.vat)}</small>` : ''}
    <div class="wallpage bsoc"><div class="acts"><span data-votes="item:${esc(i.id)}"></span><button type="button" class="act share" data-share="${esc(location.origin + '/butik.html#' + i.id)}" data-text="${esc(en ? i.name_en : i.name)}">↗</button></div>
    <details><summary>💬</summary><div data-comments="item:${esc(i.id)}" data-rating="1"></div></details></div></div></div>`).join('');
  if (window.LunaSocial) window.LunaSocial.auto();
  $('#preview').hidden = !B.preview;
  const show = B.prices_visible;
  $('#lines').innerHTML = `<tr><th></th><th>${esc(t.released)}</th><th>${esc(t.planned)}</th>${show ? '<th>zł</th>' + (B.foreign ? '<th>€</th><th>$</th>' : '') + '' : ''}</tr>` +
    Object.keys(B.lines).map(k => { const r = (B.ranges || {})[k]; const rel = B.items.filter(i => i.line === k).length;
      return `<tr><td><b>${esc(t[LN[k]])}</b></td><td>${rel}</td><td>${B.planned[k] || 0}</td>${show && r ? `<td>${pl(r.pln[0])}–${pl(r.pln[1])}</td>${B.foreign ? `<td>${pl(r.eur[0])}–${pl(r.eur[1])}</td><td>${r.usd[0]}–${r.usd[1]}</td>` : ''}` : ''}</tr>`; }).join('');
  const card = (name, big, sub, btn, hot) => `<div class="plancard${hot ? ' hot' : ''}"><h3>${esc(name)}</h3><div class="pbig">${big}</div><p class="psub">${sub}</p>${btn || ''}</div>`;
  const isFree = p => p.prices && Number(String(p.prices.pln).replace(',', '.')) <= 0;
  $('#plansTbl').innerHTML = card(t.free, '0 zł', esc(t.no_acct)) + B.plans.map(p => {
    if (!p.prices) return card(p.name, '–', esc(t.hidden));
    if (isFree(p)) return card(p.name, '0 zł', esc(t.with_acct));
    const fx = B.foreign && p.prices.eur ? `<br><small>${pl(p.prices.eur)} € · $${p.prices.usd}</small>` : '';
    return card(p.name, `${pl(p.prices.pln)} zł`, `${esc(t.no_renew)}${fx}`, payBtn('pass', p.id), p.id === 'premium');
  }).join('') + (B.foreign ? '' : `<p class="hint pfoot">${esc(t.zl_only)}</p>`);
  $('#itemPrices').innerHTML = show ? `<table class="tbl">${B.items.map(i => `<tr><td>${esc(en ? i.name_en : i.name)}</td><td>${money(i.price)}</td><td>${payBtn('item', i.id)}</td></tr>`).join('')}</table>` : `<p>${esc(t.hidden)}</p>`;
  const pb = $('#payBox');
  pb.innerHTML = twa ? `<p>${esc(t.pay_twa)}</p>` : !B.payments.web ? `<p>💳 ${esc(t.pay_soon)} · BLIK · ${esc(B.payments.methods.slice(1).join(' · '))}</p>`
    : `<label class="consent"><input type="checkbox" id="payConsent"> <span>${esc(t.consent)}</span></label>${ME ? '' : `<p class="hint">${esc(t.login)}</p>`}`;
  document.querySelectorAll('[data-pay]').forEach(b => b.onclick = () => pay(b.dataset.kind, b.dataset.pay));
}
function payBtn(kind, ref){
  const t = T(); if (twa) return '';
  const dis = !B.payments.web || !B.prices_visible || !ME;
  return `<button type="button" class="blik" data-kind="${kind}" data-pay="${esc(ref)}"${dis ? ' disabled title="' + esc(B.payments.web ? t.login : t.pay_soon) + '"' : ''}>${esc(t.pay_btn)} <b>BLIK</b></button>`;
}
function coach(){
  try { if (localStorage.getItem('luna.coachBlik')) return; localStorage.setItem('luna.coachBlik', '1'); } catch(e){ return; }
  const c = document.createElement('div'); c.className = 'coach'; c.setAttribute('role', 'status'); c.textContent = T().coach;
  const x = document.createElement('button'); x.type = 'button'; x.textContent = '✕'; x.setAttribute('aria-label', 'OK'); x.onclick = () => c.remove(); c.appendChild(x);
  $('#howPay').before(c); $('#howPay').open = true;
}
async function pay(kind, ref){
  const t = T();
  if (!$('#payConsent') || !$('#payConsent').checked){ alert(t.consent); return; }
  try {
    const r = await fetch('/api/pay/checkout', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': CSRF}, credentials: 'same-origin', body: JSON.stringify({kind, ref, consent_immediate: true, twa})});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    location.href = d.url;
  } catch(e){ alert('⚠️ ' + e.message); }
}
Promise.all([fetch('/api/butik', {headers: h}).then(r => r.json()), fetch('/api/account/me', {credentials: 'same-origin'}).then(r => r.json()).catch(() => ({}))])
  .then(([b, m]) => { B = b; ME = m.user; CSRF = m.csrf || ''; render(); }).catch(() => {});
window.addEventListener('luna-lang', render);
})();
