/* Oficjalne wpisy Ścianki – renderowanie bogatej treści (z pliku w repo). Ceny przychodzą z katalogu na żywo. */
(() => {
const CUR = {pl: ['pln', ',', false, 'zł', 'zł'], en: ['usd', '.', true, '$', 'PLN'], es: ['eur', ',', false, '€', 'PLN'], de: ['eur', ',', false, '€', 'zł'], uk: ['eur', ',', false, '€', 'зл.']};
const SOON = {pl: 'Premiera', en: 'Release:', es: 'Estreno:', de: 'Start:', uk: 'Прем’єра:'};
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const href = (u, l) => { if (!u) return '#'; const [a, h] = u.split('#'); return a + (l !== 'pl' ? (a.includes('?') ? '&' : '?') + 'lang=' + l : '') + (h ? '#' + h : ''); };
function money(prices, l, foreign){
  if (!prices) return '';
  const c = CUR[l] || CUR.pl; const cur = foreign && prices[c[0]] != null ? c[0] : 'pln';
  const n = Number(prices[cur]).toFixed(2).replace('.', c[1]);
  const sym = cur === 'pln' ? c[4] : c[3];
  return (cur === 'usd' ? `<sup class="pre">${sym}</sup>${n}` : `${n}<sup>${esc(sym)}</sup>`);
}
const planp = (v, l) => { const c = CUR[l] || CUR.pl; return `${String(v).replace(/[.,]/, c[1])}<sup class="cur">${esc(c[4])}</sup>`; };
const soonTxt = (d, l) => { try { return SOON[l] + ' ' + new Date(d + 'T12:00:00').toLocaleDateString(l === 'uk' ? 'uk-UA' : l, {day: 'numeric', month: 'long'}); } catch(e){ return SOON[l] + ' ' + d; } };
function render(p, l){
  const R = p.rich, a = R.v[l] || R.v.pl, L = R.links || {};
  const ps = (arr, cls) => `<div class="ptext${cls ? ' ' + cls : ''}">` + arr.map(x => `<p>${x}</p>`).join('') + '</div>';
  const media = `<figure class="media"><img src="${esc(p.img)}" alt="" loading="lazy" width="1280" height="720"><span class="ai-badge" title="AI">✦ AI</span></figure>`;
  const cards = () => '<div class="pgrid">' + R.items.map(it => `<div class="pc"><small>${esc(it.collection)}</small><div class="pn">${esc((a.names || {})[it.id] || it.id)}</div>${it.price ? `<div class="pp">${money(it.price, l, R.foreign)}</div>` : ''}<div class="tier">${esc(a.tiers[it.tier] || '')}</div>${it.upcoming && it.release_date ? `<span class="soon">📅 ${esc(soonTxt(it.release_date, l))}</span>` : ''}</div>`).join('') + '</div>';
  let b = `<div class="ptag">${a.tag}</div><h2 class="lead-h">${a.h}</h2>`;
  switch (R.kind){
    case 1: b += ps(a.ps) + media + cards() + `<p class="pnote">${a.note}</p><div class="cta-row"><a class="btn" href="${href(L.btn, l)}">${a.btn}</a></div>`; break;
    case 2: b += ps(a.ps) + media + cards() + `<div class="date"><div class="day">${a.day}</div><div><div class="mon">${a.mon}</div><small>${a.small}</small></div><a class="btn" href="${href(L.btn, l)}">${a.btn}</a></div>`; break;
    case 3: { const ic = ['📸', '👗', '✍️', '💚'];
      b += `<p class="quote">${a.quote}</p>` + ps([a.intro]) + media + '<ul class="checks">' + a.checks.map((c, k) => `<li><span class="ic">${ic[k]}</span><span>${c}</span></li>`).join('') + '</ul>' + ps([a.after], 'mt14') +
        `<a class="linkcard" href="${href(L.link, l)}"><span class="lc-ico">🌟</span><div><b>${a.link}</b><small>${a.lsmall} · ${esc(a.url || '')}</small></div><span class="arrow">→</span></a>`; break; }
    case 4: { const ids = ['podstawowa', 'premium', 'pro'];
      const plans = a.plans.map(([n, per, perk], k) => `<div class="plan${k === 1 ? ' hot' : ''}">${k === 1 ? `<span class="hotlbl">${a.hot}</span>` : ''}<span class="pl">${n}</span>${R.plans && R.plans[ids[k]] != null ? `<div class="big">${planp(R.plans[ids[k]], l)}</div>` : ''}<span class="per">${per}</span><span class="perk">${perk}</span></div>`).join('');
      b += '<div class="quiz">' + a.quiz.map((q, k) => `<span${k === 2 ? ' class="ok"' : ''}>${q}</span>`).join('') + '</div>' + ps([a.p]) + media + `<div class="plans">${plans}</div><div class="planfoot">` + a.chips.map(c => `<span class="chip">${c}</span>`).join('') + `<a class="btn" href="${href(L.btn, l)}">${a.btn}</a></div>`; break; }
    case 5: b += `<div class="mvf"><div class="mit"><b>${a.mit[0]}</b>${a.mit[1]}</div><div class="fakt"><b>${a.fakt[0]}</b>${a.fakt[1]}</div></div>` + ps(a.ps, 'mt14') + media + `<div class="cta-row"><span class="noads">${a.noads}</span><a class="btn ml-auto" href="${href(L.btn, l)}">${a.btn}</a></div>`; break;
    case 6: b += ps([a.p1]) + `<p class="quote">${a.quote}</p>` + media + `<div class="ptext mt14"><p>${a.p2}</p><p class="sign">${a.sign}</p></div><div class="cta-row"><a class="btn" href="${href(L.btn, l)}">${a.btn}</a><a class="btn ghostb" href="${href(L.btn2, l)}">${a.btn2}</a></div>`; break;
  }
  return b;
}
window.LunaOfficial = {render, esc};
})();
