/* „Stwórz własną asystentkę” – personalizacja po stronie użytkownika (localStorage). */
(() => {
const $ = s => document.querySelector(s);
const RANK = {podstawowa: 0, premium: 1, pro: 2};
const PLAN_NAME = {podstawowa: 'Podstawowa', premium: 'Premium', pro: 'Pro / Ultra'};
const DEF = {plan: 'podstawowa', agent: 'luna', name: '', wake: '', tone: '', length: '', ring: '', outfit: '', pose: '', body: '', own: ''};
let C = Object.assign({}, DEF, JSON.parse(localStorage.getItem('luna.custom') || '{}'));
let CAT = null;
const save = () => { try { localStorage.setItem('luna.custom', JSON.stringify(C)); } catch(e){ alert('Za mało miejsca na obraz – wybierz mniejszy plik.'); } };
const has = plan => RANK[C.plan] >= RANK[plan || 'podstawowa'];
const agent = () => (CAT && (CAT.agents.find(a => a.id === C.agent && has(a.plan)) || CAT.agents[0])) || null;
const item = (kind, id) => { const a = agent(); return a && a[kind].find(o => o.id === id && has(o.plan)); };
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

function card(o, kind, selected){
  const locked = !has(o.plan);
  const b = document.createElement('button'); b.type = 'button'; b.className = 'card' + (selected ? ' on' : '') + (locked ? ' locked' : '');
  const im1 = o.image || o.avatar, im2 = o.image2x;
  b.innerHTML = `<img src="${im1}"${im2 ? ` srcset="${im1} 1x, ${im2} 2x"` : ''} alt="" loading="lazy"><span>${o.name}</span>` +
    (locked ? `<em>🔒 ${PLAN_NAME[o.plan]}</em>` : (o.placeholder ? '<em class="soon">wkrótce</em>' : ''));
  b.onclick = () => {
    if (locked) { alert('Ta opcja jest dostępna w planie ' + PLAN_NAME[o.plan] + '.'); return; }
    if (kind === 'agents') { C.agent = o.id; C.outfit = C.pose = C.body = ''; }
    else { const k = {outfits: 'outfit', poses: 'pose', bodies: 'body'}[kind]; C[k] = C[k] === o.id && kind !== 'outfits' ? '' : o.id; }
    save(); render(); apply();
  };
  return b;
}
function render(){
  if (!CAT) return;
  $('#c_plan').value = C.plan;
  const a = agent();
  const fill = (sel, list, kind, cur) => { const el = $(sel); el.innerHTML = ''; list.forEach(o => el.appendChild(card(o, kind, o.id === cur))); };
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
$('#c_plan').onchange = e => { C.plan = e.target.value; save(); render(); apply(); };
['name', 'wake'].forEach(k => $('#c_' + k).oninput = e => { C[k] = e.target.value.replace(/[<>]/g, ''); save(); apply(); });
['tone', 'length'].forEach(k => $('#c_' + k).onchange = e => { C[k] = e.target.value; save(); });
$('#c_ring').oninput = e => { C.ring = e.target.value; save(); apply(); };
$('#c_upload').onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  const img = new Image(); img.onload = () => {
    const s = Math.min(512 / img.width, 512 / img.height, 1), cv = document.createElement('canvas');
    cv.width = Math.round(img.width * s); cv.height = Math.round(img.height * s);
    cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
    C.own = cv.toDataURL('image/jpeg', 0.85); save(); apply(); URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(f); e.target.value = '';
};
$('#c_upload_clear').onclick = () => { C.own = ''; save(); apply(); };
$('#c_voice').onclick = () => { $('#custom').close(); $('#settingsBtn').click(); };
$('#c_reset').onclick = () => { const plan = C.plan; C = Object.assign({}, DEF, {plan}); save(); render(); apply(); };
$('#customBtn').onclick = () => { render(); $('#custom').showModal(); };
window.LunaReloadCatalog = () => fetch('/api/catalog').then(r => r.json()).then(c => { CAT = c; render(); apply(); });
window.LunaReloadCatalog().catch(() => {});
})();
