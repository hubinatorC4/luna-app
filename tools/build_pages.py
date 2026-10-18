# -*- coding: utf-8 -*-
"""Generuje strony informacyjne v1.3.1: testerzy, wesprzyj, dolacz, twarz, problemy, butik, regulamin. Uruchom: python3 tools/build_pages.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_common import HEAD, FOOT, VER
import pages_content as C
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

def page(fn, title, desc, body, i18n=None, scripts=(), active="", cls=""):
    act = {k: "" for k in ("a_butik", "a_test", "a_join", "a_face", "a_sup", "a_wall")}
    if active: act[active] = ' aria-current="page"'
    h = HEAD.format(title=title, desc=desc, ver=VER, cls=cls, **act)
    j = f'<script type="application/json" id="i18n">{json.dumps(i18n, ensure_ascii=False)}</script>\n' if i18n else ""
    sc = "".join(f'<script src="{s}?v={VER}"></script>\n' for s in scripts)
    pi = '<script src="/pagei18n.js?v=' + VER + '"></script>\n' if i18n else ""
    open(os.path.join(S, fn), "w", encoding="utf-8").write(h + body + FOOT + j + pi + sc + '<script src="/helpbot-loader.js?v=' + VER + '"></script>\n</body>\n</html>\n')

def t(k, tag="span", cls=""): return f'<{tag} data-i18n="{k}"{f" class=\"{cls}\"" if cls else ""}>{C.TESTERZY["pl"].get(k, "")}</{tag}>'
L = C.LANGTABS
# ---------- testerzy ----------
P = C.TESTERZY["pl"]
body = f"""<main class="page">
{L}
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p><span class="badge-noads" data-note="noads"></span></p>
<div class="card"><h2 data-i18n="left_h">{P['left_h']}</h2><div class="tst-bar"><i></i></div><p class="tst-left" aria-live="polite">Zostało … z 50 miejsc</p></div>
<h2 data-i18n="rules_h">{P['rules_h']}</h2><ul data-i18n="rules">{P['rules']}</ul>
<h2 data-i18n="steps_h">{P['steps_h']}</h2>
<ol class="steps"><li data-i18n="s1">{P['s1']}</li><li data-i18n="s2">{P['s2']}</li><li data-i18n="s3">{P['s3']}</li><li data-i18n="s4">{P['s4']}</li><li data-i18n="s5">{P['s5']}</li></ol>
<h2 id="formularz" data-i18n="form_h">{P['form_h']}</h2><p class="note" data-i18n="form_note">{P['form_note']}</p>
<div id="testerzy-form" class="tform card"></div>
<h2 data-i18n="faq_h">{P['faq_h']}</h2>
<div class="faq">{''.join(f'<details><summary data-i18n="q{i}">{P[f"q{i}"]}</summary><p data-i18n="a{i}">{P[f"a{i}"]}</p></details>' for i in range(1, 6))}</div>
</main>
"""
page("testerzy.html", P["_title"], "Jak zostać testerem aplikacji Luna mówi jak jest: 5 kroków, zasady i FAQ. Maksymalnie 50 osób, Premium za darmo na 2 miesiące.", body, C.TESTERZY, ["/testers.js"], "a_test")

# ---------- wesprzyj ----------
P = C.WESPRZYJ["pl"]
body = f"""<main class="page">
<div class="no-twa">
{L}
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p class="money" data-note="money"></p>
<div class="card" id="bank" hidden>
  <h2 data-i18n="bank_h">{P['bank_h']}</h2>
  <p><span data-i18n="holder">{P['holder']}</span>: <b id="bHolder"></b></p>
  <p><span data-i18n="iban">{P['iban']}</span>: <b id="bIban"></b> <button type="button" class="pill ghost copybtn" data-copy="bIban" data-i18n="copy">{P['copy']}</button></p>
  <p><span data-i18n="title">{P['title']}</span>: <b id="bTitle"></b> <button type="button" class="pill ghost copybtn" data-copy="bTitle" data-i18n="copy">{P['copy']}</button></p>
