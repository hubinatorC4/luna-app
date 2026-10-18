"""Generuje static/zespol.html („Dołącz do zespołu”) z tools/team_content.py (szablon nagłówka/stopki: static/testerzy.html). Uruchom: python3 tools/build_team.py"""
import json, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "tools"))
from team_content import C, F
L = ['pl', 'en', 'es', 'de', 'uk']
I = {l: {k: v[i] for k, v in C.items()} for i, l in enumerate(L)}
for i, l in enumerate(L): I[l].update({"f_" + k: v[i] for k, v in F.items()})
P = I['pl']
s = open(os.path.join(R, 'static/testerzy.html'), encoding='utf-8').read()
i = s.index('<main class="page">'); j = s.index('</main>') + len('</main>')
main = f'''<main class="page team">
<div class="langtabs" role="group" aria-label="Język / Language"><button type="button" data-lang="pl">Polski</button><button type="button" data-lang="en">English</button><button type="button" data-lang="es">Español</button><button type="button" data-lang="de">Deutsch</button><button type="button" data-lang="uk">Українська</button></div>
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<div class="teamgrid">
<section class="card tcard"><h2 data-i18n="areas_h">{P['areas_h']}</h2><ul data-i18n="areas">{P['areas']}</ul></section>
<section class="card tcard honest"><h2 data-i18n="honest_h">{P['honest_h']}</h2><ul data-i18n="honest">{P['honest']}</ul></section>
<section class="card tcard"><h2 data-i18n="how_h">{P['how_h']}</h2><ol data-i18n="how">{P['how']}</ol></section>
</div>
<section class="card" id="zgloszenie"><h2 data-i18n="form_h">{P['form_h']}</h2><div data-team-form></div></section>
</main>'''
s = s[:i] + main + s[j:]
s = re.sub(r'<title>[^<]*</title>', f'<title>{P["_title"]}</title>', s, count=1)
s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Dołącz do zespołu Luny: moderacja, grafika, programowanie, marketing, tłumaczenia, głos. Uczciwie: bez obietnic pensji – warunki ustalamy indywidualnie.">', s, count=1)
s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{P["_title"]}">', s, count=1)
s = s.replace(' aria-current="page" class="hot"', ' class="hot"')
k = s.index('<script type="application/json" id="i18n">'); e = s.index('</script>', k) + len('</script>')
s = s[:k] + '<script type="application/json" id="i18n">' + json.dumps(I, ensure_ascii=False) + '</script>' + s[e:]
for x in ['<script src="/testers.js?v=1.4.1"></script>\n', '<script src="/forms18-i18n.js?v=1.0"></script>\n', '<script src="/forms18.js?v=1.0"></script>\n', '<link rel="stylesheet" href="/forms18.css?v=1.0">\n']: s = s.replace(x, '')
s = s.replace('</body>', '<script src="/team.js?v=1.0" defer></script>\n</body>', 1)
s = s.replace('</head>', '''<style>.teamgrid{display:grid;gap:16px;margin:18px 0}@media(min-width:900px){.teamgrid{grid-template-columns:1fr 1fr 1fr}}.tcard h2{margin-top:0;font-size:21px}.tcard ul,.tcard ol{margin:0;padding-left:20px;display:grid;gap:7px;line-height:1.5}.tcard.honest{border:1px solid rgba(61,220,151,.35)}
.tmf{display:grid;gap:12px;max-width:680px}.tmf label{display:grid;gap:6px;font-weight:600}.tmf small{font-weight:400;opacity:.75}.tmf input[type=text],.tmf input[type=email],.tmf input[type=url],.tmf textarea{border-radius:16px;padding:12px 14px;border:1.5px solid rgba(255,255,255,.14);background:rgba(0,0,0,.25);color:inherit;font:inherit}
.tmchips{display:flex;flex-wrap:wrap;gap:8px}.tmchips button{padding:10px 14px;border-radius:999px;border:1.5px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:inherit;font:inherit;cursor:pointer;transition:transform .15s}.tmchips button[aria-pressed=true]{border-color:#3DDC97;background:rgba(61,220,151,.16);transform:scale(1.04)}
.tmck{display:flex!important;grid-template-columns:none;gap:10px;align-items:flex-start;font-weight:400!important}.tmck input{width:20px;height:20px;margin-top:2px;accent-color:#3DDC97}.tmcnt{font-size:12px;opacity:.7;text-align:right}.tmerr{color:#ffb4a8;min-height:1.2em}.tmok{padding:16px;border-radius:22px;background:rgba(61,220,151,.12);border:1px solid rgba(61,220,151,.35)}.tmhp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
@media (prefers-reduced-motion:reduce){.tmchips button{transition:none}}</style>
</head>''', 1)
open(os.path.join(R, 'static/zespol.html'), 'w', encoding='utf-8').write(s)
print("zespol.html", len(s))
