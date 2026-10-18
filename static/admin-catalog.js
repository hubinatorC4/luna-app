/* Tryb producenta – edycja katalogu postaci / strojów / póz / sylwetek / planów. */
(() => {
const $ = s => document.querySelector(s);
const PLANS = [['darmowy','Darmowy'],['podstawowa','Podstawowa'],['premium','Premium'],['pro','Pro / Ultra']];
const TONES = [['rzeczowa','Rzeczowa'],['ciepla','Ciepła'],['zalotna','Zalotna (subtelna)'],['motywujaca','Motywująca']];
const KIND = {outfits:'Stroje', poses:'Pozy', bodies:'Sylwetki'};
let CAT = null, PUB = null, cur = 0;
const tok = () => sessionStorage.getItem('luna.admin') || '';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const opts = (list, v) => list.map(([k, n]) => `<option value="${k}"${k === v ? ' selected' : ''}>${n}</option>`).join('');
function msg(t, bad){ const m = $('#catMsg'); m.textContent = t; m.style.color = bad ? '#ff8a7a' : '#7dffa8'; }
async function api(path, body){
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify(body) : undefined});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function pubImg(aid, kind, id){ const a = PUB && PUB.agents.find(x => x.id === aid); const o = a && a[kind].find(x => x.id === id); return o ? o.image : ''; }
function renderPlans(){
  $('#catPlans').innerHTML = CAT.plans.map((p, i) => `<div class="item">
    <div class="row3"><input type="text" data-p="${i}" data-k="name" value="${esc(p.name)}" placeholder="Nazwa">
    <input type="text" data-p="${i}" data-k="price" value="${esc(p.price)}" placeholder="Cena">
    <input type="text" data-p="${i}" data-k="period" value="${esc(p.period)}" placeholder="Okres"></div>
    <label>Funkcje (jedna w wierszu)<textarea rows="4" data-p="${i}" data-k="features">${esc(p.features.join('\n'))}</textarea></label></div>`).join('');
  $('#catPlans').querySelectorAll('[data-p]').forEach(el => el.oninput = () => {
    const p = CAT.plans[el.dataset.p]; p[el.dataset.k] = el.dataset.k === 'features' ? el.value.split('\n').map(s => s.trim()).filter(Boolean) : el.value; });
}
function renderAgent(){
  $('#catAgentSel').innerHTML = CAT.agents.map((a, i) => `<option value="${i}"${i === cur ? ' selected' : ''}>${esc(a.name)}</option>`).join('');
  const a = CAT.agents[cur]; if (!a) return;
  let h = `<div class="item">
    <div class="row3"><input type="text" data-a="name" value="${esc(a.name)}" placeholder="Imię">
    <input type="text" data-a="wake_word" value="${esc(a.wake_word)}" placeholder="Słowo wybudzające">
    <select data-a="plan">${opts(PLANS, a.plan)}</select></div>
    <label>Ton<select data-a="tone">${opts(TONES, a.tone)}</select></label>
    <label>Opis<input type="text" data-a="description" value="${esc(a.description)}"></label>
    <label>Osobowość (puste = globalny prompt Luny)<textarea rows="3" data-a="persona">${esc(a.persona)}</textarea></label>
    <div class="row3"><label>Wysokość głosu<input type="number" step="0.1" min="-6" max="2" data-v="pitch" value="${a.voice.pitch}"></label>
    <label>Tempo %<input type="number" step="1" min="-40" max="30" data-v="rate" value="${a.voice.rate}"></label>
    <label>Ciepło<input type="number" step="0.5" min="0" max="10" data-v="warmth" value="${a.voice.warmth}"></label></div></div>`;
  for (const k of Object.keys(KIND)){
    h += `<h4 class="sub">${KIND[k]}</h4>` + (a[k].length ? '' : '<p class="hint">Brak.</p>') + a[k].map((o, j) => `<div class="itemrow">
      <img src="${esc(o.image || pubImg(a.id, k, o.id))}" alt="">
      <input type="text" data-k="${k}" data-j="${j}" data-f="name" value="${esc(o.name)}">
      <select data-k="${k}" data-j="${j}" data-f="plan">${opts(PLANS, o.plan)}</select>
      <button type="button" class="del" data-k="${k}" data-j="${j}" title="Usuń">✕</button></div>`).join('');
  }
  const box = $('#catAgent'); box.innerHTML = h;
  box.querySelectorAll('[data-a]').forEach(el => el.oninput = () => { a[el.dataset.a] = el.value; if (el.dataset.a === 'name') $('#catAgentSel').options[cur].text = el.value; });
  box.querySelectorAll('[data-v]').forEach(el => el.oninput = () => { a.voice[el.dataset.v] = parseFloat(el.value); });
  box.querySelectorAll('[data-f]').forEach(el => el.oninput = () => { a[el.dataset.k][el.dataset.j][el.dataset.f] = el.value; });
  box.querySelectorAll('.del').forEach(el => el.onclick = () => { a[el.dataset.k].splice(+el.dataset.j, 1); renderAgent(); });
}
function render(){ renderPlans(); renderAgent(); }
async function load(){ if (!tok()) return; try { const d = await api('/api/admin/catalog'); CAT = d.catalog; PUB = d.public; cur = 0; render(); } catch(e){} }
function after(d, t){ CAT = d.catalog; PUB = d.public; render(); msg(t); window.LunaReloadCatalog && window.LunaReloadCatalog(); }
$('#catSection').addEventListener('toggle', e => { if (e.target.open && !CAT) load(); });
$('#catAgentSel').onchange = e => { cur = +e.target.value; renderAgent(); };
$('#catAddAgent').onclick = () => { const n = prompt('Imię nowej postaci:'); if (!n) return;
  CAT.agents.push({id: n.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '') || 'agent' + Date.now(), name: n, wake_word: n, plan: 'pro', tone: 'ciepla', persona: '', description: '',
    voice: {voice: 'pl-PL-ZofiaNeural', pitch: -2, rate: -6, warmth: 4, volume: -27, spanish: false}, outfits: [], poses: [], bodies: []});
  cur = CAT.agents.length - 1; renderAgent(); msg('Dodaj postaci co najmniej jeden strój (obraz), a potem zapisz katalog.'); };
