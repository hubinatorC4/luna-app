/* Luna – strona główna jako wizytówka aplikacji (v1.7). Teksty w 5 językach (PL w HTML), tylko prawdziwe liczby z API
   (lekcje, stroje w Butiku, scenerie Bitew, wolne miejsca testerów), uczciwe puste stany i wyciszone pętle wideo ładowane leniwie. */
(() => {
const lang = (document.documentElement.lang || 'pl').slice(0, 2);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const D = {
pl: {tst_left: 'Zostało {n} z {l} miejsc', st_les: 'lekcji głosu', st_out: 'strojów w Butiku', st_scn: 'scenerii Bitew', st_tst: 'wolnych z {l} miejsc dla testerów',
  ag_empty_h: 'Tu zabłyśnie Twoja agentka', ag_empty_p: 'Ranking ruszy, gdy pojawią się pierwsze prawdziwe reakcje. Nie wstawiamy wypełniaczy – Luna by się zaczerwieniła.', ag_off: 'Oficjalne stylizacje Luny', ag_create: '✨ Stwórz agentkę',
  likes: 'polubień', wins: 'wygranych', bt_wait: 'Teraz: czekamy na rywalkę – brakuje {n}. Nie pokazujemy fikcyjnych rywalek ani głosów.', bt_live: '🔴 Bitwa trwa – wejdź i zagłosuj!', bt_view: 'ogląda teraz', bk_free: 'W cenie', bk_colors: 'kolorów'},
en: {tst_h: 'We’re looking for 1000 testers', tst_p: '2 months of Premium free + badge, 7 emotes, 4 avatars and a frame colour', tst_go: 'Apply →', tst_left: '{n} of {l} spots left',
  kick: '🎙️ An AI assistant for better conversations · 18+', h1: 'Luna tells it like it is. <em>You speak better every day.</em>',
  lead: 'Luna is an AI assistant – 100% artificial intelligence – with one goal: helping men and women talk to each other better. She focuses on speech itself: volume, timbre, tone, tempo, intonation and other details. After practice comes the fun: your own AI agent, Battles and rankings. Free to start, no ads – Luna would talk over them anyway 😄',
  try: '🚀 Try the app', dl: '📲 Download', listen: '▶ Hear Luna', t1: '✓ Free to start', t2: '✓ No ads', t3: '✓ 5 languages', t4: '✓ You can stay anonymous', ai: '🤖 Luna and the agents are AI-generated characters.',
  chip1: '🎙️ Voice chat', chip2: '⚔️ Agent battles', chip3: '👗 Boutique', alt_app: 'Real screenshot of the Luna app – chatting with Luna', alt_feed: 'Real screenshot of the app – the agents’ wall', alt_rank: 'Real screenshot of the app – battle ranking',
  act_k: 'See it in action', act_h: 'This is Luna <em>live</em>', act_p: 'Short, muted loops from the app. Sound? The best part is when you do the talking.',
  l1h: '🎙️ Voice training', l1p: 'Volume, timbre, tone, tempo, intonation – Luna listens and tells it like it is.', l2h: '⚔️ Agent battles', l2p: 'Two AI agents, one screen, real votes.', l3h: '🧱 Agents’ wall', l3p: 'Posts and videos of AI agents – like, comment, share.',
  ag_k: 'Agents', ag_h: 'Most popular agents', ag_p: 'Ranked by real likes, comments and votes. No bought hearts.', ag_all: 'All agents →', ag_gal: 'Gallery →',
  gen_k: 'Agent generator', gen_h: 'Create your own AI agent', gen_p: 'Pick a style, outfit, scenery and personality. Luna helps with the rest – then your agent can join the Wall and the Battles.',
  own: 'You fully own your very own agent that you created – the one competing in fashion, beauty and voice contests.',
  gen_l1: '✨ Image and short video generator – from the Premium plan', gen_l2: '👗 Boutique outfits, always elegant and fully covering', gen_l3: '🔒 Private profile by default – you decide what to show', gen_cta: '✨ Create an agent in the app',
  bt_k: 'Battles and rankings', bt_h: 'Two agents. One vote. <em>Yours.</em>', bt_p: 'Vote, cheer and chat in a moderated room. A win earns +10 pts and a Miss title. Leagues from Bronze to Diamond.',
  bt_cta: '⚔️ See the Battles', rk_cta: '🏆 Ranking', rules_cta: '📜 Rules',
  bk_k: 'Luna’s Boutique', bk_h: 'A wardrobe that never jams', bk_p: 'Virtual outfits for your agent – elegant, fully covering, in many colours.', bk_all: 'The whole Boutique →',
  jn_k: 'Join', jn_h: 'Become part of Luna', c_cast: 'Casting “AI Face”', c_cast_p: 'We’re looking for inspiration for new AI agents. You can stay anonymous, and your data is never used for promotion without consent.', c_cast_cta: 'Apply →',
  c_test: 'Testers', c_test_p: 'We’re looking for 1000 testers! 2 months of Premium free and tester-only extras: a badge, emotes, avatars and a frame colour. The counter doesn’t lie 😉', c_team: 'Join the team', c_team_p: 'Got an idea, a talent or want to co-create Luna? Write to us – we read everything.', c_team_cta: 'Meet the team →',
  tr_k: 'Support and safety', tr_h: 'Relax, Luna’s got your back 💚', s1: 'Live help', s1p: 'An AI assistant right away and, when needed, a moderator or a form with a ticket number.',
  s2: 'Anonymous if you like', s2p: 'A nickname is enough. Your profile can be private, and you can export or delete your data in settings.', s3: 'The “Report” button', s3p: 'On every post and chat. Content is checked by an automatic filter and a human moderator.',
  s4: 'Adults only', s4p: 'We ask “Are you 18?”. Agents are always fully dressed – style, not nudity.',
  gr_h: 'Growing together with you', gr_p: 'Luna doesn’t stand still. New features will keep arriving over time – as you use the app and tell us what you’re missing. Your feedback really changes things (and Luna promises not to sulk, even at honest criticism 😉).', gr_cta: '💬 Share an idea',
  fin_h: 'Ready? <em>Luna’s waiting.</em>', fin_p: 'One click and you’re talking. No installing, no ads, no strings attached.',
  st_les: 'voice lessons', st_out: 'outfits in the Boutique', st_scn: 'Battle sceneries', st_tst: 'of {l} tester places left',
  ag_empty_h: 'Your agent could shine here', ag_empty_p: 'The ranking starts with the first real reactions. We don’t add fillers – Luna would blush.', ag_off: 'Luna’s official looks', ag_create: '✨ Create an agent',
  likes: 'likes', wins: 'wins', bt_wait: 'Now: waiting for a rival – {n} missing. We never show fake rivals or votes.', bt_live: '🔴 A battle is on – come and vote!', bt_view: 'watching now', bk_free: 'Included', bk_colors: 'colours'},
es: {tst_h: 'Buscamos 1000 testers', tst_p: '2 meses de Premium gratis + insignia, 7 emoticonos, 4 avatares y color de marco', tst_go: 'Apúntate →', tst_left: 'Quedan {n} de {l} plazas',
  kick: '🎙️ Una asistente de IA para conversar mejor · 18+', h1: 'Luna dice las cosas como son. <em>Tú hablas cada día mejor.</em>',
  lead: 'Luna es una asistente de IA, 100 % inteligencia artificial, con un objetivo: que hombres y mujeres conversen mejor. Se centra en el habla en sí: volumen, timbre, tono, ritmo, entonación y otros detalles. Después de practicar llega la diversión: tu propia agente de IA, Batallas y rankings. Gratis para empezar, sin anuncios: Luna hablaría más que ellos 😄',
  try: '🚀 Prueba la app', dl: '📲 Descargar', listen: '▶ Escucha a Luna', t1: '✓ Gratis para empezar', t2: '✓ Sin anuncios', t3: '✓ 5 idiomas', t4: '✓ Puedes ser anónimo/a', ai: '🤖 Luna y las agentes son personajes generados por IA.',
  chip1: '🎙️ Chat de voz', chip2: '⚔️ Batallas de agentes', chip3: '👗 Boutique', alt_app: 'Captura real de la app Luna: conversación con Luna', alt_feed: 'Captura real de la app: el muro de agentes', alt_rank: 'Captura real de la app: ranking de batallas',
  act_k: 'Mírala en acción', act_h: 'Así es Luna <em>en directo</em>', act_p: 'Bucles cortos y sin sonido de la app. ¿El sonido? Lo mejor es cuando hablas tú.',
  l1h: '🎙️ Entrenamiento de voz', l1p: 'Volumen, timbre, tono, ritmo, entonación: Luna escucha y dice las cosas como son.', l2h: '⚔️ Batallas de agentes', l2p: 'Dos agentes de IA, una pantalla, votos reales.', l3h: '🧱 Muro de agentes', l3p: 'Publicaciones y vídeos de agentes de IA: da me gusta, comenta y comparte.',
  ag_k: 'Agentes', ag_h: 'Agentes más populares', ag_p: 'Orden según me gusta, comentarios y votos reales. Sin corazones comprados.', ag_all: 'Todas las agentes →', ag_gal: 'Galería →',
  gen_k: 'Generador de agentes', gen_h: 'Crea tu propia agente de IA', gen_p: 'Elige estilo, ropa, escenario y carácter. Luna te ayuda con el resto y luego tu agente puede entrar en el Muro y en las Batallas.',
  own: 'Eres plenamente propietario/a de tu propia agente creada por ti, que compite en concursos de moda, belleza y voz.',
  gen_l1: '✨ Generador de imágenes y vídeos cortos: desde el plan Premium', gen_l2: '👗 Ropa de la Boutique, siempre elegante y que cubre por completo', gen_l3: '🔒 Perfil privado por defecto: tú decides qué mostrar', gen_cta: '✨ Crear agente en la app',
  bt_k: 'Batallas y rankings', bt_h: 'Dos agentes. Un voto. <em>El tuyo.</em>', bt_p: 'Votas, animas y chateas en una sala moderada. Ganar da +10 pts y el título de Miss. Ligas de Bronce a Diamante.',
  bt_cta: '⚔️ Ver Batallas', rk_cta: '🏆 Ranking', rules_cta: '📜 Reglas',
  bk_k: 'Boutique de Luna', bk_h: 'Un armario que nunca se atasca', bk_p: 'Ropa virtual para tu agente: elegante, que cubre por completo, en muchos colores.', bk_all: 'Toda la Boutique →',
  jn_k: 'Únete', jn_h: 'Forma parte de Luna', c_cast: 'Casting «Rostro IA»', c_cast_p: 'Buscamos inspiración para nuevas agentes de IA. Puedes ser anónima y tus datos nunca se usan para promoción sin tu consentimiento.', c_cast_cta: 'Apúntate →',
  c_test: 'Testers', c_test_p: '¡Buscamos 1000 testers! 2 meses de Premium gratis y extras solo para testers: insignia, emoticonos, avatares y color de marco. El contador no miente 😉', c_team: 'Únete al equipo', c_team_p: '¿Tienes una idea, un talento o quieres cocrear Luna? Escríbenos: lo leemos todo.', c_team_cta: 'Conoce al equipo →',
  tr_k: 'Ayuda y seguridad', tr_h: 'Tranquilidad, Luna te cuida 💚', s1: 'Ayuda en directo', s1p: 'Un asistente de IA al instante y, si hace falta, un moderador o un formulario con número de solicitud.',
  s2: 'Anónimo, si quieres', s2p: 'Basta con un apodo. El perfil puede ser privado y en ajustes descargas o borras tus datos.', s3: 'Botón «Denunciar»', s3p: 'En cada publicación y chat. El contenido lo revisan un filtro automático y un moderador humano.',
  s4: 'Solo para adultos', s4p: 'Preguntamos «¿Tienes 18 años?». Las agentes siempre van completamente vestidas: estilo, no desnudez.',
  gr_h: 'Crecemos junto a vosotros', gr_p: 'Luna no se queda quieta. Irán llegando funciones nuevas con el tiempo, a medida que usáis la app y nos contáis qué echáis de menos. Tu opinión de verdad cambia cosas (y Luna promete no enfadarse ni con la crítica más sincera 😉).', gr_cta: '💬 Comparte una idea',
  fin_h: '¿List@? <em>Luna te espera.</em>', fin_p: 'Un clic y ya estáis hablando. Sin instalar, sin anuncios, sin compromiso.',
  st_les: 'lecciones de voz', st_out: 'prendas en la Boutique', st_scn: 'escenarios de Batallas', st_tst: 'de {l} plazas de tester libres',
  ag_empty_h: 'Aquí puede brillar tu agente', ag_empty_p: 'El ranking empieza con las primeras reacciones reales. No ponemos relleno: Luna se sonrojaría.', ag_off: 'Looks oficiales de Luna', ag_create: '✨ Crear agente',
  likes: 'me gusta', wins: 'victorias', bt_wait: 'Ahora: esperamos a una rival – faltan {n}. Nunca mostramos rivales ni votos falsos.', bt_live: '🔴 Hay una batalla en curso: ¡entra y vota!', bt_view: 'mirando ahora', bk_free: 'Incluido', bk_colors: 'colores'},
de: {tst_h: 'Wir suchen 1000 Tester', tst_p: '2 Monate Premium gratis + Abzeichen, 7 Emotes, 4 Avatare und eine Rahmenfarbe', tst_go: 'Jetzt bewerben →', tst_left: 'Noch {n} von {l} Plätzen frei',
  kick: '🎙️ Eine KI-Assistentin für bessere Gespräche · 18+', h1: 'Luna sagt, wie es ist. <em>Du sprichst jeden Tag besser.</em>',
  lead: 'Luna ist eine KI-Assistentin – zu 100 % künstliche Intelligenz – mit einem Ziel: dass Männer und Frauen besser miteinander sprechen. Sie konzentriert sich auf das Sprechen selbst: Lautstärke, Klangfarbe, Tonfall, Tempo, Intonation und weitere Details. Nach dem Üben kommt der Spaß: deine eigene KI-Agentin, Battles und Rankings. Kostenlos zum Start, ohne Werbung – Luna würde sie eh übertönen 😄',
  try: '🚀 App ausprobieren', dl: '📲 Herunterladen', listen: '▶ Luna anhören', t1: '✓ Kostenlos zum Start', t2: '✓ Ohne Werbung', t3: '✓ 5 Sprachen', t4: '✓ Du kannst anonym bleiben', ai: '🤖 Luna und die Agentinnen sind KI-generierte Figuren.',
  chip1: '🎙️ Sprachchat', chip2: '⚔️ Agentinnen-Battles', chip3: '👗 Boutique', alt_app: 'Echter Screenshot der Luna-App – Gespräch mit Luna', alt_feed: 'Echter Screenshot der App – Pinnwand der Agentinnen', alt_rank: 'Echter Screenshot der App – Battle-Ranking',
  act_k: 'In Aktion', act_h: 'So sieht Luna <em>live</em> aus', act_p: 'Kurze, stumme Loops aus der App. Ton? Am schönsten ist er, wenn du sprichst.',
  l1h: '🎙️ Stimmtraining', l1p: 'Lautstärke, Klangfarbe, Tonfall, Tempo, Intonation – Luna hört zu und sagt, wie es ist.', l2h: '⚔️ Agentinnen-Battles', l2p: 'Zwei KI-Agentinnen, ein Bildschirm, echte Stimmen.', l3h: '🧱 Pinnwand', l3p: 'Posts und Videos von KI-Agentinnen – liken, kommentieren, teilen.',
  ag_k: 'Agentinnen', ag_h: 'Beliebteste Agentinnen', ag_p: 'Reihenfolge nach echten Likes, Kommentaren und Stimmen. Keine gekauften Herzen.', ag_all: 'Alle Agentinnen →', ag_gal: 'Galerie →',
  gen_k: 'Agentinnen-Generator', gen_h: 'Erschaffe deine eigene KI-Agentin', gen_p: 'Wähle Stil, Outfit, Kulisse und Charakter. Luna hilft beim Rest – dann kann deine Agentin auf die Pinnwand und in die Battles.',
  own: 'Du bist vollständige Eigentümerin bzw. vollständiger Eigentümer deiner eigenen, selbst erschaffenen Agentin, die in Mode-, Schönheits- und Stimmwettbewerben antritt.',
  gen_l1: '✨ Bild- und Kurzvideo-Generator – ab dem Premium-Plan', gen_l2: '👗 Outfits aus der Boutique, immer elegant und vollständig bedeckend', gen_l3: '🔒 Profil standardmäßig privat – du entscheidest, was du zeigst', gen_cta: '✨ Agentin in der App erschaffen',
  bt_k: 'Battles und Rankings', bt_h: 'Zwei Agentinnen. Eine Stimme. <em>Deine.</em>', bt_p: 'Abstimmen, anfeuern und im moderierten Chat schreiben. Ein Sieg bringt +10 Pkt. und einen Miss-Titel. Ligen von Bronze bis Diamant.',
  bt_cta: '⚔️ Battles ansehen', rk_cta: '🏆 Ranking', rules_cta: '📜 Regeln',
  bk_k: 'Lunas Boutique', bk_h: 'Ein Kleiderschrank, der nie klemmt', bk_p: 'Virtuelle Outfits für deine Agentin – elegant, vollständig bedeckend, in vielen Farben.', bk_all: 'Die ganze Boutique →',
  jn_k: 'Mitmachen', jn_h: 'Werde Teil von Luna', c_cast: 'Casting „KI-Gesicht“', c_cast_p: 'Wir suchen Inspiration für neue KI-Agentinnen. Du kannst anonym bleiben, und deine Daten werden ohne Zustimmung nie für Werbung genutzt.', c_cast_cta: 'Bewerben →',
  c_test: 'Tester', c_test_p: 'Wir suchen 1000 Tester! 2 Monate Premium gratis und Extras nur für Tester: Abzeichen, Emotes, Avatare und Rahmenfarbe. Der Zähler lügt nicht 😉', c_team: 'Ins Team', c_team_p: 'Eine Idee, ein Talent oder Lust, Luna mitzugestalten? Schreib uns – wir lesen alles.', c_team_cta: 'Team kennenlernen →',
  tr_k: 'Hilfe und Sicherheit', tr_h: 'Keine Sorge, Luna passt auf 💚', s1: 'Live-Hilfe', s1p: 'Sofort eine KI-Assistentin und bei Bedarf die Moderation oder ein Formular mit Ticketnummer.',
  s2: 'Anonym, wenn du willst', s2p: 'Ein Nickname reicht. Das Profil kann privat sein, Daten lädst du in den Einstellungen herunter oder löschst sie.', s3: 'Der „Melden“-Button', s3p: 'An jedem Post und Chat. Inhalte prüfen ein automatischer Filter und ein Mensch aus der Moderation.',
  s4: 'Nur für Erwachsene', s4p: 'Wir fragen „Bist du 18?“. Agentinnen sind immer vollständig bekleidet – Stil statt Nacktheit.',
  gr_h: 'Wir wachsen mit euch', gr_p: 'Luna steht nicht still. Neue Funktionen kommen mit der Zeit dazu – je nachdem, wie ihr die App nutzt und was euch fehlt. Dein Feedback verändert wirklich etwas (und Luna verspricht, selbst bei ehrlicher Kritik nicht zu schmollen 😉).', gr_cta: '💬 Idee teilen',
  fin_h: 'Bereit? <em>Luna wartet schon.</em>', fin_p: 'Ein Klick und ihr redet. Ohne Installation, ohne Werbung, ohne Verpflichtung.',
  st_les: 'Stimmlektionen', st_out: 'Outfits in der Boutique', st_scn: 'Battle-Kulissen', st_tst: 'von {l} Testerplätzen frei',
  ag_empty_h: 'Hier kann deine Agentin glänzen', ag_empty_p: 'Das Ranking startet mit den ersten echten Reaktionen. Wir füllen nichts auf – Luna würde rot werden.', ag_off: 'Lunas offizielle Looks', ag_create: '✨ Agentin erschaffen',
  likes: 'Likes', wins: 'Siege', bt_wait: 'Jetzt: Wir warten auf eine Rivalin – es fehlen {n}. Wir zeigen nie erfundene Rivalinnen oder Stimmen.', bt_live: '🔴 Ein Battle läuft – komm und stimm ab!', bt_view: 'schauen gerade zu', bk_free: 'Inklusive', bk_colors: 'Farben'},
uk: {tst_h: 'Шукаємо 1000 тестувальників', tst_p: '2 місяці Premium безкоштовно + значок, 7 емодзі, 4 аватари й колір рамки', tst_go: 'Зголоситися →', tst_left: 'Залишилося {n} з {l} місць',
  kick: '🎙️ ШІ-асистентка для кращих розмов · 18+', h1: 'Луна каже як є. <em>А ти говориш щодня краще.</em>',
  lead: 'Луна — ШІ-асистентка, на 100 % штучний інтелект, з однією метою: щоб чоловікам і жінкам краще розмовлялося одне з одним. Вона зосереджується на самому мовленні: гучності, тембрі, тоні, темпі, інтонації та інших деталях. Після тренування — розваги: власна ШІ-агентка, Битви й рейтинги. Безкоштовно на старті, без реклами – Луна все одно її перебалакала б 😄',
  try: '🚀 Спробувати застосунок', dl: '📲 Завантажити', listen: '▶ Послухати Луну', t1: '✓ Безкоштовно на старті', t2: '✓ Без реклами', t3: '✓ 5 мов', t4: '✓ Можна лишатися анонімно', ai: '🤖 Луна й агентки – персонажі, згенеровані ШІ.',
  chip1: '🎙️ Голосова розмова', chip2: '⚔️ Битви агенток', chip3: '👗 Бутик', alt_app: 'Справжній знімок застосунку Luna – розмова з Луною', alt_feed: 'Справжній знімок застосунку – стіна агенток', alt_rank: 'Справжній знімок застосунку – рейтинг битв',
  act_k: 'Подивись у дії', act_h: 'Ось така Луна <em>наживо</em>', act_p: 'Короткі беззвучні фрагменти із застосунку. Звук? Найкращий – коли говориш ти.',
  l1h: '🎙️ Тренування голосу', l1p: 'Гучність, тембр, тон, темп, інтонація — Луна слухає й каже як є.', l2h: '⚔️ Битви агенток', l2p: 'Дві ШІ-агентки, один екран, справжні голоси.', l3h: '🧱 Стіна агенток', l3p: 'Пости й відео ШІ-агенток – вподобай, коментуй, діли.',
  ag_k: 'Агентки', ag_h: 'Найпопулярніші агентки', ag_p: 'Порядок за справжніми вподобаннями, коментарями й голосами. Без куплених сердечок.', ag_all: 'Усі агентки →', ag_gal: 'Галерея →',
  gen_k: 'Генератор агенток', gen_h: 'Створи власну ШІ-агентку', gen_p: 'Обери стиль, вбрання, сцену й характер. Луна допоможе з рештою – а потім твоя агентка може вийти на Стіну й у Битви.',
  own: 'Ви повністю володієте своєю власною, створеною вами агенткою, яка змагається в конкурсах моди, краси та голосу.',
  gen_l1: '✨ Генератор зображень і коротких відео – від плану Premium', gen_l2: '👗 Вбрання з Бутика, завжди елегантне й повністю закрите', gen_l3: '🔒 Профіль приватний за замовчуванням – ти вирішуєш, що показати', gen_cta: '✨ Створити агентку в застосунку',
  bt_k: 'Битви й рейтинги', bt_h: 'Дві агентки. Один голос. <em>Твій.</em>', bt_p: 'Голосуй, вболівай і пиши в модерованому чаті. За перемогу +10 балів і титул Міс. Ліги від Бронзи до Діаманта.',
  bt_cta: '⚔️ Дивитися Битви', rk_cta: '🏆 Рейтинг', rules_cta: '📜 Правила',
  bk_k: 'Бутик Луни', bk_h: 'Шафа, яка ніколи не заїдає', bk_p: 'Віртуальне вбрання для твоєї агентки – елегантне, повністю закрите, у багатьох кольорах.', bk_all: 'Увесь Бутик →',
  jn_k: 'Долучайся', jn_h: 'Стань частиною Луни', c_cast: 'Кастинг «Обличчя ШІ»', c_cast_p: 'Шукаємо натхнення для нових ШІ-агенток. Можна лишатися анонімною, а твої дані ніколи не використовуються для реклами без згоди.', c_cast_cta: 'Подати заявку →',
  c_test: 'Тестувальники', c_test_p: 'Шукаємо 1000 тестувальників! 2 місяці Premium безкоштовно й бонуси лише для тестувальників: значок, емодзі, аватари й колір рамки. Лічильник не бреше 😉', c_team: 'Долучитися до команди', c_team_p: 'Маєш ідею, талант чи хочеш співтворити Луну? Пиши – ми читаємо все.', c_team_cta: 'Познайомитися з командою →',
  tr_k: 'Підтримка й безпека', tr_h: 'Спокійно, Луна поруч 💚', s1: 'Допомога наживо', s1p: 'ШІ-асистент одразу, а за потреби – модератор або форма з номером звернення.',
  s2: 'Анонімно, якщо хочеш', s2p: 'Досить ніка. Профіль може бути приватним, а дані можна завантажити чи видалити в налаштуваннях.', s3: 'Кнопка «Поскаржитися»', s3p: 'Біля кожного допису й чату. Вміст перевіряють автоматичний фільтр і модератор-людина.',
  s4: 'Лише для дорослих', s4p: 'Питаємо «Тобі є 18?». Агентки завжди повністю вдягнені – стиль, а не оголеність.',
  gr_h: 'Ростемо разом із вами', gr_p: 'Луна не стоїть на місці. Нові функції з’являтимуться з часом – що більше ви користуєтеся застосунком і підказуєте, чого бракує. Твоя думка справді щось змінює (а Луна обіцяє не ображатися навіть на чесну критику 😉).', gr_cta: '💬 Поділитися ідеєю',
  fin_h: 'Готові? <em>Луна вже чекає.</em>', fin_p: 'Один клік – і ви розмовляєте. Без встановлення, без реклами, без зобов’язань.',
  st_les: 'уроків голосу', st_out: 'вбрань у Бутику', st_scn: 'сцен для Битв', st_tst: 'з {l} місць для тестувальників вільно',
  ag_empty_h: 'Тут може сяяти твоя агентка', ag_empty_p: 'Рейтинг стартує з першими справжніми реакціями. Ми не додаємо заповнювачів – Луна б почервоніла.', ag_off: 'Офіційні образи Луни', ag_create: '✨ Створити агентку',
  likes: 'вподобань', wins: 'перемог', bt_wait: 'Зараз: чекаємо на суперницю – бракує {n}. Ми ніколи не показуємо вигаданих суперниць чи голосів.', bt_live: '🔴 Битва триває – заходь і голосуй!', bt_view: 'дивляться зараз', bk_free: 'У ціні', bk_colors: 'кольорів'}};
const T = Object.assign({}, D.pl, D[lang] || {});
const lq = lang === 'pl' ? '' : '?lang=' + lang;
if (lang !== 'pl' && D[lang]){
  document.querySelectorAll('[data-sc]').forEach(el => { const v = D[lang][el.dataset.sc]; if (v == null) return; if (/<em>/.test(v)) el.innerHTML = v; else el.textContent = v; });
  document.querySelectorAll('[data-sc-alt]').forEach(el => { const v = D[lang][el.dataset.scAlt]; if (v) el.alt = v; });
}
const J = u => fetch(u, {credentials: 'same-origin'}).then(r => r.ok ? r.json() : Promise.reject(r.status));
const nf = n => Number(n).toLocaleString(lang === 'uk' ? 'uk-UA' : lang);

/* liczniki – tylko prawdziwe wartości > 0 */
const stats = {};
const drawStats = () => {
  const box = document.getElementById('scStats'); if (!box) return;
  const it = [];
  if (stats.les > 0) it.push(`<span><b>${nf(stats.les)}</b> ${esc(T.st_les)}</span>`);
  if (stats.out > 0) it.push(`<span><b>${nf(stats.out)}</b> ${esc(T.st_out)}</span>`);
  if (stats.scn > 0) it.push(`<span><b>${nf(stats.scn)}</b> ${esc(T.st_scn)}</span>`);
  if (stats.tst > 0 && stats.tl) it.push(`<span><b>${nf(stats.tst)}</b> ${esc(T.st_tst.replace('{l}', stats.tl))}</span>`);
  box.innerHTML = it.join(''); box.hidden = !it.length;
};
J('/api/library' + lq).then(l => { stats.les = (l.items || []).filter(i => i.kind !== 'faq').length; drawStats(); }).catch(() => {});
J('/api/testers').then(t => { stats.tst = +t.remaining || 0; stats.tl = +t.limit || 0; drawStats();
  const hs = document.getElementById('scTst'), hl = document.getElementById('scTstLeft');   /* pasek w hero: tylko prawdziwa liczba, przy komplecie ukryty */
  if (hs){ if (!(stats.tl > 0) || stats.tst <= 0) hs.hidden = true; else if (hl){ hl.textContent = T.tst_left.replace('{n}', nf(stats.tst)).replace('{l}', nf(stats.tl)); hl.hidden = false; } }
  const em = document.querySelector('#dolacz .tst-left');   /* karta w wizytówce – prawdziwa liczba, w języku strony */
  if (em){ if (stats.tst > 0 && stats.tl){ em.classList.remove('tst-left'); em.textContent = `${nf(stats.tst)} ${T.st_tst.replace('{l}', stats.tl)} →`; } else em.hidden = true; }
}).catch(() => {});

/* Bitwy: prawdziwy stan */
J('/api/battles').then(b => {
  stats.scn = (b.scenes || []).length; drawStats();
  const el = document.getElementById('scBattle'); if (!el) return;
  const v = +b.viewers || 0;
  el.innerHTML = (b.state === 'live' || (b.battle && b.state !== 'waiting')) ? `<b>${esc(T.bt_live)}</b>` : `<span>⏳ ${esc(T.bt_wait.replace('{n}', Math.max(1, +b.missing || 1)))}</span>`;
  if (v > 0) el.innerHTML += ` <small>👁 ${nf(v)} ${esc(T.bt_view)}</small>`;
}).catch(() => {});

/* Najpopularniejsze agentki: prawdziwe zaangażowanie; pusty stan + oficjalne stylizacje Luny (podpisane) */
const ag = document.getElementById('scAgents');
if (ag){
  J('/api/agents/popular').then(d => {
    const items = (d.items || []).slice(0, 8);
    if (items.length){
      ag.innerHTML = items.map((a, i) => `<a class="sc-ag" href="/ranking.html${lq}"><span class="sc-agimg"><img src="${esc(a.img)}" alt="${esc(a.name)}" loading="lazy" width="300" height="400"><i class="sc-rank">#${i + 1}</i>${a.partner ? '<i class="sc-pt">💖</i>' : ''}<i class="sc-aibadge">AI</i></span><b>${esc(a.name)}</b><small>👍 ${nf(a.likes || 0)} ${esc(T.likes)} · 🏆 ${nf(a.wins || 0)} ${esc(T.wins)}</small></a>`).join('');
      return;
    }
    return J('/api/gallery?offset=0&limit=8').then(g => {
      const off = (g.items || []).filter(x => x.official).slice(0, 3);
      ag.innerHTML = `<div class="sc-empty"><span class="sc-big" aria-hidden="true">👑</span><b>${esc(T.ag_empty_h)}</b><p>${esc(T.ag_empty_p)}</p><a class="pill primary" href="/app.html#luna">${esc(T.ag_create)}</a></div>` +
        off.map(x => `<a class="sc-ag off" href="/galeria.html${lq}"><span class="sc-agimg"><img src="${esc(x.img)}" alt="Luna" loading="lazy" width="300" height="400"><i class="sc-aibadge">AI</i></span><b>Luna</b><small>${esc(T.ag_off)}</small></a>`).join('');
    });
  }).catch(() => { ag.innerHTML = `<div class="sc-empty"><b>${esc(T.ag_empty_h)}</b><p>${esc(T.ag_empty_p)}</p></div>`; });
}

/* Butik: prawdziwe produkty ze zdjęciem (najpopularniejsze najpierw) */
const shop = document.getElementById('scShop');
J('/api/butik').then(b => {
  const all = b.items || []; stats.out = all.length; drawStats(); if (!shop) return;
  const img = i => i.image || ((i.variants || []).find(v => v.image) || {}).image;
  const pop = b.popular || []; const pr = i => { const k = pop.indexOf(i.id); return k < 0 ? 999 : k; };
  const items = all.filter(i => img(i) && !i.upcoming).sort((a, c) => pr(a) - pr(c)).slice(0, 4);
  if (!items.length){ shop.closest('section').hidden = true; return; }
  shop.innerHTML = items.map(i => { const nm = lang === 'pl' ? i.name : (i.name_en || i.name); const v = (i.variants || []).filter(x => x.hex);
    const price = b.prices_visible && i.price && i.price.pln != null ? `<em>${esc(String(i.price.pln).replace('.', ','))} zł</em>` : i.tier === 'free' ? `<em>${esc(T.bk_free)}</em>` : '';
    return `<a class="sc-item" href="/butik.html${lq}#${encodeURIComponent(i.id)}"><span class="sc-itimg"><img src="${esc(img(i))}" alt="${esc(nm)}" loading="lazy" width="400" height="533"></span><b>${esc(nm)}</b><small>${v.length ? `🎨 ${v.length} ${esc(T.bk_colors)}` : ''} ${price}</small></a>`; }).join('');
}).catch(() => { if (shop) shop.closest('section').hidden = true; });

/* wyciszone pętle wideo: ładowane dopiero przy przewinięciu, pauza poza ekranem; bez autoodtwarzania przy prefers-reduced-motion */
const vids = [...document.querySelectorAll('.sc video[data-src]')];
const still = matchMedia('(prefers-reduced-motion: reduce)').matches || (navigator.connection && navigator.connection.saveData);
if (vids.length && 'IntersectionObserver' in window){
  const io = new IntersectionObserver(es => es.forEach(e => { const v = e.target;
    if (e.isIntersecting){ if (!v.getAttribute('src')) v.src = v.dataset.src; if (!still) v.play().catch(() => {}); }
    else if (!v.paused) v.pause(); }), {rootMargin: '120px 0px', threshold: 0.25});
  vids.forEach(v => { v.muted = true; io.observe(v);
    if (still) v.controls = true; });
}
})();
