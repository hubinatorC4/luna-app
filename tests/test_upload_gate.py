"""t479u: filtr nagości i jedna bramka dla wszystkich obrazów. Tylko syntetyczne, neutralne obrazy testowe (gradienty, figury) – bez treści dla dorosłych.
Uruchom: python3 -m unittest tests.test_upload_gate -v"""
import ast, base64, io, json, os, sys, tempfile, unittest
from unittest import mock
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.pop("DATABASE_URL", None)
import store
_TMP = tempfile.mkdtemp(); store.FILE = os.path.join(_TMP, "kv.json"); store._mem = None
from PIL import Image, ImageDraw
import nsfw_filter, upload_gate, imgsafe, textsafe

def png(w=400, h=300, color=(40, 90, 160), fmt="PNG", **kw):
    """Syntetyczny, neutralny obraz: niebieskie tło, zielone wzgórze, żółte słońce (bez ludzi)."""
    im = Image.new("RGB", (w, h), color); d = ImageDraw.Draw(im)
    d.ellipse((w * 0.65, h * 0.1, w * 0.85, h * 0.37), fill=(250, 210, 60)); d.rectangle((0, h * 0.7, w, h), fill=(40, 140, 60))
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()
def durl(raw, mime="png"): return f"data:image/{mime};base64," + base64.b64encode(raw).decode()

BLOCK = ("block", "TEST_BLOCK", {"FEMALE_BREAST_EXPOSED": 0.99})
class _Spy:
    """Podmienia nsfw_filter.classify_all na „blokada” i zapisuje konteksty, z którymi wołano upload_gate.image."""
    def __init__(self, verdict=BLOCK): self.v = verdict; self.ctx = []
    def __enter__(self):
        orig = upload_gate.image
        def spy(src, ctx, **kw): self.ctx.append(ctx); return orig(src, ctx, **kw)
        self.p = [mock.patch.object(nsfw_filter, "classify_all", lambda raw: self.v), mock.patch.object(upload_gate, "image", spy)]
        for p in self.p: p.start()
        store.put("nsfw_hash_block", [])
        return self
    def __exit__(self, *a):
        for p in self.p: p.stop()
        store.put("nsfw_hash_block", [])

