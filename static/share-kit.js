/* Udostępnianie (E3, uczciwa promocja): natywne Web Share API + „Kopiuj link” dla bitew (trwająca: „Głosuj na moją agentkę”,
   wyniki), rankingu i profili agentek. Linki prowadzą do stron z kartą OG (1200×630) konkretnej bitwy/agentki.
   Liczymy tylko prawdziwe kliknięcia (/api/track, raz na sesję). Bez nagród za udostępnienia. Moduł samodzielny. */
(() => {
const L = (document.documentElement.lang || 'pl').slice(0, 2);
const T = {
  pl: {share: 'Udostępnij', copy: 'Kopiuj link', copied: 'Link skopiowany ✓', vote_mine: '📣 Głosuj na moją agentkę', battle: '📣 Udostępnij bitwę', result: 'Udostępnij wynik',
       rank: '📣 Udostępnij ranking', mypos: '📣 Pochwal się pozycją agentki', t_vote: 'Głosuj na moją agentkę {a} w Bitwie agentek AI! 1 konto = 1 głos 💚', t_battle: '{a} vs {b} – zagłosuj w Bitwie agentek AI 💚',
       t_result: 'Wynik Bitwy agentek AI: {a} vs {b} 🏆', t_rank: 'Ranking Bitew agentek AI – tylko prawdziwe głosy 💚', t_pos: 'Moja agentka AI {a} jest #{n} w rankingu Bitew! 💚'},
  en: {share: 'Share', copy: 'Copy link', copied: 'Link copied ✓', vote_mine: '📣 Vote for my agent', battle: '📣 Share the battle', result: 'Share the result',
       rank: '📣 Share the ranking', mypos: '📣 Show off your agent’s rank', t_vote: 'Vote for my agent {a} in the AI Agent Battle! 1 account = 1 vote 💚', t_battle: '{a} vs {b} – vote in the AI Agent Battle 💚',
       t_result: 'AI Agent Battle result: {a} vs {b} 🏆', t_rank: 'AI Agent Battle ranking – real votes only 💚', t_pos: 'My AI agent {a} is #{n} in the Battle ranking! 💚'},
  es: {share: 'Compartir', copy: 'Copiar enlace', copied: 'Enlace copiado ✓', vote_mine: '📣 Vota por mi agente', battle: '📣 Comparte la batalla', result: 'Compartir resultado',
       rank: '📣 Compartir ranking', mypos: '📣 Presume del puesto de tu agente', t_vote: '¡Vota por mi agente {a} en la Batalla de agentes IA! 1 cuenta = 1 voto 💚', t_battle: '{a} vs {b} – vota en la Batalla de agentes IA 💚',
       t_result: 'Resultado de la Batalla de agentes IA: {a} vs {b} 🏆', t_rank: 'Ranking de Batallas de agentes IA – solo votos reales 💚', t_pos: '¡Mi agente IA {a} es #{n} en el ranking de Batallas! 💚'},
  de: {share: 'Teilen', copy: 'Link kopieren', copied: 'Link kopiert ✓', vote_mine: '📣 Stimm für meine Agentin', battle: '📣 Battle teilen', result: 'Ergebnis teilen',
       rank: '📣 Ranking teilen', mypos: '📣 Platz deiner Agentin teilen', t_vote: 'Stimm für meine Agentin {a} im KI-Agentinnen-Battle! 1 Konto = 1 Stimme 💚', t_battle: '{a} vs {b} – stimm im KI-Agentinnen-Battle ab 💚',
       t_result: 'Ergebnis des KI-Agentinnen-Battles: {a} vs {b} 🏆', t_rank: 'Battle-Ranking der KI-Agentinnen – nur echte Stimmen 💚', t_pos: 'Meine KI-Agentin {a} ist #{n} im Battle-Ranking! 💚'},
  uk: {share: 'Поділитися', copy: 'Копіювати посилання', copied: 'Посилання скопійовано ✓', vote_mine: '📣 Голосуй за мою агентку', battle: '📣 Поділитися битвою', result: 'Поділитися результатом',
       rank: '📣 Поділитися рейтингом', mypos: '📣 Похвалися місцем агентки', t_vote: 'Голосуй за мою агентку {a} у Битві ШІ-агенток! 1 акаунт = 1 голос 💚', t_battle: '{a} vs {b} – голосуй у Битві ШІ-агенток 💚',
       t_result: 'Результат Битви ШІ-агенток: {a} vs {b} 🏆', t_rank: 'Рейтинг Битв ШІ-агенток – лише справжні голоси 💚', t_pos: 'Моя ШІ-агентка {a} – #{n} у рейтингу Битв! 💚'}
}[L] || {};
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const fill = (s, o) => String(s).replace(/\{(\w+)\}/g, (_, k) => o[k] ?? '');
let SID = ''; try { SID = sessionStorage.getItem('luna.vsid') || ''; if (!SID){ SID = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join(''); sessionStorage.setItem('luna.vsid', SID); } } catch (e) {}
function track(ev, key){ try { const b = JSON.stringify({sid: SID, ev, keys: [key], lang: L}); navigator.sendBeacon ? navigator.sendBeacon('/api/track', new Blob([b], {type: 'application/json'})) : fetch('/api/track', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: b, credentials: 'same-origin'}); } catch (e) {} }
function link(path, camp, net){
  const u = new URL(path, location.origin); if (L !== 'pl') u.searchParams.set('lang', L);
  u.searchParams.set('utm_source', net); u.searchParams.set('utm_medium', 'share'); u.searchParams.set('utm_campaign', camp); return u.toString();
}
function toast(msg){
  let el = document.getElementById('lshToast'); if (!el){ el = document.createElement('div'); el.id = 'lshToast'; el.className = 'lsh-toast'; el.setAttribute('role', 'status'); document.body.appendChild(el); }
  el.textContent = msg; el.classList.add('on'); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove('on'), 2000);
}
async function copy(url){
  try { await navigator.clipboard.writeText(url); } catch (e) { const i = document.createElement('input'); i.value = url; document.body.appendChild(i); i.select(); try { document.execCommand('copy'); } catch (_) {} i.remove(); }
  toast(T.copied);
}
/* opts: {path, camp, title, text, key} */
async function share(o){
  track('share', o.key || 'page:share');
  if (navigator.share){ try { await navigator.share({title: o.title || 'Luna', text: o.text || '', url: link(o.path, o.camp, 'native')}); track('sharenet', 'utm:native'); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
  copy(link(o.path, o.camp, 'copy')); track('sharenet', 'utm:copy');
}
function bar(o, label, small){
  const d = document.createElement('div'); d.className = 'lsh-bar' + (small ? ' sm' : ''); d.dataset.lsh = o.id || '';
  d.innerHTML = `${navigator.share ? `<button type="button" class="lsh-btn pri">${esc(label || T.share)}</button>` : ''}<button type="button" class="lsh-btn${navigator.share ? '' : ' pri'}">🔗 ${esc(navigator.share ? T.copy : (label ? label.replace(/^📣\s*/, '') + ' · ' + T.copy : T.copy))}</button>`;
  const bs = d.querySelectorAll('button');
  if (navigator.share){ bs[0].onclick = () => share(o); bs[1].onclick = () => { track('share', o.key || 'page:share'); track('sharenet', 'utm:copy'); copy(link(o.path, o.camp, 'copy')); }; }
  else bs[0].onclick = () => share(o);
  return d;
}
function css(){
  if (document.getElementById('lshCss')) return;
  const s = document.createElement('style'); s.id = 'lshCss';
  s.textContent = `.lsh-bar{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:12px auto}.lsh-bar.sm{justify-content:flex-start;margin:6px 0 0}
.lsh-btn{font:inherit;font-weight:700;border-radius:var(--luna-r-pill,999px);border:1px solid rgba(61,220,132,.45);background:rgba(61,220,132,.08);color:inherit;padding:9px 16px;cursor:pointer;min-height:40px;transition:transform .15s var(--luna-ease,ease),background .15s}
.lsh-btn.pri{background:linear-gradient(135deg,#3ddc84,#2bb673);color:#0b0705;border-color:transparent;box-shadow:var(--luna-shadow-sm,0 4px 14px rgba(61,220,132,.25))}
.lsh-btn:hover{transform:translateY(-1px)}.lsh-btn:focus-visible{outline:3px solid #ff9f43;outline-offset:2px}.lsh-bar.sm .lsh-btn{padding:6px 12px;min-height:34px;font-size:.88em}
.lsh-toast{position:fixed;left:50%;bottom:calc(18px + env(safe-area-inset-bottom));transform:translate(-50%,20px);opacity:0;pointer-events:none;background:#141010;color:#f5f0e8;border:1px solid rgba(61,220,132,.5);border-radius:var(--luna-r-lg,22px);padding:10px 18px;box-shadow:0 10px 30px rgba(0,0,0,.45);transition:.25s var(--luna-ease,ease);z-index:2147483000}
.lsh-toast.on{opacity:1;transform:translate(-50%,0)}@media (prefers-reduced-motion:reduce){.lsh-btn,.lsh-toast{transition:none}}`;
  document.head.appendChild(s);
}
const get = p => fetch(p, {credentials: 'same-origin'}).then(r => r.ok ? r.json() : null).catch(() => null);
function keep(host, make){ /* host jest przerysowywany co 20 s – dokładamy pasek ponownie */
  if (!host) return; const run = () => { try { make(); } catch (e) {} }; run(); new MutationObserver(run).observe(host, {childList: true});
}
/* ---------- Bitwy ---------- */
async function battles(){
  const QS = new URLSearchParams(location.search), BID = QS.get('b') || '';
  let S = await get('/api/battles' + (BID ? '?b=' + encodeURIComponent(BID) : '')); if (!S) return;
  setInterval(async () => { if (!document.hidden){ const n = await get('/api/battles' + (BID ? '?b=' + encodeURIComponent(BID) : '')); if (n) S = n; } }, 30000);
  const stage = document.getElementById('btStage');
  if (stage) keep(stage.parentElement, () => {
    const old = document.getElementById('lshBattle'), b = S.battle;
    if (S.state !== 'live' || !b){ if (old) old.remove(); return; }
    if (old && old.dataset.lsh === b.id + (b.own ? 'o' : '')) return; if (old) old.remove();
    const own = !!b.own, mine = own ? (S.my_entry && [b.a, b.b].find(c => c.id === S.my_entry.id)) || b.a : null;
    const d = bar({id: b.id + (own ? 'o' : ''), path: '/bitwy.html?b=' + b.id + (own ? '&v=1' : ''), camp: own ? 'glosuj' : 'bitwa', key: 'page:bitwy', title: 'Luna – ' + b.a.name + ' vs ' + b.b.name,
                   text: own ? fill(T.t_vote, {a: mine.name}) : fill(T.t_battle, {a: b.a.name, b: b.b.name})}, own ? T.vote_mine : T.battle);
    d.id = 'lshBattle'; stage.after(d);
  });
  const champ = document.getElementById('btChamp');
  keep(champ, () => { const c = S.champion; if (!c || !c.bid || champ.querySelector('.lsh-bar')) return;
    champ.appendChild(bar({path: '/bitwy.html?sum=' + c.bid, camp: 'wynik', key: 'page:bitwy', title: 'Luna', text: fill(T.t_result, {a: c.a.name, b: c.b.name})}, '📣 ' + T.result)); });
  const last = document.getElementById('btLastList');
  keep(last, () => { (S.last || []).forEach((r, i) => { const row = last.querySelectorAll('.bt-r')[i]; if (!row || row.querySelector('.lsh-bar') || r.reason !== 'end') return;
    (row.lastElementChild || row).appendChild(bar({path: '/bitwy.html?sum=' + r.id, camp: 'wynik', key: 'page:bitwy', title: 'Luna', text: fill(T.t_result, {a: r.a.name, b: r.b.name})}, '↗ ' + T.result, true)); }); });
}
/* ---------- Ranking ---------- */
async function ranking(){
  const lead = document.querySelector('main .lead') || document.querySelector('main h1');
  if (lead && !document.getElementById('lshRank')){ const d = bar({path: '/ranking.html', camp: 'ranking', key: 'page:ranking', title: 'Luna', text: T.t_rank}, T.rank); d.id = 'lshRank'; lead.after(d); }
  const R = await get('/api/battles/ranking?period=all'); const m = R && R.my_agent; const me = document.getElementById('rkMe');
  if (m && me) keep(me, () => { if (me.querySelector('.lsh-bar') || !me.querySelector('.rk-mine')) return;
    me.appendChild(bar({path: '/ranking.html?a=' + m.id, camp: 'pozycja', key: 'page:ranking', title: 'Luna', text: fill(T.t_pos, {a: m.name, n: m.pos})}, T.mypos)); });
}
/* ---------- Profil agentki: dokładamy „Kopiuj link” obok istniejącego „Udostępnij” ---------- */
function agent(){
  const host = document.querySelector('main') || document.body;
  keep(host, () => { const b = document.getElementById('phShare'); if (!b || document.getElementById('lshCopy')) return;
    const id = new URLSearchParams(location.search).get('id') || 'luna';
    const c = document.createElement('button'); c.type = 'button'; c.id = 'lshCopy'; c.className = b.className; c.textContent = '🔗 ' + T.copy;
    c.onclick = () => { track('share', 'page:agentka'); track('sharenet', 'utm:copy'); copy(link('/agentka.html?id=' + encodeURIComponent(id), 'agentka', 'copy')); }; b.after(c); });
}
const P = location.pathname;
const go = () => { css(); if (P === '/bitwy.html' || P === '/bitwy') battles(); else if (P === '/ranking.html' || P === '/ranking') ranking(); else if (P === '/agentka.html') agent(); };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
window.LunaShare = {share, copy, link, bar};
})();
