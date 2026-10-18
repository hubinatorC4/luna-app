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
    if (locked) { alert('Ta opcja jest dostępna od planu ' + PLAN_NAME[need] + '. Płatności – wkrótce.'); return; }
    if (kind === 'agents') { C.agent = o.id; C.outfit = C.pose = C.body = ''; }
    else { const k = {outfits: 'outfit', poses: 'pose', bodies: 'body'}[kind]; C[k] = C[k] === o.id && kind !== 'outfits' ? '' : o.id; }
    save(); render(); apply();
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
['name', 'wake'].forEach(k => $('#c_' + k).oninput = e => { C[k] = e.target.value.replace(/[<>]/g, ''); save(); apply(); });
['tone', 'length'].forEach(k => $('#c_' + k).onchange = e => { C[k] = e.target.value; save(); });
$('#c_ring').oninput = e => { C.ring = e.target.value; save(); apply(); };
$('#c_upload').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  if (!window.LunaAiUpload) return;
  const url = await window.LunaAiUpload(f, 512); if (url){ C.own = url; save(); apply(); }
};
$('#c_upload_clear').onclick = () => { C.own = ''; save(); apply(); };
$('#c_voice').onclick = () => { $('#custom').close(); $('#settingsBtn').click(); };
$('#c_reset').onclick = () => { const plan = C.plan; C = Object.assign({}, DEF, {plan}); save(); render(); apply(); };
$('#customBtn').onclick = () => { render(); $('#custom').showModal(); };
window.LunaReloadCatalog = () => fetch('/api/catalog').then(r => r.json()).then(c => { CAT = c; render(); apply(); });
window.LunaReloadCatalog().catch(() => {});
window.LunaPlanRefresh();
})();
