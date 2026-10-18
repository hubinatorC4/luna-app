"""Płatności WWW – warstwa niezależna od dostawcy (v1.7.0).

PAYMENTS_PROVIDER=paddle | stripe
  • paddle (zalecane): Paddle Billing jako Merchant of Record (MoR) – Paddle jest sprzedawcą wobec kupującego,
    nalicza i odprowadza VAT/podatek od sprzedaży w kraju kupującego i wypłaca nam saldo na jedno konto.
  • stripe: Stripe Checkout (+ opcjonalnie Stripe Tax). Tu sprzedawcą jest właściciel – VAT rozlicza sam (z księgowym).
Bez kompletu kluczy płatności są WYŁĄCZONE: przyciski pokazują „płatności startują wkrótce”, nic nie udaje sukcesu.
Plan/pozycję przyznaje WYŁĄCZNIE webhook z poprawnym podpisem, idempotentnie (po id zdarzenia/transakcji), z wpisem w dzienniku audytu.
Nie przechowujemy danych kart – płatność odbywa się w kasie dostawcy. Numer konta bankowego jest tylko w panelu dostawcy.
W aplikacji Android (TWA, Google Play) płatności WWW są wyłączone – decyzja o Google Play Billing należy do właściciela."""
import datetime, hashlib, hmac, json, os, re, threading, time, urllib.parse, urllib.request
import store

def _e(k): return os.getenv(k, "").strip()
# --- Stripe ---
SK = _e("STRIPE_SECRET_KEY"); WH = _e("STRIPE_WEBHOOK_SECRET")
P24 = _e("STRIPE_ENABLE_P24") == "1"
TAX = _e("STRIPE_TAX") == "1"            # Stripe Tax: ceny brutto (tax_behavior=inclusive) – nadal sprzedawcą jest właściciel
# --- Paddle ---
PK = _e("PADDLE_API_KEY"); PWH = _e("PADDLE_WEBHOOK_SECRET"); PCT = _e("PADDLE_CLIENT_TOKEN")
def penv(): return _e("PADDLE_ENV") or ("sandbox" if PK.startswith("pdl_sdbx") or PCT.startswith("test_") else "live")
def papi(): return "https://sandbox-api.paddle.com" if penv() == "sandbox" else "https://api.paddle.com"
# Opcjonalne ceny z katalogu Paddle (z lokalizacją cen per kraj ustawioną w panelu Paddle). Bez nich – cena PLN z panelu Luny.
PPRICE = {"pass:premium": _e("PADDLE_PRICE_PREMIUM"), "pass:pro": _e("PADDLE_PRICE_PRO"),
          "sub:premium": _e("PADDLE_PRICE_PREMIUM_SUB"), "sub:pro": _e("PADDLE_PRICE_PRO_SUB")}
SPRICE = {"sub:premium": _e("STRIPE_PRICE_PREMIUM_SUB"), "sub:pro": _e("STRIPE_PRICE_PRO_SUB")}

def provider():
    p = _e("PAYMENTS_PROVIDER").lower()
    if p in ("paddle", "stripe"): return p
    return "paddle" if PK else ("stripe" if SK else "paddle")
def _keys_ok(p=None):
    p = p or provider()
    return bool(PK and PWH and PCT) if p == "paddle" else bool(SK and WH)
def enabled(): return _keys_ok()
def mode():
    if not enabled(): return "off"
    if provider() == "paddle": return "test" if penv() == "sandbox" else "live"
    return "test" if SK.startswith("sk_test_") else "live"
def mor(): return enabled() and provider() == "paddle"   # tylko wtedy wolno mówić „VAT rozlicza partner płatniczy”
def methods():
    if provider() == "paddle": return ["BLIK", "karta / card", "PayPal", "Apple Pay / Google Pay"]
    return ["BLIK", "karta / card"] + (["Przelewy24"] if P24 else [])
def public_config():
    """Bezpieczne dla przeglądarki (bez sekretów; token klienta Paddle jest publiczny z założenia)."""
    p = provider(); on = enabled()
    return {"web": on, "provider": p if on else None, "mor": mor(), "methods": methods(), "subs": on,
            "vat": "mor" if mor() else ("gross" if on else "soon"),
            "paddle": {"token": PCT, "env": penv()} if on and p == "paddle" else None}

def grosze(pln): return int(round(float(str(pln).replace(",", ".")) * 100))
_lock = threading.Lock()
ON_PAID = None        # (ref, amount, currency) – zakup stroju (statystyki)
ON_USER_PAID = None   # (uid) – każdy opłacony zakup (np. Poleć Lunę)
AUDIT = None          # (action, detail) – dziennik audytu (security.audit)

