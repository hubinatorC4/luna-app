/* Luna – rekrutacja testerów (formularz, licznik miejsc) i status testera (Premium + kolorowa obwódka awatara). */
(() => {
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const code = () => localStorage.getItem('luna.tester') || '';
window.LunaTesterCode = code;

/* ---------- status testera: obwódka i Premium ---------- */
function applyStatus(st){
  window.LunaTesterRing = st && st.granted ? st.ring : null;
  document.documentElement.style.setProperty('--uring', window.LunaTesterRing || 'var(--amber)');
  document.body.classList.toggle('tester', !!window.LunaTesterRing);
  if (st && st.granted){
    window.LunaPlanRefresh && window.LunaPlanRefresh();  // plan potwierdza serwer (kod testera / konto)
  }
  const el = $('#testerState'); if (el) el.textContent = st && st.found ? (st.granted ? `✅ Tester ${st.name}: Premium aktywne do ${new Date(st.until * 1000).toLocaleDateString('pl-PL')}, obwódka ${st.ring_choice}.` : `⏳ Zgłoszenie przyjęte (${st.name}). Premium i obwódkę ${st.ring_choice} włączymy po zatwierdzeniu.`) : '';
}
function refresh(){ if (!code()) return applyStatus(null); fetch('/api/testers/status?code=' + encodeURIComponent(code())).then(r => r.json()).then(applyStatus).catch(() => {}); }
window.LunaTesterRefresh = refresh;
refresh();
const ti = $('#u_tester'); if (ti){ ti.value = code(); ti.onchange = () => { const v = ti.value.trim().toUpperCase(); if (v) localStorage.setItem('luna.tester', v); else localStorage.removeItem('luna.tester'); refresh(); }; }

/* ---------- baner w aplikacji ---------- */
const ab = $('#testerBanner');
function loadInfo(){ return fetch('/api/testers').then(r => r.json()); }
if (ab) loadInfo().then(d => { if (d.remaining > 0 && !code()){ ab.querySelector('b').textContent = `Zostało ${d.remaining} z ${d.limit} miejsc`; ab.hidden = false; } }).catch(() => {});

/* ---------- formularz (strona główna / promocyjna) ---------- */
const PERKS = '🎟️ Dodatki testera: odznaka, ekskluzywne emotki, specjalne awatary i wybór koloru ramki – znajdziesz je w „Mój panel”, gdy podepniesz kod testera do konta.';
const box = $('#testerzy-form');
function count(d){
  document.querySelectorAll('.tst-left').forEach(e => e.textContent = d.remaining > 0 ? `Zostało ${d.remaining} z ${d.limit} miejsc` : 'Komplet – wszystkie miejsca zajęte');
  document.querySelectorAll('.tst-bar i').forEach(e => e.style.width = ((d.limit - d.remaining) / d.limit * 100) + '%');
}
/* licznik miejsc – prawdziwe dane z /api/testers (zgłoszenia przyjęte do testów), także gdy formularz to [data-f18="tester"] */
if (!box){ if (document.querySelector('.tst-left')) loadInfo().then(count).catch(() => {}); return; }
function render(d){
  count(d);
  if (code()){ box.innerHTML = `<div class="tst-done">🎉 Jesteś na liście testerów! Twój kod testera: <b>${esc(code())}</b>.<br>Zachowaj go – wpiszesz go w aplikacji (Ustawienia → Twój profil), jeśli zmienisz urządzenie.<br><br>${PERKS}</div>`; return; }
  if (d.remaining <= 0){ box.innerHTML = '<div class="tst-done">Dziękujemy! Wszystkie 1000 miejsc dla testerów jest już zajętych. Zapisz się na powiadomienia, by nie przegapić premiery.</div>'; return; }
  box.innerHTML = `<form class="tst-form" novalidate>
    <label>Imię *<input name="name" required maxlength="40" autocomplete="given-name"></label>
    <label>E-mail *<input name="email" type="email" required maxlength="254" autocomplete="email"></label>
    <label>Dlaczego chcesz testować? <small>(opcjonalnie)</small><textarea name="reason" maxlength="300" rows="2"></textarea></label>
    <fieldset><legend>Kolor obwódki Twojego awatara *</legend>
      <label class="ring-opt"><input type="radio" name="ring" value="fioletowa" required><span class="dot" style="--c:#8B5CF6"></span>Fioletowa</label>
      <label class="ring-opt"><input type="radio" name="ring" value="niebieska"><span class="dot" style="--c:#3B82F6"></span>Niebieska</label>
    </fieldset>
    <fieldset><legend>Masz telefon z Androidem? *</legend>
      <label class="ring-opt"><input type="radio" name="android" value="1" required>Tak</label>
      <label class="ring-opt"><input type="radio" name="android" value="0">Nie</label>
      <p class="hint">Do zamkniętych testów w Google Play potrzebny jest adres e-mail powiązany z Twoim kontem Google – najlepiej podaj właśnie ten.</p>
    </fieldset>
    <label class="consent"><input type="checkbox" name="adult" required> <span>Oświadczam, że jestem osobą pełnoletnią (18+) i posiadam własne konto bankowe. *</span></label>
    <label class="consent"><input type="checkbox" name="consent" required> <span>${esc(d.consent)} * <a href="/privacy.html" target="_blank">Informacja o danych</a></span></label>
    <button class="btn primary" type="submit">Zgłaszam się do testów</button>
    <p class="tst-err" role="alert"></p>
  </form>`;
  const f = box.querySelector('form');
  f.onsubmit = async e => {
    e.preventDefault(); const fd = new FormData(f), err = f.querySelector('.tst-err'); err.textContent = '';
    const body = {name: fd.get('name'), email: fd.get('email'), reason: fd.get('reason'), ring: fd.get('ring'),
      android: fd.get('android') === null ? null : fd.get('android') === '1', consent: !!fd.get('consent'), adult: !!fd.get('adult')};
    f.querySelector('button').disabled = true;
    try {
      const r = await fetch('/api/testers/signup', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      const j = await r.json();
      if (!r.ok){ if (j.full) return loadInfo().then(render); if (j.underage){ box.innerHTML = '<div class="tst-done">' + esc(j.error) + '</div>'; return; } throw new Error(j.error || r.status); }
      localStorage.setItem('luna.tester', j.code); refresh(); loadInfo().then(render);
    } catch(x){ err.textContent = '⚠️ ' + x.message; f.querySelector('button').disabled = false; }
  };
}
loadInfo().then(render).catch(() => { box.textContent = 'Nie udało się wczytać formularza. Odśwież stronę.'; });
})();
