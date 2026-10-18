# -*- coding: utf-8 -*-
"""Pomoc Luny · bot AI – odpowiedzi z edytowalnej bazy FAQ (panel admina). Z LLM (jeśli skonfigurowany) wyłącznie na podstawie FAQ,
inaczej dopasowanie słów kluczowych. Nie wymyśla cen ani zasad, nie prosi o hasła, kody BLIK ani numery kart."""
import json, os, re, threading, time, unicodedata, urllib.request
import store
LANGS = ("pl", "en", "es", "de", "uk")
_lock = threading.Lock()

def F(id_, kw, pl, en, es, de, uk, chip=None):
    return {"id": id_, "keywords": kw, "answers": {"pl": pl, "en": en, "es": es, "de": de, "uk": uk}, "chip": chip or {}}

DEFAULT = [
 F("platnosci", "płatność płacić zapłacić kupić zakup blik karta checkout stripe pay payment buy purchase pagar pago comprar zahlen kaufen zahlung оплата платити купити",
   "Płatność w 3 krokach: 1) w Butiku lub Cenniku kliknij „Zapłać BLIK-iem”, 2) w aplikacji banku wygeneruj 6-cyfrowy kod BLIK, 3) wpisz go i potwierdź płatność w banku. Dostęp włącza się automatycznie. W aplikacji z Google Play płacisz przez Google Play. Uwaga: płatności jeszcze nie działają – startują wkrótce, a do tego czasu przyciski zakupu są oznaczone „wkrótce”. Testerzy dostają Premium za darmo.",
   "Paying in 3 steps: 1) in the Boutique or Prices tab, click “Pay with BLIK”, 2) generate a 6-digit BLIK code in your banking app, 3) enter it and confirm the payment in your bank. Access is switched on automatically. In the Google Play app, you pay through Google Play. Note: payments aren’t live yet – they’re launching soon, and until then the buy buttons say “soon”. Testers get Premium for free.",
   "Pago en 3 pasos: 1) en la Boutique o en Precios, haz clic en «Pagar con BLIK», 2) genera un código BLIK de 6 dígitos en la app de tu banco, 3) introdúcelo y confirma el pago en el banco. El acceso se activa automáticamente. En la app de Google Play pagas a través de Google Play. Nota: los pagos aún no están activos; llegarán pronto y, hasta entonces, los botones de compra indican «pronto». Los testers reciben Premium gratis.",
   "Bezahlen in 3 Schritten: 1) Klicke in der Boutique oder bei den Preisen auf „Mit BLIK bezahlen“, 2) erzeuge in deiner Banking-App einen 6-stelligen BLIK-Code, 3) gib ihn ein und bestätige die Zahlung in deiner Bank. Der Zugang wird automatisch freigeschaltet. In der Google-Play-App bezahlst du über Google Play. Hinweis: Zahlungen sind noch nicht aktiv – sie starten in Kürze, bis dahin zeigen die Kauf-Buttons „bald“. Tester bekommen Premium gratis.",
   "Оплата у 3 кроки: 1) у Бутику або в розділі «Ціни» натисніть «Оплатити через BLIK», 2) згенеруйте 6-значний код BLIK у застосунку банку, 3) введіть його й підтвердьте платіж у банку. Доступ увімкнеться автоматично. У застосунку з Google Play оплата йде через Google Play. Зауважте: оплата ще не працює – вона запрацює незабаром, а доти кнопки покупки позначено «незабаром». Тестувальники отримують Premium безкоштовно.",
   {"pl": "Jak zapłacić?", "en": "How do I pay?", "es": "¿Cómo pago?", "de": "Wie bezahle ich?", "uk": "Як оплатити?"}),
 F("blik_wygasl", "kod blik wygasł nie działa expired code error błąd timeout caducado abgelaufen прострочений",
   "Kod BLIK jest ważny tylko 2 minuty. Jeśli wygasł, po prostu wygeneruj nowy w aplikacji banku i spróbuj jeszcze raz – za nieudaną próbę nic nie pobieramy.",
   "A BLIK code is only valid for 2 minutes. If it expired, just generate a new one in your banking app and try again – nothing is charged for a failed attempt.",
   "El código BLIK solo es válido 2 minutos. Si ha caducado, genera uno nuevo en la app de tu banco y vuelve a intentarlo: un intento fallido no tiene ningún cargo.",
   "Ein BLIK-Code ist nur 2 Minuten gültig. Ist er abgelaufen, erzeuge einfach einen neuen in deiner Banking-App und versuch es noch einmal – für einen fehlgeschlagenen Versuch wird nichts abgebucht.",
   "Код BLIK дійсний лише 2 хвилини. Якщо він прострочився, просто згенеруйте новий у застосунку банку та спробуйте ще раз — за невдалу спробу нічого не списується."),
 F("w_toku", "w toku oczekuje pending czeka nie dostałem dostępu brak dostępu pendiente ausstehend очікує",
   "Jeśli płatność jest „w toku”, bank jeszcze ją potwierdza. Zwykle trwa to kilka sekund – odśwież aplikację za chwilę. Jeśli po kilku minutach dostęp się nie pojawi, kliknij „Porozmawiaj z człowiekiem”, a utworzę zgłoszenie.",
   "If a payment is “pending”, your bank is still confirming it. It usually takes a few seconds – refresh the app in a moment. If access doesn’t appear after a few minutes, click “Talk to a human” and I’ll create a ticket.",
   "Si un pago está «pendiente», tu banco aún lo está confirmando. Suele tardar unos segundos: actualiza la app en un momento. Si el acceso no aparece en unos minutos, pulsa «Hablar con una persona» y crearé una incidencia.",
   "Steht eine Zahlung auf „ausstehend“, bestätigt deine Bank sie noch. Das dauert meist nur Sekunden – aktualisiere die App gleich noch einmal. Erscheint der Zugang nach einigen Minuten nicht, klicke auf „Mit einem Menschen sprechen“, dann lege ich ein Ticket an.",
   "Якщо платіж «очікує», банк ще його підтверджує. Зазвичай це кілька секунд — оновіть застосунок трохи згодом. Якщо доступ не з’явиться за кілька хвилин, натисніть «Поговорити з людиною», і я створю звернення."),
 F("vat", "vat podatek brutto faktura paragon tax invoice receipt iva impuesto factura mwst steuer rechnung пдв податок",
   "Wszystkie ceny są cenami brutto, czyli zawierają VAT. Potwierdzenie płatności wysyła Stripe na Twój e-mail; w Google Play – Google Play.",
   "All prices are gross, meaning VAT is included. Stripe emails you the payment receipt; for Google Play purchases, Google Play does.",
   "Todos los precios son finales, con el IVA incluido. Stripe te envía el recibo por correo; en las compras de Google Play, lo hace Google Play.",
   "Alle Preise sind Bruttopreise, die Mehrwertsteuer ist also enthalten. Den Zahlungsbeleg schickt dir Stripe per E-Mail, bei Käufen über Google Play übernimmt das Google Play.",
   "Усі ціни вказано з ПДВ. Підтвердження оплати надсилає Stripe на ваш e-mail, а для покупок у Google Play — Google Play."),
 F("mikrofon", "mikrofon uprawnienia nie słyszy nie działa mikrofon microphone mic permission micrófono permiso mikrofon berechtigung мікрофон дозвіл",
   "Mikrofon: w Chrome stuknij kłódkę obok adresu → Uprawnienia → Mikrofon → Zezwól, a potem odśwież stronę. W aplikacji na Androida: Ustawienia telefonu → Aplikacje → Chrome → Uprawnienia → Mikrofon. Na iPhonie: Ustawienia → Safari → Mikrofon.",
   "Microphone: in Chrome, tap the padlock next to the address → Permissions → Microphone → Allow, then refresh the page. In the Android app: phone Settings → Apps → Chrome → Permissions → Microphone. On iPhone: Settings → Safari → Microphone.",
   "Micrófono: en Chrome, toca el candado junto a la dirección → Permisos → Micrófono → Permitir y actualiza la página. En la app de Android: Ajustes del teléfono → Aplicaciones → Chrome → Permisos → Micrófono. En iPhone: Ajustes → Safari → Micrófono.",
   "Mikrofon: Tippe in Chrome auf das Schloss neben der Adresse → Berechtigungen → Mikrofon → Zulassen und lade die Seite neu. In der Android-App: Handy-Einstellungen → Apps → Chrome → Berechtigungen → Mikrofon. Auf dem iPhone: Einstellungen → Safari → Mikrofon.",
   "Мікрофон: у Chrome торкніться замка біля адреси → Дозволи → Мікрофон → Дозволити, а потім оновіть сторінку. У застосунку Android: Налаштування телефону → Застосунки → Chrome → Дозволи → Мікрофон. На iPhone: Налаштування → Safari → Мікрофон.",
   {"pl": "Mikrofon nie działa", "en": "My mic isn’t working", "es": "El micrófono no funciona", "de": "Mikrofon geht nicht", "uk": "Не працює мікрофон"}),
 F("glos", "głos dźwięk cicho głośno trzaski nie słychać voice sound quiet loud audio voz sonido stimme ton звук голос",
   "Dźwięk: sprawdź głośność telefonu i to, czy w Ustawieniach jest włączone „Czytaj odpowiedzi na głos”. Barwę, tempo i głośność Luny zmienisz w Ustawieniach głosu. Po każdej odpowiedzi możesz też ocenić głos 👍/👎 – to bardzo nam pomaga.",
   "Sound: check your phone’s volume and make sure “Read answers aloud” is on in Settings. You can change Luna’s tone, pace and volume in the voice settings. After each answer you can also rate the voice 👍/👎 – it helps us a lot.",
   "Sonido: comprueba el volumen del teléfono y que «Leer respuestas en voz alta» esté activado en Ajustes. El timbre, el ritmo y el volumen de Luna se cambian en los ajustes de voz. Después de cada respuesta también puedes valorar la voz 👍/👎; nos ayuda muchísimo.",
   "Ton: Prüfe die Lautstärke deines Handys und ob in den Einstellungen „Antworten vorlesen“ aktiviert ist. Klang, Tempo und Lautstärke von Luna änderst du in den Stimmeinstellungen. Nach jeder Antwort kannst du die Stimme mit 👍/👎 bewerten – das hilft uns sehr.",
   "Звук: перевірте гучність телефона і чи ввімкнено в Налаштуваннях «Читати відповіді вголос». Тембр, темп і гучність Луни можна змінити в налаштуваннях голосу. Після кожної відповіді можна також оцінити голос 👍/👎 — це нам дуже допомагає."),
 F("konto", "konto logowanie hasło hasła zalogować rejestracja 18 pełnoletni account login password sign up cuenta contraseña konto anmelden passwort обліковий вхід пароль",
   "Konto zakładasz w Ustawieniach → Konto i plan (e-mail i hasło, a potem jedno pytanie: „Masz 18 lat?” – bez podawania daty urodzenia). Luna jest wyłącznie dla osób pełnoletnich. Nigdy nie wpisuj hasła w czacie – ja też o nie nie poproszę. Jeśli konto jest zablokowane po kilku nieudanych próbach, odczekaj 15 minut.",
   "You create an account in Settings → Account and plan (email and password, then one question: “Are you 18?” – no date of birth needed). Luna is for adults only. Never type your password into a chat – I will never ask for it. If your account is locked after several failed attempts, wait 15 minutes.",
   "La cuenta se crea en Ajustes → Cuenta y plan (correo y contraseña, y luego una pregunta: «¿Tienes 18 años?», sin fecha de nacimiento). Luna es solo para personas adultas. Nunca escribas tu contraseña en un chat: yo nunca te la pediré. Si la cuenta se bloquea tras varios intentos fallidos, espera 15 minutos.",
   "Ein Konto legst du unter Einstellungen → Konto und Plan an (E-Mail und Passwort, dann eine Frage: „Bist du 18?“ – ohne Geburtsdatum). Luna ist nur für Volljährige. Gib dein Passwort niemals in einen Chat ein – ich werde nie danach fragen. Ist dein Konto nach mehreren Fehlversuchen gesperrt, warte 15 Minuten.",
   "Обліковий запис створюється в Налаштуваннях → Обліковий запис і план (e-mail і пароль, а потім одне запитання: «Тобі є 18?» – без дати народження). Луна лише для повнолітніх. Ніколи не вводьте пароль у чаті — я ніколи його не попрошу. Якщо обліковий запис заблоковано після кількох невдалих спроб, зачекайте 15 хвилин."),
 F("testerzy", "tester testerzy testy beta kod testera premium za darmo tester probador prueba testen тестувальник",
   "Testerów szukamy na stronie /testerzy.html: maks. 50 osób, Premium za darmo na 2 miesiące i fioletowa lub niebieska obwódka. Kod testera wpisujesz w Ustawieniach → Twój profil.",
   "We’re recruiting testers at /testerzy.html: up to 50 people, Premium free for 2 months and a purple or blue ring. You enter your tester code in Settings → Your profile.",
   "Buscamos testers en /testerzy.html: hasta 50 personas, Premium gratis durante 2 meses y un aro morado o azul. El código de tester se introduce en Ajustes → Tu perfil.",
   "Tester suchen wir auf /testerzy.html: bis zu 50 Personen, Premium 2 Monate gratis und ein lila oder blauer Ring. Den Tester-Code gibst du unter Einstellungen → Dein Profil ein.",
   "Тестувальників шукаємо на сторінці /testerzy.html: до 50 осіб, Premium безкоштовно на 2 місяці та фіолетова чи синя обвідка. Код тестувальника вводиться в Налаштуваннях → Ваш профіль.",
   {"pl": "Jak zostać testerem?", "en": "How do I become a tester?", "es": "¿Cómo ser tester?", "de": "Wie werde ich Tester?", "uk": "Як стати тестувальником?"}),
 F("casting", "casting twarz gwiazda zgłoszenie zdjęcie zgoda finał termin face star photo casting rostro foto gesicht foto кастинг обличчя фото",
   "Casting „Twarz AI” trwa od 18.10 do 31.12.2026 (23:59 czasu polskiego), a finał odbędzie się na początku stycznia 2027 r. Na tym etapie nie wysyłasz zdjęć – materiały zbieramy dopiero po podpisaniu umowy i tylko za Twoją zgodą, którą możesz wycofać; wtedy usuwamy Twoje dane. Szczegóły: /twarz.html.",
   "The “AI Face” casting runs from 18 October to 31 December 2026 (23:59 Polish time), with the final in early January 2027. You don’t send photos at this stage – we collect materials only after an agreement is signed and only with your consent, which you can withdraw; we then delete your data. Details: /twarz.html.",
   "El casting «Rostro IA» va del 18 de octubre al 31 de diciembre de 2026 (23:59, hora de Polonia), y la final será a principios de enero de 2027. En esta fase no envías fotos: solo recogemos materiales tras firmar un contrato y con tu consentimiento, que puedes retirar; en ese caso borramos tus datos. Detalles: /twarz.html.",
   "Das Casting „KI-Gesicht“ läuft vom 18. Oktober bis zum 31. Dezember 2026 (23:59 Uhr polnischer Zeit); das Finale findet Anfang Januar 2027 statt. In dieser Phase schickst du keine Fotos – Material sammeln wir erst nach Vertragsunterzeichnung und nur mit deiner Einwilligung, die du widerrufen kannst; dann löschen wir deine Daten. Details: /twarz.html.",
   "Кастинг «Обличчя ШІ» триває з 18 жовтня до 31 грудня 2026 р. (23:59 за польським часом), а фінал відбудеться на початку січня 2027 р. На цьому етапі фото не надсилаються — матеріали збираємо лише після підписання договору і тільки за вашою згодою, яку можна відкликати; тоді ми видаляємо ваші дані. Подробиці: /twarz.html."),
 F("butik", "butik strój stroje kolekcja ubranie sukienka cena stroju boutique outfit collection dress tienda ropa vestido kleid kollektion бутик вбрання сукня колекція",
   "Butik Luny ma trzy linie: Ekonomiczną, Classic i Couture. Nowe stroje wydajemy partiami w kolejnych aktualizacjach, czasem w kolekcjach sezonowych. Ceny zobaczysz w zakładce Cennik, gdy zostaną opublikowane – nie podam ich z pamięci.",
   "Luna’s Boutique has three lines: Economy, Classic and Couture. We release new outfits in batches with each update, sometimes as seasonal collections. You’ll see the prices in the Prices tab once they’re published – I won’t quote them from memory.",
   "La boutique de Luna tiene tres líneas: Económica, Classic y Couture. Lanzamos ropa nueva por tandas en cada actualización, a veces en colecciones de temporada. Verás los precios en la pestaña Precios cuando se publiquen; no los daré de memoria.",
   "Lunas Boutique hat drei Linien: Economy, Classic und Couture. Neue Outfits erscheinen schrittweise mit jedem Update, manchmal als saisonale Kollektionen. Die Preise siehst du im Tab „Preise“, sobald sie veröffentlicht sind – aus dem Gedächtnis nenne ich keine.",
   "Бутик Луни має три лінії: Економ, Classic і Couture. Нове вбрання виходить партіями з кожним оновленням, іноді як сезонні колекції. Ціни ви побачите в розділі «Ціни», щойно їх опублікують — з пам’яті я їх не називатиму."),
 F("plany", "ile kosztuje koszt cena ceny cennik cost price prices precio cuánto kostet kosten preis ціна скільки plan plany darmowy podstawowa premium pro limit subskrypcja miesiąc plan free subscription month gratis suscripción abo monat план безкоштовний підписка",
   "Plany: Darmowy bez konta (ok. 5 minut rozmowy dziennie, test głosu, oglądanie Luna Live i 1 strój), Podstawowa – za darmo, wystarczy konto – oraz płatne Premium i Pro: jednorazowy dostęp na 30 dni, bez automatycznego odnawiania, cena zawiera VAT.",
   "Plans: Free without an account (about 5 minutes of conversation a day, a voice test, watching Luna Live and 1 outfit), Basic – free, you just need an account – and the paid Premium and Pro: one-off 30-day access, no automatic renewal, VAT included.",
   "Planes: Gratuito sin cuenta (unos 5 minutos de conversación al día, prueba de voz, ver Luna Live y 1 conjunto), Básico, gratis con solo crear una cuenta, y los de pago Premium y Pro: acceso único de 30 días, sin renovación automática, IVA incluido.",
   "Pläne: Gratis ohne Konto (etwa 5 Minuten Gespräch pro Tag, Stimmtest, Luna Live ansehen und 1 Outfit), Basis – kostenlos, ein Konto genügt – sowie die kostenpflichtigen Pläne Premium und Pro: einmaliger 30-Tage-Zugang ohne automatische Verlängerung, inkl. MwSt.",
   "Плани: Безкоштовний без облікового запису (близько 5 хвилин розмови на день, тест голосу, перегляд Luna Live та 1 образ), Базовий — безкоштовно, достатньо облікового запису, — а також платні Premium і Pro: разовий доступ на 30 днів без автоматичного продовження, ціна з ПДВ.",
   {"pl": "Jakie są plany?", "en": "What plans are there?", "es": "¿Qué planes hay?", "de": "Welche Pläne gibt es?", "uk": "Які є плани?"}),
 F("live", "live transmisja stream kiedy niedziela harmonogram luna live schedule sunday directo emisión domingo sendung sonntag трансляція неділя",
   "Luna Live odbywa się co tydzień – domyślnie w niedzielę od 20:00 do 23:00 czasu polskiego (dokładny termin i odliczanie są na stronie /live.html). W planie Darmowy możesz oglądać i pisać na czacie, a pytania do Luny zadasz od planu Podstawowa.",
   "Luna Live takes place every week – by default on Sundays from 20:00 to 23:00 Polish time (the exact schedule and countdown are at /live.html). On the Free plan you can watch and chat; asking Luna questions starts with the Basic plan.",
   "Luna Live se emite cada semana, por defecto los domingos de 20:00 a 23:00, hora de Polonia (el horario exacto y la cuenta atrás están en /live.html). Con el plan Gratuito puedes verlo y escribir en el chat; para hacer preguntas a Luna necesitas el plan Básico.",
   "Luna Live findet jede Woche statt – standardmäßig sonntags von 20:00 bis 23:00 Uhr polnischer Zeit (genauer Termin und Countdown auf /live.html). Im Gratis-Plan kannst du zuschauen und chatten; Fragen an Luna gibt es ab dem Basis-Plan.",
   "Luna Live відбувається щотижня — за замовчуванням у неділю з 20:00 до 23:00 за польським часом (точний розклад і зворотний відлік на /live.html). У безкоштовному плані можна дивитися і писати в чаті, а ставити запитання Луні — від плану Базовий."),
 F("android", "android apk instalacja zainstalować google play pobrać telefon install download instalar descargar installieren herunterladen встановити завантажити",
   "Android: pobierz plik APK z przycisku „Pobierz na Androida” na stronie głównej i zezwól na instalację z nieznanych źródeł. Link do testów w Google Play prześlemy później. Na iPhonie otwórz Lunę w Safari i dodaj ją do ekranu początkowego.",
   "Android: download the APK with the “Download for Android” button on the home page and allow installation from unknown sources. We’ll send the Google Play test link later. On iPhone, open Luna in Safari and add it to your home screen.",
   "Android: descarga el APK con el botón «Descargar para Android» de la página principal y permite la instalación desde fuentes desconocidas. El enlace de prueba de Google Play llegará más adelante. En iPhone, abre Luna en Safari y añádela a la pantalla de inicio.",
   "Android: Lade die APK über den Button „Für Android herunterladen“ auf der Startseite herunter und erlaube die Installation aus unbekannten Quellen. Den Testlink für Google Play schicken wir später. Auf dem iPhone öffnest du Luna in Safari und fügst sie zum Startbildschirm hinzu.",
   "Android: завантажте APK кнопкою «Завантажити для Android» на головній сторінці та дозвольте встановлення з невідомих джерел. Посилання на тестування в Google Play надішлемо пізніше. На iPhone відкрийте Луну в Safari й додайте її на головний екран."),
 F("reklamy", "reklamy reklama ads advertising anuncios publicidad werbung реклама",
   "Luna nie ogląda reklam, bo i tak by je przegadała 😄 Aplikacja nie zawiera żadnych reklam.",
   "Luna doesn’t watch ads – she’d talk right over them anyway 😄 The app contains no ads at all.",
   "Luna no ve anuncios; de todos modos, los dejaría sin palabras 😄 La app no contiene ningún anuncio.",
   "Luna schaut keine Werbung – sie würde sie ohnehin totquatschen 😄 Die App enthält keinerlei Werbung.",
   "Луна не дивиться рекламу — однаково її переговорила б 😄 Застосунок не містить жодної реклами."),
 F("fan", "fanowski projekt kto stoi kim jesteście fan project who proyecto fans fanprojekt фанатський проєкт",
   "Luna mówi jak jest to projekt fanowski – i taki zostanie, słowo Luny! 💚 Jeśli chcesz pomóc, zajrzyj na /dolacz.html.",
   "Luna Tells It Like It Is is a fan project – and it will stay that way, Luna’s word of honour! 💚 If you’d like to help, visit /dolacz.html.",
   "Luna dice las cosas como son es un proyecto de fans, y así seguirá, ¡palabra de Luna! 💚 Si quieres ayudar, visita /dolacz.html.",
   "Luna sagt, wie es ist, ist ein Fanprojekt – und bleibt es, Ehrenwort von Luna! 💚 Wenn du helfen möchtest, schau auf /dolacz.html vorbei.",
   "Луна каже як є — фанатський проєкт, і таким він залишиться, слово Луни! 💚 Якщо хочете допомогти, зазирніть на /dolacz.html."),
 F("usuniecie", "usunąć usuń usunięcie konto dane rodo eksport moje dane delete deletion account gdpr export borrar datos eliminar cuenta löschen konto daten dsgvo видалити видалення обліковий дані",
   "Swoje dane pobierzesz w „Mój panel”. Tam też usuniesz konto w 2 krokach (wpisujesz swój nick), a przez 30 dni możesz je przywrócić – potem usuwamy wszystko na zawsze. Pozostałe dane usuniemy na prośbę w ciągu 30 dni. Szczegóły: /privacy.html.",
   "Download your data in “My panel”. That’s also where you delete your account in 2 steps (you type your nick); you can restore it within 30 days – after that everything is deleted for good. We’ll delete any other data on request within 30 days. Details: /privacy.html.",
   "Descarga tus datos en «Mi panel». Allí también eliminas la cuenta en 2 pasos (escribes tu nick) y puedes restaurarla durante 30 días; después lo borramos todo para siempre. Cualquier otro dato lo borraremos a petición en un plazo de 30 días. Detalles: /privacy.html.",
   "Deine Daten lädst du unter „Mein Bereich“ herunter. Dort löschst du auch dein Konto in 2 Schritten (du gibst deinen Nick ein); 30 Tage lang kannst du es wiederherstellen – danach ist alles endgültig gelöscht. Alle anderen Daten löschen wir auf Anfrage innerhalb von 30 Tagen. Details: /privacy.html.",
   "Свої дані завантажите в «Моя панель». Там же видалите акаунт у 2 кроки (вводите свій нік), а протягом 30 днів його можна відновити – потім усе видаляється назавжди. Інші дані видалимо на прохання протягом 30 днів. Подробиці: /privacy.html."),
]
INTRO = {"pl": "Cześć! Jestem Pomocą Luny – botem AI. Odpowiem na najczęstsze pytania. Nigdy nie podawaj tu haseł, kodów BLIK ani numerów kart. 💚",
         "en": "Hi! I’m Luna’s Help – an AI bot. I can answer the most common questions. Never share passwords, BLIK codes or card numbers here. 💚",
         "es": "¡Hola! Soy la Ayuda de Luna, un bot de IA. Respondo a las preguntas más frecuentes. Nunca compartas aquí contraseñas, códigos BLIK ni números de tarjeta. 💚",
         "de": "Hallo! Ich bin Lunas Hilfe – ein KI-Bot. Ich beantworte die häufigsten Fragen. Teile hier niemals Passwörter, BLIK-Codes oder Kartennummern. 💚",
         "uk": "Привіт! Я Допомога Луни — ШІ-бот. Відповім на найчастіші запитання. Ніколи не повідомляйте тут паролі, коди BLIK чи номери карток. 💚"}