def _audit(action, detail=""):
    try:
        if AUDIT: AUDIT(action, detail)
    except Exception: pass

def _http(method, url, headers, body=None, timeout=20):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read() or b"{}")

def _stripe(method, path, fields=None, query=None):
    q = ("?" + urllib.parse.urlencode(query, doseq=True)) if query else ""
    body = urllib.parse.urlencode(fields).encode() if fields is not None else None
    return _http(method, "https://api.stripe.com/v1" + path + q, {"Authorization": "Bearer " + SK, "Content-Type": "application/x-www-form-urlencoded"}, body)

def _paddle(method, path, payload=None, query=None):
    q = ("?" + urllib.parse.urlencode(query)) if query else ""
    body = json.dumps(payload).encode() if payload is not None else None
    return _http(method, papi() + path + q, {"Authorization": "Bearer " + PK, "Content-Type": "application/json", "Paddle-Version": "1"}, body)

# ---------------- kasa ----------------
def create_checkout(kind, ref, name, pln, uid, email, base_url, sub=False, cust=None):
    """kind: pass | item. sub=True – subskrypcja miesięczna (karta/PayPal; BLIK tylko płatności jednorazowe)."""
    if not enabled(): raise RuntimeError("soon")
    amount = grosze(pln)
    if amount < 200: raise ValueError("Kwota za niska (min. 2 zł).")
    sub = bool(sub and kind == "pass")
    md = {"kind": "sub" if sub else kind, "ref": ref, "uid": uid}
    if provider() == "paddle":
        pid = PPRICE.get(("sub:" if sub else "pass:") + ref) if kind == "pass" else ""
        item = {"quantity": 1, "price_id": pid} if pid else {"quantity": 1, "price": {
            "description": f"Luna {md['kind']}:{ref}"[:500], "name": name[:150],
            "billing_cycle": {"interval": "month", "frequency": 1} if sub else None,
            "tax_mode": "internal",   # cena zawiera podatek
            "unit_price": {"amount": str(amount), "currency_code": "PLN"},
            "product": {"name": name[:150], "tax_category": "standard"}}}
        body = {"items": [item], "custom_data": md, "currency_code": "PLN", "collection_mode": "automatic",
                "checkout": {"url": f"{base_url}/kasa.html"}}
        if cust: body["customer_id"] = cust
        t = _paddle("POST", "/transactions", body)["data"]
        return {"id": t["id"], "url": f"{base_url}/kasa.html?_ptxn={t['id']}", "provider": "paddle"}
    f = {"mode": "subscription" if sub else "payment",
         "success_url": f"{base_url}/app?platnosc=ok&session_id={{CHECKOUT_SESSION_ID}}", "cancel_url": f"{base_url}/app?platnosc=anulowano",
         "client_reference_id": uid, "locale": "auto", "line_items[0][quantity]": "1"}
    if cust: f["customer"] = cust
    else: f["customer_email"] = email
    spid = SPRICE.get("sub:" + ref) if sub else ""
    if spid: f["line_items[0][price]"] = spid
    else:
        f.update({"line_items[0][price_data][currency]": "pln", "line_items[0][price_data][unit_amount]": str(amount),
                  "line_items[0][price_data][product_data][name]": name[:120]})
        if sub: f["line_items[0][price_data][recurring][interval]"] = "month"
        if TAX: f["line_items[0][price_data][tax_behavior]"] = "inclusive"
    for k, v in md.items(): f[f"metadata[{k}]"] = v
    f["metadata[immediate_delivery_consent]"] = "1"
    tgt = "subscription_data" if sub else "payment_intent_data"
    for k, v in md.items(): f[f"{tgt}[metadata][{k}]"] = v
    if not sub:
        f["payment_intent_data[receipt_email]"] = email
        ms = ["blik", "card"] + (["p24"] if P24 else [])
    else: ms = ["card"]
    for i, m in enumerate(ms): f[f"payment_method_types[{i}]"] = m
    if TAX: f["automatic_tax[enabled]"] = "true"; f["billing_address_collection"] = "required"
    s = _stripe("POST", "/checkout/sessions", f)
    return {"id": s["id"], "url": s["url"], "provider": "stripe"}

def portal(cust, base_url, subs=None):
    """Link do portalu klienta (anulowanie, zmiana metody płatności, faktury)."""
    if not enabled() or not cust: raise RuntimeError("soon")
    if provider() == "paddle":
        d = _paddle("POST", f"/customers/{cust}/portal-sessions", {"subscription_ids": list(subs or [])[:25]})["data"]
        return d["urls"]["general"]["overview"]
    return _stripe("POST", "/billing_portal/sessions", {"customer": cust, "return_url": base_url + "/app"})["url"]

