/* Luna – panel producenta: testerzy, Luna Live, powiadomienia, kopia danych. */
(() => {
const $ = s => document.querySelector(s);
const tok = () => sessionStorage.getItem('luna.admin') || '';
async function api(path, body){
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers:{'Content-Type':'application/json','X-Admin-Token':tok()}, body: body ? JSON.stringify(body) : undefined});
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || r.status); return d;
}
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const RING = {fioletowa: '#8B5CF6', niebieska: '#3B82F6'};
/* ---------- testerzy ---------- */
async function testers(){
  try {
    const d = await api('/api/admin/testers'); const L = $('#tstList'); L.textContent = '';
    $('#tstCount').textContent = `(${d.testers.length}/${d.limit})`;
    $('#tstStore').textContent = d.storage.persistent ? '✅ Zgłoszenia zapisywane w Postgresie (trwale).' : '⚠️ Zgłoszenia są na ulotnym dysku – znikną przy wdrożeniu. Rób eksport CSV / kopię danych!';
    $('#tstStore').style.color = d.storage.persistent ? '#7dffa8' : '#ffb3a7';
    if (!d.testers.length) L.appendChild(el('p', 'hint', 'Brak zgłoszeń.'));
    d.testers.forEach(t => {
      const it = el('div', 'item tst');
      const h = el('div'); const dot = el('span', 'rdot'); dot.style.background = RING[t.ring]; h.append(dot, el('b', null, t.name + ' '), el('small', null, t.email));
      const m = el('small', null, `${new Date(t.t * 1000).toLocaleString('pl-PL')} · obwódka: ${t.ring} · Android: ${t.android ? 'tak' : 'nie'} · kod: ${t.code}`);
      const r = el('p', 'reason', t.reason || '—');
      const ctl = el('div', 'btns');
      const lab = el('label', 'row'); const cb = el('input'); cb.type = 'checkbox'; cb.checked = t.granted && t.until * 1000 > Date.now();
      lab.append(cb, document.createTextNode(cb.checked ? ` Premium do ${new Date(t.until * 1000).toLocaleDateString('pl-PL')}` : ' Przyznaj Premium (60 dni) i obwódkę'));
      const sel = el('select'); ['fioletowa', 'niebieska'].forEach(v => { const o = el('option', null, v); o.value = v; sel.appendChild(o); }); sel.value = t.ring;
      cb.onchange = sel.onchange = async () => { try { await api('/api/admin/testers/grant', {code: t.code, on: cb.checked, ring: sel.value}); testers(); } catch(e){ alert(e.message); } };
      const del = el('button', 'ghost danger', 'Usuń'); del.type = 'button'; del.onclick = async () => { if (confirm('Usunąć zgłoszenie ' + t.name + '?')){ await api('/api/admin/testers/delete', {code: t.code}); testers(); } };
      ctl.append(lab, sel, del); it.append(h, m, r, ctl); L.appendChild(it);
    });
  } catch(e){ $('#tstStore').textContent = 'Błąd: ' + e.message; }
}
$('#tstReload').onclick = testers;
$('#tstCsv').onclick = async () => {
  const r = await fetch('/api/admin/testers.csv', {headers: {'X-Admin-Token': tok()}}); if (!r.ok) return alert('Błąd eksportu');
  const b = await r.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'testerzy-luna-' + new Date().toISOString().slice(0, 10) + '.csv'; a.click();
};
$('#tstSection').addEventListener('toggle', e => { if (e.target.open) testers(); });
/* ---------- Luna Live ---------- */
async function lv(action, extra = {}){
  try { await api('/api/admin/live-room', Object.assign({action}, extra)); } catch(e){ alert(e.message); }
  liveState();
}
async function liveState(){
  try { const s = await (await fetch('/api/live-room/state', {headers: {'X-Admin-Token': tok()}})).json();
    $('#lvState').textContent = (s.on ? '🔴 NA ŻYWO' : '⚪ Offline') + ` · tryb: ${({auto: 'harmonogram', on: 'ręcznie włączona', off: 'ręcznie wyłączona'})[s.mode]} · widzowie: ${s.viewers} · pytania w kolejce: ${s.queue_len} · następna: ${s.sched.next_label} · ${s.sched.weekly}`;
    if (!$('#lvTopic').value) $('#lvTopic').value = s.topic || '';
  } catch(e){}
}
$('#lvStart').onclick = () => lv('start', {topic: $('#lvTopic').value});
$('#lvStop').onclick = () => { if (confirm('Zakończyć transmisję?')) lv('stop'); };
$('#lvSched').onclick = () => lv('schedule');
$('#liveSection').addEventListener('toggle', e => { if (e.target.open) liveState(); });
/* ---------- powiadomienia ---------- */
async function ntf(){
  try { const s = await api('/api/admin/notify');
    const lines = [
      `Push: ${s.push.enabled ? '✅ włączone' : '❌ brak kluczy VAPID'} · subskrybenci: ${s.push.subscribers}`,
      `E-mail: ${s.email.enabled ? '✅ ' + s.email.provider : '❌ wyłączony – brak EMAIL_PROVIDER / EMAIL_API_KEY / EMAIL_FROM'} · zapisani: ${s.email.subscribers} (potwierdzeni: ${s.email.confirmed})`,
      `Cron: ${s.cron.configured ? '✅ sekret ustawiony' : '❌ brak CRON_SECRET'} · ostatnie wywołanie: ${s.cron.last ? new Date(s.cron.last.t * 1000).toLocaleString('pl-PL') : 'brak'}`,
      `Magazyn: ${s.storage.persistent ? '✅ Postgres' : '⚠️ plik (ulotny)'}`];
    $('#ntfStatus').textContent = lines.join('\n'); $('#ntfStatus').style.whiteSpace = 'pre-line';
  } catch(e){ $('#ntfStatus').textContent = 'Błąd: ' + e.message; }
}
$('#ntfSection').addEventListener('toggle', e => { if (e.target.open) ntf(); });
$('#ntfSend').onclick = async () => {
  const b = {topic: $('#ntfTopic').value, title: $('#ntfTitle').value.trim(), body: $('#ntfBody').value.trim(), url: $('#ntfUrl').value.trim() || '/'};
  if (!b.title) return alert('Podaj tytuł.');
  if (!confirm('Wysłać powiadomienie do subskrybentów?')) return;
  try { const r = await api('/api/admin/notify/push', b); alert(r.disabled ? 'Push wyłączony (brak kluczy).' : `Wysłano: ${r.sent}, błędy: ${r.failed}`); ntf(); } catch(e){ alert(e.message); }
};
$('#ntfMailSend').onclick = async () => { try { await api('/api/admin/notify/email-test', {to: $('#ntfMail').value.trim()}); alert('Wysłano test.'); } catch(e){ alert(e.message); } };
/* ---------- kopia danych ---------- */
$('#bakExport').onclick = async () => { try { const d = await api('/api/admin/backup'); const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 1)], {type: 'application/json'})); a.download = 'luna-dane-' + new Date().toISOString().slice(0, 10) + '.json'; a.click(); } catch(e){ alert(e.message); } };
$('#bakImport').onchange = async e => { const f = e.target.files[0]; if (!f) return; try { const d = JSON.parse(await f.text()); const r = await api('/api/admin/backup', d); alert('Zaimportowano: ' + JSON.stringify(r.imported)); testers(); } catch(x){ alert('Błąd importu: ' + x.message); } e.target.value = ''; };
})();
