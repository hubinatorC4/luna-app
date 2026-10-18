/* Pomoc na żywo (v1.6.6) – pływający dymek na każdej stronie. Pierwsza linia: Asystent AI (FAQ). „Porozmawiaj z moderatorem”:
   na żywo tylko, gdy moderator naprawdę jest online (heartbeat panelu); inaczej „zostaw wiadomość” + formularz „Napisz do moderatora”.
   Wejścia: window.LunaHelpOpen(), window.LunaSupport.open('form'|'mine'), #napisz-do-moderatora, ?pomoc=formularz, /problemy.html. */
(() => {
if (window.__lunaHelp) return; window.__lunaHelp = 1;
const NOFAB = !!(document.currentScript && document.currentScript.dataset.nofab);
/* W ramce aplikacji (app.html) okno pomocy otwiera powłoka – tu tylko przekazujemy kliknięcia i parametry. */
try { if (window.top !== window && window.top.location.origin === location.origin && window.top.document.querySelector('script[src*="helpbot-loader"]')){
  const top = () => window.top.LunaSupport;
  window.LunaSupport = {open: v => top() && top().open(v)}; window.LunaHelpOpen = () => top() && top().open('chat');
  document.addEventListener('click', e => { const a = e.target.closest && e.target.closest('[data-support]'); if (a){ e.preventDefault(); window.LunaSupport.open(a.dataset.support); } });
  const qp0 = new URLSearchParams(location.search).get('pomoc');
  const go = v => setTimeout(() => window.LunaSupport.open(v), 400);
  if (location.hash === '#napisz-do-moderatora' || qp0 === 'formularz') go('form'); else if (qp0 === 'zgloszenia') go('mine');
  return; } } catch(e){}
const LS = ['pl', 'en', 'es', 'de', 'uk'];
const lang = (() => { let l = 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || document.documentElement.lang || navigator.language || 'pl'; } catch(e){} l = String(l).slice(0, 2).toLowerCase(); return LS.includes(l) ? l : 'pl'; })();
const I = {
pl: {title: 'Pomoc na żywo', sub: 'Asystent AI · odpowiada od razu', open: 'Otwórz Pomoc na żywo', close: 'Zamknij', back: 'Wróć do czatu', ph: 'Napisz pytanie…', send: 'Wyślij',
 hello: 'Cześć! Tu Asystent AI Luny 🤖💚 Nie jem, nie śpię i nie piję kawy, więc odpowiadam od razu. Gdy utknę – zawołam człowieka. Nigdy nie podawaj tu haseł, kodów BLIK ani numerów kart.',
 mod: '🙋 Porozmawiaj z moderatorem', form: '✉️ Napisz do moderatora', mine: '📬 Moje zgłoszenia', ai: 'Asystent AI', me: 'Ty', modName: 'Zespół Luny · Moderator',
 checking: 'Zaglądam, czy moderator jest przy biurku…', offline: 'Moderator jest teraz offline – zostaw wiadomość. Ludzie, w przeciwieństwie do Luny, czasem śpią 😴 Odpiszemy, gdy tylko wrócą.',
 honest: 'Moderatorzy to ludzie z Zespołu Luny – nie dyżurujemy 24/7, ale czytamy każdą wiadomość.', on: 'Moderator jest online! Od teraz piszesz z człowiekiem z Zespołu Luny. Czekaj chwilę na odpowiedź…',
 lost: 'Moderator właśnie odszedł od biurka (pewnie po herbatę – kawy nie pijemy 😄). Zostaw wiadomość, nic nie zginie.', closed: 'Moderator zakończył rozmowę. Dzięki, że piszesz! 💚', end: 'Zakończ rozmowę',
 consentLive: 'Pokaż moderatorowi moją rozmowę z Asystentem AI', consent: 'Dołącz rozmowę z czatu (pomaga szybciej zrozumieć sprawę)',
 fTitle: 'Napisz do moderatora', fLead: 'Opisz sprawę jak najlepszej przyjaciółce: konkretnie i bez owijania w bawełnę. Luna by tak chciała 😉',
 cat: 'Kategoria *', choose: 'Wybierz…', tTitle: 'Tytuł * (5–120 znaków)', tPh: 'np. Nie mogę się zalogować', desc: 'Opis * (20–4000 znaków)', dPh: 'Co się stało? Co robiłeś/-aś tuż przed? Im więcej szczegółów, tym szybciej pomożemy.',
 shot: 'Zrzut ekranu (opcjonalnie, obraz do 5 MB – usuwamy z niego dane EXIF)', email: 'E-mail do odpowiedzi (opcjonalnie)',
 rIn: 'Odpowiedź przyjdzie do Twojej Skrzynki 📬 w aplikacji – anonimowo, e-mail nie jest potrzebny.', rGuest: 'Nie jesteś zalogowany/-a: odpowiedź zobaczysz w „Moje zgłoszenia” na tym urządzeniu albo podaj e-mail.',
 submit: 'Wyślij do moderatora', sending: 'Wysyłam…',
 cats: {konto: 'Konto i logowanie', platnosci: 'Płatności i plany', naruszenie: 'Zgłoszenie naruszenia/użytkownika', bitwy: 'Bitwy i ranking', generator: 'Generator agentek', prywatnosc: 'Prywatność i dane (RODO)', casting: 'Casting/współpraca', blad: 'Błąd w aplikacji', inne: 'Inne'},
 e: {fast: 'Wow, szybciej niż Luna! 😄 Odczekaj sekundkę i wyślij jeszcze raz.', cat: 'Wybierz kategorię sprawy.', title: 'Tytuł musi mieć od 5 do 120 znaków.', desc: 'Opis musi mieć od 20 do 4000 znaków.', email: 'Podaj poprawny e-mail albo zostaw pole puste.', shot_type: 'Zrzut ekranu musi być obrazem (JPG, PNG lub WEBP).', shot_size: 'Zrzut ekranu jest za duży (maks. 5 MB).', rate: 'Za dużo zgłoszeń naraz – odczekaj chwilę.', net: 'Ups, nie udało się wysłać. Sprawdź internet i spróbuj ponownie.'},
 done: 'Gotowe! Twoje zgłoszenie ma numer', doneIn: 'Moderator już parzy herbatę ☕ Odpowiedź znajdziesz w Skrzynce 📬.', doneGuest: 'Zachowaj numer – odpowiedź zobaczysz w „Moje zgłoszenia” na tym urządzeniu.',
 empty: 'Pusto jak w lodówce Luny – a ona przecież nie je 😄 Nie masz jeszcze żadnych zgłoszeń.', st: {'nowe': 'nowe', 'w trakcie': 'w trakcie', 'rozwiązane': 'rozwiązane ✅'}, err: 'Ups, coś poszło nie tak. Spróbuj za chwilę.', online: 'Moderator online', offl: 'Moderator offline'},
en: {title: 'Live help', sub: 'AI assistant · replies instantly', open: 'Open live help', close: 'Close', back: 'Back to chat', ph: 'Type your question…', send: 'Send',
 hello: 'Hi! I’m Luna’s AI assistant 🤖💚 I don’t eat, sleep or drink coffee, so I reply right away. If I get stuck, I’ll call a human. Never share passwords, BLIK codes or card numbers here.',
 mod: '🙋 Talk to a moderator', form: '✉️ Write to a moderator', mine: '📬 My tickets', ai: 'AI assistant', me: 'You', modName: 'Luna Team · Moderator',
 checking: 'Checking whether a moderator is at the desk…', offline: 'The moderator is offline right now – leave a message. Unlike Luna, humans sometimes sleep 😴 We’ll reply as soon as they’re back.',
 honest: 'Moderators are real people from the Luna Team – we’re not on duty 24/7, but we read every message.', on: 'A moderator is online! From now on you’re chatting with a human from the Luna Team. Give them a moment…',
 lost: 'The moderator just stepped away (probably for tea – we don’t drink coffee 😄). Leave a message, nothing gets lost.', closed: 'The moderator ended the chat. Thanks for writing! 💚', end: 'End chat',
 consentLive: 'Show the moderator my chat with the AI assistant', consent: 'Attach the chat so far (helps us understand faster)',
 fTitle: 'Write to a moderator', fLead: 'Describe it like you would to your best friend: clear and straight to the point. Luna would approve 😉',
 cat: 'Category *', choose: 'Choose…', tTitle: 'Title * (5–120 characters)', tPh: 'e.g. I can’t sign in', desc: 'Description * (20–4000 characters)', dPh: 'What happened? What were you doing right before? The more detail, the faster we can help.',
 shot: 'Screenshot (optional, image up to 5 MB – we strip EXIF data)', email: 'Email for a reply (optional)',
 rIn: 'The reply will arrive in your in-app Inbox 📬 – anonymously, no email needed.', rGuest: 'You’re not signed in: you’ll see the reply under “My tickets” on this device, or add an email.',
 submit: 'Send to moderator', sending: 'Sending…',
 cats: {konto: 'Account & sign-in', platnosci: 'Payments & plans', naruszenie: 'Report a violation/user', bitwy: 'Battles & ranking', generator: 'Agent generator', prywatnosc: 'Privacy & data (GDPR)', casting: 'Casting/partnership', blad: 'App bug', inne: 'Other'},
 e: {fast: 'Wow, faster than Luna! 😄 Wait a second and send it again.', cat: 'Choose a category.', title: 'The title must be 5 to 120 characters.', desc: 'The description must be 20 to 4000 characters.', email: 'Enter a valid email or leave it empty.', shot_type: 'The screenshot must be an image (JPG, PNG or WEBP).', shot_size: 'The screenshot is too large (max 5 MB).', rate: 'Too many tickets at once – wait a moment.', net: 'Oops, couldn’t send. Check your connection and try again.'},
 done: 'Done! Your ticket number is', doneIn: 'The moderator is already brewing tea ☕ You’ll find the reply in your Inbox 📬.', doneGuest: 'Keep the number – you’ll see the reply under “My tickets” on this device.',
 empty: 'Empty as Luna’s fridge – and she doesn’t even eat 😄 You have no tickets yet.', st: {'nowe': 'new', 'w trakcie': 'in progress', 'rozwiązane': 'solved ✅'}, err: 'Oops, something went wrong. Please try again in a moment.', online: 'Moderator online', offl: 'Moderator offline'},
es: {title: 'Ayuda en directo', sub: 'Asistente IA · responde al instante', open: 'Abrir la ayuda en directo', close: 'Cerrar', back: 'Volver al chat', ph: 'Escribe tu pregunta…', send: 'Enviar',
 hello: '¡Hola! Soy el asistente IA de Luna 🤖💚 No como, no duermo ni tomo café, así que respondo enseguida. Si me atasco, llamo a una persona. Nunca compartas aquí contraseñas, códigos BLIK ni números de tarjeta.',
 mod: '🙋 Hablar con un moderador', form: '✉️ Escribir a un moderador', mine: '📬 Mis incidencias', ai: 'Asistente IA', me: 'Tú', modName: 'Equipo de Luna · Moderador',
 checking: 'Miro si hay un moderador en su mesa…', offline: 'El moderador está desconectado ahora mismo: deja un mensaje. A diferencia de Luna, las personas a veces duermen 😴 Responderemos en cuanto vuelvan.',
 honest: 'Los moderadores son personas del Equipo de Luna: no estamos de guardia 24/7, pero leemos cada mensaje.', on: '¡Hay un moderador conectado! A partir de ahora hablas con una persona del Equipo de Luna. Dale un momento…',
 lost: 'El moderador acaba de levantarse (seguramente a por té, que café no tomamos 😄). Deja un mensaje, no se pierde nada.', closed: 'El moderador ha cerrado la conversación. ¡Gracias por escribir! 💚', end: 'Terminar chat',
 consentLive: 'Mostrar al moderador mi chat con el asistente IA', consent: 'Adjuntar la conversación (nos ayuda a entenderlo antes)',
 fTitle: 'Escribir a un moderador', fLead: 'Cuéntalo como a tu mejor amiga: claro y sin rodeos. A Luna le encantaría 😉',
 cat: 'Categoría *', choose: 'Elige…', tTitle: 'Título * (5–120 caracteres)', tPh: 'p. ej. No puedo iniciar sesión', desc: 'Descripción * (20–4000 caracteres)', dPh: '¿Qué ha pasado? ¿Qué hacías justo antes? Cuantos más detalles, antes te ayudamos.',
 shot: 'Captura de pantalla (opcional, imagen de hasta 5 MB; eliminamos los datos EXIF)', email: 'Correo para la respuesta (opcional)',
 rIn: 'La respuesta llegará a tu Buzón 📬 en la app, de forma anónima; no hace falta correo.', rGuest: 'No has iniciado sesión: verás la respuesta en «Mis incidencias» en este dispositivo, o añade un correo.',
 submit: 'Enviar al moderador', sending: 'Enviando…',
 cats: {konto: 'Cuenta e inicio de sesión', platnosci: 'Pagos y planes', naruszenie: 'Denunciar una infracción/usuario', bitwy: 'Batallas y ranking', generator: 'Generador de agentes', prywatnosc: 'Privacidad y datos (RGPD)', casting: 'Casting/colaboración', blad: 'Error en la app', inne: 'Otros'},
 e: {fast: '¡Vaya, más rápido que Luna! 😄 Espera un segundo y vuelve a enviarlo.', cat: 'Elige una categoría.', title: 'El título debe tener entre 5 y 120 caracteres.', desc: 'La descripción debe tener entre 20 y 4000 caracteres.', email: 'Introduce un correo válido o deja el campo vacío.', shot_type: 'La captura debe ser una imagen (JPG, PNG o WEBP).', shot_size: 'La captura es demasiado grande (máx. 5 MB).', rate: 'Demasiadas incidencias a la vez: espera un momento.', net: 'Vaya, no se pudo enviar. Revisa la conexión e inténtalo de nuevo.'},
 done: '¡Listo! Tu número de incidencia es', doneIn: 'El moderador ya está preparando té ☕ Encontrarás la respuesta en tu Buzón 📬.', doneGuest: 'Guarda el número: verás la respuesta en «Mis incidencias» en este dispositivo.',
 empty: 'Vacío como la nevera de Luna, y eso que ella no come 😄 Aún no tienes incidencias.', st: {'nowe': 'nueva', 'w trakcie': 'en curso', 'rozwiązane': 'resuelta ✅'}, err: 'Vaya, algo ha fallado. Inténtalo de nuevo en un momento.', online: 'Moderador conectado', offl: 'Moderador desconectado'},
de: {title: 'Live-Hilfe', sub: 'KI-Assistent · antwortet sofort', open: 'Live-Hilfe öffnen', close: 'Schließen', back: 'Zurück zum Chat', ph: 'Schreib deine Frage…', send: 'Senden',
 hello: 'Hallo! Ich bin Lunas KI-Assistent 🤖💚 Ich esse nicht, schlafe nicht und trinke keinen Kaffee – darum antworte ich sofort. Wenn ich nicht weiterweiß, hole ich einen Menschen. Teile hier niemals Passwörter, BLIK-Codes oder Kartennummern.',
 mod: '🙋 Mit der Moderation sprechen', form: '✉️ Der Moderation schreiben', mine: '📬 Meine Tickets', ai: 'KI-Assistent', me: 'Du', modName: 'Luna-Team · Moderation',
 checking: 'Ich schaue, ob jemand von der Moderation am Schreibtisch sitzt…', offline: 'Die Moderation ist gerade offline – hinterlass eine Nachricht. Anders als Luna schlafen Menschen manchmal 😴 Wir antworten, sobald sie zurück sind.',
 honest: 'Die Moderation sind echte Menschen aus dem Luna-Team – nicht rund um die Uhr, aber wir lesen jede Nachricht.', on: 'Die Moderation ist online! Ab jetzt schreibst du mit einem Menschen aus dem Luna-Team. Einen Moment Geduld…',
 lost: 'Die Moderation ist gerade kurz weg (bestimmt Tee holen – Kaffee trinken wir nicht 😄). Hinterlass eine Nachricht, nichts geht verloren.', closed: 'Die Moderation hat den Chat beendet. Danke fürs Schreiben! 💚', end: 'Chat beenden',
 consentLive: 'Der Moderation meinen Chat mit dem KI-Assistenten zeigen', consent: 'Bisherigen Chat anhängen (hilft, schneller zu verstehen)',
 fTitle: 'Der Moderation schreiben', fLead: 'Beschreib es wie deiner besten Freundin: klar und ohne Umschweife. Luna würde es so wollen 😉',
 cat: 'Kategorie *', choose: 'Auswählen…', tTitle: 'Titel * (5–120 Zeichen)', tPh: 'z. B. Ich kann mich nicht anmelden', desc: 'Beschreibung * (20–4000 Zeichen)', dPh: 'Was ist passiert? Was hast du direkt davor gemacht? Je mehr Details, desto schneller helfen wir.',
 shot: 'Screenshot (optional, Bild bis 5 MB – EXIF-Daten werden entfernt)', email: 'E-Mail für eine Antwort (optional)',
 rIn: 'Die Antwort kommt in dein Postfach 📬 in der App – anonym, ohne E-Mail.', rGuest: 'Du bist nicht angemeldet: Die Antwort siehst du unter „Meine Tickets“ auf diesem Gerät, oder gib eine E-Mail an.',
 submit: 'An die Moderation senden', sending: 'Wird gesendet…',
 cats: {konto: 'Konto & Anmeldung', platnosci: 'Zahlungen & Pläne', naruszenie: 'Verstoß/Nutzer melden', bitwy: 'Battles & Ranking', generator: 'Agentinnen-Generator', prywatnosc: 'Datenschutz & Daten (DSGVO)', casting: 'Casting/Zusammenarbeit', blad: 'Fehler in der App', inne: 'Sonstiges'},
 e: {fast: 'Wow, schneller als Luna! 😄 Warte eine Sekunde und sende es noch einmal.', cat: 'Wähle eine Kategorie.', title: 'Der Titel muss 5 bis 120 Zeichen lang sein.', desc: 'Die Beschreibung muss 20 bis 4000 Zeichen lang sein.', email: 'Gib eine gültige E-Mail an oder lass das Feld leer.', shot_type: 'Der Screenshot muss ein Bild sein (JPG, PNG oder WEBP).', shot_size: 'Der Screenshot ist zu groß (max. 5 MB).', rate: 'Zu viele Tickets auf einmal – warte kurz.', net: 'Hoppla, Senden fehlgeschlagen. Prüfe deine Verbindung und versuch es erneut.'},
 done: 'Fertig! Deine Ticketnummer lautet', doneIn: 'Die Moderation kocht schon Tee ☕ Die Antwort findest du im Postfach 📬.', doneGuest: 'Notier dir die Nummer – die Antwort siehst du unter „Meine Tickets“ auf diesem Gerät.',
 empty: 'Leer wie Lunas Kühlschrank – und sie isst ja nicht mal 😄 Du hast noch keine Tickets.', st: {'nowe': 'neu', 'w trakcie': 'in Bearbeitung', 'rozwiązane': 'gelöst ✅'}, err: 'Hoppla, da ist etwas schiefgelaufen. Versuch es gleich noch einmal.', online: 'Moderation online', offl: 'Moderation offline'},
uk: {title: 'Допомога наживо', sub: 'ШІ-асистент · відповідає одразу', open: 'Відкрити допомогу наживо', close: 'Закрити', back: 'Назад до чату', ph: 'Напишіть запитання…', send: 'Надіслати',
 hello: 'Привіт! Я ШІ-асистент Луни 🤖💚 Я не їм, не сплю й не п’ю кави, тож відповідаю одразу. Якщо застрягну — покличу людину. Ніколи не повідомляйте тут паролі, коди BLIK чи номери карток.',
 mod: '🙋 Поговорити з модератором', form: '✉️ Написати модератору', mine: '📬 Мої звернення', ai: 'ШІ-асистент', me: 'Ви', modName: 'Команда Луни · Модератор',
 checking: 'Дивлюся, чи модератор на місці…', offline: 'Модератор зараз офлайн — залиште повідомлення. На відміну від Луни, люди іноді сплять 😴 Відповімо, щойно вони повернуться.',
 honest: 'Модератори — справжні люди з Команди Луни: ми не чергуємо 24/7, але читаємо кожне повідомлення.', on: 'Модератор онлайн! Відтепер ви пишете людині з Команди Луни. Зачекайте хвилинку…',
 lost: 'Модератор щойно відійшов (мабуть, по чай — кави ми не п’ємо 😄). Залиште повідомлення, нічого не загубиться.', closed: 'Модератор завершив розмову. Дякуємо, що написали! 💚', end: 'Завершити чат',
 consentLive: 'Показати модератору мою розмову з ШІ-асистентом', consent: 'Додати розмову з чату (допомагає швидше зрозуміти справу)',
 fTitle: 'Написати модератору', fLead: 'Опишіть справу, як найкращій подрузі: конкретно й без зайвого. Луні б це сподобалося 😉',
 cat: 'Категорія *', choose: 'Оберіть…', tTitle: 'Заголовок * (5–120 символів)', tPh: 'напр. Не можу увійти', desc: 'Опис * (20–4000 символів)', dPh: 'Що сталося? Що ви робили перед цим? Чим більше деталей, тим швидше допоможемо.',
 shot: 'Знімок екрана (необов’язково, зображення до 5 МБ — дані EXIF видаляємо)', email: 'E-mail для відповіді (необов’язково)',
 rIn: 'Відповідь надійде у вашу Скриньку 📬 у застосунку — анонімно, e-mail не потрібен.', rGuest: 'Ви не увійшли: відповідь побачите в «Мої звернення» на цьому пристрої або вкажіть e-mail.',
 submit: 'Надіслати модератору', sending: 'Надсилаю…',
 cats: {konto: 'Акаунт і вхід', platnosci: 'Платежі й плани', naruszenie: 'Скарга на порушення/користувача', bitwy: 'Битви й рейтинг', generator: 'Генератор агенток', prywatnosc: 'Приватність і дані (GDPR)', casting: 'Кастинг/співпраця', blad: 'Помилка в застосунку', inne: 'Інше'},
 e: {fast: 'Ого, швидше за Луну! 😄 Зачекайте секунду й надішліть ще раз.', cat: 'Оберіть категорію.', title: 'Заголовок має містити від 5 до 120 символів.', desc: 'Опис має містити від 20 до 4000 символів.', email: 'Вкажіть правильний e-mail або залиште поле порожнім.', shot_type: 'Знімок екрана має бути зображенням (JPG, PNG або WEBP).', shot_size: 'Знімок екрана завеликий (макс. 5 МБ).', rate: 'Забагато звернень одразу — зачекайте хвилинку.', net: 'Ой, не вдалося надіслати. Перевірте інтернет і спробуйте ще раз.'},
 done: 'Готово! Номер вашого звернення', doneIn: 'Модератор уже заварює чай ☕ Відповідь знайдете у Скриньці 📬.', doneGuest: 'Збережіть номер — відповідь побачите в «Мої звернення» на цьому пристрої.',
 empty: 'Порожньо, як у холодильнику Луни, — а вона ж не їсть 😄 У вас ще немає звернень.', st: {'nowe': 'нове', 'w trakcie': 'у роботі', 'rozwiązane': 'вирішено ✅'}, err: 'Ой, щось пішло не так. Спробуйте трохи згодом.', online: 'Модератор онлайн', offl: 'Модератор офлайн'}};
const T = I[lang];
const CATS = ['konto', 'platnosci', 'naruszenie', 'bitwy', 'generator', 'prywatnosc', 'casting', 'blad', 'inne'];
const css = `.hb-fab{position:fixed;right:18px;bottom:18px;z-index:80;width:58px;height:58px;border-radius:50%;border:0;background:radial-gradient(circle at 30% 30%,#3ee68a,#1f9d57);color:#06120b;font-size:26px;box-shadow:0 14px 30px -10px rgba(46,204,113,.6);cursor:pointer}
.hb-win{position:fixed;right:18px;bottom:88px;z-index:81;width:380px;height:600px;max-height:calc(100vh - 110px);display:flex;flex-direction:column;background:#111613;color:#eee;border:1px solid #26332b;border-radius:var(--r-modal,24px);box-shadow:0 30px 80px -20px rgba(0,0,0,.8);overflow:hidden;font-family:var(--font-ui,system-ui)}
.hb-win[hidden],.hb-v[hidden],.hb-win [hidden]{display:none!important}.hb-h{display:flex;align-items:center;gap:10px;padding:12px 14px;background:linear-gradient(135deg,#17241c,#111613);border-bottom:1px solid #26332b}
.hb-h img{width:34px;height:34px;border-radius:50%}.hb-h b{flex:1;font-size:15px}.hb-h small{display:block;font-weight:400;color:#9fb5a8;font-size:11.5px}
.hb-x,.hb-bk{background:none;border:0;color:#ccc;font-size:20px;cursor:pointer;border-radius:50%;width:36px;height:36px;flex:none}.hb-x:focus-visible,.hb-bk:focus-visible,.hb-win button:focus-visible{outline:2px solid #3ee68a;outline-offset:2px}
.hb-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#7a857f;margin-right:5px;vertical-align:middle}.hb-dot.on{background:#3ee68a;box-shadow:0 0 0 3px rgba(62,230,138,.2)}
.hb-v{flex:1;display:flex;flex-direction:column;min-height:0}.hb-log{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.hb-m{max-width:85%;padding:9px 13px;border-radius:18px;font-size:14px;line-height:1.45;white-space:pre-wrap;word-wrap:break-word;animation:hbpop .25s var(--ease,ease)}
.hb-m small{display:block;font-size:11px;opacity:.7;margin-bottom:2px;font-weight:700}
.hb-m.bot{background:#1b251f;align-self:flex-start;border-bottom-left-radius:6px}.hb-m.mod{background:#2a2140;border:1px solid #4b3a7a;align-self:flex-start;border-bottom-left-radius:6px}
.hb-m.sys{align-self:center;background:#1a1f1c;border:1px dashed #33443a;color:#cfe;font-size:13px;text-align:center;max-width:95%}
.hb-m.me{background:#2ecc71;color:#06120b;align-self:flex-end;border-bottom-right-radius:6px}
@keyframes hbpop{from{transform:scale(.92);opacity:0}to{transform:none;opacity:1}}@media (prefers-reduced-motion:reduce){.hb-m{animation:none}}
.hb-typing{align-self:flex-start;color:#9fb5a8;font-size:20px;letter-spacing:2px;padding:0 8px}.hb-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 8px}
.hb-chips button,.hb-act button{background:#1b251f;border:1px solid #2c3b31;color:#dfe;border-radius:999px;padding:7px 12px;font-size:12.5px;cursor:pointer;min-height:34px}
.hb-act{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 8px}.hb-act .mod{border-color:#ff9a3c;color:#ffc58f}.hb-act .frm{border-color:#8b5cf6;color:#d8c8ff}
.hb-f{display:flex;gap:8px;padding:10px;border-top:1px solid #26332b}.hb-f input{flex:1;min-width:0;background:#0c100e;color:#eee;border:1px solid #2c3b31;border-radius:16px;padding:10px 12px;font-size:16px}
.hb-f button,.hb-go{background:#2ecc71;border:0;color:#06120b;font-weight:800;border-radius:999px;padding:0 16px;cursor:pointer;min-height:42px}
.hb-form{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}.hb-form h3{margin:0;font-size:18px}.hb-form p{margin:0;color:#b9cbbf;font-size:13px;line-height:1.45}
.hb-form label{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:700;color:#dfe}.hb-form label.ck{flex-direction:row;align-items:flex-start;gap:8px;font-weight:400}
.hb-form input:not([type=checkbox]),.hb-form select,.hb-form textarea{background:#0c100e;color:#eee;border:1px solid #2c3b31;border-radius:16px;padding:10px 12px;font-size:16px;font-family:inherit}
.hb-form [aria-invalid=true]{border-color:#ff6b6b}.hb-form .cnt{font-weight:400;color:#8fa597;font-size:11.5px;align-self:flex-end}.hb-form .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.hb-err{color:#ffb3a7;font-size:13px;min-height:1em}.hb-go{padding:12px 18px;font-size:15px}.hb-go:disabled{opacity:.6}
.hb-done{background:#13241a;border:1px solid #2e6b46;border-radius:20px;padding:14px;text-align:center}.hb-done b{font-size:22px;display:block;margin:6px 0;color:#7dffa8;user-select:all}
.hb-tk{background:#161d19;border:1px solid #26332b;border-radius:18px;padding:10px 12px;font-size:13px}.hb-tk b{display:block}.hb-tk .r{margin-top:6px;padding:8px 10px;background:#2a2140;border-radius:14px;white-space:pre-wrap}
@media (max-width:600px){.hb-win{right:0;left:0;bottom:0;width:auto;height:86vh;max-height:86vh;border-radius:24px 24px 0 0}.hb-fab{bottom:14px;right:14px}}`;
const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
const fab = document.createElement('button'); fab.className = 'hb-fab'; fab.type = 'button'; fab.setAttribute('aria-label', T.open); fab.setAttribute('aria-haspopup', 'dialog'); fab.textContent = '💬';
const w = document.createElement('section'); w.className = 'hb-win'; w.hidden = true; w.setAttribute('role', 'dialog'); w.setAttribute('aria-label', T.title);
const catOpts = CATS.map(c => `<option value="${c}">${T.cats[c]}</option>`).join('');
w.innerHTML = `<div class="hb-h"><button class="hb-bk" type="button" aria-label="${T.back}" hidden>←</button><img src="/brand-emblem-96.webp" alt=""><b><span class="hb-ttl">${T.title}</span><small class="hb-sub">${T.sub}</small></b><button class="hb-x" type="button" aria-label="${T.close}">✕</button></div>
<div class="hb-v hb-chat"><div class="hb-log" aria-live="polite"></div><div class="hb-chips"></div>
<div class="hb-act"><button type="button" class="mod">${T.mod}</button><button type="button" class="frm">${T.form}</button><button type="button" class="mn">${T.mine}</button><button type="button" class="endl" hidden>${T.end}</button></div>
<form class="hb-f"><input maxlength="500" placeholder="${T.ph}" aria-label="${T.ph}" enterkeyhint="send"><button type="submit">${T.send}</button></form></div>
<div class="hb-v hb-fv" hidden><form class="hb-form" novalidate><h3>${T.fTitle}</h3><p>${T.fLead}</p>
<label>${T.cat}<select name="category" required><option value="">${T.choose}</option>${catOpts}</select></label>
<label>${T.tTitle}<input name="title" required minlength="5" maxlength="120" placeholder="${T.tPh}" autocomplete="off"><span class="cnt" data-for="title">0/120</span></label>
<label>${T.desc}<textarea name="description" required minlength="20" maxlength="4000" rows="5" placeholder="${T.dPh}"></textarea><span class="cnt" data-for="description">0/4000</span></label>
<label>${T.shot}<input name="shot" type="file" accept="image/png,image/jpeg,image/webp"></label>
<label>${T.email}<input name="email" type="email" maxlength="254" autocomplete="email" inputmode="email"></label>
<p class="hb-reply"></p>
<label class="ck hb-ckw" hidden><input type="checkbox" name="consent" checked><span>${T.consent}</span></label>
<label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
<p class="hb-err" role="alert"></p><button class="hb-go" type="submit">${T.submit}</button><p style="font-size:12px">${T.honest}</p></form></div>
<div class="hb-v hb-dv" hidden><div class="hb-form"><div class="hb-done" role="status"></div></div></div>
<div class="hb-v hb-mv" hidden><div class="hb-form hb-mlist" aria-live="polite"></div></div>`;
document.body.append(w); if (!NOFAB) document.body.appendChild(fab);
const $ = s => w.querySelector(s);
const log = $('.hb-log'), inp = $('.hb-f input'), chips = $('.hb-chips'), sub = $('.hb-sub'), bk = $('.hb-bk');
const tr = []; let started = false, sid = '', since = 0, pollT = 0, loggedIn = false, t0 = Date.now(), offlineShown = false;
const store = (k, v) => { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); localStorage.setItem(k, JSON.stringify(v)); } catch(e){ return null; } };
function add(t, who, label){ const d = document.createElement('div'); d.className = 'hb-m ' + who; if (label){ const s = document.createElement('small'); s.textContent = label; d.appendChild(s); } d.appendChild(document.createTextNode(t)); log.appendChild(d); log.scrollTop = log.scrollHeight; if (who !== 'sys') tr.push({who: who === 'me' ? 'me' : who === 'mod' ? 'mod' : 'ai', t}); return d; }
function view(v){ ['chat', 'fv', 'dv', 'mv'].forEach(n => $('.hb-' + n).hidden = n !== v); bk.hidden = v === 'chat'; if (v === 'chat') setTimeout(() => inp.focus(), 30); }
function setSub(online, live){ sub.innerHTML = ''; const d = document.createElement('span'); d.className = 'hb-dot' + (online ? ' on' : ''); sub.append(d, document.createTextNode(live ? T.modName : (T.sub + ' · ' + (online ? T.online : T.offl)))); }
async function status(){ try { const d = await (await fetch('/api/support/status', {credentials: 'same-origin'})).json(); loggedIn = !!d.login; setSub(d.online, !!sid); return d; } catch(e){ return {online: false}; } }
function start(){ if (started) return; started = true;
  add(T.hello, 'bot', T.ai); status();
  fetch('/api/help/chips?lang=' + lang).then(r => r.json()).then(d => { (d.chips || []).forEach(c => { const b = document.createElement('button'); b.type = 'button'; b.textContent = c.label; b.onclick = () => ask(c.label); chips.appendChild(b); }); }).catch(() => {});
  const s = store('luna.sup.sid'); if (s && /^[0-9a-f]{24}$/.test(s)){ sid = s; since = 0; liveMode(true); poll(); } }
