/* Luna – tryb producenta (panel administracyjny). Kod jest sprawdzany wyłącznie na serwerze. */
(() => {
const $ = s => document.querySelector(s);
const adm = $('#admin'), TXT = ['system_prompt','style_notes','greeting','wake_reply','ai_first','ai_tag','chat_notice'];
const tok = () => sessionStorage.getItem('luna.admin') || '';
let meta = {};
function msg(t, bad){ const m = $('#admMsg'); m.textContent = t; m.style.color = bad ? '#ff8a7a' : '#7dffa8'; }
async function api(path, body){
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers:{'Content-Type':'application/json','X-Admin-Token':tok()}, body: body ? JSON.stringify(body) : undefined});
  if (r.status === 401){ sessionStorage.removeItem('luna.admin'); if (adm.open) adm.close(); alert('Sesja producenta wygasła. Wpisz kod ponownie w czacie.'); throw new Error('401'); }
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function esc(s){ return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function kbItem(o = {keywords:[], answer:''}){
  const d = document.createElement('div'); d.className = 'item kb';
  d.innerHTML = `<button type="button" class="del" title="Usuń">✕</button>
    <label>Słowa kluczowe (po przecinku)<input type="text" class="kw" value="${esc(o.keywords.join(', '))}"></label>
    <label>Odpowiedź<textarea class="ans" rows="3">${esc(o.answer)}</textarea></label>`;
  d.querySelector('.del').onclick = () => d.remove(); $('#kbList').appendChild(d);
}
function ruleItem(o = {trigger:'', reply:'', match:'zawiera'}){
  const d = document.createElement('div'); d.className = 'item rule';
  d.innerHTML = `<button type="button" class="del" title="Usuń">✕</button>
    <label>Fraza / komenda<input type="text" class="tr" value="${esc(o.trigger)}"></label>
    <label>Dopasowanie<select class="mt"><option value="zawiera">wiadomość zawiera frazę</option><option value="dokladnie">dokładnie ta fraza</option></select></label>
    <label>Odpowiedź Luny<textarea class="rp" rows="2">${esc(o.reply)}</textarea></label>`;
  d.querySelector('.mt').value = o.match; d.querySelector('.del').onclick = () => d.remove(); $('#ruleList').appendChild(d);
}
const V = [['pitch', v => (v > 0 ? '+' : '') + v + ' półt.'], ['rate', v => (v > 0 ? '+' : '') + v + '%'], ['warmth', v => Math.round(v * 10) + '%'], ['volume', v => Math.round((+v + 36) / 20 * 100) + '%'], ['hz', v => v + ' Hz'], ['rasp', v => Math.round(v * 10) + '%'], ['breath', v => Math.round(v * 10) + '%']];
const CHRYPKA = {voice:'pl-PL-ZofiaNeural', pitch:-1.6, hz:-14, rate:-10, warmth:6, volume:-31, rasp:4, breath:5, lisp:true, spanish:true};
function labels(){ V.forEach(([k, f]) => $('#adm_v_' + k + '_v').textContent = f($('#adm_v_' + k).value)); $('#adm_pulse_v').textContent = $('#adm_pulse_speed').value + ' s'; }
let MUS = [];
function musRender(){
  const el = $('#musList'); el.innerHTML = '';
  MUS.forEach((t, i) => { const d = document.createElement('div'); d.className = 'item';
    d.innerHTML = `<button type="button" class="del" title="Usuń">✕</button><b>${esc(t.title)}</b> – ${esc(t.artist)}<br><small>${esc(t.license)} · ${esc(t.url)}</small>
      <div><button type="button" class="add up">↑</button> <button type="button" class="add pl">▶</button></div>`;
    d.querySelector('.del').onclick = () => { MUS.splice(i, 1); musRender(); };
    d.querySelector('.up').onclick = () => { if (i) { [MUS[i-1], MUS[i]] = [MUS[i], MUS[i-1]]; musRender(); } };
    d.querySelector('.pl').onclick = () => { const au = new Audio(t.url); au.volume = .4; au.play(); setTimeout(() => au.pause(), 8000); };
    el.appendChild(d); });
}
function fill(c){
  TXT.forEach(k => $('#adm_' + k).value = c[k] || '');
  $('#adm_tone').value = c.tone; $('#adm_length').value = c.length;
  $('#kbList').innerHTML = ''; (c.kb_topics || []).forEach(kbItem);
  $('#ruleList').innerHTML = ''; (c.rules || []).forEach(ruleItem);
  const vs = $('#adm_v_voice'); if (!vs.options.length) for (const [k, v] of Object.entries(meta.voices || {})){ const o = document.createElement('option'); o.value = k; o.textContent = v; vs.appendChild(o); }
  const vd = c.voice_defaults; vs.value = vd.voice; V.forEach(([k]) => $('#adm_v_' + k).value = vd[k] ?? CHRYPKA[k]); $('#adm_v_spanish').checked = vd.spanish; $('#adm_v_lisp').checked = !!vd.lisp;
  MUS = JSON.parse(JSON.stringify((c.music && c.music.tracks) || [])); musRender(); $('#adm_mvol').value = c.music ? c.music.volume : .25; $('#adm_mvol_v').textContent = Math.round($('#adm_mvol').value * 100) + '%';
  $('#adm_holo_default').checked = !!c.ui.holo_default; $('#adm_holo_plan').value = c.ui.holo_plan || 'podstawowa';
  const lv = c.live || {}; $('#adm_lv_day').value = lv.day ?? 6; $('#adm_lv_time').value = lv.time || '20:00'; $('#adm_lv_hours').value = lv.hours ?? 3; $('#adm_lv_note').value = lv.note || ''; $('#adm_lv_pool').checked = lv.pool !== false; $('#adm_lv_auto').checked = lv.auto !== false;
  const pr = c.pricing || {plans: {}}; $('#adm_pr_show').checked = !!pr.show; $('#adm_app_play').value = (c.app && c.app.play_url) || ''; $('#adm_pr_foreign').checked = !!pr.foreign;
  ['podstawowa', 'premium', 'pro'].forEach(p => ['pln', 'eur', 'usd'].forEach(k => $(`#adm_pr_${p}_${k}`).value = (pr.plans[p] || {})[k] || ''));
  const fr = c.free || {}; $('#adm_fr_min').value = fr.chat_minutes ?? 5; $('#adm_fr_live').checked = !!fr.live_questions; $('#adm_fr_convo').checked = fr.convo !== false; $('#adm_fr_voice').checked = fr.voice_test !== false;
  const se = c.seller || {}; ['name', 'address', 'nip', 'vat'].forEach(k => $('#adm_se_' + k).value = se[k] || '');
  const su = c.support || {}; ['holder', 'iban', 'title'].forEach(k => $('#adm_su_' + k).value = su[k] || '');
  const ca = c.casting || {}; $('#adm_ca_start').value = ca.start || ''; $('#adm_ca_end').value = ca.end || ''; $('#adm_ca_final').value = (ca.final || '').length === 10 ? ca.final + 'T18:00' : (ca.final || ''); $('#adm_ca_xmas').checked = ca.xmas !== false;
  window.LunaGenAdminFill && window.LunaGenAdminFill(c);
  $('#adm_ring_color').value = c.ui.ring_color; $('#adm_pulse_speed').value = c.ui.pulse_speed; labels();
}
function collect(){
  const c = {}; TXT.forEach(k => c[k] = $('#adm_' + k).value);
  c.tone = $('#adm_tone').value; c.length = $('#adm_length').value;
  c.kb_topics = [...document.querySelectorAll('#kbList .item')].map(d => ({keywords: d.querySelector('.kw').value.split(',').map(s => s.trim()).filter(Boolean), answer: d.querySelector('.ans').value.trim()})).filter(o => o.keywords.length && o.answer);
  c.rules = [...document.querySelectorAll('#ruleList .item')].map(d => ({trigger: d.querySelector('.tr').value.trim(), match: d.querySelector('.mt').value, reply: d.querySelector('.rp').value.trim()})).filter(o => o.trigger && o.reply);
  c.voice_defaults = {voice: $('#adm_v_voice').value, spanish: $('#adm_v_spanish').checked, lisp: $('#adm_v_lisp').checked}; V.forEach(([k]) => c.voice_defaults[k] = parseFloat($('#adm_v_' + k).value));
  c.live = {day: +$('#adm_lv_day').value, time: $('#adm_lv_time').value, hours: parseFloat($('#adm_lv_hours').value), note: $('#adm_lv_note').value, pool: $('#adm_lv_pool').checked, auto: $('#adm_lv_auto').checked};
  c.music = {volume: parseFloat($('#adm_mvol').value), tracks: MUS};
  c.ui = {ring_color: $('#adm_ring_color').value, pulse_speed: parseFloat($('#adm_pulse_speed').value), holo_default: $('#adm_holo_default').checked, holo_plan: $('#adm_holo_plan').value};
  c.app = {play_url: $('#adm_app_play').value.trim()}; c.pricing = {v: 2, show: $('#adm_pr_show').checked, foreign: $('#adm_pr_foreign').checked, plans: {}};
  ['podstawowa', 'premium', 'pro'].forEach(p => { c.pricing.plans[p] = {}; ['pln', 'eur', 'usd'].forEach(k => c.pricing.plans[p][k] = $(`#adm_pr_${p}_${k}`).value.trim()); });
  c.free = {chat_minutes: +$('#adm_fr_min').value, live_questions: $('#adm_fr_live').checked, convo: $('#adm_fr_convo').checked, voice_test: $('#adm_fr_voice').checked, outfits: 1};
  c.seller = {}; ['name', 'address', 'nip', 'vat'].forEach(k => c.seller[k] = $('#adm_se_' + k).value.trim());
  c.support = {}; ['holder', 'iban', 'title'].forEach(k => c.support[k] = $('#adm_su_' + k).value.trim());
  c.casting = {start: $('#adm_ca_start').value, end: $('#adm_ca_end').value, final: $('#adm_ca_final').value, xmas: $('#adm_ca_xmas').checked};
  if (window.LunaGenAdminCollect) c.gen = window.LunaGenAdminCollect();
  return c;
}
function applied(c){ fill(c); window.LunaApplyConfig && window.LunaApplyConfig(c); window.LunaMusicConfig && window.LunaMusicConfig(c.music); window.LunaHoloConfig && window.LunaHoloConfig(c.ui); }
async function open(){
  try { meta = await api('/api/admin/config'); $('#adm_safety').textContent = meta.safety_line; fill(meta.config); msg(''); adm.showModal(); } catch(e){ console.error('admin open', e); }
}
adm.addEventListener('input', e => { if (e.target.type === 'range') labels(); if (e.target.id === 'adm_ring_color' || e.target.id === 'adm_pulse_speed') window.LunaApplyConfig && window.LunaApplyConfig({ui:{ring_color: $('#adm_ring_color').value, pulse_speed: parseFloat($('#adm_pulse_speed').value)}}); });
$('#kbAdd').onclick = () => kbItem(); $('#ruleAdd').onclick = () => ruleItem();
$('#admSave').onclick = async () => { try { const d = await api('/api/admin/config', {config: collect()}); applied(d.config); msg('Zapisano ✔'); } catch(e){ if (e.message !== '401') msg('Błąd zapisu: ' + e.message, true); } };
$('#admReset').onclick = async () => { if (!confirm('Przywrócić wszystkie domyślne ustawienia Luny?')) return; try { const d = await api('/api/admin/reset', {}); applied(d.config); msg('Przywrócono domyślne ✔'); } catch(e){ if (e.message !== '401') msg('Błąd: ' + e.message, true); } };
$('#admLogout').onclick = async () => { try { await api('/api/admin/logout', {}); } catch(e){} sessionStorage.removeItem('luna.admin'); adm.close(); };
$('#admExport').onclick = () => { const b = new Blob([JSON.stringify(collect(), null, 2)], {type:'application/json'}); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'luna-konfiguracja.json'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); msg('Wyeksportowano plik luna-konfiguracja.json'); };
$('#admImport').onchange = async e => { const f = e.target.files[0]; if (!f) return; try { const c = JSON.parse(await f.text()); const d = await api('/api/admin/config', {config: c}); applied(d.config); msg('Zaimportowano i zapisano ✔'); } catch(err){ if (err.message !== '401') msg('Nie udało się zaimportować: ' + err.message, true); } e.target.value = ''; };
$('#adm_mvol').oninput = e => $('#adm_mvol_v').textContent = Math.round(e.target.value * 100) + '%';
$('#musFile').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  const title = $('#musTitle').value.trim(), artist = $('#musArtist').value.trim(), license = $('#musLic').value.trim();
  if (!title || !artist || !license) return msg('Podaj tytuł, autora i licencję utworu.', true);
  if (!confirm('Potwierdzasz, że licencja pozwala na użycie utworu w aplikacji (np. CC0, CC BY, domena publiczna)?')) return;
  const data = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); });
  try { const d = await api('/api/admin/upload', {name: f.name, data});
    MUS.push({title, artist, license, url: d.url, source: $('#musSrc').value.trim()}); musRender();
    ['#musTitle', '#musArtist', '#musLic', '#musSrc'].forEach(s => $(s).value = ''); msg('Dodano utwór – kliknij „Zapisz”.');
  } catch(err){ if (err.message !== '401') msg('Błąd wgrywania: ' + err.message, true); }
};
window.LunaAdmin = {open};
if (tok()) {/* sesja aktywna – panel otworzy się po ponownym wpisaniu kodu lub z konsoli */}
document.querySelector('#adm_v_preset').onclick = () => { const q = s => document.querySelector(s); q('#adm_v_voice').value = CHRYPKA.voice; V.forEach(([k]) => q('#adm_v_' + k).value = CHRYPKA[k]); q('#adm_v_lisp').checked = true; q('#adm_v_spanish').checked = true; labels(); };
document.querySelector('#adm_v_test').onclick = () => { const q = s => document.querySelector(s); const p = new URLSearchParams({text: 'Słyszę cię, cariño. Szczególnie cieszę się, że ćwiczysz.', voice: q('#adm_v_voice').value, spanish: q('#adm_v_spanish').checked ? 1 : 0, lisp: q('#adm_v_lisp').checked ? 1 : 0}); V.forEach(([k]) => p.set(k, q('#adm_v_' + k).value)); new Audio('/api/tts?' + p).play(); };
})();
