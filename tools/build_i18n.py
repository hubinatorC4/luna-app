"""Kompiluje tools/i18n_src/*.py -> i18n/*.json (tłumaczenia stron publicznych, stosowane po stronie serwera)."""
import json, os, runpy, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = ["pl", "en", "es", "de", "uk"]
LIB = {}
for f in sorted(glob.glob(os.path.join(R, "tools/i18n_src/*.py"))):
    n = os.path.basename(f)[:-3]
    if n.startswith("library_"):
        LIB[n[8:]] = runpy.run_path(f)["T"]; continue
    E = runpy.run_path(f)["E"]
    for e in E: assert len(e) == 5, (f, e[0][:40])
    out = {l: [[e[0], e[i]] for e in E] for i, l in enumerate(L) if l != "pl"}
    json.dump(out, open(os.path.join(R, "i18n", n + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(n, len(E))
json.dump(LIB, open(os.path.join(R, "i18n", "library.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("library", {k: len(v["items"]) for k, v in LIB.items()})
