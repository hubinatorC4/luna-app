"""Czcionki pakietu językowego (Noto, SIL OFL 1.1): instancja wght 400–700, wdth 100, podzbiór do potrzebnych znaków → woff2."""
import glob, json, os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset
F = "/workspace/i18n_work/fonts"; OUT = "/workspace/wt_i18n/static/fonts/i18n"
def chars_for(langs):
    s = set()
    for l in langs:
        p = f"/workspace/wt_i18n/static/lang/{l}.json"
        if os.path.exists(p):
            d = json.load(open(p)); s |= set("".join(d.get("t", {}).values()))
        p2 = f"/workspace/wt_i18n/i18n/ext/{l}.json"
        if os.path.exists(p2): s |= set("".join(json.load(open(p2)).values()))
    return s
JOBS = [
 ("NotoSansArabic[wdth,wght].ttf", "noto-arabic", "U+0600-06FF,U+0750-077F,U+08A0-08FF,U+FB50-FDFF,U+FE70-FEFF,U+200C-200F,U+0020-0040,U+060C,U+061B,U+061F,U+0640,U+066A-066D", None),
 ("NotoSansHebrew[wdth,wght].ttf", "noto-hebrew", "U+0590-05FF,U+FB1D-FB4F,U+200C-200F,U+0020-0040", None),
 ("NotoSansDevanagari[wdth,wght].ttf", "noto-devanagari", "U+0900-097F,U+A8E0-A8FF,U+1CD0-1CFF,U+200C-200D,U+20B9,U+0020-0040", None),
 ("NotoSansThai[wdth,wght].ttf", "noto-thai", "U+0E00-0E7F,U+200C-200D,U+0020-0040", None),
 ("NotoSansJP[wght].ttf", "noto-jp", None, ["ja"]),
 ("NotoSansKR[wght].ttf", "noto-kr", None, ["ko"]),
 ("NotoSansSC[wght].ttf", "noto-sc", None, ["zh"]),
]
for src, name, ranges, langs in JOBS:
    f = TTFont(os.path.join(F, src), lazy=False)
    axes = {a.axisTag: a for a in f["fvar"].axes} if "fvar" in f else {}
    lim = {}
    if "wght" in axes: lim["wght"] = (400, 700)
    if "wdth" in axes: lim["wdth"] = 100
    if lim:
        import io; f = instancer.instantiateVariableFont(f, lim); b = io.BytesIO(); f.save(b); b.seek(0); f = TTFont(b, lazy=False)
    if ranges:
        uni = []
        for r in ranges.split(","):
            a, _, b = r.replace("U+", "").partition("-"); uni += range(int(a, 16), int(b or a, 16) + 1)
    else:
        cs = chars_for(langs) | set("　、。・ー「」『』（）！？：；…〜·，．") | set(chr(c) for c in range(0x3040, 0x3100))   # kana zawsze
        uni = sorted(ord(c) for c in cs if ord(c) > 0x2E7F)
    opt = subset.Options(); opt.flavor = "woff2"; opt.layout_features = ["*"]; opt.name_IDs = ["*"]; opt.notdef_outline = True
    sub = subset.Subsetter(opt); sub.populate(unicodes=uni); sub.subset(f)
    out = os.path.join(OUT, name + ".woff2"); f.flavor = "woff2"; f.save(out)
    print(name, len(uni), os.path.getsize(out))
import shutil; shutil.copy(os.path.join(F, "OFL.txt"), os.path.join(OUT, "OFL-Noto.txt"))