async function ask(q){
  q = String(q).trim(); if (!q) return; inp.value = '';
  if (sid){ add(q, 'me', T.me); try { const r = await fetch('/api/support/live', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'send', sid, text: q})}); const d = await r.json();
      if (d.msg) since = Math.max(since, d.msg.t); if (d.closed) endLive(T.closed); else if (d.online === false) offlineHint(); } catch(e){ add(T.err, 'sys'); } return; }
  add(q, 'me', T.me);
  const ty = document.createElement('div'); ty.className = 'hb-typing'; ty.textContent = '•••'; ty.setAttribute('aria-hidden', 'true'); log.appendChild(ty);
  try { const r = await fetch('/api/help', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({q, lang})}); const d = await r.json(); ty.remove();
    if (d.sensitive) tr[tr.length - 1].t = '***';
    add(d.reply || d.error || T.err, 'bot', T.ai); }
  catch(e){ ty.remove(); add(T.err, 'sys'); }
}
function offlineHint(){ if (offlineShown) return; offlineShown = true; add(T.lost, 'sys'); }
function liveMode(on){ $('.hb-act .mod').hidden = on; $('.endl').hidden = !on; chips.hidden = on; setSub(true, on); }
function endLive(msg){ clearTimeout(pollT); sid = ''; store('luna.sup.sid', ''); liveMode(false); status(); if (msg) add(msg, 'sys'); }
async function poll(){ clearTimeout(pollT); if (!sid) return;
  try { const r = await fetch('/api/support/live?sid=' + sid + '&since=' + since); const d = await r.json();
    if (r.status === 404){ endLive(''); return; }
    (d.msgs || []).forEach(m => { since = Math.max(since, m.t); if (m.from === 'mod') add(m.text, 'mod', T.modName); else if (m.from === 'system') {} else if (!w.dataset.echo) add(m.text, 'me', T.me); });
    w.dataset.echo = '1';
    if (d.closed){ endLive(T.closed); return; }
    if (!d.online) offlineHint(); else offlineShown = false;
  } catch(e){}
  pollT = setTimeout(poll, document.hidden || w.hidden ? 10000 : 3000);
}
async function talkToMod(){
  const chk = add(T.checking, 'sys'); const d = await status();
  if (!d.online){ chk.remove(); add(T.offline, 'sys'); offerForm(); return; }
  chk.remove();
  const consent = confirm(T.consentLive + '?');
  try { const r = await fetch('/api/support/live', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'start', lang, transcript_consent: consent, transcript: tr.slice(-20)})});
    const j = await r.json(); if (!j.sid){ add(T.offline, 'sys'); offerForm(); return; }
    sid = j.sid; since = 0; w.dataset.echo = '1'; store('luna.sup.sid', sid); liveMode(true); add(T.on, 'sys'); add(T.honest, 'sys'); poll();
  } catch(e){ add(T.err, 'sys'); }
}
function offerForm(){ const b = document.createElement('button'); b.type = 'button'; b.className = 'hb-go'; b.style.alignSelf = 'center'; b.textContent = T.form; b.onclick = () => openForm(true); log.appendChild(b); log.scrollTop = log.scrollHeight; }
async function openForm(fromChat){ const f = $('.hb-form'); $('.hb-ckw').hidden = !(fromChat && tr.some(m => m.who === 'me')); $('.hb-err').textContent = ''; t0 = Date.now();
  await status(); $('.hb-reply').textContent = loggedIn ? T.rIn : T.rGuest; view('fv'); setTimeout(() => f.category.focus(), 30); }
