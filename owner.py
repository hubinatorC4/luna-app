"""Raporty właściciela (tylko z prawdziwych, zliczonych danych; brak danych = 0). Używane wyłącznie przez API z tokenem administratora.
Bez etykiet ani rankingów opartych na tym, jak odsłaniające są stroje."""
import time
import store, stats, butik, social, official
def _sum(S, key): return sum(d.get(key, 0) for d in S.values())
def band(pln):
    if pln is None: return "brak ceny"
    return "do 9,99 zł" if pln < 10 else "10–29,99 zł" if pln < 30 else "30–99,99 zł" if pln < 100 else "100–199,99 zł" if pln < 200 else "200–399,99 zł"
def _payments(days):
    lim = time.time() - days * 86400
    return [p for p in (store.get("payments_done", {}) or {}).values() if p.get("t", 0) >= lim]
def butik_report(days):
    S = stats.series(days); P = _payments(days); V = social._votes()
    rows = []
    for i in butik._load():
        if i.get("status") == "hidden": continue
        k = "item:" + i["id"]; buys = [p for p in P if p.get("kind") == "item" and p.get("ref") == i["id"]]
        rev = round(sum((p.get("amount") or 0) for p in buys if (p.get("currency") or "pln").lower() == "pln") / 100, 2)
        c = social.counts(k, None, V)
        rows.append({"id": i["id"], "name": i.get("name"), "category": i.get("category") or "—", "collection": i.get("collection") or "—", "line": i.get("line") or "—",
                     "rarity": i.get("rarity") or "—", "tier": i.get("tier") or "—", "price_pln": (i.get("price") or {}).get("pln"), "band": band((i.get("price") or {}).get("pln")),
                     "status": butik.eff_status(i), "views": _sum(S, k + ":v"), "unique": _sum(S, k + ":u"), "likes": c["up"], "dislikes": c["down"],
                     "likes_period": _sum(S, k + ":like"), "dislikes_period": _sum(S, k + ":dislike"), "cart": _sum(S, k + ":cart"), "shares": _sum(S, k + ":share"), "purchases": len(buys), "revenue_pln": rev})
    def agg(field):
        out = {}
        for r in rows:
            a = out.setdefault(r[field], {"key": r[field], "items": 0, "views": 0, "likes": 0, "dislikes": 0, "cart": 0, "purchases": 0, "revenue_pln": 0})
            a["items"] += 1
            for m in ("views", "likes", "dislikes", "cart", "purchases", "revenue_pln"): a[m] = round(a[m] + r[m], 2)
        return sorted(out.values(), key=lambda a: (-a["views"], -a["purchases"], str(a["key"])))
    top = {m: [r for r in sorted(rows, key=lambda r: -r[m]) if r[m] > 0][:10] for m in ("views", "likes", "cart", "purchases", "revenue_pln")}
    passes = [p for p in P if p.get("kind") == "pass"]
    return {"items": rows, "by": {f: agg(f) for f in ("category", "collection", "line", "rarity", "tier", "band")}, "top": top,
            "totals": {"views": sum(r["views"] for r in rows), "cart": sum(r["cart"] for r in rows), "purchases": sum(r["purchases"] for r in rows),
                       "revenue_pln": round(sum(r["revenue_pln"] for r in rows), 2), "pass_purchases": len(passes),
                       "pass_revenue_pln": round(sum((p.get("amount") or 0) for p in passes if (p.get("currency") or "pln").lower() == "pln") / 100, 2)}}
def site_report(days):
    S = stats.series(days); keys = {}
    for d in S.values():
        for k, n in d.items():
            if k.startswith(("sec:", "page:")) and k.endswith(":v"): keys[k[:-2]] = keys.get(k[:-2], 0) + n
    secs = sorted(({"key": k, "views": n} for k, n in keys.items()), key=lambda x: -x["views"])
    U = {}
    for d in S.values():
        for k, n in d.items():
            if k.startswith("utm:") and k.endswith((":arr", ":shr")):
                src = k[4:-4]; u = U.setdefault(src, {"source": src, "arrivals": 0, "shares": 0}); u["arrivals" if k.endswith(":arr") else "shares"] += n
    shares = {k[:-6]: 0 for k in ()}
    for d in S.values():
        for k, n in d.items():
            if k.endswith(":share") and k.startswith(("post:", "item:")): shares[k[:-6]] = shares.get(k[:-6], 0) + n
    return {"sections": secs, "utm": sorted(U.values(), key=lambda u: (-u["arrivals"], -u["shares"])),
            "shares_total": sum(shares.values()), "shares_top": sorted(({"key": k, "shares": n} for k, n in shares.items()), key=lambda x: -x["shares"])[:20]}