_pv = {}
def localized(ip_or_country, refs=("premium", "pro")):
    """Dokładne ceny w walucie kraju – WYŁĄCZNIE od dostawcy (Paddle pricing preview z cenami katalogowymi).
    Gdy nie ma kluczy/katalogu – None (pokazujemy wtedy samo PLN, bez wymyślonych kursów)."""
    if not (enabled() and provider() == "paddle"): return None
    ids = {r: PPRICE.get("pass:" + r) for r in refs if PPRICE.get("pass:" + r)}
    if not ids or not ip_or_country: return None
    key = (ip_or_country, tuple(sorted(ids.items())))
    c = _pv.get(key)
    if c and time.time() - c[0] < 3600: return c[1]
    body = {"items": [{"price_id": v, "quantity": 1} for v in ids.values()]}
    if re.fullmatch(r"[A-Z]{2}", ip_or_country): body["address"] = {"country_code": ip_or_country}
    else: body["customer_ip_address"] = ip_or_country
    try: d = _paddle("POST", "/pricing-preview", body)["data"]
    except Exception: return None
    rev = {v: k for k, v in ids.items()}; out = {"currency": d.get("currency_code"), "country": (d.get("address") or {}).get("country_code"), "prices": {}}
    for li in (d.get("details") or {}).get("line_items", []):
        r = rev.get((li.get("price") or {}).get("id"))
        if r: out["prices"][r] = (li.get("formatted_totals") or {}).get("total")
    _pv[key] = (time.time(), out)
    if len(_pv) > 500: _pv.clear()
    return out

# ---------------- webhooki ----------------
def verify(payload, sig_header, secret=None, tolerance=300, now=None):
    """Stripe-Signature (t=…,v1=…): HMAC-SHA256(secret, f"{t}.{payload}")."""
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

def verify_paddle(payload, sig_header, secret=None, tolerance=300, now=None):
    """Paddle-Signature (ts=…;h1=…): HMAC-SHA256(secret, f"{ts}:{surowe body}")."""
    secret = secret if secret is not None else PWH
    if not secret or not sig_header: return False
    parts = {}
    for kv in sig_header.split(";"):
        k, _, v = kv.strip().partition("="); parts.setdefault(k, []).append(v)
    try: ts = int(parts.get("ts", ["0"])[0])
    except ValueError: return False
    if abs((now or time.time()) - ts) > tolerance: return False
    exp = hmac.new(secret.encode(), f"{ts}:".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(exp, v) for v in parts.get("h1", []))

def _cust_set(uid, prov, cust, sub=None):
    if not uid or not cust: return
    with _lock:
        C = store.get("pay_customers", {}) or {}
        c = C.get(uid) or {}
        c[prov] = cust
        if sub: c.setdefault("subs_" + prov, []); c["subs_" + prov] = ([sub] + [s for s in c["subs_" + prov] if s != sub])[:5]
        C[uid] = c; store.put("pay_customers", C)
def customer(uid, prov=None):
    c = (store.get("pay_customers", {}) or {}).get(uid) or {}
    p = prov or provider(); return c.get(p), c.get("subs_" + p, [])

def _grant(key, prov, kind, ref, uid, amount, currency, grant_pass, grant_item, extra=None):
    """Wspólne, idempotentne przyznanie. key – id transakcji/faktury/sesji u dostawcy."""
    with _lock:
        done = store.get("payments_done", {}) or {}
        if key in done: return "duplicate"
        if kind in ("pass", "sub"):
            if ref not in ("premium", "pro"): return "unknown"
            grant_pass(uid, ref, 1)
        elif kind == "item": grant_item(uid, ref)
        else: return "unknown"
        done[key] = {"t": int(time.time()), "prov": prov, "kind": kind, "ref": ref, "uid": uid, "amount": amount, "currency": currency, **(extra or {})}
        if len(done) > 20000:
            for k in sorted(done, key=lambda k: done[k].get("t", 0))[:2000]: done.pop(k, None)
        store.put("payments_done", done)
    _audit(f"pay {prov} {kind}", f"{ref} uid:{str(uid)[:6]} {amount} {currency} {key[:24]}")
    try:
        if kind == "item" and ON_PAID: ON_PAID(ref, amount, currency)
    except Exception: pass
    try:
        if ON_USER_PAID and uid: ON_USER_PAID(uid)
    except Exception: pass
    return "granted"