NOANS = {"pl": "Hmm, tego nie wiem na pewno, a nie chcę zgadywać. Mogę przekazać rozmowę człowiekowi – kliknij „Porozmawiaj z człowiekiem”.",
         "en": "Hmm, I don’t know that for sure, and I’d rather not guess. I can pass this chat to a human – click “Talk to a human”.",
         "es": "Mmm, eso no lo sé con seguridad y prefiero no adivinar. Puedo pasar la conversación a una persona: pulsa «Hablar con una persona».",
         "de": "Hm, das weiß ich nicht sicher, und raten möchte ich nicht. Ich kann das Gespräch an einen Menschen weitergeben – klicke auf „Mit einem Menschen sprechen“.",
         "uk": "Хм, цього я точно не знаю, а вгадувати не хочу. Можу передати розмову людині — натисніть «Поговорити з людиною»."}
SENSITIVE = {"pl": "⚠️ Wygląda na to, że wpisujesz poufne dane (np. kod BLIK, numer karty lub hasło). Nie podawaj ich nikomu – usunęłam je z rozmowy.",
             "en": "⚠️ It looks like you’re typing sensitive data (e.g. a BLIK code, card number or password). Never share it with anyone – I’ve removed it from the chat.",
             "es": "⚠️ Parece que estás escribiendo datos confidenciales (p. ej., un código BLIK, un número de tarjeta o una contraseña). No los compartas con nadie: los he eliminado de la conversación.",
             "de": "⚠️ Es sieht so aus, als würdest du vertrauliche Daten eingeben (z. B. einen BLIK-Code, eine Kartennummer oder ein Passwort). Gib sie niemandem weiter – ich habe sie aus dem Chat entfernt.",
             "uk": "⚠️ Схоже, ви вводите конфіденційні дані (наприклад, код BLIK, номер картки чи пароль). Нікому їх не повідомляйте — я видалила їх із розмови."}
