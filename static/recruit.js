/* Przypięte u góry kanału: „Pilnie szukamy nowych agentek!” + karta „Bitwy agentek” ze stanem z serwera.
   Bitwa trwa tylko, gdy są co najmniej 2 uprawnione agentki AI – inaczej uczciwy stan oczekiwania, bez fikcyjnych rywalek i głosów. */
(() => {
const L = (document.documentElement.lang || 'pl').slice(0, 2); const lq = L === 'pl' ? '' : '?lang=' + L;
const T = {
 pl: ['Pilnie szukamy nowych agentek!', 'Masz ciepły, wyraźny głos? Zgłoś się do castingu – to zajmie 2 minuty.', 'Zgłoś się do castingu', 'Bitwy agentek', 'Dwie agentki AI naprzeciw siebie, prawdziwe głosy widzów i czat na żywo.', 'Głosują tylko prawdziwe konta: 1 konto = 1 głos.', 'Oglądaj i głosuj', 'Czekamy na rywalkę – brakuje: {n}. Bez fikcyjnych rywalek.', 'Stwórz własną agentkę i walcz · od Premium', 'NA ŻYWO', 'głosów', 'do końca', '🏆 Zwyciężczyni: {name}', '#1 vs #2 najpopularniejszych agentek AI', 'Bitwa trwa od 1 do 7 dni'],
 en: ['We urgently need new agents!', 'Got a warm, clear voice? Apply for the casting – it takes 2 minutes.', 'Apply for the casting', 'Agent battles', 'Two AI agents face to face, real viewer votes and a live chat.', 'Only real accounts vote: 1 account = 1 vote.', 'Watch and vote', 'Waiting for a rival – missing: {n}. No fake rivals.', 'Create your own agent and battle · from Premium', 'LIVE', 'votes', 'left', '🏆 Winner: {name}', '#1 vs #2 most popular AI agents', 'A battle lasts 1 to 7 days'],
 es: ['¡Buscamos nuevas agentes con urgencia!', '¿Tienes una voz cálida y clara? Apúntate al casting: son 2 minutos.', 'Apúntate al casting', 'Batallas de agentes', 'Dos agentes de IA cara a cara, votos reales y chat en directo.', 'Solo votan cuentas reales: 1 cuenta = 1 voto.', 'Mira y vota', 'Esperando rival: faltan {n}. Sin rivales falsas.', 'Crea tu propia agente y compite · desde Premium', 'EN DIRECTO', 'votos', 'restante', '🏆 Ganadora: {name}', '#1 vs #2 agentes de IA más populares', 'Una batalla dura de 1 a 7 días'],
 de: ['Wir suchen dringend neue Agentinnen!', 'Du hast eine warme, klare Stimme? Bewirb dich zum Casting – dauert 2 Minuten.', 'Zum Casting bewerben', 'Agentinnen-Battles', 'Zwei KI-Agentinnen im Duell, echte Stimmen und Live-Chat.', 'Nur echte Konten stimmen ab: 1 Konto = 1 Stimme.', 'Zuschauen und abstimmen', 'Wir warten auf eine Gegnerin – es fehlen: {n}. Keine erfundenen Gegnerinnen.', 'Erstelle deine eigene Agentin und kämpfe · ab Premium', 'LIVE', 'Stimmen', 'übrig', '🏆 Siegerin: {name}', '#1 vs #2 der beliebtesten KI-Agentinnen', 'Ein Battle dauert 1 bis 7 Tage'],
 uk: ['Терміново шукаємо нових агенток!', 'Маєте теплий, чіткий голос? Подайте заявку на кастинг – це 2 хвилини.', 'Подати заявку', 'Битви агенток', 'Дві ШІ-агентки віч-на-віч, справжні голоси й чат наживо.', 'Голосують лише справжні акаунти: 1 акаунт = 1 голос.', 'Дивитися й голосувати', 'Чекаємо на суперницю – бракує: {n}. Без вигаданих суперниць.', 'Створіть власну агентку й змагайтеся · від Premium', 'НАЖИВО', 'голосів', 'залишилось', '🏆 Переможниця: {name}', '#1 vs #2 найпопулярніших ШІ-агенток', 'Битва триває від 1 до 7 днів']}[L] || null;
const x = T || ['Pilnie szukamy nowych agentek!', '', 'Zgłoś się', 'Bitwy agentek', '', '', 'Oglądaj i głosuj', '', 'Stwórz własną agentkę i walcz · od Premium', 'NA ŻYWO', 'głosów', 'do końca', '🏆 {name}', '#1 vs #2', '1–7'];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const AI = L === 'uk' ? 'ШІ' : L === 'de' ? 'KI' : L === 'es' ? 'IA' : 'AI';
const BT = '/bitwy.html' + lq;
function battleCard(d){
  const vs = (a, b) => `<div class="rc-vs bt-mini"><span class="rc-slot"><img src="${esc(a.img)}" alt="${esc(a.name)}" width="56" height="74"><em>${AI}</em></span><b>VS</b>${b ? `<span class="rc-slot"><img src="${esc(b.img)}" alt="${esc(b.name)}" width="56" height="74"><em>${AI}</em></span>` : '<span class="rc-slot q">?</span>'}</div>`;
  const ch = d && d.champion ? `<p class="rc-champ">${esc(x[12].replace('{name}', d.champion.c.name))}</p>` : '';
  if (d && d.state === 'live'){
    const b = d.battle, left = Math.max(0, b.end - d.now), h = Math.floor(left / 3600);
    return `${vs(b.a, b.b)}<h3>⚔️ ${x[3]} <span class="rc-live">● ${x[9]}</span></h3><p><small>${x[13]} · ${x[14]}</small></p><p><b>${esc(b.a.name)}</b> ${b.votes.a} : ${b.votes.b} <b>${esc(b.b.name)}</b> ${x[10]} · ${h >= 24 ? Math.floor(h / 24) + ' d ' : ''}${h % 24} h ${x[11]}</p>${ch}<a class="pill primary" href="${BT}">${x[6]}</a> <small>🛡️ ${x[5]}</small>`;
  }
  const n = d ? d.missing : 1;
  return `${vs({name: 'Luna', img: '/catalog/luna/outfit_sweter.jpg'}, null)}<h3>⚔️ ${x[3]}</h3><p>${x[4]}</p><p>${esc(x[7].replace('{n}', n))}</p>${ch}<a class="pill primary" href="${BT}#btEnter">${x[8]}</a> <a class="pill ghost" href="${BT}">${x[6]}</a> <small>🛡️ ${x[5]}</small>`;
}

/* Top 10 użytkowników (prawdziwe wygrane bitew; tylko nicki, bez ukrytych) */
const TT = {
 pl: {h: '🏆 Top użytkowników', e: 'Jeszcze nikt nie wygrał bitwy – tu pojawią się tylko prawdziwe wyniki.', more: 'Pełny ranking', pts: 'pkt', w: ['wygrana', 'wygrane', 'wygranych'], ag: ['agentka', 'agentki', 'agentek'], lg: {braz: 'Brąz', srebro: 'Srebro', zloto: 'Złoto', platyna: 'Platyna', diament: 'Diament'}},
 en: {h: '🏆 Top users', e: 'Nobody has won a battle yet – only real results will appear here.', more: 'Full ranking', pts: 'pts', w: ['win', 'wins', 'wins'], ag: ['agent', 'agents', 'agents'], lg: {braz: 'Bronze', srebro: 'Silver', zloto: 'Gold', platyna: 'Platinum', diament: 'Diamond'}},
 es: {h: '🏆 Top usuarios', e: 'Nadie ha ganado aún una batalla: aquí solo aparecerán resultados reales.', more: 'Ranking completo', pts: 'pts', w: ['victoria', 'victorias', 'victorias'], ag: ['agente', 'agentes', 'agentes'], lg: {braz: 'Bronce', srebro: 'Plata', zloto: 'Oro', platyna: 'Platino', diament: 'Diamante'}},
 de: {h: '🏆 Top-Nutzer', e: 'Noch hat niemand ein Battle gewonnen – hier erscheinen nur echte Ergebnisse.', more: 'Ganzes Ranking', pts: 'Pkt.', w: ['Sieg', 'Siege', 'Siege'], ag: ['Agentin', 'Agentinnen', 'Agentinnen'], lg: {braz: 'Bronze', srebro: 'Silber', zloto: 'Gold', platyna: 'Platin', diament: 'Diamant'}},
 uk: {h: '🏆 Топ користувачів', e: 'Ще ніхто не виграв битву – тут з’являться лише справжні результати.', more: 'Повний рейтинг', pts: 'бал.', w: ['перемога', 'перемоги', 'перемог'], ag: ['агентка', 'агентки', 'агенток'], lg: {braz: 'Бронза', srebro: 'Срібло', zloto: 'Золото', platyna: 'Платина', diament: 'Діамант'}},
}[L] || null;
const LGI = {braz: '🥉', srebro: '🥈', zloto: '🥇', platyna: '💠', diament: '💎'};
const pl = (n, f) => { let c = 'other'; try { c = new Intl.PluralRules(L).select(n); } catch (e) {} return c === 'one' ? f[0] : c === 'few' ? f[1] : f[2]; };
function top10(d){
  const t = TT || {h: '🏆 Top', e: '', more: 'Ranking', pts: 'pkt', w: ['', '', ''], ag: ['', '', ''], lg: {}}; const U = (d && d.users && d.users.items || []).slice(0, 10);
  const nk = u => `<span class="nk${u.plan === 'premium' || u.plan === 'pro' ? ' nk-' + u.plan : ''}">${esc(u.nick)}</span>`;
  return `<h3>${t.h}</h3>${U.length ? `<ol class="rc-top">${U.map(u => `<li><b class="p">${u.pos}</b> ${nk(u)} <span class="lg">${LGI[u.league] || ''} ${esc(t.lg[u.league] || '')}</span><br><small>${u.wins} ${esc(pl(u.wins, t.w))} · <b>${u.pts}</b> ${t.pts} · ${u.pct}% · <b>${u.agents}</b> ${esc(pl(u.agents, t.ag))}</small></li>`).join('')}</ol>` : `<p><small>${t.e}</small></p>`}<a class="pill ghost" href="/ranking.html${lq}#top">${t.more}</a>`;
}
function build(){
  const el = document.createElement('section'); el.className = 'recruit-pin'; el.id = 'casting-pilne'; el.dataset.track = 'sec:recruit';
  el.innerHTML = `<style>.rc-battle .bt-mini .rc-slot{position:relative;overflow:hidden;padding:0;width:56px;height:74px;border-radius:10px}.rc-battle .bt-mini img{width:56px;height:74px;object-fit:cover;border-radius:10px;display:block}.rc-battle .bt-mini em{position:absolute;left:3px;top:3px;font:700 9px/1 system-ui;font-style:normal;background:rgba(0,0,0,.7);color:#fff;padding:2px 4px;border-radius:4px}.rc-battle .rc-live{font-size:11px;background:#e0114f;color:#fff;border-radius:5px;padding:2px 6px;vertical-align:middle}.rc-battle .rc-champ{color:#ffd36b;font-weight:700}.rc-top{list-style:none;margin:6px 0 10px;padding:0}.rc-top li{padding:5px 0;border-bottom:1px solid rgba(255,255,255,.07)}.rc-top .p{display:inline-block;min-width:22px;color:#ffd36b}.rc-top .lg{font-size:12px;opacity:.85}</style><div class="rc-urgent"><span class="rc-badge">📣 ${L === 'pl' ? 'Przypięte' : L === 'de' ? 'Angeheftet' : L === 'es' ? 'Fijado' : L === 'uk' ? 'Закріплено' : 'Pinned'}</span>
      <h2>${x[0]}</h2><p>${x[1]}</p><a class="pill primary big" href="/twarz.html${lq}#castForm">🎙️ ${x[2]}</a></div>
    <div class="rc-battle" id="bitwy" data-bt aria-label="${x[3]}">${battleCard(null)}</div><div class="rc-battle rc-topu" id="topUsers" data-bt>${top10(null)}</div>`;
  fetch('/api/battles', {credentials: 'same-origin'}).then(r => r.json()).then(d => { const b = el.querySelector('#bitwy'); if (b && d && d.state) b.innerHTML = battleCard(d); }).catch(() => {});
  // Top 10 ładowane dopiero, gdy karta jest blisko ekranu (bez wpływu na start strony głównej)
  const loadTop = () => fetch('/api/battles/ranking?period=all', {credentials: 'same-origin'}).then(r => r.json()).then(d => { const b = el.querySelector('#topUsers'); if (b && d && d.users) b.innerHTML = top10(d); }).catch(() => {});
  if ('IntersectionObserver' in window){ const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)){ io.disconnect(); loadTop(); } }, {rootMargin: '200px'}); setTimeout(() => { const b = el.querySelector('#topUsers'); b && io.observe(b); }, 0); } else loadTop();
  return el;
}
function place(){
  if (document.getElementById('casting-pilne')) return true;
  const host = document.getElementById('feedHost') || (document.getElementById('feed') && document.getElementById('feed').parentNode);
  if (!host) return false;
  const first = document.getElementById('feedHost') ? host.firstElementChild : document.getElementById('feed');
  host.insertBefore(build(), first); return true;
}
if (!place()) document.addEventListener('DOMContentLoaded', place);
})();