</div>
<p class="note" id="bankSoon" data-i18n="soon">{P['soon']}</p>
</div>
<p class="twa-only note" data-i18n="twa">{P['twa']}</p>
</main>
"""
page("wesprzyj.html", P["_title"], "Wesprzyj projekt fanowski Luna mówi jak jest dobrowolną wpłatą.", body, C.WESPRZYJ, ["/wesprzyj.js"], "a_sup")

# ---------- dolacz ----------
P = C.DOLACZ["pl"]
roles = [("projektant/ka", "r_design"), ("grafik/czka", "r_graph"), ("programista/ka", "r_dev"), ("lektor/ka", "r_voice"), ("twórca treści", "r_content"), ("tłumacz/ka", "r_tr"), ("marketing", "r_mkt"), ("inne", "r_other")]
FORM_COMMON = lambda P, extra="": f"""
  <label><span data-i18n="f_name">{C.DOLACZ['pl']['f_name']}</span><input name="name" required maxlength="60" autocomplete="given-name"></label>
  <label><span data-i18n="f_email">{C.DOLACZ['pl']['f_email']}</span><input name="email" type="email" required maxlength="254" autocomplete="email"></label>
  {extra}
  <label><span data-i18n="f_dob">{C.DOLACZ['pl']['f_dob']}</span><input name="dob" type="date" required></label>
  <label class="consent"><input type="checkbox" name="adult" required> <span data-i18n="f_adult">{C.DOLACZ['pl']['f_adult']}</span></label>
  <label class="consent"><input type="checkbox" name="consent" required> <span data-i18n="f_consent">{C.DOLACZ['pl']['f_consent']}</span> <a href="/privacy.html" target="_blank">↗</a></label>
  <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
"""
body = f"""<main class="page">
{L}
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p class="note" data-note="invite"></p>
<p class="warnbox"><b data-i18n="note">{P['note']}</b></p>
<form class="form card" id="joinForm" novalidate data-kind="projekt">
  {FORM_COMMON(P, f'''<label><span data-i18n="f_role">{P['f_role']}</span><select name="role" required><option value=""></option>{''.join(f'<option value="{v}" data-i18n="{k}">{P[k]}</option>' for v, k in roles)}</select></label>
  <label id="otherRow" hidden><span data-i18n="f_other">{P['f_other']}</span><input name="role_other" maxlength="60"></label>
  <label><span data-i18n="f_msg">{P['f_msg']}</span><textarea name="message" rows="4" maxlength="1500" required></textarea></label>
  <label><span data-i18n="f_link">{P['f_link']}</span><input name="portfolio" type="url" maxlength="300" placeholder="https://"></label>''')}
  <button class="pill primary big" type="submit" data-i18n="f_send">{P['f_send']}</button>
  <p class="err" role="alert"></p><p class="ok" role="status" hidden data-i18n="f_ok">{P['f_ok']}</p>
</form>
</main>
"""
D2 = {l: dict(C.DOLACZ[l]) for l in C.DOLACZ}
page("dolacz.html", P["_title"], "Dołącz do projektu Luna mówi jak jest – szukamy projektantów, programistów, lektorów, twórców treści i tłumaczy.", body, D2, ["/joinform.js"], "a_join")

# ---------- twarz ----------
P = C.TWARZ["pl"]
TW = {l: {**{k: C.DOLACZ[l][k] for k in ("f_name", "f_email", "f_dob", "f_adult", "f_consent")}, **C.TWARZ[l]} for l in C.TWARZ}
body = f"""<main class="page">
{L}
<div class="xmas-only xmas-banner" hidden><p data-i18n="xmas">{P['xmas']}</p></div>
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p class="badge-ai ailabel" data-i18n="ailabel">{P['ailabel']}</p>
<p class="warnbox" data-i18n="scam">{P['scam']}</p>
<p data-i18n="how">{P['how']}</p>
<p class="note" data-i18n="body">{P['body']}</p>
<div class="card"><h2 data-i18n="dates_h">{P['dates_h']}</h2>
<p><b data-i18n="d_open">{P['d_open']}</b> <span id="cDates">18.10.2026 – 31.12.2026, 23:59 (czas polski)</span></p>
<p><b data-i18n="d_final">{P['d_final']}</b> <span id="cFinal" data-i18n="d_final_tbd">{P['d_final_tbd']}</span></p>
<div id="countdown" class="countdown" aria-live="polite"><p data-i18n="cd_h">{P['cd_h']}</p>
<div class="cd"><span><b id="cdD">–</b><small data-i18n="cd_d">{P['cd_d']}</small></span><span><b id="cdH">–</b><small data-i18n="cd_h2">{P['cd_h2']}</small></span><span><b id="cdM">–</b><small data-i18n="cd_m">{P['cd_m']}</small></span><span><b id="cdS">–</b><small data-i18n="cd_s">{P['cd_s']}</small></span></div></div>
<p class="note" id="cClosed" hidden data-i18n="closed">{P['closed']}</p>
</div>
<h2 data-i18n="rules_h">{P['rules_h']}</h2><ul data-i18n="rules">{P['rules']}</ul>
<p class="note" data-i18n="idcheck">{P['idcheck']}</p>
<details class="card"><summary data-i18n="gdpr_h">{P['gdpr_h']}</summary><ul data-i18n="gdpr">{P['gdpr']}</ul></details>
<div id="castForm"><h2 data-i18n="form_h">{P['form_h']}</h2>
<form class="form card" id="joinForm" novalidate data-kind="twarz">
  {FORM_COMMON(P, f'''<input type="hidden" name="role" value="twarz AI">
  <label><span data-i18n="f_height">{P['f_height']}</span><input name="height" type="number" min="120" max="220" step="1" inputmode="numeric"></label>
  <label><span data-i18n="f_msg">{P['f_msg']}</span><textarea name="message" rows="4" maxlength="1500" required></textarea></label>
  <label><span data-i18n="f_link">{P['f_link']}</span><input name="portfolio" type="url" maxlength="300" placeholder="https://"></label>
  <label class="consent"><input type="checkbox" name="img_consent" required> <span data-i18n="f_img">{P['f_img']}</span></label>''')}
  <button class="pill primary big" type="submit" data-i18n="f_send">{P['f_send']}</button>
  <p class="err" role="alert"></p><p class="ok" role="status" hidden data-i18n="f_ok">{P['f_ok']}</p>
