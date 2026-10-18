#!/usr/bin/env python3
"""Buduje ostre warianty obrazów: 1x/2x JPEG+WebP, awatar 512/1024, ikony PWA i favicon.
Źródła: /workspace (luna_avatar3.png, luna_*.jpg) oraz załączniki z wygenerowanymi strojami/pozami."""
import os, glob, sys
from PIL import Image, ImageFilter, ImageDraw, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, "static")
ATT = "/cursor/stores/store-902a91ab-d561-47a7-b8e9-ddddf9099cb5/grok-bot/agents/25110661-769a-437e-89ba-c1d241a29d9d/attachments"
def att(prefix):
    g = glob.glob(os.path.join(ATT, prefix + "*.jpg")); return g[0] if g else None
SRC = {  # (rodzaj, id) -> źródło
    ("outfit", "koronkowa"): att("21adaa56") or "/workspace/luna_koronka.jpg",
    ("outfit", "wieczorowa"): att("b856a570"), ("outfit", "biznes"): att("89a471e7"),
    ("outfit", "sweter"): att("75f5b2db"),  # letnia: brak zatwierdzonego obrazu → „wkrótce”
    ("pose", "prosto"): att("b856a570"), ("pose", "polobrot"): att("3e7cac4b"),
    ("pose", "zamyslona"): att("029f5812"), ("pose", "siedzaca"): att("8f463d09"),
}
ALIAS = {"suknia": "wieczorowa", "zakiet": "biznes", "marynarka": "biznes", "koronka": "koronkowa"}
# obrazy dostarczone później w /workspace mają pierwszeństwo: luna_outfit_<id>.jpg, luna_pose_<id>.jpg, luna_body_<id>.jpg
for f in glob.glob("/workspace/luna_outfit_*.*") + glob.glob("/workspace/luna_pose_*.*") + glob.glob("/workspace/luna_body_*.*"):
    k, i = os.path.splitext(os.path.basename(f))[0].split("_", 2)[1:]
    SRC[(k, ALIAS.get(i, i))] = f

def sharp_resize(im, w):
    h = round(im.height * w / im.width)
    out = im.resize((w, h), Image.LANCZOS)
    if w > im.width:  # powiększenie: delikatne wyostrzenie
        out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    else:
        out = out.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=2))
    return out
def save_pair(im, base):
    im = im.convert("RGB")
    im.save(base + ".jpg", quality=88, optimize=True, progressive=True, subsampling=0)
    im.save(base + ".webp", quality=86, method=6)
def variants(src, base, w1):
    im = ImageOps.exif_transpose(Image.open(src))
    save_pair(sharp_resize(im, w1), base)
    save_pair(sharp_resize(im, w1 * 2), base + "@2x")

os.makedirs(os.path.join(ST, "catalog", "luna"), exist_ok=True)
for (k, i), src in SRC.items():
    if src and os.path.exists(src):
        variants(src, os.path.join(ST, "catalog", "luna", f"{k}_{i}"), 960); print("katalog:", k, i)

# promo hero (z oryginału z koronkową sukienką) i tło aplikacji
hero = SRC[("outfit", "koronkowa")]
im = Image.open(hero); w, h = im.size
crop = im.crop((int(w * .25), 0, int(w * .75), int(h * .78)))  # kadr na twarz
os.makedirs(os.path.join(ST, "promo"), exist_ok=True)
save_pair(sharp_resize(crop, 640), os.path.join(ST, "promo", "luna_hero")); save_pair(sharp_resize(crop, 1280), os.path.join(ST, "promo", "luna_hero@2x"))
save_pair(sharp_resize(im, 1280), os.path.join(ST, "luna_portrait")); save_pair(sharp_resize(im, 1920), os.path.join(ST, "luna_portrait@2x"))

# awatar 512/1024
av = Image.open("/workspace/luna_avatar3.png").convert("RGB")
_w, _h = av.size  # kadr na twarz – czytelny w małych rozmiarach
av = av.crop((int(_w * .17), int(_h * .02), int(_w * .83), int(_h * .68)))
for n in (256, 512, 1024):
    save_pair(sharp_resize(av, n), os.path.join(ST, f"avatar-{n}"))
sharp_resize(av, 512).save(os.path.join(ST, "avatar_round.png"), optimize=True)
sharp_resize(av, 512).save(os.path.join(ST, "promo", "avatar.png"), optimize=True)

def icon(size, maskable=False, ring=True):
    S = size * 4  # rysujemy w 4x i zmniejszamy (antyaliasing)
    bg = Image.new("RGB", (S, S), (11, 7, 5))
    pad = int(S * (0.14 if maskable else 0.03))
    ringw = int(S * 0.045) if ring else 0
    d = ImageDraw.Draw(bg)
    if ring: d.ellipse((pad, pad, S - pad, S - pad), fill=(46, 230, 107))
    inner = pad + ringw
    face = sharp_resize(av, S - 2 * inner)
    m = Image.new("L", face.size, 0); ImageDraw.Draw(m).ellipse((0, 0, face.size[0] - 1, face.size[1] - 1), fill=255)
    bg.paste(face, (inner, inner), m)
    if not maskable:  # przezroczyste rogi dla zwykłych ikon
        out = bg.convert("RGBA"); mm = Image.new("L", (S, S), 0); ImageDraw.Draw(mm).ellipse((pad, pad, S - pad, S - pad), fill=255)
        out.putalpha(mm); bg = out
    return bg.resize((size, size), Image.LANCZOS)
icon(192).save(os.path.join(ST, "icon-192.png")); icon(512).save(os.path.join(ST, "icon-512.png"))
icon(512, maskable=True).save(os.path.join(ST, "icon-maskable-512.png")); icon(192, maskable=True).save(os.path.join(ST, "icon-maskable-192.png"))
icon(180, maskable=True).save(os.path.join(ST, "apple-touch-icon.png"))
icon(48).save(os.path.join(ST, "favicon-48.png")); icon(32).save(os.path.join(ST, "favicon-32.png"))
icon(48).save(os.path.join(ST, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
print("gotowe")
