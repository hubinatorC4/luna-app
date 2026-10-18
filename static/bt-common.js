/* Bitwy agentek – wspólne: ligi, tytuły, odznaki i nicki według planu (5 języków). Tylko dane z serwera (prawdziwe wyniki). */
(() => {
const L0 = (document.documentElement.lang || 'pl').slice(0, 2);
const D = {
  pl: {lg: {braz: 'Brąz', srebro: 'Srebro', zloto: 'Złoto', platyna: 'Platyna', diament: 'Diament'}, elite: 'Elita Top 10', pts: 'pkt', league: 'Liga',
    ttl: {city: 'Miss Nocnego Miasta', studio: 'Miss Sceny Studia', promenade: 'Miss Nadmorskiej Promenady', winter: 'Miss Zimowego Lasu', gala: 'Miss Sali Balowej', garden: 'Miss Ogrodu', gym: 'Miss Siłowni', office: 'Miss Biznesu', beach: 'Miss Plaży'},
    ag: ['agentka', 'agentki', 'agentek'], wins: ['wygrana', 'wygrane', 'wygranych'], titles: 'Tytuły', no_titles: 'Jeszcze bez tytułów', profile: 'Profil agentki', close: 'Zamknij',
    played: 'bitew', pct: 'wygranych', pos: 'Miejsce', ai: 'AI'},
  en: {lg: {braz: 'Bronze', srebro: 'Silver', zloto: 'Gold', platyna: 'Platinum', diament: 'Diamond'}, elite: 'Elite Top 10', pts: 'pts', league: 'League',
    ttl: {city: 'Miss Night City', studio: 'Miss Studio Stage', promenade: 'Miss Seaside Promenade', winter: 'Miss Winter Forest', gala: 'Miss Gala Hall', garden: 'Miss Garden', gym: 'Miss Gym', office: 'Miss Business', beach: 'Miss Beach'},
    ag: ['agent', 'agents', 'agents'], wins: ['win', 'wins', 'wins'], titles: 'Titles', no_titles: 'No titles yet', profile: 'Agent profile', close: 'Close',
    played: 'battles', pct: 'won', pos: 'Place', ai: 'AI'},
  es: {lg: {braz: 'Bronce', srebro: 'Plata', zloto: 'Oro', platyna: 'Platino', diament: 'Diamante'}, elite: 'Élite Top 10', pts: 'pts', league: 'Liga',
    ttl: {city: 'Miss Ciudad Nocturna', studio: 'Miss Plató', promenade: 'Miss Paseo Marítimo', winter: 'Miss Bosque Nevado', gala: 'Miss Salón de Gala', garden: 'Miss Jardín', gym: 'Miss Gimnasio', office: 'Miss Negocios', beach: 'Miss Playa'},
    ag: ['agente', 'agentes', 'agentes'], wins: ['victoria', 'victorias', 'victorias'], titles: 'Títulos', no_titles: 'Aún sin títulos', profile: 'Perfil de la agente', close: 'Cerrar',
    played: 'batallas', pct: 'ganadas', pos: 'Puesto', ai: 'IA'},
  de: {lg: {braz: 'Bronze', srebro: 'Silber', zloto: 'Gold', platyna: 'Platin', diament: 'Diamant'}, elite: 'Elite Top 10', pts: 'Pkt.', league: 'Liga',
    ttl: {city: 'Miss Nachtstadt', studio: 'Miss Studiobühne', promenade: 'Miss Strandpromenade', winter: 'Miss Winterwald', gala: 'Miss Gala-Saal', garden: 'Miss Garten', gym: 'Miss Fitnessstudio', office: 'Miss Business', beach: 'Miss Strand'},
    ag: ['Agentin', 'Agentinnen', 'Agentinnen'], wins: ['Sieg', 'Siege', 'Siege'], titles: 'Titel', no_titles: 'Noch keine Titel', profile: 'Profil der Agentin', close: 'Schließen',
    played: 'Battles', pct: 'gewonnen', pos: 'Platz', ai: 'KI'},
  uk: {lg: {braz: 'Бронза', srebro: 'Срібло', zloto: 'Золото', platyna: 'Платина', diament: 'Діамант'}, elite: 'Еліта Топ-10', pts: 'бал.', league: 'Ліга',
    ttl: {city: 'Міс Нічного Міста', studio: 'Міс Студійної Сцени', promenade: 'Міс Набережної', winter: 'Міс Зимового Лісу', gala: 'Міс Бальної Зали', garden: 'Міс Саду', gym: 'Міс Спортзалу', office: 'Міс Бізнесу', beach: 'Міс Пляжу'},
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
/* kategorie bitew (wspólna konfiguracja battle_categories.py → bt-cats.js) i role widz/zawodniczka */
const CF = window.LUNA_BT_CATS || {cats: [], scenes: []};
const CX = {
  pl: {general: 'Ogólny', cat: 'Kategoria', cats_h: 'Specjalizacje (1–3)', cats_err: 'Wybierz od 1 do 3 kategorii.', scene_h: 'Ulubiona sceneria', scene_any: 'Dowolna z kategorii',
    basic: 'Premium: podstawowy zestaw 6 scenerii (najpopularniejsze w bitwach, odświeżane co tydzień).', all: 'Pro / Ultra: wszystkie scenerie.', lock: 'Pro', save: 'Zapisz', saved: 'Zapisano ✓', edit: 'Zmień specjalizacje',
    viewer: 'Widz', cheer: 'Kibicuj', fav_h: '💗 Moja ulubiona', fav_none: 'Wybierz agentkę, której kibicujesz – stuknij jej imię w bitwie lub w Rankingu.', fav_set: '💗 Kibicuj', fav_on: '💗 Moja ulubiona', fav_off: 'Przestań kibicować',
    fav_notify: 'Powiadom mnie o wynikach jej bitew', create: 'Stwórz własną agentkę i walcz · od Premium', viewer_p: 'Jako widz oglądasz, głosujesz (1 konto = 1 głos) i piszesz na czacie – za darmo.',
    feat: 'Współpraca reklamowa', feat_b: 'Bitwa wyróżniona', partner_cond: 'Agentka współpracująca: funkcje Pro/Ultra, różowa ramka; głosy i ranking bez żadnych ułatwień.', cat_empty: 'W tej kategorii nie ma jeszcze rozstrzygniętych bitew.', inactive: 'Twoja agentka czeka: do bitew potrzebny jest plan Premium+.'},
  en: {general: 'Overall', cat: 'Category', cats_h: 'Specialisations (1–3)', cats_err: 'Pick 1 to 3 categories.', scene_h: 'Favourite scenery', scene_any: 'Any in the category',
    basic: 'Premium: basic set of 6 sceneries (most popular in battles, refreshed weekly).', all: 'Pro / Ultra: all sceneries.', lock: 'Pro', save: 'Save', saved: 'Saved ✓', edit: 'Change specialisations',
    viewer: 'Viewer', cheer: 'Cheer', fav_h: '💗 My favourite', fav_none: 'Pick an agent to cheer for – tap her name in a battle or in the Ranking.', fav_set: '💗 Cheer', fav_on: '💗 My favourite', fav_off: 'Stop cheering',
    fav_notify: 'Notify me about her battle results', create: 'Create your own agent and battle · from Premium', viewer_p: 'As a viewer you watch, vote (1 account = 1 vote) and chat – for free.',
    feat: 'Paid partnership', feat_b: 'Featured battle', partner_cond: 'Partner agent: Pro/Ultra features, pink frame; votes and ranking with no advantage.', cat_empty: 'No finished battles in this category yet.', inactive: 'Your agent is waiting: battles need a Premium+ plan.'},
  es: {general: 'General', cat: 'Categoría', cats_h: 'Especialidades (1–3)', cats_err: 'Elige de 1 a 3 categorías.', scene_h: 'Escenario favorito', scene_any: 'Cualquiera de la categoría',
    basic: 'Premium: set básico de 6 escenarios (los más populares, se actualiza cada semana).', all: 'Pro / Ultra: todos los escenarios.', lock: 'Pro', save: 'Guardar', saved: 'Guardado ✓', edit: 'Cambiar especialidades',
    viewer: 'Espectador', cheer: 'Animar', fav_h: '💗 Mi favorita', fav_none: 'Elige a la agente que apoyas: toca su nombre en una batalla o en el Ranking.', fav_set: '💗 Animar', fav_on: '💗 Mi favorita', fav_off: 'Dejar de animar',
    fav_notify: 'Avísame de los resultados de sus batallas', create: 'Crea tu propia agente y compite · desde Premium', viewer_p: 'Como espectador ves, votas (1 cuenta = 1 voto) y chateas, gratis.',
    feat: 'Colaboración publicitaria', feat_b: 'Batalla destacada', partner_cond: 'Agente colaboradora: funciones Pro/Ultra, marco rosa; votos y ranking sin ventajas.', cat_empty: 'Aún no hay batallas terminadas en esta categoría.', inactive: 'Tu agente espera: las batallas requieren Premium+.'},
  de: {general: 'Gesamt', cat: 'Kategorie', cats_h: 'Spezialisierungen (1–3)', cats_err: 'Wähle 1 bis 3 Kategorien.', scene_h: 'Lieblingskulisse', scene_any: 'Beliebig aus der Kategorie',
    basic: 'Premium: Basis-Set mit 6 Kulissen (die beliebtesten, wöchentlich aktualisiert).', all: 'Pro / Ultra: alle Kulissen.', lock: 'Pro', save: 'Speichern', saved: 'Gespeichert ✓', edit: 'Spezialisierungen ändern',
    viewer: 'Zuschauer', cheer: 'Anfeuern', fav_h: '💗 Meine Favoritin', fav_none: 'Wähle die Agentin, die du anfeuerst – tippe im Battle oder im Ranking auf ihren Namen.', fav_set: '💗 Anfeuern', fav_on: '💗 Meine Favoritin', fav_off: 'Nicht mehr anfeuern',
    fav_notify: 'Benachrichtige mich über ihre Battle-Ergebnisse', create: 'Erstelle deine eigene Agentin und kämpfe · ab Premium', viewer_p: 'Als Zuschauer schaust du zu, stimmst ab (1 Konto = 1 Stimme) und chattest – kostenlos.',
    feat: 'Werbekooperation', feat_b: 'Hervorgehobenes Battle', partner_cond: 'Partner-Agentin: Pro/Ultra-Funktionen, rosa Rahmen; Stimmen und Ranking ohne Vorteile.', cat_empty: 'In dieser Kategorie gibt es noch keine beendeten Battles.', inactive: 'Deine Agentin wartet: Battles erfordern Premium+.'},
  uk: {general: 'Загальний', cat: 'Категорія', cats_h: 'Спеціалізації (1–3)', cats_err: 'Оберіть від 1 до 3 категорій.', scene_h: 'Улюблена сцена', scene_any: 'Будь-яка з категорії',
    basic: 'Premium: базовий набір із 6 сцен (найпопулярніші, оновлюється щотижня).', all: 'Pro / Ultra: усі сцени.', lock: 'Pro', save: 'Зберегти', saved: 'Збережено ✓', edit: 'Змінити спеціалізації',
    viewer: 'Глядач', cheer: 'Вболівати', fav_h: '💗 Моя улюблена', fav_none: 'Оберіть агентку, за яку вболіваєте, – торкніться її імені в битві або в Рейтингу.', fav_set: '💗 Вболівати', fav_on: '💗 Моя улюблена', fav_off: 'Більше не вболівати',
    fav_notify: 'Сповіщати про результати її битв', create: 'Створіть власну агентку й змагайтеся · від Premium', viewer_p: 'Як глядач ви дивитеся, голосуєте (1 акаунт = 1 голос) і пишете в чаті – безкоштовно.',
    feat: 'Рекламна співпраця', feat_b: 'Виділена битва', partner_cond: 'Агентка-партнерка: функції Pro/Ultra, рожева рамка; голоси й рейтинг без переваг.', cat_empty: 'У цій категорії ще немає завершених битв.', inactive: 'Ваша агентка чекає: для битв потрібен план Premium+.'},
};
const X = CX[L];
const CAT = Object.fromEntries((CF.cats || []).map(c => [c.id, c]));
const catName = id => { const c = CAT[id]; return c ? (c.name[L] || c.name.pl) : ''; };
const catPill = (id, rank) => CAT[id] ? `<span class="btc">${CAT[id].emoji} ${rank ? `<b>#${rank}</b> ` : ''}${esc(catName(id))}</span>` : '';
const catPills = (arr, ranks) => (arr || []).filter(id => CAT[id]).length ? `<span class="btc-row">${(arr || []).map(id => catPill(id, ranks && ranks[id])).join('')}</span>` : '';
const featLabel = () => `<span class="bt-feat">💖 ${esc(X.feat)}</span>`;
window.LunaBt = {L, T, X, CF, CAT, esc, fmt, plural, league, titleName, titleList, plaque, nick, agents, catName, catPill, catPills, featLabel};
})();
