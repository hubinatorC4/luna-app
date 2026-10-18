"""Trening własnej agentki AI – dostęp według planu (sprawdzany na serwerze, nie tylko w przeglądarce).
Darmowy i Podstawowa: bez treningu. Premium: podstawy i styl. Pro / Ultra: wszystko (także poza i sylwetka).
Tylko opcje, które naprawdę istnieją w aplikacji."""
import plans

# opcja -> minimalny plan
TIERS = {
    "name": "premium", "wake": "premium", "tone": "premium", "length": "premium",   # osobowość
    "ring": "premium", "own": "premium",                                            # styl
    "pose": "pro", "body": "pro",                                                   # pełny trening
}
PRICE = {"premium": "59,99 zł", "pro": "99,99 zł"}

def required(fields, cat=None):
    """Najwyższy plan wymagany przez ustawione pola (stroje i postacie według katalogu)."""
    need = "darmowy"
    def up(p):
        nonlocal need
        if plans.RANK.get(p, 0) > plans.RANK[need]: need = p
    for k, p in TIERS.items():
        v = fields.get(k)
        if v not in (None, "", False, 0): up(p)
    ag = None
    if cat:
        ag = next((a for a in cat.get("agents", []) if a["id"] == fields.get("agent")), None)
        if ag: up(ag.get("plan", "darmowy"))
        base = ag or (cat.get("agents") or [None])[0]
        if base and fields.get("outfit"):
            o = next((o for o in base.get("outfits", []) if o["id"] == fields.get("outfit")), None)
            if o: up(o.get("plan", "darmowy"))
    return need

def check(plan, fields, cat=None):
    need = required(fields if isinstance(fields, dict) else {}, cat)
    if plans.has(plan, need): return None
    return {"error": "plan_required", "required": need, "plan_name": plans.NAMES[need], "price": PRICE.get(need, ""),
            "message": f"Trening własnej agentki AI jest w planie {plans.NAMES[need]}."}

def strip_persona(plan, p):
    """Persona do czatu: pola ponad plan są pomijane (bez błędu – Luna odpowiada jako domyślna agentka)."""
    p = dict(p) if isinstance(p, dict) else {}
    locked = []
    for k in ("name", "tone", "length"):
        if p.get(k) and not plans.has(plan, TIERS[k]): p.pop(k, None); locked.append(k)
    return p, locked

def public():
    return {"tiers": {"darmowy": [], "podstawowa": [], "premium": [k for k, v in TIERS.items() if v == "premium"],
                      "pro": list(TIERS)}, "price": PRICE}