</form></div>
</main>
<div class="snow" aria-hidden="true"></div>
"""
page("twarz.html", P["_title"], P["lead"], body, TW, ["/joinform.js", "/twarz.js"], "a_face")

# ---------- problemy ----------
P = C.PROBLEMY["pl"]
cats = [("Płatności", "c_pay"), ("Dźwięk/głos", "c_voice"), ("Mikrofon", "c_mic"), ("Konto/logowanie", "c_acc"), ("Butik", "c_shop"), ("Luna Live", "c_live"), ("Aplikacja Android", "c_android"), ("Inne", "c_other")]
body = f"""<main class="page">
{L}
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p class="warnbox" data-i18n="warn">{P['warn']}</p>
<form class="form card" id="tkForm" novalidate>
  <label><span data-i18n="f_cat">{P['f_cat']}</span><select name="category" required><option value=""></option>{''.join(f'<option value="{v}" data-i18n="{k}">{P[k]}</option>' for v, k in cats)}</select></label>
  <label><span data-i18n="f_desc">{P['f_desc']}</span><textarea name="description" rows="5" maxlength="3000" required data-i18n-ph="f_desc_ph" placeholder="{P['f_desc_ph']}"></textarea></label>
  <label><span data-i18n="f_email">{P['f_email']}</span><input name="email" type="email" maxlength="254" autocomplete="email"></label>
  <label><span data-i18n="f_shot">{P['f_shot']}</span><input name="shot" type="file" accept="image/png,image/jpeg,image/webp"></label>
  <p class="hint" data-i18n="f_auto">{P['f_auto']}</p>
  <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
  <button class="pill primary big" type="submit" data-i18n="f_send">{P['f_send']}</button>
  <p class="err" role="alert"></p>
  <div class="ok" role="status" hidden><p><span data-i18n="f_ok">{P['f_ok']}</span> <b id="tkId"></b></p><p data-i18n="f_keep">{P['f_keep']}</p></div>
</form>
<div class="card"><h2 data-i18n="st_h">{P['st_h']}</h2>
<form id="stForm" class="form"><input name="id" placeholder="LUNA-0001" maxlength="12"><button class="pill ghost" data-i18n="st_btn">{P['st_btn']}</button></form><p id="stOut"></p></div>
</main>
"""
page("problemy.html", P["_title"], "Zgłoś problem techniczny z aplikacją Luna mówi jak jest.", body, C.PROBLEMY, ["/problemy.js"], "", "help-open")

# ---------- butik ----------
P = C.BUTIK["pl"]
body = f"""<main class="page">
{L}
<h1 data-i18n="h1">{P['h1']}</h1>
<p class="lead" data-i18n="lead">{P['lead']}</p>
<p><span class="badge-noads" data-note="noads"></span></p>
<div class="annbox" id="ann" aria-live="polite"><button type="button" class="annnav" data-prev aria-label="‹">‹</button><p class="anntext"></p><button type="button" class="annnav" data-next aria-label="›">›</button><div class="anndots"></div></div>
<p class="nonude" id="nonude"><b>Tylko eleganckie, w pełni zakrywające stroje.</b> W Butiku nie ma nagości, bielizny ani strojów odsłaniających – Luna zawsze wygląda z klasą.</p>
<div class="tabsx" role="tablist"><button type="button" class="on" data-tab="col" data-i18n="t_col">{P['t_col']}</button><button type="button" data-tab="price" data-i18n="t_price">{P['t_price']}</button></div>
<section id="tab-col"><div class="chips" id="chips" role="group" aria-label="Kategorie"></div><div class="grid3" id="items"></div></section>
<section id="tab-price" hidden>
  <p class="warnbox" id="preview" hidden data-i18n="preview">{P['preview']}</p>
  <h2 data-i18n="lines_h">{P['lines_h']}</h2><table class="tbl" id="lines"></table>
  <h2 data-i18n="plans_h">{P['plans_h']}</h2><p data-i18n="plans_note">{P['plans_note']}</p><div class="plancards" id="plansTbl"></div>
  <p class="hint" data-i18n="vat">{P['vat']}</p>
  <details class="card" id="howPay"><summary data-i18n="how_h">{P['how_h']}</summary><ol data-i18n="how">{P['how']}</ol></details>
  <div class="card" id="payBox"></div>
  <h2 data-i18n="items_h">{P['items_h']}</h2><div id="itemPrices"></div>
