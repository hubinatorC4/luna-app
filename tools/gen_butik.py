"""Generuje przykładową bazę Butiku Luny: 3 linie × 150 strojów = 450 (data/catalog_outfits.json). Deterministycznie (seed)."""
import json, os, random
random.seed(20261018)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINES = {
    "ekonomiczna": {"name": "Linia Ekonomiczna", "usd": (1.0, 5.0), "tier": "podstawowa",
                    "collections": ["Codzienna Lekkość", "Miejski Poranek", "Kawa i Notatki", "Ciepły Dom", "Pierwszy Krok"]},
    "classic": {"name": "Linia Classic", "usd": (6.0, 30.0), "tier": "premium",
                "collections": ["Klasyka Biura", "Weekend w Mieście", "Jesienne Tony", "Scena i Mikrofon", "Spokojna Elegancja"]},
    "couture": {"name": "Linia Couture", "usd": (31.0, 99.99), "tier": "pro",
                "collections": ["Gala Księżycowa", "Złota Scena", "Haute Couture Luna", "Noc Premiery", "Limitowana Aurora"]},
}
CATS = {
    "sukienki": ("sukienka", "dress", [("midi z rękawem 3/4", "midi 3/4-sleeve"), ("maxi z długim rękawem", "long-sleeve maxi"), ("kopertowa do kolan", "knee-length wrap"), ("koszulowa z paskiem", "belted shirt"), ("plisowana midi", "pleated midi")]),
    "bluzki": ("bluzka", "blouse", [("z kołnierzykiem", "collared"), ("z bufiastym rękawem", "puff-sleeve"), ("kopertowa", "wrap"), ("z wiązaniem pod szyją", "tie-neck"), ("z delikatnym żabotem", "jabot")]),
    "spódnice": ("spódnica", "skirt", [("plisowana midi", "pleated midi"), ("ołówkowa do kolan", "knee-length pencil"), ("rozkloszowana midi", "flared midi"), ("maxi", "maxi"), ("trapezowa za kolano", "below-knee A-line")]),
    "spodnie": ("spodnie", "trousers", [("z szeroką nogawką", "wide-leg"), ("cygaretki", "cigarette"), ("w kant", "creased"), ("palazzo", "palazzo"), ("z wysokim stanem", "high-waisted")]),
    "żakiety": ("żakiet", "blazer", [("taliowany", "tailored"), ("oversize", "oversized"), ("dwurzędowy", "double-breasted"), ("krótki", "cropped"), ("z paskiem", "belted")]),
    "swetry": ("sweter", "sweater", [("z golfem", "turtleneck"), ("kardigan na guziki", "button cardigan"), ("w warkocze", "cable-knit"), ("z zakrytym dekoltem w łódkę", "boat-neck"), ("oversize", "oversized")]),
    "płaszcze": ("płaszcz", "coat", [("kopertowy", "wrap"), ("trencz", "trench"), ("dwurzędowy", "double-breasted"), ("z pelerynką", "caped"), ("długi z paskiem", "long belted")]),
    "suknie wieczorowe": ("suknia wieczorowa", "evening gown", [("z długim rękawem", "long-sleeve"), ("z peleryną", "caped"), ("z wysokim kołnierzem", "high-neck"), ("z trenem", "with train"), ("z zakrytymi ramionami", "covered-shoulder")]),
    "sportowe-skromne": ("komplet sportowy", "modest sports set", [("z luźną bluzą", "relaxed sweatshirt"), ("z długą tuniką", "long tunic"), ("z kapturem i joggerami", "hoodie and joggers"), ("do jogi z długim rękawem", "long-sleeve yoga"), ("trekkingowy", "trekking")]),
    "dodatki": ("dodatek", "accessory", [("– apaszka jedwabna", "silk scarf"), ("– kapelusz z rondem", "brimmed hat"), ("– rękawiczki", "gloves"), ("– pasek z klamrą", "buckle belt"), ("– opaska do włosów", "headband")]),
}
COLORS = [("bordowy", "burgundy"), ("butelkowa zieleń", "bottle green"), ("granatowy", "navy"), ("karmelowy", "caramel"), ("kremowy", "cream"),
          ("grafitowy", "graphite"), ("pudrowy róż", "powder pink"), ("szałwiowy", "sage"), ("musztardowy", "mustard"), ("lawendowy", "lavender"),
          ("czekoladowy", "chocolate"), ("złoty", "gold"), ("srebrny", "silver"), ("szmaragdowy", "emerald"), ("kobaltowy", "cobalt"), ("czarny", "black"), ("biały", "white")]
MATS = {"ekonomiczna": [("bawełna", "cotton"), ("dzianina", "knit"), ("len", "linen"), ("wiskoza", "viscose"), ("dżersej", "jersey")],
        "classic": [("wełna", "wool"), ("satyna", "satin"), ("tweed", "tweed"), ("kaszmir z wełną", "cashmere blend"), ("szyfon na podszewce", "lined chiffon"), ("welur", "velour")],
        "couture": [("jedwab", "silk"), ("aksamit", "velvet"), ("brokat", "brocade"), ("koronka na nieprześwitującej podszewce", "lace on opaque lining"), ("tafta", "taffeta"), ("krepa jedwabna z cekinami", "sequined silk crepe")]}
