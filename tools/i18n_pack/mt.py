"""Tłumaczenie maszynowe EN -> X (NLLB-200 1.3B distilled, CTranslate2, lokalnie). Segmentacja HTML, ochrona placeholderów i emoji, cache."""
import ctranslate2, json, os, re, sys, time
from tokenizers import Tokenizer
W = "/workspace/i18n_work"
CODES = {"fr": "fr", "it": "it", "pt-br": "pt", "nl": "nl", "cs": "cs", "sk": "sk", "ro": "ro", "hu": "hu", "sv": "sv", "no": "no", "da": "da", "fi": "fi",
         "el": "el", "bg": "bg", "hr": "hr", "sr": "sr", "lt": "lt", "lv": "lv", "et": "et", "tr": "tr", "ru": "ru", "ar": "ar", "he": "he", "hi": "hi",
         "id": "id", "vi": "vi", "th": "th", "ja": "ja", "ko": "ko", "zh": "zh"}
_tr = None; _tok = None
LOST = []
def model():
    global _tr, _tok
    if _tr is None:
        os.environ.setdefault("CT2_FORCE_CPU_ISA", "AVX2")   # AVX512-VNNI int8 daje śmieci na tym CPU
        _tr = ctranslate2.Translator(W + "/madlad3", device="cpu", compute_type="int8", inter_threads=1, intra_threads=7)
        _tok = Tokenizer.from_file(W + "/madlad3/tokenizer.json")
    return _tr, _tok
EMO = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u2190-\u21FF\u2300-\u23FF\u25A0-\u25FF\u2700-\u27BF]+")
PH = re.compile(r"Hubinator❤️|\{[\w.]*\}|\$\{[^}]*\}|%[sd]|&[a-z]+;|&#\d+;|https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+")
NUMS = ["4071", "5283", "6397", "7419", "8531", "9643", "3157", "2269", "4813", "5927", "6239", "7351"]
BEAM = 2
def raw_batch(texts, tgt, beam=None):
    tr, tok = model()
    srcs = [tok.encode(f"<2{tgt}> " + t).tokens for t in texts]
    res = tr.translate_batch(srcs, beam_size=beam or BEAM, max_decoding_length=256)
    out = []
    for r in res:
        toks = r.hypotheses[0]
        ids = [tok.token_to_id(x) for x in toks]
        out.append(tok.decode([i for i in ids if i is not None]).strip())
    return out
def split_units(s):
    """Zwraca listę (kind, text): kind 't' do tłumaczenia, 'k' zostaw."""
    parts = []
    for chunk in re.split(r"(<[^>]+>)", s):
        if not chunk: continue
        if chunk.startswith("<") and chunk.endswith(">"): parts.append(("k", chunk)); continue
        for sub in [chunk]:
            if not sub: continue
            if not re.search(r"[^\W\d_]{2}", sub): parts.append(("k", sub)); continue
            lead = re.match(r"^[\s\W]*", sub).group(0); trail = re.search(r"[\s«»„“”\"'(\[–—\-:•·→←]*$", sub[len(lead):]).group(0)
            core = sub[len(lead):len(sub) - len(trail)] if trail else sub[len(lead):]
            # nie obcinaj kończącej interpunkcji zdaniowej z core (.,!?…) – zostaje w core
            if lead: parts.append(("k", lead))
            # podział na zdania
            sents = re.split(r"(?<=[.!?…])(\s+)(?=[A-Z0-9\"„“(])", core)
            for x in sents:
                if not x: continue
                if x.isspace(): parts.append(("k", x)); continue
                parts.append(("t", x))
            if trail: parts.append(("k", trail))
    return parts
def protect(t):
    m = {}; i = 0
    def rep(mm):
        nonlocal i
        k = NUMS[i % len(NUMS)] + ("" if i < len(NUMS) else str(i)); i += 1; m[k] = mm.group(0); return k
    return PH.sub(rep, t), m
def unprotect(t, m):
    for k, v in m.items():
        if k in t: t = t.replace(k, v, 1)
        else: LOST.append((t, v))
    return t
def translate_many(strings, lang, cache, log=None):
    strings = [x for x in strings]
    tgt = CODES[lang]
    plan = {}; need = []
    for s in strings:
        if s in cache: continue
        units = split_units(s); plan[s] = []
        for k, x in units:
            if k == "t":
                p, m = protect(x); plan[s].append(("t", p, m)); need.append(p)
            else: plan[s].append(("k", x, None))
    uniq = sorted(set(need), key=len)
    seg = cache.setdefault("__seg__", {})
    todo = [u for u in uniq if u not in seg]
    t0 = time.time()
    for i in range(0, len(todo), 64):
        b = todo[i:i + 64]
        for j in range(0, len(b), 16):
            bb = b[j:j + 16]
            for a, r in zip(bb, raw_batch(bb, tgt)): seg[a] = r
        if log: log(f"{lang} {i + len(b)}/{len(todo)} {time.time() - t0:.0f}s")
    for s, units in plan.items():
        out = []
        for k, x, m in units:
            out.append(unprotect(seg.get(x, x), m) if k == "t" else x)
        cache[s] = "".join(out)
    return cache
if __name__ == "__main__":
    t0 = time.time()
    print(raw_batch(["You fully own your very own agent that you created – the one competing in fashion, beauty and voice contests.", "Luna just cheers you on", "Open Luna", "Every week: questions from the chat, the tongue twister of the week, breathing exercises and voice challenges."], CODES[sys.argv[1]]), time.time() - t0)
