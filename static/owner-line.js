/* Linia własności (5 języków): „Jesteś w pełni właścicielem swojej własnej, wykreowanej agentki…” – pogrubiona, w miękkim stylu Luny.
   Wstawiana: kreator/trening agentki (#custom), edycja profilu własnej agentki (.ph-ed – widzi tylko właściciel), zgłoszenie do Bitew (#btEnter).
   Pełna treść o prawach: regulamin § 9g. */
(() => {
const T = {
  pl: 'Jesteś w pełni właścicielem swojej własnej, wykreowanej agentki, która rywalizuje w konkursach mody, piękna i głosu.',
  en: 'You fully own your very own agent that you created – the one competing in fashion, beauty and voice contests.',
  es: 'Eres plenamente propietario/a de tu propia agente creada por ti, que compite en concursos de moda, belleza y voz.',
  de: 'Du bist vollständige Eigentümerin bzw. vollständiger Eigentümer deiner eigenen, selbst erschaffenen Agentin, die in Mode-, Schönheits- und Stimmwettbewerben antritt.',
  uk: 'Ви повністю володієте своєю власною, створеною вами агенткою, яка змагається в конкурсах моди, краси та голосу.'
};
const WINK = {pl: 'Luna tylko kibicuje 💚', en: 'Luna just cheers you on 💚', es: 'Luna solo te anima 💚', de: 'Luna feuert dich nur an 💚', uk: 'Луна лише вболіває 💚'};
const MORE = {pl: 'Twoje prawa', en: 'Your rights', es: 'Tus derechos', de: 'Deine Rechte', uk: 'Ваші права'};
const lang = () => { let l = document.documentElement.lang || 'pl'; try { l = new URLSearchParams(location.search).get('lang') || localStorage.getItem('luna.lang') || l; } catch(e){} l = String(l).slice(0, 2); return T[l] ? l : 'pl'; };
if (!document.getElementById('ownLineCss')){ const st = document.createElement('style'); st.id = 'ownLineCss';
  st.textContent = '.own-line{display:flex;gap:10px;align-items:flex-start;margin:10px 0 12px;padding:12px 14px;border-radius:22px;background:linear-gradient(135deg,rgba(61,220,151,.12),rgba(255,154,60,.08));border:1px solid rgba(61,220,151,.28);color:#eafff4;font-size:14.5px;line-height:1.45;text-align:left}.own-line i{font-style:normal;font-size:20px;line-height:1}.own-line strong{font-weight:800}.own-line a{color:#FF9A3C;font-weight:700;white-space:nowrap}';
  document.head.appendChild(st); }
const html = () => { const l = lang(); return `<i aria-hidden="true">👑</i><span><strong>${T[l]}</strong> ${WINK[l]} <a href="/regulamin.html${l !== 'pl' ? '?lang=' + l : ''}#tresci">${MORE[l]} →</a></span>`; };
const SPOTS = [['#custom > form > h2', 'after'], ['.ph-ed > h2', 'after'], ['#btEnter > h2', 'after']];
function place(){
  for (const [sel, where] of SPOTS){
    const a = document.querySelector(sel); if (!a) continue;
    const nx = a.nextElementSibling; if (nx && nx.classList.contains('own-line')) continue;
    const p = document.createElement('p'); p.className = 'own-line'; p.innerHTML = html(); a.insertAdjacentElement(where === 'after' ? 'afterend' : 'beforebegin', p);
  }
}
window.LunaOwnLine = {text: () => T[lang()], html};
place();
let q = 0; new MutationObserver(() => { if (!q) q = requestAnimationFrame(() => { q = 0; place(); }); }).observe(document.body, {childList: true, subtree: true});
window.addEventListener('luna-lang', () => document.querySelectorAll('.own-line').forEach(p => { p.innerHTML = html(); }));
})();
