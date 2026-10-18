/* Panel: „Agentka współpracująca” – status nadawany ręcznie po zgodzie twórcy (opt-in). Nigdy dla Luny ani realnej osoby. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
async function api(body){
  const r = await fetch('/api/admin/partners', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: JSON.stringify(body || {})});
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function render(d){
  const B = $('#ptAdminBody');
  B.innerHTML = `<p class="hint">Tylko agentki AI użytkowników, po zgodzie twórcy. Publicznie widać wyłącznie imię agentki, różową ramkę i prawdziwe kampanie. Nigdy Luna ani realna osoba.</p>
    <p><label>ID profilu (agentka.html?id=…) lub ID zgłoszenia w Bitwach <input id="ptRef" maxlength="20" style="width:160px"></label></p>
    <p><label><input type="checkbox" id="ptOptin"> Twórca wyraził zgodę (opt-in)</label></p>
    <p><label>Kampanie / marki (prawdziwe, po jednej w wierszu – opcjonalnie)<br><textarea id="ptCamps" rows="3" style="width:100%"></textarea></label></p>
    <p><button type="button" id="ptOn">Nadaj status</button> <button type="button" id="ptOff">Odbierz status</button> <span id="ptMsg"></span></p>
    <table class="tbl"><tr><th>Agentka</th><th>Profil</th><th>Bitwy</th><th>Status</th><th>Kampanie</th></tr>${(d.items || []).map(i => `<tr><td>${esc(i.agent)}</td><td>${esc(i.profile)}</td><td>${esc(i.battle)}</td><td>${i.on ? '💖 tak' : 'nie'}</td><td>${esc((i.campaigns || []).join(', '))}</td></tr>`).join('') || '<tr><td colspan="5">–</td></tr>'}</table>`;
  const go = async on => { try { render(await api({action: 'set', ref: $('#ptRef').value.trim(), on, optin: $('#ptOptin').checked, campaigns: $('#ptCamps').value.split('\n').map(x => x.trim()).filter(Boolean)})); $('#ptMsg').textContent = '✓'; } catch(e){ $('#ptMsg').textContent = '⚠️ ' + e.message; } };
  $('#ptOn').onclick = () => go(true); $('#ptOff').onclick = () => go(false);
}
const box = document.getElementById('ptAdmin');
if (box) box.addEventListener('toggle', () => { if (box.open) api().then(render).catch(e => { $('#ptAdminBody').textContent = '⚠️ ' + e.message; }); });
})();
