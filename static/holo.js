/* Tryb hologram – efekt CSS + Canvas nad awatarem; pierścienie reagują na dźwięk mowy (WebAudio). */
(() => {
const $ = s => document.querySelector(s);
const cv = $('#holoCanvas'), g = cv.getContext('2d'), player = $('#player');
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
let on = false, raf = 0, actx = null, an = null, buf = null, parts = [];
let H = {plan: 'podstawowa', def: false};
const S = () => JSON.parse(localStorage.getItem('luna.settings') || '{}');
const allowed = () => !window.LunaHas || window.LunaHas(H.plan);
function want(){ const s = S(); return allowed() && (s.holo ?? H.def); }
function ensureAudio(){
  if (actx) return;
  try {
    actx = new (window.AudioContext || window.webkitAudioContext)();
    const src = actx.createMediaElementSource(player); an = actx.createAnalyser(); an.fftSize = 256;
    src.connect(an); an.connect(actx.destination); buf = new Uint8Array(an.frequencyBinCount);
  } catch(e){ an = null; }
}
player.addEventListener('play', () => { if (on){ ensureAudio(); actx && actx.resume(); } });
function level(){ if (!an || !document.body.classList.contains('speaking')) return 0; an.getByteFrequencyData(buf); let s = 0; for (let i = 2; i < 40; i++) s += buf[i]; return s / (38 * 255); }
function size(){ const r = cv.parentElement.getBoundingClientRect(), d = devicePixelRatio || 1; cv.width = r.width * 1.8 * d; cv.height = r.height * 1.8 * d; }
function frame(t){
  const W = cv.width, Hh = cv.height, cx = W / 2, cy = Hh / 2, d = devicePixelRatio || 1, R = Math.min(W, Hh) / 3.6;
  g.clearRect(0, 0, W, Hh);
  const lv = level(), speaking = document.body.classList.contains('speaking');
  // pierścienie fal dźwiękowych
  if (speaking){
    for (let i = 0; i < 3; i++){
      const p = ((t / 1400 + i / 3) % 1), r = R * (1.02 + p * 0.55 + lv * 0.35);
      g.strokeStyle = `rgba(90,255,240,${(1 - p) * (0.35 + lv)})`; g.lineWidth = (2 + lv * 6) * d;
      g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.stroke();
    }
  }
  // cząsteczki światła
  if (!reduce.matches){
    if (parts.length < 40 && Math.random() < 0.5) parts.push({x: cx + (Math.random() - .5) * R * 1.6, y: cy + R * 1.25, v: (0.3 + Math.random() * 0.7) * d, a: 1, s: (1 + Math.random() * 2) * d});
    parts.forEach(p => { p.y -= p.v * (1 + lv * 3); p.a -= 0.006; g.fillStyle = `rgba(150,255,250,${Math.max(0, p.a) * 0.7})`; g.beginPath(); g.arc(p.x, p.y, p.s, 0, 7); g.fill(); });
    parts = parts.filter(p => p.a > 0);
  }
  raf = requestAnimationFrame(frame);
}
function set(v){
  on = v; document.body.classList.toggle('holo', on);
  cancelAnimationFrame(raf); g.clearRect(0, 0, cv.width, cv.height); parts = [];
  if (on){ size(); raf = requestAnimationFrame(frame); }
}
addEventListener('resize', () => on && size());
new ResizeObserver(() => on && size()).observe(cv.parentElement);
const chk = $('#holoChk');
function sync(){
  const ok = allowed(); chk.disabled = !ok;
  $('#holoTag').textContent = ok ? '' : '🔒 ' + ({podstawowa: 'Podstawowa', premium: 'Premium', pro: 'Pro / Ultra'}[H.plan]);
  chk.checked = want(); set(want());
}
chk.onchange = () => { const s = S(); s.holo = chk.checked; localStorage.setItem('luna.settings', JSON.stringify(s)); set(want()); };
window.LunaHoloConfig = ui => { if (ui){ H.plan = ui.holo_plan || 'podstawowa'; H.def = !!ui.holo_default; } sync(); };
document.getElementById('settingsBtn').addEventListener('click', sync);
document.getElementById('c_plan') && document.getElementById('c_plan').addEventListener('change', () => setTimeout(sync, 0));
fetch('/api/config').then(r => r.json()).then(c => window.LunaHoloConfig(c.ui)).catch(() => sync());
})();
