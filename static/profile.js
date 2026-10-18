/* Profil użytkownika: imię i awatar (zdjęcie przycięte do koła 256 px albo gotowa ikona) – tylko localStorage. */
(() => {
const $ = s => document.querySelector(s);
const COLORS = ['#c87524', '#2e8b57', '#4169e1', '#8e44ad', '#c0392b', '#16a085', '#d4ac0d', '#5d6d7e'];
const ICONS = ['🎤', '🎧', '🎵', '⭐', '🌙', '🦊', '🌿', ''];
let P = Object.assign({name: '', avatar: '', preset: -1}, JSON.parse(localStorage.getItem('luna.user') || '{}'));
const save = () => { try { localStorage.setItem('luna.user', JSON.stringify(P)); } catch(e){ alert('Zdjęcie jest za duże.'); } };
function presetSvg(i, name){
  const ch = ICONS[i] || ((name || '?').trim()[0] || '?').toUpperCase();
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><circle cx="64" cy="64" r="64" fill="${COLORS[i]}"/><text x="64" y="${ICONS[i] ? 82 : 84}" font-size="${ICONS[i] ? 60 : 64}" text-anchor="middle" fill="#fff" font-family="system-ui,sans-serif" font-weight="600">${ch.replace(/[<&>]/g, '')}</text></svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
window.UserAvatarSrc = () => P.avatar || (P.preset >= 0 ? presetSvg(P.preset, P.name) : '');
window.UserName = () => P.name;
function render(){
  $('#u_name').value = P.name;
  const box = $('#u_presets'); box.innerHTML = '';
  COLORS.forEach((c, i) => { const b = document.createElement('button'); b.type = 'button'; b.className = P.preset === i && !P.avatar ? 'on' : '';
    b.innerHTML = `<img src="${presetSvg(i, P.name)}" alt="Awatar ${i + 1}">`; b.onclick = () => { P.preset = i; P.avatar = ''; save(); render(); refresh(); }; box.appendChild(b); });
  if (P.avatar){ const b = document.createElement('button'); b.type = 'button'; b.className = 'on'; b.innerHTML = `<img src="${P.avatar}" alt="Twoje zdjęcie">`; box.prepend(b); }
}
const refresh = () => window.LunaRefreshAvatars && window.LunaRefreshAvatars();
$('#u_name').oninput = e => { P.name = e.target.value.replace(/[<>]/g, '').slice(0, 30); save(); render(); refresh(); };
$('#u_clear').onclick = () => { P.avatar = ''; P.preset = -1; save(); render(); refresh(); };
$('#u_upload').onchange = e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  if (f.size > 10 * 1024 * 1024) return alert('Plik jest za duży (maks. 10 MB).');
  const img = new Image(); img.onload = () => {
    const s = Math.min(img.width, img.height), cv = document.createElement('canvas'); cv.width = cv.height = 256;
    const g = cv.getContext('2d'); g.beginPath(); g.arc(128, 128, 128, 0, Math.PI * 2); g.clip();
    g.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 256, 256);
    P.avatar = cv.toDataURL('image/webp', 0.85); if (P.avatar.length < 100) P.avatar = cv.toDataURL('image/png');
    save(); render(); refresh(); URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(f);
};
document.getElementById('settingsBtn').addEventListener('click', render);
render(); setTimeout(refresh, 0);
})();