$('#catDelAgent').onclick = () => { if (CAT.agents.length < 2) return msg('Musi zostać co najmniej jedna postać.', true);
  if (!confirm('Usunąć postać ' + CAT.agents[cur].name + '?')) return; CAT.agents.splice(cur, 1); cur = 0; renderAgent(); };
$('#catItemFile').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  const name = $('#catItemName').value.trim(); if (!name) return msg('Najpierw wpisz nazwę elementu.', true);
  if (f.size > 4 * 1024 * 1024) return msg('Plik większy niż 4 MB.', true);
  if (!confirm('Potwierdzasz, że obraz jest stonowany i nie zawiera treści erotycznych?')) return;
  const data = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); });
  try {
    const d = await api('/api/admin/upload', {name: f.name, data});
    const k = $('#catKind').value, a = CAT.agents[cur];
    a[k].push({id: name.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '') || 'el' + Date.now(), name, plan: $('#catItemPlan').value, image: d.url});
    $('#catItemName').value = ''; renderAgent(); msg('Dodano – pamiętaj, aby zapisać katalog.');
  } catch(err){ msg('Błąd wgrywania: ' + err.message, true); }
};
$('#catSave').onclick = async () => { try { after(await api('/api/admin/catalog', {catalog: CAT}), 'Katalog zapisany ✔'); } catch(e){ msg('Błąd: ' + e.message, true); } };
$('#catReset').onclick = async () => { if (!confirm('Przywrócić domyślny katalog?')) return; try { after(await api('/api/admin/catalog/reset', {}), 'Przywrócono domyślny katalog ✔'); } catch(e){ msg('Błąd: ' + e.message, true); } };
$('#catExport').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(CAT, null, 2)], {type: 'application/json'})); a.download = 'luna-katalog.json'; a.click(); };
$('#catImport').onchange = async e => { const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  try { after(await api('/api/admin/catalog', {catalog: JSON.parse(await f.text())}), 'Zaimportowano katalog ✔'); } catch(err){ msg('Błąd importu: ' + err.message, true); } };
})();