HUMAN = {"pl": "Jasne! Kliknij „Porozmawiaj z człowiekiem”, a przekażę całą rozmowę moderatorowi jako zgłoszenie.",
         "en": "Of course! Click “Talk to a human” and I’ll pass the whole chat to a moderator as a ticket.",
         "es": "¡Claro! Pulsa «Hablar con una persona» y pasaré toda la conversación a un moderador como incidencia.",
         "de": "Klar! Klicke auf „Mit einem Menschen sprechen“, dann leite ich das ganze Gespräch als Ticket an einen Moderator weiter.",
         "uk": "Звісно! Натисніть «Поговорити з людиною», і я передам усю розмову модератору як звернення."}
HUMAN_RE = re.compile(r"\b(człowiek|czlowiek|konsultant|moderator|human|person|agent|persona|humano|mensch|людин|оператор)", re.I)
SENS_RE = re.compile(r"(\b\d{6}\b|\b(?:\d[ -]?){13,19}\b|hasło\s*[:=]|password\s*[:=]|contraseña\s*[:=]|passwort\s*[:=]|пароль\s*[:=])", re.I)

PRICES = None  # ustawiane przez serwer: () -> {"premium": "59,99", "pro": "99,99"} albo None, gdy ceny są ukryte
PRICE_LINE = {"pl": " Ceny: Premium {premium} zł, Pro {pro} zł (za 30 dni).", "en": " Prices: Premium PLN {premium}, Pro PLN {pro} (per 30 days).",
              "es": " Precios: Premium {premium} PLN, Pro {pro} PLN (por 30 días).", "de": " Preise: Premium {premium} zł, Pro {pro} zł (für 30 Tage).",
              "uk": " Ціни: Premium {premium} зл., Pro {pro} зл. (за 30 днів)."}
