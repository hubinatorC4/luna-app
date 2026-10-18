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
let B = null, ME = null, CSRF = '', CHIP = '';
/* Kategorie (filtr): uzgodnione Topy, Sukienki, Bluzki, Koszulki, Bluzy, Swetry, Buty, Szpilki + kategorie zatwierdzonego katalogu v2. Puste ukrywamy. */
const CN = (pl, en, es, de, uk) => [pl, {pl, en, es, de, uk}];
const CHIPS = [['topy', ...CN('Topy', 'Tops', 'Tops', 'Tops', 'Топи')], ['sukienki', ...CN('Sukienki', 'Dresses', 'Vestidos', 'Kleider', 'Сукні')], ['bluzki', ...CN('Bluzki', 'Blouses', 'Blusas', 'Blusen', 'Блузки')],
  ['koszulki', ...CN('Koszulki', 'T-shirts', 'Camisetas', 'T-Shirts', 'Футболки')], ['bluzy', ...CN('Bluzy', 'Sweatshirts', 'Sudaderas', 'Sweatshirts', 'Світшоти')], ['swetry', ...CN('Swetry', 'Jumpers', 'Jerséis', 'Pullover', 'Светри')],
  ['buty', ...CN('Buty', 'Shoes', 'Zapatos', 'Schuhe', 'Взуття')], ['szpilki', ...CN('Szpilki', 'Heels', 'Tacones', 'High Heels', 'Туфлі на підборах')],
  ['spodnice', ...CN('Spódnice', 'Skirts', 'Faldas', 'Röcke', 'Спідниці')], ['spodnie', ...CN('Spodnie', 'Trousers', 'Pantalones', 'Hosen', 'Штани')], ['zakiety', ...CN('Żakiety', 'Blazers', 'Americanas', 'Blazer', 'Жакети')],
  ['plaszcze', ...CN('Płaszcze', 'Coats', 'Abrigos', 'Mäntel', 'Пальта')], ['sportowe', ...CN('Sportowe', 'Activewear', 'Deportivo', 'Sportlich', 'Спортивне')], ['dodatki', ...CN('Dodatki', 'Accessories', 'Complementos', 'Accessoires', 'Аксесуари')]]
  .map(([id, pl, tr]) => [id, pl, tr]);
const CMAP = {'sukienki': 'sukienki', 'suknie wieczorowe': 'sukienki', 'sukienka': 'sukienki', 'bluzki': 'bluzki', 'swetry': 'swetry', 'sweter': 'swetry', 'topy': 'topy', 'koszulki': 'koszulki', 'bluzy': 'bluzy', 'buty': 'buty', 'szpilki': 'szpilki',
  'spódnice': 'spodnice', 'spodnie': 'spodnie', 'żakiety': 'zakiety', 'płaszcze': 'plaszcze', 'sportowe-skromne': 'sportowe', 'dodatki': 'dodatki'};
const chipOf = i => CMAP[String(i.category || '').toLowerCase()] || '';
const BX = {pl: {all: 'Wszystkie', color: 'Kolor', allcol: 'Wszystkie kolory w cenie', nophoto: 'zdjęcie wkrótce'}, en: {all: 'All', color: 'Colour', allcol: 'All colours included in the price', nophoto: 'photo coming soon'},
  es: {all: 'Todo', color: 'Color', allcol: 'Todos los colores incluidos en el precio', nophoto: 'foto próximamente'}, de: {all: 'Alle', color: 'Farbe', allcol: 'Alle Farben im Preis enthalten', nophoto: 'Foto folgt'},
  uk: {all: 'Усі', color: 'Колір', allcol: 'Усі кольори входять у ціну', nophoto: 'фото незабаром'}};
