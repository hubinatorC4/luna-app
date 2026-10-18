/* Casting „Twarz AI”: terminy, odliczanie, zamknięcie zgłoszeń, motyw świąteczny (1 grudnia → finał). */
(() => {
const $ = s => document.querySelector(s);
const pad = n => String(n).padStart(2, '0');
const fmt = ms => new Date(ms).toLocaleString(document.documentElement.lang || 'pl', {timeZone: 'Europe/Warsaw', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'});
fetch('/api/casting').then(r => r.json()).then(c => {
  const off = c.now - Date.now();
  const show = () => {
    $('#cDates').textContent = `${fmt(c.start)} – ${fmt(c.end)} (Europe/Warsaw)`;
    if (c.final) $('#cFinal').textContent = fmt(c.final);
  };
  show(); window.addEventListener('luna-lang', show);
  if (c.xmas){ document.body.classList.add('xmas'); document.querySelectorAll('.xmas-only').forEach(e => e.hidden = false); snow(); }
  const tick = () => {
    const left = c.end - (Date.now() + off);
    if (left <= 0){ $('#countdown').hidden = true; $('#cClosed').hidden = false; $('#castForm').hidden = true; return; }
    const s = Math.floor(left / 1000);
    $('#cdD').textContent = Math.floor(s / 86400); $('#cdH').textContent = pad(Math.floor(s % 86400 / 3600)); $('#cdM').textContent = pad(Math.floor(s % 3600 / 60)); $('#cdS').textContent = pad(s % 60);
    setTimeout(tick, 1000);
  };
  tick();
}).catch(() => {});
function snow(){
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const box = document.querySelector('.snow'); if (!box) return;
  for (let i = 0; i < 28; i++){ const f = document.createElement('i'); f.style.left = (Math.random() * 100) + 'vw'; f.style.animationDuration = (9 + Math.random() * 10) + 's'; f.style.animationDelay = (-Math.random() * 15) + 's'; f.style.opacity = (.35 + Math.random() * .5).toFixed(2); f.style.transform = `scale(${(.5 + Math.random()).toFixed(2)})`; box.appendChild(f); }
}
})();