HIDDEN_LINE = {"pl": " Ceny pojawią się w Cenniku po publikacji.", "en": " Prices will appear in the Prices tab once published.", "es": " Los precios aparecerán en la pestaña Precios cuando se publiquen.",
               "de": " Die Preise erscheinen nach der Veröffentlichung im Tab „Preise“.", "uk": " Ціни з’являться в розділі «Ціни» після публікації."}

# Wersja poprawionych odpowiedzi domyślnych. Zapisane w panelu FAQ (help_faq) starsze niż KB_REV nie mogą przywrócić
# nieaktualnych treści: dla kluczy z CORRECTED wygrywa wersja z kodu. Każda odpowiedź z nieaktualną frazą (STALE_RE) też.
KB_REV = 2
CORRECTED = {"konto", "platnosci", "usuniecie"}
STALE_RE = re.compile(r"2160\s*px|dat[aęy] urodzenia|date of birth|fecha de nacimiento|geburtsdatum|дат[аиу] народження|jednym klikni|one click|un solo clic|einem klick|одним клац", re.I)
_DEF = {e["id"]: e for e in DEFAULT}

def _fresh(e):
    d = _DEF.get(e.get("id")) if isinstance(e, dict) else None
    if not d: return e
    hit = lambda x: any(STALE_RE.search(str(a or "")) for a in (x.get("answers") or {}).values())
    stale = hit(e) and not hit(d)
    if stale or (e["id"] in CORRECTED and int(e.get("rev") or 0) < KB_REV): return d
    return e