# ---------------------------------------------------------------- warstwy bramki
class GateLayers(unittest.TestCase):
    def setUp(self): store.put("nsfw_hash_block", [])
    def rej(self, src, exc=upload_gate.Rejected, **kw):
        with self.assertRaises(exc): upload_gate.image(src, "test", **kw)
    def test_benign_passes_real_models(self):
        r = upload_gate.image(durl(png()), "test")
        self.assertEqual(r.verdict, "ok"); self.assertIn(imgsafe.kind(r.bytes), ("jpg", "png"))
    def test_svg_html_gif_pdf_rejected(self):
        self.rej("data:image/svg+xml;base64," + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>").decode())
        self.rej(durl(b"<html><body>hi</body></html>"))
        self.rej(durl(png(fmt="GIF"), "gif"))
        self.rej(durl(png(fmt="GIF"), "png"))           # GIF udający PNG – sygnatura
        self.rej(durl(b"%PDF-1.4 fake"))
        self.rej("https://example.com/x.jpg")           # zewnętrzne adresy obrazów nie są przyjmowane
    def test_polyglot_rejected(self):
        self.rej(durl(png(fmt="JPEG") + b"<script>alert(1)</script>", "jpeg"))
        self.rej(durl(png() + b"<?php echo 1; ?>"))
    def test_animated_rejected(self):
        fr = [Image.new("RGB", (64, 64), c) for c in ((255, 0, 0), (0, 255, 0))]
        b = io.BytesIO(); fr[0].save(b, "WEBP", save_all=True, append_images=fr[1:]); self.rej(durl(b.getvalue(), "webp"))
        b = io.BytesIO(); fr[0].save(b, "PNG", save_all=True, append_images=fr[1:]); self.rej(durl(b.getvalue()))   # APNG
    def test_size_limits(self):
        self.rej(durl(png(9000, 20)))                     # za długi bok
        self.rej(durl(png(4, 4)))                         # za mały
        self.rej(durl(png()), max_in=100)                 # za duży plik
        self.rej("data:image/png;base64,@@@notbase64")
    def test_exif_stripped(self):
        im = Image.open(io.BytesIO(png(fmt="JPEG"))); ex = Image.Exif(); ex[0x010F] = "CameraMaker"; ex[0x8825] = {2: (52.0, 13.0, 0.0)}
        b = io.BytesIO(); im.save(b, "JPEG", exif=ex.tobytes()); raw = b.getvalue()
        self.assertIn(b"CameraMaker", raw)
        out = upload_gate.image(durl(raw, "jpeg"), "test").bytes
        self.assertNotIn(b"CameraMaker", out); self.assertNotIn(b"Exif", out)
    def test_hash_blocklist_survives_resize(self):
        raw = png(); im = Image.open(io.BytesIO(raw)); h = upload_gate.dhash(im)[0]
        upload_gate.add_hash(h, "test")
        small = io.BytesIO(); im.resize((200, 150)).save(small, "JPEG", quality=70)
        with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(small.getvalue(), "jpeg"), "test")
        mir = io.BytesIO(); im.transpose(Image.FLIP_LEFT_RIGHT).save(mir, "PNG")
        with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(mir.getvalue()), "test")   # odbicie lustrzane
    def test_block_adds_hash_and_audit(self):
        with mock.patch.object(nsfw_filter, "classify_all", lambda raw: BLOCK):
            with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(png()), "test")
        self.assertEqual(len(store.get("nsfw_hash_block")), 1)
        self.assertTrue(any(a["action"] == "nsfw_block" for a in store.get("audit", [])))
        with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(png()), "test")   # już bez modelu – po skrócie
    def test_fail_closed_when_model_missing(self):
        with mock.patch.object(nsfw_filter, "_sessions", lambda: (None, None)):
            with self.assertRaises(nsfw_filter.Blocked) as c: upload_gate.image(durl(png()), "test")
        self.assertIn("niedostępny", str(c.exception))
    def test_fail_closed_on_scan_error(self):
        def boom(*a, **k): raise RuntimeError("x")
        with mock.patch.object(nsfw_filter, "scores", boom):
            with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(png()), "test")
    def test_review_modes(self):
        rv = ("review", "TEST", {})
        with mock.patch.object(nsfw_filter, "classify_all", lambda raw: rv):
            self.assertEqual(upload_gate.image(durl(png()), "test").verdict, "review")
            with self.assertRaises(nsfw_filter.Held): upload_gate.image(durl(png()), "test", review="hold")
            with self.assertRaises(nsfw_filter.Blocked): upload_gate.image(durl(png()), "test", review="block")
    def test_no_bypass_parameter(self):
        import inspect
        for f in (upload_gate.image, nsfw_filter.enforce, nsfw_filter.classify):
            ps = set(inspect.signature(f).parameters)
            self.assertFalse(ps & {"admin", "bypass", "skip", "force", "owner", "trusted"}, f.__name__)

# ---------------------------------------------------------------- decyzje (bez modeli)
class Decide(unittest.TestCase):
    d = staticmethod(nsfw_filter.decide)
    def test_thresholds(self):
        self.assertEqual(self.d({})[0], "ok")
        self.assertEqual(self.d({"FEMALE_GENITALIA_EXPOSED": 0.56})[0], "block")
        self.assertEqual(self.d({"FEMALE_BREAST_EXPOSED": 0.61})[0], "block")
        self.assertEqual(self.d({"FEMALE_BREAST_EXPOSED": 0.45})[0], "review")
        self.assertEqual(self.d({"FEMALE_BREAST_EXPOSED": 0.45, "m2_porn": 0.55})[0], "block")   # dwa głosy
        self.assertEqual(self.d({"m2_porn": 0.85})[0], "block")
        self.assertEqual(self.d({"m2_hentai": 0.9})[0], "block")
        self.assertEqual(self.d({"m2_sexy": 0.6})[0], "review")
        self.assertEqual(self.d({"t_BUTTOCKS_EXPOSED": 0.9})[0], "review")    # ćwiartki – tylko do moderatora
        self.assertEqual(self.d({"FEMALE_GENITALIA_COVERED": 0.5})[0], "review")
        self.assertEqual(self.d({"MALE_BREAST_EXPOSED": 0.6})[0], "review")
        self.assertEqual(self.d({"skin": 0.7})[0], "review")
        self.assertEqual(self.d({"FEMALE_GENITALIA_COVERED": 0.7, "BELLY_EXPOSED": 0.6})[0], "block")
    def test_enforce_error_blocks(self):
        with mock.patch.object(nsfw_filter, "classify_all", lambda raw: ("error", "unavailable:X", {})):
            with self.assertRaises(nsfw_filter.Blocked): nsfw_filter.enforce(b"x", "t")
    def test_animated_every_frame_scanned(self):
        fr = [Image.new("RGB", (64, 64), ((i * 25) % 256, (i * 70) % 256, (i * 130) % 256)) for i in range(10)]
        b = io.BytesIO(); fr[0].save(b, "GIF", save_all=True, append_images=fr[1:])
        seen = []
        def cl(raw, im=None): seen.append(1); return ("ok", "", {})
        with mock.patch.object(nsfw_filter, "classify", cl): nsfw_filter.classify_all(b.getvalue())
        self.assertEqual(len(seen), 10)

