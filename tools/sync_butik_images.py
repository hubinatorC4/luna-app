"""Jednym poleceniem dołącza najnowsze partie Butiku (bez fałszywych zdjęć):
  1) uruchamia /workspace/luna_butik_v2/tools/update_images.py (uzupełnia image / image_ready wg plików w img/),
  2) kopiuje img/*.jpg|webp do static/catalog/butik/,
  3) kopiuje catalog_outfits_v2.json do data/catalog_outfits.json, czyszcząc ścieżki do nieistniejących plików
     (strój bez zdjęcia dostaje image="", wariant bez zdjęcia image_ready=false → szara kropka „zdjęcie wkrótce”).
Serwer sam przeładuje katalog z bazy (butik._seed_ver = skrót pliku), zachowując statusy wydania ustawione przez moderatora.
Użycie:  python3 tools/sync_butik_images.py && ./deploy.sh "Butik: nowe zdjęcia" && (Render) trigger_deploy"""
import hashlib, json, os, shutil, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = sys.argv[1] if len(sys.argv) > 1 else "/workspace/luna_butik_v2"
DST = os.path.join(R, "static/catalog/butik"); CAT = os.path.join(R, "data/catalog_outfits.json")
os.makedirs(DST, exist_ok=True)
if os.path.exists(os.path.join(B, "tools/update_images.py")):
    subprocess.run([sys.executable, os.path.join(B, "tools/update_images.py")], check=True)
copied = 0
for f in sorted(os.listdir(os.path.join(B, "img"))):
    if not f.lower().endswith((".jpg", ".webp")) or "rejected" in f: continue
    s, d = os.path.join(B, "img", f), os.path.join(DST, f)
    if not os.path.exists(d) or os.path.getsize(d) != os.path.getsize(s): shutil.copy2(s, d); copied += 1
have = set(os.listdir(DST)); static = os.path.join(R, "static")
exists = lambda url: bool(url) and os.path.exists(os.path.join(static, url.lstrip("/")))
cat = json.load(open(os.path.join(B, "catalog_outfits_v2.json"), encoding="utf-8"))
# Wstrzymane stroje (np. zdjęcie do poprawki): tools/butik_hold.json {"id": "sha256 starego zdjęcia"}.
# Strój jest ukryty, dopóki plik img/<id>.jpg ma ten sam skrót; gdy przyjdzie nowe zdjęcie, wstrzymanie znika samo.
HOLDF = os.path.join(R, "tools/butik_hold.json")
hold = json.load(open(HOLDF)) if os.path.exists(HOLDF) else {}
def _sha(f): return hashlib.sha256(open(f, "rb").read()).hexdigest() if os.path.exists(f) else ""
held = {i for i, h in hold.items() if _sha(os.path.join(B, "img", i + ".jpg")) == h}
heroes = ready = 0
for it in cat["items"]:
    if it.get("id") in held:
        it["image"] = ""; it.pop("image_webp", None)
        for v in it.get("variants") or []: v["image_ready"] = False; v["image"] = ""; v.pop("image_webp", None)
        continue
    if not exists(it.get("image", "")): it["image"] = ""; it.pop("image_webp", None)
    else: heroes += 1
    if it.get("image_webp") and not exists(it["image_webp"]): it.pop("image_webp")
    for v in it.get("variants") or []:
        ok = exists(v.get("image", ""))
        v["image_ready"] = ok
        if not ok: v["image"] = ""; v.pop("image_webp", None)
        else:
            ready += 1
            if v.get("image_webp") and not exists(v["image_webp"]): v.pop("image_webp")
old = open(CAT, "rb").read() if os.path.exists(CAT) else b""
new = json.dumps(cat, ensure_ascii=False, indent=1).encode()
if new != old: open(CAT, "wb").write(new)
print("wstrzymane:", ", ".join(sorted(held)) or "brak", "| zwolnione (nowe zdjęcie):", ", ".join(sorted(set(hold) - held)) or "brak")
print(f"skopiowano plików: {copied} · stroje ze zdjęciem: {heroes}/{len(cat['items'])} · warianty ze zdjęciem: {ready} · katalog {'ZMIENIONY' if new != old else 'bez zmian'} · skrót {hashlib.sha256(new).hexdigest()[:10]}")
