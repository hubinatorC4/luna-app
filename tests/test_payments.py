"""Płatności: podpisy Stripe/Paddle, idempotentne przyznawanie, subskrypcje, tryb „wkrótce”, przychody/CSV – na zdarzeniach-atrapach (bez kluczy)."""
import hashlib, hmac, json, os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("DATABASE_URL", None)
import payments, store

def sign(payload, secret, t=None):
    t = t or int(time.time())
    return f"t={t},v1=" + hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
def psign(payload, secret, ts=None):
    ts = ts or int(time.time())
    return f"ts={ts};h1=" + hmac.new(secret.encode(), f"{ts}:".encode() + payload, hashlib.sha256).hexdigest()

class Base(unittest.TestCase):
    def setUp(self):
        store.put("payments_done", {}); store.put("pay_customers", {}); store.put("pay_subs", {})
        self.got = []; self.audit = []
        payments.AUDIT = lambda a, d: self.audit.append(a)
        self.g = lambda uid, plan, m: self.got.append(("pass", uid, plan)); self.gi = lambda uid, ref: self.got.append(("item", uid, ref))

class Stripe(Base):
    def ev(self, sid="cs_test_1", status="paid", kind="pass", ref="premium", mode="payment"):
        return {"type": "checkout.session.completed", "data": {"object": {"id": sid, "mode": mode, "payment_status": status, "client_reference_id": "u1", "customer": "cus_1",
                "metadata": {"kind": kind, "ref": ref, "uid": "u1"}, "amount_total": 5999, "currency": "pln"}}}
    def test_signature(self):
        p = json.dumps(self.ev()).encode(); sec = "whsec_fake"
        self.assertTrue(payments.verify(p, sign(p, sec), sec))
        self.assertFalse(payments.verify(p, sign(p, "whsec_other"), sec))
        self.assertFalse(payments.verify(p + b" ", sign(p, sec), sec))
        self.assertFalse(payments.verify(p, sign(p, sec, int(time.time()) - 3600), sec))
        self.assertFalse(payments.verify(p, "", sec))
    def test_idempotent_grant(self):
        self.assertEqual(payments.handle(self.ev(), self.g, self.gi), "granted")
        self.assertEqual(payments.handle(self.ev(), self.g, self.gi), "duplicate")
        self.assertEqual(payments.handle(self.ev("cs_2", "unpaid"), self.g, self.gi), "pending")
        self.assertEqual(payments.handle(self.ev("cs_3", kind="item", ref="cla-010"), self.g, self.gi), "granted")
        self.assertEqual(self.got, [("pass", "u1", "premium"), ("item", "u1", "cla-010")])
        self.assertIn("pay stripe pass", self.audit)
        self.assertEqual(payments.customer("u1", "stripe")[0], "cus_1")
    def test_unknown_plan_not_granted(self):
        self.assertEqual(payments.handle(self.ev("cs_9", ref="ultra-free"), self.g, self.gi), "unknown"); self.assertEqual(self.got, [])
    def test_subscription_invoice(self):
        self.assertEqual(payments.handle(self.ev("cs_s", kind="sub", mode="subscription"), self.g, self.gi), "sub_started")
        self.assertEqual(self.got, [])   # dostęp dopiero po invoice.paid
        inv = {"type": "invoice.paid", "data": {"object": {"id": "in_1", "amount_paid": 5999, "currency": "pln",
               "parent": {"subscription_details": {"metadata": {"uid": "u1", "ref": "pro", "kind": "sub"}}}}}}
        self.assertEqual(payments.handle(inv, self.g, self.gi), "granted")
        self.assertEqual(payments.handle(inv, self.g, self.gi), "duplicate")
        inv2 = json.loads(json.dumps(inv)); inv2["data"]["object"]["id"] = "in_2"
        self.assertEqual(payments.handle(inv2, self.g, self.gi), "granted")   # odnowienie = kolejne 30 dni
        self.assertEqual(self.got, [("pass", "u1", "pro"), ("pass", "u1", "pro")])

class Paddle(Base):
    def ev(self, tid="txn_1", sub=None, md=None, et="transaction.completed"):
        return {"event_id": "evt_" + tid, "event_type": et, "data": {"id": tid, "status": "completed", "customer_id": "ctm_1", "subscription_id": sub, "currency_code": "EUR",
                "custom_data": md if md is not None else {"kind": "pass", "ref": "premium", "uid": "u2"}, "items": [{"price": {"id": "pri_x"}}],
                "details": {"totals": {"total": "1499", "tax": "280", "fee": "125", "earnings": "1094"}}}}
    def test_signature(self):
        p = json.dumps(self.ev()).encode(); sec = "pdl_ntfset_fake"
        self.assertTrue(payments.verify_paddle(p, psign(p, sec), sec))
        self.assertFalse(payments.verify_paddle(p, psign(p, "other"), sec))
        self.assertFalse(payments.verify_paddle(p + b"x", psign(p, sec), sec))
        self.assertFalse(payments.verify_paddle(p, psign(p, sec, int(time.time()) - 3600), sec))
        self.assertFalse(payments.verify_paddle(p, "", sec))
    def test_grant_and_renewal(self):
        self.assertEqual(payments.handle_paddle(self.ev(), self.g, self.gi), "granted")
        self.assertEqual(payments.handle_paddle(self.ev(), self.g, self.gi), "duplicate")
        self.assertEqual(payments.handle_paddle(self.ev("txn_s1", "sub_1", {"kind": "sub", "ref": "pro", "uid": "u2"}), self.g, self.gi), "granted")
        self.assertEqual(payments.handle_paddle(self.ev("txn_s2", "sub_1", {}), self.g, self.gi), "granted")   # odnowienie bez custom_data
        self.assertEqual(payments.handle_paddle(self.ev("txn_x", None, {}), self.g, self.gi), "unknown")
        self.assertEqual(self.got, [("pass", "u2", "premium"), ("pass", "u2", "pro"), ("pass", "u2", "pro")])
        self.assertEqual(payments.customer("u2", "paddle"), ("ctm_1", ["sub_1"]))
        d = store.get("payments_done")["txn_1"]; self.assertEqual((d["tax"], d["fee"], d["earn"]), ("280", "125", "1094"))
    def test_other_events_logged(self):
        self.assertEqual(payments.handle_paddle(self.ev(et="subscription.canceled"), self.g, self.gi), "logged"); self.assertEqual(self.got, [])

