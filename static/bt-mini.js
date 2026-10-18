/* Bitwy agentek – lekki moduł globalny (ładowany z defer, nic nie pobiera, dopóki użytkownik sam nie włączy):
   • ustawienia: luna_bt_show (Pokaż bitwy, domyślnie 1), luna_bt_intro (Animacja intro, 1), luna_bt_notify (Powiadom o wyniku, 0);
   • stała pozycja „⚔️ Bitwy” w menu strony; • zminimalizowana bitwa jako przeciągany pasek (luna_bt_min), który nie zasłania nawigacji ani przycisków;
   • opcjonalne powiadomienia o wyniku (centrum powiadomień + toast), tylko po włączeniu. */
(() => {
if (window.LunaBtPrefs) return;
const LS = {get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) {} }};
const DEF = {luna_bt_show: '1', luna_bt_intro: '1', luna_bt_notify: '0', luna_bt_fav_n: '0'};
const wantNotes = () => pref('luna_bt_notify') || pref('luna_bt_fav_n');
const pref = k => (LS.get(k) ?? DEF[k]) === '1';
const L0 = (document.documentElement.lang || 'pl').slice(0, 2);
const T = {
  pl: {nav: 'Bitwy', back: 'Wróć do bitwy', close: 'Zamknij pasek', ended: 'Bitwa zakończona', open: 'Zobacz', drag: 'Przeciągnij, aby przesunąć'},
  en: {nav: 'Battles', back: 'Back to the battle', close: 'Close bar', ended: 'Battle over', open: 'View', drag: 'Drag to move'},
  es: {nav: 'Batallas', back: 'Volver a la batalla', close: 'Cerrar barra', ended: 'Batalla terminada', open: 'Ver', drag: 'Arrastra para mover'},
  de: {nav: 'Battles', back: 'Zurück zum Battle', close: 'Leiste schließen', ended: 'Battle beendet', open: 'Ansehen', drag: 'Zum Verschieben ziehen'},
  uk: {nav: 'Битви', back: 'Повернутися до битви', close: 'Закрити панель', ended: 'Битву завершено', open: 'Переглянути', drag: 'Перетягніть, щоб перемістити'},
}[L0] || null;
const t = T || {nav: 'Bitwy', back: 'Wróć do bitwy', close: 'Zamknij', ended: 'Bitwa zakończona', open: 'Zobacz', drag: ''};
const lq = L0 === 'pl' ? '' : 'lang=' + L0;
const onBattle = /^\/(bitwy)(\.html)?\/?$/.test(location.pathname);
const css = `.bt-off [data-bt]{display:none!important}
.btm{position:fixed;z-index:900;display:flex;align-items:center;gap:6px;height:42px;padding:0 6px 0 14px;border-radius:var(--luna-r-pill,999px);background:var(--luna-surface-2,#1e1a22);color:var(--luna-text,#fff);font:700 13px/1 var(--luna-font-body,system-ui);box-shadow:var(--luna-shadow-pop,0 6px 20px rgba(0,0,0,.45)),0 0 0 1.5px rgba(192,132,252,.55);touch-action:none;user-select:none;-webkit-user-select:none;cursor:pointer;font-variant-numeric:tabular-nums;max-width:calc(100vw - 16px)}
.btm b{color:#ffd36b}.btm .btm-x{all:unset;display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.12);font-size:13px;cursor:pointer}
.btm:focus-visible,.btm .btm-x:focus-visible{outline:2px solid #ffd36b;outline-offset:2px}.btm.drag{opacity:.85;transition:none}.btm.snap{transition:left .2s,top .2s}
.btt{position:fixed;z-index:950;left:50%;--pop-x:-50%;top:calc(env(safe-area-inset-top) + 8px);transform:translateX(-50%);width:min(440px,calc(100vw - 24px));display:flex;gap:10px;align-items:center;padding:12px 12px 12px 16px;border-radius:var(--luna-r-bubble,22px);background:var(--luna-surface-2,#1e1a22);color:var(--luna-text,#fff);font:600 14px/1.4 var(--luna-font-body,system-ui);box-shadow:var(--luna-shadow-pop,0 10px 30px rgba(0,0,0,.5)),0 0 0 1.5px rgba(255,211,107,.45)}
.btt::after{content:'';position:absolute;left:28px;bottom:-7px;width:16px;height:16px;background:inherit;transform:rotate(45deg);border-radius:0 0 5px 0;box-shadow:1.5px 1.5px 0 rgba(255,211,107,.45)}
.btt span{flex:1;cursor:pointer}.btt button{all:unset;cursor:pointer;width:30px;height:30px;display:grid;place-items:center;border-radius:var(--luna-r-pill,999px);background:rgba(255,255,255,.1)}
@media (prefers-reduced-motion:no-preference){.btt{animation:lunaPop var(--luna-t-slow,.25s) var(--luna-ease,ease-out) both}}@keyframes lunaPop{0%{opacity:0;transform:translate(var(--pop-x,0),8px) scale(.94)}100%{opacity:1;transform:translate(var(--pop-x,0),0) scale(1)}}`;
let styled = false; const style = () => { if (styled) return; styled = true; const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); };
function applyShow(){ document.documentElement.classList.toggle('bt-off', !pref('luna_bt_show')); if (!pref('luna_bt_show')) style(); }
applyShow();