const F = $('.hb-form');
F.querySelectorAll('[name=title],[name=description]').forEach(el => el.addEventListener('input', () => { const c = F.querySelector(`.cnt[data-for=${el.name}]`); c.textContent = el.value.length + '/' + el.maxLength; el.removeAttribute('aria-invalid'); }));
F.category.addEventListener('change', () => F.category.removeAttribute('aria-invalid'));
const readImg = file => new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = no; r.readAsDataURL(file); });
F.addEventListener('submit', async e => { e.preventDefault(); const err = $('.hb-err'); err.textContent = '';
  const bad = (el, k) => { el.setAttribute('aria-invalid', 'true'); el.focus(); err.textContent = T.e[k]; };
  const title = F.title.value.trim(), desc = F.description.value.trim(), email = F.email.value.trim(), file = F.shot.files[0];
  if (!F.category.value) return bad(F.category, 'cat');
  if (title.length < 5 || title.length > 120) return bad(F.title, 'title');
  if (desc.length < 20 || desc.length > 4000) return bad(F.description, 'desc');
  if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) return bad(F.email, 'email');
  let shot = '';
  if (file){ if (!/^image\/(png|jpeg|webp)$/.test(file.type)) return bad(F.shot, 'shot_type'); if (file.size > 5 * 1024 * 1024) return bad(F.shot, 'shot_size'); shot = await readImg(file); }
  const go = F.querySelector('.hb-go'); go.disabled = true; go.textContent = T.sending;
  const consent = !$('.hb-ckw').hidden && F.consent.checked;
  try { const r = await fetch('/api/support/ticket', {method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({category: F.category.value, title, description: desc, email, screenshot: shot, website: F.website.value, t0, lang,
      transcript_consent: consent, transcript: consent ? tr.slice(-40) : [], env: {page: location.pathname, lang, ua: navigator.userAgent.slice(0, 200), screen: screen.width + 'x' + screen.height}})});
    const d = await r.json();
    if (!r.ok || !d.ok){ const k = d.code && T.e[d.code] ? d.code : (r.status === 429 ? 'rate' : ''); if (k && F[{cat: 'category', title: 'title', desc: 'description', email: 'email', shot_type: 'shot', shot_size: 'shot'}[k]]) bad(F[{cat: 'category', title: 'title', desc: 'description', email: 'email', shot_type: 'shot', shot_size: 'shot'}[k]], k); else err.textContent = k ? T.e[k] : (d.error || T.e.net); return; }
    if (d.key){ const m = store('luna.sup.tk') || []; m.unshift(d.id + ':' + d.key); store('luna.sup.tk', m.slice(0, 20)); }
    const box = $('.hb-done'); box.textContent = ''; const p1 = document.createElement('p'); p1.textContent = T.done; const b = document.createElement('b'); b.textContent = d.id; const p2 = document.createElement('p'); p2.textContent = d.inbox ? T.doneIn : T.doneGuest;
    const bm = document.createElement('button'); bm.type = 'button'; bm.className = 'hb-go'; bm.textContent = T.mine; bm.onclick = mine; box.append(p1, b, p2, bm);
    F.reset(); F.querySelectorAll('.cnt').forEach(c => c.textContent = '0/' + (c.dataset.for === 'title' ? 120 : 4000)); view('dv');
  } catch(e2){ err.textContent = T.e.net; }
  finally { go.disabled = false; go.textContent = T.submit; }
});
async function mine(){ view('mv'); const L = $('.hb-mlist'); L.textContent = '…';
  try { const k = (store('luna.sup.tk') || []).join(','); const d = await (await fetch('/api/support/mine?k=' + encodeURIComponent(k), {credentials: 'same-origin'})).json(); L.textContent = '';
    const h = document.createElement('h3'); h.textContent = T.mine.replace(/^\S+\s/, ''); L.appendChild(h);
    if (!(d.items || []).length){ const p = document.createElement('p'); p.textContent = T.empty; L.appendChild(p); return; }
    d.items.forEach(t => { const c = document.createElement('div'); c.className = 'hb-tk'; const b = document.createElement('b'); b.textContent = t.id + ' · ' + (t.title || ''); const s = document.createElement('span'); s.textContent = (T.st[t.status] || t.status) + ' · ' + new Date(t.updated * 1000).toLocaleString(lang);
      c.append(b, s); (t.thread || []).forEach(m => { const r = document.createElement('div'); r.className = 'r'; const sm = document.createElement('small'); sm.textContent = T.modName + ': '; sm.style.fontWeight = '700'; r.append(sm, document.createTextNode(m.text)); c.appendChild(r); }); L.appendChild(c); });
  } catch(e){ L.textContent = T.err; } }
