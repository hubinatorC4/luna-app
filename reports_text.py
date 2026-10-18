"""Teksty modułu zgłoszeń (5 języków: pl, en, es, de, uk) – kategorie, decyzje i uzasadnienia (art. 17 DSA)."""
L5 = ("pl", "en", "es", "de", "uk")
def _d(*v): return dict(zip(L5, v))

CATS = {
 "harass": _d("Nękanie/obrażanie", "Harassment/insults", "Acoso/insultos", "Belästigung/Beleidigung", "Цькування/образи"),
 "spam": _d("Spam/oszustwo", "Spam/fraud", "Spam/estafa", "Spam/Betrug", "Спам/шахрайство"),
 "fake": _d("Fałszywe konto/podszywanie", "Fake account/impersonation", "Cuenta falsa/suplantación", "Fake-Konto/Identitätsdiebstahl", "Фейковий акаунт/видавання себе за іншого"),
 "nudity": _d("Nieodpowiednie zdjęcie/nagość", "Inappropriate photo/nudity", "Foto inapropiada/desnudez", "Unangemessenes Foto/Nacktheit", "Неприйнятне фото/оголеність"),
 "minor": _d("Osoba niepełnoletnia", "Minor (under 18)", "Persona menor de edad", "Minderjährige Person", "Неповнолітня особа"),
 "doxx": _d("Ujawnianie danych", "Sharing private data", "Divulgación de datos", "Weitergabe privater Daten", "Розголошення даних"),
 "other": _d("Inne", "Other", "Otro", "Sonstiges", "Інше"),
}
WHAT = {
 "post": _d("wpis", "post", "publicación", "Beitrag", "допис"), "cmt": _d("komentarz", "comment", "comentario", "Kommentar", "коментар"),
 "agent": _d("profil agentki", "agent profile", "perfil de agente", "Agentinnen-Profil", "профіль агентки"),
 "item": _d("produkt", "product", "producto", "Produkt", "товар"), "btchat": _d("wiadomość na czacie bitwy", "battle chat message", "mensaje del chat de batalla", "Battle-Chat-Nachricht", "повідомлення в чаті битви"),
 "dm": _d("wiadomość prywatna", "private message", "mensaje privado", "private Nachricht", "приватне повідомлення"),
 "user": _d("profil użytkownika", "user profile", "perfil de usuario", "Nutzerprofil", "профіль користувача"),
 "photo": _d("zdjęcie", "photo", "foto", "Foto", "фото"),
}
DEC = {
 "dismiss": _d("bez naruszenia – treść zostaje", "no violation – content stays", "sin infracción – el contenido se queda", "kein Verstoß – Inhalt bleibt", "порушення немає – вміст залишається"),
 "remove": _d("usunięcie treści", "content removed", "contenido eliminado", "Inhalt entfernt", "вміст видалено"),
 "warn": _d("ostrzeżenie", "warning", "advertencia", "Verwarnung", "попередження"),
 "temp_block": _d("czasowa blokada konta", "temporary account block", "bloqueo temporal de la cuenta", "vorübergehende Kontosperre", "тимчасове блокування акаунта"),
 "ban": _d("trwała blokada konta", "permanent account ban", "bloqueo permanente de la cuenta", "dauerhafte Kontosperre", "постійне блокування акаунта"),
}
# --- wiadomość do osoby, której dotyczy decyzja (uzasadnienie wg art. 17 DSA) ---
T_DEC = _d("🛡️ Decyzja moderatora: {dec}", "🛡️ Moderator decision: {dec}", "🛡️ Decisión de moderación: {dec}", "🛡️ Entscheidung der Moderation: {dec}", "🛡️ Рішення модератора: {dec}")
B_DEC = _d(
 "Dotyczy: {what}{snip}.\nPowód: {cat} – naruszenie Regulaminu (§ 9e).\nDecyzja: {dec}{until}.\n{strike}{auto}{note}Zgłaszający pozostaje anonimowy – nie podajemy, kto zgłosił.\nOdwołanie: w ciągu 6 miesięcy przez formularz pomocy (link poniżej, wpisz „Odwołanie {case}”). Odwołanie rozpatruje człowiek. Możesz też skorzystać z pozasądowego rozstrzygania sporów lub drogi sądowej.",
 "Concerns: {what}{snip}.\nReason: {cat} – breach of the Terms (§ 9e).\nDecision: {dec}{until}.\n{strike}{auto}{note}The reporter stays anonymous – we never say who reported.\nAppeal: within 6 months via the help form (link below, type “Appeal {case}”). A human reviews every appeal. You may also use out-of-court dispute settlement or the courts.",
 "Afecta a: {what}{snip}.\nMotivo: {cat} – incumplimiento del Reglamento (§ 9e).\nDecisión: {dec}{until}.\n{strike}{auto}{note}Quien denunció sigue siendo anónimo: nunca decimos quién fue.\nRecurso: en un plazo de 6 meses mediante el formulario de ayuda (enlace abajo, escribe «Recurso {case}»). Lo revisa una persona. También puedes acudir a la resolución extrajudicial de litigios o a los tribunales.",
 "Betrifft: {what}{snip}.\nGrund: {cat} – Verstoß gegen die Nutzungsbedingungen (§ 9e).\nEntscheidung: {dec}{until}.\n{strike}{auto}{note}Die meldende Person bleibt anonym – wir sagen nie, wer gemeldet hat.\nEinspruch: innerhalb von 6 Monaten über das Hilfeformular (Link unten, schreib „Einspruch {case}“). Ein Mensch prüft jeden Einspruch. Du kannst auch die außergerichtliche Streitbeilegung oder die Gerichte nutzen.",
 "Стосується: {what}{snip}.\nПричина: {cat} – порушення Правил (§ 9e).\nРішення: {dec}{until}.\n{strike}{auto}{note}Особа, що поскаржилася, лишається анонімною – ми не кажемо, хто це був.\nОскарження: протягом 6 місяців через форму допомоги (посилання нижче, напишіть «Оскарження {case}»). Оскарження розглядає людина. Також можна звернутися до позасудового врегулювання спорів або до суду.")
