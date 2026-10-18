import ast, glob, json, os, re, collections
R = "/workspace/wt_i18n"
src = collections.OrderedDict()   # en -> set(origins)
def add(s, o):
    if not isinstance(s, str): return
    s2 = s.strip()
    if not s2 or not re.search(r"[A-Za-z]{2}", s2): return
    if re.fullmatch(r"[\w.\-/#?=&:%]+", s2) and " " not in s2 and not re.search(r"[A-Z][a-z]", s2): return  # klucze, ścieżki
    src.setdefault(s, set()).add(o)
def leaves(v, o):
    if isinstance(v, str): add(v, o)
    elif isinstance(v, (list, tuple)): [leaves(x, o) for x in v]
    elif isinstance(v, dict): [leaves(x, o) for k, x in v.items() if not str(k).startswith("_url")]
# 1. i18n/*.json
for f in sorted(glob.glob(R + "/i18n/*.json")):
    d = json.load(open(f)); n = os.path.basename(f)[:-5]
    if n == "library": leaves(d["en"], "json:library"); continue
    for pl, en in d["en"]:
        add(en[1:] if en.startswith("~") else en, "json:" + n)
# 2. embedded <script id="i18n"> in static html
for f in sorted(glob.glob(R + "/static/**/*.html", recursive=True)):
    h = open(f, encoding="utf-8").read()
    for m in re.finditer(r'<script type="application/json" id="i18n">(.*?)</script>', h, re.S):
        try: d = json.loads(m.group(1))
        except Exception: continue
        if isinstance(d, dict) and "en" in d: leaves(d["en"], "html:" + os.path.basename(f))
# 3. python dicts/5-lists
def pyscan(f):
    try: t = ast.parse(open(f, encoding="utf-8").read())
    except Exception as e: print("PYERR", f, e); return
    o = "py:" + os.path.relpath(f, R)
    for n in ast.walk(t):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "en":
                    for x in ast.walk(v):
                        if isinstance(x, ast.Constant) and isinstance(x.value, str): add(x.value, o)
                        if isinstance(x, ast.JoinedStr): add("".join(p.value if isinstance(p, ast.Constant) else "{}" for p in x.values), o)
        if isinstance(n, (ast.List, ast.Tuple)) and len(n.elts) == 5 and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.elts):
            vals = [e.value for e in n.elts]
            if vals[0] != vals[1] or re.search("[ąćęłńóśźż]", vals[0]): add(vals[1], o)
for f in sorted(glob.glob(R + "/*.py") + glob.glob(R + "/tools/*.py") + glob.glob(R + "/tools/i18n_src/*.py")):
    if "/i18n_src/" in f: continue   # już w json
    pyscan(f)
# 4. JS
for x in json.load(open("/workspace/i18n_work/js_en.json")):
    add(x["s"], "js:" + x["file"])
out = [{"en": k, "o": sorted(v)} for k, v in src.items()]
json.dump(out, open("/workspace/i18n_work/source_en.json", "w"), ensure_ascii=False, indent=0)
c = collections.Counter(o.split(":")[0] for x in out for o in x["o"][:1])
print(len(out), sum(len(x["en"]) for x in out), c)
