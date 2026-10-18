/* Panel właściciela: Popularność Butiku, statystyki postów (dla reklamodawców), sekcje strony, podejrzane konta.
   Token administratora tylko w sessionStorage tej karty; kod nigdy nie jest zapisywany. Tylko prawdziwe dane z serwera. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const tok = () => sessionStorage.getItem('luna.admin') || '';
let TAB = 'butik', DAYS = 30, DATA = null, SUS = null;
const zl = n => (Math.round((n || 0) * 100) / 100).toFixed(2).replace('.', ',') + ' zł';
const num = n => Number(n || 0).toLocaleString('pl-PL');
async function api(path, body){
  const r = await fetch(path, body ? {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: JSON.stringify(body)} : {headers: {'X-Admin-Token': tok()}});
  if (r.status === 401){ sessionStorage.removeItem('luna.admin'); show(); throw new Error('Sesja wygasła – zaloguj się ponownie.'); }
  const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status); return d;
}
function show(){ const on = !!tok(); $('#login').hidden = on; $('#app').hidden = !on; $('#logout').hidden = !on; if (on) load(); }
$('#lf').onsubmit = async e => { e.preventDefault(); $('#lerr').textContent = '';
  try { const r = await fetch('/api/admin/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({passphrase: $('#pass').value})}); const d = await r.json();
    $('#pass').value = ''; if (!r.ok) throw new Error(d.error || r.status); sessionStorage.setItem('luna.admin', d.admin_token); show(); } catch(x){ $('#lerr').textContent = '⚠️ ' + x.message; } };
$('#logout').onclick = async () => { try { await api('/api/admin/logout', {}); } catch(e){} sessionStorage.removeItem('luna.admin'); show(); };
document.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { TAB = b.dataset.t; document.querySelectorAll('[data-t]').forEach(x => x.classList.toggle('on', x === b)); render(); });
document.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { DAYS = +b.dataset.d; document.querySelectorAll('[data-d]').forEach(x => x.classList.toggle('on', x === b)); load(); });
async function load(){ $('#view').innerHTML = '<p class="empty">Ładowanie…</p>';
  try { [DATA, SUS] = await Promise.all([api('/api/admin/stats?days=' + DAYS), api('/api/admin/suspects')]);
    $('#meta').textContent = `Dane z ${DATA.days} dni · magazyn: ${DATA.persistent ? 'trwały (Postgres)' : 'ulotny'}`; render(); } catch(e){ $('#view').innerHTML = `<p class="err">${esc(e.message)}</p>`; } }
function csv(name, rows, cols){ const q = v => { const s = String(v ?? ''); return /[",;\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const txt = '\ufeff' + cols.map(c => q(c[1])).join(';') + '\n' + rows.map(r => cols.map(c => q(typeof c[2] === 'function' ? c[2](r) : r[c[0]])).join(';')).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], {type: 'text/csv;charset=utf-8'})); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); }
function table(rows, cols, id){ if (!rows.length) return '<p class="empty">Brak danych.</p>';
  return `<div class="tw"><table data-tbl="${id || ''}"><thead><tr>${cols.map((c, i) => `<th class="${c[3] || ''}" data-i="${i}">${esc(c[1])}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(c => `<td class="${c[3] || ''}">${c[4] ? c[4](r) : esc(r[c[0]])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`; }
function sortable(){ document.querySelectorAll('#view table').forEach(t => t.querySelectorAll('th').forEach(th => th.onclick = () => { const i = +th.dataset.i, tb = t.tBodies[0], dir = th.dataset.dir = th.dataset.dir === 'a' ? 'd' : 'a';
  [...tb.rows].sort((a, b) => { const x = a.cells[i].textContent.replace(/\s|zł/g, '').replace(',', '.'), y = b.cells[i].textContent.replace(/\s|zł/g, '').replace(',', '.'); const nx = parseFloat(x), ny = parseFloat(y);
    const r = !isNaN(nx) && !isNaN(ny) ? nx - ny : x.localeCompare(y, 'pl'); return dir === 'a' ? r : -r; }).forEach(r => tb.appendChild(r)); })); }
const spark = a => `<span class="spark" title="${a.join(', ')}">${a.map(v => `<i style="height:${Math.max(1, Math.round(v / Math.max(1, ...a) * 22))}px"></i>`).join('')}</span>`;
function render(){
  if (!DATA) return; const V = $('#view');
  if (TAB === 'butik'){
    const B = DATA.butik, T = B.totals;
    const IC = [['name', 'Strój'], ['category', 'Kategoria'], ['collection', 'Kolekcja'], ['line', 'Linia'], ['rarity', 'Rzadkość'], ['tier', 'Plan'], ['price_pln', 'Cena', null, 'n', r => r.price_pln == null ? '–' : zl(r.price_pln)], ['views', 'Wyświetlenia', null, 'n', r => num(r.views)], ['unique', 'Unikalni', null, 'n', r => num(r.unique)], ['likes', '👍', null, 'n'], ['dislikes', '👎', null, 'n'], ['cart', 'Do koszyka', null, 'n'], ['purchases', 'Zakupy', null, 'n'], ['revenue_pln', 'Przychód', null, 'n', r => zl(r.revenue_pln)]];
    const AC = [['key', 'Grupa'], ['items', 'Stroje', null, 'n'], ['views', 'Wyświetlenia', null, 'n'], ['likes', '👍', null, 'n'], ['dislikes', '👎', null, 'n'], ['cart', 'Do koszyka', null, 'n'], ['purchases', 'Zakupy', null, 'n'], ['revenue_pln', 'Przychód', null, 'n', r => zl(r.revenue_pln)]];
    const names = {category: 'Kategoria', collection: 'Kolekcja', line: 'Linia', rarity: 'Rzadkość', tier: 'Plan', band: 'Przedział cenowy'};
    const tops = {views: 'Najczęściej oglądane', likes: 'Najbardziej lubiane', cart: 'Najczęściej do koszyka', purchases: 'Najczęściej kupowane', revenue_pln: 'Największy przychód'};
    V.innerHTML = `<div class="kpis"><div class="kpi"><b>${num(T.views)}</b><span>wyświetleń strojów</span></div><div class="kpi"><b>${num(T.cart)}</b><span>dodań do koszyka (klik „Zapłać”)</span></div><div class="kpi"><b>${num(T.purchases)}</b><span>zakupów strojów</span></div><div class="kpi"><b>${zl(T.revenue_pln)}</b><span>przychód ze strojów</span></div><div class="kpi"><b>${num(T.pass_purchases)}</b><span>zakupów planów · ${zl(T.pass_revenue_pln)}</span></div></div>
      <div class="card"><h2>Top 10</h2><div class="grid2">${Object.keys(tops).map(k => `<div><h3>${tops[k]}</h3>${B.top[k].length ? '<ol>' + B.top[k].map(r => `<li>${esc(r.name)} – <b>${k === 'revenue_pln' ? zl(r[k]) : num(r[k])}</b></li>`).join('') + '</ol>' : '<p class="empty">Brak danych.</p>'}</div>`).join('')}</div></div>
      <div class="grid2">${Object.keys(names).map(f => `<div class="card"><h2>Wg: ${names[f]}</h2>${table(B.by[f], AC)}</div>`).join('')}</div>
      <div class="card"><h2>Wszystkie stroje (${B.items.length}) <button id="csvI">⬇ CSV</button></h2>${table(B.items, IC)}</div>`;
    $('#csvI').onclick = () => csv(`butik-popularnosc-${DAYS}d.csv`, B.items, [['id', 'id'], ...IC.map(c => [c[0], c[1]])]);
  } else if (TAB === 'posts'){
    const P = DATA.posts.posts;
    const C = [['title', 'Wpis', null, '', r => `${r.official ? '<span class="tag">oficjalny</span> ' : ''}${esc(r.title)}`], ['views', 'Wyświetlenia', null, 'n'], ['unique', 'Unikalni', null, 'n'], ['likes', '👍 łącznie', null, 'n'], ['dislikes', '👎 łącznie', null, 'n'], ['likes_period', '👍 w okresie', null, 'n'], ['comments', 'Komentarze', null, 'n'], ['clicks', 'Kliknięcia linków', null, 'n'], ['ctr', 'CTR %', null, 'n'], ['shares', 'Udostępnienia', null, 'n'], ['engagement', 'Zaangażowanie %', null, 'n'], ['trend', 'Trend (dzień)', null, '', r => spark(r.trend)], ['langs', 'Języki', null, '', r => Object.entries(r.langs).map(([l, n]) => `<span class="tag">${l} ${n}</span>`).join('') || '–']];
    V.innerHTML = `<div class="card"><h2>Statystyki postów dla reklamodawców <button id="csvP">⬇ CSV</button></h2><p class="hint">Wyświetlenie = wpis widoczny co najmniej w 50% przez ≥1 s, raz na sesję dziennie. Boty i konta ukryte w cieniu nie są liczone. Zaangażowanie = (👍 + 👎 + komentarze + udostępnienia + kliknięcia w okresie) / wyświetlenia.</p>${table(P, C)}</div>`;
    $('#csvP').onclick = () => csv(`posty-statystyki-${DAYS}d.csv`, P, [['id', 'id'], ['title', 'wpis'], ['official', 'oficjalny'], ['views', 'wyswietlenia'], ['unique', 'unikalni'], ['views_total', 'wyswietlenia_lacznie'], ['likes', 'polubienia'], ['dislikes', 'nie_lubie'], ['likes_period', 'polubienia_okres'], ['dislikes_period', 'nie_lubie_okres'], ['comments', 'komentarze'], ['comments_period', 'komentarze_okres'], ['clicks', 'klikniecia'], ['ctr', 'ctr_proc'], ['shares', 'udostepnienia'], ['engagement', 'zaangazowanie_proc'], ['trend', 'trend', r => r.trend.join(' ')], ['langs', 'jezyki', r => Object.entries(r.langs).map(([l, n]) => l + ':' + n).join(' ')]]);
  } else if (TAB === 'site'){
    const S = DATA.site.sections;
    V.innerHTML = `<div class="card"><h2>Najczęściej oglądane sekcje strony</h2>${table(S, [['key', 'Sekcja'], ['views', 'Wyświetlenia', null, 'n']])}</div>
      <div class="card"><h2>Najczęściej oglądane wpisy</h2>${table(DATA.posts.posts.filter(p => p.views).slice(0, 10), [['title', 'Wpis'], ['views', 'Wyświetlenia', null, 'n']])}</div>`;
  } else {
    const L = SUS.suspects;
    V.innerHTML = `<div class="card"><h2>Podejrzane konta (${L.filter(s => s.status === 'flagged').length} ukrytych w cieniu)</h2>
      <p class="hint">Oznaczone automatycznie (próg: ${SUS.threshold} pkt) – ich polubienia, wyświetlenia i komentarze nie liczą się publicznie. Nic nie jest usuwane automatycznie. ${SUS.turnstile ? 'Captcha Turnstile: włączona.' : 'Captcha Turnstile: wyłączona (wymaga kluczy TURNSTILE_SITEKEY i TURNSTILE_SECRET).'}</p>
      ${L.length ? `<p><button id="bulk" class="danger">🗑 Usuń zaznaczone</button> <button id="bulkR" class="ok">↩ Przywróć zaznaczone</button></p>` : ''}
      ${table(L, [['ak', '', null, '', r => `<input type="checkbox" data-ak="${esc(r.ak)}" aria-label="zaznacz">`], ['kind', 'Typ'], ['label', 'Etykieta', null, '', r => esc(r.label || '–')], ['score', 'Punkty', null, 'n'], ['status', 'Status', null, '', r => r.status === 'flagged' ? '🚩 ukryte' : r.status === 'restored' ? '✅ przywrócone' : 'obserwowane'], ['reasons', 'Powody', null, '', r => r.reasons.map(x => `<span class="tag">${esc(x.label)} ×${x.n}</span>`).join('')], ['t', 'Od', null, '', r => new Date(r.t * 1000).toLocaleString('pl-PL')], ['act', 'Akcje', null, '', r => `<button class="danger" data-del="${esc(r.ak)}">Usuń</button> <button class="ok" data-res="${esc(r.ak)}">Przywróć</button>`]])}</div>`;
    const act = async (action, aks) => { if (!aks.length) return; if (action === 'delete' && !confirm(`Usunąć ${aks.length} kont(o) wraz z ich wpisami, komentarzami i głosami? Tego nie da się cofnąć.`)) return;
      try { SUS = Object.assign(SUS, await api('/api/admin/suspects', {action, aks})); render(); } catch(e){ alert(e.message); } };
    V.querySelectorAll('[data-del]').forEach(b => b.onclick = () => act('delete', [b.dataset.del]));
    V.querySelectorAll('[data-res]').forEach(b => b.onclick = () => act('restore', [b.dataset.res]));
    const sel = () => [...V.querySelectorAll('[data-ak]:checked')].map(x => x.dataset.ak);
    if ($('#bulk')){ $('#bulk').onclick = () => act('delete', sel()); $('#bulkR').onclick = () => act('restore', sel()); }
  }
  sortable();
}
show();
})();
