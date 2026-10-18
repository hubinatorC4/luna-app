/* Przełącznik języka z flagami w nagłówku każdej strony; wybór zapamiętany, adres ?lang=xx (indeksowalny). */
(() => {
try { const r = new URLSearchParams(location.search).get('ref'); if (r && /^[a-z0-9]{5,12}$/.test(r)) localStorage.setItem('luna.ref', r); } catch(e){}
const L0 = [['pl', '🇵🇱', 'Polski'], ['en', '🇬🇧', 'English'], ['es', '🇪🇸', 'Español'], ['de', '🇩🇪', 'Deutsch'], ['uk', '🇺🇦', 'Українська']];
/* Pakiet językowy: [kod, flaga, nazwa natywna, nazwa po polsku, nazwa po angielsku, grupa] – wybór pogrupowany i z wyszukiwarką */
const ALLL = [['pl','🇵🇱','Polski','polski','Polish','c'],['en','🇬🇧','English','angielski','English','w'],['es','🇪🇸','Español','hiszpański','Spanish','w'],['de','🇩🇪','Deutsch','niemiecki','German','w'],['uk','🇺🇦','Українська','ukraiński','Ukrainian','e'],
 ['fr','🇫🇷','Français','francuski','French','w'],['it','🇮🇹','Italiano','włoski','Italian','w'],['pt','🇵🇹','Português (Portugal)','portugalski (Portugalia)','Portuguese (Portugal)','w'],['pt-br','🇧🇷','Português (Brasil)','portugalski (Brazylia)','Portuguese (Brazil)','w'],['nl','🇳🇱','Nederlands','niderlandzki','Dutch','w'],
 ['cs','🇨🇿','Čeština','czeski','Czech','c'],['sk','🇸🇰','Slovenčina','słowacki','Slovak','c'],['hu','🇭🇺','Magyar','węgierski','Hungarian','c'],['ro','🇷🇴','Română','rumuński','Romanian','c'],
 ['sv','🇸🇪','Svenska','szwedzki','Swedish','n'],['no','🇳🇴','Norsk (bokmål)','norweski','Norwegian','n'],['da','🇩🇰','Dansk','duński','Danish','n'],['fi','🇫🇮','Suomi','fiński','Finnish','n'],['et','🇪🇪','Eesti','estoński','Estonian','n'],['lv','🇱🇻','Latviešu','łotewski','Latvian','n'],['lt','🇱🇹','Lietuvių','litewski','Lithuanian','n'],
 ['el','🇬🇷','Ελληνικά','grecki','Greek','s'],['bg','🇧🇬','Български','bułgarski','Bulgarian','s'],['hr','🇭🇷','Hrvatski','chorwacki','Croatian','s'],['sr','🇷🇸','Српски','serbski','Serbian','s'],
 ['ru','🌐','Русский','rosyjski','Russian','e'],['tr','🇹🇷','Türkçe','turecki','Turkish','m'],['ar','🌐','العربية','arabski','Arabic','m'],['he','🇮🇱','עברית','hebrajski','Hebrew','m'],
 ['hi','🇮🇳','हिन्दी','hindi','Hindi','a'],['id','🇮🇩','Bahasa Indonesia','indonezyjski','Indonesian','a'],['vi','🇻🇳','Tiếng Việt','wietnamski','Vietnamese','a'],['th','🇹🇭','ไทย','tajski','Thai','a'],['ja','🇯🇵','日本語','japoński','Japanese','a'],['ko','🇰🇷','한국어','koreański','Korean','a'],['zh','🇨🇳','简体中文','chiński (uproszczony)','Chinese (Simplified)','a']];
const ON = (document.documentElement.getAttribute('data-luna-langs') || 'pl,en,es,de,uk').split(',');
const L = ALLL.filter(x => ON.includes(x[0])).map(x => [x[0], x[1], x[2]]);
const GR = {pl: {w: 'Europa Zachodnia', c: 'Europa Środkowa', n: 'Europa Północna i Bałtyk', s: 'Europa Południowa i Bałkany', e: 'Europa Wschodnia', m: 'Bliski Wschód', a: 'Azja'},
 en: {w: 'Western Europe', c: 'Central Europe', n: 'Northern Europe & Baltics', s: 'Southern Europe & Balkans', e: 'Eastern Europe', m: 'Middle East', a: 'Asia'},
 es: {w: 'Europa occidental', c: 'Europa central', n: 'Europa del Norte y Bálticos', s: 'Europa del Sur y Balcanes', e: 'Europa del Este', m: 'Oriente Medio', a: 'Asia'},
 de: {w: 'Westeuropa', c: 'Mitteleuropa', n: 'Nordeuropa & Baltikum', s: 'Südeuropa & Balkan', e: 'Osteuropa', m: 'Naher Osten', a: 'Asien'},
 uk: {w: 'Західна Європа', c: 'Центральна Європа', n: 'Північна Європа та Балтія', s: 'Південна Європа та Балкани', e: 'Східна Європа', m: 'Близький Схід', a: 'Азія'}};
const PICK = {pl: ['Język', 'Szukaj języka…', 'Nic nie znalazłam – spróbuj inaczej 🙂', 'Tłumaczenie maszynowe – sprawdzamy je z ludźmi'], en: ['Language', 'Search languages…', 'Nothing found – try another spelling 🙂', 'Machine translation – being reviewed by humans'],
 es: ['Idioma', 'Buscar idioma…', 'No encontré nada, prueba otra forma 🙂', 'Traducción automática, en revisión humana'], de: ['Sprache', 'Sprache suchen…', 'Nichts gefunden – versuch es anders 🙂', 'Maschinelle Übersetzung – wird von Menschen geprüft'],
 uk: ['Мова', 'Пошук мови…', 'Нічого не знайшла – спробуйте інакше 🙂', 'Машинний переклад – перевіряємо з людьми']};
const APP = location.pathname === '/app' || location.pathname === '/index.html' || document.documentElement.hasAttribute('data-app');
const q = new URLSearchParams(location.search).get('lang');
let saved = null; try { saved = localStorage.getItem('luna.lang'); } catch(e){}
const MAPL = c => { c = String(c || '').toLowerCase().replace('_', '-'); if (!c) return '';
  if (c.startsWith('pt-br')) return ON.includes('pt-br') ? 'pt-br' : 'pt'; if (c.startsWith('zh')) return /hant|-tw|-hk|-mo/.test(c) || !ON.includes('zh') ? '' : 'zh';
  let b = c.split('-')[0]; b = ({nb: 'no', nn: 'no', iw: 'he', in: 'id'})[b] || b; return L.some(x => x[0] === b) ? b : ({ru: 'en', be: 'en'})[b] || ''; };
const SRV = document.documentElement.getAttribute('data-luna-lang') || MAPL(document.documentElement.lang) || 'pl';  // język wyrenderowany przez serwer (konto → ciasteczko → Accept-Language)
if (q && L.some(x => x[0] === q)){ /* ?lang=xx w adresie – bez nadpisywania zapisanego wyboru (zapis tylko po kliknięciu flagi) */ }
else if (APP){ /* aplikacja: język ustala app-shell.js */ }
else { const want = MAPL(saved) || (navigator.languages || [navigator.language]).map(MAPL).find(Boolean) || 'pl';
  if (want !== SRV && !location.pathname.startsWith('/api')){ const u = new URL(location.href); u.searchParams.set('lang', want); location.replace(u); return; } }
const cur = q || MAPL(saved) || SRV || 'pl';
const NAV = {
 en: {'/promo.html': 'Tips', '/butik.html': 'Boutique', '/scianka.html': 'Wall', '/galeria.html': 'Agents gallery', '/live.html': 'Luna Live', '/testerzy.html': 'Testers', '/dolacz.html': 'Join the project', '/twarz.html': 'AI Face', '/wesprzyj.html': 'Support Luna', '/regulamin.html': 'Terms', '/privacy.html': 'Privacy', '/problemy.html': 'Help', '/app': 'App', '/app#live': 'Chat with the creator'},
 es: {'/promo.html': 'Consejos', '/butik.html': 'Boutique', '/scianka.html': 'Muro', '/galeria.html': 'Galería de agentes', '/live.html': 'Luna Live', '/testerzy.html': 'Testers', '/dolacz.html': 'Únete al proyecto', '/twarz.html': 'Rostro IA', '/wesprzyj.html': 'Apoya a Luna', '/regulamin.html': 'Condiciones', '/privacy.html': 'Privacidad', '/problemy.html': 'Ayuda', '/app': 'App', '/app#live': 'Chat con el creador'},
 de: {'/promo.html': 'Tipps', '/butik.html': 'Boutique', '/scianka.html': 'Pinnwand', '/galeria.html': 'Galerie der Agentinnen', '/live.html': 'Luna Live', '/testerzy.html': 'Tester', '/dolacz.html': 'Mitmachen', '/twarz.html': 'KI-Gesicht', '/wesprzyj.html': 'Luna unterstützen', '/regulamin.html': 'AGB', '/privacy.html': 'Datenschutz', '/problemy.html': 'Hilfe', '/app': 'App', '/app#live': 'Chat mit dem Entwickler'},
 uk: {'/promo.html': 'Поради', '/butik.html': 'Бутик', '/scianka.html': 'Стіна', '/galeria.html': 'Галерея агенток', '/live.html': 'Luna Live', '/testerzy.html': 'Тестувальники', '/dolacz.html': 'Долучитися', '/twarz.html': 'Обличчя ШІ', '/wesprzyj.html': 'Підтримати Луну', '/regulamin.html': 'Правила', '/privacy.html': 'Конфіденційність', '/problemy.html': 'Допомога', '/': 'Застосунок', '/app#live': 'Чат з автором'}};
const OPEN = {en: 'Open Luna', es: 'Abrir Luna', de: 'Luna öffnen', uk: 'Відкрити Луну'};
function go(code){ try { localStorage.setItem('luna.lang', code); } catch(e){} document.cookie = 'luna_lang=' + code + ';path=/;max-age=31536000;samesite=lax';
  try { fetch('/api/me/lang', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({lang: code})}).catch(() => {}); } catch(e){}
  const u = new URL(location.href); u.searchParams.set('lang', code); location.href = u; }
/* Wybór języka: przycisk + okienko z wyszukiwarką (nazwy natywne, polskie i angielskie, kod), pogrupowane wg regionów; Esc zamyka, Enter wybiera pierwszy wynik. */
function picker(){
  const ui = PICK[cur] || PICK.en, gr = GR[cur] || GR.en;
  const tt = x => (window.LunaI18n ? window.LunaI18n.t(x) : x);
  const me = ALLL.find(x => x[0] === cur) || ALLL[0];
  const b = document.createElement('button'); b.type = 'button'; b.className = 'lswitch lpick-btn'; b.setAttribute('aria-haspopup', 'dialog'); b.setAttribute('aria-label', 'Język / Language: ' + me[2]);
  b.innerHTML = `<span aria-hidden="true">🌐</span> <span class="lpick-cur"></span>`; b.querySelector('.lpick-cur').textContent = me[2];
  let box = null;
  const close = () => { if (box){ box.remove(); box = null; b.setAttribute('aria-expanded', 'false'); b.focus(); } };
  b.onclick = () => {
    if (box) return close();
    box = document.createElement('div'); box.className = 'lpick'; box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Język / Language'); box.setAttribute('translate', 'no');
    const ext = !['pl', 'en', 'es', 'de', 'uk'].includes(cur);
    box.innerHTML = `<div class="lpick-h"><b>🌐 ${ext ? tt(ui[0]) : ui[0]}</b><button type="button" class="lpick-x" aria-label="×">×</button></div>
      <input type="search" class="lpick-q" autocomplete="off" spellcheck="false" placeholder="${ext ? tt(ui[1]) : ui[1]} / Search…" aria-label="${ui[1]}">
      <div class="lpick-list" role="listbox"></div><p class="lpick-note">${ext ? tt(ui[3]) : ''}</p>`;
    const list = box.querySelector('.lpick-list'), q = box.querySelector('.lpick-q');
    const draw = () => {
      const v = q.value.trim().toLowerCase(); const items = ALLL.filter(x => ON.includes(x[0]) && (!v || [x[0], x[2], x[3], x[4]].some(y => y.toLowerCase().includes(v))));
      if (!items.length){ list.innerHTML = `<p class="lpick-none">${ext ? tt(ui[2]) : ui[2]}</p>`; return; }
      let h = '';
      for (const g of ['c', 'w', 'n', 's', 'e', 'm', 'a']){
        const gi = items.filter(x => x[5] === g); if (!gi.length) continue;
        h += `<div class="lpick-g"><span class="lpick-gh">${ext ? tt(GR.en[g]) : gr[g]}</span>` + gi.map(x => `<button type="button" role="option" class="lpick-i${x[0] === cur ? ' on' : ''}" data-l="${x[0]}" lang="${x[0] === 'zh' ? 'zh-Hans' : x[0] === 'pt-br' ? 'pt-BR' : x[0]}" aria-selected="${x[0] === cur}"><span class="lpick-f" aria-hidden="true">${x[1]}</span><span class="lpick-n">${x[2]}</span><small lang="${cur === 'pl' ? 'pl' : 'en'}">${cur === 'pl' ? x[3] : x[4]}</small></button>`).join('') + '</div>';
      }
      list.innerHTML = h;
    };
    draw(); q.oninput = draw;
    q.onkeydown = e => { if (e.key === 'Enter'){ const f = list.querySelector('.lpick-i'); if (f) go(f.dataset.l); } };
    list.onclick = e => { const i = e.target.closest('.lpick-i'); if (i) go(i.dataset.l); };
    box.querySelector('.lpick-x').onclick = close;
    box.onkeydown = e => { if (e.key === 'Escape') close(); };
    document.body.appendChild(box); b.setAttribute('aria-expanded', 'true');
    setTimeout(() => { q.focus(); document.addEventListener('click', function off(e){ if (box && !box.contains(e.target) && e.target !== b && !b.contains(e.target)){ close(); document.removeEventListener('click', off); } }); }, 0);
  };
  return b;
}
window.LunaLangPicker = {open: () => { const b = document.querySelector('.lpick-btn') || picker(); if (!b.isConnected){ b.style.display = 'none'; document.body.appendChild(b); } b.click(); }, list: () => ALLL.filter(x => ON.includes(x[0])), go};
function mount(){
  if (APP) return;
  const N = NAV[cur];
  if (N){ document.querySelectorAll('header nav a, .sitefoot nav a, footer nav a').forEach(a => { const h = a.getAttribute('href'); if (N[h] && !/🎁/.test(a.textContent)) a.textContent = N[h]; else if (N[h]) a.textContent = N[h] + ' 🎁'; });
    document.querySelectorAll('header a.pill.primary[href="/app"]').forEach(a => a.textContent = OPEN[cur]); }
  appLink();
  if (document.querySelector('.lswitch')) return;
  const host = document.querySelector('header .bar .acts') || document.querySelector('header .bar') || document.querySelector('header.top') || document.querySelector('header');
  const s = picker();
  if (host) host.prepend(s); else { s.classList.add('floating'); document.body.appendChild(s); }
  document.querySelectorAll('.langtabs').forEach(t => t.hidden = true);
  document.querySelectorAll('a[href^="/"]').forEach(a => { if (cur === 'pl' || /^\/(api|music|uploads)\//.test(a.getAttribute('href'))) return; try { const u = new URL(a.href); if (u.origin === location.origin && /\.html$|\/$/.test(u.pathname) && !u.searchParams.get('lang')){ u.searchParams.set('lang', cur); a.href = u.pathname + u.search + u.hash; } } catch(e){} });
}
/* v1.4.2: dyskretny link do aplikacji (/app.html) w nagłówku i stopce strony */
function appLink(){
  if (document.documentElement.classList.contains('twa') || window.top !== window.self || document.querySelector('.applink')) return;
  const t = {pl: ['📱 Aplikacja', 'Otwórz aplikację Luny'], en: ['📱 App', 'Open the Luna app'], es: ['📱 App', 'Abrir la app de Luna'], de: ['📱 App', 'Luna-App öffnen'], uk: ['📱 Застосунок', 'Відкрити застосунок Луни']}[cur] || (cur === 'pl' ? ['📱 Aplikacja', 'Otwórz aplikację Luny'] : ['📱 App', 'Open the Luna app']);
  const href = '/app.html' + (cur !== 'pl' ? '?lang=' + cur : '');
  const acts = document.querySelector('header .bar .acts');
  if (acts){ const a = document.createElement('a'); a.className = 'pill ghost applink'; a.href = href; a.textContent = t[0]; a.title = t[1]; a.setAttribute('aria-label', t[1]); acts.prepend(a); }
  const fn = document.querySelector('.sitefoot nav, footer nav');
  if (fn && !fn.querySelector('a[href^="/app.html"]')){ const b = document.createElement('a'); b.href = href; b.textContent = t[1]; fn.prepend(b); }
  if (!document.getElementById('applinkCss')){ const st = document.createElement('style'); st.id = 'applinkCss'; st.textContent = '.applink{opacity:.9}@media (max-width:520px){header .applink{display:none!important}}'; document.head.appendChild(st); }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
