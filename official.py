"""Oficjalne wpisy Ścianki z wersjonowanego pliku data/wall_official.json (przetrwają redeploy bez DATABASE_URL).
Ceny produktów i planów dobierane na żywo z katalogu Butiku i cennika – nic nie jest zapisane na sztywno."""
import json, os
import butik
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "wall_official.json")
_D = None
def data():
    global _D
    if _D is None:
        try: _D = json.load(open(F, encoding="utf-8"))
        except (OSError, ValueError): _D = {"posts": []}
    return _D
def raw(): return data().get("posts", [])
def get(pid): return next((p for p in raw() if p["id"] == pid), None)
TIER = {"free": "basic", "darmowy": "basic", "podstawowa": "basic", "premium": "premium", "pro": "pro"}
def items(ids, pricing):
    out = []
    for iid in ids:
        it = butik.item(iid)
        if not it or it.get("status") == "hidden": continue
        pr = it["price"] if pricing.get("foreign") else {"pln": it["price"]["pln"]}
        st = butik.eff_status(it)
        out.append({"id": iid, "collection": it.get("collection", ""), "tier": TIER.get(it.get("tier"), "basic"),
                    "price": pr if pricing.get("show") else None, "upcoming": st != "released", "release_date": it.get("release_date")})
    return out
def public(p, lang, pricing, extra):
    d = data(); va = p["v"]; shown = lang if lang in va else "pl"
    plans = {k: v["pln"] for k, v in pricing.get("plans", {}).items()} if pricing.get("show") else None
    return {"id": p["id"], "nick": d["account"].get(shown, d["account"]["pl"]), "avatar": d.get("avatar"), "verified_label": d["verified"].get(shown),
            "text": va[shown]["text"], "lang": shown, "orig": "pl", "variants": {l: x["text"] for l, x in va.items()},
            "official": True, "rich": {"kind": p["kind"], "v": va, "items": items(p.get("items", []), pricing), "plans": plans, "foreign": bool(pricing.get("foreign")), "links": p.get("links", {})},
            "img": p["img"], "img_ai": True, "agent": None, "t": p["t"], "edited": 0, "mine": False, "pending": False, **extra}
