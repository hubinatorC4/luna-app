/* Stan konta 🧾 – poważne naruszenia „X z 3”, blokady i historia decyzji (dla zalogowanych). 5 języków.
   Montuje się w [data-standing], w „Moim panelu” (nad listą ustawień) i w ustawieniach aplikacji (nad kartą zaufania). */
(() => {
  const L5 = ['pl', 'en', 'es', 'de', 'uk'];
  const li = () => { const q = new URLSearchParams(location.search).get('lang'); const l = (q || document.documentElement.lang || 'pl').slice(0, 2); return Math.max(0, L5.indexOf(l)); };
  const S = {
    h: ['🧾 Stan konta', '🧾 Account status', '🧾 Estado de la cuenta', '🧾 Kontostatus', '🧾 Стан акаунта'],
    n: ['Poważne naruszenia: {n} z 3', 'Serious violations: {n} of 3', 'Infracciones graves: {n} de 3', 'Schwere Verstöße: {n} von 3', 'Серйозні порушення: {n} з 3'],
    ok: ['Czyste konto – Luna przybija piątkę ✋', 'Spotless account – Luna gives you a high five ✋', 'Cuenta impecable: Luna te choca los cinco ✋', 'Blitzsauberes Konto – Luna gibt dir High Five ✋', 'Бездоганний акаунт – Луна дає п’ять ✋'],
    some: ['Uwaga: przy 3 poważnych naruszeniach konto zostaje trwale zablokowane.', 'Heads-up: at 3 serious violations the account is permanently banned.', 'Ojo: con 3 infracciones graves la cuenta se bloquea para siempre.', 'Achtung: Bei 3 schweren Verstößen wird das Konto dauerhaft gesperrt.', 'Увага: після 3 серйозних порушень акаунт блокується назавжди.'],
    blk: ['⏸️ Czasowa blokada do {d} – możesz czytać, ale nie publikować.', '⏸️ Temporary block until {d} – you can read but not post.', '⏸️ Bloqueo temporal hasta el {d}: puedes leer, pero no publicar.', '⏸️ Vorübergehend gesperrt bis {d} – lesen ja, posten nein.', '⏸️ Тимчасове блокування до {d} – читати можна, публікувати ні.'],
    ban: ['⛔ Konto trwale zablokowane. Uzasadnienie znajdziesz w Skrzynce; możesz się odwołać, pobrać dane albo usunąć konto.', '⛔ Account permanently banned. The reasons are in your Inbox; you can appeal, download your data or delete the account.', '⛔ Cuenta bloqueada para siempre. El motivo está en tu Buzón; puedes recurrir, descargar tus datos o eliminar la cuenta.', '⛔ Konto dauerhaft gesperrt. Die Begründung steht im Postfach; du kannst Einspruch einlegen, Daten laden oder das Konto löschen.', '⛔ Акаунт заблоковано назавжди. Обґрунтування – у Скриньці; можна оскаржити, завантажити дані або видалити акаунт.'],
    warns: ['Ostrzeżenia: {n}', 'Warnings: {n}', 'Advertencias: {n}', 'Verwarnungen: {n}', 'Попередження: {n}'],
    hist: ['Historia decyzji', 'Decision history', 'Historial de decisiones', 'Entscheidungsverlauf', 'Історія рішень'],
    rules: ['Zasady i sankcje', 'Rules and sanctions', 'Normas y sanciones', 'Regeln und Sanktionen', 'Правила і санкції'],
    appeal: ['Odwołanie', 'Appeal', 'Recurso', 'Einspruch', 'Оскарження'],
    act: {remove: ['usunięcie treści', 'content removed', 'contenido eliminado', 'Inhalt entfernt', 'вміст видалено'], warn: ['ostrzeżenie', 'warning', 'advertencia', 'Verwarnung', 'попередження'],
      temp_block: ['czasowa blokada', 'temporary block', 'bloqueo temporal', 'vorübergehende Sperre', 'тимчасове блокування'], ban: ['trwała blokada', 'permanent ban', 'bloqueo permanente', 'dauerhafte Sperre', 'постійне блокування'],
      lift: ['blokada zdjęta', 'block lifted', 'bloqueo levantado', 'Sperre aufgehoben', 'блокування знято'], unstrike: ['naruszenie cofnięte', 'violation withdrawn', 'infracción retirada', 'Verstoß zurückgenommen', 'порушення скасовано']},
    serious: ['poważne', 'serious', 'grave', 'schwer', 'серйозне'],
  };
  const t = (k, o) => { let s = S[k][li()] || S[k][0]; for (const x in o || {}) s = s.replace('{' + x + '}', o[x]); return s; };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const CSS = `.lst{margin:12px 0;padding:16px 18px;border-radius:28px;background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.1);color:inherit}
.lst h3{margin:0 0 6px;font-size:17px}.lst .dots{font-size:20px;letter-spacing:4px;margin:4px 0}.lst p{margin:4px 0;font-size:14px}.lst .muted{opacity:.75;font-size:13px}
.lst ul{margin:6px 0 0;padding-left:18px;font-size:13px}.lst a{color:#ff9cbc}.lst .alert{color:#ffd59e}.lst .bad{color:#ffb4a8}`;
  async function mount(){
    let d; try { d = await (await fetch('/api/me/standing', {credentials: 'same-origin'})).json(); } catch(e){ return; }
    if (!d || !d.ok) return;
    const hosts = [...document.querySelectorAll('[data-standing]')];
    const st = document.getElementById('stApp'); if (st && !document.querySelector('.lst-auto-st')){ const x = document.createElement('div'); x.className = 'lst-auto-st'; st.parentElement.insertBefore(x, st); hosts.push(x); }
    const tc = document.querySelector('#settings .trust-card, dialog .trust-card'); if (tc && !document.querySelector('.lst-auto-tc')){ const x = document.createElement('div'); x.className = 'lst-auto-tc'; tc.parentElement.insertBefore(x, tc); hosts.push(x); }
    if (!hosts.length) return;
    if (!document.getElementById('lstCss')){ const s = document.createElement('style'); s.id = 'lstCss'; s.textContent = CSS; document.head.appendChild(s); }
    const n = Math.min(d.strikes, 3); const dots = '🔴'.repeat(n) + '💚'.repeat(3 - n);
    const fmt = ts => new Date(ts * 1000).toLocaleString(L5[li()] === 'uk' ? 'uk-UA' : L5[li()]);
    const last = (d.history || []).find(h => h.case);
    const html = `<section class="lst" aria-labelledby="lstH"><h3 id="lstH">${esc(t('h'))}</h3><div class="dots" aria-hidden="true">${dots}</div><p><b>${esc(t('n', {n}))}</b></p>
      ${d.banned ? `<p class="bad">${esc(t('ban'))}</p>` : d.block_until ? `<p class="alert">${esc(t('blk', {d: fmt(d.block_until)}))}</p>` : n ? `<p class="alert">${esc(t('some'))}</p>` : `<p>${esc(t('ok'))}</p>`}
      ${d.warns ? `<p class="muted">${esc(t('warns', {n: d.warns}))}</p>` : ''}
      ${(d.history || []).length ? `<details><summary class="muted">${esc(t('hist'))}</summary><ul>${d.history.map(h => `<li>${esc(fmt(h.t))} – ${esc((S.act[h.action] || S.act.remove)[li()])}${h.serious ? ' (' + esc(S.serious[li()]) + ')' : ''}${h.case ? ` · <a href="/problemy.html?odwolanie=${esc(h.case)}">${esc(t('appeal'))}</a>` : ''}</li>`).join('')}</ul></details>` : ''}
      <p class="muted"><a href="/regulamin.html#naruszenia">${esc(t('rules'))}</a>${last ? ` · <a href="/problemy.html?odwolanie=${esc(last.case)}">${esc(t('appeal'))}</a>` : ''}</p></section>`;
    hosts.forEach(h => { h.innerHTML = html; });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(mount, 300)); else setTimeout(mount, 300);
  // Odwołanie: /problemy.html?odwolanie=<sprawa> → wypełnia początek opisu
  const ap = new URLSearchParams(location.search).get('odwolanie');
  if (ap && /^[0-9a-f]{6,12}$/.test(ap) && location.pathname === '/problemy.html') setTimeout(() => {
    const ta = document.querySelector('textarea[name=description]'); if (!ta || ta.value) return;
    ta.value = t('appeal') + ' ' + ap + ': '; ta.focus(); ta.scrollIntoView({block: 'center'});
  }, 600);
  window.LunaStanding = {mount};
})();
