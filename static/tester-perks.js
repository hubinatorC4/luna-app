/* 🎟️ Dodatki testera (egzekwowane na serwerze: /api/tester/perks, /api/tester/frame, awatary w /api/me/profile, filtr emotek):
   1) emotki :t-…: zamieniane na obrazki w czacie, komentarzach, DM i Live (nie-testerom serwer je usuwa przy wysyłaniu),
   2) pasek emotek przy polach czatu/komentarzy – tylko dla testerów,
   3) karta „Dodatki testera” w Mój panel i w ustawieniach aplikacji: odznaka, kolor ramki, awatary testerów, lista emotek. */
(() => {
const EM = ['mic', 'luna', 'fala', 'brawo', 'hehe', 'ok', 'serce'];
const RE = /:t-(mic|luna|fala|brawo|hehe|ok|serce):/g;
const lang = () => { const l = (document.documentElement.lang || 'pl').slice(0, 2); return ['pl', 'en', 'es', 'de', 'uk'].includes(l) ? l : 'pl'; };
const LI = {pl: 0, en: 1, es: 2, de: 3, uk: 4};
const S = {
  h: ['🎟️ Dodatki testera', '🎟️ Tester extras', '🎟️ Extras de tester', '🎟️ Tester-Extras', '🎟️ Бонуси тестувальника'],
  badge: ['Odznaka testera – masz ją, bo jesteś z pierwszego tysiąca 💜', 'Tester badge – yours because you’re one of the first thousand 💜', 'Insignia de tester: es tuya por estar entre los primeros mil 💜', 'Tester-Abzeichen – deins, weil du zu den ersten Tausend gehörst 💜', 'Значок тестувальника – він ваш, бо ви з першої тисячі 💜'],
  frame: ['Kolor ramki awatara', 'Avatar frame colour', 'Color del marco del avatar', 'Farbe des Avatar-Rahmens', 'Колір рамки аватара'],
  frame_h: ['Fioletowa i niebieska to klasyka testerów; reszta to łagodne odcienie do wyboru. Kolory moderatora i Modelek są zastrzeżone.', 'Purple and blue are the tester classics; the rest are soft shades to choose from. Moderator and Model colours are reserved.', 'Morado y azul son los clásicos de los testers; el resto son tonos suaves a elegir. Los colores del moderador y de las Modelos están reservados.', 'Lila und Blau sind die Tester-Klassiker; der Rest sind sanfte Töne zur Auswahl. Farben von Moderator und Models sind reserviert.', 'Фіолетова й синя – класика тестувальників; решта – м’які відтінки на вибір. Кольори модератора й Моделей зарезервовані.'],
  av: ['Awatary testerów', 'Tester avatars', 'Avatares de tester', 'Tester-Avatare', 'Аватари тестувальників'],
  av_set: ['Ustaw', 'Use', 'Usar', 'Verwenden', 'Встановити'],
  emo: ['Ekskluzywne emotki – wpisz kod albo kliknij przy polu czatu/komentarza', 'Exclusive emotes – type the code or tap one next to a chat/comment box', 'Emoticonos exclusivos: escribe el código o tócalo junto al cuadro de chat/comentario', 'Exklusive Emotes – Code eintippen oder neben dem Chat-/Kommentarfeld antippen', 'Ексклюзивні емодзі – введіть код або натисніть біля поля чату/коментаря'],
  saved: ['Zapisane ✨', 'Saved ✨', 'Guardado ✨', 'Gespeichert ✨', 'Збережено ✨'],
  copied: ['Skopiowano', 'Copied', 'Copiado', 'Kopiert', 'Скопійовано'],
  lock_h: ['🎟️ Dodatki tylko dla testerów', '🎟️ Tester-only extras', '🎟️ Extras solo para testers', '🎟️ Extras nur für Tester', '🎟️ Бонуси лише для тестувальників'],
  lock: ['Odznaka, ekskluzywne emotki, specjalne awatary i kolor ramki – odblokujesz je kodem testera (podepnij go do konta). Miejsc jest 1000, licznik nie kłamie.', 'A badge, exclusive emotes, special avatars and a frame colour – unlocked with a tester code linked to your account. There are 1000 spots and the counter doesn’t lie.', 'Insignia, emoticonos exclusivos, avatares especiales y color de marco: se desbloquean con un código de tester vinculado a tu cuenta. Hay 1000 plazas y el contador no miente.', 'Abzeichen, exklusive Emotes, spezielle Avatare und Rahmenfarbe – freigeschaltet mit einem Tester-Code, der mit deinem Konto verknüpft ist. Es gibt 1000 Plätze, der Zähler lügt nicht.', 'Значок, ексклюзивні емодзі, спеціальні аватари й колір рамки – відкриваються кодом тестувальника, прив’язаним до акаунта. Місць 1000, лічильник не бреше.'],
  join: ['Zostań testerem →', 'Become a tester →', 'Hazte tester →', 'Tester werden →', 'Стати тестувальником →'],
};
const t = k => S[k][LI[lang()]];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

/* 1) renderowanie emotek w treści */
const SKIP = /^(SCRIPT|STYLE|TEXTAREA|INPUT|CODE|PRE|NOSCRIPT)$/;
function render(root){
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode: n => (n.nodeValue.indexOf(':t-') >= 0 && !(n.parentNode && (SKIP.test(n.parentNode.nodeName) || n.parentNode.isContentEditable))) ? 1 : 3});
  const L = []; let n; while ((n = w.nextNode())) L.push(n);
  L.forEach(n => {
    const s = n.nodeValue; RE.lastIndex = 0; if (!RE.test(s)) return; RE.lastIndex = 0;
    const f = document.createDocumentFragment(); let i = 0, m;
    while ((m = RE.exec(s))){ if (m.index > i) f.appendChild(document.createTextNode(s.slice(i, m.index)));
      const im = document.createElement('img'); im.src = `/tester/emotes/${m[1]}.svg`; im.alt = m[0]; im.title = m[0]; im.className = 't-emo'; im.width = 22; im.height = 22; im.loading = 'lazy';
      im.style.cssText = 'width:1.35em;height:1.35em;vertical-align:-.3em;margin:0 .05em'; f.appendChild(im); i = m.index + m[0].length; }
    if (i < s.length) f.appendChild(document.createTextNode(s.slice(i)));
    n.parentNode.replaceChild(f, n);
  });
}
let pend = false;
const mo = new MutationObserver(() => { if (pend) return; pend = true; requestAnimationFrame(() => { pend = false; render(document.body); }); });
function startRender(){ render(document.body); mo.observe(document.body, {childList: true, subtree: true, characterData: true}); }