STRIKE = _d("Poważne naruszenie {n} z 3. ", "Serious violation {n} of 3. ", "Infracción grave {n} de 3. ", "Schwerer Verstoß {n} von 3. ", "Серйозне порушення {n} з 3. ")
STRIKE3 = _d("To trzecie poważne naruszenie – konto zostaje trwale zablokowane. Twoimi danymi zajmujemy się zgodnie z Polityką prywatności (możesz pobrać ich kopię lub usunąć konto w ustawieniach). ",
 "This is the third serious violation – the account is permanently banned. Your data is handled under the Privacy Policy (you can download a copy or delete the account in settings). ",
 "Es la tercera infracción grave: la cuenta queda bloqueada de forma permanente. Tratamos tus datos según la Política de privacidad (puedes descargar una copia o eliminar la cuenta en ajustes). ",
 "Das ist der dritte schwere Verstoß – das Konto wird dauerhaft gesperrt. Deine Daten behandeln wir gemäß Datenschutzerklärung (in den Einstellungen kannst du eine Kopie laden oder das Konto löschen). ",
 "Це третє серйозне порушення – акаунт заблоковано назавжди. Вашими даними опікуємося згідно з Політикою конфіденційності (копію можна завантажити або видалити акаунт у налаштуваннях). ")
EGREG = _d("Szczególnie poważne naruszenie – blokada natychmiastowa, bez wcześniejszych stopni. ", "Particularly serious violation – immediate ban, without earlier steps. ",
 "Infracción especialmente grave: bloqueo inmediato, sin pasos previos. ", "Besonders schwerer Verstoß – sofortige Sperre ohne vorherige Stufen. ", "Особливо серйозне порушення – негайне блокування без попередніх кроків. ")
UNTIL = _d(" do {d}", " until {d}", " hasta el {d}", " bis {d}", " до {d}")
AUTO = _d("Treść została wcześniej automatycznie ukryta (po zgłoszeniach), a decyzję podjął człowiek. ", "The content was first hidden automatically (after reports); a human made this decision. ",
 "El contenido se ocultó primero automáticamente (tras denuncias); esta decisión la tomó una persona. ", "Der Inhalt wurde zunächst automatisch ausgeblendet (nach Meldungen); diese Entscheidung traf ein Mensch. ",
 "Вміст спершу приховано автоматично (після скарг), а рішення ухвалила людина. ")
