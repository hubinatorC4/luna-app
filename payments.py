"""Płatności WWW: Stripe Checkout (tryb payment, jednorazowo, PLN) – BLIK + karta (+ opcjonalnie Przelewy24).
Bez STRIPE_SECRET_KEY przyciski pokazują „wkrótce”. Dostęp/pozycję przyznaje WYŁĄCZNIE webhook z poprawnym podpisem (idempotentnie).
W aplikacji Android (TWA) Stripe jest wyłączony – tam płatności przez Google Play Billing (polityka Google Play)."""
import hashlib, hmac, json, os, threading, time, urllib.parse, urllib.request
import store

SK = os.getenv("STRIPE_SECRET_KEY", "").strip()
WH = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
P24 = os.getenv("STRIPE_ENABLE_P24", "") == "1"
TAX = os.getenv("STRIPE_TAX", "") == "1"  # Stripe Tax: ceny brutto (tax_behavior=inclusive)
_lock = threading.Lock()

def enabled(): return bool(SK and WH)
def mode(): return "test" if SK.startswith("sk_test_") else ("live" if SK else "off")

def grosze(pln):
    return int(round(float(str(pln).replace(",", ".")) * 100))

def create_checkout(kind, ref, name, pln, uid, email, base_url):
    if not enabled(): raise RuntimeError("Płatności – wkrótce.")
    amount = grosze(pln)
    if amount < 200: raise ValueError("Kwota za niska dla BLIK (min. 2 zł).")
    methods = ["blik", "card"] + (["p24"] if P24 else [])
    f = {"mode": "payment", "success_url": f"{base_url}/app?platnosc=ok&session_id={{CHECKOUT_SESSION_ID}}", "cancel_url": f"{base_url}/app?platnosc=anulowano",
         "client_reference_id": uid, "customer_email": email, "locale": "auto", "payment_intent_data[receipt_email]": email,
         "line_items[0][quantity]": "1", "line_items[0][price_data][currency]": "pln", "line_items[0][price_data][unit_amount]": str(amount),
         "line_items[0][price_data][product_data][name]": name[:120],
         "metadata[kind]": kind, "metadata[ref]": ref, "metadata[uid]": uid, "metadata[immediate_delivery_consent]": "1",
         "payment_intent_data[metadata][kind]": kind, "payment_intent_data[metadata][ref]": ref, "payment_intent_data[metadata][uid]": uid}
    for i, m in enumerate(methods): f[f"payment_method_types[{i}]"] = m
    if TAX:
        f["automatic_tax[enabled]"] = "true"; f["billing_address_collection"] = "required"
        f["line_items[0][price_data][tax_behavior]"] = "inclusive"
    req = urllib.request.Request("https://api.stripe.com/v1/checkout/sessions", data=urllib.parse.urlencode(f).encode(),
                                 headers={"Authorization": "Bearer " + SK, "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r: s = json.loads(r.read())
    return {"id": s["id"], "url": s["url"]}

def verify(payload, sig_header, secret=None, tolerance=300, now=None):
    """Weryfikacja podpisu Stripe-Signature (t=…,v1=…): HMAC-SHA256(secret, f"{t}.{payload}")."""
    secret = secret if secret is not None else WH
    if not secret or not sig_header: return False
    parts = {}
    for kv in sig_header.split(","):
        k, _, v = kv.strip().partition("="); parts.setdefault(k, []).append(v)
    try: t = int(parts.get("t", ["0"])[0])
    except ValueError: return False
    if abs((now or time.time()) - t) > tolerance: return False
    exp = hmac.new(secret.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(exp, v) for v in parts.get("v1", []))

ON_PAID = None
ON_USER_PAID = None   # (uid) – każdy opłacony zakup (plan lub strój), np. nagroda Poleć Lunę
def handle(event, grant_pass, grant_item):
    """Obsługa zdarzenia. Zwraca opis wyniku. Idempotentnie po id sesji Checkout."""
    typ = event.get("type"); s = (event.get("data") or {}).get("object") or {}
    if typ not in ("checkout.session.completed", "checkout.session.async_payment_succeeded"): return "ignored"
    if s.get("payment_status") != "paid": return "pending"
    sid = s.get("id"); md = s.get("metadata") or {}
    with _lock:
        done = store.get("payments_done", {}) or {}
        if sid in done: return "duplicate"
        kind, ref, uid = md.get("kind"), md.get("ref"), md.get("uid") or s.get("client_reference_id")
        if kind == "pass": grant_pass(uid, ref, 1)
        elif kind == "item": grant_item(uid, ref)
        else: return "unknown"
        done[sid] = {"t": int(time.time()), "kind": kind, "ref": ref, "uid": uid, "amount": s.get("amount_total"), "currency": s.get("currency")}
        store.put("payments_done", done)
    try:
        if kind == "item" and ON_PAID: ON_PAID(ref, s.get("amount_total"), s.get("currency"))
    except Exception: pass
    try:
        if ON_USER_PAID and uid: ON_USER_PAID(uid)
    except Exception: pass
    return "granted"
