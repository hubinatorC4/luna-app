/* Pakiet językowy Luny (i18n-pack): tłumaczy w przeglądarce napisy tworzone przez skrypty (baza „en” → język użytkownika),
   pilnuje lang/dir, formatuje daty i liczby wg języka (Intl) i daje prosty formatter ICU (liczba mnoga: Intl.PluralRules).
   Słownik: /lang/<kod>.json. Brak tłumaczenia → zostaje angielski. Nic nie wysyła na zewnątrz. */
(() => {
const D = document.documentElement; const code = D.getAttribute('data-luna-lang'); if (!code) return;
const M = {lang: code, bcp: D.getAttribute('lang') || code, dir: D.getAttribute('dir') || 'ltr'}; const BCP = M.bcp;
const keep = () => { if (D.getAttribute('lang') !== BCP) D.setAttribute('lang', BCP); if (D.getAttribute('dir') !== M.dir) D.setAttribute('dir', M.dir); };
keep(); new MutationObserver(keep).observe(D, {attributes: true, attributeFilter: ['lang', 'dir']});
try { if (!new RegExp('(?:^|; )luna_lang=' + M.lang.replace('-', '\\-') + '(;|$)').test(document.cookie)) document.cookie = 'luna_lang=' + M.lang + ';path=/;max-age=31536000;samesite=lax'; } catch(e){}
/* ---- daty i liczby: stare skrypty podają „en” albo nic → prawdziwy język ---- */
const fix = l => (l == null || /^en\b/i.test(Array.isArray(l) ? l[0] || '' : String(l))) ? BCP : l;
const wrapProto = (P, k) => { const o = P[k]; if (o) P[k] = function(l, opt){ return o.call(this, fix(l), opt); }; };
wrapProto(Date.prototype, 'toLocaleString'); wrapProto(Date.prototype, 'toLocaleDateString'); wrapProto(Date.prototype, 'toLocaleTimeString'); wrapProto(Number.prototype, 'toLocaleString');
['DateTimeFormat', 'NumberFormat', 'PluralRules', 'RelativeTimeFormat', 'ListFormat', 'Collator'].forEach(k => {
  const C = Intl[k]; if (!C) return;
  const W = function(l, o){ return new C(fix(l), o); }; W.prototype = C.prototype; W.supportedLocalesOf = C.supportedLocalesOf; Intl[k] = W; });
/* ---- ICU: {n, plural, one {# polubienie} few {…} other {…}} i {x, select, a {…} other {…}} ---- */
function icu(msg, v){
  v = v || {}; const PR = new Intl.PluralRules(BCP);
  let out = '', i = 0;
  const block = s => { let d = 0, j = s; for (; j < msg.length; j++){ if (msg[j] === '{') d++; else if (msg[j] === '}'){ d--; if (!d) return j; } } return -1; };
  while (i < msg.length){
    const c = msg[i];
    if (c !== '{'){ out += c; i++; continue; }
    const end = block(i); if (end < 0){ out += msg.slice(i); break; }
    const body = msg.slice(i + 1, end); const m = body.match(/^\s*(\w+)\s*(?:,\s*(plural|select)\s*,([\s\S]*))?$/);
    if (!m){ out += msg.slice(i, end + 1); i = end + 1; continue; }
    if (!m[2]){ out += v[m[1]] != null ? v[m[1]] : ''; i = end + 1; continue; }
    const opts = {}; const rest = m[3]; let k = 0;
    while (k < rest.length){
      const mm = rest.slice(k).match(/^\s*(=?\w+)\s*\{/); if (!mm) break;
      const st = k + mm[0].length - 1; let d = 0, e = st;
      for (; e < rest.length; e++){ if (rest[e] === '{') d++; else if (rest[e] === '}'){ d--; if (!d) break; } }
      opts[mm[1]] = rest.slice(st + 1, e); k = e + 1; }
    const val = v[m[1]];
    let pick = m[2] === 'plural' ? (opts['=' + val] ?? opts[PR.select(Number(val))] ?? opts.other) : (opts[val] ?? opts.other);
    out += icu(String(pick ?? ''), v).replace(/#/g, m[2] === 'plural' ? new Intl.NumberFormat(BCP).format(Number(val)) : '#');
    i = end + 1;
  }
  return out;
}
/* ---- słownik ---- */
let T = {}, H = {}, P = [];
const norm = s => s.replace(/\s+/g, ' ').trim();
const look = s => {
  const k = norm(s); if (!k || !/\p{L}/u.test(k)) return null;
  let r = T[k];
  if (r == null){ for (const [rx, x] of P){ const m = k.match(rx); if (m){ r = x.replace(/\{(\d+)\}/g, (_, n) => m[+n + 1] ?? ''); break; } } }
  if (r == null){
    const m2 = k.match(/^([^\p{L}\p{N}]*)(.*?)([^\p{L}\p{N}.!?…)]*)$/u);
    if (m2 && m2[2] && m2[2] !== k && T[m2[2]] != null) r = m2[1] + T[m2[2]] + m2[3];
  }
  if (r == null) return null;
  const lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0];
  return lead + r + trail;
};
const ATTR = ['placeholder', 'title', 'aria-label', 'alt', 'data-tip'];
const SKIP = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'CODE', 'PRE', 'NOSCRIPT']);
function tEl(el){
  if (el.nodeType !== 1 || SKIP.has(el.tagName) || el.isContentEditable || el.closest('[data-no-i18n],[translate=no],.lswitch,.lpick')) return;
  for (const a of ATTR){ const v = el.getAttribute(a); if (v){ const r = look(v); if (r != null && r !== v) el.setAttribute(a, r); } }
  if (el.tagName === 'INPUT' && /^(button|submit|reset)$/i.test(el.type) && el.value){ const r = look(el.value); if (r != null) el.value = r; }
  if (el.children.length && el.innerHTML.length < 4000){ const k = norm(el.innerHTML); if (H[k] != null){ el.innerHTML = H[k]; return; } }
}
function walk(root){
  if (!root) return;
  if (root.nodeType === 3){ tText(root); return; }
  if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
  if (root.nodeType === 1){ if (SKIP.has(root.tagName) || root.closest('[data-no-i18n],[translate=no],.lswitch,.lpick')) return; tEl(root); }
  const it = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {acceptNode: n => (n.nodeType === 1 && SKIP.has(n.tagName)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  let n; const els = [], txt = [];
  while ((n = it.nextNode())) (n.nodeType === 1 ? els : txt).push(n);
  els.forEach(tEl); txt.forEach(tText);
}
function tText(n){
  const v = n.nodeValue; if (!v || v.length > 3000 || !n.parentNode || SKIP.has(n.parentNode.nodeName)) return;
  if (n.parentNode.closest && n.parentNode.closest('[data-no-i18n],[translate=no],.lswitch,.lpick')) return;
  const r = look(v); if (r != null && r !== v) n.nodeValue = r;
}
function links(root){
  (root.querySelectorAll ? root.querySelectorAll('iframe[src*="lang="]') : []).forEach(f => {
    try { const u = new URL(f.src, location.href); if (u.origin === location.origin && u.searchParams.get('lang') === 'en'){ u.searchParams.set('lang', M.lang); f.src = u.pathname + u.search + u.hash; } } catch(e){}
  });
  (root.querySelectorAll ? root.querySelectorAll('a[href*="lang="]') : []).forEach(a => {
    try { const u = new URL(a.href); if (u.origin === location.origin && /^(en|pl)$/.test(u.searchParams.get('lang') || '') && !a.closest('.lpick,.lswitch') && !a.hasAttribute('hreflang') && !a.hasAttribute('lang')){ u.searchParams.set('lang', M.lang); a.href = u.pathname + u.search + u.hash; } } catch(e){}
  });
}
let busy = false; const queue = new Set();
function flush(){ busy = false; const q = [...queue]; queue.clear(); obs.disconnect(); q.forEach(n => { if (n.isConnected){ walk(n); if (n.nodeType === 1) links(n); } }); if (document.title){ const r = look(document.title); if (r) document.title = r; } start(); }
const obs = new MutationObserver(ms => {
  for (const m of ms){
    if (m.type === 'childList') m.addedNodes.forEach(x => queue.add(x));
    else if (m.type === 'characterData') queue.add(m.target);
    else if (m.type === 'attributes') queue.add(m.target);
  }
  if (!busy && queue.size){ busy = true; requestAnimationFrame(flush); }
});
const start = () => obs.observe(document.body || D, {childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTR.concat(['href', 'src'])});
window.LunaI18n = {lang: M.lang, bcp: BCP, dir: M.dir, t: s => look(s) ?? s, icu, fmt: (en, v) => icu(look(en) ?? en, v), ready: null};
window.LunaI18n.ready = fetch('/lang/' + M.lang + '.json?v=1', {credentials: 'omit'}).then(r => r.ok ? r.json() : {}).then(j => {
  T = j.t || {}; H = j.h || {};
  P = (j.p || []).map(([k, x]) => { try { return [new RegExp('^' + k.replace(/[.*+?^$()|[\]\\]/g, '\\$&').replace(/\\?\{(\d+)\\?\}/g, '(.+?)') + '$'), x]; } catch(e){ return null; } }).filter(Boolean);
  const go = () => { walk(document.body); links(document); if (document.title){ const r = look(document.title); if (r) document.title = r; } start(); window.dispatchEvent(new CustomEvent('luna-i18n-ready', {detail: M.lang})); };
  if (document.body) go(); else document.addEventListener('DOMContentLoaded', go);
}).catch(() => {});
})();
