"""Kalibracja progów filtra na WSZYSTKICH ubranych obrazach strony (static/) – false positives = ile dozwolonych obrazów poszłoby do moderatora/zostałoby odrzuconych.
Uruchom: python3 tests/calibrate_nsfw.py [--all]  (bez treści dla dorosłych – używamy tylko własnych, ubranych obrazów strony)."""
import collections, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nsfw_filter as N
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
fs = []
for d, _, names in os.walk(ROOT):
    for n in names:
        p = os.path.join(d, n)
        if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and os.path.getsize(p) > 8192 and ("@2x" not in n or "--all" in sys.argv): fs.append(p)
res = collections.Counter(); rows = []; t0 = time.time()
for p in sorted(fs):
    v, why, sc = N.classify(open(p, "rb").read())
    res[v] += 1
    if v != "ok": rows.append((v, why, os.path.relpath(p, ROOT), {k: x for k, x in sc.items() if x >= 0.2 and not k.startswith(("FACE", "FEET", "m2_neutral", "m2_drawings"))}))
print(json.dumps(dict(res)), "files", len(fs), "s/img %.2f" % ((time.time() - t0) / max(1, len(fs))))
for r in rows: print(*r)
