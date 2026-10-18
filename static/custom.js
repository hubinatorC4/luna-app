/* „Stwórz własną asystentkę” – personalizacja po stronie użytkownika (localStorage). */
(() => {
const $ = s => document.querySelector(s);
const RANK = {darmowy: 0, podstawowa: 1, premium: 2, pro: 3};
const PLAN_NAME = {darmowy: 'Darmowy', podstawowa: 'Podstawowa', premium: 'Premium', pro: 'Pro / Ultra'};
let SP = {plan: 'darmowy', free: {outfits: 1}};  // plan z serwera (konto) – nie da się go zmienić w przeglądarce
const isAdmin = () => !!sessionStorage.getItem('luna.admin');
const DEF = {plan: 'darmowy', agent: 'luna', name: '', wake: '', tone: '', length: '', ring: '', outfit: '', pose: '', body: '', own: ''};
let C = Object.assign({}, DEF, JSON.parse(localStorage.getItem('luna.custom') || '{}'));
let CAT = null;
const save = () => { try { localStorage.setItem('luna.custom', JSON.stringify(C)); } catch(e){ alert('Za mało miejsca na obraz – wybierz mniejszy plik.'); } };
const has = plan => RANK[C.plan] >= RANK[plan || 'darmowy'];
/* v1.5.5: trening agentki według planu – jeden krótki komunikat, bez natręctwa; serwer sprawdza to samo (/api/agent/custom) */
const LG = (document.documentElement.lang || 'pl').slice(0, 2);
const LK = {pl: ['🔒 Trening własnej agentki AI jest w ', 'od ', ' · 30 dni, jednorazowo, z VAT', 'Odblokuj ', 'Ta opcja jest w planie '],
  en: ['🔒 Training your own AI agent is in ', 'from ', ' · 30 days, one-off, VAT incl.', 'Unlock ', 'This option is in the plan '],
  es: ['🔒 El entrenamiento de tu propia agente de IA está en ', 'desde ', ' · 30 días, pago único, IVA incl.', 'Desbloquear ', 'Esta opción está en el plan '],
  de: ['🔒 Das Training deiner eigenen KI-Agentin ist in ', 'ab ', ' · 30 Tage, einmalig, inkl. MwSt.', '', 'Diese Option ist im Plan '],
  uk: ['🔒 Тренування власної ШІ-агентки – у плані ', 'від ', ' · 30 днів, разово, з ПДВ', 'Відкрити ', 'Ця опція – у плані ']}[LG] || null;
const LKT = LK || ['🔒 Trening własnej agentki AI jest w ', 'od ', ' · 30 dni, jednorazowo, z VAT', 'Odblokuj ', 'Ta opcja jest w planie '];
const PRICE = {premium: '59,99 zł', pro: '99,99 zł'};
const TIER = {name: 'premium', wake: 'premium', tone: 'premium', length: 'premium', ring: 'premium', own: 'premium', pose: 'pro', body: 'pro'};
function priceOf(plan){ const p = CAT && CAT.plans && CAT.plans.find(x => x.id === plan); return p && p.prices && p.prices.pln ? p.prices.pln + ' zł' : PRICE[plan]; }
function lockMsg(need, focus){
  const el = $('#c_lock'); if (!el) return;
  need = need || 'premium';
  el.hidden = has(need);
  if (el.hidden) return;
  $('#c_lockH').textContent = (focus ? LKT[4] : LKT[0]) + PLAN_NAME[need];
  $('#c_lockP').textContent = LKT[1] + priceOf(need) + LKT[2];
  $('#c_unlock').textContent = LG === 'de' ? PLAN_NAME[need] + ' freischalten' : LKT[3] + PLAN_NAME[need];
  if (focus) el.scrollIntoView({block: 'nearest', behavior: 'smooth'});
}
let syncT = 0;
function sync(){  /* serwer jest źródłem prawdy: opcje ponad plan są cofane */
  clearTimeout(syncT); syncT = setTimeout(() => {
    const h = {'Content-Type': 'application/json'}; const at = sessionStorage.getItem('luna.admin'); if (at) h['X-Admin-Token'] = at; const tc = localStorage.getItem('luna.tester'); if (tc) h['X-Tester'] = tc;
    const body = {agent: C.agent, outfit: C.outfit, name: C.name.trim(), wake: C.wake.trim(), tone: C.tone, length: C.length, ring: C.ring, own: !!C.own, pose: C.pose, body: C.body};
    fetch('/api/agent/custom', {method: 'POST', headers: h, credentials: 'same-origin', body: JSON.stringify(body)}).then(r => r.status === 402 ? r.json() : null).then(e => {
      if (!e) return;
      Object.keys(TIER).forEach(k => { if (RANK[TIER[k]] > RANK[SP.plan || 'darmowy'] && !isAdmin()) C[k] = DEF[k]; });
      save(); render(); apply(); lockMsg(e.required, true);
    }).catch(() => {});
  }, 600);
}
const freeLocked = () => false;  // przydział strojów do planów: panel → katalog (pole „plan”)
const agent = () => (CAT && (CAT.agents.find(a => a.id === C.agent && has(a.plan)) || CAT.agents[0])) || null;
const item = (kind, id) => { const a = agent(); return a && a[kind].find((o, i) => o.id === id && has(o.plan) && !freeLocked(kind, i)); };
const name = () => (has('premium') && C.name.trim()) || (agent() ? agent().name : 'Luna');

function image(){
  if (C.own && has('premium')) return C.own;
  const p = item('poses', C.pose), b = item('bodies', C.body), o = item('outfits', C.outfit);
  if (p && !p.placeholder) return p.image;
  if (b && !b.placeholder) return b.image;
  if (o) return o.image;
  const a = agent(); return a && a.id !== 'luna' ? a.avatar : null;
}
function apply(){
  const img = image();
  const two = u => u && /\.jpg$/.test(u) && !u.startsWith('data:') ? u.replace(/\.jpg$/, '@2x.jpg') : u;
  const av = $('#avatar'), mini = $('.mini');
  if (img){ av.removeAttribute('srcset'); mini.removeAttribute('srcset'); av.src = mini.src = img; if (two(img) !== img){ av.srcset = img + ' 1x, ' + two(img) + ' 2x'; mini.srcset = av.srcset; } }
  else { av.src = 'avatar-512.jpg'; av.srcset = 'avatar-512.jpg 1x, avatar-1024.jpg 2x'; mini.src = 'avatar-256.jpg'; mini.srcset = 'avatar-256.jpg 1x, avatar-512.jpg 2x, avatar-1024.jpg 3x'; }
  [av, mini].forEach(el => el.classList.toggle('cat', !!img));
  const bg = $('.bg'); if (bg) bg.style.backgroundImage = img ? `image-set(url("${img}") 1x, url("${two(img)}") 2x)` : 'image-set(url("luna_portrait.webp") type("image/webp") 1x, url("luna_portrait@2x.webp") type("image/webp") 2x, url("luna_portrait.jpg") 1x)';
  window.LunaRefreshAvatars && window.LunaRefreshAvatars();
  const n = name(); $('#agentName').textContent = n; $('#aiLabelName').textContent = n; document.title = n + ' – asystentka AI';
  const ring = has('premium') && C.ring; if (ring) document.documentElement.style.setProperty('--ring', ring);
  window.LunaSetWake && window.LunaSetWake((has('premium') && C.wake.trim()) || (agent() ? agent().wake_word : 'Luna'));
}
window.LunaName = name;
window.LunaCustomApply = () => apply();
window.LunaAvatarSrc = () => image() || 'avatar-256.jpg';
window.LunaHas = plan => has(plan);
window.LunaPersona = () => ({agent: agent() ? agent().id : 'luna', name: name(),
  tone: has('premium') ? C.tone : '', length: has('premium') ? C.length : ''});

function card(o, kind, selected, idx){
  const fl = freeLocked(kind, idx); const need = fl ? 'podstawowa' : o.plan; const locked = !has(o.plan) || fl;
  const b = document.createElement('button'); b.type = 'button'; b.className = 'card' + (selected ? ' on' : '') + (locked ? ' locked' : '');
  const im1 = o.image || o.avatar, im2 = o.image2x;
  b.innerHTML = `<img src="${im1}"${im2 ? ` srcset="${im1} 1x, ${im2} 2x"` : ''} alt="" loading="lazy"><span>${o.name}</span>` +
    (locked ? `<em>🔒 ${PLAN_NAME[need]}</em>` : (o.placeholder ? '<em class="soon">wkrótce</em>' : ''));
  b.onclick = () => {
    if (locked) { lockMsg(need, true); return; }
    if (kind === 'agents') { C.agent = o.id; C.outfit = C.pose = C.body = ''; }
    else { const k = {outfits: 'outfit', poses: 'pose', bodies: 'body'}[kind]; C[k] = C[k] === o.id && kind !== 'outfits' ? '' : o.id; }
    save(); render(); apply(); sync();
  };
  return b;
}
function render(){
  if (!CAT) return;
  $('#c_plan').value = C.plan; $('#c_plan').disabled = !isAdmin();
  $('#c_planNote').textContent = isAdmin() ? 'Tryb producenta: podgląd dowolnego planu.' : (SP.logged_in ? `Twój plan: ${PLAN_NAME[SP.plan]}.` : 'Plan Darmowy. Zaloguj się, aby korzystać z planu przypisanego do konta.') + ' Płatności – wkrótce.';
  const a = agent();
  const fill = (sel, list, kind, cur) => { const el = $(sel); el.innerHTML = ''; list.forEach((o, i) => el.appendChild(card(o, kind, o.id === cur, i))); };
  fill('#c_agents', CAT.agents, 'agents', a.id);
  fill('#c_outfits', a.outfits, 'outfits', C.outfit || (a.outfits[0] && a.outfits[0].id));
  fill('#c_poses', a.poses, 'poses', C.pose);
  fill('#c_bodies', a.bodies, 'bodies', C.body);
  $('#c_name').value = C.name; $('#c_wake').value = C.wake; $('#c_tone').value = C.tone; $('#c_length').value = C.length;
  $('#c_ring').value = C.ring || getComputedStyle(document.documentElement).getPropertyValue('--ring').trim() || '#2ee66b';
  document.querySelectorAll('#custom .lockable').forEach(el => {
    const ok = has(el.dataset.plan); el.classList.toggle('locked', !ok);
    el.querySelectorAll('input,select,button').forEach(i => i.disabled = !ok);
  });
  lockMsg();
  const cb = $('#customBtn'); if (cb) cb.classList.toggle('locked', !has('premium'));
}
$('#c_plan').onchange = e => { if (!isAdmin()) return; C.plan = e.target.value; save(); render(); apply(); };
window.LunaPlan = () => SP;
window.LunaPlanRefresh = () => {
  const h = {}; const at = sessionStorage.getItem('luna.admin'); if (at) h['X-Admin-Token'] = at; const tc = localStorage.getItem('luna.tester'); if (tc) h['X-Tester'] = tc;
  return fetch('/api/account/plan?vid=' + (window.LunaVid ? window.LunaVid() : ''), {headers: h, credentials: 'same-origin'}).then(r => r.json()).then(p => {
    SP = p; if (!isAdmin() || RANK[C.plan] === undefined) C.plan = p.plan; save(); render(); apply();
    document.body.dataset.plan = C.plan; window.dispatchEvent(new CustomEvent('luna-plan', {detail: p}));
  }).catch(() => {});
};
['name', 'wake'].forEach(k => $('#c_' + k).oninput = e => { C[k] = e.target.value.replace(/[<>]/g, ''); save(); apply(); sync(); });
['tone', 'length'].forEach(k => $('#c_' + k).onchange = e => { C[k] = e.target.value; save(); sync(); });
$('#c_ring').oninput = e => { C.ring = e.target.value; save(); apply(); sync(); };
$('#c_upload').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  if (!window.LunaAiUpload) return;
  const url = await window.LunaAiUpload(f, 512); if (url){ C.own = url; save(); apply(); sync(); }
};
$('#c_upload_clear').onclick = () => { C.own = ''; save(); apply(); };
$('#c_voice').onclick = () => { $('#custom').close(); $('#settingsBtn').click(); };
$('#c_reset').onclick = () => { const plan = C.plan; C = Object.assign({}, DEF, {plan}); save(); render(); apply(); };
$('#customBtn').onclick = () => { render(); $('#custom').showModal(); };
$('#c_unlock').onclick = () => { try { $('#custom').close(); } catch(e){} };
window.LunaReloadCatalog = () => fetch('/api/catalog').then(r => r.json()).then(c => { CAT = c; render(); apply(); });
window.LunaReloadCatalog().catch(() => {});
window.LunaPlanRefresh();
})();
