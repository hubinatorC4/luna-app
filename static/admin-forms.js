/* Panel: formularze 18+ (testerzy i casting). Status: pending / verified / failed / accepted / rejected.
   Przyjąć można tylko zgłoszenie ze zweryfikowaną pełnoletnością. Odrzucone usuwane automatycznie po 90 dniach. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
const ST = {pending: '⏳ oczekuje na weryfikację', verified: '✅ zweryfikowano 18+', failed: '⚠️ weryfikacja nieudana', accepted: '💚 przyjęte', rejected: '✖ odrzucone'};
const NAMES = {voice: 'trener głosu', battles: 'bitwy', wall: 'ściana', generator: 'generator', android: 'Android', iphone: 'iPhone', desktop: 'komputer',
  both: 'głos i wizerunek', image: 'wizerunek', voice_only: 'tylko głos', no_face: 'wizerunek bez twarzy', full: 'pełny wizerunek'};
const n = v => NAMES[v] || v || '–';
const fmt = t => t ? new Date(t * 1000).toLocaleString('pl-PL') : '–';
let FILTER = 'all';
async function api(body){
  const r = await fetch('/api/admin/forms', {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify(body) : undefined});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function row(i){
  const v = i.verification || {};
  const meth = v.method ? (v.method === 'document' ? 'dokument (Stripe Identity)' : 'karta – słabszy dowód' + (v.card ? ` (${esc(v.card.brand)} •••• ${esc(v.card.last4)}${v.card.funding ? ', ' + esc(v.card.funding) : ''})` : '')) : '–';
  const det = i.kind === 'tester'
    ? `<b>${esc(i.nickname)}</b> · ${n(i.device)} · testuje: ${(i.topics || []).map(n).join(', ')}${i.note ? `<br><i>${esc(i.note)}</i>` : ''}`
    : `<b>${esc(i.pseudonym)}</b> · oferuje: ${n(i.offer)}${i.partner_posts ? ' · posty partnerskie' : ''}${i.promo_videos ? ' · filmy promo' : ''}<br>${esc(i.description)}
       <br><small>Kategorie: ${(i.cats || []).join(', ') || '–'} · języki: ${(i.langs || []).join(', ') || '–'} · anonimowość: ${n(i.anonymity)} · dostępność: ${esc(i.availability || '–')}${i.country ? ' · ' + esc(i.country) : ''}${i.portfolio ? ` · <a href="${esc(i.portfolio)}" target="_blank" rel="noopener noreferrer nofollow">portfolio</a>` : ''}</small>
       ${i.voice ? `<br>🎙️ próbka głosu (${esc(i.voice.status)}): <audio controls preload="none" data-voice="${esc(i.id)}"></audio> <button data-a="voice_approve" data-id="${esc(i.id)}">OK</button> <button data-a="voice_reject" data-id="${esc(i.id)}">Odrzuć</button> <button data-a="voice_delete" data-id="${esc(i.id)}">Usuń próbkę</button>` : ''}`;
  return `<tr class="${i.read ? '' : 'unread'}"><td>${i.kind === 'tester' ? '🧪 tester' : '🎙️ casting'}<br><small>${fmt(i.t)}</small></td><td>${det}<br><small>Kontakt: ${esc(i.email)}${i.phone ? ' · ' + esc(i.phone) : ''} · wiek z deklaracji: ${esc(i.age)}</small></td>
    <td><b>${ST[i.status] || i.status}</b><br><small>Metoda: ${meth}<br>Wynik: ${fmt(v.at)}${v.reason ? ' · ' + esc(v.reason) : ''}${v.ref ? '<br>Ref.: ' + esc(v.ref) : ''}</small></td>
    <td class="acts"><button data-a="accept" data-id="${esc(i.id)}" ${v.status === 'verified' && i.decision !== 'accepted' ? '' : 'disabled title="Najpierw weryfikacja 18+"'}>Przyjmij</button>
      <button data-a="reject" data-id="${esc(i.id)}" ${i.decision === 'rejected' ? 'disabled' : ''}>Odrzuć</button>
      <button data-a="delete" data-id="${esc(i.id)}" class="ghost">Usuń</button></td></tr>`;
}
function render(d){
  const B = $('#f18AdminBody'); const items = (d.items || []).filter(i => FILTER === 'all' || i.kind === FILTER || i.status === FILTER);
  B.innerHTML = `<p class="hint">Weryfikacja 18+: <b>${d.verify === 'on' ? 'włączona' : 'wkrótce (brak kluczy) – zgłoszenia czekają jako „oczekuje na weryfikację”'}</b>
      ${d.verify !== 'on' ? `<br>Potrzebne zmienne środowiskowe: ${(d.env_needed || []).map(esc).join(' · ')}` : ''}<br>
      Nie zapisujemy skanów dokumentów ani numerów kart – tylko wynik. Odrzucone zgłoszenia usuwamy automatycznie po 90 dniach. Wolne miejsca testerów: ${esc(d.testers_left)}.</p>
    <p class="f18af">${[['all', 'Wszystkie'], ['tester', 'Testerzy'], ['casting', 'Casting'], ['pending', 'Oczekujące'], ['verified', 'Zweryfikowane'], ['accepted', 'Przyjęte'], ['rejected', 'Odrzucone']].map(([k, l]) => `<button data-f="${k}" class="${FILTER === k ? 'on' : ''}">${l}</button>`).join(' ')}</p>
    <div style="overflow-x:auto"><table class="tbl"><tr><th>Formularz</th><th>Zgłoszenie</th><th>Status</th><th>Akcje</th></tr>${items.map(row).join('') || '<tr><td colspan="4">Brak zgłoszeń.</td></tr>'}</table></div><p id="f18Msg" class="hint"></p>`;
  B.querySelectorAll('[data-f]').forEach(b => b.onclick = () => { FILTER = b.dataset.f; render(d); });
  B.querySelectorAll('audio[data-voice]').forEach(a => a.addEventListener('play', async () => { if (a.src) return; const r = await fetch('/api/admin/forms/voice?id=' + a.dataset.voice, {headers: {'X-Admin-Token': tok()}}); a.src = URL.createObjectURL(await r.blob()); a.play(); }, {once: false}));
  B.querySelectorAll('button[data-a]').forEach(b => b.onclick = async () => {
    if (b.dataset.a === 'delete' && !confirm('Usunąć zgłoszenie na stałe?')) return;
    try { const r = await api({action: b.dataset.a, id: b.dataset.id}); render(r);
      $('#f18Msg').textContent = '✓' + (r.tester_code ? ` Kod testera: ${r.tester_code}` : '') + (r.notified ? ` · powiadomienie: ${r.notified.join(', ') || 'brak kanału (zgłaszający bez konta, e-mail wyłączony)'}` : '');
    } catch(e){ $('#f18Msg').textContent = '⚠️ ' + e.message; }
  });
  const c = $('#f18AdminCnt'); if (c) c.textContent = d.unread ? ` (${d.unread} nowe)` : '';
}
const box = document.getElementById('f18Admin');
if (box) box.addEventListener('toggle', () => { if (box.open) api().then(render).catch(e => { $('#f18AdminBody').textContent = '⚠️ ' + e.message; }); });
})();
