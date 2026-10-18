/* Formularze „Dołącz do projektu” i „Twarz AI” → skrzynka głównego moderatora (honeypot + limit czasu). */
(() => {
const f = document.getElementById('joinForm'); if (!f) return;
/* Komunikaty serwera są po polsku – tłumaczymy znane komunikaty na język strony (EN/ES/DE/UK). */
const ERR = {
  'Za dużo zgłoszeń – spróbuj później.': ['Too many applications – please try again later.', 'Demasiadas solicitudes: inténtalo más tarde.', 'Zu viele Bewerbungen – bitte versuche es später erneut.', 'Забагато заявок — спробуйте пізніше.'],
  'Potwierdź, że nie jesteś botem, i spróbuj ponownie.': ['Please confirm you are not a bot and try again.', 'Confirma que no eres un bot e inténtalo de nuevo.', 'Bitte bestätige, dass du kein Bot bist, und versuche es erneut.', 'Підтвердьте, що ви не бот, і спробуйте ще раз.'],
  'Zgłoszenia zamknięte, finał wkrótce.': ['Applications are closed – the final is coming soon.', 'Las solicitudes están cerradas; la final llegará pronto.', 'Bewerbungen sind geschlossen – das Finale kommt bald.', 'Прийом заявок закрито, фінал незабаром.'],
  'Podaj poprawny adres e-mail.': ['Please enter a valid email address.', 'Introduce un correo electrónico válido.', 'Bitte gib eine gültige E-Mail-Adresse ein.', 'Вкажіть правильну адресу е-пошти.'],
  'Wybierz rolę.': ['Please choose a role.', 'Elige un rol.', 'Bitte wähle eine Rolle.', 'Оберіть роль.'],
  'Napisz, jaka to rola.': ['Please tell us what the role is.', 'Escribe qué rol es.', 'Bitte schreib, um welche Rolle es geht.', 'Напишіть, яка це роль.'],
  'Napisz kilka słów o sobie (min. 10 znaków).': ['Write a few words about yourself (min. 10 characters).', 'Escribe unas palabras sobre ti (mín. 10 caracteres).', 'Schreib ein paar Worte über dich (mind. 10 Zeichen).', 'Напишіть кілька слів про себе (мін. 10 символів).'],
  'Link do portfolio musi zaczynać się od https://': ['The portfolio link must start with https://', 'El enlace al portafolio debe empezar por https://', 'Der Portfolio-Link muss mit https:// beginnen.', 'Посилання на портфоліо має починатися з https://'],
  'Zaznacz oświadczenie o pełnoletności (18+).': ['Please tick the 18+ declaration.', 'Marca la declaración de mayoría de edad (18+).', 'Bitte bestätige, dass du volljährig bist (18+).', 'Позначте заяву про повноліття (18+).'],
  'Zaznacz zgodę na przetwarzanie danych.': ['Please tick the consent to data processing.', 'Marca el consentimiento para el tratamiento de datos.', 'Bitte setze das Häkchen bei der Einwilligung zur Datenverarbeitung.', 'Позначте згоду на обробку даних.']};
const trErr = m => { const i = ['en', 'es', 'de', 'uk'].indexOf((document.documentElement.lang || 'pl').slice(0, 2)); return i >= 0 && ERR[m] ? ERR[m][i] : m; };
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
    portfolio: fd.get('portfolio') || '', adult: !!fd.get('adult'), consent: !!fd.get('consent'), website: fd.get('website') || '', t0,
    height: fd.get('height') || '', img_consent: !!fd.get('img_consent')};
  const btn = f.querySelector('[type=submit]'); btn.disabled = true;
  try {
    const r = await fetch('/api/join', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const d = await r.json(); if (!r.ok) throw new Error(d.error || r.status);
    [...f.elements].forEach(x => { if (x.type !== 'submit') x.disabled = true; }); ok.hidden = false; btn.hidden = true;
  } catch(x){ err.textContent = '⚠️ ' + trErr(x.message); btn.disabled = false; }
};
})();
