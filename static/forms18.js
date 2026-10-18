/* Formularze 18+: tester (prosty) i casting (anonimowy, szczegółowy). Montowane w elementach [data-f18="tester"|"casting"].
   Weryfikacja 18+ u zewnętrznego dostawcy (Stripe Identity / karta przez Stripe Checkout) – na serwer trafia tylko wynik. */
(() => {
const S = window.F18_S || {}; const LS = ['pl', 'en', 'es', 'de', 'uk'];
const lang = () => { let l = document.documentElement.lang || 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || l; } catch(e){} l = String(l).slice(0, 2); return LS.includes(l) ? l : 'pl'; };
const t = k => { const v = S[k]; return v ? (v[LS.indexOf(lang())] || v[0]) : k; };
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const L = (k, html) => `<span data-k="${k}"${html ? ' data-h="1"' : ''}>${html ? t(k) : esc(t(k))}</span>`;
const tr = root => root.querySelectorAll('[data-k]').forEach(e => { if (e.dataset.h) e.innerHTML = t(e.dataset.k); else e.textContent = t(e.dataset.k); });
let CFG = null;
const cfg = () => CFG || (CFG = fetch('/api/forms/config', {credentials: 'same-origin'}).then(r => r.json()).catch(() => ({verify: 'soon', methods: {}, options: {}})));
const chips = (name, vals, pre, type) => `<div class="f18chips">${vals.map(v => `<label class="f18chip"><input type="${type || 'checkbox'}" name="${name}" value="${v}"><span>${L(pre + v)}</span></label>`).join('')}</div>`;

function testerHTML(o){
  return `<h3>${L('t_h')}</h3><p class="f18lead">${L('t_lead')}</p>
  <label class="f18f">${L('nick')} *<input name="nickname" required minlength="2" maxlength="30" autocomplete="nickname"><small>${L('nick_h')}</small></label>
  <label class="f18f">${L('email')} *<input name="email" type="email" required maxlength="254" autocomplete="email"><small>${L('email_h')}</small></label>
  <fieldset class="f18f"><legend>${L('device')} *</legend>${chips('device', o.devices || ['android', 'iphone', 'desktop'], 'd_', 'radio')}</fieldset>
  <fieldset class="f18f"><legend>${L('topics')} *</legend>${chips('topics', o.topics || ['voice', 'battles', 'wall', 'generator'], 'tp_')}</fieldset>
  <label class="f18f">${L('note')} <em>(${L('opt')})</em><textarea name="note" rows="2" maxlength="300"></textarea></label>
  ${dobHTML()}
  <fieldset class="f18f f18c"><legend>${L('consents')} *</legend>
    <label><input type="checkbox" name="c_terms"> ${L('c_terms', 1)}</label>
    <label><input type="checkbox" name="c_privacy"> ${L('c_privacy', 1)}</label>
    <label><input type="checkbox" name="c_nda"> ${L('c_nda')}</label></fieldset>`;
}
function castingHTML(o){
  return `<h3>${L('c_h')}</h3><p class="f18lead">${L('c_lead')}</p><div class="f18safe">${L('safe_box', 1)}</div>
  <label class="f18f">${L('pseud')} *<input name="pseudonym" required minlength="2" maxlength="40" autocomplete="off"><small>${L('pseud_h')}</small></label>
  <label class="f18f">${L('email')} *<input name="email" type="email" required maxlength="254" autocomplete="email"><small>${L('email_h')}</small></label>
  <fieldset class="f18f"><legend>${L('offer')} *</legend>${chips('offer', o.offers || ['voice', 'image', 'both'], 'o_', 'radio')}
    <div class="f18chips sm"><label class="f18chip"><input type="checkbox" name="partner_posts"><span>${L('pp')}</span></label><label class="f18chip"><input type="checkbox" name="promo_videos"><span>${L('pv')}</span></label></div></fieldset>
  <label class="f18f">${L('desc')} *<textarea name="description" rows="3" required minlength="20" maxlength="600"></textarea><small>${L('desc_h')}</small></label>
  ${dobHTML()}
  <details class="f18more"><summary>${L('more')}</summary>
    <fieldset class="f18f"><legend>${L('cats')}</legend>${chips('cats', o.cats || [], 'cat_')}</fieldset>
    <fieldset class="f18f"><legend>${L('langs')}</legend><div class="f18chips">${(o.langs || []).map(v => `<label class="f18chip"><input type="checkbox" name="langs" value="${v}"><span>${v === 'other' ? L('l_other') : v.toUpperCase()}</span></label>`).join('')}</div></fieldset>
    <fieldset class="f18f"><legend>${L('anon')}</legend>${chips('anonymity', o.anon || [], 'an_', 'radio')}</fieldset>
    <fieldset class="f18f"><legend>${L('avail')}</legend>${chips('availability', o.avail || [], 'av_', 'radio')}</fieldset>
    <label class="f18f">${L('voice')}<input name="voice" type="file" accept="audio/*"><small>${L('voice_h')}</small></label>
    <label class="f18f">${L('portfolio')}<input name="portfolio" type="url" maxlength="300" placeholder="https://"></label>
    <div class="f18row"><label class="f18f">${L('country')}<input name="country" maxlength="40" autocomplete="country-name"></label>
    <label class="f18f">${L('phone')}<input name="phone" type="tel" maxlength="20" autocomplete="tel"></label></div>
  </details>
  <fieldset class="f18f f18c"><legend>${L('consents')} *</legend>
    <label><input type="checkbox" name="c_use_voice_image"> ${L('cc_use')}</label>
    <label><input type="checkbox" name="c_discretion"> ${L('cc_disc')}</label>
    <label><input type="checkbox" name="c_withdraw"> ${L('cc_withdraw')}</label>
    <label><input type="checkbox" name="c_gdpr"> ${L('cc_gdpr', 1)}</label></fieldset>`;
}
/* 18+: tylko „Masz 18 lat?” Tak / Nie – bez daty urodzenia (zasada właściciela: nigdy nie zbieramy daty urodzenia) */
const dobHTML = () => `<fieldset class="f18f f18age"><legend>${L('a18_q')} *</legend><div class="f18chips"><label class="f18chip"><input type="radio" name="adult18" value="yes" required><span>${L('a18_yes')}</span></label><label class="f18chip"><input type="radio" name="adult18" value="no" required><span>${L('a18_no')}</span></label></div><small>${L('a18_h')}</small></fieldset>`;

function underage(box){ box.innerHTML = `<div class="f18done f18under" role="alert"><div class="f18ico">🌙</div><h3>${L('under_h')}</h3><p>${L('under')}</p></div>`; }

async function mount(box){
  const kind = box.dataset.f18; const c = await cfg(); const o = c.options || {};
  const q = new URLSearchParams(location.search);
  let saved = null; try { saved = JSON.parse(localStorage.getItem('luna.f18.' + kind) || 'null'); } catch(e){}
  if (q.get('id') && q.get('k') && (!q.get('f') || q.get('f') === kind)) return status(box, kind, q.get('id'), q.get('k'), q.get('v'));
  if (saved && saved.id && saved.k && !box.dataset.fresh) return status(box, kind, saved.id, saved.k);
  if (kind === 'casting' && c.casting_open === false){ box.innerHTML = `<p class="f18note">${L('closed')}</p>`; return; }
  if (kind === 'tester' && c.testers_left === 0){ box.innerHTML = `<p class="f18note">${L('full')}</p>`; return; }
  const t0 = Date.now();
  box.innerHTML = `<form class="f18" method="post" novalidate>${kind === 'tester' ? testerHTML(o) : castingHTML(o)}
    ${kind === 'tester' && c.testers_left != null ? `<p class="f18hint">${L('left')} <b>${c.testers_left}</b></p>` : ''}
    <div class="f18ts"></div>
    <input class="f18hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
    ${kind === 'casting' ? `<p class="f18safe sm">${L('safe_short', 1)}</p>` : ''}<p class="f18hint">${L('req')}</p>
    <button type="submit" class="f18btn">${L('send')}</button><p class="f18err" role="alert" aria-live="polite"></p></form>`;
  const f = box.querySelector('form'); let ts = '';
  if (c.turnstile) loadTS().then(() => { window.turnstile.render(f.querySelector('.f18ts'), {sitekey: c.turnstile, language: lang(), callback: v => { ts = v; }}); }).catch(() => {});
  f.querySelectorAll('[name=adult18]').forEach(r => r.addEventListener('change', () => { if (r.checked && r.value === 'no') underage(box); }));
  if (f.cats) f.addEventListener('change', e => { if (e.target.name === 'cats'){ const on = f.querySelectorAll('[name=cats]:checked'); if (on.length > 3) e.target.checked = false; } });
  f.onsubmit = async e => {
    e.preventDefault(); const err = f.querySelector('.f18err'); err.textContent = '';
    /* QA: formularz ma novalidate (własne komunikaty), więc puste pola sprawdzamy tutaj – inaczej puste zgłoszenie dawało ekran „Dziękujemy” bez zapisu */
    if (!f.checkValidity()){ const bad = f.querySelector(':invalid'); if (bad){ try { bad.focus({preventScroll: false}); bad.scrollIntoView({block: 'center'}); } catch(x){} } const nm = bad && (bad.closest('fieldset.f18age') ? bad.closest('fieldset').querySelector('legend span[data-k]') : bad.closest('label') && bad.closest('label').querySelector('span[data-k]')); err.textContent = '⚠️ ' + (nm ? nm.textContent.trim() + ': ' : '') + t('req').replace(/^\*\s*/, ''); return; }
    const fd = new FormData(f); const all = n => fd.getAll(n);
    if ((new FormData(f)).get('adult18') === 'no') return underage(box);
    /* QA (lejek testerów): grupy wyboru i zgody sprawdzamy po stronie klienta – komunikat w języku strony zamiast polskiego błędu z serwera */
    const need = kind === 'tester' ? [['device', !!fd.get('device'), 'e_device'], ['topics', all('topics').length > 0, 'e_topics']] : [['offer', !!fd.get('offer'), 'e_offer']];
    need.push(['c_', [...f.querySelectorAll('input[name^="c_"]')].every(x => x.checked), 'e_consents']);
    const miss = need.find(x => !x[1]);
    if (miss){ const el = f.querySelector(miss[0] === 'c_' ? 'input[name^="c_"]:not(:checked)' : `[name="${miss[0]}"]`); if (el){ try { el.focus({preventScroll: true}); el.closest('fieldset').scrollIntoView({block: 'center'}); } catch(x){} } err.textContent = '⚠️ ' + t(miss[2]); return; }
    const body = {email: fd.get('email'), adult_confirmed: fd.get('adult18') === 'yes', website: fd.get('website') || '', t0, turnstile: ts, lang: lang(), consents: {}};
    f.querySelectorAll('input[name^="c_"]').forEach(x => { body.consents[x.name.slice(2)] = x.checked; });
    if (kind === 'tester') Object.assign(body, {nickname: fd.get('nickname'), device: fd.get('device'), topics: all('topics'), note: fd.get('note') || ''});
    else {
      Object.assign(body, {pseudonym: fd.get('pseudonym'), offer: fd.get('offer'), partner_posts: !!fd.get('partner_posts'), promo_videos: !!fd.get('promo_videos'),
        description: fd.get('description'), cats: all('cats'), langs: all('langs'), anonymity: fd.get('anonymity') || '', availability: fd.get('availability') || '',
        portfolio: fd.get('portfolio') || '', country: fd.get('country') || '', phone: fd.get('phone') || ''});
      const file = f.voice && f.voice.files[0];
      if (file){ if (file.size > 3 * 1024 * 1024){ err.textContent = '⚠️ ' + t('voice_h'); return; } body.voice = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(file); }); }
    }
    if (c.turnstile && !ts){ err.textContent = '⚠️ ' + t('ts_wait'); return; }
    const btn = f.querySelector('.f18btn'); btn.disabled = true; btn.textContent = t('sending');
    try {
      const r = await fetch('/api/forms/' + kind, {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify(body)});
      const d = await r.json().catch(() => ({}));
      if (d.underage) return underage(box);
      if (!r.ok) throw new Error(srvErr(d.error) || r.status);
      if (d.id){ try { localStorage.setItem('luna.f18.' + kind, JSON.stringify({id: d.id, k: d.key})); } catch(e){} }
      verifyStep(box, kind, d.id, d.key, d.status, true);
    } catch(x){ err.textContent = '⚠️ ' + x.message; btn.disabled = false; btn.textContent = t('send'); if (window.turnstile) try { window.turnstile.reset(); } catch(e){} }
  };
}
/* błędy z serwera są po polsku – znane komunikaty tłumaczymy na język strony */
const SRV_ERR = [[/e-mail.*już do nas dotarło/i, 'e_dup'], [/Za dużo zgłoszeń/i, 'e_rate'], [/Komplet/i, 'full'], [/adres e-mail/i, 'e_email'], [/nick|pseudonim/i, 'e_nick'], [/zgody/i, 'e_consents'], [/urządzenie/i, 'e_device'], [/testować/i, 'e_topics'], [/botem/i, 'ts_wait']];
function srvErr(m){ if (!m || lang() === 'pl') return m; const x = SRV_ERR.find(e => e[0].test(m)); return x ? t(x[1]) : m; }
function loadTS(){ return window.turnstile ? Promise.resolve() : new Promise((ok, no) => { const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'; s.async = true; s.onload = ok; s.onerror = no; document.head.appendChild(s); }); }
const stKey = st => st.decision === 'accepted' ? 'st_accepted' : st.decision === 'rejected' ? 'st_rejected' : st.verification.status === 'verified' ? 'st_verified' : st.verification.status === 'failed' ? 'st_failed' : 'st_pending';
async function verifyStep(box, kind, id, k, st, fresh){
  const c = await cfg(); const m = c.methods || {};
  const link = id ? `${location.origin}/zgloszenie.html?f=${kind}&id=${encodeURIComponent(id)}&k=${encodeURIComponent(k)}` : '';
  const done = st && (st.decision !== 'new' || st.verification.status === 'verified');
  const card = st && st.verification.card ? ` · ${esc(st.verification.card.brand || '')} •••• ${esc(st.verification.card.last4 || '')}` : '';
  box.innerHTML = `<div class="f18done">${fresh ? `<div class="f18ico">💚</div><h3>${L('thanks')}</h3>` : `<h3>${L('status')}</h3>`}
    ${kind === 'casting' ? `<div class="f18safe">${L('safe_box', 1)}</div>` : ''}
    ${kind === 'tester' ? `<div class="f18safe f18perks">${L('perks', 1)}</div><p class="f18app"><a class="f18btn" href="/app.html${lang() !== 'pl' ? '?lang=' + lang() : ''}" target="_top">${L('open_app')}</a><small>${L('open_app_d')}</small></p>` : ''}
    ${st ? `<p class="f18st ${esc(stKey(st))}">${L(stKey(st))}${card}</p>` : ''}
    ${done ? '' : `<div class="f18v"><h4>${L('v_h')}</h4>${c.verify === 'on' ? `<p>${L('v_lead')}</p>
      <div class="f18m">${m.document ? `<button type="button" class="f18mb" data-m="document"><b>${L('m_doc')}</b><small>${L('m_doc_d')}</small></button>` : ''}
      ${m.card ? `<button type="button" class="f18mb" data-m="card"><b>${L('m_card')}</b><small>${L('m_card_d')}</small></button>` : ''}</div>`
      : `<div class="f18soon"><b>⏳ ${L('soon_h')}</b><p>${L('soon_d')}</p></div>
      <div class="f18m dis" aria-disabled="true"><div class="f18mb"><b>${L('m_doc')}</b><small>${L('m_doc_d')}</small></div><div class="f18mb"><b>${L('m_card')}</b><small>${L('m_card_d')}</small></div></div>`}
      <p class="f18err" role="alert"></p></div>`}
    ${link ? `<div class="f18link"><small>${L('link')}</small><div><input readonly value="${esc(link)}" aria-label="link"><button type="button" class="f18copy">${L('copy')}</button></div></div>` : ''}
    ${id ? `<button type="button" class="f18del">${L('del')}</button>` : ''}</div>`;
  const dl = box.querySelector('.f18del'); if (dl) dl.onclick = async () => { if (!confirm(t('del_q'))) return;
    const r = await fetch('/api/forms/delete', {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({id, k})});
    if (r.ok){ try { localStorage.removeItem('luna.f18.' + kind); } catch(e){} box.innerHTML = `<p class="f18note">${L('deleted')}</p>`; } };
  const cp = box.querySelector('.f18copy'); if (cp) cp.onclick = () => { const i = box.querySelector('.f18link input'); i.select(); (navigator.clipboard ? navigator.clipboard.writeText(i.value) : Promise.resolve(document.execCommand('copy'))).then(() => { cp.textContent = t('copied'); }); };
  box.querySelectorAll('button[data-m]').forEach(b => b.onclick = async () => {
    const err = box.querySelector('.f18err'); err.textContent = ''; b.disabled = true;
    try { const r = await fetch('/api/forms/verify', {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({id, k, method: b.dataset.m})});
      const d = await r.json(); if (d.url) { location.href = d.url; return; } if (d.already) return status(box, kind, id, k); throw new Error(d.error || r.status);
    } catch(x){ err.textContent = '⚠️ ' + x.message; b.disabled = false; }
  });
}
async function status(box, kind, id, k, back){
  box.innerHTML = `<p class="f18note">${L('checking')}</p>`;
  let st = null;
  for (let i = 0; i < (back ? 6 : 1); i++){
    try { const r = await fetch(`/api/forms/status?id=${encodeURIComponent(id)}&k=${encodeURIComponent(k)}`, {credentials: 'same-origin'}); if (r.ok) st = await r.json(); else if (r.status === 404) break; } catch(e){}
    if (!back || (st && st.verification.status !== 'pending')) break;
    await new Promise(r => setTimeout(r, 2500));
  }
  if (!st){ try { localStorage.removeItem('luna.f18.' + kind); } catch(e){} box.dataset.fresh = '1'; return mount(box); }
  verifyStep(box, kind, id, k, st, false);
}
const boxes = [...document.querySelectorAll('[data-f18]')];
boxes.forEach(mount);
window.addEventListener('luna-lang', () => boxes.forEach(tr));
})();
