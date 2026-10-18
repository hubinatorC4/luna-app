# -*- coding: utf-8 -*-
"""„Agentka współpracująca”: status nadawany WYŁĄCZNIE ręcznie przez moderatora (po zgodzie twórcy – opt-in).
Klucz = konto właściciela (prywatne, nigdy nie wychodzi na zewnątrz). Publicznie: tylko flaga i lista prawdziwych kampanii/marek.
Nigdy dla oficjalnej Luny ani realnej osoby użyczającej głosu – status dotyczy tylko agentek AI użytkowników."""
import re, threading, time
import store, social

_lock = threading.Lock()
MAX_CAMPAIGNS, CAMP_LEN = 8, 60
PRIV_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|https?://|www\.|(?:\+?\d[\s-]?){9,}", re.I)

def _all(): return store.get("agent_partners", {}) or {}

def get(uid):
    if not uid: return None
    p = _all().get(uid)
    return {"campaigns": list(p.get("campaigns", []))} if p and p.get("on") else None

def is_partner(uid): return bool(get(uid))

def _camps(L):
    out = []
    for c in (L if isinstance(L, list) else [])[:MAX_CAMPAIGNS]:
        c = re.sub(r"[<>\x00-\x1f]", "", str(c or "")).strip()[:CAMP_LEN]
        if not c: continue
        if PRIV_RE.search(c): raise ValueError("Kampanie: bez e-maili, linków i numerów telefonu.")
        out.append(social.check_text(c, CAMP_LEN))
    return out

def admin_set(uid, on, optin=False, campaigns=None, note=""):
    """Włącz/wyłącz status. Włączenie wymaga potwierdzonej zgody twórcy (optin=True)."""
    if not uid: raise KeyError("Nie znaleziono agentki.")
    with _lock:
        A = _all(); r = A.get(uid) or {}
        if on:
            if optin is not True: raise ValueError("Najpierw potwierdź zgodę twórcy (opt-in).")
            r.update(on=True, optin_at=r.get("optin_at") or int(time.time()), campaigns=_camps(campaigns if campaigns is not None else r.get("campaigns", [])),
                     note=str(note or r.get("note", ""))[:200], t=int(time.time()))
        else:
            r.update(on=False, t=int(time.time()))
        A[uid] = r; store.put("agent_partners", A)
    return {"on": bool(r.get("on")), "campaigns": r.get("campaigns", [])}

def admin_list(lookup):
    """Lista dla panelu: imię agentki i identyfikatory profilu/bitwy (bez danych konta) + stan."""
    return [dict(lookup(u), on=bool(v.get("on")), campaigns=v.get("campaigns", []), optin_at=v.get("optin_at", 0)) for u, v in _all().items()]