def posts_report(days):
    S = stats.series(days); V = social._votes(); C = social._cmts(); X = social.antibot.excluded(); T = stats.totals()
    lim = time.time() - days * 86400; dl = list(S.keys())
    posts = [{"id": o["id"], "title": (o["v"].get("pl") or {}).get("text", "")[:80], "official": True, "t": o["t"]} for o in official.raw()]
    posts += [{"id": p["id"], "title": p["text"][:80], "official": False, "t": p["t"], "nick": p["nick"]} for p in social._posts() if p["status"] == "approved"]
    out = []
    for p in posts:
        k = "post:" + p["id"]; c = social.counts(k, None, V, X)
        cm_all = [x for x in C if x["target"] == k and x["status"] == "approved" and x["author"] not in X]
        views = _sum(S, k + ":v"); clicks = _sum(S, k + ":click"); shares = _sum(S, k + ":share")
        likes_p, dis_p, cm_p = _sum(S, k + ":like"), _sum(S, k + ":dislike"), len([x for x in cm_all if x["t"] >= lim])
        eng = likes_p + dis_p + cm_p + shares + clicks
        out.append(dict(p, views=views, unique=_sum(S, k + ":u"), views_total=T.get(k + ":v", 0), likes=c["up"], dislikes=c["down"], likes_period=likes_p, dislikes_period=dis_p,
                        comments=len(cm_all), comments_period=cm_p, clicks=clicks, ctr=round(clicks / views * 100, 1) if views else 0, shares=shares,
                        engagement=round(eng / views * 100, 1) if views else 0, trend=[S[d].get(k + ":v", 0) for d in dl],
                        langs={l: _sum(S, k + ":lang:" + l) for l in ("pl", "en", "es", "de", "uk") if _sum(S, k + ":lang:" + l)}))
    out.sort(key=lambda r: (-r["views"], -r["t"]))
    return {"days": dl, "posts": out}

# ---------- skrzynka właściciela (GET /api/owner/inbox) – bez e-maili i telefonów ----------
def _short(t, n=200):
    t = " ".join(str(t or "").split()); return t if len(t) <= n else t[:n - 1] + "…"
def _iso(ts):
    import datetime
    return datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc).isoformat().replace("+00:00", "Z")
def inbox(since_ts):
    import join, tickets, livechat
    out = {}
    out["applications"] = [{"id": m["id"], "nickname": _short(m.get("name"), 40), "role": m.get("role_other") or m.get("role"), "kind": m.get("kind"),
                            "message": _short(m.get("message"), 200), "has_contact": bool(m.get("email")), "has_portfolio": bool(m.get("portfolio")), "time": _iso(m["t"])}
                           for m in join._all() if m.get("t", 0) > since_ts]
    acc = [u for u in (store.get("accounts", {}) or {}).values() if u.get("created", 0) > since_ts]
    out["signups"] = {"count": len(acc), "nicknames": [_short(u.get("name") or "—", 30) for u in acc][:50]}
    tk = [t for t in tickets._all() if t.get("t", 0) > since_ts]
    hand = lambda t: str(t.get("description", "")).startswith("[Przekazane z czatu pomocy]")
    out["tickets"] = [{"id": t["id"], "category": t.get("category"), "text": _short(t.get("description"), 200), "has_contact": bool(t.get("email")), "time": _iso(t["t"])} for t in tk if not hand(t)]
    out["help_handoffs"] = [{"id": t["id"], "text": _short(str(t.get("description", "")).split("\n", 1)[-1], 300), "has_contact": bool(t.get("email")), "time": _iso(t["t"])} for t in tk if hand(t)]
    out["help_unanswered"] = [{"question": _short(u.get("q"), 200), "lang": u.get("lang"), "time": _iso(u["t"])} for u in (store.get("help_unanswered", []) or []) if u.get("t", 0) > since_ts]
    C = social._cmts()
    out["comments_pending"] = [{"id": c["id"], "target": c["target"], "nickname": _short(c["nick"], 30), "text": _short(c["text"], 200), "time": _iso(c["t"])}
                               for c in C if c["status"] == "pending" and c.get("t", 0) > since_ts]
    out["posts_pending"] = [{"id": p["id"], "nickname": _short(p["nick"], 30), "text": _short(p["text"], 200), "time": _iso(p["t"])}
                            for p in social._posts() if p["status"] == "pending" and p.get("t", 0) > since_ts]
    out["reports"] = [{"target": r["target"], "reason": _short(r.get("reason"), 160), "time": _iso(r["t"])} for r in (store.get("social_reports", []) or []) if r.get("t", 0) > since_ts]
    try:
        ib = livechat.inbox()
        out["creator_chat"] = [{"nickname": _short(c["name"], 30), "unread": c["unread"], "last": _short(c["last"], 160), "time": _iso(c["updated"])} for c in ib["convs"] if c["updated"] > since_ts and c["last_from"] != "admin"]
    except Exception: out["creator_chat"] = []
    try: out["suspects_flagged"] = len([s for s in social.antibot.admin_list() if s["status"] == "flagged"])
    except Exception: out["suspects_flagged"] = 0
    return out

_POP = {"t": 0, "ids": []}
def butik_popular(n=12):
    """„Popularne w Butiku”: tylko prawdziwe sygnały z 30 dni (wyświetlenia, polubienia po filtrze antybotowym, koszyk,
    udostępnienia, zakupy). Bez sygnałów → pusta lista (sekcja się nie pokazuje). Pamięć podręczna 10 min."""
    if time.time() - _POP["t"] < 600: return _POP["ids"][:n]
    S = stats.series(30); V = social._votes(); X = social.antibot.excluded(); P = _payments(30)
    buys = {}
    for p in P:
        if p.get("kind") == "item": buys[p.get("ref")] = buys.get(p.get("ref"), 0) + 1
    out = []
    for i in butik._load():
        if butik.eff_status(i) != "released" or not i.get("image"): continue
        k = "item:" + i["id"]; c = social.counts(k, None, V, X)
        sc = _sum(S, k + ":v") + 5 * max(c["up"] - c["down"], 0) + 8 * _sum(S, k + ":cart") + 6 * _sum(S, k + ":share") + 20 * buys.get(i["id"], 0)
        if sc > 0: out.append((sc, i["id"]))
    out.sort(reverse=True); _POP.update(t=time.time(), ids=[x[1] for x in out[:24]])
    return _POP["ids"][:n]