const SOON = {pl: ['Premiera', 'Jeszcze niedostępne – kupisz od dnia premiery.'], en: ['Release:', 'Not available yet – you can buy it from release day.'], es: ['Estreno:', 'Aún no disponible: podrás comprarlo desde el día del estreno.'], de: ['Start:', 'Noch nicht erhältlich – ab dem Starttag kaufbar.'], uk: ['Прем’єра:', 'Ще недоступно – можна буде купити з дня прем’єри.']};
const soon = i => { const l = document.documentElement.lang; const s = SOON[l] || SOON.pl; let d = i.release_date;
  try { d = new Date(i.release_date + 'T12:00:00').toLocaleDateString(l === 'uk' ? 'uk-UA' : l, {day: 'numeric', month: 'long'}); } catch(e){}
  return `<span class="soonb" title="${esc(s[1])}">📅 ${esc(s[0] + ' ' + d)}</span>`; };
document.querySelectorAll('.tabsx button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tabsx button').forEach(x => x.classList.toggle('on', x === b));
  $('#tab-col').hidden = b.dataset.tab !== 'col'; $('#tab-price').hidden = b.dataset.tab !== 'price';
  if (b.dataset.tab === 'price') coach();
});
if (location.hash === '#cennik') document.querySelector('[data-tab=price]').click();
function render(){
  if (!B) return; const t = T(); const en = document.documentElement.lang !== 'pl';
  const L = document.documentElement.lang; const X = BX[L] || BX.pl;
  const all = [...B.items.filter(i => !i.upcoming), ...B.items.filter(i => i.upcoming)]; let firstSoon = true;
  const present = CHIPS.filter(c => all.some(i => chipOf(i) === c[0]));
  $('#chips').innerHTML = present.length > 1 ? `<button type="button" class="chip${!CHIP ? ' on' : ''}" data-chip="">${esc(X.all)}</button>` + present.map(c => `<button type="button" class="chip${CHIP === c[0] ? ' on' : ''}" data-chip="${c[0]}">${esc((c[L === 'pl' ? 1 : 2] || {})[L] || c[1])}</button>`).join('') : '';
  $('#chips').querySelectorAll('[data-chip]').forEach(b => b.onclick = () => { CHIP = b.dataset.chip; render(); });
  const its = all.filter(i => !CHIP || chipOf(i) === CHIP);
  const icard = i => { const v = (i.variants || []).filter(x => x.hex); const nm = en ? (i.name_en || i.name) : i.name;
    const real = i.image || (v.find(x => x.image) || {}).image; const img = real || '/catalog/butik/placeholder.svg';
    const sw = v.length ? `<div class="swatches" role="radiogroup" aria-label="${esc(X.color)}">${v.map((x, n) => `<button type="button" role="radio" aria-checked="${n === 0}" class="sw${n === 0 ? ' on' : ''}${x.image ? '' : ' noimg'}"${x.image || n === 0 ? '' : ' disabled'} style="--c:${esc(x.hex)}" data-img="${esc(x.image || '')}" data-name="${esc(L === 'pl' ? x.color_name_pl : x.color_name_en)}" aria-label="${esc(L === 'pl' ? x.color_name_pl : x.color_name_en)}" title="${esc((L === 'pl' ? x.color_name_pl : x.color_name_en) + (x.image ? '' : ' · ' + X.nophoto))}"></button>`).join('')}</div><small class="swname">${esc(X.color)}: <b>${esc(L === 'pl' ? v[0].color_name_pl : v[0].color_name_en)}</b></small>${v.length > 1 ? `<div class="allcol">🎨 ${esc(X.allcol)}</div>` : ''}` : '';
    return `<div class="item${i.upcoming ? ' upcoming' : ''}" id="${esc(i.id)}" data-track="item:${esc(i.id)}"${i.upcoming && firstSoon && !(firstSoon = false) ? ' data-soon="1"' : ''}><div class="pwrap"><img class="pimg" src="${esc(img)}" alt="${esc(nm)}" loading="lazy" width="800" height="600">${real ? '' : `<span class="phsoon">📷 ${esc(X.nophoto)}</span>`}</div><div class="b"><b class="pname">${esc(nm)}</b><br><small>${esc(t[LN[i.line]])} · ${esc(i.collection)}</small>${i.upcoming ? '<br>' + soon(i) : ''}${i.price ? `<div class="bprice">${money(i.price)}</div><small class="bvat">${esc(t.vat)}</small>` : ''}${sw}
    <div class="wallpage bsoc"><div class="acts"><span data-votes="item:${esc(i.id)}"></span><button type="button" class="act share" data-share="${esc(location.origin + '/butik.html#' + i.id)}" data-text="${esc(nm)}">↗</button></div>
    <details class="lazycm"><summary>💬</summary><div data-lazycm="item:${esc(i.id)}" data-rating="1"></div></details></div></div></div>`; };
  /* Kolekcja v2 ma setki strojów: renderujemy partiami po 24 (przewijanie doładowuje kolejne), komentarze ładujemy dopiero po otwarciu 💬. */
  const hid0 = decodeURIComponent(location.hash.slice(1)); const at = its.findIndex(i => i.id === hid0);
  let shown = Math.max(24, at + 1);
  $('#items').innerHTML = its.slice(0, shown).map(icard).join('');
  if (render.io) render.io.disconnect();
  const sent = $('#itemsMore') || (() => { const d = document.createElement('div'); d.id = 'itemsMore'; d.className = 'itemsmore'; $('#items').after(d); return d; })();
  const bindAll = () => {
    $('#items').querySelectorAll('.swatches').forEach(g => g.onclick = e => { const b = e.target.closest('.sw'); if (!b || b.disabled) return; g.querySelectorAll('.sw').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-checked', x === b); });
      const it = g.closest('.item'); it.querySelector('.swname b').textContent = b.dataset.name; if (b.dataset.img){ const im = it.querySelector('.pimg'); im.style.opacity = .3; setTimeout(() => { im.src = b.dataset.img; im.style.opacity = 1; }, 150); } });
    $('#items').querySelectorAll('details.lazycm:not([data-b])').forEach(d => { d.dataset.b = 1; d.addEventListener('toggle', () => { const c = d.querySelector('[data-lazycm]'); if (d.open && c && !c.dataset.comments){ c.dataset.comments = c.dataset.lazycm; window.LunaSocial && window.LunaSocial.auto(); } }); });
    if (window.LunaSocial && window.LunaSocial.observe) window.LunaSocial.observe($('#items'));
    if (window.LunaSocial) window.LunaSocial.auto();
  };
  sent.textContent = shown < its.length ? '…' : '';
  render.more = () => { if (shown >= its.length) return; const n = its.slice(shown, shown + 24); shown += n.length; $('#items').insertAdjacentHTML('beforeend', n.map(icard).join('')); bindAll(); sent.textContent = shown < its.length ? '…' : ''; };
  render.io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) render.more(); }, {rootMargin: '900px'}); render.io.observe(sent);
  render.bindAll = bindAll;
  const sn = document.querySelector('[data-soon]'); if (sn && !document.getElementById('nowosci')) sn.insertAdjacentHTML('beforebegin', '<span id="nowosci"></span>');
  bindAll();
  const hid = decodeURIComponent(location.hash.slice(1)); if (hid && hid !== 'nowosci' && hid !== 'cennik' && !render.jumpedItem && document.getElementById(hid)){ render.jumpedItem = 1; setTimeout(() => document.getElementById(hid).scrollIntoView({block: 'center'}), 300); }
  if (location.hash === '#nowosci' && !render.jumped && $('#nowosci')){ render.jumped = 1; setTimeout(() => $('#nowosci').scrollIntoView({block: 'center'}), 300); }
  $('#preview').hidden = !B.preview;
  const show = B.prices_visible;
  $('#lines').innerHTML = `<tr><th></th><th>${esc(t.released)}</th><th>${esc(t.planned)}</th>${show ? '<th>zł</th>' + (B.foreign ? '<th>€</th><th>$</th>' : '') + '' : ''}</tr>` +
    Object.keys(B.lines).map(k => { const r = (B.ranges || {})[k]; const rel = B.items.filter(i => i.line === k && !i.upcoming).length;
      return `<tr><td><b>${esc(t[LN[k]])}</b></td><td>${rel}</td><td>${B.planned[k] || 0}</td>${show && r ? `<td>${pl(r.pln[0])}–${pl(r.pln[1])}</td>${B.foreign ? `<td>${pl(r.eur[0])}–${pl(r.eur[1])}</td><td>${r.usd[0]}–${r.usd[1]}</td>` : ''}` : ''}</tr>`; }).join('');
  const card = (name, big, sub, btn, hot) => `<div class="plancard${hot ? ' hot' : ''}"><h3>${esc(name)}</h3><div class="pbig">${big}</div><p class="psub">${sub}</p>${btn || ''}</div>`;
  const isFree = p => p.prices && Number(String(p.prices.pln).replace(',', '.')) <= 0;
  $('#plansTbl').innerHTML = card(t.free, '0 zł', esc(t.no_acct)) + B.plans.map(p => {
    if (!p.prices) return card(p.name, '–', esc(t.hidden));
    if (isFree(p)) return card(p.name, '0 zł', esc(t.with_acct));
    const fx = B.foreign && p.prices.eur ? `<br><small>${pl(p.prices.eur)} € · $${p.prices.usd}</small>` : '';
    return card(p.name, `${pl(p.prices.pln)} zł`, `${esc(t.no_renew)}${fx}`, payBtn('pass', p.id), p.id === 'premium');
  }).join('') + (B.foreign ? '' : `<p class="hint pfoot">${esc(t.zl_only)}</p>`);
  $('#itemPrices').innerHTML = show ? `<table class="tbl">${B.items.map(i => `<tr><td>${esc(en ? i.name_en : i.name)}</td><td>${money(i.price)}</td><td>${i.upcoming ? soon(i) : payBtn('item', i.id)}</td></tr>`).join('')}</table>` : `<p>${esc(t.hidden)}</p>`;
  const pb = $('#payBox');
  pb.innerHTML = twa ? `<p>${esc(t.pay_twa)}</p>` : !B.payments.web ? `<p>💳 ${esc(t.pay_soon)} · BLIK · ${esc(B.payments.methods.slice(1).join(' · '))}</p>`
    : `<label class="consent"><input type="checkbox" id="payConsent"> <span>${esc(t.consent)}</span></label>${ME ? '' : `<p class="hint">${esc(t.login)}</p>`}`;
  document.querySelectorAll('[data-pay]').forEach(b => b.onclick = () => { if (b.dataset.kind === 'item' && window.LunaSocial && window.LunaSocial.track) window.LunaSocial.track('cart', 'item:' + b.dataset.pay); pay(b.dataset.kind, b.dataset.pay); });
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
/* Ogłoszenia Butiku (rotujący baner) i informacja o skromnych strojach. Tekst źródłowy PL (zatwierdzony), tłumaczenia EN/ES/DE/UK. */
(() => {
const A = {
 pl: ['✨ Twoja Luna może teraz zmienić swój wygląd! Nowa fryzura, nowy styl, nowa odsłona – zdecydujesz Ty. Zajrzyj do Butiku Luny i wybierz look, w którym Twoja agentka zachwyci od pierwszego spojrzenia.',
  '👗 Nowa kolekcja w Butiku Luny już jest! Topy, sukienki, bluzki, koszulki, bluzy, swetry, buty i szpilki – wszystko, co modne i w dobrym tonie. Każdy strój ma własną grafikę i cenę widoczną od razu.',
  '🌸 Piękno w każdym detalu. Wierzymy, że kobieta ma wyglądać pięknie – dlatego stawiamy na elegancki krój, szlachetne kolory i dopracowane szczegóły. Dobierz Lunie strój, który podkreśli jej urodę.',
  '👚 Codzienny szyk. Lekkie topy, miękkie swetry i wygodne bluzy na co dzień – a na wieczór sukienki i szpilki. Twoja Luna gotowa na każdą okazję.',
  '👠 Kropka nad i. Buty i szpilki dopełniają każdą stylizację. Odkryj nasze modele i stwórz look idealny.',
  '🎨 Każdy strój w kilku kolorach. Wybierz odcień, który najlepiej pasuje do Twojej agentki – tak, by Twoja Luna była wyjątkowa. Tylko Twoja.',
  '💚 Butik Luny zaprasza! Elegancja, styl i dobry smak w jednym miejscu.'],
 en: ['✨ Your Luna can now change her look! A new hairstyle, a new style, a fresh new look – you decide. Visit Luna’s Boutique and pick the outfit that makes your agent shine at first sight.',
  '👗 The new collection is here in Luna’s Boutique! Tops, dresses, blouses, T-shirts, sweatshirts, jumpers, shoes and heels – everything stylish and in good taste. Every outfit has its own picture and a price you can see straight away.',
  '🌸 Beauty in every detail. We believe a woman should look beautiful – that’s why we focus on elegant cuts, refined colours and carefully finished details. Choose an outfit that brings out Luna’s beauty.',
  '👚 Everyday chic. Light tops, soft jumpers and comfy sweatshirts for every day – and dresses and heels for the evening. Your Luna is ready for any occasion.',
  '👠 The finishing touch. Shoes and heels complete every look. Discover our styles and create the perfect outfit.',
  '🎨 Every outfit comes in several colours. Choose the shade that suits your agent best – so your Luna is unique. Yours alone.',
  '💚 Welcome to Luna’s Boutique! Elegance, style and good taste in one place.'],
 es: ['✨ ¡Tu Luna ya puede cambiar de look! Nuevo peinado, nuevo estilo, una imagen renovada: tú decides. Visita la Boutique de Luna y elige el look con el que tu agente enamorará a primera vista.',
  '👗 ¡Ya llegó la nueva colección a la Boutique de Luna! Tops, vestidos, blusas, camisetas, sudaderas, jerséis, zapatos y tacones: todo con estilo y buen gusto. Cada prenda tiene su propia imagen y su precio a la vista.',
  '🌸 Belleza en cada detalle. Creemos que una mujer debe lucir bella; por eso apostamos por cortes elegantes, colores nobles y detalles cuidados. Elige para Luna un conjunto que realce su belleza.',
  '👚 Elegancia diaria. Tops ligeros, jerséis suaves y sudaderas cómodas para el día a día, y vestidos y tacones para la noche. Tu Luna, lista para cualquier ocasión.',
  '👠 El toque final. Los zapatos y tacones completan cualquier look. Descubre nuestros modelos y crea el conjunto perfecto.',
  '🎨 Cada prenda en varios colores. Elige el tono que mejor le siente a tu agente, para que tu Luna sea única. Solo tuya.',
  '💚 ¡La Boutique de Luna te espera! Elegancia, estilo y buen gusto en un solo lugar.'],
 de: ['✨ Deine Luna kann jetzt ihr Aussehen ändern! Neue Frisur, neuer Stil, ein ganz neuer Look – du entscheidest. Schau in Lunas Boutique vorbei und wähle den Look, mit dem deine Agentin auf den ersten Blick begeistert.',
  '👗 Die neue Kollektion ist da – in Lunas Boutique! Tops, Kleider, Blusen, T-Shirts, Sweatshirts, Pullover, Schuhe und High Heels – alles modisch und geschmackvoll. Jedes Outfit hat ein eigenes Bild und einen sofort sichtbaren Preis.',
  '🌸 Schönheit in jedem Detail. Wir finden, eine Frau soll schön aussehen – deshalb setzen wir auf elegante Schnitte, edle Farben und durchdachte Details. Wähle für Luna ein Outfit, das ihre Schönheit unterstreicht.',
  '👚 Alltagsschick. Leichte Tops, weiche Pullover und bequeme Sweatshirts für jeden Tag – und für den Abend Kleider und High Heels. Deine Luna ist für jeden Anlass bereit.',
  '👠 Das i-Tüpfelchen. Schuhe und High Heels runden jedes Outfit ab. Entdecke unsere Modelle und kreiere den perfekten Look.',
  '🎨 Jedes Outfit in mehreren Farben. Wähle den Farbton, der am besten zu deiner Agentin passt – damit deine Luna einzigartig ist. Nur deine.',
  '💚 Lunas Boutique lädt ein! Eleganz, Stil und guter Geschmack an einem Ort.'],
 uk: ['✨ Тепер ваша Луна може змінити свій вигляд! Нова зачіска, новий стиль, новий образ – вирішуєте ви. Завітайте до Бутика Луни й оберіть образ, у якому ваша агентка зачарує з першого погляду.',
  '👗 Нова колекція вже в Бутику Луни! Топи, сукні, блузки, футболки, світшоти, светри, взуття й туфлі на підборах – усе модне та зі смаком. Кожне вбрання має власне зображення і ціну, яку видно одразу.',
  '🌸 Краса в кожній деталі. Ми віримо, що жінка має виглядати гарно, – тому обираємо елегантний крій, шляхетні кольори й продумані деталі. Доберіть Луні вбрання, яке підкреслить її красу.',
  '👚 Щоденний шик. Легкі топи, м’які светри й зручні світшоти на щодень, а на вечір – сукні й підбори. Ваша Луна готова до будь-якої нагоди.',
  '👠 Останній штрих. Взуття й підбори доповнюють кожен образ. Відкрийте наші моделі та створіть ідеальний образ.',
  '🎨 Кожне вбрання в кількох кольорах. Оберіть відтінок, який найкраще пасує вашій агентці, – щоб ваша Луна була неповторною. Тільки ваша.',
  '💚 Бутик Луни запрошує! Елегантність, стиль і добрий смак в одному місці.']};
const N = {pl: '<b>Tylko eleganckie, w pełni zakrywające stroje.</b> W Butiku nie ma nagości, bielizny ani strojów odsłaniających – Luna zawsze wygląda z klasą.',
 en: '<b>Only elegant, fully covering outfits.</b> The Boutique has no nudity, lingerie or revealing outfits – Luna always looks classy.',
 es: '<b>Solo prendas elegantes y que cubren por completo.</b> En la Boutique no hay desnudos, lencería ni ropa reveladora: Luna siempre luce con clase.',
 de: '<b>Nur elegante, vollständig bedeckende Outfits.</b> In der Boutique gibt es keine Nacktheit, keine Dessous und keine freizügigen Outfits – Luna sieht immer stilvoll aus.',
 uk: '<b>Лише елегантне вбрання, що повністю закриває тіло.</b> У Бутику немає оголеності, білизни чи відвертого одягу – Луна завжди виглядає зі смаком.'};
const box = document.getElementById('ann'), nn = document.getElementById('nonude'); if (!box) return;
let i = 0, tm = null;
function lang(){ const l = document.documentElement.lang; return A[l] ? l : 'pl'; }
function show(){ const a = A[lang()]; i = (i + a.length) % a.length; box.querySelector('.anntext').textContent = a[i];
  box.querySelector('.anndots').innerHTML = a.map((_, n) => `<button type="button" aria-label="${n + 1}/${a.length}" class="${n === i ? 'on' : ''}" data-n="${n}"></button>`).join(''); }
function start(){ clearInterval(tm); if (!matchMedia('(prefers-reduced-motion: reduce)').matches) tm = setInterval(() => { i++; show(); }, 7000); }
box.addEventListener('click', e => { const b = e.target.closest('[data-n]'); if (b){ i = +b.dataset.n; show(); start(); } if (e.target.closest('[data-prev]')){ i--; show(); start(); } if (e.target.closest('[data-next]')){ i++; show(); start(); } });
box.addEventListener('mouseenter', () => clearInterval(tm)); box.addEventListener('mouseleave', start);
function all(){ show(); if (nn) nn.innerHTML = '👗 ' + N[lang()]; }
all(); start(); window.addEventListener('luna-lang', all);
})();
