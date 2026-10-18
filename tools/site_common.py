"""Wspólny nagłówek i stopka stron informacyjnych (generowane przez tools/build_pages.py)."""
VER = "1.4.1"
HEAD = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0a0a">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}"><meta property="og:image" content="/og-luna.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:site_name" content="Luna mówi jak jest">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon-32.png" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/manifest.json">
<link rel="stylesheet" href="/portal.css?v={ver}"><link rel="stylesheet" href="/site.css?v={ver}"><link rel="stylesheet" href="/scianka.css?v={ver}">
<script src="/twa.js"></script><style>.twa .no-twa{{display:none!important}}html:not(.twa) .twa-only{{display:none!important}}</style>
</head>
<body class="site {cls}">
<header class="top">
  <div class="bar">
    <a class="logo" href="/promo.html" aria-label="Luna mówi jak jest – strona główna"><span class="lring"><img src="/brand-emblem-256.png" alt="" width="40" height="40"></span><span class="lname">Luna <small class="lsub">mówi jak jest</small></span></a>
    <div class="acts"><a class="pill primary" href="/app">Otwórz Lunę</a></div>
  </div>
  <nav class="tabs">
    <a href="/promo.html">Porady</a><a href="/butik.html"{a_butik}>Butik</a><a href="/scianka.html"{a_wall}>Ścianka Agentek Głosu</a><a href="/live.html">Luna Live</a><a href="/testerzy.html"{a_test} class="hot">Testerzy 🎁</a><a href="/dolacz.html"{a_join}>Dołącz do projektu</a><a href="/twarz.html"{a_face}>Twarz AI</a><a href="/wesprzyj.html" class="no-twa"{a_sup}>Wesprzyj</a>
  </nav>
</header>
"""
FOOT = """<footer class="sitefoot">
  <img class="fbadge" src="/brand-badge-256.png" srcset="/brand-badge-256.png 1x, /brand-badge-512.png 2x" width="96" height="96" alt="Luna mówi jak jest" loading="lazy">
  <p class="fan" data-note="fan">Luna mówi jak jest to projekt fanowski – i taki zostanie, słowo Luny! Wspieraj nas zawsze, gdziekolwiek jesteś. 💚</p>
  <p><span class="badge-noads" data-note="noads">🚫 Bez reklam – Luna nie ogląda reklam, bo i tak by je przegadała 😄 Zero reklam, sama przyjemność gadania.</span></p>
  <p class="money no-twa" data-note="money">Luna nie je, nie śpi i nie pije kawy… ale serwery już tak ☕ Każda drobna złotówka się przyda, a wsparcie jest zawsze dobrowolne.</p>
  <p class="disc"><span class="b18">18+</span> <span data-disclaimer>Luna to asystentka AI do nauki mówienia i pracy z głosem. Produkt w żaden sposób nie ma na celu seksualizacji kobiet.</span></p>
  <nav><a href="/app">Aplikacja</a><a href="/promo.html">Porady</a><a href="/butik.html">Butik</a><a href="/scianka.html">Ścianka Agentek Głosu</a><a href="/galeria.html">Galeria agentek</a><a href="/live.html">Luna Live</a><a href="/testerzy.html">Testerzy</a><a href="/dolacz.html">Dołącz do projektu</a><a href="/twarz.html">Twarz AI</a><a href="/wesprzyj.html" class="no-twa">Wesprzyj Lunę</a><a href="/regulamin.html">Regulamin</a><a href="/privacy.html">Prywatność</a><a href="/app#live">Czat z twórcą</a></nav>
  <p class="owner">Twórca i właściciel serwisu oraz aplikacji: Hubinator❤️</p>
  <p class="copy">© 2026 Luna mówi jak jest · Luna jest asystentką AI, a jej postać została wygenerowana sztucznie · v""" + VER + """</p>
</footer>
<script src="/notices.js"></script>
"""
