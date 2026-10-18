/* „Dołącz do zespołu” – formularz (method=post, honeypot, limit czasu). Teksty z <script id="i18n"> (klucze f_*), 5 języków. */
(() => {
  const host = document.querySelector('[data-team-form]'); if (!host) return;
  const I = JSON.parse(document.getElementById('i18n').textContent);
  const lang = () => { const l = (document.documentElement.lang || 'pl').slice(0, 2); return I[l] ? l : 'pl'; };
  const t = k => (I[lang()] || I.pl)['f_' + k] || I.pl['f_' + k] || k;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const AREAS = ['moderation', 'design', 'code', 'marketing', 'translation', 'voice', 'other'];
  const t0 = Date.now(); let sel = new Set(), done = false;
  function render(){
    if (done) return;
    const v = n => { const e = host.querySelector(`[name=${n}]`); return e ? (e.type === 'checkbox' ? e.checked : e.value) : ''; };
    const keep = {nick: v('nick'), email: v('email'), description: v('description'), portfolio: v('portfolio'), adult: v('adult'), consent: v('consent')};
    host.innerHTML = `<form class="tmf" method="post" action="/api/team/apply" novalidate>
      <label>${esc(t('nick'))} <small>${esc(t('nick_h'))}</small><input type="text" name="nick" maxlength="30" minlength="2" required autocomplete="nickname"></label>
      <label>${esc(t('email'))}<input type="email" name="email" maxlength="254" required autocomplete="email"></label>
      <div><b>${esc(t('area'))}</b><div class="tmchips" role="group" aria-label="${esc(t('area'))}">${AREAS.map(a => `<button type="button" data-a="${a}" aria-pressed="${sel.has(a)}">${esc(t('a_' + a))}</button>`).join('')}</div></div>
      <label>${esc(t('desc'))}<textarea name="description" rows="5" minlength="20" maxlength="2000" required placeholder="${esc(t('desc_ph'))}"></textarea><span class="tmcnt"><span>0</span>/2000</span></label>
      <label>${esc(t('link'))}<input type="url" name="portfolio" maxlength="300" placeholder="https://"></label>
      <label class="tmhp" aria-hidden="true">Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label>
      <label class="tmck"><input type="checkbox" name="adult" required> <span>${esc(t('adult'))}</span></label>
      <label class="tmck"><input type="checkbox" name="consent" required> <span>${esc(t('consent'))}</span></label>
      <p class="hint">${esc(t('terms'))}</p>
      <p class="tmerr" role="alert"></p>
      <button class="pill primary" type="submit">${esc(t('send'))}</button></form>`;
    const f = host.querySelector('form');
    for (const k in keep){ const e = f.querySelector(`[name=${k}]`); if (e){ if (e.type === 'checkbox') e.checked = !!keep[k]; else e.value = keep[k] || ''; } }
    const ta = f.description, cnt = f.querySelector('.tmcnt span'); const up = () => { cnt.textContent = ta.value.length; }; ta.oninput = up; up();
    f.querySelectorAll('.tmchips button').forEach(b => b.onclick = () => { const a = b.dataset.a; sel.has(a) ? sel.delete(a) : sel.add(a); b.setAttribute('aria-pressed', String(sel.has(a))); });
    f.onsubmit = async e => {
      e.preventDefault(); const err = f.querySelector('.tmerr'); err.textContent = '';
      const d = Object.fromEntries(new FormData(f)); const desc = (d.description || '').trim();
      if (!d.nick || !d.email || !f.adult.checked || !f.consent.checked){ err.textContent = t('e_req'); return; }
      if (!sel.size){ err.textContent = t('e_area'); return; }
      if (desc.length < 20 || desc.length > 2000){ err.textContent = t('e_desc'); return; }
      const btn = f.querySelector('button[type=submit]'); btn.disabled = true; btn.textContent = t('sending');
      try {
        const r = await fetch('/api/team/apply', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({nick: d.nick, email: d.email, areas: [...sel], description: desc, portfolio: d.portfolio || '', adult: f.adult.checked, consent: f.consent.checked, website: d.website || '', t0, lang: lang()})});
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || t('e_net'));
        done = true; host.innerHTML = `<div class="tmok" role="status">${esc(t('ok'))}</div>`;
      } catch(x){ err.textContent = '⚠️ ' + (x.message || t('e_net')); btn.disabled = false; btn.textContent = t('send'); }
    };
  }
  render();
  document.addEventListener('click', e => { if (e.target.closest('[data-lang]')) setTimeout(render, 60); });
})();
