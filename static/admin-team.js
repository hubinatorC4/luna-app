/* Panel: „Dołącz do zespołu” – kolejka zgłoszeń (przeczytane / odezwiemy się / odrzuć / usuń). Odrzucone znikają po 90 dniach. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
const fmt = t => t ? new Date(t * 1000).toLocaleString('pl-PL') : '–';
const ST = {new: '🟡 nowe', contact: '💬 odezwiemy się', rejected: '❌ odrzucone'};
let AR = {};
async function api(body){
  const r = await fetch('/api/admin/team', {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify(body) : undefined});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function draw(items){
  const box = $('#tmAdminBody'); const nNew = items.filter(a => !a.read).length;
  $('#tmAdminCnt').textContent = nNew ? ` · ${nNew} nieprzeczytane` : '';
  if (!items.length){ box.innerHTML = '<p class="empty">Na razie pusto – nikt jeszcze nie zapukał 🚪</p>'; return; }
  box.innerHTML = '<p class="hint">Bez obietnic pensji, etatu, udziałów ani umowy – warunki ustalamy indywidualnie. Odpowiedź wysyłasz e-mailem; zalogowane osoby dostają też wiadomość w skrzynce.</p>' + items.map(a => `
   <div class="card" data-id="${esc(a.id)}" style="margin:10px 0;padding:12px 14px${a.read ? '' : ';border-color:#ff9a3c'}">
    <p><b>${esc(a.nick)}</b> · <a href="mailto:${esc(a.email)}">${esc(a.email)}</a> · ${ST[a.status] || a.status} · <small>${fmt(a.t)} · ${esc(a.lang)}${a.uid ? ' · konto' : ''}</small></p>
    <p>${a.areas.map(x => `<span class="pill" style="font-size:13px;padding:3px 10px">${esc(AR[x] || x)}</span>`).join(' ')}</p>
    <p style="white-space:pre-wrap">${esc(a.description)}</p>
    ${a.portfolio ? `<p class="hint">Portfolio: <a href="${esc(a.portfolio)}" target="_blank" rel="noopener noreferrer nofollow">${esc(a.portfolio)}</a></p>` : ''}
    <p class="hint">18+: ✅ · zgoda: ✅ ${fmt(a.consent_at)}</p>
    <div style="display:flex;gap:6px;flex-wrap:wrap">${a.read ? '' : '<button class="pill" data-act="read">👀 Przeczytane</button>'}
      <button class="pill" data-act="contact">💬 Odezwiemy się</button><button class="pill" data-act="rejected">❌ Odrzuć</button><button class="pill" data-act="delete">🗑️ Usuń</button></div>
   </div>`).join('');
}
async function load(){ try { const d = await api(); AR = d.areas || {}; draw(d.items); } catch(e){ $('#tmAdminBody').innerHTML = `<p class="empty">${esc(e.message)}</p>`; } }
document.addEventListener('click', async e => {
  const b = e.target.closest('#tmAdmin [data-act]'); if (!b) return;
  const id = b.closest('[data-id]').dataset.id, act = b.dataset.act;
  if (act === 'delete' && !confirm('Usunąć zgłoszenie na stałe?')) return;
  b.disabled = true; try { draw((await api({id, action: act})).items); } catch(x){ alert(x.message); b.disabled = false; }
});
const det = $('#tmAdmin'); if (det){ det.addEventListener('toggle', () => { if (det.open) load(); }); if (tok()) load(); }
})();
