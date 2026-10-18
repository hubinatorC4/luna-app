/* Panel moderatora – wspólny dla strony (__MODE__=web) i aplikacji (app). Tożsamość: „Zespół Luny · Moderator”.
   Bezpieczeństwo: konto z rolą admin (serwer) + 2FA na urządzenie (30 dni) + token w pamięci karty + CSRF + ponowny kod 2FA przy akcjach krytycznych. */
(() => {
const P = '__P__', MODE = document.documentElement.dataset.mode;
const $ = s => document.querySelector(s), main = $('#mpMain'), tabs = $('#mpTabs');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const when = t => t ? new Date(t * 1000).toLocaleString('pl-PL', {day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'}) : '—';
let TOK = '', CSRF = '', ACSRF = '', TAB = 'home', OV = null;
if (MODE === 'app') { $('#mpSwitch').href = P + '/'; $('#mpSwitch').textContent = '🖥️ Wersja na komputer'; }
const toast = (m) => { const t = $('#mpToast'); t.textContent = m; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 3200); };
async function req(path, body, extra){
  const h = {'Content-Type': 'application/json'}; if (TOK) h['X-Admin-Token'] = TOK; if (body) h['X-CSRF-Token'] = (extra && extra.acsrf) ? ACSRF : CSRF;
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers: h, credentials: 'same-origin', body: body ? JSON.stringify(body) : undefined});
  let j = {}; try { j = await r.json(); } catch (e) {}
  if (r.status === 401 && TOK){ TOK = ''; boot(); throw new Error('Sesja wygasła – odświeżam.'); }
  if (!r.ok){ const e = new Error(j.error || ('HTTP ' + r.status)); e.data = j; throw e; }
  return j;
}
function askOtp(){
  return new Promise(res => { const d = $('#mpReauth'), i = $('#mpOtp'); i.value = ''; d.returnValue = ''; d.showModal(); i.focus();
    d.onclose = () => res(d.returnValue === 'ok' ? i.value.trim() : null); });
}
async function act(path, body){   /* akcja panelu; przy „reauth” prosi o kod 2FA i ponawia */
  try { return await req(path, body); }
  catch (e){
    if (e.data && e.data.reauth){ const otp = await askOtp(); if (!otp) throw new Error('Anulowano.'); return await req(path, Object.assign({}, body, {otp})); }
    throw e;
  }
}
/* ---------- wejście: logowanie → 2FA ---------- */
async function boot(){
  tabs.hidden = true; $('#mpLock').hidden = true; main.className = 'mp-main auth';
  let st; try { st = await req('/api/mod/state'); } catch (e){ main.innerHTML = `<p class="mp-hint">⚠️ ${esc(e.message)}</p>`; return; }
  try { const me = await fetch('/api/account/me', {credentials: 'same-origin'}).then(r => r.json()); ACSRF = me.csrf || ''; } catch (e) {}
  if (st.stage === 'login') return loginView();
  if (st.stage === 'denied') { main.innerHTML = '<div class="mp-card mp-auth"><h2>Tu wstęp ma tylko moderator 🛡️</h2><p class="mp-hint">To konto nie ma uprawnień. Wróć na <a href="/">stronę główną</a>.</p></div>'; return; }
  if (st.stage === 'setup') return setupView(st);
  if (st.stage === 'unlock') return unlockView();
  TOK = st.token; CSRF = st.csrf; $('#mpWho').textContent = st.name; $('#mpLock').hidden = false;
  try { sessionStorage.setItem('luna.admin', TOK); } catch (e) {}   /* widok Pomocy na żywo (/admin-support.html) korzysta z tego samego tokenu */
  app();
}
function loginView(){
  main.innerHTML = `<div class="mp-card mp-auth"><h2>Zaloguj się</h2><p class="mp-hint">Zwykłe logowanie: nick moderatora (albo e-mail) i hasło. Potem kod 2FA.</p>
  <label class="mp-l">Nick lub e-mail<input class="mp-in" id="lgU" autocomplete="username" maxlength="254"></label>
  <label class="mp-l">Hasło<input class="mp-in" id="lgP" type="password" autocomplete="current-password" maxlength="128"></label>
  <label class="mp-l" id="lgTw" hidden>Kod 2FA konta<input class="mp-in" id="lgT" inputmode="numeric" maxlength="6" autocomplete="one-time-code"></label>
  <div class="mp-row"><button class="mp-btn primary" id="lgGo" type="button">Zaloguj</button></div><p class="mp-hint" id="lgE" role="alert"></p></div>`;
  const go = async () => { $('#lgE').textContent = '';
    try { const r = await fetch('/api/account/login', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: $('#lgU').value.trim(), password: $('#lgP').value, totp: $('#lgT').value.trim() || undefined})});
      const j = await r.json().catch(() => ({}));
      if (j.totp_required){ $('#lgTw').hidden = false; $('#lgT').focus(); throw new Error(j.error); }
      if (!r.ok) throw new Error(j.error || r.status);
      $('#lgP').value = ''; boot(); } catch (e){ $('#lgE').textContent = '⚠️ ' + e.message; } };
  $('#lgGo').onclick = go; main.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
}
function setupView(st){
  main.innerHTML = `<div class="mp-card mp-auth"><h2>🔐 Pierwsze wejście: włącz 2FA</h2>
  <p>Panel moderatora wymaga drugiego składnika. Zeskanuj kod QR w aplikacji uwierzytelniającej (Google Authenticator, Aegis, 2FAS, Microsoft Authenticator) i wpisz 6 cyfr.</p>
  ${st.persistent ? '' : '<p class="mp-banner warn">Uwaga: serwer nie ma jeszcze bazy danych (DATABASE_URL). Po restarcie konfiguracja 2FA zniknie i trzeba ją powtórzyć – albo poproś o wpisanie klucza jako LUNA_ADMIN_TOTP_SECRET na Renderze.</p>'}
  <div id="suBox"><button class="mp-btn primary" id="suGo" type="button">Pokaż kod QR (tylko raz)</button></div><p class="mp-hint" id="suE" role="alert"></p></div>`;
  $('#suGo').onclick = async () => {
    try { const r = await req('/api/mod/setup/start', {}, {acsrf: 1});
      $('#suBox').innerHTML = `<img class="mp-qr" src="${esc(r.qr)}" alt="Kod QR do aplikacji uwierzytelniającej"><p class="mp-hint">Albo wpisz klucz ręcznie:</p><p class="mp-secret">${esc(r.secret.replace(/(.{4})/g, '$1 ').trim())}</p>
      <label class="mp-l">Kod z aplikacji<input class="mp-in" id="suC" inputmode="numeric" maxlength="6" autocomplete="one-time-code"></label><button class="mp-btn primary" id="suOk" type="button">Włącz 2FA</button>`;
      $('#suOk').onclick = async () => { try { await req('/api/mod/setup/confirm', {code: $('#suC').value.trim()}, {acsrf: 1}); toast('2FA włączone 💚 To urządzenie jest zaufane przez 30 dni.'); boot(); } catch (e){ $('#suE').textContent = '⚠️ ' + e.message; } };
    } catch (e){ $('#suE').textContent = '⚠️ ' + e.message; } };
}
function unlockView(){
  main.innerHTML = `<div class="mp-card mp-auth"><h2>🔐 Kod 2FA</h2><p class="mp-hint">Nowe urządzenie albo minęło 30 dni. Wpisz kod z aplikacji – zapamiętamy to urządzenie na 30 dni.</p>
  <input class="mp-in" id="ulC" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="123456" aria-label="Kod 2FA">
  <div class="mp-row" style="margin-top:10px"><button class="mp-btn primary" id="ulGo" type="button">Odblokuj panel</button></div><p class="mp-hint" id="ulE" role="alert"></p></div>`;
  const go = async () => { try { await req('/api/mod/unlock', {code: $('#ulC').value.trim()}, {acsrf: 1}); boot(); } catch (e){ $('#ulE').textContent = '⚠️ ' + e.message; } };
  $('#ulGo').onclick = go; $('#ulC').onkeydown = e => { if (e.key === 'Enter') go(); }; $('#ulC').focus();
}
$('#mpLock').onclick = async () => { if (!confirm('Zablokować panel na tym urządzeniu? Następne wejście poprosi o kod 2FA.')) return; try { await req('/api/mod/lock', {}); } catch (e) {} TOK = ''; boot(); };
/* ---------- panel ---------- */
const TABS = [['home', '⚡', 'Przełączniki'], ['queue', '🧹', 'Kolejka'], ['users', '👥', 'Użytkownicy'], ['content', '🖼️', 'Treści'], ['msg', '📣', 'Komunikaty'], ['support', '💬', 'Wsparcie'], ['audit', '📜', 'Dziennik']];
function app(){
  main.className = 'mp-main';
  if (MODE === 'web') main.prepend(tabs);
  const list = MODE === 'app' ? TABS.filter(t => ['home', 'queue', 'users', 'content', 'msg'].includes(t[0])) : TABS;
  tabs.innerHTML = list.map(([k, i, l]) => `<button type="button" data-t="${k}"><span class="i" aria-hidden="true">${i}</span><span>${l}</span>${k === 'queue' ? '<span class="n" id="qN" hidden></span>' : ''}</button>`).join('');
  tabs.hidden = false; tabs.querySelectorAll('button').forEach(b => b.onclick = () => show(b.dataset.t)); show(TAB);
}
function sec(html){ main.querySelectorAll('.mp-sec').forEach(s => s.remove()); main.insertAdjacentHTML('beforeend', `<section class="mp-sec">${html}</section>`); return main.querySelector('.mp-sec'); }
async function show(t){
  TAB = t; tabs.querySelectorAll('button').forEach(b => b.setAttribute('aria-current', b.dataset.t === t));
  try { await ({home, queue, users, content, msg, support, audit})[t](); } catch (e){ sec(`<p class="mp-hint">⚠️ ${esc(e.message)}</p>`); }
}
/* przełączniki + statystyki */
async function home(){
  OV = await req('/api/mod/overview'); const S = OV.switches, st = OV.stats;
  const down = Object.keys(OV.scopes).filter(k => !S[k].on);
  const sw = (id, on, title, sub, big) => `<button type="button" class="sw${big ? ' big' : ''}${on ? '' : ' off'}" role="switch" aria-checked="${on}" data-sw="${id}"><span><b>${title}</b><small>${sub}</small></span><span class="t" aria-hidden="true"></span></button>`;
  const until = S.until ? new Date(S.until * 1000) : null;
  const loc = until ? new Date(until.getTime() - until.getTimezoneOffset() * 60000).toISOString().slice(0, 16) : '';
  const s = sec(`<h2>⚡ Przełączniki systemu</h2>
  ${down.length ? `<p class="mp-banner">🛠️ Tryb serwisowy włączony: ${down.map(k => OV.scopes[k]).join(', ')}. Użytkownicy widzą „Luna poprawia makijaż, zaraz wracamy 💄”. Ty widzisz wszystko normalnie.</p>` : '<p class="mp-hint">Wszystko działa 💚 Wyłączenie = tryb serwisowy (kod 503), a nie zatrzymanie serwera. Panel zawsze działa.</p>'}
  ${OV.persistent ? '' : '<p class="mp-banner warn">Bez bazy danych (DATABASE_URL) ustawienia i dane wracają do domyślnych po restarcie serwera.</p>'}
  <div class="mp-card"><div class="mp-grid">
    ${sw('site', S.site.on, '🌐 Strona', S.site.on ? 'Włączona – działa dla wszystkich' : 'Wyłączona – przerwa techniczna', 1)}
    ${sw('app', S.app.on, '📱 Aplikacja', S.app.on ? 'Włączona (Android / zainstalowana)' : 'Wyłączona – przerwa techniczna', 1)}
    ${sw('system', S.system.on, '🧯 Cały system', S.system.on ? 'Włączony' : 'Wyłączony wszędzie', 1)}</div>
    <label class="mp-l">Komunikat na stronie przerwy (opcjonalnie)<input class="mp-in" id="swMsg" maxlength="300" value="${esc(S.msg)}" placeholder="Dopracowujemy kilka rzeczy, żeby było jeszcze piękniej…"></label>
    <label class="mp-l">Planowany powrót (opcjonalnie – samo się włączy)<input class="mp-in" id="swUntil" type="datetime-local" value="${loc}"></label>
    <div class="mp-row"><button class="mp-btn" id="swSave" type="button">Zapisz komunikat i godzinę</button></div></div>
  <h3>🎛️ Funkcje</h3><div class="mp-card"><div class="mp-grid">${Object.entries(OV.features).map(([k, l]) => sw('f:' + k, S.features[k], l, S.features[k] ? 'Działa' : 'Wstrzymane – użytkownicy dostają uprzejmy komunikat')).join('')}</div></div>
  <h3>📊 Statystyki (tylko prawdziwe liczby)</h3><div class="mp-stat">
    <div><b>${st.users}</b><small>użytkowników</small></div><div><b>${st.signups_today}</b><small>rejestracji dziś</small></div>
    <div><b>${st.active_battles ?? '—'}</b><small>aktywnych bitew</small></div><div><b>${st.open_reports ?? '—'}</b><small>w kolejce moderacji</small></div>
    <div><b>${st.tickets ?? '—'}</b><small>otwartych zgłoszeń pomocy</small></div></div>`);
  const qn = $('#qN'); if (qn && st.open_reports){ qn.textContent = st.open_reports; qn.hidden = false; }
  s.querySelectorAll('[data-sw]').forEach(b => b.onclick = async () => {
    const id = b.dataset.sw, on = b.getAttribute('aria-checked') !== 'true';
    const body = id.startsWith('f:') ? {features: {[id.slice(2)]: on}} : {scopes: {[id]: on}};
    if (!id.startsWith('f:') && !on && !confirm(`Wyłączyć: ${b.querySelector('b').textContent}? Użytkownicy zobaczą stronę przerwy technicznej.`)) return;
    try { await act('/api/mod/switches', body); toast(on ? 'Włączone ✅' : 'Wyłączone – tryb serwisowy 🛠️'); home(); } catch (e){ toast('⚠️ ' + e.message); }
  });
  $('#swSave').onclick = async () => { const v = $('#swUntil').value; try { await act('/api/mod/switches', {msg: $('#swMsg').value, until: v ? Math.floor(new Date(v).getTime() / 1000) : 0}); toast('Zapisano 💚'); home(); } catch (e){ toast('⚠️ ' + e.message); } };
}
/* kolejka */
const ACT = {approve: ['✅ Zatwierdź', 'ok'], dismiss: ['👌 Odrzuć zgłoszenie', 'ok'], remove: ['🗑️ Usuń', 'bad'], warn: ['⚠️ Ostrzeż', ''], strike: ['🟥 Strike', 'bad'], temp_block: ['⏸️ Blokada 7 dni', 'bad'], ban: ['⛔ Ban', 'bad']};
async function queue(){
  const d = await req('/api/mod/queue'); const qn = $('#qN'); if (qn){ qn.textContent = d.items.length; qn.hidden = !d.items.length; }
  const s = sec(`<h2>🧹 Kolejka moderacji</h2><p class="mp-hint">Zgłoszenia, wpisy i zdjęcia na ścianie, komentarze, awatary, agentki, czat bitew, filmy i casting – w jednym miejscu. Powód trafia do Skrzynki użytkownika.</p>
  <label class="mp-l">Powód (wysyłany użytkownikowi)<input class="mp-in" id="qR" maxlength="300" placeholder="np. nękanie innych użytkowników"></label>
  <div id="qL">${d.items.length ? d.items.map(it => `<div class="mp-item" data-src="${esc(it.src)}" data-id="${esc(it.id)}" data-bid="${esc(it.bid || '')}" data-short="${esc(it.short || '')}">
    ${it.img && !it.link ? `<img class="th" src="${esc(it.img)}" alt="" loading="lazy">` : '<span class="th" aria-hidden="true" style="font-size:34px">' + (it.src === 'cmt' ? '💬' : it.src === 'case' ? '🚩' : it.src === 'casting' ? '🎭' : it.src === 'video' ? '🎬' : '📝') + '</span>'}
    <div><div class="k">${esc(it.kind)}</div><p>${esc(it.text) || '<i>(bez tekstu)</i>'}</p><div class="m">${esc(it.who || '')} · ${when(it.t)}${it.n ? ` · zgłoszeń: ${it.n}` : ''}${it.standing ? ` · strike: ${it.standing.strikes}/${it.standing.max}${it.standing.banned ? ' · ⛔ ban' : ''}` : ''}${it.link ? ` · <a href="${esc(it.img)}" target="_blank" rel="noopener">podgląd ↗</a>` : ''}</div></div>
    <div class="acts">${it.acts.map(a => `<button type="button" class="mp-btn ${ACT[a] ? ACT[a][1] : ''}" data-a="${a}">${ACT[a] ? ACT[a][0] : a}</button>`).join('')}</div></div>`).join('') : '<div class="mp-card"><p>Pusto! ✨ Luna może iść na kawę – nic nie czeka na decyzję.</p></div>'}</div>`);
  s.querySelectorAll('.mp-item [data-a]').forEach(b => b.onclick = async () => {
    const it = b.closest('.mp-item'), a = b.dataset.a;
    if (['ban', 'remove', 'strike', 'temp_block'].includes(a) && !confirm(`Na pewno: ${b.textContent}?`)) return;
    try { await act('/api/mod/queue', {src: it.dataset.src, id: it.dataset.id, bid: it.dataset.bid, short: it.dataset.short, action: a, reason: $('#qR').value, days: 7}); toast('Gotowe ✅'); queue(); } catch (e){ toast('⚠️ ' + e.message); }
  });
}
/* użytkownicy */
async function users(q){
  const d = await req('/api/mod/users?q=' + encodeURIComponent(q || ''));
  const s = sec(`<h2>👥 Użytkownicy</h2><div class="mp-row"><input class="mp-in" id="uQ" placeholder="Szukaj po nicku" value="${esc(q || '')}" style="flex:1"><button class="mp-btn" id="uGo" type="button">Szukaj</button></div>
  <label class="mp-l">Powód (do Skrzynki użytkownika)<input class="mp-in" id="uR" maxlength="300"></label>
  <div>${d.items.map(u => `<div class="mp-item" data-uid="${esc(u.uid)}"><span class="th" aria-hidden="true" style="font-size:30px">${u.admin ? '🛡️' : '👤'}</span>
   <div><div class="k">${esc(u.nick || '(bez nicku)')} ${u.admin ? '<span class="mod-badge">🛡️ Moderator</span>' : ''}</div>
   <p><span class="mp-chip">${esc(u.plan)}${u.until ? ' do ' + when(u.until) : ''}</span>${u.partner ? '<span class="mp-chip">💖 współpracująca</span>' : ''}<span class="mp-chip ${u.standing.strikes ? 'bad' : ''}">strike ${u.standing.strikes}/${u.standing.max}</span>${u.standing.banned ? '<span class="mp-chip bad">⛔ ban</span>' : ''}${u.standing.block_until ? `<span class="mp-chip bad">⏸️ do ${when(u.standing.block_until)}</span>` : ''}${u.standing.warns ? `<span class="mp-chip">ostrzeżeń ${u.standing.warns}</span>` : ''}</p>
   <div class="m">od ${when(u.created)}</div></div>
   ${u.admin ? '' : `<div class="acts"><button type="button" class="mp-btn" data-a="warn">⚠️ Ostrzeż</button><button type="button" class="mp-btn bad" data-a="strike">🟥 Strike</button><button type="button" class="mp-btn bad" data-a="temp_block">⏸️ Blokada 7 dni</button>
   ${u.standing.banned || u.standing.block_until ? '<button type="button" class="mp-btn ok" data-a="unban">🔓 Odblokuj</button>' : '<button type="button" class="mp-btn bad" data-a="ban">⛔ Ban</button>'}${u.standing.strikes ? '<button type="button" class="mp-btn" data-a="unstrike">↩️ Cofnij strike</button>' : ''}
   <button type="button" class="mp-btn" data-a="${u.partner ? 'partner_off' : 'partner_on'}">${u.partner ? '💔 Odbierz współpracę' : '💖 Nadaj „współpracującą”'}</button>
   <select class="mp-in" data-plan style="width:auto"><option value="">Plan testowy…</option><option value="premium">Premium 30 dni</option><option value="pro">Pro 30 dni</option><option value="none">Zdejmij nadany plan</option></select></div>`}</div>`).join('') || '<p class="mp-hint">Nikogo nie znaleziono.</p>'}</div>`);
  const go = () => users($('#uQ').value.trim()); $('#uGo').onclick = go; $('#uQ').onkeydown = e => { if (e.key === 'Enter') go(); };
  const run = async (uid, body, label) => { try { await act('/api/mod/user', Object.assign({uid, reason: $('#uR').value}, body)); toast(label || 'Gotowe ✅'); users($('#uQ').value.trim()); } catch (e){ toast('⚠️ ' + e.message); } };
  s.querySelectorAll('[data-uid] [data-a]').forEach(b => b.onclick = () => { const a = b.dataset.a; if (['ban', 'strike', 'temp_block'].includes(a) && !confirm(`Na pewno: ${b.textContent}?`)) return; run(b.closest('[data-uid]').dataset.uid, {action: a, days: 7}); });
  s.querySelectorAll('[data-plan]').forEach(sl => sl.onchange = () => { if (sl.value) run(sl.closest('[data-uid]').dataset.uid, {action: 'plan', plan: sl.value, months: 1}, 'Plan zmieniony ✅'); });
}
/* treści */
async function content(q){
  const d = await req('/api/mod/content?q=' + encodeURIComponent(q || ''));
  const s = sec(`<h2>🖼️ Treści</h2><div class="mp-row"><input class="mp-in" id="cQ" placeholder="Szukaj wpisu lub agentki" value="${esc(q || '')}" style="flex:1"><button class="mp-btn" id="cGo" type="button">Szukaj</button></div><div style="margin-top:12px">
  ${d.items.map(c => `<div class="mp-item" data-type="${c.type}" data-id="${esc(c.id)}"><span class="th" aria-hidden="true" style="font-size:30px">${c.type === 'agent' ? '✨' : '📝'}</span><div><div class="k">${c.type === 'agent' ? 'Agentka' : 'Wpis'} · ${esc(c.title)} ${c.hidden ? '<span class="mp-chip bad">ukryte</span>' : ''}${c.pinned ? '<span class="mp-chip ok">📌 przypięte</span>' : ''}</div><p>${esc(c.text)}</p><div class="m">${when(c.t)}</div></div>
   <div class="acts"><button type="button" class="mp-btn" data-a="${c.hidden ? 'unhide' : 'hide'}">${c.hidden ? '👁️ Pokaż' : '🙈 Ukryj'}</button>${c.type === 'post' ? `<button type="button" class="mp-btn blue" data-a="${c.pinned ? 'unpin' : 'pin'}">${c.pinned ? '📍 Odepnij' : '📌 Przypnij na ścianie'}</button>` : ''}</div></div>`).join('') || '<p class="mp-hint">Brak treści.</p>'}</div>`);
  const go = () => content($('#cQ').value.trim()); $('#cGo').onclick = go; $('#cQ').onkeydown = e => { if (e.key === 'Enter') go(); };
  s.querySelectorAll('[data-type] [data-a]').forEach(b => b.onclick = async () => { const it = b.closest('[data-type]'); try { await act('/api/mod/content', {type: it.dataset.type, id: it.dataset.id, action: b.dataset.a}); toast('Gotowe ✅'); content($('#cQ').value.trim()); } catch (e){ toast('⚠️ ' + e.message); } });
}
/* komunikaty */
async function msg(){
  const ov = OV || await req('/api/mod/overview'); const a = ov.announcement; const b = await req('/api/mod/broadcasts');
  const s = sec(`<h2>📣 Komunikaty</h2>
  <div class="mp-card"><h3 style="margin-top:0">Ogłoszenie na stronie / „Co nowego”</h3><p class="mp-hint">Mały pasek pod nagłówkiem na stronie i w aplikacji, z krzyżykiem do zamknięcia.</p>
   <label class="mp-l">Tytuł<input class="mp-in" id="aT" maxlength="60" value="${esc(a.title)}"></label><label class="mp-l">Treść<textarea class="mp-in" id="aX" maxlength="400">${esc(a.text)}</textarea></label>
   <div class="mp-row"><button type="button" class="sw" role="switch" aria-checked="${a.on}" id="aOn" style="width:auto"><span><b>Pokazuj</b></span><span class="t" aria-hidden="true"></span></button><button class="mp-btn primary" id="aSave" type="button">Zapisz ogłoszenie</button></div></div>
  <div class="mp-card"><h3 style="margin-top:0">Wiadomość do Skrzynki wszystkich użytkowników</h3><p class="mp-hint">Podpis: „Zespół Luny · Moderator”. Przed wysłaniem poprosimy o potwierdzenie i kod 2FA.</p>
   <label class="mp-l">Tytuł<input class="mp-in" id="bT" maxlength="120"></label><label class="mp-l">Treść<textarea class="mp-in" id="bX" maxlength="1800"></textarea></label>
   <label class="mp-l"><input type="checkbox" id="bI"> Kategoria „Ważne” (zamiast „Aktualizacje”)</label><button class="mp-btn primary" id="bGo" type="button">Wyślij do wszystkich…</button>
   <h3>Ostatnio wysłane</h3><div class="mp-log">${b.items.map(x => `<div><time>${when(x.t)}</time>${esc(x.title)} <span class="mp-chip">${esc(x.cat)}</span></div>`).join('') || '<p class="mp-hint">Jeszcze nic.</p>'}</div></div>`);
  $('#aOn').onclick = e => { const t = e.currentTarget; t.setAttribute('aria-checked', t.getAttribute('aria-checked') !== 'true'); };
  $('#aSave').onclick = async () => { try { await act('/api/mod/announce', {on: $('#aOn').getAttribute('aria-checked') === 'true', title: $('#aT').value, text: $('#aX').value}); OV = null; toast('Ogłoszenie zapisane 💚'); } catch (e){ toast('⚠️ ' + e.message); } };
  $('#bGo').onclick = async () => { const t = $('#bT').value.trim(), x = $('#bX').value.trim(); if (!t || !x) return toast('Podaj tytuł i treść.');
    if (!confirm(`Wysłać do WSZYSTKICH użytkowników?\n\n„${t}”\n\n${x.slice(0, 300)}`)) return;
    try { await act('/api/mod/broadcast', {title: t, body: x, important: $('#bI').checked}); toast('Wysłane do wszystkich 📬'); $('#bT').value = $('#bX').value = ''; msg(); } catch (e){ toast('⚠️ ' + e.message); } };
}
async function support(){
  sec(`<h2>💬 Wsparcie</h2><div class="mp-card"><p>Rozmowy „Pomoc na żywo” i wiadomości „Napisz do moderatora”. Odpowiadasz jako „Zespół Luny · Moderator” – nigdy pod własnym imieniem.</p>
  <div class="mp-row"><a class="mp-btn primary" href="/admin-support.html" target="_self">Otwórz widok wsparcia ↗</a><a class="mp-btn" href="/panel.html" target="_self">Pełny panel producenta ↗</a></div></div>`);
}
async function audit(){
  const d = await req('/api/mod/audit');
  sec(`<h2>📜 Dziennik działań</h2><p class="mp-hint">Każda akcja panelu: kto (zawsze „Moderator”), co i kiedy.</p><div class="mp-card mp-log">${d.items.map(x => `<div><time>${when(x.t)}</time><b>${esc(x.who)}</b> · ${esc(x.action)} ${x.target ? '· ' + esc(x.target) : ''} ${x.detail ? '<span class="mp-hint">— ' + esc(x.detail) + '</span>' : ''}</div>`).join('') || '<p class="mp-hint">Pusto.</p>'}</div>`);
}
boot();
})();
