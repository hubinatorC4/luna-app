/* Bramka wejściowa „Masz 18 lat?” – Tak / Nie (5 języków). Strona i aplikacja są wyłącznie dla osób 18+.
   • Renderowana po stronie klienta NAD treścią (position:fixed) – treść strony zostaje w HTML, brak przesunięć układu (CLS = 0).
   • Roboty wyszukiwarek i narzędzia audytu (Googlebot, Bingbot, Lighthouse…) nie widzą bramki – SEO bez zmian.
   • „Tak” → zapamiętane na 30 dni (localStorage + ciasteczko) i zapisane na serwerze (adult_confirmed + znacznik czasu).
   • „Nie” → krótki, życzliwy komunikat i blokada (na czas tej sesji przeglądarki).
   API: window.LunaAgeGate.show({account:true}) – prośba o potwierdzenie dla konta bez adult_confirmed. */
(() => {
if (window.LunaAgeGate) return;
const DAY = 864e5, TTL = 30 * DAY, K = 'luna.age18', OLD = 'luna.age';
const BOT = /bot|crawl|spider|slurp|lighthouse|pagespeed|google|bing|yandex|baidu|duckduck|facebookexternalhit|embedly|preview|whatsapp|telegram|discord|semrush|ahrefs/i;
const T = {
  pl: {q: 'Masz 18 lat?', s: 'Luna gada wyłącznie z dorosłymi – resztę zaprasza na bajki na dobranoc 🌙', yes: 'Tak', no: 'Nie', bye: 'Dziękujemy za szczerość 💚 Luna jest tylko dla osób pełnoletnich. Wróć, gdy skończysz 18 lat – Luna poczeka, ona i tak nie śpi 😉', acc: 'Potwierdź raz, że masz ukończone 18 lat – to warunek korzystania z konta.'},
  en: {q: 'Are you 18?', s: 'Luna only chats with grown-ups – everyone else gets bedtime stories 🌙', yes: 'Yes', no: 'No', bye: 'Thanks for being honest 💚 Luna is for adults only. Come back when you turn 18 – Luna will wait, she never sleeps anyway 😉', acc: 'Please confirm once that you are 18 or older – it is required to use your account.'},
  es: {q: '¿Tienes 18 años?', s: 'Luna solo charla con adultos: al resto le recomienda cuentos para dormir 🌙', yes: 'Sí', no: 'No', bye: 'Gracias por tu sinceridad 💚 Luna es solo para personas adultas. Vuelve cuando cumplas 18: Luna esperará, total, nunca duerme 😉', acc: 'Confirma una vez que tienes 18 años o más: es necesario para usar tu cuenta.'},
  de: {q: 'Bist du 18?', s: 'Luna plaudert nur mit Erwachsenen – alle anderen bekommen Gutenachtgeschichten 🌙', yes: 'Ja', no: 'Nein', bye: 'Danke für deine Ehrlichkeit 💚 Luna ist nur für Erwachsene. Komm wieder, wenn du 18 bist – Luna wartet, sie schläft ja sowieso nie 😉', acc: 'Bitte bestätige einmal, dass du mindestens 18 bist – das ist Voraussetzung für dein Konto.'},
  uk: {q: 'Вам є 18?', s: 'Луна спілкується лише з дорослими – решті радить казки на ніч 🌙', yes: 'Так', no: 'Ні', bye: 'Дякуємо за чесність 💚 Луна лише для повнолітніх. Повертайтеся, коли виповниться 18 – Луна зачекає, вона ж однаково не спить 😉', acc: 'Підтвердьте один раз, що вам є 18 – це умова користування акаунтом.'}
};
const lang = () => { let l = ''; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || document.documentElement.lang || navigator.language || 'pl'; } catch(e){ l = 'pl'; } l = String(l).slice(0, 2).toLowerCase(); return T[l] ? l : 'pl'; };
function ok(){
  try {
    const v = JSON.parse(localStorage.getItem(K) || 'null'); if (v && v.yes && Date.now() - v.at < TTL) return true;
    const o = JSON.parse(localStorage.getItem(OLD) || 'null'); if (o && o.adult && o.at && Date.now() - o.at * 1000 < TTL) return true;  // wcześniejsze oświadczenie
  } catch(e){}
  return /(?:^|;\s*)luna_age18=1/.test(document.cookie);
}
function remember(){
  try { localStorage.setItem(K, JSON.stringify({yes: true, at: Date.now()})); localStorage.setItem(OLD, JSON.stringify({adult: true, at: Math.floor(Date.now() / 1000)})); } catch(e){}
  document.cookie = 'luna_age18=1; Path=/; Max-Age=' + (TTL / 1000) + '; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
}
function record(account){
  const vid = window.LunaVid ? window.LunaVid() : (() => { try { return localStorage.getItem('luna.vid') || ''; } catch(e){ return ''; } })();
  if (/^[0-9a-f]{16,32}$/.test(vid || '')) fetch('/api/age/declare', {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({vid, adult_confirmed: true, source: 'gate'})}).catch(() => {});
  if (window.LunaConfirmAdult) return window.LunaConfirmAdult();  // zalogowane konto bez adult_confirmed → zapis na koncie
}
const CSS = `.lag{position:fixed;inset:0;z-index:2147483000;display:grid;place-items:center;padding:20px;background:rgba(6,8,10,.72);-webkit-backdrop-filter:blur(14px) saturate(1.1);backdrop-filter:blur(14px) saturate(1.1);overscroll-behavior:contain;animation:lagIn .28s cubic-bezier(.22,.8,.3,1)}
.lag .lagc{width:min(380px,100%);background:linear-gradient(180deg,#17191c,#101214);color:#f2f2f4;border:1px solid rgba(255,255,255,.08);border-radius:32px;padding:28px 22px 24px;text-align:center;box-shadow:0 30px 80px -20px rgba(0,0,0,.8),0 0 0 6px rgba(61,220,151,.06);font-family:"Nunito",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.lag .lagb{display:inline-grid;place-items:center;width:64px;height:64px;border-radius:50%;margin:0 auto 12px;font:800 22px/1 "Nunito",system-ui,sans-serif;color:#0b0c0d;background:linear-gradient(135deg,#3DDC97,#FF9A3C);box-shadow:0 10px 30px -10px rgba(61,220,151,.6)}
.lag h2{margin:0 0 6px;font:700 28px/1.2 "Playfair Display",Georgia,serif;color:#fff}
.lag p{margin:0 0 18px;font-size:15px;line-height:1.45;color:#c9cbd1}
.lag .lagr{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.lag button{min-height:60px;border:0;border-radius:999px;font:800 20px/1 "Nunito",system-ui,sans-serif;cursor:pointer;transition:transform .2s,box-shadow .2s;touch-action:manipulation}
.lag .y{background:#3DDC97;color:#06120c;box-shadow:0 12px 28px -12px rgba(61,220,151,.8)}
.lag .n{background:#26292e;color:#f2f2f4;border:1px solid rgba(255,255,255,.12)}
.lag button:focus-visible{outline:3px solid #FF9A3C;outline-offset:3px}
.lag button:active{transform:scale(.97)}
.lag .bye{font-size:16px;color:#f2f2f4;margin:6px 0 0}
@keyframes lagIn{from{opacity:0}to{opacity:1}}
@media (prefers-reduced-motion:reduce){.lag{animation:none}}`;
function show(opt){
  opt = opt || {};
  if (document.querySelector('.lag')) return;
  const t = T[lang()];
  if (!document.getElementById('lagCss')){ const st = document.createElement('style'); st.id = 'lagCss'; st.textContent = CSS; document.head.appendChild(st); }
  const w = document.createElement('div'); w.className = 'lag'; w.setAttribute('role', 'dialog'); w.setAttribute('aria-modal', 'true'); w.setAttribute('aria-labelledby', 'lagQ');
  w.innerHTML = `<div class="lagc"><div class="lagb" aria-hidden="true">18+</div><h2 id="lagQ"></h2><p class="s"></p><div class="lagr"><button type="button" class="y"></button><button type="button" class="n"></button></div></div>`;
  w.querySelector('h2').textContent = t.q; w.querySelector('.s').textContent = opt.account ? t.acc : t.s;
  w.querySelector('.y').textContent = t.yes; w.querySelector('.n').textContent = t.no;
  const prevFocus = document.activeElement;
  const stopKeys = e => { if (e.key === 'Escape') e.preventDefault(); if (e.key === 'Tab'){ const b = [...w.querySelectorAll('button')]; if (!b.length) return; const i = b.indexOf(document.activeElement); e.preventDefault(); b[(i + (e.shiftKey ? b.length - 1 : 1)) % b.length].focus(); } };
  document.addEventListener('keydown', stopKeys, true);
  w.querySelector('.y').onclick = async () => {
    remember(); try { sessionStorage.removeItem('luna.age18.no'); } catch(e){}
    try { await record(opt.account); } catch(e){}
    document.removeEventListener('keydown', stopKeys, true); w.remove(); try { prevFocus && prevFocus.focus && prevFocus.focus(); } catch(e){}
    window.dispatchEvent(new CustomEvent('luna-adult', {detail: true}));
  };
  w.querySelector('.n').onclick = () => { try { sessionStorage.setItem('luna.age18.no', '1'); } catch(e){} no(w, t); };
  document.body.appendChild(w); w.querySelector('.y').focus({preventScroll: true});
  try { if (sessionStorage.getItem('luna.age18.no')) no(w, t); } catch(e){}
}
function no(w, t){ const c = w.querySelector('.lagc'); c.querySelector('.lagr').remove(); c.querySelector('.s').remove(); const p = document.createElement('p'); p.className = 'bye'; p.textContent = t.bye; c.appendChild(p); }
const isBot = BOT.test(navigator.userAgent || '');
window.LunaAgeGate = {show, ok, remember};
if (!isBot && !ok()){ if (document.body) show(); else document.addEventListener('DOMContentLoaded', () => show()); }
})();
