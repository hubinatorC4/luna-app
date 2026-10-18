"""Wielojęzyczność stron: ?lang=xx, <html lang>, przetłumaczone <title>/description/OG, hreflang + x-default, sitemap.xml, robots.txt."""
import html, json, os, re
LANGS = ("pl", "en", "es", "de", "uk")
OGL = {"pl": "pl_PL", "en": "en_GB", "es": "es_ES", "de": "de_DE", "uk": "uk_UA"}
PAGES = {
 "/o-lunie.html": {"pl": ("O Lunie – trenerka głosu AI | Luna mówi jak jest", "Luna to asystentka AI i trenerka głosu: rozmowa głosowa, 45 lekcji, barwa głosu, tryb hologram i własna asystentka. Bez reklam."),
       "en": ("About Luna – AI voice coach | Luna Tells It Like It Is", "Luna is an AI assistant and voice coach: voice chat, 45 lessons, voice styles, hologram mode and your own assistant. No ads."),
       "es": ("Sobre Luna – entrenadora de voz con IA | Luna dice las cosas como son", "Luna es una asistente de IA y entrenadora de voz: chat por voz, 45 lecciones, estilos de voz, modo holograma y tu propia asistente. Sin anuncios."),
       "de": ("Über Luna – KI-Stimmtrainerin | Luna sagt, wie es ist", "Luna ist KI-Assistentin und Stimmtrainerin: Sprachchat, 45 Lektionen, Stimmfarben, Hologramm-Modus und eigene Assistentin. Ohne Werbung."),
       "uk": ("Про Луну – ШІ-тренерка голосу | Луна каже як є", "Луна – ШІ-асистентка й тренерка голосу: голосовий чат, 45 уроків, тембри голосу, режим голограми й власна асистентка. Без реклами.")},
 "/": {"pl": ("Luna mówi jak jest – asystentka AI do pracy z głosem", "Rozmawiaj z Luną, asystentką AI do nauki mówienia i pracy z głosem."),
       "en": ("Luna Tells It Like It Is – your AI voice coach", "Talk to Luna, an AI assistant for learning to speak and working with your voice."),
       "es": ("Luna dice las cosas como son – tu entrenadora de voz con IA", "Habla con Luna, una asistente de IA para aprender a hablar y trabajar la voz."),
       "de": ("Luna sagt, wie es ist – deine KI-Stimmtrainerin", "Sprich mit Luna, einer KI-Assistentin zum Sprechenlernen und für die Arbeit mit der Stimme."),
       "uk": ("Луна каже як є – твоя ШІ-тренерка голосу", "Розмовляйте з Луною — ШІ-асистенткою для навчання мовлення та роботи з голосом.")},
 "/promo.html": {"pl": ("Luna mówi jak jest – porady głosowe, Luna Live i trening wypowiedzi", "Twoja trenerka głosu AI. Porady: barwa, oddech, dykcja, tempo, pewność siebie i wystąpienia. Bez reklam."),
       "en": ("Luna Tells It Like It Is – voice tips, Luna Live and speaking practice", "Your AI voice coach. Tips on tone, breathing, diction, pace, confidence and public speaking. No ads."),
       "es": ("Luna dice las cosas como son – consejos de voz, Luna Live y práctica oral", "Tu entrenadora de voz con IA: timbre, respiración, dicción, ritmo, seguridad y hablar en público. Sin anuncios."),
       "de": ("Luna sagt, wie es ist – Stimmtipps, Luna Live und Sprechtraining", "Deine KI-Stimmtrainerin: Klangfarbe, Atmung, Aussprache, Tempo, Selbstsicherheit und Auftreten. Keine Werbung."),
       "uk": ("Луна каже як є – поради для голосу, Luna Live і тренування мовлення", "Твоя ШІ-тренерка голосу: тембр, дихання, дикція, темп, упевненість і публічні виступи. Без реклами.")},
 "/galeria.html": {"pl": ("Galeria agentek – Luna mówi jak jest", "Luna i agentki AI ze Ścianki Agentek Głosu. Agentka tygodnia według prawdziwych polubień."),
       "en": ("Agents gallery – Luna Tells It Like It Is", "Luna and AI agents from the Voice Agents’ Wall. Agent of the week by real likes."),
       "es": ("Galería de agentes – Luna dice las cosas como son", "Luna y las agentes de IA del Muro de las Agentes de Voz. Agente de la semana según «me gusta» reales."),
       "de": ("Galerie der Agentinnen – Luna sagt, wie es ist", "Luna und KI-Agentinnen von der Pinnwand. Agentin der Woche nach echten Likes."),
       "uk": ("Галерея агенток – Луна каже як є", "Луна та ШІ-агентки зі Стіни голосових агенток. Агентка тижня за справжніми вподобаннями.")},
 "/live.html": {"pl": ("Luna Live – Luna mówi jak jest", "Cotygodniowa transmisja z Luną, asystentką AI: pytania z czatu i ćwiczenia głosu."),
       "en": ("Luna Live – Luna Tells It Like It Is", "A weekly live stream with Luna, an AI assistant: questions from the chat and voice exercises."),
       "es": ("Luna Live – Luna dice las cosas como son", "Una emisión semanal con Luna, asistente de IA: preguntas del chat y ejercicios de voz."),
       "de": ("Luna Live – Luna sagt, wie es ist", "Der wöchentliche Livestream mit Luna, einer KI-Assistentin: Fragen aus dem Chat und Stimmübungen."),
       "uk": ("Luna Live – Луна каже як є", "Щотижнева трансляція з Луною, ШІ-асистенткою: запитання з чату та вправи для голосу.")},
 "/regulamin.html": {"pl": ("Regulamin – Luna mówi jak jest", "Regulamin: 18+, konto, dostęp miesięczny, ceny z VAT, płatności BLIK, prawo odstąpienia, awatary AI."),
       "en": ("Terms of service – Luna Tells It Like It Is", "Terms: 18+, account, one-month access, prices incl. VAT, BLIK payments, right of withdrawal, AI avatars."),
       "es": ("Condiciones de uso – Luna dice las cosas como son", "Condiciones: 18+, cuenta, acceso mensual, precios con IVA, pagos con BLIK, desistimiento y avatares de IA."),
       "de": ("Nutzungsbedingungen – Luna sagt, wie es ist", "Bedingungen: 18+, Konto, Monatszugang, Preise inkl. MwSt., BLIK-Zahlungen, Widerrufsrecht, KI-Avatare."),
       "uk": ("Правила користування – Луна каже як є", "Правила: 18+, обліковий запис, місячний доступ, ціни з ПДВ, оплата BLIK, право на відмову, ШІ-аватари.")},
 "/privacy.html": {"pl": ("Polityka prywatności – Luna mówi jak jest", "Jakie dane przetwarza Luna, po co i jak długo. Eksport i usunięcie konta."),
       "en": ("Privacy policy – Luna Tells It Like It Is", "What data Luna processes, why and for how long. Account export and deletion."),
       "es": ("Política de privacidad – Luna dice las cosas como son", "Qué datos trata Luna, para qué y durante cuánto tiempo. Exportación y eliminación de la cuenta."),
       "de": ("Datenschutzerklärung – Luna sagt, wie es ist", "Welche Daten Luna verarbeitet, wozu und wie lange. Export und Löschung des Kontos."),
       "uk": ("Політика конфіденційності – Луна каже як є", "Які дані обробляє Луна, навіщо і як довго. Експорт і видалення облікового запису.")},
}
def load_generated():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
    try:
        import pages_content as C
        for fn, D in (("/testerzy.html", C.TESTERZY), ("/wesprzyj.html", C.WESPRZYJ), ("/dolacz.html", C.DOLACZ), ("/twarz.html", C.TWARZ), ("/problemy.html", C.PROBLEMY), ("/butik.html", C.BUTIK), ("/scianka.html", C.WALL)):
            PAGES[fn] = {l: (D[l]["_title"], re.sub(r"<[^>]+>", "", D[l].get("lead", ""))[:160]) for l in LANGS}
    except Exception:
        pass
