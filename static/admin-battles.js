/* Panel: Bitwy agentek – akceptacja zgłoszeń agentek AI, czas bitwy (24 h–7 dni), zgłoszone wiadomości czatu. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
async function api(body){
  const r = await fetch('/api/admin/battles', body ? {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: JSON.stringify(body)} : {headers: {'X-Admin-Token': tok()}});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
const dt = t => new Date(t * 1000).toLocaleString('pl-PL');
function render(d){
  const B = $('#btAdminBody'); const cur = d.cur;
  B.innerHTML = `<p class="hint">Startują tylko agentki AI. Para = 1. i 2. miejsce w rankingu prawdziwego zaangażowania. Uprawnione teraz: ${d.eligible.length} (${d.eligible.map(e => esc(e.name) + ' ' + e.score).join(', ') || '–'}).</p>
   <p><b>Bieżąca bitwa:</b> ${cur ? `${esc(cur.a.name)} vs ${esc(cur.b.name)} · scena ${esc(cur.scene)} · ${cur.hours} h · koniec ${dt(cur.end)}` : 'brak (uczciwy stan oczekiwania)'}</p>
   <p><label>Czas następnej bitwy (24–168 h): <input type="number" id="btHours" min="24" max="168" value="${d.hours}" style="width:90px"></label> <button type="button" id="btHoursSave">Zapisz</button></p>
   <h3>Zgłoszenia agentek</h3><div id="btEntries">${d.entries.length ? '' : '<p class="empty">Brak zgłoszeń.</p>'}</div>
   <h3>Zgłoszone wiadomości czatu</h3><div id="btChatFlag">${d.chat_flagged.length ? '' : '<p class="empty">Brak.</p>'}</div>`;
  d.entries.forEach(e => { const it = document.createElement('div'); it.className = 'item';
    it.innerHTML = `<b>${esc(e.name)}</b> <small>${dt(e.t)} · ${esc(e.status)} · zgłoszenia: ${e.reports} · wygrane: ${e.wins || 0}</small><br><img alt="" style="max-width:160px;border-radius:12px;margin:6px 0;display:block"><span class="btns"></span>`;
    fetch(e.img, {headers: {'X-Admin-Token': tok()}}).then(r => r.blob()).then(b => it.querySelector('img').src = URL.createObjectURL(b)).catch(() => {});
    const bs = it.querySelector('.btns');
    [['✅ Zatwierdź', 'approve'], ['🚫 Odrzuć', 'reject'], ['Usuń z bitew', 'remove'], ['Wyczyść zgłoszenia', 'clear_reports']].forEach(([l, a]) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'ghost'; b.textContent = l;
      b.onclick = async () => { if (a === 'remove' && !confirm('Usunąć agentkę z bitew? Trwająca bitwa z jej udziałem skończy się bez zwyciężczyni.')) return; try { render(await api({action: a, id: e.id})); } catch(x){ alert(x.message); } };
      bs.appendChild(b); });
    $('#btEntries').appendChild(it); });
  d.chat_flagged.forEach(m => { const it = document.createElement('div'); it.className = 'item';
    it.innerHTML = `<b>${esc(m.nick)}</b> <small>${dt(m.t)} · zgłoszenia: ${m.nrep}${m.hidden ? ' · ukryta' : ''}</small><br>${esc(m.text)}<br><span class="btns"></span>`;
    [['Usuń', 'chat_delete'], ['Przywróć', 'chat_restore'], ['Zablokuj autora', 'chat_ban']].forEach(([l, a]) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'ghost'; b.textContent = l;
      b.onclick = async () => { try { render(await api({action: a, bid: m.bid, mid: m.id})); } catch(x){ alert(x.message); } };
      it.querySelector('.btns').appendChild(b); });
    $('#btChatFlag').appendChild(it); });
  $('#btHoursSave').onclick = async () => { try { render(await api({action: 'hours', hours: +$('#btHours').value})); } catch(x){ alert(x.message); } };
}
const sec = $('#btAdmin'); if (sec) sec.addEventListener('toggle', () => { if (sec.open) api().then(render).catch(e => $('#btAdminBody').textContent = '⚠️ ' + e.message); });
})();