def handle(event, grant_pass, grant_item):
    """Stripe. Jednorazowo: checkout.session.completed / async_payment_succeeded (paid).
    Subskrypcja: invoice.paid (pierwsza i każda kolejna) – przedłuża o 30 dni. Anulowanie: dostęp trwa do końca opłaconego okresu."""
    typ = event.get("type"); s = (event.get("data") or {}).get("object") or {}
    if typ in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        md = s.get("metadata") or {}; uid = md.get("uid") or s.get("client_reference_id")
        if s.get("customer"): _cust_set(uid, "stripe", s.get("customer"), s.get("subscription"))
        if s.get("mode") == "subscription" or md.get("kind") == "sub": return "sub_started"   # dostęp przyznaje invoice.paid
        if s.get("payment_status") != "paid": return "pending"
        return _grant(s.get("id"), "stripe", md.get("kind"), md.get("ref"), uid, s.get("amount_total"), s.get("currency"), grant_pass, grant_item)
    if typ == "invoice.paid":
        md = ((s.get("parent") or {}).get("subscription_details") or {}).get("metadata") or (s.get("subscription_details") or {}).get("metadata") or {}
        if not md.get("uid"):
            try: md = (s.get("lines", {}).get("data") or [{}])[0].get("metadata") or {}
            except Exception: md = {}
        ref = md.get("ref")
        try:   # po zmianie planu w portalu – plan z ceny katalogowej
            pr = (s.get("lines", {}).get("data") or [{}])[0].get("pricing", {}).get("price_details", {}).get("price") or (s.get("lines", {}).get("data") or [{}])[0].get("price", {}).get("id")
            for k, v in SPRICE.items():
                if v and v == pr: ref = k.split(":")[1]
        except Exception: pass
        if not md.get("uid") or (s.get("amount_paid") or 0) <= 0: return "ignored"
        return _grant(s.get("id"), "stripe", "sub", ref, md.get("uid"), s.get("amount_paid"), s.get("currency"), grant_pass, grant_item)
    if typ in ("charge.refunded", "charge.dispute.created"):
        _audit("pay stripe " + typ.split(".")[1], f"{s.get('id', '')[:24]} {s.get('amount_refunded') or s.get('amount')} {s.get('currency')}")
        return "logged"
    if typ == "customer.subscription.deleted":
        _audit("pay stripe sub_end", str(s.get("id", ""))[:30]); return "logged"
    return "ignored"

def handle_paddle(event, grant_pass, grant_item):
    """Paddle. transaction.completed = płatność w pełni pobrana (także BLIK z odroczonym pobraniem i odnowienia subskrypcji)."""
    typ = event.get("event_type"); d = event.get("data") or {}
    if typ == "transaction.completed":
        md = d.get("custom_data") or {}
        if not md.get("uid") and d.get("subscription_id"):   # odnowienie – custom_data z subskrypcji
            md = (store.get("pay_subs", {}) or {}).get(d["subscription_id"]) or {}
        tot = (d.get("details") or {}).get("totals") or {}
        ref = md.get("ref")
        try:
            pid = d["items"][0]["price"]["id"]
            for k, v in PPRICE.items():
                if v and v == pid: ref = k.split(":")[1]
        except Exception: pass
        if d.get("customer_id"): _cust_set(md.get("uid"), "paddle", d["customer_id"], d.get("subscription_id"))
        if d.get("subscription_id") and md.get("uid"):
            with _lock:
                S = store.get("pay_subs", {}) or {}; S[d["subscription_id"]] = {"uid": md["uid"], "ref": ref, "kind": "sub"}; store.put("pay_subs", S)
        if not md.get("uid"): return "unknown"
        kind = "sub" if d.get("subscription_id") else md.get("kind")
        return _grant(d.get("id"), "paddle", kind, ref, md.get("uid"), tot.get("total"), d.get("currency_code"), grant_pass, grant_item,
                      {"tax": tot.get("tax"), "fee": tot.get("fee"), "earn": tot.get("earnings")})
    if typ in ("subscription.canceled", "adjustment.created", "adjustment.updated", "transaction.payment_failed"):
        _audit("pay paddle " + typ, str(d.get("id", ""))[:30] + " " + str(d.get("action") or d.get("status") or "")[:20]); return "logged"
    return "ignored"

# ---------------- przychody (panel moderatora) – wyłącznie dane od dostawcy ----------------
_rev = {}
def _fmt(minor, cur):
    try: return int(minor)
    except Exception: return 0