def kb():
    v = store.get("help_faq", None)
    if not (isinstance(v, list) and v): return DEFAULT
    return [_fresh(e) for e in v if isinstance(e, dict)]

def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower().replace("ł", "l"))
    return "".join(c for c in s if not unicodedata.combining(c))

def match(q):
    words = set(re.findall(r"\w{3,}", norm(q)))
    best, score = None, 0
    for e in kb():
        kws = set(re.findall(r"\w{3,}", norm(e.get("keywords", ""))))
        s = 0
        for w in words:
            for k in kws:
                if w == k: s += 3
                elif len(w) >= 4 and len(k) >= 4 and (w.startswith(k[:5]) or k.startswith(w[:5])): s += 1.5
        if s > score: best, score = e, s
    return best if score >= 3 else None

def llm(q, lang):
    key, base, model = os.getenv("LUNA_API_KEY"), os.getenv("LUNA_BASE_URL"), os.getenv("LUNA_MODEL")
    if not (key and base and model): return None
    faq = "\n".join(f"- [{e['id']}] {e['answers'].get(lang) or e['answers']['pl']}" for e in kb())
    sysmsg = (f"You are 'Pomoc Luny', an AI help bot for the app 'Luna mówi jak jest'. Answer ONLY using the FAQ below, in the language '{lang}', "
              "briefly, kindly and with correct grammar. Never invent prices, policies, dates or promises. Never ask for passwords, BLIK codes or card numbers. "
              "If the FAQ does not cover the question, reply exactly NOANSWER.\nFAQ:\n" + faq)
    body = {"model": model, "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": q[:500]}], "temperature": 0.2, "max_tokens": 220}
    try:
        req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r: a = json.load(r)["choices"][0]["message"]["content"].strip()
        return None if "NOANSWER" in a else a
    except Exception:
        return None

