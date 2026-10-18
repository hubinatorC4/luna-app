/* Muzyka w tle – smooth jazz z saksofonem (licencje: /music/LICENSES.md). Start tylko po interakcji użytkownika. */
(() => {
const $ = s => document.querySelector(s);
const a = new Audio(); a.preload = 'none';
let tracks = [], M = Object.assign({on: false, vol: null, i: 0}, JSON.parse(localStorage.getItem('luna.music') || '{}'));
let duck = false, defVol = 0.15;  // v1.6.6: ciche tło ~15 %, domyślnie WYŁ.
const save = () => localStorage.setItem('luna.music', JSON.stringify(M));
const vol = () => (M.vol ?? defVol);
function setVol(){ const target = vol() * (duck ? 0.12 : 1); fade(target); }
let fadeT; function fade(t){ clearInterval(fadeT); fadeT = setInterval(() => { const d = t - a.volume; if (Math.abs(d) < 0.02){ a.volume = Math.max(0, Math.min(1, t)); clearInterval(fadeT); } else a.volume = Math.max(0, Math.min(1, a.volume + d * 0.25)); }, 40); }
function info(){
  const t = tracks[M.i % (tracks.length || 1)];
  $('#musicNow').textContent = t ? '♪ ' + t.title + ' – ' + t.artist : '—';
  $('#musicCredit').innerHTML = t ? `Music: „${t.title}” by ${t.artist}${t.artist === 'Kevin MacLeod' ? ' (incompetech.com)' : ''}, licencja ${t.license}. <a href="/music/LICENSES.md" target="_blank" rel="noopener">Licencje</a>` : '';
  $('#musicBtn').classList.toggle('on', M.on);
}
function load(i){ if (!tracks.length) return; M.i = (i + tracks.length) % tracks.length; save(); a.src = tracks[M.i].url; info(); }
function play(){ if (!tracks.length) return; if (!a.src) load(M.i); a.volume = 0; a.play().then(setVol).catch(() => {}); }
function stop(){ fade(0); setTimeout(() => a.pause(), 400); }
a.addEventListener('ended', () => { load(M.i + 1); play(); });
a.addEventListener('error', () => { if (M.on && tracks.length > 1) { load(M.i + 1); play(); } });
$('#musicBtn').onclick = () => { const p = $('#musicPanel'); p.hidden = !p.hidden; };
$('#musicToggle').onchange = e => { M.on = e.target.checked; save(); info(); M.on ? play() : stop(); };
$('#musicNext').onclick = () => { load(M.i + 1); if (M.on) play(); };
$('#musicVol').oninput = e => { M.vol = parseFloat(e.target.value); save(); setVol(); };
// wyciszanie, gdy asystentka mówi lub słucha
new MutationObserver(() => { const d = document.body.classList.contains('speaking') || document.body.classList.contains('listening'); if (d !== duck){ duck = d; if (!a.paused) setVol(); } })
  .observe(document.body, {attributes: true, attributeFilter: ['class']});
// v1.6.6: pauza (z wyciszeniem) gdy karta jest w tle albo trwa nagrywanie / rozmowa głosowa / trening – i wznowienie po
let held = false; const hold = h => { if (h === held || !M.on) return; held = h; if (h) stop(); else play(); };
document.addEventListener('visibilitychange', () => hold(document.hidden || document.body.classList.contains('convo') || document.body.classList.contains('listening')));
new MutationObserver(() => hold(document.hidden || document.body.classList.contains('convo') || document.body.classList.contains('listening')))
  .observe(document.body, {attributes: true, attributeFilter: ['class']});
// przeglądarki blokują autoodtwarzanie – wznawiamy po pierwszym dotknięciu
document.addEventListener('pointerdown', () => { if (M.on && a.paused) play(); }, {once: true});
window.LunaMusicConfig = m => {
  if (!m) return; defVol = m.volume ?? defVol; tracks = m.tracks || [];
  $('#musicToggle').checked = M.on; $('#musicVol').value = vol();
  if (M.i >= tracks.length) M.i = 0; if (a.src && !tracks.some(t => a.src.endsWith(t.url))) a.removeAttribute('src');
  info();
};
fetch('/api/config').then(r => r.json()).then(c => window.LunaMusicConfig(c.music)).catch(() => {});
})();