# ---------------------------------------------------------------- każde miejsce używa bramki
class EverySurfaceUsesGate(unittest.TestCase):
    """Dla każdego miejsca przyjmującego obraz: przy werdykcie „blokada” nic nie przechodzi, a bramka była wołana z kontekstem miejsca."""
    def check(self, fn, ctx, exc=nsfw_filter.Blocked):
        with _Spy() as s:
            with self.assertRaises(exc): fn()
        self.assertIn(ctx, s.ctx)
    def test_avatar(self):
        import avatars; self.check(lambda: avatars.check_upload(durl(png()), True, "v1", "x"), "avatar")
    def test_user_avatar(self):
        import userprof; self.check(lambda: userprof.set_avatar_upload("u" * 16, "premium", durl(png())), "user_avatar")
    def test_wall_ai_and_battles(self):
        import social, battles
        self.check(lambda: social.avatars_check_wall(durl(png()), True), "wall_ai")
        with mock.patch.object(battles, "my_entry", lambda uid: None), mock.patch.object(social, "banned", lambda ak: False):
            self.check(lambda: battles.enter("u" * 16, {"modest": True, "rules": True, "name": "Ola", "image": durl(png()), "img_decl": True}), "wall_ai")
    def test_wall_user_photo(self):
        import social
        self.check(lambda: social.user_photo_wall(durl(png()), {k: True for k in social.USER_DECL}, "u" * 16), "wall_user")
    def test_dm_photo(self):
        import inbox, social
        with mock.patch.object(inbox, "uid_of", lambda p: "o" * 16), mock.patch.object(inbox, "_need_friend", lambda a, b: True), \
             mock.patch.object(inbox, "_fr", lambda u: {"blocked": [], "ph_ack": 1}), mock.patch.object(social, "banned", lambda ak: False):
            self.check(lambda: inbox.dm_photo("u" * 16, "p", durl(png()), "premium", ack=True), "dm")
    def test_tickets(self):
        import tickets, time
        self.check(lambda: tickets.submit({"t0": 0, "category": tickets.CATS[0], "description": "opis problemu tutaj", "screenshot": durl(png())}), "ticket")
        self.check(lambda: tickets.submit_support({"t0": 0, "category": tickets.SUP_CATS[0], "title": "Tytuł testu", "description": "x" * 30, "screenshot": durl(png())}),
                   "support", exc=ValueError)
    def test_admin_upload_no_bypass(self):
        import catalog
        with mock.patch.object(catalog, "UPLOADS", _TMP): self.check(lambda: catalog.save_upload("a.png", png()), "admin_upload")
    def test_admin_real_person_no_bypass(self):
        import profiles, partners
        P = {"pid1": {"uid": "u" * 16, "photos": [], "name": "A"}}
        with mock.patch.object(profiles, "_P", lambda: P), mock.patch.object(partners, "is_partner", lambda uid: True):
            self.check(lambda: profiles.admin_real_photo("pid1", durl(png()), "UM-123"), "admin_real")
    def test_chat_avatar_dropped(self):
        import livechat
        with _Spy() as s: self.assertEqual(livechat.clean_avatar(durl(png(64, 64))), "")
        self.assertIn("chat_avatar", s.ctx)
        self.assertEqual(imgsafe.safe_avatar_dataurl("data:image/svg+xml;base64,PHN2Zz4="), "")
    def test_generator_output_scanned_before_anyone_sees_it(self):
        import agentgen, quality
        b64 = base64.b64encode(png()).decode()
        J = {"j1": {"id": "j1", "uid": "u" * 16, "kind": "img", "t": 0, "plan": "premium", "px": 512, "prompt": agentgen.prompt({"hair": "brown", "outfit": "sweater"}),
                    "status": "waiting", "variants": [], "picked": [], "approved": [], "note": ""}}
        store.put("agent_gen", J); sent = {}
        def call(url, key, body, timeout=120): sent.update(body); return {"images": [b64, b64], "has_nsfw_concepts": [True, False]}
        with _Spy() as s, mock.patch.object(agentgen, "_call", call), mock.patch.object(quality, "gen_take", lambda u, p: (True, 1, 5)), \
             mock.patch.dict(os.environ, {"LUNA_IMAGE_API_URL": "http://x", "LUNA_IMAGE_API_KEY": "k"}):
            agentgen._run("j1")
        j = store.get("agent_gen")["j1"]
        self.assertEqual(j["variants"], []); self.assertEqual(j["note"], "nsfw")
        self.assertEqual(s.ctx, ["agent_gen"])                 # 1. obraz odrzucony już przez flagę dostawcy, 2. przez nasz filtr
        self.assertEqual(sent["negative"], agentgen.NEG); self.assertEqual(sent["safety_tolerance"], 0); self.assertTrue(sent["enable_safety_checker"])
        self.assertIn(agentgen.SAFE, sent["prompt"])
    def test_generator_refuses_bad_prompts_before_generation(self):
        import agentgen
        for t in ("w bikini na plaży", "sexy look", "lingerie", "wygląda na 16 lat", "teen", "Unterwäsche", "купальник", "lencería", "p0rn"):
            with self.assertRaises(ValueError, msg=t): agentgen.clean_desc(t)
        self.assertEqual(agentgen.clean_desc("lubi jazz i góry"), "lubi jazz i góry")
        with self.assertRaises(ValueError): agentgen.safe_body("woman in bikini", {})

