/* 🎨 Wygląd profilu – tylko dla zweryfikowanych Modelek Luny (rola nadana przez moderatora, sprawdzana na serwerze).
   Układ profilu identyczny dla wszystkich; zmieniają się tylko akcent, tło, czcionka nicku/nagłówków i styl ramki – z katalogu, z kontrolą kontrastu WCAG AA. */
(() => {
const L = (document.documentElement.lang || 'pl').slice(0, 2);
const T = ({
  pl: {h: '🎨 Wygląd profilu', s: 'Przywilej Modelek Luny 💗 Układ zostaje ten sam, Ty dobierasz kolory – jak szminkę do sukienki.', pal: 'Kolor akcentu', bg: 'Tło', font: 'Czcionka nicku i nagłówków', fr: 'Ramka', match: '✨ Dopasuj do agentki', save: 'Zapisz wygląd', saved: 'Zapisano – wyglądasz zjawiskowo 💗', prev: 'Podgląd', nomatch: 'Najpierw dodaj zdjęcie agentki – lustro potrzebuje odbicia 😉', btn: 'Obserwuj'},
  en: {h: '🎨 Profile look', s: 'A Luna Model perk 💗 The layout stays the same – you pick the colours, like lipstick to match the dress.', pal: 'Accent colour', bg: 'Background', font: 'Name and heading font', fr: 'Frame', match: '✨ Match my agent', save: 'Save look', saved: 'Saved – you look stunning 💗', prev: 'Preview', nomatch: 'Add an agent photo first – the mirror needs a reflection 😉', btn: 'Follow'},
  es: {h: '🎨 Aspecto del perfil', s: 'Ventaja de las Modelos de Luna 💗 El diseño es el mismo; tú eliges los colores, como el pintalabios con el vestido.', pal: 'Color de acento', bg: 'Fondo', font: 'Fuente del nombre y títulos', fr: 'Marco', match: '✨ Combinar con mi agente', save: 'Guardar aspecto', saved: 'Guardado – estás espectacular 💗', prev: 'Vista previa', nomatch: 'Primero añade una foto de tu agente – el espejo necesita un reflejo 😉', btn: 'Seguir'},
  de: {h: '🎨 Profil-Look', s: 'Ein Vorteil für Luna-Models 💗 Das Layout bleibt gleich – du wählst die Farben, wie den Lippenstift zum Kleid.', pal: 'Akzentfarbe', bg: 'Hintergrund', font: 'Schrift für Name und Überschriften', fr: 'Rahmen', match: '✨ An meine Agentin anpassen', save: 'Look speichern', saved: 'Gespeichert – du siehst umwerfend aus 💗', prev: 'Vorschau', nomatch: 'Füge zuerst ein Foto deiner Agentin hinzu – der Spiegel braucht ein Spiegelbild 😉', btn: 'Folgen'},
  uk: {h: '🎨 Вигляд профілю', s: 'Привілей Моделей Luna 💗 Макет той самий – ви обираєте кольори, як помаду до сукні.', pal: 'Колір акценту', bg: 'Тло', font: 'Шрифт ніку й заголовків', fr: 'Рамка', match: '✨ Підібрати до агентки', save: 'Зберегти вигляд', saved: 'Збережено – ви неймовірні 💗', prev: 'Попередній перегляд', nomatch: 'Спершу додайте фото агентки – дзеркалу потрібне відображення 😉', btn: 'Стежити'}
})[L] || {};
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
let D = null, LK = null, CSRF = '';
const get = p => fetch(p, {credentials: 'same-origin'}).then(r => r.json());
function bgCss(cs){ return cs.length > 1 ? `linear-gradient(135deg,${cs[0]},${cs[1]})` : cs[0]; }
function card(){
  const P = D.presets, pal = P.palettes.find(x => x.id === LK.palette), bg = P.bgs.find(x => x.id === LK.bg), f = P.fonts.find(x => x.id === LK.font);
  const nick = (document.querySelector('.st-nick') || {}).firstChild ? document.querySelector('.st-nick').firstChild.textContent : 'Nick';
  const opt = (k, id, label, sw) => `<button type="button" class="lk-opt" data-k="${k}" data-v="${id}" aria-pressed="${LK[k] === id}">${sw ? `<i class="lk-sw" style="background:${sw}"></i>` : ''}${esc(label)}</button>`;
  return `<section class="lk-card" id="lkCard" aria-labelledby="lkH"><h2 id="lkH">${T.h}</h2><p class="lk-h">${T.s}</p>
   <div class="lk-prev" style="background:${bgCss(bg.colors)};color:${bg.text}" aria-label="${T.prev}"><span class="ava-p mdl-ring fr-${LK.frame}" style="--lk-ac:${pal.color};color:${pal.color}">${esc(nick.trim()[0] || '?')}</span><b style="font-family:${f.css};color:${bg.text}">${esc(nick)}</b> <span class="mdl-badge">💗 Modelka Luny</span><span class="lk-btn" style="background:${pal.color};color:#111">${T.btn}</span></div>
   <b>${T.pal}</b><div class="lk-grid">${P.palettes.map(x => opt('palette', x.id, x.name, x.color)).join('')}</div>
   <b>${T.bg}</b><div class="lk-grid">${P.bgs.map(x => opt('bg', x.id, x.name, bgCss(x.colors))).join('')}</div>
   <b>${T.font}</b><div class="lk-grid">${P.fonts.map(x => opt('font', x.id, x.name)).join('')}</div>
   <b>${T.fr}</b><div class="lk-grid">${P.frames.map(x => opt('frame', x.id, x.name)).join('')}</div>
   <div class="lk-grid"><button type="button" class="st-btn" id="lkMatch">${T.match}</button><button type="button" class="st-btn primary" id="lkSave">${T.save}</button></div><p class="lk-msg" id="lkMsg" role="status"></p></section>`;
}
function draw(){
  const head = document.getElementById('stHead'); if (!head || !D) return;
  const old = document.getElementById('lkCard'); const html = card();
  if (old) old.outerHTML = html; else head.insertAdjacentHTML('afterend', html);
  const c = document.getElementById('lkCard');
  c.querySelectorAll('.lk-opt').forEach(b => b.onclick = () => { LK[b.dataset.k] = b.dataset.v; draw(); });
  c.querySelector('#lkMatch').onclick = async () => { const r = await get('/api/me/look?suggest=1'); if (r.suggest){ LK.palette = r.suggest; draw(); } else document.getElementById('lkMsg').textContent = T.nomatch; };
  c.querySelector('#lkSave').onclick = async () => {
    const m = document.getElementById('lkMsg');
    try { const r = await fetch('/api/me/look', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': CSRF}, body: JSON.stringify(LK)});
      const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status); m.textContent = T.saved; apply(j.view); } catch (e){ m.textContent = '⚠️ ' + e.message; } };
}
function apply(v){
  const head = document.getElementById('stHead'); if (!head || !v) return;
  head.style.background = bgCss(v.bgc); head.style.color = v.text; head.style.borderRadius = '22px'; head.style.padding = head.style.padding || '14px';
  const n = head.querySelector('.st-nick'); if (n) n.style.fontFamily = v.font_css;
  const a = head.querySelector('.st-av'); if (a){ a.classList.add('mdl-ring'); a.classList.remove('fr-podwojna', 'fr-perlowa', 'fr-satyna'); if (v.frame !== 'modelka') a.classList.add('fr-' + v.frame); a.style.setProperty('--lk-ac', v.accent); }
}
async function init(){
  const app = document.getElementById('stApp'); if (!app) return;
  try { D = await get('/api/me/look'); } catch (e){ return; }
  if (!D || !D.model) return;
  try { CSRF = (await get('/api/account/me')).csrf || ''; } catch (e) {}
  LK = Object.assign({}, D.look);
  const run = () => { if (document.getElementById('stHead') && !document.getElementById('lkCard')){ draw(); apply(D.view); } };
  run(); new MutationObserver(run).observe(app, {childList: true});
}
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
