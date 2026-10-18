/* Konto (e-mail + hasło), plan i dostęp miesięczny, bramka 18+ (jednorazowa), RODO: eksport i usunięcie konta. */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ADULT = 'Oświadczam, że jestem osobą pełnoletnią (18+) i posiadam własne konto bankowe.';
const NAMES = {darmowy: 'Darmowy', podstawowa: 'Podstawowa', premium: 'Premium', pro: 'Pro / Ultra'};
let ME = null, CSRF = '';
const vid = () => window.LunaVid ? window.LunaVid() : '';
async function api(path, body){
  const h = {'Content-Type': 'application/json'}; if (CSRF) h['X-CSRF-Token'] = CSRF;
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers: h, credentials: 'same-origin', body: body ? JSON.stringify(body) : undefined});
  const d = await r.json().catch(() => ({})); if (!r.ok){ const e = new Error(d.error || r.status); e.data = d; throw e; } return d;
}
const fmtD = t => new Date(t * 1000).toLocaleDateString('pl-PL');

/* ---------- bramka 18+ ---------- */
const AGE_KEY = 'luna.age';
function ageOk(){ try { const a = JSON.parse(localStorage.getItem(AGE_KEY) || 'null'); return !!(a && a.adult && a.at); } catch(e){ return false; } }
function ageGate(){
  if (ageOk() || (ME && ME.adult)) return;
  const d = $('#ageGate'); if (!d) return;
  d.showModal();
  d.addEventListener('cancel', e => e.preventDefault());
  $('#ageForm').onsubmit = async e => {
    e.preventDefault(); const err = $('#ageErr'); err.textContent = '';
    const dob = $('#ageDob').value, adult = $('#ageChk').checked;
    try {
      const r = await api('/api/age/declare', {vid: vid(), dob, adult, name: window.UserName ? window.UserName() : '', source: 'app'});
      localStorage.setItem(AGE_KEY, JSON.stringify({adult: true, at: r.at})); d.close();
    } catch(x){
      if (x.data && x.data.underage){ $('#ageForm').hidden = true; $('#ageBlocked').hidden = false; $('#ageBlocked p').textContent = x.message; }
      else err.textContent = '⚠️ ' + x.message;
    }
  };
}

/* ---------- plan i wygaśnięcie dostępu ---------- */
function planUI(p){
  const box = $('#planBox'); if (!box || !p) return;
  let t = `<b>Twój plan: ${esc(p.name)}</b>`;
  if (p.until) t += `<br>Dostęp ważny do <b>${fmtD(p.until)}</b> (${p.source === 'tester' ? 'Premium testera' : 'dostęp miesięczny, bez automatycznego odnawiania'}).`;
  if (p.plan === 'darmowy') t += `<br>Limit: ok. ${p.free.chat_minutes} min rozmowy dziennie` + (p.chat_seconds_left != null ? ` · zostało dziś ok. ${Math.ceil(p.chat_seconds_left / 60)} min` : '') + '.';
  box.innerHTML = t + `<div class="btns"><button type="button" class="ghost" disabled title="Płatności – wkrótce">Przedłuż o miesiąc · wkrótce</button></div>`;
  const warn = $('#planWarn');
  if (warn){
    const dl = p.days_left;
    if (dl != null && dl <= 7){ warn.hidden = false; warn.textContent = `⏳ Twój dostęp ${p.name} wygasa ${dl <= 1 ? 'jutro' : 'za ' + Math.ceil(dl) + ' dni'} (${fmtD(p.until)}). Potem wrócisz do planu Darmowy. Przedłużenie – wkrótce.`; }
    else warn.hidden = true;
  }
}
window.addEventListener('luna-plan', e => planUI(e.detail));