/* stała pozycja w menu strony */
function navEntry(){
  const nav = document.querySelector('header.top nav.tabs'); if (!nav || nav.querySelector('a[href^="/bitwy"]')) return;
  const a = document.createElement('a'); a.href = '/bitwy.html' + (lq ? '?' + lq : ''); a.dataset.bt = ''; a.textContent = '⚔️ ' + t.nav;
  const ref = nav.querySelector('a[href^="/galeria"]'); ref ? ref.after(a) : nav.appendChild(a);
}

/* ---------- zminimalizowana bitwa ---------- */
const getMin = () => { try { return JSON.parse(LS.get('luna_bt_min') || 'null'); } catch (e) { return null; } };
const setMin = v => LS.set('luna_bt_min', v ? JSON.stringify(v) : null);
let pill = null, D = null, skew = 0, iv = 0, fv = 0;
function obstacles(){
  // elementy, których pasek nie może zasłaniać: nagłówek, dolna nawigacja, pływające przyciski
  const out = []; const sel = 'header, nav, .tabs, .ah, .hb-fab, .tabbar, .bottom-nav, footer.fixed, [data-fixed], .toast:not([hidden])';
  document.querySelectorAll(sel).forEach(e => { if (e === pill || pill && pill.contains(e)) return; const cs = getComputedStyle(e); if (cs.position !== 'fixed' && cs.position !== 'sticky') return; const r = e.getBoundingClientRect(); if (r.width && r.height && r.bottom > 0 && r.top < innerHeight) out.push(r); });
  return out;
}
function place(side, top){
  const h = pill.offsetHeight || 40, w = pill.offsetWidth || 160, m = 8;
  const sa = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sat')) || 0;
  let y = Math.max(m + sa, Math.min(top, innerHeight - h - m));
  const x = side === 'right' ? innerWidth - w - m : m;
  const hits = r => !(x + w <= r.left || x >= r.right || y + h <= r.top || y >= r.bottom);
  for (let i = 0; i < 12; i++){ const r = obstacles().find(hits); if (!r) break; y = r.top - h - m < m ? r.bottom + m : r.top - h - m; }
  y = Math.max(m, Math.min(y, innerHeight - h - m));
  pill.style.left = x + 'px'; pill.style.top = y + 'px'; return {side, top: y};
}
function fmtLeft(s){ s = Math.max(0, s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = Math.floor(s % 60); return `${h}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}`; }
const pctStr = (a, b) => { const p = a + b ? a * 100 / (a + b) : 50; return p.toLocaleString(L0 === 'uk' ? 'uk-UA' : L0, {minimumFractionDigits: 1, maximumFractionDigits: 1}) + '%'; };
function paint(){
  if (!pill) return; const st = getMin(); const lab = pill.querySelector('.btm-l');
  if (!D){ lab.textContent = '⚔️ …'; return; }
  const b = D.battle;
  if (!b || b.id !== st.bid){ lab.innerHTML = `🏆 ${t.ended} · <b>${t.open}</b>`; return; }
  lab.innerHTML = `⚔️ ${fmtLeft(b.end - (Date.now() / 1000 + skew))} · <b>${pctStr(b.votes.a, b.votes.b)}</b>`;
}
async function fetchState(){
  const st = getMin(); if (!st || document.hidden) return;
  try { const r = await fetch('/api/battles?b=' + encodeURIComponent(st.bid), {credentials: 'same-origin'}); D = await r.json(); skew = D.now - Date.now() / 1000; } catch (e) {}
  paint();
}
function startTimers(){ stopTimers(); if (document.hidden) return; iv = setInterval(paint, 1000); fv = setInterval(fetchState, 30000); }
function stopTimers(){ clearInterval(iv); clearInterval(fv); }
function showPill(){
  const st = getMin(); if (!st || onBattle || !pref('luna_bt_show') || pill) return;
  style(); pill = document.createElement('div'); pill.className = 'btm'; pill.dataset.bt = ''; pill.setAttribute('role', 'button'); pill.tabIndex = 0;
  pill.setAttribute('aria-label', t.back); pill.title = t.back + ' · ' + t.drag;
  pill.innerHTML = `<span class="btm-l">⚔️ …</span><button type="button" class="btm-x" aria-label="${t.close}">✕</button>`;
  document.body.appendChild(pill);
  const pos = st.pos || {side: 'left', top: innerHeight - 170}; st.pos = place(pos.side, pos.top); setMin(st);
  const open = () => { location.href = '/bitwy.html?b=' + encodeURIComponent(st.bid) + '&restore=1' + (lq ? '&' + lq : ''); };
  pill.querySelector('.btm-x').onclick = e => { e.stopPropagation(); setMin(null); pill.remove(); pill = null; stopTimers(); };
  pill.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); open(); } if (e.key === 'Delete' || e.key === 'Escape'){ pill.querySelector('.btm-x').click(); } });
  let sx = 0, sy = 0, ox = 0, oy = 0, moved = false, down = false;
  pill.addEventListener('pointerdown', e => { if (e.target.closest('.btm-x')) return; down = true; moved = false; sx = e.clientX; sy = e.clientY; const r = pill.getBoundingClientRect(); ox = r.left; oy = r.top; pill.setPointerCapture(e.pointerId); });
  pill.addEventListener('pointermove', e => { if (!down) return; const dx = e.clientX - sx, dy = e.clientY - sy; if (!moved && Math.hypot(dx, dy) < 6) return; moved = true; pill.classList.add('drag'); pill.classList.remove('snap'); pill.style.left = (ox + dx) + 'px'; pill.style.top = (oy + dy) + 'px'; });
  pill.addEventListener('pointerup', e => { if (!down) return; down = false; pill.classList.remove('drag');
    if (!moved){ open(); return; }
    const r = pill.getBoundingClientRect(); pill.classList.add('snap'); const s = getMin() || st; s.pos = place(r.left + r.width / 2 < innerWidth / 2 ? 'left' : 'right', r.top); setMin(s); });
  addEventListener('resize', () => { const s = getMin(); if (pill && s && s.pos) place(s.pos.side, s.pos.top); });
  fetchState(); startTimers();
}
document.addEventListener('visibilitychange', () => { if (!pill) return; if (document.hidden) stopTimers(); else { fetchState(); startTimers(); } });

