/* Profil agentki AI: oficjalna Luna albo własna agentka użytkownika. Tylko obrazy AI, prywatny domyślnie, limity planu na serwerze. */
(() => {
const $ = s => document.querySelector(s);
const esc = x => String(x == null ? '' : x).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const D = JSON.parse(document.getElementById('i18n').textContent);
const lang = () => (document.documentElement.lang || 'pl').slice(0, 2);
const t = () => Object.assign({}, D.pl, D[lang()] || {});
const qs = new URLSearchParams(location.search); const id = (qs.get('id') || 'luna').slice(0, 12);
const lq = () => lang() === 'pl' ? '' : 'lang=' + lang();
const H = () => { const h = {'Content-Type': 'application/json'}; try { const tc = localStorage.getItem('luna.tester'); if (tc) h['X-Tester'] = tc; } catch(e){} return h; };
const host = $('#prof'); let V = null, ME = null, battlesOn = false, loaded = false;
const shareUrl = () => location.origin + '/agentka.html?id=' + encodeURIComponent(V.id) + (lq() ? '&' + lq() : '') + '&utm_source=share&utm_medium=profil&utm_campaign=agentka';
function draw(){
  const T = t(); if (!V){ host.innerHTML = `<div class="card"><p>${esc(T.priv)}</p><p><a class="pill primary" href="/agentka.html?id=luna${lq() ? '&' + lq() : ''}">${esc(T.luna_link)}</a></p></div>`; return; }
  const ph = V.photos || []; const main = ph.find(p => p.ref === V.pinned) || ph[0];
  const tier = V.tier === 'pro' ? 'nk-pro' : V.tier === 'premium' ? 'nk-premium' : '';
  const st = [];
  if (V.likes > 0) st.push(`<span>♥ ${esc(T.likes)}: <b>${V.likes}</b></span>`);
  if (V.battles && V.battles.wins) st.push(`<span>⚔️ ${esc(T.wins)}: <b>${V.battles.wins}</b></span>`);
  if (V.battles && (V.battles.cats || []).length){ const lg = (document.documentElement.lang || 'pl').slice(0, 2); st.push(`<span class="ph-cats">${V.battles.cats.map(c => `<span class="ph-cat">${c.emoji} ${c.rank ? `<b>#${c.rank}</b> ` : ''}${esc(c.name[lg] || c.name.pl)}</span>`).join('')}</span>`); }
  const P = V.partner;
  host.innerHTML = `<section class="card ph-head${P ? ' partner' : ''}">
    ${main ? `<span class="av-on-w"><img class="ph-main${P ? ' pt-ring' : ''}" src="${esc(main.url)}" alt="${esc(V.name)}" width="160" height="160">${V.pr && V.pr.on ? '<i class="av-dot" aria-hidden="true"></i>' : ''}</span>` : ''}
    <div><h1><span class="nk ${tier}">${esc(V.name)}</span> <span class="ai-badge" title="${esc(T.ainote)}">AI</span></h1>
      ${V.pr ? `<p class="ph-pr${V.pr.on ? ' on' : ''}">${V.pr.on ? '<i class="on-dot" aria-hidden="true"></i>' + esc(T.online) : esc(T.ago.replace('{n}', V.pr.min))}</p>` : ''}
      ${V.official ? `<p class="ph-off">✓ ${esc(T.official)}</p>` : ''}${P ? `<p class="ph-pt">${esc(T.pt_badge)}</p>` : ''}
      ${V.tags && V.tags.length ? `<p class="ph-tags">${V.tags.map(x => `<span>${esc(x)}</span>`).join('')}</p>` : ''}</div></section>
    ${P ? `<section class="card ph-ptinfo"><span class="ad-tag">${esc(T.pt_ad)}</span><p class="pt-h">${esc(T.pt_h)}</p><p>${esc(T.pt_p)}</p>${P.campaigns && P.campaigns.length ? `<h3>${esc(T.pt_c)}</h3><ul>${P.campaigns.map(c => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}</section>` : ''}
    ${V.bio ? `<p class="ph-bio">${esc(V.bio)}</p>` : ''}
    ${V.exercise ? `<p class="ph-ex"><b>🎙 ${esc(T.ex)}:</b> ${esc(V.exercise)}</p>` : ''}
    ${st.length ? `<p class="ph-stats">${st.join('')}</p>` : ''}
    <div class="ph-acts"><button type="button" class="pill ${V.liked ? 'primary' : 'ghost'}" id="phLike" aria-pressed="${V.liked}">${esc(V.liked ? T.liked : T.like)}</button>
      <button type="button" class="pill ghost" id="phShare">${esc(T.share)}</button>
      ${battlesOn ? `<a class="pill ghost" href="/bitwy.html?agent=${encodeURIComponent(V.id)}${lq() ? '&' + lq() : ''}">${esc(T.battles)}</a>` : ''}
      ${V.official || V.mine ? '' : `<button type="button" class="pill ghost" id="phRep" data-report="${esc(V.target)}">🚩 ${esc(T.report)}</button>`}</div>
    <p class="ph-msg small" id="phMsg" role="status"></p>
    ${V.battles && V.battles.history && V.battles.history.length ? `<details class="card"><summary>${esc(T.hist)}</summary><ul class="ph-hist">${V.battles.history.slice(0, 20).map(b => `<li>${b.result === 'win' ? '🏆' : b.result === 'draw' ? '🤝' : '•'} ${esc(V.name)} ${b.mine} : ${b.theirs} ${esc(b.opp)} · ${new Date(b.end * 1000).toLocaleDateString(lang())}</li>`).join('')}</ul></details>` : ''}
    ${ph.length ? `<div class="ph-grid">${ph.map(p => `<img src="${esc(p.url)}" alt="${esc(V.name)} – AI" loading="lazy" width="240" height="300"${p.ref === V.pinned ? ' class="pin"' : ''}>`).join('')}</div>` : ''}
    <p class="small ph-note">🤖 ${esc(T.ainote)}</p>
    <p class="ph-links"><a href="/agentka.html?id=${V.official ? 'me' : 'luna'}${lq() ? '&' + lq() : ''}">${esc(V.official ? T.mine_link : T.luna_link)}</a></p>`;
  $('#phLike').onclick = like; $('#phShare').onclick = share; if ($('#phRep')) $('#phRep').onclick = report;
}
async function like(){
  const r = await fetch('/api/vote', {method: 'POST', headers: H(), body: JSON.stringify({target: V.target, v: 1})}); const d = await r.json().catch(() => ({}));
  if (r.ok){ V.likes = d.up; V.liked = d.mine === 1; draw(); }
}
async function share(){
  const u = shareUrl();
  try { if (navigator.share){ await navigator.share({title: V.name + ' – AI', url: u}); return; } } catch(e){ return; }
  try { await navigator.clipboard.writeText(u); } catch(e){}
  $('#phMsg').textContent = t().copied;
}
async function report(){
  await fetch('/api/report', {method: 'POST', headers: H(), body: JSON.stringify({target: V.target, reason: 'profil agentki'})}).catch(() => {});
  $('#phMsg').textContent = t().reported;
}
/* ---------- edycja własnego profilu ---------- */
function editor(){
  const T = t(), C = ME.caps; const ed = $('#profEdit');
  if (ME.login){ ed.innerHTML = `<section class="card"><h2>${esc(T.mine_h)}</h2><p>${esc(T.login)}</p><p><a class="pill primary" href="/app">${esc(T.login_b)}</a></p></section>`; return; }
  if (!C.edit){ ed.innerHTML = `<section class="card ph-lock"><h2>${esc(T.lock)}</h2><p>${esc(T.lock_p)}</p><p><a class="pill primary" href="/app.html#plans">${esc(T.unlock)}</a></p></section>`; return; }
  const E = ME.edit || {name: (JSON.parse(localStorage.getItem('luna.custom') || '{}').name || ''), bio: '', tags: [], exercise: '', photos: [], pinned: '', public: false};
  const sel = new Set(E.photos || []);
  const opts = ME.options.map(o => `<label class="ph-opt${o.ok ? '' : ' locked'}"><input type="checkbox" value="${esc(o.ref)}"${sel.has(o.ref) ? ' checked' : ''}${o.ok ? '' : ' disabled'}><img src="${esc(o.url)}" alt="" loading="lazy" width="96" height="120">${o.ok ? '' : `<span class="lk">🔒 ${esc(o.plan === 'pro' ? 'Pro / Ultra' : o.plan === 'premium' ? 'Premium' : 'Podstawowa')}</span>`}</label>`).join('');
  ed.innerHTML = `<section class="card ph-ed"><h2>${esc(T.mine_h)}</h2><p class="small">${esc(T.anon)}</p>
    <label>${esc(T.f_name)}<input id="e_name" maxlength="24" value="${esc(E.name)}"></label>
    <label>${esc(T.f_bio)}<textarea id="e_bio" maxlength="280" rows="3">${esc(E.bio)}</textarea></label>
    <label>${esc(T.f_tags)}<input id="e_tags" maxlength="120" value="${esc((E.tags || []).join(', '))}"></label>
    <label>${esc(T.f_ex)}<input id="e_ex" maxlength="120" value="${esc(E.exercise)}"></label>
    <h3>${esc(T.f_ph)} <small id="e_cnt"></small></h3><p class="small">${esc(T.f_ph_p)}</p><div class="ph-opts" id="e_opts">${opts}</div>
    <label>${esc(T.f_pin)}${C.pin ? `<select id="e_pin"></select>` : ` <span class="lkinl">${esc(T.pin_lock)}</span>`}</label>
    <h3>${esc(T.f_own)}</h3><p class="small">${esc(T.gen_only)}</p><p><a class="pill ghost" href="/ustawienia.html#gen">✨ ${esc(T.gen_go)}</a></p>
    <label class="chk pub"><input type="checkbox" id="e_pub"${E.public ? ' checked' : ''}> ${esc(T.f_pub)}</label>
    <p class="small" id="e_pubnote"${E.public ? ' hidden' : ''}>${esc(T.pub_off)}</p>
    <p><button type="button" class="pill primary" id="e_save">${esc(T.save)}</button> ${ME.id ? `<a class="pill ghost" href="/agentka.html?id=${esc(ME.id)}${lq() ? '&' + lq() : ''}">${esc(T.view)}</a>` : ''}</p>
    <p class="ph-msg small" id="e_msg" role="status"></p></section>`;
  const boxes = () => [...ed.querySelectorAll('#e_opts input:checked')].map(i => i.value);
  const upd = () => { const n = boxes().length; $('#e_cnt').textContent = `${n}/${C.max_photos}`;
    ed.querySelectorAll('#e_opts input').forEach(i => { const o = ME.options.find(x => x.ref === i.value); i.disabled = !o.ok || (!i.checked && n >= C.max_photos); });
    const ps = $('#e_pin'); if (ps){ const cur = ps.value || E.pinned; ps.innerHTML = `<option value="">${esc(T.none)}</option>` + boxes().map((r, k) => `<option value="${esc(r)}"${r === cur ? ' selected' : ''}>${k + 1}</option>`).join(''); } };
  ed.querySelector('#e_opts').onchange = upd; upd();
  $('#e_pub').onchange = () => { $('#e_pubnote').hidden = $('#e_pub').checked; };
  $('#e_save').onclick = async () => {
    const body = {name: $('#e_name').value, bio: $('#e_bio').value, exercise: $('#e_ex').value, tags: $('#e_tags').value.split(',').map(x => x.trim()).filter(Boolean),
      photos: boxes(), pinned: $('#e_pin') ? $('#e_pin').value : '', public: $('#e_pub').checked};
    const r = await fetch('/api/agent/profile', {method: 'POST', headers: H(), body: JSON.stringify(body)}); const d = await r.json().catch(() => ({}));
    $('#e_msg').textContent = r.ok ? T.saved : (d.message || d.error || T.err); if (r.ok) load();
  };
  if ($('#e_file')) $('#e_file').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    if (!$('#e_decl').checked){ $('#e_msg').textContent = T.own_decl; return; }
    const rd = new FileReader(); rd.onload = async () => {
      const r = await fetch('/api/agent/profile/own', {method: 'POST', headers: H(), body: JSON.stringify({data: rd.result, ai_declared: true})}); const d = await r.json().catch(() => ({}));
      $('#e_msg').textContent = r.ok ? T.saved : (d.message || d.error || T.err); if (r.ok) load();
    }; rd.readAsDataURL(f);
  };
}
async function load(){
  const lp = lq() ? '&' + lq() : '';
  if (id === 'me'){
    const r = await fetch('/api/agent/profile?id=me' + lp, {headers: H()}); ME = await r.json().catch(() => ({}));
    V = ME.view || null; loaded = true; host.hidden = !V; draw(); editor(); return;
  }
  const r = await fetch('/api/agent/profile?id=' + encodeURIComponent(id) + lp, {headers: H()}); V = r.ok ? await r.json() : null; if (V && V.private) V = null; battlesOn = !!(V && V.battles_page); loaded = true; draw();
}
window.addEventListener('luna-lang', () => { if (loaded){ draw(); if (ME) editor(); } });
load();
})();
