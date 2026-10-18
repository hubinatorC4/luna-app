/* Sekcja „Pobierz aplikację”: wykrywa platformę, 5 języków, przycisk przełącza się na Google Play po ustawieniu adresu w panelu. */
(() => {
const T = {
 pl: {h: 'Pobierz aplikację', lead: 'Luna zawsze pod ręką – na telefonie, bez reklam.', btn: 'Pobierz aplikację', btn_short: '📲 Pobierz', play: 'Pobierz z Google Play', pc: 'Komputer',
  a1h: 'Stuknij „Pobierz aplikację”', a1: 'Na telefonie z Androidem – pobierze się plik instalacyjny Luny.', a2h: 'Otwórz pobrany plik', a2: 'Jeśli telefon zapyta, zezwól na instalację z tego źródła. To jednorazowe i bezpieczne ustawienie.', a3h: 'Stuknij „Zainstaluj”', a3: 'Gotowe! Luna pojawi się na ekranie głównym.',
  i1h: 'Otwórz Lunę w Safari', i1: 'Wejdź na luna-voice-coach.onrender.com.', i2h: 'Stuknij „Udostępnij”', i2: 'To ikonka kwadratu ze strzałką u dołu ekranu.', i3h: 'Wybierz „Do ekranu początkowego”', i3: 'Luna zamieszka na ekranie głównym jak zwykła aplikacja.',
  c1h: 'Otwórz Lunę w Chrome lub Edge', c1: 'Wejdź na luna-voice-coach.onrender.com.', c2h: 'Kliknij „Zainstaluj aplikację”', c2: 'Ikona na końcu paska adresu albo menu ⋮ → „Zainstaluj aplikację”.', c3h: 'Gotowe', c3: 'Luna otworzy się we własnym oknie.'},
 en: {h: 'Get the app', lead: 'Keep Luna close at hand – on your phone, with no ads.', btn: 'Download the app', btn_short: '📲 Download', play: 'Get it on Google Play', pc: 'Computer',
  a1h: 'Tap “Download the app”', a1: 'On your Android phone – Luna’s installation file will download.', a2h: 'Open the downloaded file', a2: 'If your phone asks, allow installs from this source. It’s a one-time, safe setting.', a3h: 'Tap “Install”', a3: 'Done! Luna appears on your home screen.',
  i1h: 'Open Luna in Safari', i1: 'Go to luna-voice-coach.onrender.com.', i2h: 'Tap “Share”', i2: 'It’s the square with an arrow at the bottom of the screen.', i3h: 'Choose “Add to Home Screen”', i3: 'Luna will live on your home screen like any other app.',
  c1h: 'Open Luna in Chrome or Edge', c1: 'Go to luna-voice-coach.onrender.com.', c2h: 'Click “Install app”', c2: 'Use the icon at the end of the address bar, or menu ⋮ → “Install app”.', c3h: 'Done', c3: 'Luna opens in her own window.'},
 es: {h: 'Descarga la app', lead: 'Luna siempre a mano: en tu móvil y sin anuncios.', btn: 'Descargar la app', btn_short: '📲 Descargar', play: 'Disponible en Google Play', pc: 'Ordenador',
  a1h: 'Toca «Descargar la app»', a1: 'En tu móvil Android: se descargará el archivo de instalación de Luna.', a2h: 'Abre el archivo descargado', a2: 'Si el móvil te lo pide, permite instalar desde esta fuente. Es un ajuste único y seguro.', a3h: 'Toca «Instalar»', a3: '¡Listo! Luna aparecerá en tu pantalla de inicio.',
  i1h: 'Abre Luna en Safari', i1: 'Entra en luna-voice-coach.onrender.com.', i2h: 'Toca «Compartir»', i2: 'Es el icono del cuadrado con una flecha, en la parte inferior.', i3h: 'Elige «Añadir a pantalla de inicio»', i3: 'Luna vivirá en tu pantalla de inicio como cualquier otra app.',
  c1h: 'Abre Luna en Chrome o Edge', c1: 'Entra en luna-voice-coach.onrender.com.', c2h: 'Haz clic en «Instalar aplicación»', c2: 'Usa el icono al final de la barra de direcciones o el menú ⋮ → «Instalar aplicación».', c3h: 'Listo', c3: 'Luna se abrirá en su propia ventana.'},
 de: {h: 'App herunterladen', lead: 'Luna immer griffbereit – auf dem Handy und ohne Werbung.', btn: 'App herunterladen', btn_short: '📲 Herunterladen', play: 'Jetzt bei Google Play', pc: 'Computer',
  a1h: 'Tippe auf „App herunterladen“', a1: 'Auf deinem Android-Handy wird die Installationsdatei von Luna heruntergeladen.', a2h: 'Öffne die heruntergeladene Datei', a2: 'Fragt dein Handy nach, erlaube Installationen aus dieser Quelle. Das ist eine einmalige, sichere Einstellung.', a3h: 'Tippe auf „Installieren“', a3: 'Fertig! Luna erscheint auf deinem Startbildschirm.',
  i1h: 'Öffne Luna in Safari', i1: 'Gehe auf luna-voice-coach.onrender.com.', i2h: 'Tippe auf „Teilen“', i2: 'Das ist das Quadrat mit dem Pfeil unten auf dem Bildschirm.', i3h: 'Wähle „Zum Home-Bildschirm“', i3: 'Luna wohnt dann auf deinem Startbildschirm wie jede andere App.',
  c1h: 'Öffne Luna in Chrome oder Edge', c1: 'Gehe auf luna-voice-coach.onrender.com.', c2h: 'Klicke auf „App installieren“', c2: 'Über das Symbol am Ende der Adressleiste oder Menü ⋮ → „App installieren“.', c3h: 'Fertig', c3: 'Luna öffnet sich in einem eigenen Fenster.'},
 uk: {h: 'Завантажте застосунок', lead: 'Луна завжди під рукою — на телефоні й без реклами.', btn: 'Завантажити застосунок', btn_short: '📲 Завантажити', play: 'Завантажити з Google Play', pc: 'Комп’ютер',
  a1h: 'Натисніть «Завантажити застосунок»', a1: 'На телефоні з Android завантажиться інсталяційний файл Луни.', a2h: 'Відкрийте завантажений файл', a2: 'Якщо телефон запитає, дозвольте встановлення з цього джерела. Це одноразове й безпечне налаштування.', a3h: 'Натисніть «Установити»', a3: 'Готово! Луна з’явиться на головному екрані.',
  i1h: 'Відкрийте Луну в Safari', i1: 'Перейдіть на luna-voice-coach.onrender.com.', i2h: 'Натисніть «Поділитися»', i2: 'Це значок квадрата зі стрілкою внизу екрана.', i3h: 'Виберіть «На початковий екран»', i3: 'Луна житиме на головному екрані, як звичайний застосунок.',
  c1h: 'Відкрийте Луну в Chrome або Edge', c1: 'Перейдіть на luna-voice-coach.onrender.com.', c2h: 'Натисніть «Установити застосунок»', c2: 'Значок у кінці адресного рядка або меню ⋮ → «Установити застосунок».', c3h: 'Готово', c3: 'Луна відкриється у власному вікні.'}};
let lang = 'pl'; try { lang = (new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || navigator.language || 'pl').slice(0, 2).toLowerCase(); } catch(e){}
if (!T[lang]) lang = 'pl';
const t = T[lang]; let play = '';
const ua = navigator.userAgent; const plat = /android/i.test(ua) ? 'android' : /iphone|ipad|ipod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) ? 'ios' : 'pc';
function apply(){
  document.querySelectorAll('[data-dl]').forEach(e => { const k = e.dataset.dl; if (t[k]) e.textContent = (k === 'btn' && play) ? t.play : t[k]; });
  const b = document.getElementById('dlBtn'); if (b && play) b.href = play;
}
function show(p){ document.querySelectorAll('.dl-tabs button').forEach(b => b.classList.toggle('on', b.dataset.p === p)); document.querySelectorAll('.dl-steps').forEach(o => o.hidden = o.dataset.panel !== p); }
document.querySelectorAll('.dl-tabs button').forEach(b => b.onclick = () => show(b.dataset.p));
const tabs = document.querySelector('.dl-tabs'); const first = tabs && tabs.querySelector(`[data-p="${plat}"]`); if (first) tabs.prepend(first);
show(plat); apply();
fetch('/api/config').then(r => r.json()).then(c => { play = (c.app && c.app.play_url) || ''; apply(); }).catch(() => {});
})();
