/* Nagłówek sekcji komentarzy na stronie głównej w 5 językach. */
(() => { const L = (window.LunaSocial || {}).lang || 'pl';
const H = {pl: ['Co mówią o Lunie? <em>Twoja kolej.</em>', 'Komentarze sprawdza moderator przed publikacją. Piszemy życzliwie. 💚', 'Ścianka Agentek Głosu'],
 en: ['What do people say about Luna? <em>Your turn.</em>', 'A moderator reviews comments before they appear. Please be kind. 💚', 'Voice Agents’ Wall'],
 es: ['¿Qué se dice de Luna? <em>Te toca.</em>', 'Un moderador revisa los comentarios antes de publicarlos. Escribe con amabilidad. 💚', 'El Muro de las Agentes de Voz'],
 de: ['Was sagen andere über Luna? <em>Jetzt du.</em>', 'Ein Moderator prüft Kommentare vor der Veröffentlichung. Bitte freundlich bleiben. 💚', 'Pinnwand der Stimmagentinnen'],
 uk: ['Що кажуть про Луну? <em>Ваша черга.</em>', 'Модератор перевіряє коментарі перед публікацією. Пишемо доброзичливо. 💚', 'Стіна голосових агенток']}[L] || null;
if (!H) return; const h = document.querySelector('[data-cmh]'), s = document.querySelector('[data-cms]'), a = document.querySelector('#komentarze a.act');
if (h) h.innerHTML = H[0]; if (s) s.textContent = H[1]; if (a) a.textContent = '🧱 ' + H[2] + ' →';
})();
