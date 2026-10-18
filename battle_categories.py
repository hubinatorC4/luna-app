# -*- coding: utf-8 -*-
"""Wspólna konfiguracja kategorii Bitew agentek i scenerii (używana przez serwer, aplikację i zestawy scenerii).
Dodanie scenerii: wrzuć static/bitwy/<id>.webp (+ @2x.webp, .avif, @2x.avif) i dopisz <id> do SCENES oraz do kategorii.
Sceneria bez pliku jest pomijana automatycznie. `python3 battle_categories.py` odświeża static/battle_categories.json i static/bt-cats.js."""
import json, os

LANGS = ("pl", "en", "es", "de", "uk")

# kolejność = kolejność zakładek w Rankingu
CATS = [
    {"id": "gala", "emoji": "👗", "scenes": ["gala", "studio"],
     "name": {"pl": "Elegancja i gala", "en": "Elegance & gala", "es": "Elegancia y gala", "de": "Eleganz & Gala", "uk": "Елегантність і гала"}},
    {"id": "night", "emoji": "🌃", "scenes": ["city"],
     "name": {"pl": "Miasto nocą", "en": "City at night", "es": "Ciudad de noche", "de": "Stadt bei Nacht", "uk": "Нічне місто"}},
    {"id": "beach", "emoji": "🏖️", "scenes": ["beach", "promenade"],
     "name": {"pl": "Plaża i lato", "en": "Beach & summer", "es": "Playa y verano", "de": "Strand & Sommer", "uk": "Пляж і літо"}},
    {"id": "sport", "emoji": "🏋️", "scenes": ["gym", "garden"],
     "name": {"pl": "Sport i fitness", "en": "Sport & fitness", "es": "Deporte y fitness", "de": "Sport & Fitness", "uk": "Спорт і фітнес"}},
    {"id": "business", "emoji": "💼", "scenes": ["office", "studio", "city"],
     "name": {"pl": "Biznes i styl", "en": "Business & style", "es": "Negocios y estilo", "de": "Business & Stil", "uk": "Бізнес і стиль"}},
    {"id": "nature", "emoji": "🌿", "scenes": ["garden", "winter"],
     "name": {"pl": "Natura", "en": "Nature", "es": "Naturaleza", "de": "Natur", "uk": "Природа"}},
    {"id": "voice", "emoji": "🎤", "scenes": ["studio", "gala"],
     "name": {"pl": "Głos i śpiew", "en": "Voice & singing", "es": "Voz y canto", "de": "Stimme & Gesang", "uk": "Голос і спів"}},
    {"id": "casual", "emoji": "☕", "scenes": ["promenade", "garden", "city"],
     "name": {"pl": "Casual", "en": "Casual", "es": "Casual", "de": "Casual", "uk": "Кежуал"}},
]
CAT_IDS = [c["id"] for c in CATS]
CAT = {c["id"]: c for c in CATS}
MIN_CATS, MAX_CATS = 1, 3
DEFAULT_CATS = ["casual"]
LUNA_CATS = ["voice", "gala", "night"]   # oficjalna agentka AI Luna

# wszystkie sceneria (id = nazwa pliku w static/bitwy/); podstawowy zestaw domyślny, dopóki brak danych o popularności
SCENES = ["city", "studio", "promenade", "winter", "gala", "garden", "gym", "office", "beach"]
DEFAULT_BASIC = ["city", "studio", "promenade", "gala", "garden", "winter"]
BASIC_N = 6   # Premium: 6 najpopularniejszych (prawdziwe głosy w bitwach), odświeżane co tydzień; Pro/Ultra i współpracujące: wszystkie

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "bitwy")
def available_scenes():
    return [s for s in SCENES if os.path.exists(os.path.join(_DIR, s + ".webp"))]

def clean_cats(v):
    v = [c for c in (v if isinstance(v, list) else []) if c in CAT]
    out = []
    for c in v:
        if c not in out: out.append(c)
    if not MIN_CATS <= len(out) <= MAX_CATS: raise ValueError("Wybierz od 1 do 3 kategorii.")
    return out

def public():
    return {"cats": [{"id": c["id"], "emoji": c["emoji"], "name": c["name"], "scenes": [s for s in c["scenes"] if s in available_scenes()]} for c in CATS],
            "scenes": available_scenes(), "min": MIN_CATS, "max": MAX_CATS, "basic_n": BASIC_N}

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    d = {"cats": [{k: c[k] for k in ("id", "emoji", "name", "scenes")} for c in CATS], "scenes": SCENES, "default_basic": DEFAULT_BASIC,
         "basic_n": BASIC_N, "min": MIN_CATS, "max": MAX_CATS}
    open(os.path.join(base, "battle_categories.json"), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    open(os.path.join(base, "bt-cats.js"), "w", encoding="utf-8").write(
        "/* wygenerowane z battle_categories.py – nie edytuj ręcznie */\nwindow.LUNA_BT_CATS = " + json.dumps(d, ensure_ascii=False) + ";\n")
    print("ok")