load_generated()

def alternates(base, path):
    p = "/" if path in ("", "/index.html") else path
    links = [f'<link rel="alternate" hreflang="{l}" href="{base}{p}?lang={l}">' for l in LANGS]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{base}{p}">')
    return "\n".join(links)

OGIMG = {"/butik.html": "/og-butik.jpg", "/twarz.html": "/og-casting.jpg", "/dolacz.html": "/og-casting.jpg", "/galeria.html": "/og-luna-star.jpg",
         "/": "/og-luna-star.jpg", "/promo.html": "/og-luna-star.jpg", "/o-lunie.html": "/og-luna-star.jpg", "/scianka.html": "/og-luna-star.jpg"}
def jsonld(base, lang):
    """Organizacja bez danych osobowych + aplikacja (tylko prawdziwe informacje)."""
    import json as _j
    org = {"@context": "https://schema.org", "@type": "Organization", "name": "Luna mówi jak jest", "url": base + "/", "logo": base + "/icon-512.png"}
    app = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Luna – trenerka głosu AI" if (lang or "pl") == "pl" else "Luna – AI voice coach",
           "applicationCategory": "EducationalApplication", "operatingSystem": "Android, Web", "url": base + "/", "image": base + "/og-luna-star.jpg",
           "inLanguage": list(LANGS), "offers": {"@type": "Offer", "price": "0", "priceCurrency": "PLN"}}
    return "".join(f'<script type="application/ld+json">{_j.dumps(x, ensure_ascii=False)}</script>' for x in (org, app))