</section>
</main>
"""
page("butik.html", P["_title"], "Butik Luny – stroje w trzech liniach: Ekonomiczna, Classic i Couture. Cennik planów i strojów.", body, C.BUTIK, ["/social.js", "/butik.js"], "a_butik")
print("ok")

# ---------- scianka (Ścianka Agentek Głosu) ----------
P = C.WALL["pl"]
body = f"""<div class="wallpage">
<section class="hero"><h1 data-i18n="h1">{P['h1']}</h1><p class="sub" data-i18n="sub">{P['sub']}</p>
<p class="lead" data-i18n="lead">{P['lead']}</p></section>
<main class="wrap"><div class="feed">
<form class="composer card" id="composer" novalidate>
  <span class="ava gen" id="meAva" aria-hidden="true">✦</span>
  <div class="cmain">
    <textarea class="cfield" name="text" maxlength="2000" rows="2" data-i18n-ph="ph" placeholder="{P['ph']}" aria-label="{P['ph']}"></textarea>
    <div class="cextra" id="cExtra" hidden>
      <input class="nickin" name="nick" maxlength="30" data-i18n-ph="nick" placeholder="{P['nick']}" aria-label="{P['nick']}" autocomplete="nickname">
      <label id="adultRow"><input type="checkbox" name="adult"> <span data-i18n="adult">{P['adult']}</span></label>
      <label id="imgDeclRow" hidden><input type="checkbox" name="img_decl"> <span data-i18n="img_decl">{P['img_decl']}</span></label>
      <div id="imgPrev"></div>
    </div>
    <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
    <input type="file" id="imgFile" accept="image/png,image/jpeg,image/webp" hidden>
    <div class="crow"><button type="button" class="ghost" id="imgBtn" data-i18n="img">{P['img']}</button><button type="submit" class="primary" data-i18n="publish">{P['publish']}</button></div>
    <p class="cmsg" id="cMsg" role="status" aria-live="polite"></p>
  </div>
</form>
<div class="tabs" role="tablist"><button type="button" class="on" data-sort="new" data-i18n="t_new">{P['t_new']}</button><button type="button" data-sort="top" data-i18n="t_top">{P['t_top']}</button></div>
<div id="feed" aria-live="polite"></div>
<div class="card empty" id="empty" hidden><div class="big">🎙️</div><h3 data-i18n="empty_h">{P['empty_h']}</h3><p data-i18n="empty">{P['empty']}</p></div>
<p class="endnote" id="endnote" hidden data-i18n="end">{P['end']}</p>
<div id="sentinel"></div>
</div>
<aside class="side">
  <div class="card scard"><h3 data-i18n="rules_h">{P['rules_h']}</h3><ul data-i18n="rules">{P['rules']}</ul></div>
  <div class="card scard"><h3 data-i18n="agents_h">{P['agents_h']}</h3><p class="mutep" data-i18n="agents_empty">{P['agents_empty']}</p></div>
  <div class="card scard soft"><h3 data-i18n="ref_h">{P['ref_h']}</h3><p data-i18n="ref">{P['ref']}</p><button type="button" class="btn sm" id="refCopy" data-i18n="ref_btn">{P['ref_btn']}</button></div>
</aside></main></div>
"""
page("scianka.html", P["_title"], P["lead"], body, C.WALL, ["/social.js", "/wall-official.js", "/scianka.js"], "a_wall", "wallbody")
