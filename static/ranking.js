/* Ranking bitew: agentki (globalnie i w ligach), Top użytkowników (cały czas / miesiąc / tydzień), własna pozycja i postęp do kolejnej ligi.
   Tylko prawdziwe dane z serwera, tylko nicki (bez imion i e-maili), przełącznik prywatności. */
(() => {
const $ = s => document.querySelector(s); const B = window.LunaBt, esc = B.esc, fmt = B.fmt;
const D = JSON.parse(document.getElementById('i18n').textContent); const L = B.L; const t = Object.assign({}, D.pl, D[L] || {});
const lq = L === 'pl' ? '' : '?lang=' + L;
let R = null, csrf = '', logged = false, lg = 'all', per = 'all', cat = null;
async function api(path, body){
  const o = body ? {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(body)} : {credentials: 'same-origin'};
  const r = await fetch(path, o); const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || 'error'); return d;
}
const empty = s => `<p class="rk-empty">🕊️ ${esc(s)}</p>`;
function renderMe(){
  const el = $('#rkMe'), m = R.my_agent;
  if (!logged){ el.innerHTML = `<h2>${esc(t.me_h)}</h2><p>${esc(t.me_login)}</p><a class="pill primary" href="/app#konto">${esc(t.login)}</a>`; return; }
  if (!m && R.role === 'viewer'){ const f = R.fav;   // widz (Podstawowa/Darmowy): kibicuje, nie zgłasza agentki
    el.innerHTML = `<h2>${esc(t.me_h)}</h2><p><span class="bt-role">👀 ${esc(B.X.viewer)}</span></p><h3 class="rk-favh">${esc(B.X.fav_h)}</h3>${f ? `<div class="rk-mine"><img src="${esc(f.img)}" alt="" width="56" height="74"><div><b>${esc(f.name)}</b> <span class="rk-ai">${esc(B.T.ai)}</span><br>${B.league(f.league)} <b>${fmt(f.pts)} ${esc(B.T.pts)}</b></div></div>` : `<p class="rk-note">${esc(B.X.fav_none)}</p>`}
      <a class="bt-bubble" href="/promo.html${lq}#plany">✨ ${esc(B.X.create)}<small>${esc(B.X.viewer_p)}</small></a>`; return; }
  if (!m){ el.innerHTML = `<h2>${esc(t.me_h)}</h2><p>${esc(t.me_none)}</p><a class="pill primary" href="/bitwy.html${lq}#btEnter">⚔️ ${esc(t.me_cta)}</a>`; return; }
  const nx = m.next, pct = nx ? Math.max(0, Math.min(100, Math.round((m.pts - m.from) * 100 / (nx.at - m.from)))) : 100;
  el.innerHTML = `<h2>${esc(t.me_h)}</h2><div class="rk-mine"><img src="${esc(m.img)}" alt="" width="64" height="84"><div>
    <b>${esc(m.name)}</b> <span class="rk-ai">${esc(B.T.ai)}</span><br>${B.league(m.league, m.elite)} <b class="rk-big">${fmt(m.pts)} ${esc(B.T.pts)}</b><br>
    <small>${esc(t.pos_g.replace('{n}', fmt(m.pos)))} · ${esc(t.pos_l.replace('{n}', fmt(m.lpos)))}</small></div></div>
    <div class="rk-prog" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}"><i style="width:${pct}%"></i></div>
    ${B.catPills(m.cats, Object.fromEntries((m.cats || []).map(c => [c, ((R.cats || {})[c] || []).find(x => x.id === m.id)?.cpos])))}<br><small>${esc(nx ? t.to_next.replace('{name}', B.T.lg[nx.key]).replace('{n}', fmt(nx.at - m.pts)) : t.top)}</small>${B.plaque(m.titles)}`;
}
function chips(host, items, cur, on){
  host.innerHTML = items.map(([k, label]) => `<button type="button" class="rk-chip${k === cur ? ' on' : ''}" data-k="${esc(k)}" aria-pressed="${k === cur}">${label}</button>`).join('');
  host.querySelectorAll('button').forEach(b => b.onclick = () => on(b.dataset.k));
}
function renderA(){
  chips($('#lgChips'), [['all', esc(t.global)]].concat(R.leagues.map(x => [x.key, B.league(x.key)])), lg, k => { lg = k; renderA(); });
  const el = $('#listA');
  let list, posOf;
  if (cat){   // ranking kategorii: tylko agentki z tą specjalizacją, punkty tylko z bitew tej kategorii
    const C = (R.cats || {})[cat] || []; list = lg === 'all' ? C : C.filter(a => a.league === lg);
    posOf = (a, i) => lg === 'all' ? a.cpos : i + 1;
    const head = `<p class="rk-cath">${B.catPill(cat)}</p>`;
    if (!list.length){ el.innerHTML = head + empty(lg === 'all' ? B.X.cat_empty : t.empty_l); return; }
    el.innerHTML = head + (R.cat_results && R.cat_results[cat] ? '' : empty(B.X.cat_empty)) + rows(list, posOf); return;
  }
  list = lg === 'all' ? R.agents : (R.by_league[lg] || []); posOf = a => lg === 'all' ? a.pos : a.lpos;
  if (!R.has_results && lg === 'all'){ el.innerHTML = empty(t.empty_a); return; }
  if (!list.length){ el.innerHTML = empty(t.empty_l); return; }
  el.innerHTML = rows(list, posOf);
}
function titlesOf(a){ const c = a.cat_titles || {}, k = Object.keys(c).filter(x => c[x] > 0);
  return k.length ? `<br><small class="rk-tt" title="${esc(t.titles_h || '')}">👑 ${k.map(x => `${B.CAT[x] ? B.CAT[x].emoji : ''} ${esc(B.catName(x))} ×${fmt(c[x])}`).join(' · ')}</small>` : ''; }
function rows(list, posOf){
  return `<ol class="rk-list">${list.map((a, i) => `<li class="rk-row${R.my_agent && R.my_agent.id === a.id ? ' me' : ''}"><span class="rk-pos">${fmt(posOf(a, i))}</span>
    <img src="${esc(a.img)}" alt="" width="40" height="52" loading="lazy"><span class="rk-name"><b>${esc(a.name)}</b> <span class="rk-ai">${esc(B.T.ai)}</span><br>${B.league(a.league, a.elite)}${cat ? '' : ' ' + (a.cats || []).map(c => B.CAT[c] ? `<span title="${esc(B.catName(c))}">${B.CAT[c].emoji}</span>` : '').join('')}</span>
    <span class="rk-num"><b>${fmt(a.pts)}</b> ${esc(B.T.pts)}<br><small>${esc((t.wld || '{w}/{l}/{d}').replace('{w}', fmt(a.wins)).replace('{l}', fmt(a.losses || 0)).replace('{d}', fmt(a.draws || 0)))} · ${fmt(a.pct)}%</small>${titlesOf(a)}</span></li>`).join('')}</ol>`;
}
function userRow(u, pinned){
  return `<tr class="${u.me ? 'me' : ''}${pinned ? ' pin' : ''}"><td class="rk-pos">${u.pos ? fmt(u.pos) : '–'}</td>
    <td>${u.nick ? B.nick(u.nick, u.plan) : esc(t.you)}${u.me && u.nick ? ` <small>(${esc(t.you)})</small>` : ''}<br>${B.league(u.league)}</td>
    <td class="rk-ag">${B.agents(u.agents)}</td><td>${fmt(u.wins)}</td><td><b>${fmt(u.pts)}</b></td><td>${fmt(u.pct)}%</td></tr>`;
}
async function renderU(){
  chips($('#perChips'), [['all', esc(t.all)], ['month', esc(t.month)], ['week', esc(t.week)]], per, async k => { per = k; R = await api('/api/battles/ranking?period=' + k); renderU(); });
  const U = R.users, el = $('#listU');
  const head = `<thead><tr><th>${esc(t.c_pos)}</th><th>${esc(t.c_nick)}</th><th>${esc(t.c_agents)}</th><th>${esc(t.c_wins)}</th><th>${esc(t.c_pts)}</th><th>${esc(t.c_pct)}</th></tr></thead>`;
  const me = U.me, inList = me && U.items.some(x => x.me);
  const pin = me ? (me.pos ? userRow(me, true) : `<tr class="me pin"><td class="rk-pos">–</td><td colspan="5">${esc(t.you)} · ${B.league(me.league)} · ${B.agents(me.agents)} · ${esc(t.not_ranked)}</td></tr>`) : '';
  el.innerHTML = (U.items.length ? '' : empty(t.empty_u)) + `<div class="rk-tw"><table class="rk-table">${head}<tbody>${U.items.map(u => userRow(u)).join('')}</tbody>${me && (!inList || me.pos > 10) ? `<tfoot>${pin}</tfoot>` : ''}</table></div>`;
  if (!U.items.length && !me) el.querySelector('.rk-tw').remove();
  const pb = $('#privBox'); pb.hidden = !logged; $('#privT').checked = !!U.hidden;
  let ph = $('#privOn'); if (U.hidden){ if (!ph){ pb.insertAdjacentHTML('afterend', `<p class="rk-note" id="privOn">${esc(t.priv_on)}</p>`); } } else if (ph) ph.remove();
}
$('#privT').onchange = async e => { try { await api('/api/battles/privacy', {hide: e.target.checked}); R = await api('/api/battles/ranking?period=' + per); renderU(); } catch(err){ e.target.checked = !e.target.checked; alert(err.message); } };
/* zakładki: Ogólny, Top użytkowników, potem każda kategoria (z filtrem lig) */
$('#tabA').textContent = B.X.general;
const catHost = document.createElement('div'); catHost.className = 'rk-chips rk-cats'; catHost.setAttribute('role', 'tablist'); $('.rk-tabs').after(catHost);
function renderCats(){ catHost.innerHTML = (B.CF.cats || []).map(c => `<button type="button" role="tab" class="rk-chip${cat === c.id ? ' on' : ''}" data-c="${c.id}" aria-selected="${cat === c.id}">${c.emoji} ${esc(B.catName(c.id))}</button>`).join('');
  catHost.querySelectorAll('button').forEach(b => b.onclick = () => { cat = b.dataset.c; tab(false, true); }); }
function tab(u, keepCat){ if (!keepCat) cat = null; $('#tabA').classList.toggle('on', !u && !cat); $('#tabU').classList.toggle('on', u); $('#tabA').setAttribute('aria-selected', !u && !cat); $('#tabU').setAttribute('aria-selected', u); $('#pA').hidden = u; $('#pU').hidden = !u; renderCats(); if (R && !u) renderA(); }
$('#tabA').onclick = () => tab(false); $('#tabU').onclick = () => tab(true);
renderCats();
const hc = /^#kat-(\w+)$/.exec(location.hash); if (hc && B.CAT[hc[1]]) { cat = hc[1]; tab(false, true); }
if (location.hash === '#top') tab(true);
(async () => {
  try { const m = await api('/api/account/me'); csrf = m.csrf || ''; logged = !!(m.user && m.user.uid); } catch(e){}
  try { R = await api('/api/battles/ranking?period=all'); renderMe(); renderA(); renderU(); }
  catch(e){ $('#listA').innerHTML = empty('Ups…'); }
})();
})();
