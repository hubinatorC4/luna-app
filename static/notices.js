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
    pl: 'Lubisz być pierwszy? Dołącz do tysiąca osób, które jako pierwsze sprawdzą bitwy, rankingi i swoją własną agentkę AI. W zamian dostajesz dwa miesiące Premium za darmo i wyjątkowe dodatki tylko dla testerów: ikonki, ekskluzywne emotki, specjalne awatary i możliwość delikatnej zmiany koloru ramki wokół Twojego logo. Miejsc jest dokładnie 1000 i licznik nie kłamie. Zgłoś się, zanim Luna powie „komplet” 😉',
    en: 'Like being first? Join a thousand people who’ll be the first to try battles, rankings and their very own AI agent. In return you get two months of Premium for free and special tester-only extras: icons, exclusive emotes, special avatars and the option to gently change the colour of the frame around your logo. There are exactly 1000 spots and the counter doesn’t lie. Sign up before Luna says “full house” 😉',
    es: '¿Te gusta ser de los primeros? Únete a mil personas que probarán antes que nadie las batallas, los rankings y su propia agente de IA. A cambio recibes dos meses de Premium gratis y extras exclusivos para testers: iconos, emoticonos exclusivos, avatares especiales y la opción de cambiar con suavidad el color del marco de tu logo. Hay exactamente 1000 plazas y el contador no miente. Apúntate antes de que Luna diga «completo» 😉',
    de: 'Du bist gern der Erste? Werde Teil von tausend Leuten, die als Erste Battles, Ranglisten und ihre ganz eigene KI-Agentin ausprobieren. Dafür bekommst du zwei Monate Premium gratis und besondere Extras nur für Tester: Icons, exklusive Emotes, spezielle Avatare und die Möglichkeit, die Rahmenfarbe um dein Logo sanft zu ändern. Es gibt genau 1000 Plätze, und der Zähler lügt nicht. Melde dich, bevor Luna „ausgebucht“ sagt 😉',
    uk: 'Любите бути першими? Приєднуйтеся до тисячі людей, які першими спробують битви, рейтинги й власну AI-агентку. Натомість отримаєте два місяці Premium безкоштовно та особливі бонуси лише для тестувальників: іконки, ексклюзивні емодзі, спеціальні аватари й можливість делікатно змінити колір рамки навколо вашого лого. Місць рівно 1000, і лічильник не бреше. Зголошуйтеся, поки Луна не сказала «аншлаг» 😉'}
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