$('.hb-act .mod').onclick = talkToMod; $('.hb-act .frm').onclick = () => openForm(true); $('.hb-act .mn').onclick = mine;
$('.endl').onclick = async () => { const s = sid; endLive(T.closed); try { await fetch('/api/support/live', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'end', sid: s})}); } catch(e){} };
bk.onclick = () => view('chat');
$('.hb-f').onsubmit = e => { e.preventDefault(); ask(inp.value); };
const toggle = on => { w.hidden = !on; fab.setAttribute('aria-expanded', String(on)); if (on){ start(); if (!$('.hb-chat').hidden) setTimeout(() => inp.focus(), 50); if (sid) poll(); } else if (!NOFAB) fab.focus(); };
fab.onclick = () => toggle(w.hidden); $('.hb-x').onclick = () => toggle(false);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !w.hidden) toggle(false); });
window.LunaHelpOpen = () => toggle(true);
window.LunaSupport = {open: v => { toggle(true); if (v === 'form') openForm(false); else if (v === 'mine') mine(); else view('chat'); }};
document.addEventListener('click', e => { const a = e.target.closest && e.target.closest('[data-support]'); if (a){ e.preventDefault(); window.LunaSupport.open(a.dataset.support); } });
const qp = new URLSearchParams(location.search).get('pomoc');
if (location.hash === '#napisz-do-moderatora' || qp === 'formularz') window.LunaSupport.open('form');
else if (qp === 'zgloszenia') window.LunaSupport.open('mine');
else if (/\/problemy(\.html)?$/.test(location.pathname) || qp === 'czat') toggle(true);
})();
