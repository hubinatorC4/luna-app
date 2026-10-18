import json, os, re, sys, time
os.environ["CT2_FORCE_CPU_ISA"] = "AVX2"
import mt
W = "/workspace/i18n_work"; os.makedirs(W + "/cache", exist_ok=True)
SRC = json.load(open(W + "/source_en.json"))
LEG = ("json:privacy", "json:regulamin", "html:regulamin", "html:privacy", "py:tools/build_legal", "py:tools/build_battle_rules", "html:zasady")
CODE = re.compile(r"[{;]\s*[a-z-]+\s*:\s*[^\s]|=>|function\s*\(|\bvar\b|document\.|querySelector|^\.[a-z]")
def ok(s): return not CODE.search(s)
UI = [x["en"] for x in SRC if ok(x["en"]) and not all(o.startswith(LEG) for o in x["o"])]
LG = [x["en"] for x in SRC if ok(x["en"]) and all(o.startswith(LEG) for o in x["o"])]
def prep(s): return s.replace("Hubert Szumski", "Hubinator❤️")
TOP = ["fr", "it", "pt-br", "nl", "cs", "ro", "tr", "ja", "ko", "zh", "ar", "hi", "id"]
REST = ["es_skip"] and ["sk", "hu", "sv", "no", "da", "fi", "el", "bg", "hr", "sr", "lt", "lv", "et", "ru", "he", "vi", "th"]
PHASES = [(TOP, UI, 2, "ui"), (REST, UI, 1, "ui"), (TOP, LG, 2, "legal"), (REST, LG, 1, "legal")]
only = sys.argv[1:]
for langs, strs, beam, name in PHASES:
    for lang in langs:
        if only and lang not in only: continue
        f = f"{W}/cache/{lang}.json"
        cache = json.load(open(f)) if os.path.exists(f) else {}
        mt.BEAM = beam; t0 = time.time()
        todo = [prep(s) for s in strs]
        mt.translate_many(todo, lang, cache, lambda m: print(m, flush=True))
        cache.setdefault("__lost__", []).extend(mt.LOST); mt.LOST.clear()
        cache.setdefault("__phase__", []).append(name)
        json.dump(cache, open(f + ".tmp", "w"), ensure_ascii=False); os.replace(f + ".tmp", f)
        print("DONE", name, lang, f"{time.time() - t0:.0f}s", flush=True)
print("ALL DONE", flush=True)
