/* Luna – „Dymki Luny” (v1.6.6): małe, znikające dymki obok awatara Luny. Max 1 na odsłonę, ~3 na sesję, 1 dymek „Podziel się” na sesję
   (nie przy pierwszej odsłonie). Nigdy przy pisaniu, nagrywaniu ani głosowaniu w bitwie; nie zasłania przycisków ani pól.
   Wyłącznik: Mój panel → Dymki Luny (localStorage „luna.dymki” + konto). Treści bez wymyślonych liczb. */
(() => {
if (window.__lunaDymki || window.top !== window) return; window.__lunaDymki = 1;
const ls = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch(e){ return null; } };
const ss = (k, v) => { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch(e){ return null; } };
if (ls('luna.dymki') === '0') return;
if (/^\/(testerzy|zgloszenie)(\.html)?$/.test(location.pathname)) return;   // strony zapisu testerów: nic nie zasłania nagłówka ani formularza
const views = +(ss('luna.dy.v') || 0) + 1; ss('luna.dy.v', views);
const shown = +(ss('luna.dy.n') || 0); if (shown >= 3) return;
const LS = ['pl', 'en', 'es', 'de', 'uk'];
let lang = (document.documentElement.lang || ls('luna.lang') || 'pl').slice(0, 2); if (!LS.includes(lang)) lang = 'pl';
// [pl, en, es, de, uk]
const TIPS = {
  bitwy: [['Zagłosuj – ja nie mogę, jestem stronnicza 😄', 'Go vote – I can’t, I’m biased 😄', 'Vota tú, yo no puedo: soy parcial 😄', 'Stimm ab – ich darf nicht, ich bin befangen 😄', 'Голосуйте – я не можу, я упереджена 😄'],
          ['Kibicować można bez planu. Krzyczeć do ekranu też 📣', 'Cheering is free. Yelling at the screen too 📣', 'Animar es gratis. Gritarle a la pantalla, también 📣', 'Anfeuern ist gratis. Den Bildschirm anschreien auch 📣', 'Вболівати можна безкоштовно. Кричати на екран теж 📣']],
  ranking: [['Ranking liczy prawdziwe głosy. Ja też się dziwię 🏆', 'The ranking counts real votes. Surprises me too 🏆', 'El ranking cuenta votos reales. A mí también me sorprende 🏆', 'Das Ranking zählt echte Stimmen. Überrascht mich auch 🏆', 'Рейтинг рахує справжні голоси. Мене це теж дивує 🏆']],
  agentki: [['Zostaw serduszko – agentki udają, że im nie zależy 💚', 'Leave a heart – the agents pretend they don’t care 💚', 'Deja un corazón: las agentes fingen que no les importa 💚', 'Lass ein Herz da – die Agentinnen tun so, als wäre es egal 💚', 'Залиште сердечко – агентки вдають, що їм байдуже 💚']],
  scianka: [['Komentuj śmiało, byle kulturalnie – moderacja ma dobry słuch 👂', 'Comment away, just keep it kind – moderation has great hearing 👂', 'Comenta sin miedo, pero con educación: la moderación tiene buen oído 👂', 'Kommentier ruhig, aber freundlich – die Moderation hört gut 👂', 'Коментуйте сміливо, але чемно – модерація має добрий слух 👂']],
  butik: [['Wszystko eleganckie i zakryte. Moda bez „ups” 👗', 'Everything elegant and covered. Fashion without “oops” 👗', 'Todo elegante y cubierto. Moda sin «ups» 👗', 'Alles elegant und bedeckt. Mode ohne „Ups“ 👗', 'Усе елегантне й закрите. Мода без «ой» 👗']],
  galeria: [['Polubienia są prawdziwe. Moja pewność siebie też 😌', 'The likes are real. So is my confidence 😌', 'Los «me gusta» son reales. Mi autoestima, también 😌', 'Die Likes sind echt. Mein Selbstbewusstsein auch 😌', 'Вподобання справжні. Моя впевненість теж 😌']],
  agentka: [['Profil agentki AI – ładna, mądra i ani grama prawdziwej osoby 🤖', 'An AI agent profile – pretty, smart, and zero real person 🤖', 'Perfil de agente IA: guapa, lista y ni rastro de persona real 🤖', 'Profil einer KI-Agentin – hübsch, klug, null echte Person 🤖', 'Профіль ШІ-агентки – гарна, розумна й жодної реальної людини 🤖']],
  ustawienia: [['Tu wszystko ustawisz. Nawet mnie wyciszysz – „Dymki Luny” 🙊', 'Everything’s adjustable here. Even me – “Luna’s bubbles” 🙊', 'Aquí lo ajustas todo. Incluso a mí: «Burbujas de Luna» 🙊', 'Hier stellst du alles ein. Sogar mich – „Lunas Sprechblasen“ 🙊', 'Тут усе налаштовується. Навіть я – «Бульбашки Луни» 🙊']],
  znajomi: [['Gwiazdka ☆ = bliski znajomy. Tylko oni widzą, że jesteś online 🌙', 'Star ☆ = close friend. Only they see you’re online 🌙', 'Estrella ☆ = amigo cercano. Solo ellos ven que estás en línea 🌙', 'Stern ☆ = enge Freundschaft. Nur sie sehen, dass du online bist 🌙', 'Зірочка ☆ = близький друг. Лише вони бачать, що ви онлайн 🌙']],
  live: [['Na żywo mówię bez dubli. Prawie 🎙️', 'Live, I speak without retakes. Almost 🎙️', 'En directo hablo sin repetir tomas. Casi 🎙️', 'Live spreche ich ohne zweiten Take. Fast 🎙️', 'У прямому ефірі говорю без дублів. Майже 🎙️']],
  app: [['Powiedz „bułka” trzy razy szybko. Czekam 😄', 'Say “red lorry, yellow lorry” three times fast. I’ll wait 😄', 'Di «tres tristes tigres» tres veces rápido. Espero 😄', 'Sag dreimal schnell „Fischers Fritz“. Ich warte 😄', 'Скажіть швидко «на дворі трава» тричі. Я зачекаю 😄'],
        ['Mów do mnie śmiało – oceniam dykcję, nie fryzurę 💇', 'Talk to me – I judge diction, not hairstyles 💇', 'Háblame sin miedo: juzgo la dicción, no el peinado 💇', 'Sprich ruhig mit mir – ich bewerte Aussprache, nicht Frisuren 💇', 'Говоріть сміливо – я оцінюю дикцію, а не зачіску 💇']],
  home: [['Cześć! Mówię jak jest – ale zawsze z uśmiechem 🌙', 'Hi! I tell it like it is – always with a smile 🌙', '¡Hola! Digo las cosas como son, siempre con una sonrisa 🌙', 'Hallo! Ich sag’s, wie es ist – immer mit Lächeln 🌙', 'Привіт! Кажу як є – але завжди з усмішкою 🌙']],
};
const SHARE = [['Znasz kogoś, kto mówi „eee” co drugie słowo? Podziel się Luną 😉', 'Know someone who says “umm” every other word? Share Luna 😉', '¿Conoces a alguien que dice «eh» cada dos palabras? Comparte Luna 😉', 'Kennst du wen, der jedes zweite Wort „ähm“ sagt? Teile Luna 😉', 'Знаєте когось, хто каже «е-е» через слово? Поділіться Луною 😉'],
               ['Dobra dykcja to najlepszy prezent. Prawie tak dobry jak link do mnie 🎁', 'Good diction is the best gift. Almost as good as a link to me 🎁', 'Una buena dicción es el mejor regalo. Casi tan bueno como un enlace a mí 🎁', 'Gute Aussprache ist das beste Geschenk. Fast so gut wie ein Link zu mir 🎁', 'Гарна дикція – найкращий подарунок. Майже як посилання на мене 🎁']];
// Delikatne zachęty (max 1 na sesję, odrzucona = 7 dni przerwy, nigdy dla osób, które już mają dany plan). Bez liczb i presji.
const PROMO = {
  up:     {need: p => p === 'darmowy' || p === 'podstawowa', href: '/app.html#plans', ic: '✨',
           t: ['Masz głos do bitew. Premium daje Ci do tego własną agentkę – bez pośpiechu ✨', 'You’ve got a voice for battles. Premium adds your own agent – no rush ✨', 'Tienes voz para las batallas. Premium te da tu propia agente, sin prisas ✨', 'Du hast die Stimme für Battles. Premium gibt dir eine eigene Agentin dazu – ganz ohne Eile ✨', 'У вас голос для батлів. Premium додасть власну агентку – без поспіху ✨'],
           c: ['Zobacz plany', 'See plans', 'Ver planes', 'Pläne ansehen', 'Переглянути плани']},
  agent:  {need: p => p === 'premium' || p === 'pro', href: '/ustawienia.html#gen', ic: '🎨',
           t: ['Generator agentek jest w Twoim planie. Ona sama się nie wymyśli… choć by chciała 🎨', 'The agent generator is in your plan. She won’t invent herself… though she’d love to 🎨', 'El generador de agentes está en tu plan. No se va a inventar sola… aunque le encantaría 🎨', 'Der Agentinnen-Generator ist in deinem Plan. Sie erfindet sich nicht selbst … obwohl sie gern würde 🎨', 'Генератор агенток уже у вашому плані. Сама себе вона не вигадає… хоча й хотіла б 🎨'],
           c: ['Stwórz agentkę', 'Create an agent', 'Crear agente', 'Agentin erstellen', 'Створити агентку']},
  battle: {need: p => p === 'premium' || p === 'pro', href: '/bitwy.html', ic: '⚔️',
           t: ['Twoja agentka może stanąć do bitwy. Ja trzymam kciuki – obie 😄', 'Your agent can enter a battle. I’ll keep my fingers crossed – both hands 😄', 'Tu agente puede entrar en una batalla. Yo cruzo los dedos, los de las dos manos 😄', 'Deine Agentin kann ins Battle. Ich drück die Daumen – beide 😄', 'Ваша агентка може вийти на батл. Я тримаю кулачки – обидва 😄'],
           c: ['Do bitwy', 'To battle', 'A la batalla', 'Zum Battle', 'До батлу']},
  butik:  {need: () => true, href: '/butik.html', ic: '👗',
           t: ['W Butiku czekają eleganckie stylizacje. Lustro już przetarte 👗', 'Elegant outfits are waiting in the Boutique. The mirror’s already polished 👗', 'En la Boutique esperan looks elegantes. El espejo ya está limpio 👗', 'In der Boutique warten elegante Outfits. Der Spiegel ist schon geputzt 👗', 'У Бутику чекають елегантні образи. Дзеркало вже протерте 👗'],
           c: ['Do Butiku', 'Visit Boutique', 'Ir a la Boutique', 'Zur Boutique', 'До Бутику']},
};
const WEEK = 7 * 864e5;
const promoFree = id => { const t = +(ls('luna.dy.x.' + id) || 0); return !t || Date.now() - t > WEEK; };
async function pickPromo(){
  if (views < 2 || ss('luna.dy.pr')) return null;
  let plan = 'darmowy';
  try { const r = await fetch('/api/account/plan', {credentials: 'same-origin'}); if (r.ok) plan = (await r.json()).plan || plan; } catch(e){ return null; }
  const here = p.replace(/^\//, '');
  const ids = Object.keys(PROMO).filter(id => PROMO[id].need(plan) && promoFree(id) && !(id === 'butik' && here === 'butik') && !(id === 'battle' && here === 'bitwy'));
  return ids.length ? ids[Math.floor(Math.random() * ids.length)] : null;
}
const COPIED = ['Link skopiowany – teraz wklej go komuś, kto „eee” 😄', 'Link copied – now paste it to someone who “umm”s 😄', 'Enlace copiado: pégaselo a quien diga «eh» 😄', 'Link kopiert – jetzt an jemanden schicken, der „ähm“ sagt 😄', 'Посилання скопійовано – надішліть тому, хто «е-е» 😄'];
const CLOSE = ['Zamknij dymek', 'Close bubble', 'Cerrar burbuja', 'Sprechblase schließen', 'Закрити бульбашку'];
const L = a => a[LS.indexOf(lang)] || a[0];
const p = location.pathname.replace(/\.html$/, '').replace(/^\//, '') || 'home';
const ctx = {promo: 'home', index: 'home', home: 'home', app: 'app', bitwy: 'bitwy', ranking: 'ranking', agentki: 'agentki', scianka: 'scianka', butik: 'butik', galeria: 'galeria',
             agentka: 'agentka', ustawienia: 'ustawienia', znajomi: 'znajomi', skrzynka: 'znajomi', live: 'live'}[p] || (p === 'o-lunie' ? 'home' : '');
const shareOk = views > 1 && !ss('luna.dy.sh');
let pickShare = shareOk && (!ctx || Math.random() < 0.3);

const busy = () => {
  const a = document.activeElement;
  if (a && (a.matches('input:not([type=checkbox]):not([type=radio]):not([type=button]),textarea,select,[contenteditable=""],[contenteditable=true]'))) return true;
  if (Date.now() - lastKey < 4000) return true;
  if (window.LUNA_BUSY || document.querySelector('.recording,.is-recording,[data-recording="1"],body.rec,.mic.on,[aria-label][aria-pressed="true"].mic')) return true;
  if (document.querySelector('dialog[open],.st-sheet:not([hidden]),#ibChat:not([hidden]),.onb:not([hidden]),.lag')) return true;
  const v = [...document.querySelectorAll('.bt-vote:not(.done)')].some(e => { const r = e.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && r.width > 0; });
  return v; // trwa głosowanie w bitwie – nie przeszkadzamy
};
let lastKey = 0; addEventListener('keydown', () => { lastKey = Date.now(); }, true);
const anchor = () => {
  const c = [...document.querySelectorAll('header img[src*="brand-emblem"], .ah-brand img, .logo img, img.hero-luna, .hero img[src*="luna"]')];
  return c.find(e => { const r = e.getBoundingClientRect(); return r.width > 16 && r.bottom > 0 && r.top < innerHeight; });
};
const hitsUI = (r, a) => {
  const pts = [[r.left + 4, r.top + 4], [r.right - 4, r.top + 4], [r.left + 4, r.bottom - 4], [r.right - 4, r.bottom - 4], [(r.left + r.right) / 2, (r.top + r.bottom) / 2]];
  return pts.some(([x, y]) => { if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return true;
    const e = document.elementFromPoint(x, y); if (!e) return false;
    const u = e.closest('button,a,input,select,textarea,label,[role=button],[role=tab],[tabindex]:not([tabindex="-1"])');
    return u && !(a && u.contains(a)); });   // sam logotyp (pod dymkiem) się nie liczy
};

function shareNow(b){
  ss('luna.dy.sh', '1');
  const go = url => {
    const d = {title: 'Luna – mówi jak jest', text: b.textContent.replace(/[✕×]/g, '').trim(), url};
    if (navigator.share) return navigator.share(d).catch(() => {});
    const done = () => { b.querySelector('.dy-t').textContent = L(COPIED); setTimeout(() => hide(b), 2600); };
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(done).catch(() => { try { const i = document.createElement('input'); i.value = url; document.body.appendChild(i); i.select(); document.execCommand('copy'); i.remove(); done(); } catch(e){} });
  };
  const base = location.origin + '/?utm_source=luna&utm_medium=share&utm_campaign=dymek';
  fetch('/api/referral', {credentials: 'same-origin'}).then(r => r.ok ? r.json() : null).then(d => go(d && d.link ? d.link : base)).catch(() => go(base));
}
function hide(b){ if (!b.isConnected) return; b.classList.remove('in'); setTimeout(() => b.remove(), 260); }
async function show(){
  if (busy()) return;
  const a = anchor(); if (!a) return;
  const promo = !pickShare && Math.random() < 0.45 ? await pickPromo() : null;
  if (!promo && !pickShare && !ctx) return;
  if (busy()) return;
  const isShare = pickShare && !promo, P = promo && PROMO[promo];
  const txt = P ? L(P.t) : isShare ? L(SHARE[Math.floor(Math.random() * SHARE.length)]) : L(TIPS[ctx][Math.floor(Math.random() * TIPS[ctx].length)]);
  const b = document.createElement('div');
  b.className = 'dy' + (isShare ? ' dy-sh' : '') + (P ? ' dy-pr' : ''); b.setAttribute('role', 'status'); b.setAttribute('aria-live', 'polite');
  b.innerHTML = `<img class="dy-av" src="/brand-emblem-96.webp" alt="" width="28" height="28"><span class="dy-c">${isShare ? '<button type="button" class="dy-t dy-shb"></button>' : '<span class="dy-t"></span>'}${P ? `<a class="dy-cta" href="${P.href}">${P.ic} ${L(P.c)} ›</a>` : ''}</span><button type="button" class="dy-x" aria-label="${L(CLOSE)}">✕</button>`;
  b.querySelector('.dy-t').textContent = txt;
  b.title = L(CLOSE); document.body.appendChild(b);
  const ar = a.getBoundingClientRect(), br = b.getBoundingClientRect();
  const hd = a.closest('header,.top,.app-head,.ah'), hb = hd ? hd.getBoundingClientRect().bottom : ar.bottom;
  const spots = [[ar.left, ar.bottom + 10, 'tl'], [ar.right + 10, ar.top, 'l'], [Math.max(8, ar.right - br.width), ar.bottom + 10, 'tr'],
                 [Math.max(8, ar.left - 6), Math.max(ar.bottom, hb) + 10, 'tl']];   // pod paskiem nagłówka, ogonek wskazuje logo
  let ok = null;
  for (const [x, y, k] of spots){
    const L0 = Math.min(Math.max(8, x), innerWidth - br.width - 8), T0 = Math.min(Math.max(8, y), innerHeight - br.height - 8);
    b.style.left = L0 + 'px'; b.style.top = T0 + 'px'; b.dataset.tail = k;
    b.style.visibility = 'hidden'; b.style.pointerEvents = 'none';
    const r = b.getBoundingClientRect();
    if (!hitsUI(r, a)){ ok = k; break; }
  }
  if (!ok){ b.remove(); return; }   // brak miejsca, które nie zasłania przycisków – odpuszczamy
  b.style.visibility = ''; b.style.pointerEvents = '';
  ss('luna.dy.n', shown + 1); if (isShare) ss('luna.dy.sh', '1'); if (P) ss('luna.dy.pr', promo);
  requestAnimationFrame(() => b.classList.add('in'));
  const t = setTimeout(() => hide(b), P ? 6500 : isShare ? 6000 : 5000);
  b.onclick = e => { clearTimeout(t);
    if (e.target.closest('.dy-x')){ if (P) ls('luna.dy.x.' + promo, String(Date.now())); return hide(b); }  // odrzucona zachęta wraca najwcześniej za 7 dni
    if (P){ if (!e.target.closest('.dy-cta')) hide(b); return; }
    if (isShare) shareNow(b); else hide(b); };
  addEventListener('scroll', () => hide(b), {once: true, passive: true});
  addEventListener('keydown', () => hide(b), {once: true});
}
const css = document.createElement('style');
css.textContent = `.dy{position:fixed;z-index:60;max-width:min(300px,calc(100vw - 16px));display:flex;gap:10px;align-items:flex-start;padding:10px 8px 10px 10px;
border:0;border-radius:var(--luna-r-bubble,22px);background:linear-gradient(160deg,rgba(38,33,52,.94),rgba(24,21,34,.94));-webkit-backdrop-filter:blur(14px) saturate(1.2);backdrop-filter:blur(14px) saturate(1.2);
color:var(--luna-text,#f3f3f6);box-shadow:var(--luna-shadow-pop,0 14px 40px rgba(0,0,0,.45)),inset 0 0 0 1px rgba(255,255,255,.09);
font:600 14px/1.4 var(--luna-font-body,system-ui,sans-serif);text-align:left;cursor:pointer;opacity:0;transform:translate3d(0,8px,0) scale(.92);transform-origin:top left;
transition:opacity .2s ease,transform .42s cubic-bezier(.34,1.56,.64,1);will-change:transform,opacity}
.dy.in{opacity:1;transform:none}.dy::before{content:"";position:absolute;width:12px;height:12px;background:rgba(36,31,50,.97);transform:rotate(45deg);border-radius:3px;box-shadow:-1px -1px 0 rgba(255,255,255,.08)}
.dy[data-tail=tl]::before{top:-5px;left:20px}.dy[data-tail=tr]::before{top:-5px;right:20px}.dy[data-tail=tr]{transform-origin:top right}.dy[data-tail=l]::before{left:-5px;top:16px}
.dy-av{width:28px;height:28px;border-radius:50%;flex:none;box-shadow:0 0 0 2px rgba(61,220,151,.5)}.dy-c{display:flex;flex-direction:column;gap:6px;padding-top:4px}
.dy-shb{all:unset;cursor:pointer;border-radius:8px}.dy-sh .dy-t{text-decoration:underline dotted #FF9BD2 1px;text-underline-offset:3px}.dy-sh .dy-av{box-shadow:0 0 0 2px rgba(255,111,181,.6)}
.dy-pr .dy-av{box-shadow:0 0 0 2px rgba(179,136,255,.65)}
.dy-cta{align-self:flex-start;padding:7px 14px;border-radius:999px;background:linear-gradient(135deg,#B388FF,#4DD0E1);color:#120f1a;font-weight:800;text-decoration:none;transition:transform .15s ease}
.dy-cta:active{transform:scale(.95)}
.dy-x{all:unset;flex:none;display:grid;place-items:center;width:30px;height:30px;border-radius:50%;opacity:.7;font-size:12px;cursor:pointer}.dy-x:hover{opacity:1;background:rgba(255,255,255,.08)}
.dy-shb:focus-visible,.dy-x:focus-visible,.dy-cta:focus-visible{outline:2px solid var(--luna-emerald,#3DDC97);outline-offset:2px}
@media (prefers-reduced-motion:reduce){.dy{transition:opacity .15s linear;transform:none}.dy-cta{transition:none}}`;
document.head.appendChild(css);
const start = () => setTimeout(show, 2200 + Math.random() * 1500);
if (document.readyState === 'complete') start(); else addEventListener('load', start, {once: true});
})();
