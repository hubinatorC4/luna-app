/* Panel: kolejka Zgłoś 🚩 – sprawy pogrupowane po celu (treść/osoba), kopia treści, powody, decyzje i strike'i (3 = trwała blokada).
   Tożsamość zgłaszających nie jest tu pokazywana (tylko liczba i konto/gość); autor dostaje uzasadnienie (art. 17 DSA) z linkiem do odwołania. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
const fmt = t => t ? new Date(t * 1000).toLocaleString('pl-PL') : '–';
let F = {status: 'open', type: '', cat: ''}, D = null;
async function api(body){
  const q = new URLSearchParams(F).toString();
  const r = await fetch('/api/admin/reports' + (body ? '' : '?' + q), {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify({...body, status: F.status}) : undefined});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
const ST = {open: '🟡 nowe', hidden: '⏸️ ukryte automatycznie', decided: '✅ rozpatrzone'};
function card(c){
  const cats = Object.entries(c.cats).map(([k, v]) => `${esc(D.cats[k] || k)} ×${v}`).join(' · ');
  const sd = c.standing ? `Poważne naruszenia: <b>${c.standing.strikes} z ${c.standing.max}</b>${c.standing.banned ? ' · ⛔ ban' : ''}${c.standing.block_until ? ' · ⏸️ do ' + fmt(c.standing.block_until) : ''}${c.standing.warns ? ' · ostrzeżenia: ' + c.standing.warns : ''}` : (c.author_kind === 'guest' ? 'autor: gość (urządzenie) – możliwy tylko ban urządzenia w Ściance' : 'brak autora (np. produkt)');
  const dec = c.dec ? `<p class="hint">Decyzja ${fmt(c.dec.t)}: <b>${esc(D.decisions[c.dec.final === 'ban' ? 'ban' : c.dec.action] || c.dec.action)}</b> · ${esc(D.cats[c.dec.cat] || c.dec.cat)}${c.dec.serious ? ' · poważne' + (c.dec.strike_n ? ` (${c.dec.strike_n} z 3)` : '') : ''}${c.dec.note ? ' · „' + esc(c.dec.note) + '”' : ''}</p>` : '';
  return `<div class="card rpc" data-id="${esc(c.id)}" style="margin:10px 0;padding:12px 14px">
    <p><b>${esc(D.types[c.type] || c.type)}</b> · ${ST[c.status] || c.status}${c.auto ? (c.hidden_why === 'minor' ? ' (kategoria „Osoba niepełnoletnia” – od razu)' : ` (≥${D.rules.auto_hide_at} zgłoszeń)`) : ''} · <small>${fmt(c.t)} · sprawa ${esc(c.id)} · cel ${esc(c.tid)}</small></p>
    <div style="display:flex;gap:12px;align-items:flex-start">${c.snap.img ? `<img data-src="${esc(c.snap.img)}" alt="" style="width:96px;height:96px;object-fit:cover;border-radius:12px;background:#222">` : ''}
      <div><p><b>${esc(c.snap.nick || '–')}</b>${c.snap.text ? ': ' + esc(c.snap.text) : ''}</p>
      <p class="hint">Zgłoszenia: <b>${c.n}</b> (w tym goście: ${c.guests}) · ${cats}</p>${c.notes.length ? `<p class="hint">Notatki: ${c.notes.map(n => '„' + esc(n) + '”').join(' · ')}</p>` : ''}
      <p class="hint">${sd}</p>${dec}</div></div>
    <div class="rpa" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px">
      <select class="rpcat" aria-label="Powód">${Object.entries(D.cats).map(([k, v]) => `<option value="${k}"${(Object.keys(c.cats)[0] || '') === k ? ' selected' : ''}>${esc(v)}</option>`).join('')}</select>
      <label style="font-size:13px"><input type="checkbox" class="rpser"> poważne (strike)</label>
      <select class="rpdays" aria-label="Dni blokady"><option value="1">1 dzień</option><option value="7" selected>7 dni</option><option value="30">30 dni</option></select>
      <input class="rpnote" maxlength="300" placeholder="Uzasadnienie dla autora (opcjonalnie)" style="flex:1;min-width:180px">
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px">
      <button data-a="dismiss">Odrzuć zgłoszenie (bez naruszenia)</button><button data-a="remove">Usuń treść</button><button data-a="warn">Ostrzeżenie</button>
      <button data-a="temp_block" ${c.owner_short ? '' : 'disabled'}>Blokada czasowa</button><button data-a="ban" class="danger">Ban</button>
      ${c.standing && (c.standing.banned || c.standing.block_until) ? '<button data-a="lift" class="ghost">Zdejmij blokadę</button>' : ''}${c.standing && c.standing.strikes ? '<button data-a="unstrike" class="ghost">Cofnij 1 strike</button>' : ''}
    </div></div>`;
}
function render(){
  const B = $('#rpAdminBody'); const c = D.counts;
  $('#rpAdminCnt').textContent = ` (${c.open} nowe, ${c.hidden} ukryte)`;
  B.innerHTML = `<p class="hint">Automatycznie: ≥${D.rules.auto_hide_at} różnych zgłaszających → treść ukryta do decyzji; „Osoba niepełnoletnia” → ukrycie od razu. Poważne naruszenie = strike; ${D.rules.max_strikes}. strike = trwała blokada. Ban = natychmiast (najcięższe przypadki). Zgłaszający i autor dostają wiadomość w Skrzynce; zgłaszający pozostaje anonimowy.</p>
    <p class="f18af">${[['open', 'Do decyzji'], ['hidden', 'Ukryte'], ['decided', 'Rozpatrzone'], ['all', 'Wszystkie']].map(([k, v]) => `<button data-s="${k}" class="${F.status === k ? 'on' : ''}">${v}</button>`).join(' ')}
      <select id="rpT"><option value="">każdy typ</option>${Object.entries(D.types).map(([k, v]) => `<option value="${k}"${F.type === k ? ' selected' : ''}>${esc(v)}</option>`).join('')}</select>
      <select id="rpC"><option value="">każdy powód</option>${Object.entries(D.cats).map(([k, v]) => `<option value="${k}"${F.cat === k ? ' selected' : ''}>${esc(v)}</option>`).join('')}</select></p>
    ${D.items.map(card).join('') || '<p class="empty">Brak zgłoszeń – spokojny dzień 🌙</p>'}`;
  B.querySelectorAll('[data-s]').forEach(b => b.onclick = () => { F.status = b.dataset.s; load(); });
  $('#rpT').onchange = e => { F.type = e.target.value; load(); }; $('#rpC').onchange = e => { F.cat = e.target.value; load(); };
  B.querySelectorAll('img[data-src]').forEach(async im => { try { const r = await fetch(im.dataset.src, {headers: {'X-Admin-Token': tok()}}); if (r.ok) im.src = URL.createObjectURL(await r.blob()); } catch(e){} });
  B.querySelectorAll('.rpc button[data-a]').forEach(b => b.onclick = async () => {
    const box = b.closest('.rpc'); const a = b.dataset.a;
    if (a === 'ban' && !confirm('Ban = trwała blokada konta. Na pewno?')) return;
    try { D = await api({id: box.dataset.id, action: a, cat: box.querySelector('.rpcat').value, serious: a === 'ban' || a === 'temp_block' ? true : box.querySelector('.rpser').checked,
      days: +box.querySelector('.rpdays').value, note: box.querySelector('.rpnote').value}); render(); } catch(e){ alert(e.message); }
  });
}
async function load(){ try { D = await api(); render(); } catch(e){ $('#rpAdminBody').innerHTML = `<p class="empty">${esc(e.message)}</p>`; } }
const el = $('#rpAdmin'); if (!el) return;
el.addEventListener('toggle', () => { if (el.open) load(); });
if (tok()) api().then(d => { D = d; $('#rpAdminCnt').textContent = ` (${d.counts.open} nowe, ${d.counts.hidden} ukryte)`; }).catch(() => {});
})();