/* ---------- konto ---------- */
function acctUI(){
  const box = $('#acctBox'); if (!box) return;
  if (ME){
    box.innerHTML = `<p>Zalogowano: <b>${esc(ME.email)}</b> ${ME.verified ? '✅' : `<span class="warn">(adres niepotwierdzony${ME.email_verification_available ? ' – sprawdź skrzynkę' : ' – potwierdzanie e-mail włączymy wkrótce'})</span>`}</p>
      <p class="hint">Oświadczenie 18+: ${ME.adult ? 'złożone ' + fmtD(ME.adult_at) : 'brak'} · Plan: ${NAMES[ME.plan] || ME.plan}${ME.until ? ' do ' + fmtD(ME.until) : ''}</p>
      <label>Kod testera<input id="a_tester" maxlength="12" value="${esc(ME.tester)}" placeholder="np. 1A2B3C4D"></label>
      <div class="btns"><button type="button" class="ghost" id="a_link">Przypisz kod testera</button>
      <a class="ghost btnlink" href="/api/account/export" download>⬇ Pobierz moje dane</a>
      <button type="button" class="ghost" id="a_logout">Wyloguj</button>
      <button type="button" class="ghost danger" id="a_delete">Usuń konto</button></div><p class="tst-err" id="a_err"></p>`;
    $('#a_logout').onclick = async () => { await api('/api/account/logout', {}).catch(() => {}); ME = null; CSRF = ''; acctUI(); window.LunaPlanRefresh && window.LunaPlanRefresh(); };
    $('#a_link').onclick = async () => { try { const r = await api('/api/account/link-tester', {code: $('#a_tester').value}); ME = r.user; localStorage.setItem('luna.tester', ME.tester); acctUI(); window.LunaPlanRefresh && window.LunaPlanRefresh(); } catch(e){ $('#a_err').textContent = '⚠️ ' + e.message; } };
    $('#a_delete').onclick = async () => {
      const L = (localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2).toLowerCase();
      const M = {pl: ['Usunąć konto na zawsze?\n\nUsuniemy konto i dane osobowe (e-mail, imię, hasło, sesje, zgłoszenie testera). Twoje dawne komentarze i wpisy zostaną zanonimizowane jako „Usunięty użytkownik”. Tego nie da się cofnąć.', 'Konto i dane osobowe zostały usunięte.'],
        en: ['Delete your account for good?\n\nWe will delete your account and personal data (email, name, password, sessions, tester application). Your past comments and posts will be anonymised as “Deleted user”. This cannot be undone.', 'Your account and personal data have been deleted.'],
        es: ['¿Eliminar tu cuenta para siempre?\n\nEliminaremos la cuenta y tus datos personales (correo, nombre, contraseña, sesiones, solicitud de tester). Tus comentarios y publicaciones anteriores se anonimizarán como «Usuario eliminado». No se puede deshacer.', 'Tu cuenta y tus datos personales se han eliminado.'],
        de: ['Konto endgültig löschen?\n\nWir löschen dein Konto und deine personenbezogenen Daten (E-Mail, Name, Passwort, Sitzungen, Testeranmeldung). Frühere Kommentare und Beiträge werden als „Gelöschter Nutzer“ anonymisiert. Das kann nicht rückgängig gemacht werden.', 'Dein Konto und deine personenbezogenen Daten wurden gelöscht.'],
        uk: ['Видалити акаунт назавжди?\n\nМи видалимо акаунт і персональні дані (е-пошту, ім’я, пароль, сесії, заявку тестувальника). Ваші попередні коментарі та дописи буде анонімізовано як «Видалений користувач». Цю дію не можна скасувати.', 'Акаунт і персональні дані видалено.']}[L] || null;
      const m = M || ['Usunąć konto na zawsze?', 'Konto zostało usunięte.'];
      if (!confirm(m[0])) return;
      try { await api('/api/account/delete', {}); ME = null; CSRF = ''; alert(m[1]); acctUI(); window.LunaPlanRefresh && window.LunaPlanRefresh(); } catch(e){ $('#a_err').textContent = '⚠️ ' + e.message; }
    };
    return;
  }
  box.innerHTML = `<div class="tabs2"><button type="button" class="on" data-t="in">Zaloguj</button><button type="button" data-t="up">Załóż konto</button></div>
    <form id="a_form" novalidate>
      <label>E-mail<input name="email" type="email" required maxlength="254" autocomplete="email"></label>
      <label>Hasło<input name="password" type="password" required minlength="10" maxlength="128" autocomplete="current-password"></label>
      <div class="up" hidden>
        <p class="hint">Hasło: min. 10 znaków, małe i wielkie litery oraz cyfra.</p>
        <label>Imię (opcjonalnie)<input name="name" maxlength="30" autocomplete="given-name"></label>
        <label>Data urodzenia *<input name="dob" type="date" max="${new Date().toISOString().slice(0, 10)}"></label>
        <label class="consent"><input type="checkbox" name="adult"> <span>${ADULT} *</span></label>
        <label class="consent"><input type="checkbox" name="terms"> <span>Akceptuję <a href="/regulamin.html" target="_blank">regulamin</a> i <a href="/privacy.html" target="_blank">informację o prywatności</a>. *</span></label>
        <p class="hint">To oświadczenie – nie weryfikujemy wieku ani konta bankowego.</p>
      </div>
      <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">
      <div class="btns"><button class="primary" type="submit">Zaloguj</button></div>
      <p class="tst-err" id="a_err"></p>
    </form>`;
  let mode = 'in'; const f = $('#a_form'); const shownAt = Date.now();
  box.querySelectorAll('.tabs2 button').forEach(b => b.onclick = () => { mode = b.dataset.t; box.querySelectorAll('.tabs2 button').forEach(x => x.classList.toggle('on', x === b)); f.querySelector('.up').hidden = mode !== 'up'; f.querySelector('[type=submit]').textContent = mode === 'up' ? 'Załóż konto' : 'Zaloguj'; f.password.autocomplete = mode === 'up' ? 'new-password' : 'current-password'; });
  f.onsubmit = async e => {
    e.preventDefault(); const err = $('#a_err'); err.textContent = '';
    const body = {email: f.email.value.trim(), password: f.password.value};
    if (mode === 'up') Object.assign(body, {name: f.name.value, dob: f.dob.value, adult: f.adult.checked, terms: f.terms.checked, website: f.website.value, fill_ms: Date.now() - shownAt});
    try {
      const r = await api(mode === 'up' ? '/api/account/signup' : '/api/account/login', body);
      ME = r.user; CSRF = r.csrf; f.password.value = '';
      if (ME.adult) localStorage.setItem(AGE_KEY, JSON.stringify({adult: true, at: ME.adult_at}));
      if (mode === 'up') alert(r.verification_sent ? 'Konto założone. Sprawdź skrzynkę, aby potwierdzić adres e-mail.' : 'Konto założone. Potwierdzanie adresu e-mail włączymy wkrótce – konto jest oznaczone jako niepotwierdzone.');
      acctUI(); window.LunaPlanRefresh && window.LunaPlanRefresh();
    } catch(x){ err.textContent = '⚠️ ' + x.message; }
  };
}
api('/api/account/me').then(d => { ME = d.user; CSRF = d.csrf || ''; acctUI(); ageGate(); }).catch(() => { acctUI(); ageGate(); });
window.LunaAccount = () => ME;
})();
/* ---------- status płatności po powrocie ze Stripe, ogłoszenie płatności, „Co nowego” ---------- */
(() => {
const $ = s => document.querySelector(s);
const banner = (txt, cls) => { const b = document.createElement('div'); b.className = 'pay-banner ' + (cls || ''); b.setAttribute('role', 'status'); b.textContent = txt; const x = document.createElement('button'); x.type = 'button'; x.textContent = '✕'; x.setAttribute('aria-label', 'Zamknij'); x.onclick = () => b.remove(); b.appendChild(x); document.body.appendChild(b); return b; };
const q = new URLSearchParams(location.search).get('platnosc');
if (q){
  history.replaceState(null, '', location.pathname);
  if (q === 'anulowano') banner('Płatność anulowana – nic nie pobraliśmy. Możesz spróbować ponownie albo wybrać inną metodę. 🙂', 'warn');
  else {
    const b = banner('Dziękujemy! 💚 Sprawdzamy płatność – to zwykle trwa kilka sekund…', 'ok');
    let n = 0; const before = (window.LunaPlan && window.LunaPlan().until) || 0;
    const poll = () => { window.LunaPlanRefresh && window.LunaPlanRefresh().then(() => {
      const p = window.LunaPlan ? window.LunaPlan() : {};
      if (p.until && p.until !== before){ b.firstChild.textContent = `Płatność przyjęta ✅ Plan ${p.name} jest aktywny do ${new Date(p.until * 1000).toLocaleDateString('pl-PL')}. Potwierdzenie wyśle Stripe na Twój e-mail.`; return; }
      if (++n < 10) setTimeout(poll, 3000); else b.firstChild.textContent = 'Płatność jest jeszcze w toku (np. BLIK czeka na potwierdzenie w banku). Odśwież stronę za chwilę – jeśli dostęp się nie pojawi, zgłoś to w zakładce „Problemy techniczne”.';
    }); };
    setTimeout(poll, 1500);
  }
}
fetch('/api/config').then(r => r.json()).then(c => {
  const pn = c.pay_notice || {}; if (!pn.text || !pn.t) return;
  try { if (+localStorage.getItem('luna.payNotice') >= pn.t) return; } catch(e){}
  const b = banner('💳 ' + pn.text, 'info'); b.querySelector('button').addEventListener('click', () => { try { localStorage.setItem('luna.payNotice', pn.t); } catch(e){} });
}).catch(() => {});
const NEWS = [
  ['🏠 Strona główna jak kanał', 'Jeden długi kanał: wpisy, nowości, Butik i casting. Większe litery, „Pokaż więcej” przy długich tekstach.'],
  ['🧱 Ścianka Agentek Głosu', 'Nowa nazwa Ścianki. Pod wpisami: polubienia, wyświetlenia i komentarze jak w czacie – tylko prawdziwe liczby.'],
  ['🛍 Nowy Butik Luny', 'Nowa kolekcja, kategorie i kolory. Wszystkie kolory w cenie stroju. Tylko eleganckie, zakrywające stroje.'],
  ['🔒 Prywatność', 'Usuwamy metadane (GPS, urządzenie) ze zdjęć. Konto usuniesz jednym kliknięciem.'],
  ['🤖 Ochrona przed botami', 'Fałszywe konta nie zawyżają liczników.']
];
window.LunaNews = () => {
  let d = $('#newsDlg');
  if (!d){ d = document.createElement('dialog'); d.id = 'newsDlg'; d.className = 'news';
    d.innerHTML = '<h2>Co nowego w wersji 1.4.0</h2><ul>' + NEWS.map(([h, t]) => `<li><b>${h}</b><br>${t}</li>`).join('') + '</ul><form method="dialog"><button class="primary">Super!</button></form>';
    document.body.appendChild(d); }
  d.showModal(); try { localStorage.setItem('luna.seenVer', '1.4.0'); } catch(e){}
};
try { if (localStorage.getItem('luna.seenVer') !== '1.4.0' && (localStorage.getItem('luna.age') || localStorage.getItem('luna.history'))) setTimeout(() => { if (!document.querySelector('dialog[open]')) window.LunaNews(); }, 1200); } catch(e){}
document.addEventListener('click', e => { if (e.target.closest && e.target.closest('[data-news]')){ e.preventDefault(); window.LunaNews(); } });
})();
