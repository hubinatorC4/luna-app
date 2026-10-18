/* Profil użytkownika: imię i awatar. Zasada: tylko obrazy wygenerowane przez AI lub gotowe ikony – bez zdjęć prawdziwych osób.
   Domyślnie: galeria gotowych awatarów/ikon i generator stylizowanego awatara (SVG). Wgrywanie – opcjonalne, sprawdzane na serwerze. */
(() => {
const $ = s => document.querySelector(s);
const COLORS = ['#c87524', '#2e8b57', '#4169e1', '#8e44ad', '#c0392b', '#16a085', '#d4ac0d', '#5d6d7e'];
const ICONS = ['🎤', '🎧', '🎵', '⭐', '🌙', '🦊', '🌿', ''];
let P = Object.assign({name: '', avatar: '', preset: -1, gen: null}, JSON.parse(localStorage.getItem('luna.user') || '{}'));
const save = () => { try { localStorage.setItem('luna.user', JSON.stringify(P)); } catch(e){ alert('Obraz jest za duży.'); } };
function presetSvg(i, name){
  const ch = ICONS[i] || ((name || '?').trim()[0] || '?').toUpperCase();
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><circle cx="64" cy="64" r="64" fill="${COLORS[i]}"/><text x="64" y="${ICONS[i] ? 82 : 84}" font-size="${ICONS[i] ? 60 : 64}" text-anchor="middle" fill="#fff" font-family="system-ui,sans-serif" font-weight="600">${ch.replace(/[<&>]/g, '')}</text></svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
/* ---------- generator stylizowanego awatara (SVG, bez zewnętrznego API) ---------- */
const G = {
  bg: ['#2b1d14', '#1d2b3a', '#2a1f3d', '#1f3a2b', '#3a1f24', '#33301c'],
  skin: ['#f6d7c3', '#eec1a0', '#d9a07a', '#b97b52', '#8d5a3b', '#5e3b26'],
  hair: ['krótkie', 'długie', 'kok', 'kręcone', 'grzywka', 'bez włosów'],
  hairCol: ['#2a1b12', '#5a3820', '#a0652e', '#d9b36a', '#8a8a8a', '#b04a3a', '#3b4a8a'],
  eyes: ['#3b2a1a', '#2f5d8a', '#3f7a4a', '#6a6a6a'],
  top: ['#f0a040', '#2ee66b', '#8B5CF6', '#3B82F6', '#e05a7a', '#e8e0d0'],
  extra: ['brak', 'okulary', 'słuchawki', 'kolczyki']
};
const pick = a => Math.floor(Math.random() * a.length);
function genSvg(g){
  const sk = G.skin[g.skin], hc = G.hairCol[g.hairCol], ey = G.eyes[g.eyes], top = G.top[g.top];
  const hair = {
    'krótkie': `<path d="M34 58c0-22 13-34 30-34s30 12 30 34c-6-10-16-16-30-16s-24 6-30 16z" fill="${hc}"/>`,
    'długie': `<path d="M30 60c0-24 14-38 34-38s34 14 34 38v40c-6 4-12 4-16 0V62c-6-10-12-14-18-14s-12 4-18 14v38c-4 4-10 4-16 0z" fill="${hc}"/>`,
    'kok': `<circle cx="64" cy="22" r="12" fill="${hc}"/><path d="M34 58c0-22 13-32 30-32s30 10 30 32c-6-9-16-14-30-14s-24 5-30 14z" fill="${hc}"/>`,
    'kręcone': [36, 46, 56, 66, 76, 86, 92, 34].map((x, i) => `<circle cx="${x}" cy="${i % 2 ? 34 : 30}" r="11" fill="${hc}"/>`).join('') + `<circle cx="32" cy="50" r="9" fill="${hc}"/><circle cx="96" cy="50" r="9" fill="${hc}"/>`,
    'grzywka': `<path d="M32 62c0-26 14-38 32-38s32 12 32 38c-4-6-8-9-12-10-8-1-12-10-20-12-6 6-20 10-32 22z" fill="${hc}"/>`,
    'bez włosów': ''
  }[G.hair[g.hair]];
  const extra = {
    'okulary': `<g fill="none" stroke="#222" stroke-width="2.5"><circle cx="52" cy="64" r="8"/><circle cx="76" cy="64" r="8"/><path d="M60 64h8"/></g>`,
    'słuchawki': `<path d="M30 66c0-24 14-40 34-40s34 16 34 40" fill="none" stroke="#333" stroke-width="5"/><rect x="24" y="60" width="10" height="18" rx="4" fill="#444"/><rect x="94" y="60" width="10" height="18" rx="4" fill="#444"/>`,
    'kolczyki': `<circle cx="38" cy="78" r="3" fill="#f5d36b"/><circle cx="90" cy="78" r="3" fill="#f5d36b"/>`,
    'brak': ''
  }[G.extra[g.extra]];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><circle cx="64" cy="64" r="64" fill="${G.bg[g.bg]}"/>
<path d="M22 128c4-22 20-32 42-32s38 10 42 32z" fill="${top}"/><rect x="56" y="84" width="16" height="14" fill="${sk}"/>
${G.hair[g.hair] === 'długie' ? hair : ''}<ellipse cx="64" cy="64" rx="26" ry="30" fill="${sk}"/>${G.hair[g.hair] !== 'długie' ? hair : `<path d="M38 58c4-14 14-22 26-22s22 8 26 22c-8-6-16-9-26-9s-18 3-26 9z" fill="${hc}"/>`}
<ellipse cx="52" cy="65" rx="3.6" ry="4.2" fill="${ey}"/><ellipse cx="76" cy="65" rx="3.6" ry="4.2" fill="${ey}"/>
<path d="M56 79c4 4 12 4 16 0" fill="none" stroke="#7a3b2e" stroke-width="2.5" stroke-linecap="round"/><circle cx="46" cy="74" r="4" fill="#e88" opacity=".25"/><circle cx="82" cy="74" r="4" fill="#e88" opacity=".25"/>${extra}</svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
const GALLERY = [
  {bg: 0, skin: 1, hair: 1, hairCol: 1, eyes: 0, top: 0, extra: 3}, {bg: 1, skin: 3, hair: 0, hairCol: 0, eyes: 0, top: 3, extra: 0},
  {bg: 2, skin: 0, hair: 2, hairCol: 3, eyes: 1, top: 2, extra: 0}, {bg: 3, skin: 4, hair: 3, hairCol: 0, eyes: 0, top: 1, extra: 2},
  {bg: 4, skin: 2, hair: 4, hairCol: 5, eyes: 2, top: 4, extra: 1}, {bg: 5, skin: 5, hair: 5, hairCol: 0, eyes: 0, top: 5, extra: 2}
];
window.UserAvatarSrc = () => P.avatar || (P.gen ? genSvg(P.gen) : '') || (P.preset >= 0 ? presetSvg(P.preset, P.name) : '');
window.UserName = () => P.name;
function btn(src, on, alt, fn){ const b = document.createElement('button'); b.type = 'button'; b.className = on ? 'on' : ''; const i = document.createElement('img'); i.src = src; i.alt = alt; b.appendChild(i); b.onclick = fn; return b; }
function render(){
  $('#u_name').value = P.name;
  const box = $('#u_presets'); box.innerHTML = '';
  if (P.avatar) box.appendChild(btn(P.avatar, true, 'Twój obraz AI', () => {}));
  GALLERY.forEach((g, i) => box.appendChild(btn(genSvg(g), !P.avatar && P.gen && JSON.stringify(P.gen) === JSON.stringify(g), 'Gotowy awatar ' + (i + 1), () => { P.gen = Object.assign({}, g); P.avatar = ''; P.preset = -1; save(); render(); refresh(); })));
  COLORS.forEach((c, i) => box.appendChild(btn(presetSvg(i, P.name), !P.avatar && !P.gen && P.preset === i, 'Ikona ' + (i + 1), () => { P.preset = i; P.avatar = ''; P.gen = null; save(); render(); refresh(); })));
  renderGen();
}
function renderGen(){
  const g = P.gen || GALLERY[0]; const box = $('#u_gen'); if (!box) return;
  $('#u_genPrev').src = genSvg(g);
  box.innerHTML = '';
  [['hair', 'Fryzura', G.hair], ['hairCol', 'Kolor włosów', G.hairCol], ['skin', 'Odcień skóry', G.skin], ['eyes', 'Oczy', G.eyes], ['top', 'Ubranie', G.top], ['bg', 'Tło', G.bg], ['extra', 'Dodatek', G.extra]].forEach(([k, label, arr]) => {
    const l = document.createElement('label'); l.textContent = label + ' ';
    const s = document.createElement('select');
    arr.forEach((v, i) => { const o = document.createElement('option'); o.value = i; o.textContent = v.startsWith('#') ? `${label} ${i + 1}` : v; if (v.startsWith('#')) o.style.background = v; s.appendChild(o); });
    s.value = g[k]; s.onchange = () => { P.gen = Object.assign({}, g, {[k]: +s.value}); P.avatar = ''; P.preset = -1; save(); render(); refresh(); };
    l.appendChild(s); box.appendChild(l);
  });
}
const refresh = () => window.LunaRefreshAvatars && window.LunaRefreshAvatars();
$('#u_name').oninput = e => { P.name = e.target.value.replace(/[<>]/g, '').slice(0, 30); save(); render(); refresh(); };
$('#u_clear').onclick = () => { P.avatar = ''; P.preset = -1; P.gen = null; save(); render(); refresh(); };
$('#u_random').onclick = () => { P.gen = {bg: pick(G.bg), skin: pick(G.skin), hair: pick(G.hair), hairCol: pick(G.hairCol), eyes: pick(G.eyes), top: pick(G.top), extra: pick(G.extra)}; P.avatar = ''; P.preset = -1; save(); render(); refresh(); };

/* ---------- opcjonalne wgrywanie obrazu AI: oświadczenie + kontrola na serwerze ---------- */
window.LunaAiUpload = (f, max) => new Promise(res => {
  const decl = $('#u_aiDecl');
  if (!decl || !decl.checked){ alert('Zaznacz najpierw oświadczenie: „Oświadczam, że to obraz wygenerowany przez AI i nie przedstawia prawdziwej osoby”.'); return res(null); }
  if (f.size > 5 * 1024 * 1024){ alert('Plik jest za duży (maks. 5 MB).'); return res(null); }
  const rd = new FileReader();
  rd.onload = async () => {
    try {
      const r = await fetch('/api/avatar/upload', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data: rd.result, ai_declared: true, vid: window.LunaVid ? window.LunaVid() : '', name: P.name})});
      const d = await r.json(); if (!r.ok){ alert('⚠️ ' + (d.error || 'Nie udało się przesłać obrazu.')); return res(null); }
      if (max && max < 256) return res(d.avatar);
      res(d.avatar);
    } catch(e){ alert('Błąd połączenia.'); res(null); }
  };
  rd.readAsDataURL(f);
});
$('#u_upload').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  const url = await window.LunaAiUpload(f, 256);
  if (url){ P.avatar = url; P.gen = null; P.preset = -1; save(); render(); refresh(); }
};
document.getElementById('settingsBtn').addEventListener('click', render);
render(); setTimeout(refresh, 0);
})();
