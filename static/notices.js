/* Komunikaty marki w 5 językach: zastrzeżenie, projekt fanowski, „bez reklam”, lekka linijka o wsparciu (tylko WWW), zaproszenie do współpracy. */
(() => {
const T = {
  disclaimer: {
    pl: 'Luna to asystentka AI do nauki mówienia i pracy z głosem. Produkt w żaden sposób nie ma na celu seksualizacji kobiet.',
    en: 'Luna is an AI assistant for learning to speak and working with your voice. The product is in no way intended to sexualise women.',
    es: 'Luna es una asistente de IA para aprender a hablar y trabajar la voz. El producto no pretende en modo alguno sexualizar a las mujeres.',
    de: 'Luna ist eine KI-Assistentin zum Sprechenlernen und für die Arbeit mit der Stimme. Das Produkt zielt in keiner Weise darauf ab, Frauen zu sexualisieren.',
    uk: 'Луна — це ШІ-асистентка для навчання мовлення та роботи з голосом. Продукт жодним чином не має на меті сексуалізацію жінок.'},
  fan: {
    pl: 'Luna mówi jak jest to projekt fanowski – i taki zostanie, słowo Luny! Wspieraj nas zawsze, gdziekolwiek jesteś. 💚',
    en: 'Luna Tells It Like It Is is a fan project – and it will stay that way, Luna’s word of honour! Support us always, wherever you are. 💚',
    es: 'Luna dice las cosas como son es un proyecto de fans – y así seguirá, ¡palabra de Luna! Apóyanos siempre, estés donde estés. 💚',
    de: 'Luna sagt, wie es ist, ist ein Fanprojekt – und bleibt es, Ehrenwort von Luna! Unterstütze uns immer, wo auch immer du bist. 💚',
    uk: 'Луна каже як є — це фанатський проєкт, і таким він залишиться, слово Луни! Підтримуйте нас завжди, де б ви не були. 💚'},
  noads: {
    pl: '🚫 Bez reklam – Luna nie ogląda reklam, bo i tak by je przegadała 😄 Zero reklam, sama przyjemność gadania.',
    en: '🚫 No ads – Luna doesn’t watch ads – she’d talk right over them anyway 😄 Zero ads, just the joy of chatting.',
    es: '🚫 Sin anuncios – Luna no ve anuncios, de todos modos los dejaría sin palabras 😄 Cero anuncios, solo el placer de charlar.',
    de: '🚫 Keine Werbung – Luna schaut keine Werbung, sie würde sie ohnehin totquatschen 😄 Null Werbung, nur Freude am Reden.',
    uk: '🚫 Без реклами – Луна не дивиться рекламу, бо однаково її переговорила б 😄 Нуль реклами, лише задоволення від розмови.'},
  money: {
    pl: 'Luna nie je, nie śpi i nie pije kawy… ale serwery już tak ☕ Każda drobna złotówka się przyda, a wsparcie jest zawsze dobrowolne.',
    en: 'Luna doesn’t eat, sleep or drink coffee… but the servers do ☕ Every little bit helps, and support is always voluntary.',
    es: 'Luna no come, no duerme ni toma café… pero los servidores sí ☕ Cualquier pequeña ayuda cuenta, y el apoyo siempre es voluntario.',
    de: 'Luna isst nicht, schläft nicht und trinkt keinen Kaffee… die Server aber schon ☕ Jeder kleine Betrag hilft, und Unterstützung ist immer freiwillig.',
    uk: 'Луна не їсть, не спить і не п’є каву… а от сервери — так ☕ Кожна дрібна копійка знадобиться, а підтримка завжди добровільна.'},
  invite: {
    pl: 'Masz talent i odrobinę wolnego czasu? Projektanci, graficy, programiści, lektorzy, twórcy treści i tłumacze – Luna aż się rumieni na myśl o współpracy z wami! Wszystkie wiadomości trafiają do głównego moderatora (on też pije kawę ☕).',
    en: 'Got talent and a little spare time? Designers, graphic artists, developers, voice actors, content creators and translators – Luna is blushing at the thought of working with you! All messages go to the lead moderator (who runs on coffee too ☕).',
    es: '¿Tienes talento y un poco de tiempo libre? Diseñadores, grafistas, programadores, locutores, creadores de contenido y traductores: ¡Luna se sonroja solo de pensar en colaborar con vosotros! Todos los mensajes llegan al moderador principal (él también toma café ☕).',
    de: 'Talent und ein bisschen Freizeit? Designer, Grafiker, Entwickler, Sprecher, Content-Creator und Übersetzer – Luna wird ganz rot beim Gedanken an die Zusammenarbeit mit euch! Alle Nachrichten gehen an den Hauptmoderator (der trinkt auch Kaffee ☕).',
    uk: 'Маєш талант і трохи вільного часу? Дизайнери, графіки, програмісти, диктори, автори контенту й перекладачі — Луна аж червоніє від думки про співпрацю з вами! Усі повідомлення надходять головному модератору (він теж п’є каву ☕).'},
  testers: {
    pl: 'Szukamy 50 śmiałków, którzy nie boją się mówić „szczęście” bez zająknięcia… Premium będzie płatne, ale testerzy dostają je za darmo na 2 miesiące – plus fioletową lub niebieską obwódkę!',
    en: 'We’re looking for 50 brave souls who can say “szczęście” without a stumble… Premium will be paid, but testers get it free for 2 months – plus a purple or blue ring!',
    es: 'Buscamos 50 valientes capaces de decir «szczęście» sin trabarse… Premium será de pago, pero los testers lo tienen gratis 2 meses, ¡y además un aro morado o azul!',
    de: 'Wir suchen 50 Mutige, die „szczęście“ ohne Stolpern sagen können… Premium wird kostenpflichtig, aber Tester bekommen es 2 Monate gratis – plus einen lila oder blauen Ring!',
    uk: 'Шукаємо 50 сміливців, які вимовлять «szczęście» без затинки… Premium буде платним, але тестувальники отримають його безкоштовно на 2 місяці — ще й фіолетову чи синю обвідку!'}
};
window.LunaNotices = T; window.LunaDisclaimers = T.disclaimer;
let l = 'pl'; try { l = (localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2).toLowerCase(); } catch(e){}
if (!T.fan[l]) l = 'pl';
function apply(lang){
  if (!T.fan[lang]) lang = 'pl';
  document.querySelectorAll('[data-disclaimer]').forEach(e => { e.textContent = T.disclaimer[lang]; e.lang = lang; });
  document.querySelectorAll('[data-note]').forEach(e => { const t = T[e.dataset.note]; if (t){ e.textContent = t[lang]; e.lang = lang; } });
}
window.LunaDisclaimerLang = apply;
apply(l);
})();

/* „Polub nas” – pasek widoczny tylko wtedy, gdy ustawiono adresy profili (LUNA_SOCIAL_*). Bez nagród za polubienia i bez liczników. */
(() => {
  const foot = document.querySelector('.sitefoot'); if (!foot) return;
  const L = (document.documentElement.lang || 'pl').slice(0, 2);
  const H = {pl: 'Polub nas', en: 'Follow us', es: 'Síguenos', de: 'Folge uns', uk: 'Стежте за нами'}[L] || 'Polub nas';
  const N = {facebook: 'Facebook', instagram: 'Instagram', tiktok: 'TikTok', youtube: 'YouTube', x: 'X'};
  fetch('/api/social-links').then(r => r.json()).then(d => { const k = Object.keys(d.links || {}); if (!k.length) return;
    const el = document.createElement('div'); el.className = 'likestrip';
    el.innerHTML = '<b>💚 ' + H + '</b> ' + k.map(x => `<a href="${d.links[x].replace(/"/g, '')}" target="_blank" rel="noopener me">${N[x]}</a>`).join('');
    foot.insertBefore(el, foot.firstChild); }).catch(() => {});
})();