/* ---------- powiadomienia o wyniku (opcjonalne) ---------- */
let csrf = null;
async function notes(){
  if (!wantNotes() || document.hidden) return [];
  try { const r = await fetch('/api/battles/notes?lang=' + L0, {credentials: 'same-origin'}); if (!r.ok) return []; const d = await r.json(); return d.items || []; } catch (e) { return []; }
}
async function seen(bids){
  try { if (csrf == null){ const m = await (await fetch('/api/account/me', {credentials: 'same-origin'})).json(); csrf = m.csrf || ''; }
    await fetch('/api/battles/notes/seen', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify({bids})}); } catch (e) {}
}
function toast(n){
  style(); document.querySelectorAll('.btt').forEach(x => x.remove());
  const el = document.createElement('div'); el.className = 'btt'; el.dataset.bt = ''; el.setAttribute('role', 'status');
  const s = document.createElement('span'); s.textContent = n.text; el.appendChild(s);
  const x = document.createElement('button'); x.type = 'button'; x.textContent = '✕'; x.setAttribute('aria-label', t.close); el.appendChild(x);
  s.onclick = () => { location.href = '/bitwy.html?sum=' + encodeURIComponent(n.bid) + (lq ? '&' + lq : ''); };
  x.onclick = () => el.remove(); document.body.appendChild(el);
  let top = 8; document.querySelectorAll('header, .bt-topbar, .ah').forEach(h => { const cs = getComputedStyle(h), r = h.getBoundingClientRect(); if ((cs.position === 'fixed' || cs.position === 'sticky') && r.top <= 1 && r.bottom > 0) top = Math.max(top, r.bottom + 8); }); el.style.top = `calc(env(safe-area-inset-top) + ${Math.round(top)}px)`; setTimeout(() => el.remove(), 8000);
}
async function checkNotes(){
  const N = await notes(); const fresh = N.filter(n => !n.seen); if (!fresh.length) return;
  toast(fresh[0]); seen(fresh.map(n => n.bid));
  document.dispatchEvent(new CustomEvent('lunabt:notes', {detail: N}));
}
let nv = 0;
function notesLoop(){ clearInterval(nv); if (!wantNotes()) return; checkNotes(); nv = setInterval(() => { if (!document.hidden) checkNotes(); }, 60000); }


