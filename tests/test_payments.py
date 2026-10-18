import hashlib, hmac, json, os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("DATABASE_URL", None)
import payments, store

def sign(payload, secret, t=None):
    t = t or int(time.time())
    return f"t={t},v1=" + hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()

class T(unittest.TestCase):
    def setUp(self): store.put("payments_done", {})
    def ev(self, sid="cs_test_1", status="paid", kind="pass", ref="premium"):
        return {"type": "checkout.session.completed", "data": {"object": {"id": sid, "payment_status": status, "client_reference_id": "u1",
                "metadata": {"kind": kind, "ref": ref, "uid": "u1"}, "amount_total": 3999, "currency": "pln"}}}
    def test_signature(self):
        p = json.dumps(self.ev()).encode(); sec = "whsec_fake"
        self.assertTrue(payments.verify(p, sign(p, sec), sec))
        self.assertFalse(payments.verify(p, sign(p, "whsec_other"), sec))
        self.assertFalse(payments.verify(p + b" ", sign(p, sec), sec))
        self.assertFalse(payments.verify(p, sign(p, sec, int(time.time()) - 3600), sec))
        self.assertFalse(payments.verify(p, "", sec))
    def test_idempotent_grant(self):
        got = []
        g = lambda uid, plan, m: got.append(("pass", uid, plan)); gi = lambda uid, ref: got.append(("item", uid, ref))
        self.assertEqual(payments.handle(self.ev(), g, gi), "granted")
        self.assertEqual(payments.handle(self.ev(), g, gi), "duplicate")
        self.assertEqual(payments.handle(self.ev("cs_2", "unpaid"), g, gi), "pending")
        self.assertEqual(payments.handle(self.ev("cs_3", kind="item", ref="cla-010"), g, gi), "granted")
        self.assertEqual(got, [("pass", "u1", "premium"), ("item", "u1", "cla-010")])

if __name__ == "__main__": unittest.main()
