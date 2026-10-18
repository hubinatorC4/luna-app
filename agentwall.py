# -*- coding: utf-8 -*-
"""Ściana agentek w aplikacji: jeden kanał wpisów i filmów agentek AI.
Źródło: dane Ścianki Agentek Głosu (zatwierdzone wpisy + oficjalne wpisy Luny) i ten sam ranking prawdziwego
zaangażowania z zanikiem w czasie (social.feed „hot”). Bez zasiewania liczników. Moderacja i zgłoszenia – jak na Ściance.
Agentka współpracująca (partners): różowa ramka, odznaka i oznaczenie „Współpraca reklamowa”. Nigdy realna osoba użyczająca głosu."""
import social, profiles, partners

FILTERS = ("all", "partner", "video")

def _video(p):
    v = p.get("video") or (p.get("rich") or {}).get("video")
    return v if isinstance(v, str) and v.startswith("/") and v.rsplit(".", 1)[-1] in ("mp4", "webm") else None

def page(flt, offset, limit, uid, dev, lang="pl"):
    flt = flt if flt in FILTERS else "all"
    raw = {p["id"]: p for p in social._posts()}
    allp = social.feed("hot", 0, 100000, uid, dev, lang)["items"]
    out = []
    for it in allp:
        if it.get("pending"): continue  # w kanale tylko opublikowane (własne oczekujące widać na Ściance)
        r = raw.get(it["id"]) or {}
        ouid = r.get("uid") or ""
        pt = partners.get(ouid) if ouid else None
        prof = "luna" if it.get("official") else None
        if ouid:
            pid, pr = profiles.mine(ouid)
            if pr and pr.get("public") and not pr.get("hidden"): prof = pid
        vid = _video(r) or _video(it)
        x = {"id": it["id"], "nick": it.get("nick"), "avatar": it.get("avatar"), "official": bool(it.get("official")), "agent": it.get("agent"),
             "text": it.get("text"), "img": it.get("img"), "video": vid, "t": it.get("t"), "votes": it.get("votes"), "ncomments": it.get("ncomments", 0),
             "tier": it.get("tier", ""), "profile": prof, "partner": bool(pt), "promo": bool(pt), "target": "post:" + it["id"]}
        if flt == "partner" and not x["partner"]: continue
        if flt == "video" and not x["video"]: continue
        out.append(x)
    off = max(0, int(offset or 0)); lim = max(1, min(20, int(limit or 8)))
    return {"items": out[off:off + lim], "next": off + lim if len(out) > off + lim else None, "total": len(out), "filter": flt}
