/* Kasa Luny (v1.7.0): wspólna dla strony i aplikacji. 3 kroki: wybierz → BLIK lub karta → potwierdź (w kasie partnera płatniczego).
   Bez kluczy dostawcy: uczciwe „płatności startują wkrótce” – nic nie pobieramy i nie udajemy sukcesu.
   Ceny w walucie kraju – tylko od dostawcy (Paddle); inaczej samo PLN. Nie przechowujemy danych kart. */
(() => {
if (window.LunaKasa) return;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const I = {
 pl: {s1: 'Wybierz', s2: 'BLIK lub karta', s3: 'Potwierdź', h: 'Kasa Luny', once: 'Jednorazowo – 30 dni', once_n: 'BLIK, karta i inne. Bez automatycznego odnawiania.',
  sub: 'Co miesiąc – subskrypcja', sub_n: 'Karta lub PayPal (BLIK nie obsługuje subskrypcji). Anulujesz jednym kliknięciem w portalu klienta.', item: 'Strój do Butiku – na zawsze w Twojej szafie Luny.',
  next: 'Dalej', back: 'Wstecz', close: 'Zamknij', consent: 'Żądam natychmiastowego dostarczenia treści cyfrowych i przyjmuję do wiadomości, że tracę prawo odstąpienia od umowy z chwilą rozpoczęcia dostarczania.',
  consent_need: 'Zaznacz proszę zgodę – bez niej kasa nie ruszy.', go: 'Przejdź do bezpiecznej kasy', methods: 'Metody płatności', safe: 'Płacisz w kasie partnera płatniczego. Luna nie widzi i nie zapisuje danych Twojej karty.',
  confirm: 'W kasie wybierz BLIK (kod z aplikacji banku) albo kartę i potwierdź płatność. Plan włączy się sam, gdy partner potwierdzi wpłatę.',
  soon_h: 'Płatności startują wkrótce 💄', soon: 'Kasa jeszcze się maluje przed lustrem. Nic nie pobieramy i niczego nie udajemy – gdy ruszy, ten przycisk zaprowadzi Cię prosto do BLIK-a lub karty. Do tego czasu plan Podstawowa jest za darmo.',
  login: 'Zaloguj się, żeby kupić – Luna musi wiedzieć, komu włączyć plan.', login_b: 'Zaloguj się', twa: 'W aplikacji z Google Play płatności będą przez Google Play – wkrótce. Na stronie www działa kasa Luny.',
  err: 'Nie udało się otworzyć kasy. Spróbuj za chwilę.', wait: 'Otwieram kasę…', price: 'Cena',
  vat_mor: 'Ceny zawierają wszystkie podatki, w tym VAT. Płatności obsługuje nasz partner płatniczy, który rozlicza VAT.',
  vat_gross: 'Ceny brutto – to kwota, którą płacisz.', vat_soon: 'Ceny brutto – to kwota do zapłaty. Płatności startują wkrótce.',
  loc_exact: 'Cena dla Twojego kraju od partnera płatniczego – ostateczna kwota w kasie.', loc_pln: 'Ceny w złotych (PLN). Ostateczna kwota i waluta – w kasie.',
  portal: 'Zarządzaj subskrypcją', portal_n: 'Anulowanie, zmiana karty i faktury – w portalu klienta partnera płatniczego.'},
 en: {s1: 'Choose', s2: 'BLIK or card', s3: 'Confirm', h: 'Luna checkout', once: 'One-off – 30 days', once_n: 'BLIK, card and more. No automatic renewal.',
  sub: 'Monthly – subscription', sub_n: 'Card or PayPal (BLIK doesn’t support subscriptions). Cancel in one click in the customer portal.', item: 'A Boutique outfit – yours forever in Luna’s wardrobe.',
  next: 'Next', back: 'Back', close: 'Close', consent: 'I request immediate delivery of the digital content and acknowledge that I lose my right of withdrawal once delivery begins.',
  consent_need: 'Please tick the consent – the checkout won’t start without it.', go: 'Go to secure checkout', methods: 'Payment methods', safe: 'You pay in our payment partner’s checkout. Luna never sees or stores your card details.',
  confirm: 'In the checkout choose BLIK (code from your banking app) or a card and confirm. Your plan switches on by itself once the partner confirms the payment.',
  soon_h: 'Payments are coming soon 💄', soon: 'The checkout is still doing its make-up in front of the mirror. We charge nothing and fake nothing – once it’s live, this button takes you straight to BLIK or card. Until then the Basic plan is free.',
  login: 'Please log in to buy – Luna needs to know whose plan to switch on.', login_b: 'Log in', twa: 'In the Google Play app payments will go through Google Play – coming soon. The Luna checkout works on the website.',
  err: 'Couldn’t open the checkout. Please try again in a moment.', wait: 'Opening checkout…', price: 'Price',
  vat_mor: 'Prices include all taxes, including VAT. Payments are handled by our payment partner, which accounts for VAT.',
  vat_gross: 'Gross prices – this is the amount you pay.', vat_soon: 'Gross prices – this is the amount to pay. Payments are coming soon.',
  loc_exact: 'Price for your country from our payment partner – final amount at checkout.', loc_pln: 'Prices in Polish złoty (PLN). Final amount and currency at checkout.',
  portal: 'Manage subscription', portal_n: 'Cancel, change card and invoices – in the payment partner’s customer portal.'},
 es: {s1: 'Elige', s2: 'BLIK o tarjeta', s3: 'Confirma', h: 'Caja de Luna', once: 'Pago único – 30 días', once_n: 'BLIK, tarjeta y más. Sin renovación automática.',
  sub: 'Mensual – suscripción', sub_n: 'Tarjeta o PayPal (BLIK no admite suscripciones). Cancela con un clic en el portal del cliente.', item: 'Un conjunto de la Boutique: tuyo para siempre en el armario de Luna.',
  next: 'Siguiente', back: 'Atrás', close: 'Cerrar', consent: 'Solicito la entrega inmediata del contenido digital y acepto que pierdo el derecho de desistimiento en cuanto comienza la entrega.',
  consent_need: 'Marca el consentimiento: sin él la caja no arranca.', go: 'Ir a la caja segura', methods: 'Métodos de pago', safe: 'Pagas en la caja de nuestro socio de pagos. Luna nunca ve ni guarda los datos de tu tarjeta.',
  confirm: 'En la caja elige BLIK (código de tu app bancaria) o tarjeta y confirma. Tu plan se activa solo cuando el socio confirma el pago.',
  soon_h: 'Los pagos llegan pronto 💄', soon: 'La caja aún se está maquillando frente al espejo. No cobramos nada ni fingimos nada: cuando esté lista, este botón te llevará directo a BLIK o tarjeta. Mientras tanto, el plan Básico es gratis.',
  login: 'Inicia sesión para comprar: Luna necesita saber a quién activar el plan.', login_b: 'Iniciar sesión', twa: 'En la app de Google Play los pagos serán a través de Google Play: próximamente. En la web funciona la caja de Luna.',
  err: 'No se pudo abrir la caja. Inténtalo en un momento.', wait: 'Abriendo la caja…', price: 'Precio',
  vat_mor: 'Los precios incluyen todos los impuestos, incluido el IVA. Los pagos los gestiona nuestro socio de pagos, que liquida el IVA.',
  vat_gross: 'Precios brutos: es lo que pagas.', vat_soon: 'Precios brutos: es lo que pagarás. Los pagos llegan pronto.',
  loc_exact: 'Precio para tu país de nuestro socio de pagos; importe final en la caja.', loc_pln: 'Precios en zlotys polacos (PLN). Importe y moneda finales en la caja.',
  portal: 'Gestionar suscripción', portal_n: 'Cancelar, cambiar tarjeta y facturas: en el portal del cliente del socio de pagos.'},
 de: {s1: 'Wählen', s2: 'BLIK oder Karte', s3: 'Bestätigen', h: 'Lunas Kasse', once: 'Einmalig – 30 Tage', once_n: 'BLIK, Karte und mehr. Keine automatische Verlängerung.',
  sub: 'Monatlich – Abo', sub_n: 'Karte oder PayPal (BLIK unterstützt keine Abos). Mit einem Klick im Kundenportal kündbar.', item: 'Ein Boutique-Outfit – für immer in Lunas Kleiderschrank.',
  next: 'Weiter', back: 'Zurück', close: 'Schließen', consent: 'Ich verlange die sofortige Bereitstellung der digitalen Inhalte und nehme zur Kenntnis, dass ich mein Widerrufsrecht mit Beginn der Bereitstellung verliere.',
  consent_need: 'Bitte die Zustimmung ankreuzen – ohne sie startet die Kasse nicht.', go: 'Zur sicheren Kasse', methods: 'Zahlungsarten', safe: 'Du zahlst in der Kasse unseres Zahlungspartners. Luna sieht und speichert deine Kartendaten nie.',
  confirm: 'Wähle in der Kasse BLIK (Code aus deiner Banking-App) oder Karte und bestätige. Dein Plan startet von selbst, sobald der Partner die Zahlung bestätigt.',
  soon_h: 'Zahlungen starten bald 💄', soon: 'Die Kasse schminkt sich noch vor dem Spiegel. Wir buchen nichts ab und täuschen nichts vor – sobald sie live ist, bringt dich dieser Knopf direkt zu BLIK oder Karte. Bis dahin ist der Basis-Plan kostenlos.',
  login: 'Bitte melde dich zum Kaufen an – Luna muss wissen, wessen Plan sie freischaltet.', login_b: 'Anmelden', twa: 'In der Google-Play-App laufen Zahlungen über Google Play – bald. Auf der Website funktioniert Lunas Kasse.',
  err: 'Die Kasse ließ sich nicht öffnen. Bitte gleich noch einmal.', wait: 'Kasse wird geöffnet…', price: 'Preis',
  vat_mor: 'Die Preise enthalten alle Steuern, einschließlich MwSt. Zahlungen wickelt unser Zahlungspartner ab, der die MwSt. abrechnet.',
  vat_gross: 'Bruttopreise – das ist der Betrag, den du zahlst.', vat_soon: 'Bruttopreise – das ist der zu zahlende Betrag. Zahlungen starten bald.',
  loc_exact: 'Preis für dein Land von unserem Zahlungspartner – Endbetrag in der Kasse.', loc_pln: 'Preise in polnischen Złoty (PLN). Endbetrag und Währung in der Kasse.',
  portal: 'Abo verwalten', portal_n: 'Kündigen, Karte ändern und Rechnungen – im Kundenportal des Zahlungspartners.'},
 uk: {s1: 'Оберіть', s2: 'BLIK або картка', s3: 'Підтвердьте', h: 'Каса Луни', once: 'Разово – 30 днів', once_n: 'BLIK, картка та інше. Без автоматичного продовження.',
  sub: 'Щомісяця – підписка', sub_n: 'Картка або PayPal (BLIK не підтримує підписки). Скасування одним кліком у порталі клієнта.', item: 'Вбрання з Бутика – назавжди в гардеробі Луни.',
  next: 'Далі', back: 'Назад', close: 'Закрити', consent: 'Вимагаю негайного надання цифрового контенту та беру до відома, що з початком надання втрачаю право на відмову від договору.',
  consent_need: 'Будь ласка, позначте згоду – без неї каса не запуститься.', go: 'До безпечної каси', methods: 'Способи оплати', safe: 'Ви платите в касі нашого платіжного партнера. Луна не бачить і не зберігає дані вашої картки.',
  confirm: 'У касі оберіть BLIK (код із банківського застосунку) або картку й підтвердьте. План увімкнеться сам, щойно партнер підтвердить оплату.',
  soon_h: 'Оплата незабаром 💄', soon: 'Каса ще фарбується перед дзеркалом. Ми нічого не списуємо й нічого не вдаємо – коли запрацює, ця кнопка поведе вас просто до BLIK або картки. Доти план Базовий безкоштовний.',
  login: 'Увійдіть, щоб купити – Луна має знати, кому ввімкнути план.', login_b: 'Увійти', twa: 'У застосунку з Google Play оплата буде через Google Play – незабаром. На сайті працює каса Луни.',
  err: 'Не вдалося відкрити касу. Спробуйте за мить.', wait: 'Відкриваю касу…', price: 'Ціна',
  vat_mor: 'Ціни містять усі податки, зокрема ПДВ. Платежі обслуговує наш платіжний партнер, який розраховує ПДВ.',
  vat_gross: 'Ціни брутто – це сума, яку ви платите.', vat_soon: 'Ціни брутто – це сума до сплати. Оплата незабаром.',
  loc_exact: 'Ціна для вашої країни від платіжного партнера – остаточна сума в касі.', loc_pln: 'Ціни в польських злотих (PLN). Остаточна сума й валюта – у касі.',
  portal: 'Керувати підпискою', portal_n: 'Скасування, зміна картки й рахунки – у порталі клієнта платіжного партнера.'}
};
const lang = () => (document.documentElement.lang || 'pl').slice(0, 2);
const T = () => Object.assign({}, I.pl, I[lang()] || {});
const twa = () => document.documentElement.classList.contains('twa');
let CFG = null, cfgP = null;
function config(force){
  if (CFG && !force) return Promise.resolve(CFG);
  if (!cfgP || force) cfgP = fetch('/api/pay/config', {credentials: 'same-origin'}).then(r => r.json()).then(c => (CFG = c)).catch(() => (CFG = {web: false, vat: 'soon', methods: ['BLIK', 'karta / card'], plans: {}}));
  return cfgP;
}
const zl = v => String(v).replace('.', ',') + ' zł';
function vatNote(c){ const t = T(); c = c || CFG || {}; return c.vat === 'mor' ? t.vat_mor : c.vat === 'gross' ? t.vat_gross : t.vat_soon; }
function locNote(c){ const t = T(); c = c || CFG || {}; return c.local && c.local.prices && Object.keys(c.local.prices).length ? t.loc_exact : t.loc_pln; }
function priceOf(ref, pln, c){ c = c || CFG || {}; const lp = c.local && c.local.prices && c.local.prices[ref]; return lp ? `${esc(lp)} <small>(${esc(zl(pln))})</small>` : esc(zl(pln)); }
function mountNotes(){
  config().then(c => document.querySelectorAll('[data-kasa-vat]').forEach(el => { el.textContent = '🧾 ' + vatNote(c) + ' ' + locNote(c); el.hidden = false; }));
}
async function me(){ try { return await (await fetch('/api/account/me', {credentials: 'same-origin'})).json(); } catch(e){ return {}; } }

let box = null;
function shell(){
  if (box) return box;
  box = document.createElement('div'); box.className = 'kasa-bg'; box.hidden = true;
  box.innerHTML = '<div class="kasa" role="dialog" aria-modal="true" aria-labelledby="kasaH"><button type="button" class="kasa-x" aria-label="✕">✕</button><h2 id="kasaH"></h2><ol class="kasa-steps"></ol><div class="kasa-body"></div></div>';
  document.body.appendChild(box);
  box.addEventListener('click', e => { if (e.target === box || e.target.closest('.kasa-x')) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !box.hidden) close(); });
  return box;
}
function close(){ if (box){ box.hidden = true; document.documentElement.classList.remove('kasa-open'); } }
function steps(n){ const t = T(); box.querySelector('.kasa-steps').innerHTML = [t.s1, t.s2, t.s3].map((s, i) => `<li class="${i + 1 === n ? 'on' : i + 1 < n ? 'done' : ''}"${i + 1 === n ? ' aria-current="step"' : ''}><b>${i + 1}</b> ${esc(s)}</li>`).join('<li class="arr" aria-hidden="true">→</li>'); }

async function open(o){
  const t = T(); shell(); box.hidden = false; document.documentElement.classList.add('kasa-open');
  box.querySelector('#kasaH').textContent = t.h + ' · ' + (o.name || '');
  const body = box.querySelector('.kasa-body'); body.innerHTML = `<p class="kasa-wait">${esc(t.wait)}</p>`;
  const [c, m] = await Promise.all([config(), me()]);
  const st = {sub: false};
  const head = `<div class="kasa-prod"><span>${esc(o.name || '')}</span><b>${priceOf(o.ref, o.pln, c)}</b></div><p class="kasa-vat">🧾 ${esc(vatNote(c))} ${esc(locNote(c))}</p>`;
  const s1 = () => { steps(1);
    body.innerHTML = head + (o.kind === 'pass' ? `<div class="kasa-opts" role="radiogroup">
      <label class="kasa-opt"><input type="radio" name="kasaSub" value="0" checked><span><b>${esc(t.once)}</b><small>${esc(t.once_n)}</small></span></label>
      <label class="kasa-opt"><input type="radio" name="kasaSub" value="1"><span><b>${esc(t.sub)}</b><small>${esc(t.sub_n)}</small></span></label></div>` : `<p class="kasa-n">👗 ${esc(t.item)}</p>`) +
      `<div class="kasa-act"><button type="button" class="kasa-btn pri" data-n>${esc(t.next)} →</button></div>`;
    body.querySelector('[data-n]').onclick = () => { const r = body.querySelector('input[name=kasaSub]:checked'); st.sub = !!(r && r.value === '1'); s2(); };
  };
  const s2 = () => { steps(2);
    const ms = (c.methods || []).filter(x => !st.sub || !/BLIK/i.test(x));
    let inner;
    if (twa()) inner = `<div class="kasa-soon"><p>${esc(t.twa)}</p></div>`;
    else if (!c.web) inner = `<div class="kasa-soon" role="status"><h3>${esc(t.soon_h)}</h3><p>${esc(t.soon)}</p></div>`;
    else if (!m.user) inner = `<div class="kasa-soon"><p>${esc(t.login)}</p><a class="kasa-btn pri" href="/app?konto=1">${esc(t.login_b)}</a></div>`;
    else inner = `<label class="kasa-cons"><input type="checkbox" id="kasaCons"> <span>${esc(t.consent)}</span></label><p class="kasa-msg" role="alert"></p>`;
    body.innerHTML = head + `<p class="kasa-m"><b>${esc(t.methods)}:</b> ${ms.map(esc).join(' · ')}</p>` + inner + `<p class="kasa-safe">🔒 ${esc(t.safe)}</p>` +
      `<div class="kasa-act"><button type="button" class="kasa-btn" data-b>← ${esc(t.back)}</button><button type="button" class="kasa-btn pri" data-go${c.web && m.user && !twa() ? '' : ' disabled aria-disabled="true"'}>${esc(t.go)}</button></div>`;
    body.querySelector('[data-b]').onclick = s1;
    const go = body.querySelector('[data-go]');
    go.onclick = async () => {
      if (go.disabled) return;
      const msg = body.querySelector('.kasa-msg');
      if (!body.querySelector('#kasaCons').checked){ msg.textContent = t.consent_need; return; }
      go.disabled = true; msg.textContent = t.wait;
      try {
        const r = await fetch('/api/pay/checkout', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': m.csrf || ''},
          body: JSON.stringify({kind: o.kind, ref: o.ref, sub: st.sub, consent_immediate: true, twa: twa()})});
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.url){ s3(); setTimeout(() => { (window.top || window).location.assign(d.url); }, 600); return; }
        msg.textContent = d.soon ? t.soon : (d.error || t.err);
      } catch(e){ msg.textContent = t.err; }
      go.disabled = false;
    };
  };
  const s3 = () => { steps(3); body.innerHTML = head + `<p class="kasa-n">${esc(t.confirm)}</p><p class="kasa-wait">${esc(t.wait)}</p>`; };
  s1();
  setTimeout(() => { const f = box.querySelector('.kasa-btn.pri'); if (f) f.focus(); }, 30);
}
async function portal(){
  const t = T(); const m = await me();
  try { const r = await fetch('/api/pay/portal', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': m.csrf || ''}, body: '{}'});
    const d = await r.json().catch(() => ({})); if (r.ok && d.url){ (window.top || window).location.assign(d.url); return; } alert(d.soon ? t.soon : (d.error || t.err)); } catch(e){ alert(t.err); }
}
window.LunaKasa = {open, config, vatNote, locNote, priceOf, mountNotes, portal, T};
if (document.readyState !== 'loading') mountNotes(); else document.addEventListener('DOMContentLoaded', mountNotes);
window.addEventListener('luna-lang', mountNotes);
})();
