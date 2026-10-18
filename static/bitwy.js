/* Bitwy agentek: stan z serwera (prawdziwe głosy, bez zasiewania), odliczanie, 1 głos na konto, czat na żywo, zgłoszenie własnej agentki AI. */
(() => {
const $ = s => document.querySelector(s);
const D = JSON.parse(document.getElementById('i18n').textContent);
const L = (document.documentElement.lang || 'pl').slice(0, 2); const t = Object.assign({}, D.pl, D[L] || {});
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
const role = c => c.official ? t.official : t.user_agent;
function face(c, side){
  return `<div class="bt-half ${side}"><div class="bt-face"><img src="${esc(c.img)}" alt="${esc(c.name)} (${esc(t.ai)})" width="220" height="293" decoding="async"><span class="bt-ai">${esc(t.ai)}</span></div>
    <div class="bt-name">${esc(c.name)}</div><div class="bt-role">${esc(role(c))}</div>${c.wins ? `<div class="bt-wins">🏆 ${fmt(c.wins)} ${esc(t.wins)}</div>` : ''}</div>`;
}
const scene = id => `--sc:${id}`;
function timer(){
  const el = $('#btTimer'); if (!el || !S || !S.battle) return;
  let s = Math.max(0, Math.floor(S.battle.end - (Date.now() / 1000 + skew)));
  if (s <= 0){ el.innerHTML = `<b>${esc(t.closed)}</b>`; document.querySelectorAll('.bt-vote').forEach(b => b.disabled = true); clearInterval(timer.iv); setTimeout(load, 2500); return; }
  const d = Math.floor(s / 86400); s %= 86400; const h = Math.floor(s / 3600); s %= 3600; const m = Math.floor(s / 60); s %= 60;
  el.innerHTML = `${esc(t.ends)}: <b>${d ? d + ' ' + t.dd + ' ' : ''}${h} ${t.hh} ${String(m).padStart(2, '0')} ${t.mm} ${String(s).padStart(2, '0')} ${t.ss}</b>`;
}
function renderStage(){
  const host = $('#btStage');
  if (S.state === 'live'){
    const b = S.battle, va = b.votes.a, vb = b.votes.b, tot = va + vb, pa = tot ? Math.round(va * 100 / tot) : 50;
    let act;
    if (b.own) act = `<p class="bt-msg">${esc(t.own)}</p>`;
    else if (b.mine) act = `<p class="bt-msg">${esc(t.voted.replace('{name}', b[b.mine].name))}</p>`;
    else if (!S.logged_in) act = `<p class="bt-msg"><a class="pill primary" href="/app#konto">${esc(t.login_vote)}</a></p>`;
    else act = `<div class="bt-actions"><button type="button" class="pill bt-vote a" data-side="a">${esc(t.vote)}: ${esc(b.a.name)}</button><button type="button" class="pill bt-vote b" data-side="b">${esc(t.vote)}: ${esc(b.b.name)}</button></div>`;
    host.innerHTML = `<div class="bt-stage" style="background-image:url('/bitwy/${esc(b.scene)}.webp')">
      <div class="bt-top"><span class="bt-live">${esc(t.live)}</span><span class="bt-scene">${esc(t['scene_' + b.scene] || '')}</span></div>
      ${face(b.a, 'a')}<div class="bt-split" aria-hidden="true"></div><div class="bt-vs" aria-hidden="true">VS</div>${face(b.b, 'b')}
      <div class="bt-bottom"><div class="bt-timer" id="btTimer"></div><div class="bt-bar" role="img" aria-label="${fmt(va)} : ${fmt(vb)}"><i class="a" style="width:${pa}%"></i><i class="b" style="width:${100 - pa}%"></i></div>
      <div class="bt-counts"><span>${fmt(va)} ${esc(t.votes)}</span><span>${fmt(vb)} ${esc(t.votes)}</span></div></div></div>${act}
      <p class="bt-msg"><button type="button" class="pill ghost sm" data-report="${esc(b.a.target)}">⚑ ${esc(t.report)}: ${esc(b.a.name)}</button> <button type="button" class="pill ghost sm" data-report="${esc(b.b.target)}">⚑ ${esc(t.report)}: ${esc(b.b.name)}</button></p>`;
    clearInterval(timer.iv); timer(); timer.iv = setInterval(timer, 1000);
    host.querySelectorAll('.bt-vote').forEach(btn => btn.onclick = vote);
  } else {
    const luna = {name: 'Luna', img: '/catalog/luna/outfit_sweter.jpg', official: true};
    host.innerHTML = `<div class="bt-stage" style="background-image:url('/bitwy/studio.webp')">
      <div class="bt-top"><span class="bt-live off">${esc(t.wait_h)}</span><span class="bt-scene">${esc(t.host)}</span></div>
      ${face(luna, 'a')}<div class="bt-split" aria-hidden="true"></div><div class="bt-vs" aria-hidden="true">VS</div>
      <div class="bt-half b"><div class="bt-slot"><span><b>?</b>${esc(t.slot)}</span></div></div>
      <div class="bt-wait"><h2>${esc(t.wait_h)}</h2><p>${esc(t.wait_p.replace('{n}', S.missing))}</p><a class="pill primary" href="#btEnter">⚔️ ${esc(t.enter_cta)}</a></div></div>
      <p class="bt-msg">${esc(t.free_note)}</p>`;
  }
}
function renderChamp(){
  const el = $('#btChamp'); const c = S.champion;
  if (!c){ el.hidden = true; return; }
  el.hidden = false; el.innerHTML = `<img src="${esc(c.c.img)}" alt="" width="56" height="72"><div><small>${esc(t.champ)}</small><b>${esc(c.c.name)} <span class="bt-ai" style="position:static">${esc(t.ai)}</span></b><small>${fmt(c.votes)} ${esc(t.votes)}</small></div>`;
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
  const el = $('#btEnterBody'); const lock = S.price ? t.lock.replace('{price}', String(S.price).replace('.', L === 'en' ? '.' : ',')) : t.lock_np;
  if (S.my_entry){ const m = S.my_entry;
    el.innerHTML = `<div class="bt-mine"><img src="${esc(m.img)}" alt="" width="72" height="96"><div><small>${esc(t.my_h)}</small><br><b>${esc(m.name)}</b> <span class="bt-ai" style="position:static">${esc(t.ai)}</span><br>${esc(m.status === 'approved' ? t.st_approved : t.st_pending)}${m.wins ? ` · 🏆 ${fmt(m.wins)}` : ''}<br><button type="button" class="pill ghost sm" id="btWd">${esc(t.withdraw)}</button></div></div>`;
    $('#btWd').onclick = async () => { if (!confirm(t.withdraw_q)) return; try { await api('/api/battles/withdraw', {}); load(); } catch(e){ alert(e.message); } };
    return; }
  if (!S.logged_in){ el.innerHTML = `<div class="bt-lock">${esc(lock)}</div><a class="pill primary" href="/app#konto">${esc(t.login)}</a> <span class="bt-note">${esc(t.login_enter)}</span>`; return; }
  if (!S.can_enter){ el.innerHTML = `<div class="bt-lock">${esc(lock)}</div><a class="pill primary" href="/promo.html${lq}#plany">💎 ${esc(t.unlock)}</a>`; return; }
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
  if (busy) return; busy = true; const side = e.currentTarget.dataset.side;
  document.querySelectorAll('.bt-vote').forEach(b => b.disabled = true);
  try { const d = await api('/api/battles/vote', {bid: S.battle.id, side}); apply(d); }
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
$('#btSay').onsubmit = async e => {
  e.preventDefault(); const inp = $('#btText'); const text = inp.value.trim(); if (!text) return;
  try { const d = await api('/api/battles/chat', {bid: S.battle.id, text, since: lastMsg, website: e.target.website.value}); inp.value = ''; addMsgs(d.items); }
  catch(err){ $('#btChatNote').textContent = err.message; }
};
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-mrep]'); if (!b) return;
  try { await api('/api/battles/chat/report', {bid: S.battle.id, mid: +b.dataset.mrep}); b.closest('.bt-m').style.opacity = .45; b.remove(); alert(t.reported); } catch(err){ alert(err.message); }
});
/* ---------- start ---------- */
function apply(d){ S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); renderEnter(); renderChat(); }
async function load(){
  try { if (!me){ const m = await api('/api/account/me'); me = m.user || {}; csrf = m.csrf || ''; } apply(await api('/api/battles')); }
  catch(e){ $('#btStage').innerHTML = `<p class="bt-note">${esc(t.err)}</p>`; }
}
load();
setInterval(() => { if (!document.hidden && !busy) api('/api/battles').then(d => { const keep = $('#btForm'); S = d; skew = d.now - Date.now() / 1000; renderStage(); renderChamp(); renderLast(); if (!keep) renderEnter(); }).catch(() => {}); }, 20000);
setInterval(pollChat, 4000);
})();
