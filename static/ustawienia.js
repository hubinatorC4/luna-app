/* Mój panel / Ustawienia: nagłówek profilu, wyszukiwarka, grupy wierszy, arkusze edycji, przewodnik w dymkach.
   Wszystkie limity planu sprawdza serwer (402 z nazwą planu) – tu tylko je pokazujemy. */
(() => {
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const D = JSON.parse(document.getElementById('i18n').textContent);
const lang = () => (document.documentElement.lang || 'pl').slice(0, 2);
const T = k => (Object.assign({}, D.pl, D[lang()] || {}))[k] || k;
const F = (k, o) => T(k).replace(/\{(\w+)\}/g, (_, x) => o[x] ?? '');
const INBOX = '/skrzynka.html', FRIENDS = '/znajomi.html', PRIV = '/znajomi.html#prywatnosc';  // trasy Skrzynki/Znajomych (inbox.py / inbox.js)
let ME = null, CSRF = '', P = null, open = '', FP = {};
const api = async (u, body, csrf) => {
  const o = body === undefined ? {credentials: 'same-origin'} : {method: 'POST', credentials: 'same-origin', headers: Object.assign({'Content-Type': 'application/json'}, csrf ? {'X-CSRF-Token': CSRF} : {}), body: JSON.stringify(body)};
  const r = await fetch(u, o); let j = {}; try { j = await r.json(); } catch(e){}
  if (!r.ok) { const e = new Error(j.message || j.error || ('HTTP ' + r.status)); e.status = r.status; e.data = j; throw e; }
  return j;
};
const toast = (msg, emoji) => {
  let t = $('#stToast'); if (!t){ t = document.createElement('div'); t.id = 'stToast'; t.className = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
  t.innerHTML = `<span class="toast-ic" aria-hidden="true">${emoji || '🌙'}</span><span>${esc(msg)}</span>`; t.hidden = false;
  clearTimeout(t._h); t._h = setTimeout(() => { t.hidden = true; }, 3800);
};
const avatarURL = () => {
  const a = (P && P.profile && P.profile.avatar) || '';
  if (a.startsWith('preset:')) return `/avatars/preset-${a.slice(7)}.svg`;
  if (a.startsWith('up:')) return `/api/user/avatar/${P.uref}.jpg?v=${a.slice(3, 9)}`;
  if (a.startsWith('gen:') && P.agent) return `/api/agent/profile/img/${P.agent.id}.jpg?v=${a.slice(4, 12)}`;
  return '/avatars/preset-ksiezyc.svg';
};
const ROWS = [
  ['g_acc', [['edit', '👤', 'r_edit', 'h_edit'], ['pub', '🌐', 'r_pub', 'h_pub', 'toggle'], ['plan', '💎', 'r_plan'], ['pw', '🔑', 'r_pw', 'h_pw']]],
  ['g_cont', [['wall', '🧱', 'r_wall'], ['photos', '🖼️', 'r_photos'], ['add', '📷', 'r_add', 'h_add'], ['agents', '✨', 'r_agents', '', 'link:/agentka.html?id=me'], ['gen', '🎬', 'r_gen', 'h_gen']]],
  ['g_soc', [['friends', '🤝', 'r_friends', '', 'link:' + FRIENDS], ['inbox', '✉️', 'r_inbox', '', 'link:' + INBOX], ['battles', '⚔️', 'r_battles', 'h_battles', 'link:/bitwy.html']]],
  ['g_not', [['n_battles', '🏆', 'n_battles', '', 'ntoggle'], ['n_friends', '🤝', 'n_friends', '', 'ntoggle'], ['n_messages', '💬', 'n_messages', '', 'ntoggle'], ['n_updates', '🆕', 'n_updates', '', 'ntoggle']]],
  ['g_priv', [['hide', '🙈', 'r_hide', '', 'toggle'], ['invite', '📨', 'r_invite'], ['online', '🟢', 'r_online'], ['blocked', '⛔', 'r_blocked', '', 'link:' + PRIV], ['export', '⬇️', 'r_export', '', 'link:/api/account/export']]],
  ['g_more', [['bubbles', '💭', 'r_bubbles', 'h_bubbles', 'toggle'], ['lang', '🌍', 'r_lang'], ['help', '🛟', 'r_help', '', 'link:/problemy.html'], ['modmsg', '💬', 'r_mod', 'h_mod', 'link:/ustawienia.html?pomoc=formularz'], ['terms', '📜', 'r_terms', '', 'link:/regulamin.html'], ['logout', '🚪', 'r_logout']]],
  ['', [['del', '🗑️', 'r_del', '', 'danger']]],
];
function rowHTML([id, ic, k, h, kind]){
  kind = kind || ''; const link = kind.startsWith('link:') ? kind.slice(5) : '';
  const tog = kind === 'toggle' || kind === 'ntoggle';
  let on = false, sub = h ? T(h) : '';
  if (id === 'pub') on = !!P.profile.public;
  if (id === 'hide') on = !!P.profile.hide_rank;
  if (id === 'bubbles') on = P.settings.bubbles !== false;
  if (kind === 'ntoggle') on = id === 'n_battles' && FP.battles !== undefined ? FP.battles : !!(P.settings.notif || {})[id.slice(2)];
  if (id === 'gen' && !(P.caps.gen > 0)) sub = `<span class="st-lockb">${esc(T('gen_lock'))}</span>`;
  if (id === 'plan') sub = esc(F('plan_now', {p: P.plan_name}));
  if (id === 'invite') sub = esc(T(FP.invites === 'none' ? 'inv_no' : 'inv_all'));
  if (id === 'online') sub = esc(T('on_' + (FP.online || 'close')));
  const inner = `<span class="st-ic" aria-hidden="true">${ic}</span><span class="st-tx"><b>${esc(T(k))}</b>${sub ? `<small>${sub.startsWith('<span') ? sub : esc(sub)}</small>` : ''}</span>` +
    (id === 'inbox' ? '<span class="st-badge" id="stUnread" hidden></span>' : '') + (tog ? '<span class="sw" aria-hidden="true"></span>' : '<span class="st-chev" aria-hidden="true">›</span>');
  const cls = 'st-row' + (kind === 'danger' ? ' danger' : '');
  const kw = esc((T(k) + ' ' + (h ? T(h) : '')).toLowerCase());
  if (link) return `<a class="${cls}" data-id="${id}" data-kw="${kw}" href="${link}"${id === 'export' ? ' download' : ''}>${inner}</a>`;
  if (tog) return `<button type="button" class="${cls}" role="switch" aria-checked="${on}" data-id="${id}" data-kind="${kind}" data-kw="${kw}">${inner}</button>`;
  return `<button type="button" class="${cls}" data-id="${id}" data-kw="${kw}" aria-expanded="false" aria-controls="stSheet">${inner}</button>`;
}
// O mnie: w nagłówku tylko to, co właściciel sam pokazał (małym drukiem)
function identLine(p){
  const x = [];
  if (p.show_gender && p.gender && p.gender !== 'na') x.push(p.gender === 'other' && p.gender_x ? p.gender_x : T('g_' + p.gender));
  if (p.show_pron && p.pron) x.push(p.pron === 'custom' ? p.pron_x : T('p_' + p.pron));
  if (p.show_age && p.age) x.push(F('id_age', {n: p.age}));
  return x.filter(Boolean).length ? `<div class="st-id">${x.filter(Boolean).map(esc).join(' · ')}</div>` : '';
}
function draw(){
  const pr = P.profile, c = P.completion || {pct: 0};
  const tier = P.tier ? ` nk-${P.tier}` : '';
  $('#stApp').removeAttribute('aria-busy'); $('#stApp').innerHTML = `
  <section class="st-head" id="stHead">
    <img class="st-av" src="${esc(avatarURL())}" alt="" width="72" height="72">
    <div class="st-who"><div class="st-nick nk${tier}">${esc(pr.nick || '—')}</div>
${identLine(pr)}
            <span class="st-plan ${esc(P.plan)}">${esc(P.plan_name)}</span>${P.partner ? ' <span class="st-tag pt-mark">💖</span>' : ''}
      <div class="st-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${c.pct}" aria-label="${esc(F('compl', {p: c.pct}))}"><i style="width:${c.pct}%"></i></div>
      <div class="st-bl">${esc(F('compl', {p: c.pct}))} · ${esc(T('compl_h'))}</div>
      <button type="button" class="st-btn st-tourb" id="stTourB">🌙 ${esc(T('tour'))}</button>
    </div>
  </section>
  <input type="search" class="st-search" id="stQ" placeholder="${esc(T('search'))}" aria-label="${esc(T('search'))}">
  ${ROWS.map(([g, rows]) => `<section class="st-g" data-g="${g}">${g ? `<h2>${esc(T(g))}</h2>` : ''}<div class="st-list">${rows.map(rowHTML).join('')}</div></section>`).join('')}
  <p class="hint" id="stNores" hidden>${esc(T('nores'))}</p>
  <div id="stSheet" class="st-sheet" hidden tabindex="-1"></div>`;
  $('#stQ').oninput = e => {
    const q = e.target.value.trim().toLowerCase(); let any = false;
    $$('.st-row').forEach(r => { const hit = !q || r.dataset.kw.includes(q); r.hidden = !hit; any = any || hit; });
    $$('.st-g').forEach(g => { g.hidden = !g.querySelector('.st-row:not([hidden])'); });
    $('#stNores').hidden = any;
  };
  $$('.st-row').forEach(r => r.addEventListener('click', e => onRow(r, e)));
  $('#stTourB').onclick = () => tour(0);
  unread();
  if (pr.nick && !pr.tour_done && !sessionStorage.getItem('st.tour')) setTimeout(() => tour(0), 500);
  if (!pr.nick) sheet('edit');
  if (P.settings.delete_at) delBanner();
  const h = (location.hash || '').slice(1); if (h && SHEETS[h] && !open) sheet(h);
}
async function unread(){
  try { const r = await fetch('/api/inbox/unread', {credentials: 'same-origin'}); if (!r.ok) return; const j = await r.json(); const n = j.total ?? j.unread ?? 0;
    if (j.available === false){ ['friends', 'inbox'].forEach(id => { const x = $(`.st-row[data-id=${id}]`); if (x) x.remove(); }); return; }
    const b = $('#stUnread'); if (b && n > 0){ b.hidden = false; b.textContent = n > 99 ? '99+' : n; b.setAttribute('aria-label', n); } } catch(e){}
}
async function save(d, quiet){
  try { const r = await api('/api/me/profile', d); P.profile = r.profile; if (!quiet) toast(T('saved'), '💚'); return true; }
  catch(e){ toast(e.message, '⚠️'); return false; }
}
async function saveSet(d){ try { const r = await api('/api/me/settings', d, true); Object.assign(P.settings, r); toast(T('saved'), '💚'); return true; } catch(e){ toast(e.message, '⚠️'); return false; } }
async function onRow(r, e){
  const id = r.dataset.id, kind = r.dataset.kind;
  if (kind === 'toggle' || kind === 'ntoggle'){
    const on = r.getAttribute('aria-checked') !== 'true';
    if (id === 'n_battles'){ try { await api('/api/friends/prefs', {battles: on, lang: lang()}, true); } catch(e){} }  // wyniki bitew: ta sama preferencja co w Znajomych/Skrzynce
    if (id === 'bubbles'){ try { localStorage.setItem('luna.dymki', on ? '1' : '0'); } catch(e){}  // Dymki Luny: localStorage + konto
      if (await saveSet({bubbles: on})) r.setAttribute('aria-checked', on); return; }
    const ok = kind === 'ntoggle' ? await saveSet({notif: {[id.slice(2)]: on}}) : await save(id === 'pub' ? {public: on} : {hide_rank: on});
    if (ok) r.setAttribute('aria-checked', on); return;
  }
  if (r.tagName === 'A') return;
  if (id === 'logout'){ try { await api('/api/account/logout', {}, true); } catch(e){} location.href = '/app'; return; }
  sheet(open === id ? '' : id);
}
function sheet(id){
  open = id; const S = $('#stSheet');
  $$('.st-row[aria-expanded]').forEach(b => b.setAttribute('aria-expanded', b.dataset.id === id));
  if (!id){ S.hidden = true; return; }
  const fn = SHEETS[id]; if (!fn){ S.hidden = true; return; }
  S.hidden = false; S.innerHTML = fn();
  const bk = document.createElement('div'); bk.className = 'st-btns'; bk.innerHTML = `<button type="button" data-back>${esc(T('back'))}</button>`; S.appendChild(bk);
  S.querySelector('[data-back]').onclick = () => { sheet(''); $(`.st-row[data-id="${id}"]`)?.focus(); };
  (BIND[id] || (() => {}))(S);
  S.focus({preventScroll: true}); S.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
}
const chk = (n, k) => `<label class="st-chk"><input type="checkbox" name="${n}"> <span>${esc(T(k))}</span></label>`;
const SHEETS = {
  edit: () => { const p = P.profile; return `<h2>${esc(T('r_edit'))}</h2>
    <label for="eNick">${esc(T('f_nick'))}</label><input type="text" id="eNick" maxlength="24" minlength="2" required autocomplete="nickname" value="${esc(p.nick)}">
    <label>${esc(T('f_av'))}</label><p class="hint">${esc(T('f_av_h'))}</p>
    <div class="st-avs" role="group" aria-label="${esc(T('f_av'))}">${P.presets.map(k => `<button type="button" data-av="preset:${k}" aria-pressed="${p.avatar === 'preset:' + k}" aria-label="${k}"><img src="/avatars/preset-${k}.svg" alt="" width="60" height="60"></button>`).join('')}</div>
    <div class="st-btns"><label class="st-btn" style="margin:0">${esc(T('f_av_up'))}<input type="file" id="eAv" accept="image/jpeg,image/png,image/webp" hidden></label>
    ${P.caps.gen > 0 && P.agent && P.agent.own ? `<button type="button" id="eGen">${esc(T('f_av_gen'))}</button>` : ''}</div>
    ${p.avatar.startsWith('up:') ? `<p class="hint">${esc(T('av_pending'))}</p>` : ''}
    <label for="eBio">${esc(T('f_bio'))}</label><textarea id="eBio" maxlength="200">${esc(p.bio)}</textarea>
    <label for="eInt">${esc(T('f_int'))}</label><input type="text" id="eInt" value="${esc(p.interests.join(', '))}">
    <label for="eLinks">${esc(T('f_links'))}</label><textarea id="eLinks">${esc(p.links.join('\n'))}</textarea>
    <p class="hint" style="margin-top:12px">${esc(T('f_show'))}</p>
    <label class="st-chk"><input type="checkbox" id="sBio" ${p.show_bio ? 'checked' : ''}> <span>${esc(T('f_bio'))}</span></label>
    <label class="st-chk"><input type="checkbox" id="sInt" ${p.show_interests ? 'checked' : ''}> <span>${esc(T('f_int'))}</span></label>
    <label class="st-chk"><input type="checkbox" id="sLinks" ${p.show_links ? 'checked' : ''}> <span>${esc(T('f_links'))}</span></label>
    <fieldset class="st-about"><legend>${esc(T('f_about'))}</legend><p class="hint">${esc(T('f_about_h'))}</p>
    <label for="eAge">${esc(T('f_age'))}</label><input type="number" id="eAge" min="18" max="99" step="1" inputmode="numeric" value="${p.age || ''}" aria-describedby="eAgeH"><p class="hint" id="eAgeH">${esc(T('f_age_h'))}</p>
    <label class="st-chk"><input type="checkbox" id="sAge" ${p.show_age ? 'checked' : ''}> <span>${esc(T('f_showin'))}: ${esc(T('f_age'))}</span></label>
    <label for="eG">${esc(T('f_gender'))}</label><select id="eG"><option value="">${esc(T('g_none'))}</option>${['f', 'm', 'nb', 'trans', 'other', 'na'].map(v => `<option value="${v}" ${p.gender === v ? 'selected' : ''}>${esc(T('g_' + v))}</option>`).join('')}</select>
    <div id="eGxW" ${p.gender === 'other' ? '' : 'hidden'}><label for="eGx">${esc(T('f_gx'))}</label><input type="text" id="eGx" maxlength="30" value="${esc(p.gender_x || '')}"></div>
    <label class="st-chk"><input type="checkbox" id="sG" ${p.show_gender ? 'checked' : ''}> <span>${esc(T('f_showin'))}: ${esc(T('f_gender'))}</span></label>
    <label for="eP">${esc(T('f_pron'))}</label><select id="eP"><option value="">${esc(T('g_none'))}</option>${['she', 'he', 'they', 'custom'].map(v => `<option value="${v}" ${p.pron === v ? 'selected' : ''}>${esc(T('p_' + v))}</option>`).join('')}</select>
    <div id="ePxW" ${p.pron === 'custom' ? '' : 'hidden'}><label for="ePx">${esc(T('f_px'))}</label><input type="text" id="ePx" maxlength="30" value="${esc(p.pron_x || '')}"></div>
    <label class="st-chk"><input type="checkbox" id="sP" ${p.show_pron ? 'checked' : ''}> <span>${esc(T('f_showin'))}: ${esc(T('f_pron'))}</span></label></fieldset>
    <div class="st-btns"><button type="button" class="primary" id="eSave">${esc(T('save'))}</button></div>`; },
  plan: () => { const c = P.caps; return `<h2>${esc(F('plan_now', {p: P.plan_name}))}</h2>
    <ul><li>${esc(F('q_img', {n: c.img}))}</li><li>${esc(F('q_vid', {n: c.video}))}</li><li>${c.gen ? esc(F('q_gen', {n: c.gen})) : esc(T('gen_lock'))}</li></ul>
    ${P.partner ? `<p class="hint">${esc(T('partner'))}</p>` : ''}
    <label for="qSel">${esc(T('q_sel'))}</label><select id="qSel"><option value="auto">${esc(T('q_auto'))}</option>${[480, 720, 1080].map(v => `<option value="${v}" ${v > c.video ? 'disabled' : ''}>${v}p${v > c.video ? ' 🔒' : ''}</option>`).join('')}</select>
    ${c.video < 1080 ? `<p class="st-lockb">${esc(T('q_more'))}</p>` : ''}
    <div class="st-btns"><a class="st-btn primary" href="/app#plany">${esc(T('plans_b'))}</a></div>`; },
  pw: () => `<h2>${esc(T('r_pw'))}</h2><p class="hint">${esc(T('h_pw'))}</p><p>✉️ ${esc((ME && ME.email || '').replace(/^(.).*?(.?)@/, '$1•••$2@'))}</p>
    <div class="st-btns"><a class="st-btn" href="/app#konto">${esc(T('r_pw'))}</a></div>`,
  wall: () => `<h2>${esc(T('r_wall'))}</h2><div id="mPosts">…</div>`,
  photos: () => `<h2>${esc(T('r_photos'))}</h2><div class="st-grid" id="mPhotos">…</div>`,
  add: () => `<h2>${esc(T('r_add'))}</h2><p class="hint">${esc(T('h_add'))}</p>
    <input type="file" id="aFile" accept="image/jpeg,image/png,image/webp" aria-label="${esc(T('r_add'))}">
    <label for="aText">${esc(T('add_text'))}</label><textarea id="aText" maxlength="500"></textarea>
    <p class="hint">${esc(T('add_decl'))}</p>${chk('own', 'd_own')}${chk('no_nudity', 'd_nud')}${chk('no_minors', 'd_min')}${chk('consent', 'd_con')}${chk('no_brands', 'd_brand')}
    <div class="st-btns"><button type="button" class="primary" id="aGo">${esc(T('add_go'))}</button></div>`,
  gen: () => `<h2>${esc(T('r_gen'))}</h2><div id="gWrap"><div class="skel skel-l" style="height:120px;border-radius:20px"></div></div>`,
  invite: () => `<h2>${esc(T('r_invite'))}</h2>${['all', 'none'].map(v => `<label class="st-chk"><input type="radio" name="inv" value="${v}" ${(FP.invites || 'all') === v ? 'checked' : ''}> <span>${esc(T(v === 'all' ? 'inv_all' : 'inv_no'))}</span></label>`).join('')}`,
  online: () => `<h2>${esc(T('r_online'))}</h2>${['all', 'close', 'nobody'].map(v => `<label class="st-chk"><input type="radio" name="onl" value="${v}" ${(FP.online || 'close') === v ? 'checked' : ''}> <span>${esc(T('on_' + v))}</span></label>`).join('')}<p class="hint">${esc(T('on_hint'))}</p>
    <div class="st-btns"><a class="st-btn" href="/znajomi.html">☆ ${esc(T('on_star'))}</a></div>`,
  blocked: () => `<h2>${esc(T('r_blocked'))}</h2><div id="bList">${P.settings.blocked.length ? P.settings.blocked.map(b => `<div class="st-post"><p>${esc(b.nick)}</p><button type="button" class="st-btn" data-unb="${esc(b.nick)}">${esc(T('unblk'))}</button></div>`).join('') : `<p class="hint">${esc(T('blk_none'))}</p>`}</div>
    <label for="bNick">${esc(T('blk_ph'))}</label><input type="text" id="bNick" maxlength="24"><div class="st-btns"><button type="button" id="bGo">${esc(T('blk_b'))}</button></div>`,
  lang: () => `<h2>${esc(T('r_lang'))}</h2>${[['pl', '🇵🇱 Polski'], ['en', '🇬🇧 English'], ['es', '🇪🇸 Español'], ['de', '🇩🇪 Deutsch'], ['uk', '🇺🇦 Українська']].map(([k, n]) => `<label class="st-chk"><input type="radio" name="lg" value="${k}" ${lang() === k ? 'checked' : ''}> <span>${n}</span></label>`).join('')}`,
  del: () => `<h2>${esc(T('r_del'))}</h2><p>${esc(T('del_1'))}</p><div class="st-btns"><button type="button" class="st-btn danger" id="d1">${esc(T('del_next'))}</button></div>
    <div id="d2" hidden><label for="dNick">${esc(T('del_2'))} <b>${esc(P.profile.nick)}</b></label><input type="text" id="dNick" autocomplete="off"><div class="st-btns"><button type="button" class="st-btn danger" id="dGo">${esc(T('del_go'))}</button></div></div>`,
};
const readFile = f => new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = no; r.readAsDataURL(f); });
const BIND = {
  edit: S => {
    let av = null;
    S.querySelectorAll('[data-av]').forEach(b => b.onclick = () => { av = b.dataset.av; S.querySelectorAll('[data-av]').forEach(x => x.setAttribute('aria-pressed', x === b)); });
    const g = S.querySelector('#eGen'); if (g) g.onclick = () => { av = 'gen:' + P.agent.own; toast(T('f_av_gen'), '✨'); };
    S.querySelector('#eAv').onchange = async e => { const f = e.target.files[0]; if (!f) return;
      try { const r = await api('/api/me/avatar', {data: await readFile(f)}); P.profile.avatar = r.avatar; toast(T('av_pending'), '🕊️'); await reload(); sheet('edit'); } catch(err){ toast(err.message, '⚠️'); } };
    S.querySelector('#eG').onchange = e => { S.querySelector('#eGxW').hidden = e.target.value !== 'other'; };
    S.querySelector('#eP').onchange = e => { S.querySelector('#ePxW').hidden = e.target.value !== 'custom'; };
    S.querySelector('#eSave').onclick = async () => {
      const d = {nick: S.querySelector('#eNick').value, bio: S.querySelector('#eBio').value, interests: S.querySelector('#eInt').value.split(',').map(x => x.trim()).filter(Boolean),
        links: S.querySelector('#eLinks').value.split('\n').map(x => x.trim()).filter(Boolean), show_bio: S.querySelector('#sBio').checked, show_interests: S.querySelector('#sInt').checked, show_links: S.querySelector('#sLinks').checked};
      const ag = S.querySelector('#eAge').value.trim();
      if (ag && !(/^\d+$/.test(ag) && +ag >= 18 && +ag <= 99)) { toast(T('age_bad'), '🌙'); S.querySelector('#eAge').focus(); return; }
      Object.assign(d, {age: ag ? +ag : null, gender: S.querySelector('#eG').value, gender_x: S.querySelector('#eGx').value, pron: S.querySelector('#eP').value, pron_x: S.querySelector('#ePx').value,
        show_age: S.querySelector('#sAge').checked, show_gender: S.querySelector('#sG').checked, show_pron: S.querySelector('#sP').checked});
      if (av) d.avatar = av;
      if (await save(d)) { await reload(); }
    };
  },
  plan: S => { const s = S.querySelector('#qSel'); try { s.value = localStorage.getItem('luna.q') || 'auto'; } catch(e){}
    s.onchange = () => { try { localStorage.setItem('luna.q', s.value); } catch(e){} toast(T('saved'), '💚'); }; },
  wall: async S => { const r = await api('/api/me/posts'); const L = r.items || [];
    S.querySelector('#mPosts').innerHTML = L.length ? L.map(p => `<div class="st-post"><p>${esc(p.text)}${p.pending ? ` <span class="st-tag">${esc(T('pending'))}</span>` : ''}</p><button type="button" class="st-btn" data-del="${p.id}">${esc(T('del'))}</button></div>`).join('') : `<p class="hint">${esc(T('empty_posts'))}</p>`;
    bindDel(S, 'wall'); },
  photos: async S => { const r = await api('/api/me/posts'); const L = (r.items || []).filter(p => p.img_kind);
    S.querySelector('#mPhotos').innerHTML = L.length ? L.map(p => `<figure>${p.img ? `<img src="${esc(p.img)}" alt="" loading="lazy" width="200" height="200">` : '<div style="aspect-ratio:1;border-radius:16px;background:#ffffff10"></div>'}<button type="button" data-del="${p.id}">${esc(T('del'))}</button><figcaption>${esc(p.img_kind === 'user' ? T('user_photo') : 'AI')}${p.pending ? ' · ' + esc(T('pending')) : ''}</figcaption></figure>`).join('') : `<p class="hint">${esc(T('empty_photos'))}</p>`;
    bindDel(S, 'photos'); },
  add: S => { S.querySelector('#aGo').onclick = async () => {
    const f = S.querySelector('#aFile').files[0]; if (!f) return toast(T('r_add'), '📷');
    const decl = {}; S.querySelectorAll('.st-chk input').forEach(i => decl[i.name] = i.checked);
    try { await api('/api/wall/post', {text: S.querySelector('#aText').value || '📷', image: await readFile(f), img_kind: 'user', user_decl: decl, lang: lang()});
      toast(T('add_ok'), '🕊️'); sheet('photos'); } catch(e){ toast(e.message, '⚠️'); } }; },
  gen: async S => {
    // Generator z opisu (t429u/t430u): proste wybory → „Stwórz moją agentkę AI” → warianty → wybór → sprawdzenie → profil gotowy. Bez wgrywania zdjęć i bez edytora.
    const W = S.querySelector('#gWrap'); let G, sel = {spec: ['diction']}, pickSet = new Set(), poll = null;
    const steps = n => `<ol class="g-steps" aria-label="${esc(T('r_gen'))}">${T('g_steps').map((x, i) => `<li class="${i + 1 < n ? 'done' : i + 1 === n ? 'cur' : ''}"${i + 1 === n ? ' aria-current="step"' : ''}><span>${i + 1 < n ? '✓' : i + 1}</span>${esc(x)}</li>`).join('')}</ol>`;
    const chips = (k, multi) => `<fieldset class="g-f"><legend>${esc(T('g_' + k))}</legend><div class="g-chips">${G.options[k].map(o => { const on = multi ? (sel[k] || []).includes(o.id) : sel[k] === o.id;
      return `<button type="button" class="g-chip${on ? ' on' : ''}" aria-pressed="${on}" data-k="${k}" data-v="${o.id}"${multi ? ' data-m="1"' : ''}>${esc(o.label)}</button>`; }).join('')}</div></fieldset>`;
    const capsTxt = () => F('g_caps', {px: G.caps.px, s: G.caps.video_s, p: G.caps.video_p, u: G.caps.used, l: G.caps.per_day});
    const vidBox = () => { const im = G.state && G.state.img, v = G.state && G.state.vid;
      if (!im || im.status !== 'done') return `<h3>🎬 ${esc(T('g_vid_h'))}</h3><p class="hint">${esc(T('g_vid_need'))}</p>`;
      let body = `<p class="hint">${esc(F('g_vid_cap', {n: 3, s: G.caps.video_s, p: G.caps.video_p}))}</p>`;
      if (v && v.status === 'waiting' && !v.engine) body += `<p class="g-note">${esc(T('g_vid_wait'))}</p>`;
      else if (v && v.status === 'variants') body += `<div class="g-grid">${v.variants.map(x => `<button type="button" class="g-var" data-vv="${x.id}"><video src="${esc(x.url)}" muted playsinline preload="metadata"></video><span class="ai-badge">AI</span></button>`).join('')}</div>`;
      const busy = v && ['waiting', 'generating', 'checking'].includes(v.status);
      return `<h3>🎬 ${esc(T('g_vid_h'))}</h3>${body}<div class="st-btns"><button type="button" class="primary g-big" id="gVid"${busy ? ' disabled' : ''}>🎬 ${esc(T('g_vid_go'))}</button></div>`; };
    const draw = () => {
      if (G.locked) { W.innerHTML = `<div class="g-teaser">${steps(1)}<p class="st-lockb">${esc(T('gen_lock'))}</p><p class="hint">${esc(T('g_safe'))}</p><div class="st-btns"><a class="st-btn primary" href="/app#plany">${esc(T('plans_b'))}</a></div></div>`; return; }
      const im = G.state && G.state.img, st = im ? im.status : 'new';
      let h = `${G.partner ? `<p class="hint">${esc(T('partner'))}</p>` : ''}`;
      if (!im || st === 'rejected' || st === 'failed' || st === 'new' || st === 'draft'){
        h += steps(1) + (st === 'rejected' ? `<p class="g-note">${esc(T('g_rej'))}</p>` : '') +
          chips('hair') + chips('eyes') + chips('style') + chips('outfit') + chips('personality') + chips('voice') + chips('spec', true) +
          `<label for="gName">${esc(T('g_name'))}</label><input type="text" id="gName" maxlength="24" autocomplete="off">
           <label for="gDesc">${esc(T('g_desc'))}</label><textarea id="gDesc" maxlength="200" rows="2" placeholder="${esc(T('g_desc_ph'))}"></textarea>
           <p class="hint">🛡️ ${esc(T('g_safe'))}</p><p class="hint">${esc(capsTxt())}</p>
           <div class="st-btns"><button type="button" class="primary g-big" id="gGo">✨ ${esc(T('g_go'))}</button></div>`;
      } else if (st === 'waiting' || st === 'generating'){
        h += steps(2) + `<div class="g-wait"><span class="g-orb" aria-hidden="true"></span><p>${esc(st === 'waiting' && !im.engine ? T('g_wait') : T('g_working'))}</p></div><p class="hint">${esc(T('g_purge'))}</p>`;
      } else if (st === 'variants'){
        h += steps(3) + `<p class="hint">${esc(T('g_pick'))}</p><div class="g-grid">${im.variants.map(x => `<button type="button" class="g-var${pickSet.has(x.id) ? ' on' : ''}" aria-pressed="${pickSet.has(x.id)}" data-pv="${x.id}"><img src="${esc(x.url)}" alt="" loading="lazy"><span class="ai-badge">AI</span><i class="g-tick" aria-hidden="true">✓</i></button>`).join('')}</div>
          <div class="st-btns"><button type="button" class="primary g-big" id="gPick"${pickSet.size ? '' : ' disabled'}>${esc(T('g_pick_go'))}</button></div><p class="hint">${esc(T('g_purge'))}</p>`;
      } else if (st === 'checking'){
        h += steps(4) + `<div class="g-wait"><span class="g-orb" aria-hidden="true"></span><p>${esc(T('g_check'))}</p></div>`;
      } else if (st === 'done'){
        h += steps(5) + `<p class="g-ok">${esc(T('g_done'))}</p><div class="st-btns"><a class="st-btn primary" href="/agentka.html?id=me">${esc(T('g_view'))}</a><button type="button" class="st-btn" id="gNew">${esc(T('g_new'))}</button></div>`;
      }
      W.innerHTML = h + (G.state ? vidBox() : '');
      W.querySelectorAll('.g-chip').forEach(b => b.onclick = () => { const k = b.dataset.k, v = b.dataset.v;
        if (b.dataset.m){ const a = sel[k] || []; sel[k] = a.includes(v) ? a.filter(x => x !== v) : (a.length >= 3 ? a : a.concat(v)); } else sel[k] = sel[k] === v ? '' : v;
        const nm = W.querySelector('#gName')?.value, ds = W.querySelector('#gDesc')?.value; draw(); if (nm) W.querySelector('#gName').value = nm; if (ds) W.querySelector('#gDesc').value = ds; W.querySelector(`[data-k="${k}"][data-v="${v}"]`)?.focus(); });
      const go = W.querySelector('#gGo'); if (go) go.onclick = async () => { go.disabled = true; go.classList.add('busy');
        try { const r = await api('/api/agent/gen', Object.assign({}, sel, {name: W.querySelector('#gName').value, desc: W.querySelector('#gDesc').value}), true);
          G.state = G.state || {}; G.state.img = r.job; draw(); watch(); toast(r.job.engine ? T('g_working') : '⏳', '✨'); } catch(e){ toast(e.message, '⚠️'); go.disabled = false; go.classList.remove('busy'); } };
      W.querySelectorAll('[data-pv]').forEach(b => b.onclick = () => { const v = b.dataset.pv; if (pickSet.has(v)) pickSet.delete(v); else if (pickSet.size < 4) pickSet.add(v); draw(); });
      const pk = W.querySelector('#gPick'); if (pk) pk.onclick = async () => { pk.disabled = true;
        try { const r = await api('/api/agent/gen/pick', {job: G.state.img.id, ids: [...pickSet]}, true); G.state.img = r.job; pickSet.clear(); draw(); watch(); } catch(e){ toast(e.message, '⚠️'); pk.disabled = false; } };
      const nw = W.querySelector('#gNew'); if (nw) nw.onclick = () => { G.state.img = null; draw(); };
      const gv = W.querySelector('#gVid'); if (gv) gv.onclick = async () => { gv.disabled = true;
        try { const r = await api('/api/agent/gen/video', {}, true); G.state.vid = r.job; draw(); watch(); } catch(e){ toast(e.message, '⚠️'); gv.disabled = false; } };
    };
    const watch = () => { clearInterval(poll); poll = setInterval(async () => { if (open !== 'gen') return clearInterval(poll);
      const busy = s => s && ['generating', 'checking'].includes(s.status) || (s && s.status === 'waiting' && s.engine);
      if (!busy(G.state.img) && !busy(G.state.vid)) return clearInterval(poll);
      try { const g = await api('/api/agent/gen?lang=' + lang()); const was = G.state.img && G.state.img.status; G = g; draw();
        if (was !== (g.state.img || {}).status && (g.state.img || {}).status === 'variants') toast(T('g_pick'), '🎨'); } catch(e){} }, 4000); };
    try { G = await api('/api/agent/gen?lang=' + lang()); } catch(e){ W.innerHTML = `<p class="hint">${esc(e.message)}</p>`; return; }
    const d = G.state && G.state.img && G.state.img.draft; if (d) sel = Object.assign({spec: ['diction']}, d);
    draw(); watch();
  },
  online: S => S.querySelectorAll('[name=onl]').forEach(i => i.onchange = async () => { try { await api('/api/friends/prefs', {online: i.value}, true); FP.online = i.value; toast(T('saved'), '💚'); } catch(e){ toast(e.message, '⚠️'); } }),
  invite: S => S.querySelectorAll('[name=inv]').forEach(i => i.onchange = async () => { try { await api('/api/friends/prefs', {invites: i.value}, true); FP.invites = i.value; toast(T('saved'), '💚'); } catch(e){ toast(e.message, '⚠️'); } }),
  blocked: S => { S.querySelector('#bGo').onclick = async () => { if (await saveSet({block: S.querySelector('#bNick').value})) sheet('blocked'); };
    S.querySelectorAll('[data-unb]').forEach(b => b.onclick = async () => { if (await saveSet({unblock: b.dataset.unb})) sheet('blocked'); }); },
  lang: S => S.querySelectorAll('[name=lg]').forEach(i => i.onchange = () => { try { localStorage.setItem('luna.lang', i.value); } catch(e){}
    document.cookie = 'luna_lang=' + i.value + ';path=/;max-age=31536000;samesite=lax'; api('/api/me/lang', {lang: i.value}).catch(() => {}); const u = new URL(location.href); u.searchParams.set('lang', i.value); location.href = u; }),
  del: S => { S.querySelector('#d1').onclick = () => { S.querySelector('#d2').hidden = false; S.querySelector('#dNick').focus(); };
    S.querySelector('#dGo').onclick = async () => { try { const r = await api('/api/account/delete-request', {nick: S.querySelector('#dNick').value}, true); P.settings.delete_at = r.delete_at; sheet(''); delBanner(); } catch(e){ toast(e.message, '⚠️'); } }; },
};
function bindDel(S, again){ S.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => { try { await api('/api/wall/delete', {id: b.dataset.del}); sheet(again); } catch(e){ toast(e.message, '⚠️'); } }); }
function delBanner(){
  let b = $('#stDel'); if (!b){ b = document.createElement('div'); b.id = 'stDel'; b.className = 'st-sheet'; b.setAttribute('role', 'alert'); $('#stApp').prepend(b); }
  b.innerHTML = `<p>${esc(F('del_pending', {d: new Date(P.settings.delete_at * 1000).toLocaleDateString(lang())}))}</p><div class="st-btns"><button type="button" class="primary" id="dRe">${esc(T('del_restore'))}</button></div>`;
  b.querySelector('#dRe').onclick = async () => { await api('/api/account/delete-cancel', {}, true); P.settings.delete_at = 0; b.remove(); toast(T('saved'), '💚'); };
}
const STEPS = [['#stHead', 't1'], ['.st-row[data-id=edit]', 't2'], ['.st-row[data-id=plan]', 't3'], ['.st-row[data-id=hide]', 't4']];
function tour(i){
  $$('.st-hl').forEach(e => e.classList.remove('st-hl')); $('#stTour')?.remove();
  if (i >= STEPS.length){ sessionStorage.setItem('st.tour', '1'); save({tour_done: true}, true); return; }
  const el = $(STEPS[i][0]); if (el){ el.classList.add('st-hl'); el.scrollIntoView({block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}); }
  const b = document.createElement('div'); b.id = 'stTour'; b.className = 'st-tour'; b.setAttribute('role', 'dialog'); b.setAttribute('aria-live', 'polite');
  b.innerHTML = `<p>${esc(T(STEPS[i][1]))}</p><div class="st-btns"><button type="button" class="primary" data-n>${esc(T(i === STEPS.length - 1 ? 't_done' : 't_next'))}</button><button type="button" data-s>${esc(T('t_skip'))}</button></div><small>${i + 1} / ${STEPS.length}</small>`;
  document.body.appendChild(b); b.querySelector('[data-n]').onclick = () => tour(i + 1); b.querySelector('[data-s]').onclick = () => tour(STEPS.length); b.querySelector('[data-n]').focus();
}
async function reload(){ P = await api('/api/me/profile'); if (!P.login) draw(); }
(async () => {
  try { const a = await api('/api/account/me'); ME = a.user; CSRF = a.csrf || ''; } catch(e){}
  try { P = await api('/api/me/profile'); } catch(e){ P = {login: true}; }
  try { if (P.settings && P.settings.bubbles !== undefined) localStorage.setItem('luna.dymki', P.settings.bubbles === false ? '0' : '1'); } catch(e){}
  if (P.login || !ME){ $('#stApp').innerHTML = `<div class="st-sheet"><p>${esc(T('login'))}</p><div class="st-btns"><a class="st-btn primary" href="/app#konto">${esc(T('login_b'))}</a></div></div>`; return; }
  try { const f = await api('/api/friends/settings'); FP = {invites: f.keys.invites.value, battles: !!f.keys.battles.value, online: (f.keys.online || {}).value || 'close'}; } catch(e){}
  draw();
  window.addEventListener('luna-lang', () => { if (P && !P.login) draw(); });
})();
})();
