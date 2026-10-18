"""E2E (lokalnie albo na żywo): kluczowe strony 200, filtr gotowy, neutralny obraz przechodzi, zły typ pliku odrzucony, trasy admina bez autoryzacji zamknięte.
Użycie: python3 tests/e2e_filter.py http://localhost:8893 [--no-upload] [--admin-sweep]   (tylko syntetyczne, neutralne obrazy)"""
import base64, io, json, os, re, sys, urllib.request, urllib.error
from PIL import Image, ImageDraw
BASE = sys.argv[1].rstrip("/"); ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def req(path, body=None, method=None, hdr=None):
    h = {"Content-Type": "application/json", "User-Agent": "LunaQA/1.0 (filter-e2e)"}; h.update(hdr or {})
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return x.status, x.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
def png():
    im = Image.new("RGB", (256, 256), (40, 90, 160)); d = ImageDraw.Draw(im); d.ellipse((160, 30, 220, 90), fill=(250, 210, 60)); d.rectangle((0, 180, 256, 256), fill=(40, 140, 60))
    b = io.BytesIO(); im.save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
res = []
def ok(name, cond, info=""): res.append((name, bool(cond), info)); print(("✅" if cond else "❌"), name, info)
for p in ("/", "/app", "/scianka.html", "/bitwy.html", "/agentki.html", "/bezpieczenstwo.html", "/regulamin.html", "/zgloszenie.html"):
    c, _ = req(p); ok("GET " + p, c == 200, str(c))
c, b = req("/api/health"); h = json.loads(b or b"{}"); ok("health photo_filter", h.get("photo_filter") is True, json.dumps(h))
if "--no-upload" not in sys.argv:
    c, b = req("/api/avatar/upload", {"data": png(), "ai_declared": True, "vid": "qa-filter", "name": "QA filtr"}); ok("benign upload passes", c == 200 and b'"ok": true' in b, f"{c} {b[:80]!r}")
svg = "data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>").decode()
c, b = req("/api/avatar/upload", {"data": svg, "ai_declared": True, "vid": "qa-filter", "name": "QA"}); ok("SVG rejected", c == 400, f"{c} {b[:90].decode('utf-8','replace')}")
c, b = req("/api/avatar/upload", {"data": "data:image/png;base64," + base64.b64encode(b"<html><script>alert(1)</script></html>").decode(), "ai_declared": True}); ok("HTML-as-PNG rejected", c == 400, str(c))
c, b = req("/api/avatar/upload", {"data": png()}, hdr={"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"}); ok("cross-site POST blocked (CSRF)", c == 403, str(c))
c, b = req("/"); 
try:
    with urllib.request.urlopen(urllib.request.Request(BASE + "/", headers={"User-Agent": "LunaQA"}), timeout=30) as x: csp = x.headers.get("Content-Security-Policy", "")
except Exception: csp = ""
ok("CSP: no inline/external scripts, images only self/data/blob", "script-src 'self'" in csp and "img-src 'self' data: blob:" in csp, csp[:120])
if "--admin-sweep" in sys.argv:
    paths = set()
    for fn in os.listdir(ROOT):
        if fn.endswith(".py"): paths |= set(re.findall(r'"(/api/(?:admin|mod)/[\w\-/]+)"', open(os.path.join(ROOT, fn), encoding="utf-8").read()))
    paths -= {"/api/mod/public", "/api/mod/state", "/api/admin/login"}
    opened = []
    for p in sorted(paths):
        for m in ("GET", "POST"):
            c, b = req(p, {} if m == "POST" else None, m)
            if c == 200 and not re.search(rb'"(error|login|stage)"', b or b""): opened.append(f"{m} {p} {b[:60]!r}")
    ok(f"admin/mod routes closed without auth ({len(paths)} paths × GET/POST)", not opened, "; ".join(opened)[:400])
print(json.dumps({"passed": sum(1 for r in res if r[1]), "total": len(res)}))
sys.exit(0 if all(r[1] for r in res) else 1)
