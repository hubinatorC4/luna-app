/* Pomoc Luny · bot AI – pływający dymek na każdej stronie; na /problemy.html otwiera się sam. Język: ?lang / luna.lang / przeglądarka. */
(() => {
if (window.__lunaHelp) return; window.__lunaHelp = 1;
const LS = ['pl', 'en', 'es', 'de', 'uk'];
const lang = (() => { let l = 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || navigator.language || 'pl'; } catch(e){} l = l.slice(0, 2).toLowerCase(); return LS.includes(l) ? l : 'pl'; })();
const T = {
 pl: {title: 'Pomoc Luny · bot AI', ph: 'Napisz pytanie…', send: 'Wyślij', human: 'Porozmawiaj z człowiekiem', open: 'Otwórz czat pomocy', close: 'Zamknij', email: 'E-mail do odpowiedzi (opcjonalnie)', handed: 'Przekazane! Numer zgłoszenia: ', err: 'Ups, coś poszło nie tak. Spróbuj za chwilę.', ai: 'Rozmawiasz z botem AI.'},
 en: {title: 'Luna’s Help · AI bot', ph: 'Type your question…', send: 'Send', human: 'Talk to a human', open: 'Open help chat', close: 'Close', email: 'Email for a reply (optional)', handed: 'Passed on! Ticket number: ', err: 'Oops, something went wrong. Please try again in a moment.', ai: 'You’re chatting with an AI bot.'},
 es: {title: 'Ayuda de Luna · bot de IA', ph: 'Escribe tu pregunta…', send: 'Enviar', human: 'Hablar con una persona', open: 'Abrir el chat de ayuda', close: 'Cerrar', email: 'Correo para la respuesta (opcional)', handed: '¡Enviado! Número de incidencia: ', err: 'Vaya, algo ha fallado. Inténtalo de nuevo en un momento.', ai: 'Estás hablando con un bot de IA.'},
 de: {title: 'Lunas Hilfe · KI-Bot', ph: 'Schreib deine Frage…', send: 'Senden', human: 'Mit einem Menschen sprechen', open: 'Hilfe-Chat öffnen', close: 'Schließen', email: 'E-Mail für eine Antwort (optional)', handed: 'Weitergeleitet! Ticketnummer: ', err: 'Hoppla, da ist etwas schiefgelaufen. Versuch es gleich noch einmal.', ai: 'Du chattest mit einem KI-Bot.'},
 uk: {title: 'Допомога Луни · ШІ-бот', ph: 'Напишіть запитання…', send: 'Надіслати', human: 'Поговорити з людиною', open: 'Відкрити чат допомоги', close: 'Закрити', email: 'E-mail для відповіді (необов’язково)', handed: 'Передано! Номер звернення: ', err: 'Ой, щось пішло не так. Спробуйте трохи згодом.', ai: 'Ви спілкуєтеся з ШІ-ботом.'}}[lang];
const css = `.hb-fab{position:fixed;right:18px;bottom:18px;z-index:80;width:58px;height:58px;border-radius:50%;border:0;background:radial-gradient(circle at 30% 30%,#3ee68a,#1f9d57);color:#06120b;font-size:26px;box-shadow:0 14px 30px -10px rgba(46,204,113,.6);cursor:pointer}
.hb-win{position:fixed;right:18px;bottom:88px;z-index:81;width:360px;height:520px;max-height:calc(100vh - 110px);display:flex;flex-direction:column;background:#111613;color:#eee;border:1px solid #26332b;border-radius:24px;box-shadow:0 30px 80px -20px rgba(0,0,0,.8);overflow:hidden;font-family:var(--font-ui,system-ui)}
.hb-win[hidden]{display:none}.hb-h{display:flex;align-items:center;gap:10px;padding:12px 14px;background:linear-gradient(135deg,#17241c,#111613);border-bottom:1px solid #26332b}
.hb-h img{width:34px;height:34px;border-radius:50%}.hb-h b{flex:1;font-size:15px}.hb-h small{display:block;font-weight:400;color:#9fb5a8;font-size:11.5px}
.hb-x{background:none;border:0;color:#ccc;font-size:20px;cursor:pointer;border-radius:50%;width:34px;height:34px}
.hb-log{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}.hb-m{max-width:85%;padding:9px 13px;border-radius:18px;font-size:14px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word}
.hb-m.bot{background:#1b251f;align-self:flex-start;border-bottom-left-radius:6px}.hb-m.me{background:#2ecc71;color:#06120b;align-self:flex-end;border-bottom-right-radius:6px}
.hb-typing{align-self:flex-start;color:#9fb5a8;font-size:20px;letter-spacing:2px;padding:0 8px}.hb-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 8px}
.hb-chips button,.hb-hum{background:#1b251f;border:1px solid #2c3b31;color:#dfe;border-radius:999px;padding:6px 12px;font-size:12.5px;cursor:pointer}
.hb-hum{margin:0 12px 8px;align-self:flex-start;border-color:#ff9a3c;color:#ffc58f}
.hb-f{display:flex;gap:8px;padding:10px;border-top:1px solid #26332b}.hb-f input{flex:1;background:#0c100e;color:#eee;border:1px solid #2c3b31;border-radius:16px;padding:10px 12px;font-size:14px}
.hb-f button{background:#2ecc71;border:0;color:#06120b;font-weight:800;border-radius:999px;padding:0 16px;cursor:pointer}
@media (max-width:600px){.hb-win{right:0;left:0;bottom:0;width:auto;height:78vh;max-height:78vh;border-radius:24px 24px 0 0}.hb-fab{bottom:14px;right:14px}}`;
const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
const fab = document.createElement('button'); fab.className = 'hb-fab'; fab.type = 'button'; fab.setAttribute('aria-label', T.open); fab.textContent = '💬';
const w = document.createElement('section'); w.className = 'hb-win'; w.hidden = true; w.setAttribute('role', 'dialog'); w.setAttribute('aria-label', T.title);
w.innerHTML = `<div class="hb-h"><img src="/brand-emblem-96.webp" alt=""><b>${T.title}<small>${T.ai}</small></b><button class="hb-x" type="button" aria-label="${T.close}">✕</button></div>
<div class="hb-log" aria-live="polite"></div><div class="hb-chips"></div><button class="hb-hum" type="button" hidden>🙋 ${T.human}</button>
<form class="hb-f"><input maxlength="500" placeholder="${T.ph}" aria-label="${T.ph}"><button type="submit">${T.send}</button></form>`;
document.body.append(fab, w);
const log = w.querySelector('.hb-log'), inp = w.querySelector('input'), hum = w.querySelector('.hb-hum'), chips = w.querySelector('.hb-chips');
const tr = [];
function add(t, me){ const d = document.createElement('div'); d.className = 'hb-m ' + (me ? 'me' : 'bot'); d.textContent = t; log.appendChild(d); log.scrollTop = log.scrollHeight; tr.push({me: !!me, t}); }
let started = false;
function start(){ if (started) return; started = true;
  fetch('/api/help/chips?lang=' + lang).then(r => r.json()).then(d => { add(d.intro); (d.chips || []).forEach(c => { const b = document.createElement('button'); b.type = 'button'; b.textContent = c.label; b.onclick = () => ask(c.label); chips.appendChild(b); }); hum.hidden = false; }).catch(() => add(T.err)); }
async function ask(q){
  q = String(q).trim(); if (!q) return; add(q, true); inp.value = '';
  const ty = document.createElement('div'); ty.className = 'hb-typing'; ty.textContent = '•••'; log.appendChild(ty);
  try { const r = await fetch('/api/help', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({q, lang})}); const d = await r.json(); ty.remove();
    if (d.sensitive) tr[tr.length - 1].t = '***';
    add(d.reply || d.error || T.err); if (d.handoff) hum.hidden = false; }
  catch(e){ ty.remove(); add(T.err); }
}
hum.onclick = async () => {
  const email = prompt(T.email) || '';
  try { const r = await fetch('/api/help/handoff', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({transcript: tr, email, lang, env: {page: location.pathname, lang, ua: navigator.userAgent.slice(0, 200)}})});
    const d = await r.json(); add(d.ok ? T.handed + d.id : (d.error || T.err)); } catch(e){ add(T.err); }
};
w.querySelector('form').onsubmit = e => { e.preventDefault(); ask(inp.value); };
const toggle = on => { w.hidden = !on; fab.setAttribute('aria-expanded', String(on)); if (on){ start(); setTimeout(() => inp.focus(), 50); } };
fab.onclick = () => toggle(w.hidden); w.querySelector('.hb-x').onclick = () => toggle(false);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !w.hidden) toggle(false); });
window.LunaHelpOpen = () => toggle(true);
if (/\/problemy(\.html)?$/.test(location.pathname)) toggle(true);
})();