NOTE = _d("Wyjaśnienie moderatora: {x}\n", "Moderator’s note: {x}\n", "Nota de moderación: {x}\n", "Hinweis der Moderation: {x}\n", "Пояснення модератора: {x}\n")
# --- wiadomość do zgłaszającego ---
T_REP = _d("🚩 Twoje zgłoszenie zostało rozpatrzone", "🚩 Your report has been reviewed", "🚩 Hemos revisado tu denuncia", "🚩 Deine Meldung wurde geprüft", "🚩 Вашу скаргу розглянуто")
B_REP = _d("Dziękujemy – moderator zdjął już okulary 🕵️. Zgłoszenie dotyczyło: {what} (powód: {cat}).\nWynik: {res}.\nDruga strona nie dowie się, kto zgłosił. Szczegółów sankcji nie podajemy. Jeśli się nie zgadzasz, możesz się odwołać w ciągu 6 miesięcy przez formularz pomocy (wpisz „Odwołanie {case}”).",
 "Thank you – the moderator has taken their glasses off 🕵️. Your report concerned: {what} (reason: {cat}).\nOutcome: {res}.\nThe other person will never learn who reported. We don’t share sanction details. If you disagree, you can appeal within 6 months via the help form (type “Appeal {case}”).",
 "Gracias: el moderador ya se ha quitado las gafas 🕵️. Tu denuncia era sobre: {what} (motivo: {cat}).\nResultado: {res}.\nLa otra persona nunca sabrá quién denunció. No compartimos detalles de las sanciones. Si no estás de acuerdo, puedes recurrir en 6 meses desde el formulario de ayuda (escribe «Recurso {case}»).",
 "Danke – die Moderation hat die Brille wieder abgesetzt 🕵️. Deine Meldung betraf: {what} (Grund: {cat}).\nErgebnis: {res}.\nDie andere Person erfährt nie, wer gemeldet hat. Details zu Sanktionen nennen wir nicht. Wenn du nicht einverstanden bist, kannst du innerhalb von 6 Monaten über das Hilfeformular Einspruch einlegen (schreib „Einspruch {case}“).",
 "Дякуємо – модератор уже зняв окуляри 🕵️. Скарга стосувалася: {what} (причина: {cat}).\nРезультат: {res}.\nІнша сторона не дізнається, хто поскаржився. Подробиць санкцій ми не повідомляємо. Якщо не згодні, оскаржте протягом 6 місяців через форму допомоги (напишіть «Оскарження {case}»).")
RES = {
 "dismiss": _d("nie stwierdziliśmy naruszenia Regulaminu – treść zostaje", "we found no breach of the Terms – the content stays", "no encontramos incumplimiento del Reglamento: el contenido se queda", "wir haben keinen Verstoß festgestellt – der Inhalt bleibt", "порушення Правил не виявлено – вміст залишається"),
 "action": _d("stwierdziliśmy naruszenie i podjęliśmy działania", "we found a violation and took action", "encontramos una infracción y actuamos", "wir haben einen Verstoß festgestellt und gehandelt", "ми виявили порушення і вжили заходів"),
}
# --- automatyczne ukrycie: informacja dla autora ---
T_HID = _d("⏸️ Twoja treść czeka na sprawdzenie", "⏸️ Your content is waiting for review", "⏸️ Tu contenido espera revisión", "⏸️ Dein Inhalt wartet auf Prüfung", "⏸️ Ваш вміст чекає на перевірку")
B_HID = _d("Ukryliśmy tymczasowo: {what}{snip} – po zgłoszeniach (środek automatyczny). Człowiek sprawdzi to wkrótce; jeśli wszystko w porządku, treść wróci. To jeszcze nie jest kara.",
 "We temporarily hid: {what}{snip} – after reports (automated measure). A human will check it soon; if all is fine, it comes back. This is not a penalty (yet).",
 "Hemos ocultado temporalmente: {what}{snip}, tras denuncias (medida automática). Una persona lo revisará pronto; si todo está bien, volverá. Esto todavía no es una sanción.",
 "Vorübergehend ausgeblendet: {what}{snip} – nach Meldungen (automatische Maßnahme). Ein Mensch prüft das bald; ist alles in Ordnung, kommt es zurück. Das ist (noch) keine Strafe.",
 "Тимчасово приховано: {what}{snip} – після скарг (автоматичний захід). Людина незабаром перевірить; якщо все гаразд, вміст повернеться. Це ще не покарання.")
# --- blokada zapisu ---
BLOCKED = _d("Twoje konto jest czasowo zablokowane do {d}. Szczegóły i odwołanie: Skrzynka → Ważne.", "Your account is temporarily blocked until {d}. Details and appeal: Inbox → Important.",
 "Tu cuenta está bloqueada temporalmente hasta el {d}. Detalles y recurso: Buzón → Importante.", "Dein Konto ist vorübergehend gesperrt bis {d}. Details und Einspruch: Postfach → Wichtig.",
 "Ваш акаунт тимчасово заблоковано до {d}. Подробиці й оскарження: Скринька → Важливе.")
BANNED = _d("To konto zostało trwale zablokowane. Możesz przeczytać uzasadnienie w Skrzynce, odwołać się, pobrać kopię danych lub usunąć konto.", "This account has been permanently banned. You can read the reasons in your Inbox, appeal, download your data or delete the account.",
 "Esta cuenta se ha bloqueado de forma permanente. Puedes leer el motivo en el Buzón, recurrir, descargar tus datos o eliminar la cuenta.", "Dieses Konto wurde dauerhaft gesperrt. Du kannst die Begründung im Postfach lesen, Einspruch einlegen, deine Daten herunterladen oder das Konto löschen.",
 "Цей акаунт заблоковано назавжди. Обґрунтування – у Скриньці; можна оскаржити, завантажити дані або видалити акаунт.")
