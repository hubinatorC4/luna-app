/* Formularze „Dołącz do projektu” i „Twarz AI” → skrzynka głównego moderatora (honeypot + limit czasu). */
(() => {
const f = document.getElementById('joinForm'); if (!f) return;
const t0 = Date.now();
const other = document.getElementById('otherRow');
if (other) f.role.onchange = () => { other.hidden = f.role.value !== 'inne'; };
f.onsubmit = async e => {
  e.preventDefault();
  const err = f.querySelector('.err'), ok = f.querySelector('.ok'); err.textContent = '';
  /* QA: novalidate – puste pola sprawdzamy tutaj (wcześniej szybkie puste wysłanie pokazywało „wysłano”, choć serwer nic nie zapisał) */
  if (!f.checkValidity()){
    const bad = f.querySelector(':invalid'); const L = (document.documentElement.lang || 'pl').slice(0, 2);
    const REQ = {pl: 'Uzupełnij wymagane pole', en: 'Please fill in the required field', es: 'Completa el campo obligatorio', de: 'Bitte fülle das Pflichtfeld aus', uk: 'Заповніть обов’язкове поле'}[L] || 'Uzupełnij wymagane pole';
    const lab = bad && bad.closest('label'); const nm = lab ? (lab.childNodes[0] && lab.childNodes[0].textContent || '').replace(/[*:]/g, '').trim() : '';
    if (bad){ try { bad.focus(); bad.scrollIntoView({block: 'center'}); } catch(x){} }
    err.textContent = '⚠️ ' + REQ + (nm ? ': ' + nm.slice(0, 60) : '') + '.'; return;
  }
  const fd = new FormData(f);
  const body = {name: fd.get('name'), email: fd.get('email'), role: fd.get('role'), role_other: fd.get('role_other') || '', message: fd.get('message'),
    portfolio: fd.get('portfolio') || '', dob: fd.get('dob'), adult: !!fd.get('adult'), consent: !!fd.get('consent'), website: fd.get('website') || '', t0,
    height: fd.get('height') || '', img_consent: !!fd.get('img_consent')};
  const btn = f.querySelector('[type=submit]'); btn.disabled = true;
  try {
    const r = await fetch('/api/join', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    [...f.elements].forEach(x => { if (x.type !== 'submit') x.disabled = true; }); ok.hidden = false; btn.hidden = true;
  } catch(x){ err.textContent = '⚠️ ' + x.message; btn.disabled = false; }
};
})();
