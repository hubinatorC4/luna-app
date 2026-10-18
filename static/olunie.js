fetch('/api/catalog').then(r => r.json()).then(c => {
  const esc = s => String(s).replace(/[&<>]/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[x]));
  document.getElementById('plans').innerHTML = c.plans.map((p, i) => `<div class="plan${i === 1 ? ' hl' : ''}"><h3>${esc(p.name)}</h3><ul>${p.features.map((f, j) => `<li>${/oraz:$/.test(f) ? '<b>' + esc(f) + '</b>' : esc(f)}</li>`).join('')}</ul></div>`).join('');
}).catch(() => {});
