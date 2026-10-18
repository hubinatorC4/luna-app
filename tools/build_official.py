"""Buduje data/wall_official.json (oficjalne wpisy Ścianki, zatwierdzone przez właściciela) + obrazy WebP.
Źródło treści: tools/official_texts.py (kopia luna_scianka_oficjalne/src/texts.py). Ceny NIE są tu zapisywane –
serwer dobiera je z katalogu Butiku i cennika planów przy każdym żądaniu."""
import json, os, re, sys, datetime
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "tools"))
import official_texts as OT
SRC = "/workspace/luna_scianka_oficjalne/img"
IMG = ["butik", "butik_swieta", "casting", "premium", "trening", "druzyna"]
ITEMS = [["sweter", "biznes", "wieczorowa"], ["cla-128", "cou-117", "eko-132"], [], [], [], []]
LINKS = [{"btn": "/butik.html"}, {"btn": "/butik.html#nowosci"}, {"link": "/twarz.html"}, {"btn": "/promo.html#plany"}, {"btn": "/"}, {"btn": "/twarz.html", "btn2": "/dolacz.html"}]
# Kolejność czytania od góry: 1 Butik … 6 Drużyna → najnowszy znacznik czasu ma wpis 1 (5 minut odstępu).
T1 = int(datetime.datetime(2026, 10, 18, 16, 45, tzinfo=datetime.timezone.utc).timestamp())
plain = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h.replace("&nbsp;", " "))).strip()
out = {"account": {l: OT.T[l]["acc"] for l in OT.LANGS}, "verified": {l: OT.T[l]["ver"] for l in OT.LANGS},
       "avatar": "/wall/official/logo.webp", "posts": []}
for i in range(6):
    v = {}
    for l in OT.LANGS:
        a = dict(OT.T[l][f"p{i+1}"]); a["tiers"] = OT.T[l]["tiers"]
        a["names"] = {iid: OT.ITEMS[iid][4][l] for iid in ITEMS[i]}
        if i == 2: a["url"] = OT.URL
        a["text"] = plain(a["tag"] + " · " + a["h"])
        v[l] = a
    out["posts"].append({"id": f"off-{i+1}", "kind": i + 1, "t": T1 - i * 300, "img": f"/wall/official/{IMG[i]}.webp", "items": ITEMS[i], "links": LINKS[i], "v": v})
for n in IMG:
    Image.open(f"{SRC}/{n}.jpg").convert("RGB").save(os.path.join(R, "static/wall/official", n + ".webp"), "WEBP", quality=80, method=6)
Image.open(f"{SRC}/logo.png").save(os.path.join(R, "static/wall/official/logo.webp"), "WEBP", quality=90, method=6)
json.dump(out, open(os.path.join(R, "data/wall_official.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", [(p["id"], p["t"]) for p in out["posts"]])
