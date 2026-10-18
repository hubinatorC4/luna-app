"""Generuje static/zaufanie.html z tools/trust_content.py (szablon nagłówka/stopki: static/testerzy.html). Uruchom: python3 tools/build_trust.py"""
import json, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "tools"))
from trust_content import C
L = ['pl', 'en', 'es', 'de', 'uk']
I = {l: {k: v[i] for k, v in C.items()} for i, l in enumerate(L)}
P = I['pl']
s = open(os.path.join(R, 'static/testerzy.html'), encoding='utf-8').read()
i = s.index('<main class="page">'); j = s.index('</main>') + len('</main>')
main = f'''<main class="page trust">
<div class="langtabs" role="group" aria-label="Język / Language"><button type="button" data-lang="pl">Polski</button><button type="button" data-lang="en">English</button><button type="button" data-lang="es">Español</button><button type="button" data-lang="de">Deutsch</button><button type="button" data-lang="uk">Українська</button></div>
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<div class="trustgrid">
<section class="card tcard" id="anonimowosc"><h2 data-i18n="anon_h">{P['anon_h']}</h2><ul data-i18n="anon">{P['anon']}</ul></section>
<section class="card tcard"><h2 data-i18n="safe_h">{P['safe_h']}</h2><ul data-i18n="safe">{P['safe']}</ul></section>
<section class="card tcard pink" id="modelki"><h2 data-i18n="models_h">{P['models_h']}</h2><ul data-i18n="models">{P['models']}</ul><p><a class="pill" href="/zgloszenie.html?f=casting">🎙️ Casting</a></p></section>
<section class="card tcard" id="wlasnosc"><h2 data-i18n="own_h">{P['own_h']}</h2><p class="own-line"><i aria-hidden="true">👑</i><span><strong data-i18n="own_line">{P['own_line']}</strong></span></p><ul data-i18n="own">{P['own']}</ul></section>
<section class="card tcard" id="odpowiedzialnosc"><h2 data-i18n="resp_h">{P['resp_h']}</h2><ul data-i18n="resp">{P['resp']}</ul></section>
<section class="card tcard" id="zasady"><h2 data-i18n="rules_h">{P['rules_h']}</h2><ul data-i18n="rules">{P['rules']}</ul></section>
<section class="card tcard report" id="zglos"><h2 data-i18n="rep_h">{P['rep_h']}</h2><p data-i18n="rep">{P['rep']}</p><p class="tbtns"><a class="pill primary" href="/problemy.html" data-i18n="rep_b">{P['rep_b']}</a> <a class="pill" href="/problemy.html" data-i18n="app_b">{P['app_b']}</a></p></section>
</div>
<p class="hint" data-i18n="honest">{P['honest']}</p>
</main>'''
s = s[:i] + main + s[j:]
s = re.sub(r'<title>[^<]*</title>', f'<title>{P["_title"]}</title>', s, count=1)
s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Bezpieczeństwo i anonimowość w Lunie: wystarczy nick, profil prywatny, moderacja, bramka 18+, bez przechowywania dokumentów i kart. Zasady, odpowiedzialność i zgłaszanie.">', s, count=1)
s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{P["_title"]}">', s, count=1)
s = s.replace(' aria-current="page" class="hot"', ' class="hot"')
k = s.index('<script type="application/json" id="i18n">'); e = s.index('</script>', k) + len('</script>')
s = s[:k] + '<script type="application/json" id="i18n">' + json.dumps(I, ensure_ascii=False) + '</script>' + s[e:]
for x in ['<script src="/testers.js?v=1.4.1"></script>\n', '<script src="/forms18-i18n.js?v=1.0"></script>\n', '<script src="/forms18.js?v=1.0"></script>\n', '<link rel="stylesheet" href="/forms18.css?v=1.0">\n']: s = s.replace(x, '')
s = s.replace('</head>', '''<style>.trustgrid{display:grid;gap:16px;margin:18px 0}@media(min-width:820px){.trustgrid{grid-template-columns:1fr 1fr}}.tcard h2{margin-top:0;font-size:21px}.tcard ul{margin:0;padding-left:20px;display:grid;gap:7px;line-height:1.5}.tcard.pink{border:1px solid rgba(255,105,180,.45);box-shadow:0 0 0 4px rgba(255,105,180,.08),var(--shadow-soft)}.tcard.report{border:1px solid rgba(255,154,60,.35)}.tbtns{display:flex;flex-wrap:wrap;gap:10px}.own-line{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:22px;background:linear-gradient(135deg,rgba(61,220,151,.12),rgba(255,154,60,.08));border:1px solid rgba(61,220,151,.28)}.own-line i{font-style:normal;font-size:20px}</style>
</head>''', 1)
open(os.path.join(R, 'static/zaufanie.html'), 'w', encoding='utf-8').write(s)
print("zaufanie.html", len(s))