/* 2) pasek emotek przy polach czatu/komentarzy (tylko testerzy) */
let bar = null, target = null;
const FORMS_EXCLUDE = '.tmf,.f18,.f18f,form[data-f18],.tst-form,.lr-sheet,#a_form,.st-form,[data-no-emotes]';
function isChatField(el){
  if (!el || !(el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search' && false)))) return false;
  if (el.closest(FORMS_EXCLUDE)) return false;
  if (el.type === 'email' || el.type === 'password' || /mail|nick|name|code|kod|tester|url|link/i.test((el.name || '') + (el.id || ''))) return false;
  return true;
}
function showBar(el){
  target = el;
  if (!bar){
    bar = document.createElement('div'); bar.className = 't-emobar'; bar.setAttribute('role', 'toolbar'); bar.setAttribute('aria-label', t('h'));
    bar.style.cssText = 'position:fixed;z-index:9998;display:flex;gap:4px;padding:5px 7px;border-radius:999px;background:rgba(20,16,32,.94);border:1px solid rgba(139,92,246,.55);box-shadow:0 10px 26px -10px rgba(0,0,0,.7)';
    bar.innerHTML = `<img src="/tester/badge.svg" alt="" width="20" height="20" style="width:20px;height:20px;align-self:center;opacity:.9">` + EM.map(e => `<button type="button" data-e="${e}" aria-label=":t-${e}:" style="border:0;background:none;padding:2px;cursor:pointer;line-height:0"><img src="/tester/emotes/${e}.svg" alt="" width="26" height="26"></button>`).join('');
    bar.addEventListener('mousedown', e => e.preventDefault());
    bar.addEventListener('click', e => { const b = e.target.closest('[data-e]'); if (!b || !target) return; const code = `:t-${b.dataset.e}: `;
      const s = target.selectionStart ?? target.value.length, en = target.selectionEnd ?? s; target.setRangeText ? target.setRangeText(code, s, en, 'end') : (target.value += code);
      target.dispatchEvent(new Event('input', {bubbles: true})); target.focus(); });
    document.body.appendChild(bar);
  }
  const r = el.getBoundingClientRect(); const top = r.top > 60 ? r.top - 46 : r.bottom + 6;
  bar.style.left = Math.max(6, Math.min(r.left, innerWidth - 300)) + 'px'; bar.style.top = top + 'px'; bar.hidden = false;
}
function startBar(){
  document.addEventListener('focusin', e => { if (isChatField(e.target)) showBar(e.target); });
  document.addEventListener('focusout', e => { setTimeout(() => { if (bar && document.activeElement !== target) bar.hidden = true; }, 150); });
  addEventListener('scroll', () => { if (bar && !bar.hidden && target) showBar(target); }, {passive: true});
}

/* 3) karta w Mój panel / ustawieniach aplikacji */
let P = null, CSRF = '';
function card(){
  if (!P.tester) return `<section class="tp-card" id="tpCard" style="margin:14px 0;padding:16px 18px;border-radius:24px;border:1px dashed rgba(139,92,246,.5);background:rgba(139,92,246,.07)">
    <h2 style="margin:0 0 6px;font-size:18px">${t('lock_h')}</h2><p style="margin:0 0 8px;font-size:14px;opacity:.88">${t('lock')}</p>
    <div style="display:flex;gap:6px;opacity:.55" aria-hidden="true">${EM.slice(0, 5).map(e => `<img src="/tester/emotes/${e}.svg" alt="" width="28" height="28">`).join('')}</div>
    <a class="pill" href="/testerzy.html" style="display:inline-block;margin-top:10px">${t('join')}</a></section>`;
  const li = LI[lang()];
  return `<section class="tp-card" id="tpCard" style="margin:14px 0;padding:16px 18px;border-radius:24px;border:1px solid rgba(139,92,246,.45);background:linear-gradient(135deg,rgba(139,92,246,.14),rgba(59,130,246,.10))">
    <h2 style="margin:0 0 8px;font-size:18px">${t('h')}</h2>
    <p style="display:flex;gap:10px;align-items:center;margin:0 0 12px"><img src="${esc(P.badge)}" alt="" width="40" height="40"><span>${t('badge')}</span></p>
    <h3 style="margin:8px 0 4px;font-size:15px">${t('frame')}</h3><p style="margin:0 0 8px;font-size:13px;opacity:.8">${t('frame_h')}</p>
    <div class="tp-frames" role="radiogroup" aria-label="${esc(t('frame'))}" style="display:flex;flex-wrap:wrap;gap:8px">${P.frames.map(f => `<button type="button" role="radio" aria-checked="${f.id === P.frame}" data-f="${f.id}" title="${esc(f.names[li])}" style="display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;border:2px solid ${f.id === P.frame ? f.color : 'rgba(255,255,255,.14)'};background:rgba(0,0,0,.25);color:inherit;cursor:pointer;font-size:13px"><i style="width:18px;height:18px;border-radius:50%;background:${f.color};box-shadow:0 0 8px ${f.color}"></i>${esc(f.names[li])}</button>`).join('')}</div>
    <h3 style="margin:14px 0 6px;font-size:15px">${t('av')}</h3>
    <div style="display:flex;flex-wrap:wrap;gap:10px">${P.avatars.map(a => `<button type="button" data-av="${a}" aria-label="${esc(t('av_set'))} ${esc(a.slice(14))}" style="border:0;background:none;padding:0;cursor:pointer"><img src="/avatars/preset-${a.slice(7)}.svg" alt="" width="64" height="64" style="border-radius:50%;box-shadow:0 0 0 3px ${P.color}"></button>`).join('')}</div>
    <h3 style="margin:14px 0 6px;font-size:15px">${t('emo')}</h3>
    <div style="display:flex;flex-wrap:wrap;gap:8px">${P.emotes.map(e => `<button type="button" data-copy="${e.code}" title="${e.code}" style="display:flex;align-items:center;gap:4px;border:1px solid rgba(255,255,255,.12);border-radius:12px;background:rgba(0,0,0,.2);color:inherit;padding:4px 8px;cursor:pointer;font-size:12px"><img src="${e.src}" alt="" width="26" height="26">${e.code}</button>`).join('')}</div>
    <p class="tp-msg" role="status" style="min-height:1.2em;margin:8px 0 0;font-size:13px"></p></section>`;
}
function paintAvatar(){
  if (!P || !P.tester) return;
  document.querySelectorAll('.st-av:not(.mod-av):not(.mdl-ring)').forEach(a => { a.style.boxShadow = `0 0 0 3px ${P.color}, 0 0 14px ${P.color}`; });
  const n = document.querySelector('.st-nick'); if (n && !n.querySelector('.t-badge')) n.insertAdjacentHTML('beforeend', ` <img class="t-badge" src="${esc(P.badge)}" alt="Tester" title="Tester" width="22" height="22" style="vertical-align:-4px">`);
  document.documentElement.style.setProperty('--uring', P.color);
}
function wire(c){
  const msg = c.querySelector('.tp-msg');
  const post = async (url, body) => { const r = await fetch(url, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': CSRF, ...(localStorage.getItem('luna.tester') ? {'X-Tester': localStorage.getItem('luna.tester')} : {})}, body: JSON.stringify(body)});
    const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.error || r.status); return j; };
  c.querySelectorAll('[data-f]').forEach(b => b.onclick = async () => { try { const j = await post('/api/tester/frame', {frame: b.dataset.f}); P.frame = b.dataset.f; P.color = j.color; mount(true); paintAvatar(); document.querySelector('#tpCard .tp-msg').textContent = t('saved'); } catch(e){ msg.textContent = '⚠️ ' + e.message; } });
  c.querySelectorAll('[data-av]').forEach(b => b.onclick = async () => { try { await post('/api/me/profile', {avatar: b.dataset.av}); msg.textContent = t('saved'); document.querySelectorAll('.st-av').forEach(a => { if (a.tagName === 'IMG') a.src = '/avatars/preset-' + b.dataset.av.slice(7) + '.svg'; }); } catch(e){ msg.textContent = '⚠️ ' + e.message; } });
  c.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => { (navigator.clipboard ? navigator.clipboard.writeText(b.dataset.copy) : Promise.reject()).then(() => { msg.textContent = t('copied') + ': ' + b.dataset.copy; }).catch(() => {}); });
}
function mount(force){
  const app = document.getElementById('stApp'), appCard = document.querySelector('[data-tester-perks]');
  let host = null, where = null;
  if (app && document.getElementById('stHead')){ host = document.getElementById('stHead'); where = 'afterend'; }
  else if (appCard){ host = appCard; where = 'afterend'; }
  if (!host) return;
  if (!P.tester && host === appCard) return;   // w aplikacji karta promocyjna już zaprasza
  const old = document.getElementById('tpCard'); if (old && !force) return; if (old) old.remove();
  host.insertAdjacentHTML(where, card()); const c = document.getElementById('tpCard'); if (P.tester) wire(c); paintAvatar();
}
async function init(){
  startRender();
  const h = {}; const tc = localStorage.getItem('luna.tester'); if (tc) h['X-Tester'] = tc;
  try { P = await (await fetch('/api/tester/perks', {credentials: 'same-origin', headers: h})).json(); } catch(e){ return; }
  window.LunaTesterPerks = P;
  if (P.tester) startBar();
  if (document.getElementById('stApp') || document.querySelector('[data-tester-perks]')){
    try { CSRF = (await (await fetch('/api/account/me', {credentials: 'same-origin'})).json()).csrf || ''; } catch(e){}
    mount(); const app = document.getElementById('stApp'); if (app) new MutationObserver(() => mount()).observe(app, {childList: true});
  }
}
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