def revenue(days=400):
    """Lista transakcji z API dostawcy. Pola w jednostkach groszowych waluty wypłaty (Paddle: payout_totals) lub transakcji."""
    if not enabled(): return {"on": False, "provider": provider(), "rows": []}
    key = (provider(), days); c = _rev.get(key)
    if c and time.time() - c[0] < 300: return c[1]
    rows = []; since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    if provider() == "paddle":
        q = {"status": "completed", "per_page": "100", "order_by": "created_at[DESC]", "created_at[GTE]": since.strftime("%Y-%m-%dT%H:%M:%SZ")}
        path = "/transactions"
        for _ in range(30):
            r = _paddle("GET", path, query=q)
            for t in r.get("data", []):
                det = t.get("details") or {}; pt = det.get("payout_totals") or det.get("totals") or {}
                rows.append({"id": t["id"], "t": t.get("billed_at") or t.get("created_at"), "cur": pt.get("currency_code") or t.get("currency_code"),
                             "gross": _fmt(pt.get("total"), 0), "tax": _fmt(pt.get("tax"), 0), "fee": _fmt(pt.get("fee"), 0), "net": _fmt(pt.get("earnings"), 0),
                             "what": ((t.get("custom_data") or {}).get("kind", "") + ":" + (t.get("custom_data") or {}).get("ref", "")).strip(":"), "sub": bool(t.get("subscription_id"))})
            nxt = ((r.get("meta") or {}).get("pagination") or {}).get("next")
            if not nxt or not ((r.get("meta") or {}).get("pagination") or {}).get("has_more"): break
            pq = urllib.parse.urlparse(nxt); path = pq.path; q = dict(urllib.parse.parse_qsl(pq.query))
    else:
        q = {"limit": "100", "created[gte]": str(int(since.timestamp()))}
        for _ in range(30):
            r = _stripe("GET", "/balance_transactions", query=q)
            for b in r.get("data", []):
                if b.get("type") not in ("charge", "payment", "refund", "payment_refund", "adjustment"): continue
                rows.append({"id": b["id"], "t": datetime.datetime.utcfromtimestamp(b["created"]).strftime("%Y-%m-%dT%H:%M:%SZ"), "cur": b.get("currency", "").upper(),
                             "gross": b.get("amount", 0), "tax": None, "fee": b.get("fee", 0), "net": b.get("net", 0), "what": b.get("type"), "sub": False})
            if not r.get("has_more") or not r.get("data"): break
            q["starting_after"] = r["data"][-1]["id"]
    out = {"on": True, "provider": provider(), "mode": mode(), "mor": mor(), "rows": rows}
    _rev[key] = (time.time(), out); return out

def monthly(rows):
    M = {}
    for r in rows:
        k = (str(r["t"])[:7], r["cur"]); m = M.setdefault(k, {"month": k[0], "cur": k[1], "n": 0, "gross": 0, "tax": 0, "fee": 0, "net": 0, "tax_known": True})
        m["n"] += 1; m["gross"] += r["gross"] or 0; m["fee"] += r["fee"] or 0; m["net"] += r["net"] or 0
        if r["tax"] is None: m["tax_known"] = False
        else: m["tax"] += r["tax"]
    return sorted(M.values(), key=lambda m: (m["month"], m["cur"]), reverse=True)

def csv_month(rows, month):
    """CSV do księgowości: miesiąc, waluta, brutto, opłaty pośrednika, VAT rozliczony przez pośrednika, wypłata netto."""
    import csv, io
    b = io.StringIO(); w = csv.writer(b, delimiter=";")
    w.writerow(["data", "id_transakcji", "co", "waluta", "brutto", "oplaty_posrednika", "vat_rozliczony_przez_posrednika", "netto_do_wyplaty", "dostawca"])
    z = lambda v: "" if v is None else f"{v / 100:.2f}".replace(".", ",")
    tot = {}
    for r in rows:
        if not str(r["t"]).startswith(month): continue
        w.writerow([str(r["t"])[:19], r["id"], r["what"], r["cur"], z(r["gross"]), z(r["fee"]), z(r["tax"]) if provider() == "paddle" else "n/d (sprzedawcą jest właściciel)", z(r["net"]), provider()])
        t = tot.setdefault(r["cur"], [0, 0, 0, 0]); t[0] += r["gross"] or 0; t[1] += r["fee"] or 0; t[2] += r["tax"] or 0; t[3] += r["net"] or 0
    for cur, t in tot.items(): w.writerow(["SUMA " + month, "", "", cur, z(t[0]), z(t[1]), z(t[2]) if provider() == "paddle" else "", z(t[3]), provider()])
    return "\ufeff" + b.getvalue()
