/* Luna – ikona Skrzynki z licznikiem nieprzeczytanych w nagłówku aplikacji + wpis w „Więcej”. Lekki: pierwszy odczyt dopiero po załadowaniu strony (bezczynność), potem co 90 s tylko przy widocznej karcie. */
(() => {
const lang = (document.documentElement.lang || 'pl').slice(0, 2);
const W = {pl: ['Skrzynka', 'Znajomi', 'Wiadomości, znajomi i prywatny czat', 'nieprzeczytanych'], en: ['Inbox', 'Friends', 'Messages, friends and private chat', 'unread'],
  es: ['Buzón', 'Amigos', 'Mensajes, amigos y chat privado', 'sin leer'], de: ['Postfach', 'Freunde', 'Nachrichten, Freunde und privater Chat', 'ungelesen'],
  uk: ['Скринька', 'Друзі', 'Повідомлення, друзі й приватний чат', 'непрочитаних']}[lang] || ['Skrzynka', 'Znajomi', '', 'nieprzeczytanych'];
const open = (p) => { if (window.LunaShell && LunaShell.openPage) LunaShell.openPage(p); else location.href = p + (lang !== 'pl' ? '?lang=' + lang : ''); };
const acts = document.querySelector('.ah-acts');
let btn = null;
if (acts && !document.getElementById('ibBtn')){
  btn = document.createElement('button'); btn.type = 'button'; btn.id = 'ibBtn'; btn.className = 'ah-ib'; btn.setAttribute('aria-label', W[0]); btn.title = W[0];
  btn.innerHTML = '<span aria-hidden="true">📬</span><b class="ah-ib-n" hidden></b>';
  btn.onclick = () => open('/skrzynka.html');
  acts.prepend(btn);
  const st = document.createElement('style');
  st.textContent = `.ah-ib{position:relative;width:42px;height:42px;display:grid;place-items:center;border:0;border-radius:50%!important;background:var(--luna-surface-2,#1e1a22);color:inherit;font-size:20px;cursor:pointer;margin-right:8px;box-shadow:var(--luna-shadow-soft)}
.ah-ib-n{position:absolute;top:-4px;right:-4px;min-width:20px;height:20px;padding:0 5px;border-radius:999px;background:var(--luna-pink,#FF6FB5);color:#2a0716;font:700 11.5px/20px var(--luna-font-head,system-ui);text-align:center;box-shadow:0 0 0 2px #0b0705;animation:lunaPop .25s var(--luna-ease,ease) both}
.ah-ib-n[hidden]{display:none}@media (prefers-reduced-motion:reduce){.ah-ib-n{animation:none}}`;
  document.head.appendChild(st);
}
const set = n => { if (!btn) return; const b = btn.querySelector('b'); n = +n || 0; b.hidden = !n; b.textContent = n > 99 ? '99+' : n;
  btn.setAttribute('aria-label', n ? `${W[0]}: ${n} ${W[3]}` : W[0]); };
try { set(localStorage.getItem('luna.ib.unread')); } catch(e){}
const poll = () => { if (document.hidden) return; fetch('/api/inbox/unread', {credentials: 'same-origin'}).then(r => r.json()).then(d => set(d.total)).catch(() => {}); };
const start = () => { poll(); setInterval(poll, 90000); };
if ('requestIdleCallback' in window) addEventListener('load', () => requestIdleCallback(start, {timeout: 4000})); else addEventListener('load', () => setTimeout(start, 2500));
document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
addEventListener('message', e => { if (e.origin === location.origin && e.data && e.data.luna === 'inbox-unread') set(e.data.total); });
/* wpis w zakładce „Więcej” */
const more = document.getElementById('p-more');
const add = () => { const m = more && more.querySelector('ul.menu'); if (!m || more.querySelector('[data-ib]')) return;
  const li = document.createElement('li'); li.innerHTML = `<button type="button" data-ib><span>📬 ${W[0]} · 💚 ${W[1]}<small>${W[2]}</small></span></button>`;
  li.querySelector('button').onclick = () => open('/skrzynka.html'); m.prepend(li); };
if (more){ add(); new MutationObserver(add).observe(more, {childList: true}); }
window.LunaInbox = {open: () => open('/skrzynka.html'), friends: () => open('/znajomi.html'), privacy: () => open('/znajomi.html#prywatnosc'), refresh: poll};
})();