def log_unanswered(q, lang):
    with _lock:
        u = store.get("help_unanswered", []) or []
        u.append({"t": int(time.time()), "q": SENS_RE.sub("***", q)[:300], "lang": lang}); store.put("help_unanswered", u[-500:])

def answer(q, lang):
    lang = lang if lang in LANGS else "pl"; q = str(q or "").strip()[:500]
    if SENS_RE.search(q): return {"reply": SENSITIVE[lang], "sensitive": True, "handoff": False}
    if HUMAN_RE.search(q): return {"reply": HUMAN[lang], "handoff": True}
    e = match(q)
    if e:
        rep = e["answers"].get(lang) or e["answers"]["pl"]
        if e["id"] == "plany":
            pr = PRICES() if PRICES else None
            rep += PRICE_LINE[lang].format(**pr) if pr else HIDDEN_LINE[lang]
        return {"reply": rep, "id": e["id"], "source": "faq"}
    a = llm(q, lang)
    if a: return {"reply": a, "source": "llm"}
    log_unanswered(q, lang)
    return {"reply": NOANS[lang], "handoff": True}

def chips(lang):
    return [{"id": e["id"], "label": e["chip"].get(lang) or e["chip"].get("pl")} for e in kb() if e.get("chip")]

def save_kb(items):
    out = []
    for e in (items or [])[:80]:
        if not isinstance(e, dict) or not re.fullmatch(r"[\w\-]{2,30}", str(e.get("id", ""))): continue
        ans = {l: re.sub(r"[<>]", "", str((e.get("answers") or {}).get(l, "")))[:1200] for l in LANGS}
        if not ans["pl"]: continue
        out.append({"id": e["id"], "rev": KB_REV, "keywords": str(e.get("keywords", ""))[:600], "answers": ans,
                    "chip": {l: re.sub(r"[<>]", "", str((e.get("chip") or {}).get(l, "")))[:40] for l in LANGS} if e.get("chip") else {}})
    store.put("help_faq", out); return out
