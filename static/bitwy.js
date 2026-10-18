/* Bitwy agentek: stan z serwera (prawdziwe głosy, bez zasiewania), odliczanie, 1 głos na konto, czat na żywo, zgłoszenie własnej agentki AI. */
(() => {
const $ = s => document.querySelector(s);
const D = JSON.parse(document.getElementById('i18n').textContent);
const L = (document.documentElement.lang || 'pl').slice(0, 2); const t = Object.assign({}, D.pl, D[L] || {});
const VW = {pl: ['głos', 'głosy', 'głosów'], en: ['vote', 'votes', 'votes'], es: ['voto', 'votos', 'votos'], de: ['Stimme', 'Stimmen', 'Stimmen'], uk: ['голос', 'голоси', 'голосів']};
const vw = n => { const f = VW[L] || VW.pl; let c = 'other'; try { c = new Intl.PluralRules(L).select(n); } catch (e) {} return esc(c === 'one' ? f[0] : c === 'few' ? f[1] : f[2]); };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const lq = L === 'pl' ? '' : '?lang=' + L;
const fmt = n => Number(n || 0).toLocaleString(L === 'uk' ? 'uk-UA' : L);
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
function face(c, side, rank, sub, cls){
  return `<div class="bt-half ${side} ${cls || ''}">${rank ? `<span class="bt-rank">#${rank}</span>` : ''}<div class="bt-pic"><img src="${esc(c.img)}" alt="${esc(c.name)} (${esc(t.ai)})" width="300" height="400" decoding="async"></div>
    <div class="bt-cap"><div class="bt-name">${esc(c.name)}<span class="bt-ai">${esc(t.ai)}</span></div><div class="bt-sub">${sub}</div></div></div>`;
}
const role = c => esc(c.official ? t.official : t.user_agent) + (c.wins ? ` · 🏆 ${fmt(c.wins)}` : '');
function timer(){
  const el = $('#btTimer'); if (!el || !S || !S.battle) return;
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
    const b = S.battle, va = b.votes.a, vb = b.votes.b, pa = pct(va, vb);
    const btn = side => { const c = b[side], mine = b.mine === side;
      const dis = !!b.mine || b.own || !S.logged_in;
      return `<button type="button" class="bt-vote ${side}${mine ? ' done' : ''}" data-side="${side}"${dis ? ' disabled' : ''}>${esc(mine ? t.voted_btn : t.vote_for.replace('{name}', c.name))}</button>`; };
    const note = b.own ? `<p class="bt-msg">${esc(t.own)}</p>` : !S.logged_in ? `<p class="bt-msg"><a class="pill primary" href="/app#konto">${esc(t.login_vote)}</a></p>` : '';
    host.innerHTML = `${head(true)}<div class="bt-timeline"><span class="bt-timer" id="btTimer"></span><span class="bt-scene">${esc(t.scene)}: ${esc(t['scene_' + b.scene] || '')}</span></div>
      <div class="bt-stage" style="background-image:url('/bitwy/${esc(b.scene)}.webp')">${face(b.a, 'a', 1, `${fmt(va)} ${vw(va)} · ${role(b.a)}`)}${face(b.b, 'b', 2, `${fmt(vb)} ${vw(vb)} · ${role(b.b)}`)}<div class="bt-vs" aria-hidden="true">VS</div></div>
      <div class="bt-actions">${btn('a')}${btn('b')}</div>
      <div class="bt-bar" role="img" aria-label="${esc(b.a.name)} ${pa}% · ${esc(b.b.name)} ${100 - pa}%"><i class="a" style="width:${pa}%"></i><i class="b" style="width:${100 - pa}%"></i></div>
      <div class="bt-counts"><span class="a">${esc(b.a.name)} ${pa}%</span><span class="b">${esc(b.b.name)} ${100 - pa}%</span></div>${note}
      <p class="bt-msg"><button type="button" class="pill ghost sm" data-report="${esc(b.a.target)}">⚑ ${esc(t.report)}: ${esc(b.a.name)}</button> <button type="button" class="pill ghost sm" data-report="${esc(b.b.target)}">⚑ ${esc(t.report)}: ${esc(b.b.name)}</button></p>`;
    clearInterval(timer.iv); timer(); timer.iv = setInterval(timer, 1000);
    host.querySelectorAll('.bt-vote:not([disabled])').forEach(x => x.onclick = vote);
  } else {
    const luna = {name: 'Luna', img: '/catalog/luna/outfit_sweter.jpg', official: true};
    host.innerHTML = `${head(false)}<div class="bt-timeline"><span class="bt-scene">${esc(t.host)}</span></div>
      <div class="bt-stage" style="background-image:url('/bitwy/studio.webp')">${face(luna, 'a', 0, role(luna))}
      <div class="bt-half b"><div class="bt-slot"><span><b>?</b>${esc(t.slot)}</span></div></div><div class="bt-vs" aria-hidden="true">VS</div></div>
      <div class="bt-wait"><h2>${esc(t.wait_h)}</h2><p>${esc(t.wait_p.replace('{n}', S.missing))}</p><a class="pill primary" href="#btEnter">⚔️ ${esc(t.enter_cta)}</a><p class="bt-msg">${esc(t.free_note)}</p></div>`;
  }
}
function renderChamp(){
  const el = $('#btChamp'); const c = S.champion;
  if (!c || !c.a){ el.hidden = true; return; }
  const w = c.winner, sub = (side, n) => `${fmt(n)} ${vw(n)}`;
  el.hidden = false;
  el.innerHTML = `<h2>${esc(t.champ)} · ${esc(t.ended)}</h2><div class="bt-stage" style="background-image:url('/bitwy/${esc(c.scene || 'gala')}.webp')">
    ${face(c.a, 'a', 0, sub('a', c.va), w === 'a' ? '' : 'lost')}${face(c.b, 'b', 0, sub('b', c.vb), w === 'b' ? '' : 'lost')}<div class="bt-vs" aria-hidden="true">VS</div>
    <div class="bt-win" style="left:${w === 'a' ? '25%' : '75%'}">🏆 ${esc(t.winner)}<small>${esc(t.pct_votes.replace('{p}', c.pct))}</small></div></div>`;
}
function renderLast(){
  const el = $('#btLastList');
  if (!S.last.length){ el.innerHTML = `<p class="bt-note">${esc(t.none_yet)}</p>`; return; }
  el.innerHTML = S.last.map(r => {
    const res = r.reason !== 'end' ? t.cancelled : r.winner ? `<span class="w">🏆 ${esc(r[r.winner].name)}</span> ${esc(t.won)}` : t.draw;
    return `<div class="bt-r"><img src="${esc(r.a.img)}" alt="" width="40" height="52"><img src="${esc(r.b.img)}" alt="" width="40" height="52"><div><b>${esc(r.a.name)}</b> ${fmt(r.va)} : ${fmt(r.vb)} <b>${esc(r.b.name)}</b><br>${res} · ${new Date(r.end * 1000).toLocaleDateString(L)}</div></div>`;
  }).join('');
}
function renderEnter(){
  const el = $('#btEnterBody');
  if (S.my_entry){ const m = S.my_entry;
    el.innerHTML = `<div class="bt-mine"><img src="${esc(m.img)}" alt="" width="72" height="96"><div><small>${esc(t.my_h)}</small><br><b>${esc(m.name)}</b> <span class="bt-ai" style="position:static">${esc(t.ai)}</span><br>${esc(m.status === 'approved' ? t.st_approved : t.st_pending)}${m.wins ? ` · 🏆 ${fmt(m.wins)}` : ''}<br><button type="button" class="pill ghost sm" id="btWd">${esc(t.withdraw)}</button></div></div>`;
    $('#btWd').onclick = async () => { if (!confirm(t.withdraw_q)) return; try { await api('/api/battles/withdraw', {}); load(); } catch(e){ alert(e.message); } };
    return; }
  const pr = v => String(v || '').replace('.', L === 'en' ? '.' : ',');
  const mp = S.my_plan === 'pro' ? 'u' : S.my_plan === 'premium' ? 'p' : 'f';
  const tiers = `<div class="bt-tiers"><div class="bt-tier${mp === 'f' ? ' mine' : ''}"><b>${esc(t.t_free_h)}</b>${esc(t.t_free_p)}</div>
    <div class="bt-tier p${mp === 'p' ? ' mine' : ''}"><b>${esc(S.price ? t.t_prem_h.replace('{price}', pr(S.price)) : 'Premium')}</b>${esc(t.t_prem_p)}${S.price ? ` <small>(${esc(t.per30)})</small>` : ''}</div>
    <div class="bt-tier u${mp === 'u' ? ' mine' : ''}"><b>${esc(S.price_pro ? t.t_pro_h.replace('{price}', pr(S.price_pro)) : 'Pro / Ultra')}</b>${esc(t.t_pro_p)}</div></div><ul class="bt-chk">${t.chk}</ul>`;
  if (!S.logged_in){ el.innerHTML = `${tiers}<a class="pill primary" href="/app#konto">${esc(t.login)}</a> <span class="bt-note">${esc(t.login_enter)}</span>`; return; }
  if (!S.can_enter){ el.innerHTML = `${tiers}<a class="pill primary" href="/promo.html${lq}#plany">💎 ${esc(t.unlock)}</a>`; return; }
  el.innerHTML = `<form id="btForm"><label>${esc(t.f_name)}<input type="text" id="btName" maxlength="24" required autocomplete="off"></label>
    <label>${esc(t.f_img)}<input type="file" id="btImg" accept="image/jpeg,image/png,image/webp" required></label>
    <label class="ck"><input type="checkbox" id="btDecl" required><span>${esc(t.f_decl)}</span></label>
    <label class="ck"><input type="checkbox" id="btModest" required><span>${esc(t.f_modest)}</span></label>
    <label class="ck"><input type="checkbox" id="btRules" required><span>${esc(t.f_rules)} <a href="/regulamin.html${lq}#bitwy">§</a></span></label>
    <input type="text" name="website" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
    <button class="pill primary">${esc(t.f_send)}</button><p class="bt-note" id="btFormMsg" role="status"></p></form>`;
  $('#btForm').onsubmit = async e => {
    e.preventDefault(); const f = $('#btImg').files[0]; const msg = $('#btFormMsg'); if (!f) return;
    if (f.size > 5 * 1024 * 1024){ msg.textContent = 'Max 5 MB'; return; }
    const image = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); });
    e.submitter && (e.submitter.disabled = true);
    try { await api('/api/battles/enter', {name: $('#btName').value, image, img_decl: $('#btDecl').checked, modest: $('#btModest').checked, rules: $('#btRules').checked, website: e.target.website.value});
      msg.textContent = t.f_sent; setTimeout(load, 800);
    } catch(err){ msg.textContent = err.message; e.submitter && (e.submitter.disabled = false); }
  };
}
async function vote(e){
  if (busy) return; busy = true; const btn0 = e.currentTarget, side = btn0.dataset.side;
  document.querySelectorAll('.bt-vote').forEach(b => b.disabled = true);
  try { const d = await api('/api/battles/vote', {bid: S.battle.id, side}); heart(btn0); setTimeout(() => apply(d), 800); }
  catch(err){ alert(err.message); load(); }
  busy = false;
}
/* ---------- czat ---------- */
function msgHtml(m){ return `<div class="bt-m${m.mine ? ' mine' : ''}" data-id="${m.id}">${m.mine ? '' : `<button type="button" data-mrep="${m.id}" aria-label="${esc(t.report)}">⚑</button>`}<b>${esc(m.nick)}</b>${esc(m.text)}</div>`; }
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
(() => { const x = $('#btClose'); if (!x) return; x.setAttribute('aria-label', t.close);
  x.onclick = e => { let same = false; try { same = !!document.referrer && new URL(document.referrer).origin === location.origin; } catch (_) {}
    if (same && history.length > 1){ e.preventDefault(); history.back(); } else x.href = '/promo.html' + lq; }; })();
let introDone = false;
function intro(){
  if (introDone) return; introDone = true;
  if (!S || S.state !== 'live' || !S.battle || RM()) return;
  const b = S.battle;
  const plaque = c => c.wins > 0 ? `<div class="bi-plq">🏆 ${fmt(c.wins)} ${esc(plural(c.wins, t.pl_w))}</div>` : '';
  const card = (c, side, rank) => `<div class="bi-ag ${side}"><span class="bt-rank">#${rank}</span><img src="${esc(c.img)}" alt="" width="300" height="400"><div class="bi-nm">${esc(c.name)}<span class="bt-ai">${esc(t.ai)}</span></div>${plaque(c)}</div>`;
  const o = document.createElement('div'); o.className = 'bt-intro'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-label', t.intro_t);
  o.innerHTML = `<div class="bi-bg" style="background-image:url('/bitwy/${esc(b.scene)}.webp')"></div><i class="bi-slash"></i>
    <h2 class="bi-t">${esc(t.intro_t)}</h2>${card(b.a, 'a', 1)}${card(b.b, 'b', 2)}<div class="bt-vs bi-vs" aria-hidden="true">VS</div>
    <button type="button" class="bi-skip">${esc(t.skip)} ›</button>`;
  document.body.appendChild(o); document.body.classList.add('bt-introon');
  let gone = false; const end = () => { if (gone) return; gone = true; o.classList.add('out'); document.body.classList.remove('bt-introon'); document.removeEventListener('keydown', key); setTimeout(() => o.remove(), 350); };
  const key = e => { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') end(); };
  o.addEventListener('click', end); document.addEventListener('keydown', key); o.querySelector('.bi-skip').focus({preventScroll: true});
  setTimeout(end, 2600);
}
function apply(d){ S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); renderEnter(); renderChat(); intro(); }
async function load(){
  try { if (!me){ const m = await api('/api/account/me'); me = m.user || {}; csrf = m.csrf || ''; } apply(await api('/api/battles')); }
  catch(e){ $('#btStage').innerHTML = `<p class="bt-note">${esc(t.err)}</p>`; }
}
load();
setInterval(() => { if (!document.hidden && !busy) api('/api/battles').then(d => { const keep = $('#btForm'); S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); if (!keep) renderEnter(); }).catch(() => {}); }, 20000);
setInterval(pollChat, 4000);
})();
