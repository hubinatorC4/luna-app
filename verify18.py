"""Weryfikacja pełnoletności (18+) TYLKO dla formularzy testerów i castingu – u zewnętrznego dostawcy (Stripe).
Zasada minimalizacji: NIGDY nie zapisujemy skanów dokumentów ani pełnych numerów kart. Zapisujemy wyłącznie wynik
(zweryfikowano 18+: tak/nie), datę, metodę, identyfikator sesji u dostawcy oraz – dla karty – markę, 4 ostatnie cyfry i typ.

a) Dokument: Stripe Identity (VerificationSession, strona hostowana przez Stripe). Datę urodzenia odczytujemy z wyniku
   tylko po to, by policzyć wiek – nie zapisujemy jej.
b) Karta: Stripe Checkout w trybie „setup” (strona hostowana przez Stripe, dane karty nigdy nie trafiają na nasz serwer),
   bez obciążenia. Karta to słabszy dowód (karty debetowe mogą mieć osoby niepełnoletnie) – dlatego zawsze łączymy ją
   z oświadczeniem o dacie urodzenia i oznaczamy jako „karta (słabszy dowód)”. Karty przedpłacone nie są akceptowane.

Flaga: VERIFY18_ENABLED=1 + STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET. Dokument dodatkowo: STRIPE_IDENTITY=1
(Stripe Identity włączone na koncie). Bez kluczy: stan „Weryfikacja wkrótce” – zgłoszenie zapisujemy jako
„oczekuje na weryfikację”, nigdy jako zweryfikowane."""
import datetime, json, os, urllib.parse, urllib.request

def _sk(): return os.getenv("STRIPE_SECRET_KEY", "").strip()
def _wh(): return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
def flag(): return os.getenv("VERIFY18_ENABLED", "") == "1"
def doc_on(): return flag() and bool(_sk() and _wh()) and os.getenv("STRIPE_IDENTITY", "") == "1"
def card_on(): return flag() and bool(_sk() and _wh()) and os.getenv("VERIFY18_CARD", "1") != "0"
def methods(): return {"document": doc_on(), "card": card_on()}
def state(): return "on" if (doc_on() or card_on()) else "soon"

def _req(path, fields=None, method="POST"):
    data = urllib.parse.urlencode(fields or {}).encode() if method == "POST" else None
    url = "https://api.stripe.com/v1/" + path
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + _sk(), "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read())

def start(app_id, kind, method, return_url):
    """Tworzy sesję u dostawcy. Zwraca {"url", "ref", "provider"}. Rzuca RuntimeError, gdy metoda wyłączona."""
    md = {"metadata[luna_kind]": "verify18", "metadata[app_id]": app_id, "metadata[form]": kind}
    if method == "document":
        if not doc_on(): raise RuntimeError("soon")
        s = _req("identity/verification_sessions", {"type": "document", "return_url": return_url,
                 "options[document][allowed_types][0]": "id_card", "options[document][allowed_types][1]": "passport",
                 "options[document][allowed_types][2]": "driving_license", **md})
        return {"url": s["url"], "ref": s["id"], "provider": "stripe_identity"}
    if method == "card":
        if not card_on(): raise RuntimeError("soon")
        sep = "&" if "?" in return_url else "?"
        s = _req("checkout/sessions", {"mode": "setup", "currency": "pln", "payment_method_types[0]": "card", "locale": "auto",
                 "success_url": return_url + sep + "v=card", "cancel_url": return_url + sep + "v=cancel",
                 "client_reference_id": app_id, "setup_intent_data[metadata][luna_kind]": "verify18",
                 "setup_intent_data[metadata][app_id]": app_id, **md})
        return {"url": s["url"], "ref": s["id"], "provider": "stripe_card"}
    raise ValueError("Wybierz metodę weryfikacji.")

def _age(dob):
    try:
        b = datetime.date(int(dob["year"]), int(dob["month"]), int(dob["day"]))
    except Exception: return None
    t = datetime.date.today(); return t.year - b.year - ((t.month, t.day) < (b.month, b.day))

def handle(event):
    """Zdarzenie z webhooka Stripe (podpis sprawdzony wcześniej). Zwraca None, jeśli nie dotyczy weryfikacji 18+,
    albo (app_id, wynik) gdzie wynik = {"status": "verified"|"failed", ...} – bez danych dokumentu/karty poza marką i last4."""
    typ = event.get("type") or ""; o = (event.get("data") or {}).get("object") or {}
    md = o.get("metadata") or {}
    if md.get("luna_kind") != "verify18": return None
    app = md.get("app_id") or o.get("client_reference_id")
    if typ == "identity.verification_session.verified":
        try:
            full = _req("identity/verification_sessions/" + o["id"] + "?expand[]=verified_outputs.dob", method="GET")
            a = _age(((full.get("verified_outputs") or {}).get("dob")) or {})
        except Exception: a = None
        if a is None: return app, {"status": "failed", "method": "document", "provider": "stripe_identity", "ref": o.get("id"), "reason": "no_dob"}
        return app, {"status": "verified" if a >= 18 else "failed", "method": "document", "provider": "stripe_identity", "ref": o.get("id"),
                     "reason": "" if a >= 18 else "underage"}
    if typ in ("identity.verification_session.requires_input", "identity.verification_session.canceled"):
        return app, {"status": "failed", "method": "document", "provider": "stripe_identity", "ref": o.get("id"),
                     "reason": ((o.get("last_error") or {}).get("code") or typ.rsplit(".", 1)[-1])[:40]}
    if typ == "checkout.session.completed" and o.get("mode") == "setup":
        card = {}
        try:
            si = _req("setup_intents/" + o["setup_intent"] + "?expand[]=payment_method", method="GET")
            c = ((si.get("payment_method") or {}).get("card")) or {}
            card = {"brand": str(c.get("brand", ""))[:20], "last4": str(c.get("last4", ""))[-4:], "funding": str(c.get("funding", ""))[:10]}
            # karta służyła tylko do sprawdzenia – odłączamy metodę płatności, nic nie zostaje zapisane u nas ani w Stripe
            try: _req("payment_methods/" + si["payment_method"]["id"] + "/detach")
            except Exception: pass
        except Exception: pass
        ok = bool(card.get("last4")) and card.get("funding") != "prepaid"
        return app, {"status": "verified" if ok else "failed", "method": "card", "provider": "stripe_card", "ref": o.get("id"),
                     "card": card, "weak": True, "reason": "" if ok else ("prepaid" if card.get("funding") == "prepaid" else "card_error")}
    return None

ENV_NEEDED = ["VERIFY18_ENABLED=1", "STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY (only if Stripe Elements is used later)",
              "STRIPE_WEBHOOK_SECRET (+ webhook events: identity.verification_session.verified, identity.verification_session.requires_input, identity.verification_session.canceled, checkout.session.completed)",
              "STRIPE_IDENTITY=1 (after activating Stripe Identity in the Stripe dashboard)", "VERIFY18_CARD=0 to disable the card method (optional)",
              "TURNSTILE_SITEKEY + TURNSTILE_SECRET (Cloudflare Turnstile)"]