/* ---------- ustawienia (strona Bitew i Ustawienia aplikacji: elementy [data-bt-settings]) ---------- */
const ST = {
  pl: {h: '⚔️ Bitwy agentek', show: 'Pokaż bitwy', show_d: 'Wyłączenie ukrywa wszystkie elementy Bitew, także pływający pasek.', intro: 'Animacja intro', intro_d: 'Krótkie intro po wejściu do bitwy (zawsze z „Pomiń”).',
       notify: 'Powiadom mnie o wyniku bitwy', notify_d: 'Domyślnie wyłączone. Wynik pojawi się w aplikacji; push tylko po Twojej zgodzie w przeglądarce.', login: 'Zaloguj się, aby włączyć powiadomienia o wyniku.', denied: 'Push zablokowany w przeglądarce – wynik zobaczysz w aplikacji.', notes: 'Powiadomienia', none: 'Brak powiadomień.'},
  en: {h: '⚔️ Agent battles', show: 'Show battles', show_d: 'Turning this off hides all battle elements, including the floating bar.', intro: 'Intro animation', intro_d: 'A short intro when you enter a battle (always with “Skip”).',
       notify: 'Notify me about the battle result', notify_d: 'Off by default. The result appears in the app; push only after you allow it in the browser.', login: 'Log in to turn on result notifications.', denied: 'Push is blocked in the browser – you’ll see the result in the app.', notes: 'Notifications', none: 'No notifications.'},
  es: {h: '⚔️ Batallas de agentes', show: 'Mostrar batallas', show_d: 'Al desactivarlo se ocultan todos los elementos de las batallas, también la barra flotante.', intro: 'Animación de intro', intro_d: 'Una intro breve al entrar en una batalla (siempre con «Saltar»).',
       notify: 'Avisarme del resultado de la batalla', notify_d: 'Desactivado por defecto. El resultado aparece en la app; push solo si lo permites en el navegador.', login: 'Inicia sesión para activar los avisos de resultado.', denied: 'Push bloqueado en el navegador: verás el resultado en la app.', notes: 'Notificaciones', none: 'Sin notificaciones.'},
  de: {h: '⚔️ Agentinnen-Battles', show: 'Battles anzeigen', show_d: 'Ausschalten blendet alle Battle-Elemente aus, auch die schwebende Leiste.', intro: 'Intro-Animation', intro_d: 'Kurzes Intro beim Betreten eines Battles (immer mit „Überspringen“).',
       notify: 'Über das Battle-Ergebnis benachrichtigen', notify_d: 'Standardmäßig aus. Das Ergebnis erscheint in der App; Push nur nach deiner Erlaubnis im Browser.', login: 'Melde dich an, um Ergebnis-Benachrichtigungen einzuschalten.', denied: 'Push ist im Browser blockiert – du siehst das Ergebnis in der App.', notes: 'Benachrichtigungen', none: 'Keine Benachrichtigungen.'},
  uk: {h: '⚔️ Битви агенток', show: 'Показувати битви', show_d: 'Вимкнення приховує всі елементи битв, зокрема плаваючу панель.', intro: 'Анімація інтро', intro_d: 'Коротке інтро під час входу в битву (завжди з «Пропустити»).',
       notify: 'Повідомити мене про результат битви', notify_d: 'Типово вимкнено. Результат з’явиться в застосунку; push – лише після вашого дозволу в браузері.', login: 'Увійдіть, щоб увімкнути сповіщення про результат.', denied: 'Push заблоковано в браузері – результат побачите в застосунку.', notes: 'Сповіщення', none: 'Немає сповіщень.'},
}[L0] || null;
const b64 = s => { const p = '='.repeat((4 - s.length % 4) % 4); const r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...r].map(c => c.charCodeAt(0))); };
async function notifyServer(on, sub){
  if (csrf == null){ const m = await (await fetch('/api/account/me', {credentials: 'same-origin'})).json(); csrf = m.user ? (m.csrf || '') : ''; }
  if (!csrf) throw new Error('login');
  const r = await fetch('/api/battles/notify', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify({on, lang: L0, sub: sub || null})});
  if (!r.ok) throw new Error(r.status === 401 ? 'login' : 'err');
}
async function pushOptIn(after){
  // tylko po włączeniu przełącznika (gest użytkownika) i tylko gdy przeglądarka i serwer obsługują push
  if (!('serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window)) return 'na';
  const k = await (await fetch('/api/push/key')).json(); if (!k.enabled || !k.key) return 'na';
  const perm = Notification.permission === 'default' ? await Notification.requestPermission() : Notification.permission;
  if (perm !== 'granted') return 'denied';
  const reg = await navigator.serviceWorker.register('/sw.js'); await navigator.serviceWorker.ready;
  const sub = (await reg.pushManager.getSubscription()) || await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64(k.key)});
  if (after) await after(sub.toJSON()); else await notifyServer(true, sub.toJSON()); return 'ok';
}
let css2on = false;
function renderSettings(host){
  const s = ST || {}; style(); if (!css2on){ css2on = true; const s2 = document.createElement('style'); s2.textContent = css2; document.head.appendChild(s2); }
  const row = (k, label, desc) => `<label class="bts-row"><input type="checkbox" data-k="${k}"${pref(k) ? ' checked' : ''}><span><b>${label}</b><small>${desc}</small></span></label>`;
  host.innerHTML = `<div class="bts"><h3>${s.h}</h3>${row('luna_bt_show', s.show, s.show_d)}${row('luna_bt_intro', s.intro, s.intro_d)}${row('luna_bt_notify', s.notify, s.notify_d)}<p class="bts-msg" role="status"></p>
    <h4>${s.notes}</h4><div class="bts-notes"></div></div>`;
  const msg = host.querySelector('.bts-msg');
  host.querySelectorAll('input[data-k]').forEach(i => i.onchange = async () => {
    const k = i.dataset.k, on = i.checked; msg.textContent = '';
    if (k !== 'luna_bt_notify'){ window.LunaBtPrefs.set(k, on); return; }
    try { await notifyServer(on); window.LunaBtPrefs.set(k, on);
      if (on){ const r = await pushOptIn().catch(() => 'na'); if (r === 'denied') msg.textContent = s.denied; } }
    catch (e){ i.checked = !on; msg.textContent = e.message === 'login' ? s.login : '…'; }
  });
  const list = async () => { const N = await notes(); const box = host.querySelector('.bts-notes'); if (!box) return;
    box.innerHTML = N.length ? '' : `<small>${s.none}</small>`;
    N.slice(0, 10).forEach(n => { const a = document.createElement('a'); a.className = 'bts-n' + (n.seen ? '' : ' new'); a.href = '/bitwy.html?sum=' + encodeURIComponent(n.bid) + (lq ? '&' + lq : ''); a.textContent = n.text; box.appendChild(a); }); };
  list(); document.addEventListener('lunabt:notes', list);
}
const css2 = `.bts h3{margin:0 0 8px;font-size:16px}.bts h4{margin:14px 0 6px;font-size:14px}.bts-row{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid rgba(127,127,127,.2);cursor:pointer}
.bts-row input{width:20px;height:20px;margin-top:2px;flex:0 0 auto}.bts-row span{display:flex;flex-direction:column;gap:2px}.bts-row small{opacity:.75;font-size:12px}.bts-msg{font-size:12px;color:#ffb347;min-height:1em;margin:6px 0 0}
.bts-notes{display:flex;flex-direction:column;gap:6px}.bts-n{display:block;padding:8px 10px;border-radius:10px;background:rgba(127,127,127,.12);color:inherit;text-decoration:none;font-size:13px}.bts-n.new{box-shadow:inset 3px 0 0 #ffd36b}`;
window.LunaBtPrefs = {
  push: after => pushOptIn(after),
  get: pref, set: (k, on) => { LS.set(k, on ? '1' : '0'); if (k === 'luna_bt_show'){ applyShow(); if (!on && pill){ pill.remove(); pill = null; stopTimers(); } else showPill(); } if (k === 'luna_bt_notify' || k === 'luna_bt_fav_n') notesLoop(); },
  minimize: st => setMin(st), renderSettings, restoreState: () => { const s = getMin(); setMin(null); return s; }, notes, seen, toast,
};
const boot = () => { navEntry(); showPill(); notesLoop(); document.querySelectorAll('[data-bt-settings]').forEach(renderSettings); };
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', boot) : boot();
})();
