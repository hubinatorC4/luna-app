/* Bitwy agentek: stan z serwera (prawdziwe głosy, bez zasiewania), odliczanie, 1 głos na konto, czat na żywo, zgłoszenie własnej agentki AI. */
(() => {
const $ = s => document.querySelector(s);
const D = JSON.parse(document.getElementById('i18n').textContent);
const L = (document.documentElement.lang || 'pl').slice(0, 2); const t = Object.assign({}, D.pl, D[L] || {});
const B = window.LunaBt;
const VW = {pl: ['głos', 'głosy', 'głosów'], en: ['vote', 'votes', 'votes'], es: ['voto', 'votos', 'votos'], de: ['Stimme', 'Stimmen', 'Stimmen'], uk: ['голос', 'голоси', 'голосів']};
const vw = n => { const f = VW[L] || VW.pl; let c = 'other'; try { c = new Intl.PluralRules(L).select(n); } catch (e) {} return esc(c === 'one' ? f[0] : c === 'few' ? f[1] : f[2]); };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const lq = L === 'pl' ? '' : '?lang=' + L;
const PT = {pl: 'Agentka współpracująca', en: 'Partner agent', es: 'Agente colaboradora', de: 'Partner-Agentin', uk: 'Агентка-партнерка'}[L] || 'Agentka współpracująca';
const ptm = c => c && c.partner ? `<span class="pt-mark" title="${esc(PT)}" aria-label="${esc(PT)}">💖</span>` : '';
const fmt = n => Number(n || 0).toLocaleString(L === 'uk' ? 'uk-UA' : L);
const BID = new URLSearchParams(location.search).get('b') || '';
const bq = () => '/api/battles' + (BID ? '?b=' + encodeURIComponent(BID) : '');
let S = null, csrf = '', me = null, skew = 0, lastMsg = 0, busy = false;
async function api(path, body){
  const o = body ? {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(body)} : {credentials: 'same-origin'};
  const r = await fetch(path, o); const d = await r.json().catch(() => ({}));
  if (!r.ok){ const e = new Error(d.error === 'plan_required' ? t.lock_np : d.login ? t.login_vote : (d.error || t.err)); e.status = r.status; throw e; }
  return d;
}
const HEART = '<svg class="bt-heart" viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="bth" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff5a6e"/><stop offset=".55" stop-color="#e0112b"/><stop offset="1" stop-color="#9c0618"/></linearGradient><linearGradient id="bta" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff2b0"/><stop offset=".5" stop-color="#f2c14e"/><stop offset="1" stop-color="#b8860b"/></linearGradient></defs>'
  + '<path d="M6 50 L22 38" stroke="url(#bta)" stroke-width="3" stroke-linecap="round"/><path d="M4 46 L8 44 L9 49 Z M7 51 L9 47 L12 50 Z" fill="#f2c14e"/>'
  + '<path d="M32 56 C14 43 6 34 6 23 C6 15 12 9 20 9 C25 9 29 12 32 16 C35 12 39 9 44 9 C52 9 58 15 58 23 C58 34 50 43 32 56 Z" fill="url(#bth)" stroke="#7a0412" stroke-width="1.2"/>'
  + '<path d="M15 16 C18 12 23 12 26 15" stroke="#fff" stroke-opacity=".75" stroke-width="3" fill="none" stroke-linecap="round"/><ellipse cx="44" cy="19" rx="4" ry="2.4" fill="#fff" fill-opacity=".35"/>'
  + '<path d="M40 28 L58 15" stroke="url(#bta)" stroke-width="3" stroke-linecap="round"/><path d="M60 13 L53 14 L57 19 Z" fill="url(#bta)"/></svg>';
function heart(btn){ if (matchMedia('(prefers-reduced-motion: reduce)').matches) return; btn.insertAdjacentHTML('beforeend', HEART); const h = btn.lastElementChild; setTimeout(() => h.remove(), 900); }
/* Ostre obrazy: sceneria 1x/2x w AVIF i WebP (image-set), agentki z katalogu 1x/2x (WebP z zapasowym JPG). Limit źródła scenerii: 1280×720. */
const SCN = (B.CF.scenes || []).concat(['city', 'studio', 'promenade', 'winter', 'gala', 'garden']);
const scName = s => t['scene_' + s] || B.titleName(s).replace(/^(Miss|Міс)\s/, '');
let CUR_CAT = null;
const sceneStyle = s => { s = SCN.includes(s) ? s : 'studio'; const u = (x, e) => `url('/bitwy/${s}${x}.${e}')`;
  return `background-image:${u('', 'webp')};background-image:-webkit-image-set(${u('', 'webp')} 1x,${u('@2x', 'webp')} 2x);background-image:image-set(${u('', 'avif')} type('image/avif') 1x,${u('@2x', 'avif')} type('image/avif') 2x,${u('', 'webp')} type('image/webp') 1x,${u('@2x', 'webp')} type('image/webp') 2x)`; };
function pic(src, alt, w, h, lazy){
  const m = /^(\/catalog\/[\w\/-]+)\.jpg$/.exec(src || ''); const at = `alt="${esc(alt)}" width="${w}" height="${h}" decoding="async"${lazy ? ' loading="lazy"' : ''}`;
  if (!m) return `<img src="${esc(src)}" ${at}>`;
  return `<picture><source type="image/webp" srcset="${m[1]}.webp 1x, ${m[1]}@2x.webp 2x"><img src="${m[1]}.jpg" srcset="${m[1]}.jpg 1x, ${m[1]}@2x.jpg 2x" ${at}></picture>`;
}
function face(c, side, rank, sub, cls){
  return `<div class="bt-half ${side} ${cls || ''}">${rank ? `<span class="bt-rank">#${rank}</span>` : ''}<div class="bt-pic${c.partner ? ' pt-ring' : ''}">${pic(c.img, c.name + ' (' + t.ai + ')', 300, 400)}</div>
    <div class="bt-cap"><div class="bt-name"><button type="button" class="bt-prof" data-agent="${esc(c.id || '')}">${esc(c.name)}</button>${ptm(c)}<span class="bt-ai">${esc(t.ai)}</span></div>${c.league ? `<div class="bt-lgrow">${B.league(c.league, c.elite)}${(c.titles || []).length ? ` <span class="bt-tt1">👑 ${esc(B.titleName(c.titles[c.titles.length - 1]))}</span>` : ''}</div>` : ''}${c.crank && CUR_CAT ? `<div class="bt-lgrow">${B.catPill(CUR_CAT, c.crank)}</div>` : ''}<div class="bt-sub">${sub}</div></div></div>`;
}
const role = c => esc(c.official ? t.official : t.user_agent) + (c.pts ? ` · ${fmt(c.pts)} ${esc(B.T.pts)}` : '');
function timer(){
  const el = $('#btTimer'); if (!el || !S || !S.battle || document.hidden) return;
  let s = Math.max(0, Math.floor(S.battle.end - (Date.now() / 1000 + skew)));
  if (s <= 0){ el.textContent = t.closed; document.querySelectorAll('.bt-vote').forEach(b => b.disabled = true); clearInterval(timer.iv); setTimeout(load, 2500); return; }
  const d = Math.floor(s / 86400); s %= 86400; const h = Math.floor(s / 3600); s %= 3600; const m = Math.floor(s / 60); s %= 60;
  el.textContent = `${t.ends}: ${d ? d + ' ' + t.dd + ' ' : ''}${h} ${t.hh} ${String(m).padStart(2, '0')} ${t.mm} ${String(s).padStart(2, '0')} ${t.ss}`;
}
const pct = (x, y) => (x + y) ? Math.round(x * 100 / (x + y)) : 50;
function renderStage(){
  const host = $('#btStage');
  const head = live => `<div class="bt-head"><span class="bt-live${live ? '' : ' off'}">${esc(live ? t.live : t.wait_h)}</span><span class="bt-view">👁 ${fmt(S.viewers)} ${esc(t.viewers)}</span></div>`;
  if (S.state === 'live'){
    const b = S.battle, va = b.votes.a, vb = b.votes.b, pa = pct(va, vb); CUR_CAT = b.cat || null;
    const btn = side => { const c = b[side], mine = b.mine === side;
      const dis = !!b.mine || b.own || !S.logged_in;
      return `<button type="button" class="bt-vote ${side}${mine ? ' done' : ''}" data-side="${side}"${dis ? ' disabled' : ''}>${esc(mine ? t.voted_btn : t.vote_for.replace('{name}', c.name))}</button>`; };
    const note = b.own ? `<p class="bt-msg">${esc(t.own)}</p>` : !S.logged_in ? `<p class="bt-msg"><a class="pill primary" href="/app#konto">${esc(t.login_vote)}</a></p>` : '';
    host.innerHTML = `${head(true)}<div class="bt-timeline"><span class="bt-timer" id="btTimer"></span><span class="bt-scene">${b.feat ? B.featLabel() + ' ' : ''}${b.cat ? B.catPill(b.cat) + ' ' : ''}${b.lg ? B.league(b.lg) + ' ' : ''}${esc(t.scene)}: ${esc(scName(b.scene))}</span></div>
      <div class="bt-stage" style="${sceneStyle(b.scene)}">${face(b.a, 'a', 1, `${fmt(va)} ${vw(va)} · ${role(b.a)}`)}${face(b.b, 'b', 2, `${fmt(vb)} ${vw(vb)} · ${role(b.b)}`)}<div class="bt-vs" aria-hidden="true">VS</div></div>
      <div class="bt-actions">${btn('a')}${btn('b')}</div>
      <div class="bt-bar" role="img" aria-label="${esc(b.a.name)} ${pa}% · ${esc(b.b.name)} ${100 - pa}%"><i class="a" style="width:${pa}%"></i><i class="b" style="width:${100 - pa}%"></i></div>
      <div class="bt-counts"><span class="a">${esc(b.a.name)} ${pa}%</span><span class="b">${esc(b.b.name)} ${100 - pa}%</span></div>${note}
      <p class="bt-msg"><button type="button" class="pill ghost sm" data-report="${esc(b.a.target)}">⚑ ${esc(t.report)}: ${esc(b.a.name)}</button> <button type="button" class="pill ghost sm" data-report="${esc(b.b.target)}">⚑ ${esc(t.report)}: ${esc(b.b.name)}</button></p>`;
    clearInterval(timer.iv); timer(); timer.iv = setInterval(timer, 1000);
    host.querySelectorAll('.bt-vote:not([disabled])').forEach(x => x.onclick = vote);
  } else {
    const luna = {id: 'luna', name: 'Luna', img: '/catalog/luna/outfit_sweter.jpg', official: true};
    host.innerHTML = `${head(false)}<div class="bt-timeline"><span class="bt-scene">${esc(t.host)}</span></div>
      <div class="bt-stage" style="${sceneStyle('studio')}">${face(luna, 'a', 0, role(luna))}
      <div class="bt-half b"><div class="bt-slot"><span><b>?</b>${esc(t.slot)}</span></div></div><div class="bt-vs" aria-hidden="true">VS</div></div>
      <div class="bt-wait"><h2>${esc(t.wait_h)}</h2><p>${esc(t.wait_p.replace('{n}', S.missing))}</p>${S.can_enter ? `<a class="pill primary" href="#btEnter">⚔️ ${esc(t.enter_cta)}</a>` : `<a class="bt-bubble" href="/promo.html${lq}#plany">✨ ${esc(B.X.create)}</a>`}<p class="bt-msg">${esc(t.free_note)}</p></div>`;
  }
}
function renderChamp(){
  const el = $('#btChamp'); const c = S.champion; CUR_CAT = null;
  if (!c || !c.a){ el.hidden = true; return; }
  const w = c.winner, sub = (side, n) => `${fmt(n)} ${vw(n)}`;
  el.hidden = false;
  el.innerHTML = `<h2>${esc(t.champ)} · ${esc(t.ended)}</h2>${c.cat ? `<p>${B.catPill(c.cat)}</p>` : ''}<div class="bt-stage" style="${sceneStyle(c.scene || 'gala')}">
    ${face(c.a, 'a', 0, sub('a', c.va), w === 'a' ? '' : 'lost')}${face(c.b, 'b', 0, sub('b', c.vb), w === 'b' ? '' : 'lost')}<div class="bt-vs" aria-hidden="true">VS</div>
    <div class="bt-win" style="left:${w === 'a' ? '25%' : '75%'}">🏆 ${esc(t.winner)}<small>${esc(t.pct_votes.replace('{p}', c.pct))}</small>${B.titleName(c.scene) ? `<small class="bt-wt">👑 ${esc(B.titleName(c.scene))}</small>` : ''}</div></div>`;
}
function renderLast(){
  const el = $('#btLastList');
  if (!S.last.length){ el.innerHTML = `<p class="bt-note">${esc(t.none_yet)}</p>`; return; }
  el.innerHTML = S.last.map(r => {
    const res = r.reason !== 'end' ? t.cancelled : r.winner ? `<span class="w">🏆 ${esc(r[r.winner].name)}</span> ${esc(t.won)} · 👑 ${esc(B.titleName(r.scene))} · +${S.pts_win || 10} ${esc(B.T.pts)}` : t.draw;
    const lgl = (r.feat ? B.featLabel() + ' ' : '') + (r.cat ? B.catPill(r.cat) + ' ' : '') + (r.lg ? `${B.league(r.lg)} ` : '');
    return `<div class="bt-r"><img${r.a.partner ? ' class="pt-ring"' : ''} src="${esc(r.a.img)}" alt="" width="40" height="52"><img${r.b.partner ? ' class="pt-ring"' : ''} src="${esc(r.b.img)}" alt="" width="40" height="52"><div><b>${esc(r.a.name)}</b>${ptm(r.a)} ${fmt(r.va)} : ${fmt(r.vb)} <b>${esc(r.b.name)}</b>${ptm(r.b)}<br>${lgl}${res} · ${new Date(r.end * 1000).toLocaleDateString(L)}</div></div>`;
  }).join('');
}
function renderEnter(){
  const el = $('#btEnterBody');
  if (S.my_entry){ const m = S.my_entry;
    el.innerHTML = `<div class="bt-mine"><img src="${esc(m.img)}" alt="" width="72" height="96"><div><small>${esc(t.my_h)}</small><br><b>${esc(m.name)}</b> <span class="bt-ai" style="position:static">${esc(t.ai)}</span><br>${esc(m.status === 'approved' ? t.st_approved : t.st_pending)}<br>${B.league(m.league || 'braz')} <b>${fmt(m.pts)} ${esc(B.T.pts)}</b>${m.pos ? ` · #${fmt(m.pos)}` : ''} · <a href="/ranking.html${lq}">${esc(t.rank_link)}</a>${B.plaque(m.titles)}${B.catPills(m.cats, m.cranks)}${m.active === false ? `<p class="bt-note">${esc(B.X.inactive)}</p>` : ''}<br><button type="button" class="pill ghost sm" id="btEdit">${esc(B.X.edit)}</button> <button type="button" class="pill ghost sm" id="btWd">${esc(t.withdraw)}</button></div></div>`;
    $('#btEdit').onclick = () => editPrefs(m);
    $('#btWd').onclick = async () => { if (!confirm(t.withdraw_q)) return; try { await api('/api/battles/withdraw', {}); load(); } catch(e){ alert(e.message); } };
    return; }
  const pr = v => String(v || '').replace('.', L === 'en' ? '.' : ',');
  const mp = S.my_plan === 'pro' ? 'u' : S.my_plan === 'premium' ? 'p' : 'f';
  const tiers = `<div class="bt-tiers"><div class="bt-tier${mp === 'f' ? ' mine' : ''}"><b>${esc(t.t_free_h)}</b>${esc(t.t_free_p)}</div>
    <div class="bt-tier p${mp === 'p' ? ' mine' : ''}"><b>${esc(S.price ? t.t_prem_h.replace('{price}', pr(S.price)) : 'Premium')}</b>${esc(t.t_prem_p)}${S.price ? ` <small>(${esc(t.per30)})</small>` : ''}</div>
    <div class="bt-tier u${mp === 'u' ? ' mine' : ''}"><b>${esc(S.price_pro ? t.t_pro_h.replace('{price}', pr(S.price_pro)) : 'Pro / Ultra')}</b>${esc(t.t_pro_p)}</div></div><ul class="bt-chk">${t.chk}</ul>`;
  const bubble = `<a class="bt-bubble" href="/promo.html${lq}#plany">✨ ${esc(B.X.create)}<small>${esc(B.X.viewer_p)}</small></a>`;
  const hd = $('#btEnter h2'), ld = $('#btEnter > p');
  if (!S.can_enter){ if (hd) hd.textContent = '👀 ' + B.X.viewer + ' · ' + B.X.cheer; if (ld) ld.hidden = true; }
  if (!S.logged_in){ el.innerHTML = `${bubble}${tiers}<a class="pill primary" href="/app#konto">${esc(t.login)}</a>`; return; }
  if (!S.can_enter){ el.innerHTML = `${favBlock()}${bubble}${tiers}`; bindFav(); return; }
  el.innerHTML = `<form id="btForm"><label>${esc(t.f_name)}<input type="text" id="btName" maxlength="24" required autocomplete="off"></label>
    <label>${esc(t.f_img)}<input type="file" id="btImg" accept="image/jpeg,image/png,image/webp" required></label>
    ${prefsFields({cats: [], scene: null, allowed_scenes: S.my_allowed || null})}
    <label class="ck"><input type="checkbox" id="btDecl" required><span>${esc(t.f_decl)}</span></label>
    <label class="ck"><input type="checkbox" id="btModest" required><span>${esc(t.f_modest)}</span></label>
    <label class="ck"><input type="checkbox" id="btRules" required><span>${esc(t.f_rules)} <a href="/regulamin.html${lq}#bitwy">§</a></span></label>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
    <button class="pill primary">${esc(t.f_send)}</button><p class="bt-note" id="btFormMsg" role="status"></p></form>`;
  limitCats($('#btForm'));
  $('#btForm').onsubmit = async e => {
    e.preventDefault(); const f = $('#btImg').files[0]; const msg = $('#btFormMsg'); if (!f) return;
    if (f.size > 5 * 1024 * 1024){ msg.textContent = 'Max 5 MB'; return; }
    const image = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); });
    e.submitter && (e.submitter.disabled = true);
    const cats = [...el.querySelectorAll('input[name=btcat]:checked')].map(x => x.value); if (cats.length < 1 || cats.length > 3){ msg.textContent = B.X.cats_err; e.submitter && (e.submitter.disabled = false); return; }
    try { await api('/api/battles/enter', {cats, scene: (el.querySelector('input[name=btsc]:checked') || {}).value || '', name: $('#btName').value, image, img_decl: $('#btDecl').checked, modest: $('#btModest').checked, rules: $('#btRules').checked, website: e.target.website.value});
      msg.textContent = t.f_sent; setTimeout(load, 800);
    } catch(err){ msg.textContent = err.message; e.submitter && (e.submitter.disabled = false); }
  };
}
/* ---------- specjalizacje i sceneria (Premium: podstawowy zestaw, Pro/Ultra i współpracujące: wszystkie) ---------- */
function prefsFields(m){
  const basic = S.basic_scenes || [], all = (S.scenes || []);
  const tier = m.scene_tier || ((S.my_plan === 'pro' || S.partner_me) ? 'all' : 'basic');
  const ok = s => tier === 'all' || basic.includes(s);
  return `<fieldset class="bt-fs"><legend>${esc(B.X.cats_h)}</legend><div class="bt-catpick">${(B.CF.cats || []).map(c => `<label><input type="checkbox" name="btcat" value="${c.id}"${(m.cats || []).includes(c.id) ? ' checked' : ''}> ${c.emoji} ${esc(B.catName(c.id))}</label>`).join('')}</div></fieldset>
    <fieldset class="bt-fs"><legend>${esc(B.X.scene_h)}</legend><div class="bt-catpick"><label><input type="radio" name="btsc" value=""${m.scene ? '' : ' checked'}> ${esc(B.X.scene_any)}</label>${all.map(s => `<label class="${ok(s) ? '' : 'lock'}"><input type="radio" name="btsc" value="${s}"${m.scene === s ? ' checked' : ''}${ok(s) ? '' : ' disabled'}> ${esc(scName(s))}${ok(s) ? '' : ' 🔒 ' + esc(B.X.lock)}</label>`).join('')}</div>
    <p class="bt-note">${esc(tier === 'all' ? B.X.all : B.X.basic)}</p></fieldset>`;
}
function limitCats(root){ root.addEventListener('change', e => { if (e.target.name !== 'btcat') return; const on = root.querySelectorAll('input[name=btcat]:checked'); if (on.length > 3) e.target.checked = false; }); }
function editPrefs(m){
  const d = sheet(`<h3>${esc(B.X.edit)}</h3><form id="btPrefs">${prefsFields(m)}<button class="pill primary">${esc(B.X.save)}</button> <span class="bt-note" id="btPrefsMsg" role="status"></span></form>`, B.X.edit);
  const f = d.querySelector('#btPrefs'); limitCats(f);
  f.onsubmit = async e => { e.preventDefault(); const msg = f.querySelector('#btPrefsMsg');
    const cats = [...f.querySelectorAll('input[name=btcat]:checked')].map(x => x.value); if (cats.length < 1 || cats.length > 3){ msg.textContent = B.X.cats_err; return; }
    try { await api('/api/battles/prefs', {cats, scene: (f.querySelector('input[name=btsc]:checked') || {}).value || ''}); msg.textContent = B.X.saved; setTimeout(load, 400); } catch (er){ msg.textContent = er.message; } };
}
/* ---------- „Moja ulubiona” – widz kibicuje agentce (opcjonalne powiadomienia o jej bitwach) ---------- */
function favBlock(){
  const f = S.fav;
  if (!f) return `<div class="bt-fav"><h3>${esc(B.X.fav_h)}</h3><p class="bt-note">${esc(B.X.fav_none)}</p></div>`;
  return `<div class="bt-fav"><h3>${esc(B.X.fav_h)}</h3><div class="bt-mine"><img src="${esc(f.img)}" alt="" width="56" height="74"><div><b>${esc(f.name)}</b> <span class="bt-ai" style="position:static">${esc(t.ai)}</span><br>${B.league(f.league || 'braz')} <b>${fmt(f.pts)} ${esc(B.T.pts)}</b>
    <label class="ck"><input type="checkbox" id="btFavN"${f.notify ? ' checked' : ''}><span>${esc(B.X.fav_notify)}</span></label><button type="button" class="pill ghost sm" id="btFavX">${esc(B.X.fav_off)}</button></div></div></div>`;
}
function bindFav(){
  const n = $('#btFavN'), x = $('#btFavX');
  if (n) n.onchange = async () => { try {
      const r = await api('/api/battles/fav', {id: S.fav.id, notify: n.checked, lang: L}); S.fav = r.fav; P.set('luna_bt_fav_n', n.checked);
      if (n.checked && P.push) P.push(sub => api('/api/battles/fav', {id: S.fav.id, notify: true, lang: L, sub})).catch(() => {});   // Web Push tylko po zgodzie przeglądarki
    } catch (er){ n.checked = !n.checked; alert(er.message); } };
  if (x) x.onclick = async () => { try { await api('/api/battles/fav', {id: ''}); S.fav = null; P.set('luna_bt_fav_n', false); renderEnter(); } catch (er){ alert(er.message); } };
}
async function vote(e){
  if (busy) return; busy = true; const btn0 = e.currentTarget, side = btn0.dataset.side;
  document.querySelectorAll('.bt-vote').forEach(b => b.disabled = true);
  try { const d = await api('/api/battles/vote', {bid: S.battle.id, side}); heart(btn0); setTimeout(() => apply(d), 800); }
  catch(err){ alert(err.message); load(); }
  busy = false;
}
/* ---------- czat ---------- */
function msgHtml(m){ return `<div class="bt-m${m.mine ? ' mine' : ''}" data-id="${m.id}">${m.mine ? '' : `<button type="button" data-mrep="${m.id}" aria-label="${esc(t.report)}">⚑</button>`}<b class="nk${m.tier ? ' nk-' + m.tier : ''}">${esc(m.nick)}</b>${m.partner ? ptm(m) : ''}${esc(m.text)}</div>`; }
async function pollChat(){
  if (!S || S.state !== 'live' || document.hidden) return;
  try { const d = await api('/api/battles/chat?bid=' + S.battle.id + '&since=' + lastMsg); addMsgs(d.items); } catch(e){}
}
function addMsgs(items){
  const box = $('#btMsgs'); if (!items.length && !box.children.length){ box.innerHTML = `<p class="bt-note" id="btEmpty">${esc(t.chat_empty)}</p>`; return; }
  const em = $('#btEmpty'); if (em && items.length) em.remove();
  const atEnd = box.scrollHeight - box.scrollTop - box.clientHeight < 40;
  items.forEach(m => { if (m.id > lastMsg) lastMsg = m.id; if (!box.querySelector(`[data-id="${m.id}"]`)) box.insertAdjacentHTML('beforeend', msgHtml(m)); });
  if (atEnd || items.some(m => m.mine)) box.scrollTop = box.scrollHeight;
}
function renderChat(){
  const form = $('#btSay'), note = $('#btChatNote');
  if (S.state !== 'live'){ form.hidden = true; $('#btMsgs').innerHTML = ''; note.textContent = t.chat_closed; return; }
  if (renderChat.bid !== S.battle.id){ renderChat.bid = S.battle.id; lastMsg = 0; $('#btMsgs').innerHTML = ''; }
  form.hidden = !S.logged_in; note.innerHTML = S.logged_in ? '' : `<a href="/app#konto">${esc(t.chat_login)}</a>`;
  pollChat();
}
$('#btSay').onsubmit = async e => { try { window.LunaEmoji && window.LunaEmoji.close(); } catch (_) {}
  e.preventDefault(); const inp = $('#btText'); const text = inp.value.trim(); if (!text) return;
  try { const d = await api('/api/battles/chat', {bid: S.battle.id, text, since: lastMsg, website: e.target.website.value}); inp.value = ''; addMsgs(d.items); }
  catch(err){ $('#btChatNote').textContent = err.message; }
};
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-mrep]'); if (!b) return;
  try { await api('/api/battles/chat/report', {bid: S.battle.id, mid: +b.dataset.mrep}); b.closest('.bt-m').style.opacity = .45; b.remove(); alert(t.reported); } catch(err){ alert(err.message); }
});
/* emoji: wspólny moduł /emoji.js (dołączany przez seo.localize) podpina się sam do pola z data-emoji */
/* ---------- start ---------- */
/* Pełny ekran na telefonie: zamknięcie (X) i cienki pasek; intro TOP 2 z prawdziwymi wygranymi z historii bitew. */
const RM = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const plural = (n, f) => { let c = 'other'; try { c = new Intl.PluralRules(L).select(n); } catch (e) {} return c === 'one' ? f[0] : c === 'few' ? f[1] : f[2]; };
/* Wejście/wyjście bez przymusu: X, ESC, przesunięcie w dół, minimalizacja do paska; ustawienia; podsumowanie (?sum=). */
const P = window.LunaBtPrefs || {get: k => k !== 'luna_bt_notify', set(){}, minimize(){}, restoreState: () => null, renderSettings(){}};
const QS = new URLSearchParams(location.search);
const sameRef = (() => { try { return !!document.referrer && new URL(document.referrer).origin === location.origin; } catch (_) { return false; } })();
const RESTORE = QS.get('restore') === '1' ? P.restoreState() : null;
function leave(){ if (sameRef && history.length > 1) history.back(); else location.href = '/' + (L === 'pl' ? '' : '?lang=' + L); }
function minimize(){
  if (!S || S.state !== 'live' || !S.battle){ leave(); return; }
  P.minimize({bid: S.battle.id, y: scrollY, pos: RESTORE && RESTORE.pos, t: Date.now()}); leave();
}
const sheetOpen = () => !!document.querySelector('.bt-sheet, .bt-intro');
(() => {
  const x = $('#btClose'); x.setAttribute('aria-label', t.close); x.title = t.close;
  x.onclick = e => { e.preventDefault(); leave(); };
  const m = $('#btMin'); m.setAttribute('aria-label', t.min); m.title = t.min; m.onclick = minimize;
  const g = $('#btSet'); g.setAttribute('aria-label', t.settings); g.title = t.settings; g.onclick = openSettings;
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !sheetOpen() && !/INPUT|TEXTAREA/.test((document.activeElement || {}).tagName || '')) leave(); });
  // przesunięcie w dół od góry ekranu = zamknięcie (jak w aplikacjach), tylko gdy strona jest na samej górze
  let y0 = null, x0 = 0;
  addEventListener('touchstart', e => { if (scrollY > 0 || sheetOpen() || e.target.closest('input,textarea,.bt-msgs,.bt-olist')) { y0 = null; return; } y0 = e.touches[0].clientY; x0 = e.touches[0].clientX; }, {passive: true});
  addEventListener('touchmove', e => { if (y0 == null) return; const dy = e.touches[0].clientY - y0; const m2 = $('main'); if (dy > 0 && Math.abs(e.touches[0].clientX - x0) < dy) m2.style.transform = `translateY(${Math.min(dy, 140) / 2}px)`; }, {passive: true});
  addEventListener('touchend', e => { if (y0 == null) return; const dy = (e.changedTouches[0] || {}).clientY - y0; $('main').style.transform = ''; y0 = null; if (dy > 120) leave(); });
})();
function sheet(html, label){
  const d = document.createElement('div'); d.className = 'bt-sheet'; d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true'); d.setAttribute('aria-label', label);
  d.innerHTML = `<div class="bt-sheet-in"><button type="button" class="bt-x2" aria-label="${esc(t.close)}">✕</button>${html}</div>`;
  document.body.appendChild(d); const x = d.querySelector('.bt-x2'); const prev = document.activeElement; x.focus();
  const close = () => { d.remove(); document.removeEventListener('keydown', k); prev && prev.focus && prev.focus(); }; const k = ev => { if (ev.key === 'Escape') close(); };
  x.onclick = close; d.onclick = ev => { if (ev.target === d) close(); }; document.addEventListener('keydown', k); return d;
}
function openSettings(){ const d = sheet('<div class="bt-sethost"></div>', t.settings); P.renderSettings(d.querySelector('.bt-sethost')); }
async function openSummary(bid){
  let s; try { s = await api('/api/battles/summary?bid=' + encodeURIComponent(bid)); } catch (_) { return; }
  const w = s.winner ? s[s.winner] : null, dec = L === 'en' ? (x => x.replace(',', '.')) : (x => x);
  const days = Math.max(1, Math.round((s.end - s.start) / 86400));
  sheet(`<h3>${esc(t.sum_h)}</h3><table class="bt-sum"><tr><th>${esc(t.sum_win)}</th><td>${w ? `🏆 <b>${esc(w.name)}</b> <span class="bt-ai" style="position:static">${esc(t.ai)}</span>` : esc(s.reason === 'end' ? t.draw : t.cancelled)}</td></tr>
    <tr><th>${esc(t.sum_score)}</th><td><b>${dec(s.pa)}% : ${dec(s.pb)}%</b></td></tr><tr><th>${esc(s.a.name)}</th><td>${fmt(s.va)} ${vw(s.va)}</td></tr><tr><th>${esc(s.b.name)}</th><td>${fmt(s.vb)} ${vw(s.vb)}</td></tr>
    ${w ? `<tr><th>${esc(t.sum_title)}</th><td><b class="bt-gold">👑 ${esc(B.titleName(s.scene))}</b> · +${S && S.pts_win || 10} ${esc(B.T.pts)}</td></tr>` : ''}<tr><th>${esc(t.sum_dur)}</th><td>${fmt(days)} ${esc(t.dd)}</td></tr></table>`, t.sum_h);
}
let introDone = false;
function intro(){
  if (introDone) return; introDone = true;
  if (!S || S.state !== 'live' || !S.battle || RM() || !P.get('luna_bt_intro') || RESTORE || QS.get('sum') || !(sameRef || QS.get('intro') === '1')) return;
  const b = S.battle;
  const plaque = c => `<div class="bi-lg">${B.league(c.league || 'braz', c.elite)}</div>${B.plaque(c.titles)}`;
  const card = (c, side, rank) => `<div class="bi-ag ${side}"><span class="bt-rank">#${rank}</span><span class="${c.partner ? 'pt-ring' : ''}">${pic(c.img, '', 300, 400)}</span><div class="bi-nm">${esc(c.name)}${ptm(c)}<span class="bt-ai">${esc(t.ai)}</span></div>${c.crank && b.cat ? `<div class="bi-lg">${B.catPill(b.cat, c.crank)}</div>` : ''}${plaque(c)}</div>`;
  const o = document.createElement('div'); o.className = 'bt-intro'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-label', t.intro_t);
  o.innerHTML = `<div class="bi-bg" style="${sceneStyle(b.scene)}"></div><i class="bi-slash"></i>
    <h2 class="bi-t">${b.lg ? esc(B.T.league + ' ' + (B.T.lg[b.lg] || '')) + ' · ' + esc(t.h1.replace(/^\S+\s/, '')) : esc(t.intro_t)}${b.cat ? `<small class="bi-cat">${B.CAT[b.cat] ? B.CAT[b.cat].emoji : ''} ${esc(B.catName(b.cat))}</small>` : ''}${b.feat ? `<small class="bi-cat">${B.featLabel()}</small>` : ''}</h2>${card(b.a, 'a', 1)}${card(b.b, 'b', 2)}<div class="bt-vs bi-vs" aria-hidden="true">VS</div>
    <button type="button" class="bi-skip">${esc(t.skip)} ›</button>`;
  document.body.appendChild(o); document.body.classList.add('bt-introon');
  let gone = false; const end = () => { if (gone) return; gone = true; o.classList.add('out'); document.body.classList.remove('bt-introon'); document.removeEventListener('keydown', key); setTimeout(() => o.remove(), 350); };
  const key = e => { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') end(); };
  o.addEventListener('click', end); document.addEventListener('keydown', key); o.querySelector('.bi-skip').focus({preventScroll: true});
  setTimeout(end, 2600);
}

/* ---------- inne trwające bitwy (pokazowa Top 2 i ligowe) ---------- */
function renderOthers(){
  const el = $('#btOthers'); const O = (S.others || []);
  if (O.length < 2){ el.hidden = true; return; }
  el.hidden = false; const cur = S.battle && S.battle.id;
  el.innerHTML = `<h2>${esc(t.others_h)}</h2><div class="bt-olist">${O.map(o => `<a class="bt-o${o.id === cur ? ' on' : ''}" href="/bitwy.html?b=${esc(o.id)}${L === 'pl' ? '' : '&lang=' + L}">
    <span class="bt-ot">${o.feat ? B.featLabel() : o.main ? esc(t.main_b) : B.league(o.lg)} ${o.cat ? B.catPill(o.cat) : ''}</span><span class="bt-ov"><img src="${esc(o.a.img)}" alt="" width="44" height="58"><i>VS</i><img src="${esc(o.b.img)}" alt="" width="44" height="58"></span>
    <span class="bt-on">${esc(o.a.name)} ${fmt(o.votes.a)} : ${fmt(o.votes.b)} ${esc(o.b.name)}</span></a>`).join('')}</div>`;
}
/* ---------- profil agentki (liga, Elita, punkty, tytuły – z prawdziwych wyników) ---------- */
document.addEventListener('click', async e => {
  const b = e.target.closest('.bt-prof'); if (!b || !b.dataset.agent) return;
  let d; try { d = await api('/api/battles/agent/' + encodeURIComponent(b.dataset.agent)); } catch(_){ return; }
  const T = B.T, dlg = document.createElement('div'); dlg.className = 'bt-sheet'; dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true'); dlg.setAttribute('aria-label', T.profile);
  dlg.innerHTML = `<div class="bt-sheet-in"><button type="button" class="bt-x2" aria-label="${esc(T.close)}">✕</button><img src="${esc(d.img)}" alt="${esc(d.name)} (${esc(T.ai)})" width="120" height="160">
    <h3>${esc(d.name)} <span class="bt-ai" style="position:static">${esc(T.ai)}</span></h3><p>${esc(d.official ? t.official : t.user_agent)}</p>
    <p>${B.league(d.league, d.elite)}</p><p class="bt-pstats"><b>${fmt(d.pts)} ${esc(T.pts)}</b> · ${esc(T.pos)} #${fmt(d.pos)} · ${fmt(d.wins)} ${esc(B.plural(d.wins, T.wins))} / ${fmt(d.played)} ${esc(T.played)} (${fmt(d.pct)}% ${esc(T.pct)})</p>
    ${B.catPills(d.cats, d.cranks)}<h4>${esc(T.titles)}</h4>${B.plaque(d.titles) || `<p class="bt-note">${esc(T.no_titles)}</p>`}<p>${S && S.logged_in ? `<button type="button" class="pill ${S.fav && S.fav.id === d.id ? 'primary' : 'ghost'} sm" id="btFavB">${esc(S.fav && S.fav.id === d.id ? B.X.fav_on : B.X.fav_set)}</button> ` : ''}<a class="pill ghost sm" href="/ranking.html${lq}">${esc(t.rank_link)}</a></p></div>`;
  document.body.appendChild(dlg); const x = dlg.querySelector('.bt-x2'); x.focus();
  const close = () => { dlg.remove(); document.removeEventListener('keydown', k); b.focus(); }; const k = ev => { if (ev.key === 'Escape') close(); };
  x.onclick = close; dlg.onclick = ev => { if (ev.target === dlg) close(); }; document.addEventListener('keydown', k);
  const fb = dlg.querySelector('#btFavB'); if (fb) fb.onclick = async () => { const on = !(S.fav && S.fav.id === d.id); try { const r = await api('/api/battles/fav', {id: on ? d.id : '', notify: on && !!(S.fav && S.fav.notify), lang: L}); S.fav = r.fav; fb.className = 'pill ' + (on ? 'primary' : 'ghost') + ' sm'; fb.textContent = on ? B.X.fav_on : B.X.fav_set; renderEnter(); } catch (er){ alert(er.message); } };
});
/* ---------- „+10 pkt” po prawdziwej wygranej Twojej agentki (raz na bitwę) ---------- */
function ptsGain(){
  const W = S.my_wins || []; if (!W.length) return;
  let seen = []; try { seen = JSON.parse(localStorage.getItem('bt_pts_seen') || '[]'); } catch(_){}
  const fresh = W.filter(x => !seen.includes(x)); if (!fresh.length) return;
  try { localStorage.setItem('bt_pts_seen', JSON.stringify(seen.concat(fresh).slice(-50))); } catch(_){}
  const n = fresh.length * (S.pts_win || 10), el = document.createElement('div');
  el.className = 'bt-pts' + (RM() ? ' still' : ''); el.setAttribute('role', 'status'); el.innerHTML = `<b>+${fmt(n)} ${esc(B.T.pts)}</b><small>${esc(t.pts_gain)}</small>`;
  document.body.appendChild(el); setTimeout(() => el.remove(), RM() ? 4000 : 2600);
}
let first = true;
function apply(d){ S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); renderEnter(); renderChat(); renderOthers(); intro();
  if (first){ first = false; if (RESTORE && RESTORE.y) scrollTo(0, RESTORE.y); if (QS.get('sum')) openSummary(QS.get('sum')); } setTimeout(ptsGain, introDone && S.state === 'live' && !RM() ? 2800 : 300); }
async function load(){
  try { if (!me){ const m = await api('/api/account/me'); me = m.user || {}; csrf = m.csrf || ''; } apply(await api(bq())); }
  catch(e){ $('#btStage').innerHTML = `<p class="bt-note">${esc(t.err)}</p>`; }
}
if (!P.get('luna_bt_show')){ $('main').innerHTML = `<section class="card bt-offmsg"><h2>⚔️ ${esc(t.h1.replace(/^\S+\s/, ''))}</h2><p>${esc(t.off_msg)}</p><button type="button" class="pill primary" id="btOn">${esc(t.off_btn)}</button></section>`; $('#btOn').onclick = () => { P.set('luna_bt_show', true); location.reload(); }; return; }
load();
setInterval(() => { if (!document.hidden && !busy) api(bq()).then(d => { const keep = $('#btForm'); S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); renderOthers(); if (!keep) renderEnter(); }).catch(() => {}); }, 20000);
setInterval(pollChat, 4000);
})();