class Off(Base):
    def test_soon_mode(self):
        for k in ("SK", "WH", "PK", "PWH", "PCT"): setattr(payments, k, "")
        self.assertFalse(payments.enabled()); self.assertEqual(payments.mode(), "off")
        c = payments.public_config(); self.assertFalse(c["web"]); self.assertFalse(c["mor"]); self.assertEqual(c["vat"], "soon"); self.assertIsNone(c["paddle"])
        with self.assertRaises(RuntimeError): payments.create_checkout("pass", "premium", "x", "59,99", "u", "e@x", "https://x")
        self.assertIsNone(payments.localized("DE"))
        self.assertEqual(payments.revenue()["on"], False)
    def test_mor_only_with_paddle_keys(self):
        old = (payments.PK, payments.PWH, payments.PCT)
        payments.PK, payments.PWH, payments.PCT = "pdl_sdbx_apikey_x", "pdl_ntfset_x", "test_x"
        os.environ["PAYMENTS_PROVIDER"] = "paddle"
        try:
            self.assertTrue(payments.mor()); self.assertEqual(payments.public_config()["vat"], "mor"); self.assertEqual(payments.mode(), "test")
            os.environ["PAYMENTS_PROVIDER"] = "stripe"; self.assertFalse(payments.mor())
        finally:
            payments.PK, payments.PWH, payments.PCT = old; os.environ.pop("PAYMENTS_PROVIDER", None)

class Revenue(Base):
    def test_paddle_revenue_csv_and_localized(self):
        old = (payments.PK, payments.PWH, payments.PCT, payments._paddle, dict(payments.PPRICE))
        payments.PK, payments.PWH, payments.PCT = "pdl_sdbx_apikey_x", "pdl_ntfset_x", "test_x"; os.environ["PAYMENTS_PROVIDER"] = "paddle"
        calls = []
        def fake(method, path, payload=None, query=None):
            calls.append(path)
            if path == "/transactions":
                return {"data": [{"id": "txn_a", "billed_at": "2026-11-03T10:00:00Z", "currency_code": "EUR", "custom_data": {"kind": "pass", "ref": "premium"},
                                  "details": {"payout_totals": {"currency_code": "PLN", "total": "6400", "tax": "1196", "fee": "370", "earnings": "4834"}}},
                                 {"id": "txn_b", "billed_at": "2026-10-20T10:00:00Z", "currency_code": "PLN", "custom_data": {"kind": "item", "ref": "cla-1"},
                                  "details": {"payout_totals": {"currency_code": "PLN", "total": "1999", "tax": "374", "fee": "150", "earnings": "1475"}}}],
                        "meta": {"pagination": {"has_more": False}}}
            if path == "/pricing-preview":
                return {"data": {"currency_code": "EUR", "address": {"country_code": "DE"}, "details": {"line_items": [{"price": {"id": "pri_p"}, "formatted_totals": {"total": "€14.99"}}]}}}
        payments._paddle = fake; payments._rev.clear(); payments._pv.clear(); payments.PPRICE["pass:premium"] = "pri_p"
        try:
            R = payments.revenue(); self.assertTrue(R["on"]); self.assertEqual(len(R["rows"]), 2)
            M = payments.monthly(R["rows"]); self.assertEqual([m["month"] for m in M], ["2026-11", "2026-10"]); self.assertEqual(M[0]["net"], 4834)
            c = payments.csv_month(R["rows"], "2026-11"); self.assertIn("64,00", c); self.assertIn("11,96", c); self.assertIn("48,34", c); self.assertNotIn("txn_b", c)
            self.assertEqual(payments.localized("DE"), {"currency": "EUR", "country": "DE", "prices": {"premium": "€14.99"}})
        finally:
            payments.PK, payments.PWH, payments.PCT, payments._paddle = old[:4]; payments.PPRICE.clear(); payments.PPRICE.update(old[4]); os.environ.pop("PAYMENTS_PROVIDER", None)
            payments._rev.clear(); payments._pv.clear()

if __name__ == "__main__": unittest.main()