class StaticNoBypass(unittest.TestCase):
    """Nikt nie woła niskopoziomowego ponownego kodowania ani filtra z pominięciem bramki – poza jawną listą pochodnych już sprawdzonych obrazów."""
    LOW = {("imgsafe", "reencode"), ("imgsafe", "reencode_webp"), ("nsfw_filter", "enforce"), ("nsfw_filter", "check_dataurl"), ("nsfw_filter", "classify")}
    ALLOW = {("quality.py", "scaled_dataurl"): "zmiana rozmiaru przy wydawaniu obrazów zapisanych PO bramce"}
    INFRA = {"upload_gate.py", "imgsafe.py", "nsfw_filter.py"}
    def test_ast(self):
        bad = []
        for fn in sorted(os.listdir(ROOT)):
            if not fn.endswith(".py") or fn in self.INFRA: continue
            with open(os.path.join(ROOT, fn), encoding="utf-8") as fh: tree = ast.parse(fh.read())
            for fnode in ast.walk(tree):
                if not isinstance(fnode, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
                for n in ast.walk(fnode):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and (n.func.value.id, n.func.attr) in self.LOW:
                        if (fn, fnode.name) not in self.ALLOW: bad.append(f"{fn}:{fnode.name}:{n.lineno} {n.func.value.id}.{n.func.attr}")
        self.assertEqual(bad, [], "Obrazy muszą iść przez upload_gate.image(): " + ", ".join(bad))
    def test_modules_decoding_user_images_use_gate(self):
        import re
        miss = []
        for fn in sorted(os.listdir(ROOT)):
            if not fn.endswith(".py") or fn in self.INFRA: continue
            with open(os.path.join(ROOT, fn), encoding="utf-8") as fh: s = fh.read()
            if re.search(r'fullmatch\(r"data:image/', s) and "upload_gate" not in s and fn not in ("server.py",): miss.append(fn)
        self.assertEqual(miss, [])

class Text(unittest.TestCase):
    def test_blocks(self):
        for t in ("p0rn", "n a k e d", "nudes?", "nastolatka nago", "15 lat i seks", "child porn", "голий", "desnuda", "nackt", "🍆🍑"):
            self.assertIsNotNone(textsafe.scan(t, "text")[0], t)
    def test_minor_sexual_is_special(self):
        self.assertEqual(textsafe.scan("teen nude", "text")[0], "minor_sexual")
        with self.assertRaises(textsafe.Refused): textsafe.check_text("teen nude")
    def test_no_false_positives(self):
        for t in ("Hej, super głos!", "Sussex is nice", "sexto día", "moje dziecko lubi Lunę", "Kinder sind toll", "nagroda", "nagonka",
                  "Das ist geil", "голос Луни", "lody i lodami", "Jana Kedzierska", "string quartet", "analiza tekstu", "therapist"):
            self.assertIsNone(textsafe.scan(t, "text")[0], t)
    def test_social_hooks(self):
        import social
        with self.assertRaises(ValueError): social.check_text("free p.o.r.n here", 200)
        with self.assertRaises(ValueError): social.nick_ok("sexy_kitty")
        self.assertEqual(social.nick_ok("Kasia2000"), "Kasia2000")

if __name__ == "__main__": unittest.main()
