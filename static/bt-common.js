/* Bitwy agentek – wspólne: ligi, tytuły, odznaki i nicki według planu (5 języków). Tylko dane z serwera (prawdziwe wyniki). */
(() => {
const L0 = (document.documentElement.lang || 'pl').slice(0, 2);
const D = {
  pl: {lg: {braz: 'Brąz', srebro: 'Srebro', zloto: 'Złoto', platyna: 'Platyna', diament: 'Diament'}, elite: 'Elita Top 10', pts: 'pkt', league: 'Liga',
    ttl: {city: 'Miss Nocnego Miasta', studio: 'Miss Sceny Studia', promenade: 'Miss Nadmorskiej Promenady', winter: 'Miss Zimowego Lasu', gala: 'Miss Sali Balowej', garden: 'Miss Ogrodu'},
    ag: ['agentka', 'agentki', 'agentek'], wins: ['wygrana', 'wygrane', 'wygranych'], titles: 'Tytuły', no_titles: 'Jeszcze bez tytułów', profile: 'Profil agentki', close: 'Zamknij',
    played: 'bitew', pct: 'wygranych', pos: 'Miejsce', ai: 'AI'},
  en: {lg: {braz: 'Bronze', srebro: 'Silver', zloto: 'Gold', platyna: 'Platinum', diament: 'Diamond'}, elite: 'Elite Top 10', pts: 'pts', league: 'League',
    ttl: {city: 'Miss Night City', studio: 'Miss Studio Stage', promenade: 'Miss Seaside Promenade', winter: 'Miss Winter Forest', gala: 'Miss Gala Hall', garden: 'Miss Garden'},
    ag: ['agent', 'agents', 'agents'], wins: ['win', 'wins', 'wins'], titles: 'Titles', no_titles: 'No titles yet', profile: 'Agent profile', close: 'Close',
    played: 'battles', pct: 'won', pos: 'Place', ai: 'AI'},
  es: {lg: {braz: 'Bronce', srebro: 'Plata', zloto: 'Oro', platyna: 'Platino', diament: 'Diamante'}, elite: 'Élite Top 10', pts: 'pts', league: 'Liga',
    ttl: {city: 'Miss Ciudad Nocturna', studio: 'Miss Plató', promenade: 'Miss Paseo Marítimo', winter: 'Miss Bosque Nevado', gala: 'Miss Salón de Gala', garden: 'Miss Jardín'},
    ag: ['agente', 'agentes', 'agentes'], wins: ['victoria', 'victorias', 'victorias'], titles: 'Títulos', no_titles: 'Aún sin títulos', profile: 'Perfil de la agente', close: 'Cerrar',
    played: 'batallas', pct: 'ganadas', pos: 'Puesto', ai: 'IA'},
  de: {lg: {braz: 'Bronze', srebro: 'Silber', zloto: 'Gold', platyna: 'Platin', diament: 'Diamant'}, elite: 'Elite Top 10', pts: 'Pkt.', league: 'Liga',
    ttl: {city: 'Miss Nachtstadt', studio: 'Miss Studiobühne', promenade: 'Miss Strandpromenade', winter: 'Miss Winterwald', gala: 'Miss Gala-Saal', garden: 'Miss Garten'},
    ag: ['Agentin', 'Agentinnen', 'Agentinnen'], wins: ['Sieg', 'Siege', 'Siege'], titles: 'Titel', no_titles: 'Noch keine Titel', profile: 'Profil der Agentin', close: 'Schließen',
    played: 'Battles', pct: 'gewonnen', pos: 'Platz', ai: 'KI'},
  uk: {lg: {braz: 'Бронза', srebro: 'Срібло', zloto: 'Золото', platyna: 'Платина', diament: 'Діамант'}, elite: 'Еліта Топ-10', pts: 'бал.', league: 'Ліга',
    ttl: {city: 'Міс Нічного Міста', studio: 'Міс Студійної Сцени', promenade: 'Міс Набережної', winter: 'Міс Зимового Лісу', gala: 'Міс Бальної Зали', garden: 'Міс Саду'},
    ag: ['агентка', 'агентки', 'агенток'], wins: ['перемога', 'перемоги', 'перемог'], titles: 'Титули', no_titles: 'Поки без титулів', profile: 'Профіль агентки', close: 'Закрити',
    played: 'битв', pct: 'перемог', pos: 'Місце', ai: 'ШІ'},
};
const L = D[L0] ? L0 : 'pl', T = D[L];
const ICON = {braz: '🥉', srebro: '🥈', zloto: '🥇', platyna: '💠', diament: '💎'};
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const fmt = n => Number(n || 0).toLocaleString(L === 'uk' ? 'uk-UA' : L);
const plural = (n, f) => { let c = 'other'; try { c = new Intl.PluralRules(L).select(n); } catch (e) {} return c === 'one' ? f[0] : c === 'few' ? f[1] : f[2]; };
const league = (k, elite) => `<span class="lgb lg-${esc(k)}" title="${esc(T.league)}: ${esc(T.lg[k] || k)}">${ICON[k] || ''} ${esc(T.lg[k] || k)}</span>${elite ? ` <span class="lgb lg-elite">★ ${esc(T.elite)}</span>` : ''}`;
const titleName = s => T.ttl[s] || '';
function titleList(arr){ const m = new Map(); (arr || []).forEach(s => { if (T.ttl[s]) m.set(s, (m.get(s) || 0) + 1); }); return [...m.entries()]; }
const plaque = arr => { const l = titleList(arr); return l.length ? `<div class="bt-plq">${l.map(([s, n]) => `<b>👑 ${esc(titleName(s))}${n > 1 ? ' ×' + n : ''}</b>`).join('')}</div>` : ''; };
const nick = (n, plan) => `<span class="nk${plan === 'premium' || plan === 'pro' ? ' nk-' + plan : ''}">${esc(n)}</span>`;
const agents = n => `<b>${fmt(n)}</b> ${esc(plural(n, T.ag))}`;
window.LunaBt = {L, T, esc, fmt, plural, league, titleName, titleList, plaque, nick, agents};
})();
