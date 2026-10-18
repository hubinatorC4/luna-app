/* Strona kasy Paddle (domyślny link płatności w panelu Paddle: https://<domena>/kasa.html). Paddle.js sam otwiera kasę dla ?_ptxn=txn_…
   Plan włącza dopiero webhook transaction.completed – ta strona niczego nie przyznaje. */
(() => {
const L = (document.documentElement.lang = (navigator.language || 'pl').slice(0, 2));
const M = {pl: ['Otwieram bezpieczną kasę partnera płatniczego…', 'Płatności startują wkrótce 💄 Kasa jeszcze się maluje – nic nie pobieramy.', 'Ceny zawierają wszystkie podatki, w tym VAT. Płatności obsługuje nasz partner płatniczy, który rozlicza VAT.'],
  en: ['Opening our payment partner’s secure checkout…', 'Payments are coming soon 💄 The checkout is still doing its make-up – we charge nothing.', 'Prices include all taxes, including VAT. Payments are handled by our payment partner, which accounts for VAT.'],
  es: ['Abriendo la caja segura de nuestro socio de pagos…', 'Los pagos llegan pronto 💄 La caja aún se maquilla: no cobramos nada.', 'Los precios incluyen todos los impuestos, incluido el IVA. Los pagos los gestiona nuestro socio de pagos, que liquida el IVA.'],
  de: ['Die sichere Kasse unseres Zahlungspartners wird geöffnet…', 'Zahlungen starten bald 💄 Die Kasse schminkt sich noch – wir buchen nichts ab.', 'Die Preise enthalten alle Steuern, einschließlich MwSt. Zahlungen wickelt unser Zahlungspartner ab, der die MwSt. abrechnet.'],
  uk: ['Відкриваю безпечну касу платіжного партнера…', 'Оплата незабаром 💄 Каса ще фарбується – ми нічого не списуємо.', 'Ціни містять усі податки, зокрема ПДВ. Платежі обслуговує наш платіжний партнер, який розраховує ПДВ.']};
let done = false; const t = M[L] || M.pl; const km = document.getElementById('km');
km.textContent = t[0];
fetch('/api/pay/config', {credentials: 'same-origin'}).then(r => r.json()).then(c => {
  if (!c.web || !c.paddle || !window.Paddle){ km.textContent = t[1]; return; }
  if (c.mor) document.getElementById('kv').textContent = '🧾 ' + t[2];
  if (c.paddle.env === 'sandbox') Paddle.Environment.set('sandbox');
  Paddle.Initialize({token: c.paddle.token, checkout: {settings: {displayMode: 'overlay', locale: L, successUrl: location.origin + '/app?platnosc=ok'}},
    eventCallback: e => { if (!e) return; if (e.name === 'checkout.completed') done = true;
      if (e.name === 'checkout.closed') location.assign('/app?platnosc=' + (done ? 'ok' : 'anulowano')); }});
}).catch(() => { km.textContent = t[1]; });
})();
