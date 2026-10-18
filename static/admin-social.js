/* Panel admina: Ścianka (wpisy), Komentarze, zgłoszenia, blokady. */
(() => {
const $ = s => document.querySelector(s);
const tok = () => sessionStorage.getItem('luna.admin') || '';
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
async function api(body){ const r = await fetch('/api/admin/social', {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json', 'X-Admin-Token': tok()}, body: body ? JSON.stringify(body) : undefined}); const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || r.status); return d; }
function btn(label, fn, cls){ const b = el('button', cls || 'ghost', label); b.type = 'button'; b.onclick = fn; return b; }
function render(d){
  $('#socStats').textContent = `Opublikowane: ${d.stats.posts} wpisów, ${d.stats.comments} komentarzy · Czeka: ${d.stats.pending} · Zgłoszenia: ${d.reports.length}`;
  $('#socBadge').textContent = d.stats.pending ? d.stats.pending : '';
  const act = (kind, id, action) => async () => { if (action === 'delete' && !confirm('Usunąć na stałe?')) return; if (action === 'ban' && !confirm('Zablokować autora (ukryje też ten wpis)?')) return; try { render(await api({kind, id, action})); } catch(e){ alert(e.message); } };
  const P = $('#socPosts'); P.textContent = ''; if (!d.posts.length) P.appendChild(el('p', 'hint', 'Brak wpisów do sprawdzenia.'));
  d.posts.forEach(p => { const it = el('div', 'item');
    it.append(el('b', null, p.nick + ' '), el('small', null, `${new Date(p.t * 1000).toLocaleString('pl-PL')} · ${p.status} · język: ${p.lang || 'pl'}${p.reports ? ' · ⚠️ zgłoszenia: ' + p.reports : ''}${p.uid ? ' · konto' : ' · bez konta'}`), el('p', 'reason', p.text));
    if (p.img_url){ const im = el('img'); im.alt = ''; im.style.cssText = 'max-width:220px;border-radius:14px;display:block;margin:6px 0'; fetch(p.img_url, {headers: {'X-Admin-Token': tok()}}).then(r => r.blob()).then(b => im.src = URL.createObjectURL(b)); it.appendChild(im); }
    const c = el('div', 'btns');
    c.append(btn('✅ Zatwierdź', act('post', p.id, 'approve')), btn('🚫 Odrzuć', act('post', p.id, 'reject')), btn('🙈 Ukryj', act('post', p.id, 'hide')), btn('🌐 Wersje językowe', async () => {
      const v = {}; for (const l of ['pl', 'en', 'es', 'de', 'uk']){ if (l === (p.lang || 'pl')) continue; const t = prompt(`Tekst wersji ${l.toUpperCase()} (puste = brak):`, (p.variants || {})[l] || ''); if (t === null) return; if (t.trim()) v[l] = t; }
      try { render(await api({kind: 'post', id: p.id, action: 'variants', variants: v})); } catch(e){ alert(e.message); } }), btn('Usuń', act('post', p.id, 'delete'), 'ghost danger'), btn('Zablokuj autora', act('post', p.id, 'ban'), 'ghost danger'));
    it.appendChild(c); P.appendChild(it); });
  const C = $('#socCmts'); C.textContent = ''; if (!d.comments.length) C.appendChild(el('p', 'hint', 'Brak komentarzy do sprawdzenia.'));
  d.comments.forEach(x => { const it = el('div', 'item');
    it.append(el('b', null, x.nick + ' '), el('small', null, `${new Date(x.t * 1000).toLocaleString('pl-PL')} · ${x.target}${x.parent ? ' · odpowiedź' : ''}${x.rating ? ' · ' + '★'.repeat(x.rating) : ''} · ${x.status}${x.reports ? ' · ⚠️ ' + x.reports : ''}`), el('p', 'reason', x.text));
    const c = el('div', 'btns'); c.append(btn('✅ Zatwierdź', act('cmt', x.id, 'approve')), btn('🚫 Odrzuć', act('cmt', x.id, 'reject')), btn('Usuń', act('cmt', x.id, 'delete'), 'ghost danger'), btn('Zablokuj autora', act('cmt', x.id, 'ban'), 'ghost danger'));
    it.appendChild(c); C.appendChild(it); });
  const B = $('#socBans'); B.textContent = ''; if (!d.bans.length) B.appendChild(el('p', 'hint', 'Nikt nie jest zablokowany.'));
  d.bans.forEach(a => { const it = el('div', 'item'); it.append(el('code', null, a), btn('Odblokuj', async () => render(await api({action: 'unban', author: a})))); B.appendChild(it); });
}
const sec = $('#socSection'); if (sec) sec.addEventListener('toggle', () => { if (sec.open) api().then(render).catch(e => $('#socStats').textContent = '⚠️ ' + e.message); });
})();
