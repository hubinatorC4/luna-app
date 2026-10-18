/* Luna – lekki wybór emoji dla pól czatu (bez bibliotek, zgodny z CSP).
   Użycie: dodaj <script src="/emoji.js" defer></script> (strony z seo.localize mają go automatycznie),
   oznacz pole atrybutem data-emoji albo wywołaj LunaEmoji.attach(inputLubTextarea).
   Pola dodane później (MutationObserver) podpinają się same. data-noemoji wyłącza. */
(() => {
if (window.LunaEmoji) return;
const SEL = '[data-emoji], #input, #liveInput, #inboxInput, #chatInput, .hb-f input, .wallpage textarea.cfield, .chatform input[name=text]';
const T = {
  pl: {btn: 'Wstaw emoji', dlg: 'Emoji', close: 'Zamknij', c: ['Buźki', 'Serca', 'Gesty', 'Muzyka i głos', 'Świętowanie']},
  en: {btn: 'Insert emoji', dlg: 'Emoji', close: 'Close', c: ['Faces', 'Hearts', 'Gestures', 'Music & voice', 'Celebration']},
  es: {btn: 'Insertar emoji', dlg: 'Emojis', close: 'Cerrar', c: ['Caras', 'Corazones', 'Gestos', 'Música y voz', 'Celebración']},
  de: {btn: 'Emoji einfügen', dlg: 'Emojis', close: 'Schließen', c: ['Gesichter', 'Herzen', 'Gesten', 'Musik & Stimme', 'Feiern']},
  uk: {btn: 'Вставити емодзі', dlg: 'Емодзі', close: 'Закрити', c: ['Обличчя', 'Серця', 'Жести', 'Музика й голос', 'Свято']},
};
const SETS = [
  ['😊', '😀', '😂', '🥰', '😍', '😉', '🤔', '😮'],
  ['❤️', '🧡', '💛', '💚', '💙', '💜', '💘', '💖'],
  ['👍', '👏', '🙌', '🙏', '👋', '💪', '✌️', '👌'],
  ['🎤', '🎶', '🎵', '🎙️', '🗣️', '🎧', '🎼', '🔊'],
  ['🎉', '🥳', '✨', '🌟', '🎁', '🏆', '🌸', '🔥'],
];
const lang = () => { const l = (document.documentElement.lang || 'pl').slice(0, 2); return T[l] ? l : 'pl'; };
(() => { if (document.querySelector('link[href^="/emoji.css"]')) return; const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/emoji.css?v=1'; document.head.appendChild(l); })();

let panel = null, cur = null, uid = 0;
function build(){
  const t = T[lang()];
  panel = document.createElement('div'); panel.className = 'emj-panel'; panel.id = 'emjPanel'; panel.hidden = true;
  panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', t.dlg);
  panel.innerHTML = SETS.map((s, i) => `<div class="emj-sec" role="group" aria-label="${t.c[i]}"><div class="emj-h" aria-hidden="true">${t.c[i]}</div><div class="emj-grid">${s.map(e => `<button type="button" class="emj-e" data-e="${e}">${e}</button>`).join('')}</div></div>`).join('')
    + `<button type="button" class="emj-x" aria-label="${t.close}">✕</button>`;
  document.body.appendChild(panel);
  panel.addEventListener('mousedown', e => e.preventDefault()); // nie zabieraj kursora z pola (komputer)
  panel.addEventListener('click', e => {
    const b = e.target.closest('.emj-e'); if (b){ insert(b.dataset.e); return; }
    if (e.target.closest('.emj-x')) close(true);
  });
  panel.addEventListener('keydown', key);
}
function all(){ return [...panel.querySelectorAll('.emj-e')]; }
function key(e){
  const L = all(), i = L.indexOf(document.activeElement), cols = 8;
  let n = -1;
  if (e.key === 'Escape'){ e.preventDefault(); close(true); return; }
  if (e.key === 'Tab'){ close(false); return; }
  if (i < 0) return;
  if (e.key === 'ArrowRight') n = Math.min(L.length - 1, i + 1);
  else if (e.key === 'ArrowLeft') n = Math.max(0, i - 1);
  else if (e.key === 'ArrowDown') n = Math.min(L.length - 1, i + cols);
  else if (e.key === 'ArrowUp') n = Math.max(0, i - cols);
  else if (e.key === 'Home') n = 0; else if (e.key === 'End') n = L.length - 1;
  if (n >= 0){ e.preventDefault(); L.forEach(b => b.tabIndex = -1); L[n].tabIndex = 0; L[n].focus(); }
}
function insert(em){
  const inp = cur && cur.inp; if (!inp) return;
  const v = inp.value, s = inp._emjS != null ? inp._emjS : v.length, en = inp._emjE != null ? inp._emjE : s;
  const max = inp.maxLength > 0 ? inp.maxLength : Infinity;
  if (v.length - (en - s) + em.length > max){ inp.classList.add('emj-full'); setTimeout(() => inp.classList.remove('emj-full'), 600); return; }
  inp.value = v.slice(0, s) + em + v.slice(en);
  const p = s + em.length; inp._emjS = inp._emjE = p;
  try { inp.setSelectionRange(p, p); } catch(e){}
  inp.dispatchEvent(new Event('input', {bubbles: true}));
}
function place(btn){
  const r = btn.getBoundingClientRect(), W = innerWidth, H = innerHeight;
  const pw = Math.min(332, W - 16); panel.style.width = pw + 'px';
  const ph = panel.offsetHeight;
  let left = Math.min(Math.max(8, r.right - pw), W - pw - 8);
  let top = r.top - ph - 8; if (top < 8) top = Math.min(H - ph - 8, r.bottom + 8);
  panel.style.left = left + 'px'; panel.style.top = Math.max(8, top) + 'px';
}
function open(c){
  if (!panel) build();
  cur = c; panel.hidden = false; place(c.btn); c.btn.setAttribute('aria-expanded', 'true');
  const L = all(); L.forEach((b, k) => b.tabIndex = k ? -1 : 0);
  L[0].focus({preventScroll: true});
}
function close(refocus){
  if (!panel || panel.hidden) return;
  panel.hidden = true; if (cur){ cur.btn.setAttribute('aria-expanded', 'false'); if (refocus) cur.inp.focus({preventScroll: true}); }
  cur = null;
}
document.addEventListener('pointerdown', e => { if (panel && !panel.hidden && !panel.contains(e.target) && !(cur && cur.btn.contains(e.target))) close(false); }, true);
addEventListener('resize', () => { if (cur) place(cur.btn); });
addEventListener('scroll', () => { if (cur) place(cur.btn); }, true);

function attach(inp){
  if (!inp || inp._emj || inp.hasAttribute('data-noemoji') || inp.type === 'hidden' || inp.closest('.emj-wrap')) return;
  inp._emj = 1;
  const t = T[lang()];
  const remember = () => { try { inp._emjS = inp.selectionStart; inp._emjE = inp.selectionEnd; } catch(e){} };
  ['keyup', 'click', 'select', 'input', 'blur'].forEach(ev => inp.addEventListener(ev, remember));
  const cs = getComputedStyle(inp);
  const w = document.createElement('span'); w.className = 'emj-wrap' + (inp.tagName === 'TEXTAREA' ? ' emj-ta' : '');
  w.style.flex = cs.flex; if (cs.display === 'block' || inp.tagName === 'TEXTAREA') w.style.display = 'block';
  if (cs.order && cs.order !== '0') w.style.order = cs.order;
  inp.parentNode.insertBefore(w, inp); w.appendChild(inp);
  const b = document.createElement('button'); b.type = 'button'; b.className = 'emj-btn'; b.id = 'emjBtn' + (++uid);
  b.textContent = '😊'; b.setAttribute('aria-label', t.btn); b.title = t.btn;
  b.setAttribute('aria-haspopup', 'dialog'); b.setAttribute('aria-expanded', 'false'); b.setAttribute('aria-controls', 'emjPanel');
  w.appendChild(b);
  const c = {inp, btn: b};
  b.addEventListener('mousedown', e => e.preventDefault());
  b.addEventListener('click', () => { if (cur && cur.btn === b) close(true); else { remember(); if (inp._emjS == null) inp._emjS = inp._emjE = inp.value.length; open(c); } });
}
function scan(root){ (root.querySelectorAll ? root : document).querySelectorAll(SEL).forEach(attach); if (root.matches && root.matches(SEL)) attach(root); }
function start(){
  scan(document);
  new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1 && !(panel && panel.contains(n))) scan(n); })
    .observe(document.body, {childList: true, subtree: true});
}
window.LunaEmoji = {attach, open: inp => { attach(inp); const w = inp.closest('.emj-wrap'); if (w) w.querySelector('.emj-btn').click(); }, close: () => close(false), SETS};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