def localize(doc, path, lang, base):
    p = "/" if path in ("", "/index.html") else path
    meta = PAGES.get(p, {}).get(lang) if lang else None
    l = lang or "pl"
    doc = re.sub(r'<html lang="[a-z]{2}"', f'<html lang="{l}"', doc, count=1)
    if meta:
        t, d = (html.escape(x, quote=True) for x in meta)
        doc = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", doc, count=1, flags=re.S)
        doc = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{d}">', doc, count=1)
        doc = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">', doc)
        if 'og:title' not in doc: doc = doc.replace("</title>", f'</title>\n<meta property="og:title" content="{t}">', 1)
        if 'name="description"' not in doc: doc = doc.replace("</title>", f'</title>\n<meta name="description" content="{d}">', 1)
        doc = doc.replace("</title>", f'</title>\n<meta property="og:description" content="{d}"><meta property="og:locale" content="{OGL[l]}">', 1)
    canon = f"{base}{'/' if p == '/promo.html' else p}" + (f"?lang={lang}" if lang else "")
    if p in OGIMG: doc = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{OGIMG[p]}">', doc, count=1)
    if "og:locale" not in doc: doc = doc.replace("</title>", f'</title>\n<meta property="og:locale" content="{OGL[l]}">', 1)
    if 'property="og:type"' not in doc: doc = doc.replace("</title>", '</title>\n<meta property="og:type" content="website">', 1)
    doc = re.sub(r'(<meta property="og:image" content=")/', r"\g<1>" + base + "/", doc)
    if "twitter:card" not in doc:
        mt = re.search(r"<title>(.*?)</title>", doc, re.S); md = re.search(r'<meta name="description" content="([^"]*)"', doc); mi = re.search(r'<meta property="og:image" content="([^"]*)"', doc)
        tw = '<meta name="twitter:card" content="summary_large_image">' + (f'<meta name="twitter:title" content="{mt.group(1).strip()}">' if mt else "") + \
             (f'<meta name="twitter:description" content="{md.group(1)}">' if md else "") + (f'<meta name="twitter:image" content="{mi.group(1)}">' if mi else "")
        doc = doc.replace("</head>", tw + "\n</head>", 1)
    if p in ("/", "/promo.html", "/o-lunie.html") and "application/ld+json" not in doc: doc = doc.replace("</head>", jsonld(base, lang) + "\n</head>", 1)
    if 'og:url' not in doc: doc = doc.replace("</head>", f'<meta property="og:url" content="{canon}">\n</head>', 1)
    doc = doc.replace("</head>", f'<link rel="canonical" href="{canon}">\n{alternates(base, path)}\n<script src="/langswitch.js" defer></script>\n<script src="/emoji.js" defer></script>\n<link rel="stylesheet" href="/soft.css">\n</head>', 1)
    doc = re.sub(r'(<meta charset="utf-8">)', r'\1<script src="/lg.js"></script>', doc, count=1, flags=re.I)
    return doc

def sitemap(base):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in [x for x in PAGES if x not in ("/privacy.html", "/regulamin.html", "/promo.html")]:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{base}{p}?lang={l}"/>' for l in LANGS) + f'<xhtml:link rel="alternate" hreflang="x-default" href="{base}{p}"/>'
        out.append(f"<url><loc>{base}{p}</loc>{alts}</url>")
        for l in LANGS: out.append(f"<url><loc>{base}{p}?lang={l}</loc>{alts}</url>")
    out.append("</urlset>")
    return "\n".join(out)

def robots(base):
    return f"User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /panel.html\nSitemap: {base}/sitemap.xml\n"