POET = ["Księżycowy", "Poranny", "Ciepły", "Spokojny", "Promienny", "Aksamitny", "Szepczący", "Złoty", "Miejski", "Jesienny", "Wiosenny", "Gwiezdny", "Sceniczny", "Wieczorny", "Cichy"]
POET_EN = ["Moonlit", "Morning", "Warm", "Calm", "Radiant", "Velvet", "Whispering", "Golden", "Downtown", "Autumn", "Spring", "Starry", "Stage", "Evening", "Quiet"]
RELEASED = [("koronkowa", "Koronkowa sukienka", "Lace dress", "sukienki", "ekonomiczna", "free", "1.0"),
            ("sweter", "Sweter (na co dzień)", "Everyday sweater", "swetry", "ekonomiczna", "podstawowa", "1.2"),
            ("biznes", "Marynarka (biznes)", "Business blazer", "żakiety", "classic", "premium", "1.2"),
            ("koktajlowa", "Sukienka koktajlowa", "Cocktail dress", "sukienki", "classic", "pro", "1.2"),
            ("wieczorowa", "Suknia wieczorowa", "Evening gown", "suknie wieczorowe", "couture", "premium", "1.2")]

def r99(x): return round(int(x) + 0.99, 2)
def prices(usd):
    usd = min(99.99, max(1.0, usd))
    if usd < 1.5: return {"usd": 1.0, "eur": 0.99, "pln": 3.99}
    return {"usd": min(r99(usd), 99.99), "eur": max(0.99, min(r99(usd * 0.92), 99.99)), "pln": max(3.99, min(r99(usd * 3.99), 429.99))}

items, seen = [], set()
for line, L in LINES.items():
    lo, hi = L["usd"]
    rel = [r for r in RELEASED if r[4] == line]
    for i, pl, en, cat, _, tier, ver in rel:
        items.append({"id": i, "name": pl, "name_en": en, "line": line, "collection": L["collections"][0], "category": cat,
                      "colors": [], "material": "", "description": f"{pl} – strój dostępny już w aplikacji.",
                      "price": prices(lo + (hi - lo) * 0.25), "tier": tier,
                      "rarity": {"ekonomiczna": "zwykły", "classic": "rzadki", "couture": "ekskluzywny"}[line],
                      "image_prompt": "", "image": f"/catalog/luna/outfit_{i}.jpg", "status": "released", "release_version": ver})
    n = len(rel); k = 0
    while n < 150:
        cat = list(CATS)[k % len(CATS)]; k += 1
        noun, noun_en, cuts = CATS[cat]
        cut, cut_en = random.choice(cuts); col, col_en = random.choice(COLORS); mat, mat_en = random.choice(MATS[line]); pi = random.randrange(len(POET))
        adj = POET[pi] if noun.endswith(("t", "r", "k", "c", "z", "s")) and cat not in ("sukienki", "bluzki", "spódnice", "suknie wieczorowe") else POET[pi][:-1] + ("a" if cat in ("sukienki", "bluzki", "spódnice", "suknie wieczorowe") else "e" if cat == "spodnie" else "y")
        if cat in ("sukienki", "bluzki", "spódnice", "suknie wieczorowe"): adj = POET[pi][:-1] + "a"
        elif cat == "spodnie": adj = POET[pi][:-1] + ("e" if not POET[pi].endswith("y") else "e")
        else: adj = POET[pi]
        name = f"{adj} {noun} {cut} · {col}"
        if name.lower() in seen: continue
        seen.add(name.lower()); n += 1
        t = random.random() ** (1.5 if line == "couture" else 1.2); usd = lo + (hi - lo) * t
        tier = "free" if (line == "ekonomiczna" and n <= 12) else L["tier"]
        rarity = {"ekonomiczna": "zwykły", "classic": "rzadki"}.get(line) or ("limitowany" if usd > 70 else "ekskluzywny")
        coll = L["collections"][4] if rarity == "limitowany" else L["collections"][random.randrange(4)]
        items.append({
            "id": f"{line[:3]}-{n:03d}", "name": name[0].upper() + name[1:], "name_en": f"{POET_EN[pi]} {cut_en} {noun_en} · {col_en}",
            "line": line, "collection": coll, "category": cat, "colors": [col], "material": mat,
            "description": f"{noun.capitalize()} {cut}, kolor {col}, materiał: {mat}. Elegancki, skromny krój z kolekcji „{coll}”.",
            "price": prices(usd), "tier": tier, "rarity": rarity,
            "image_prompt": (f"Tasteful fashion illustration of the AI character Luna (same face as reference image) wearing a {col_en} {mat_en} {cut_en} {noun_en}"
                             f"{', glamorous gala couture details' if line == 'couture' else ''}; modest and non-revealing, sleeves or covered shoulders, "
                             f"knee-length or longer where applicable, warm studio light, full outfit visible, no text, no logos, no real brands"),
            "image": "", "status": "planned", "release_version": None})
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump({"version": 1, "lines": {k: {"name": v["name"], "usd": list(v["usd"]), "collections": v["collections"]} for k, v in LINES.items()}, "items": items},
          open(os.path.join(ROOT, "data", "catalog_outfits.json"), "w"), ensure_ascii=False, indent=1)
print(len(items), sum(1 for i in items if i["status"] == "released"))
