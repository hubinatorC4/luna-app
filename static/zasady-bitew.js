/* 📜 Zasady bitew: prawdziwa liczba głosów usuniętych jako oszustwo (bez nazw kont). */
(() => {
const D = JSON.parse(document.getElementById('i18n').textContent);
const t = () => Object.assign({}, D.pl, D[(document.documentElement.lang || 'pl').slice(0, 2)] || {});
const el = document.getElementById('zbFraud');
fetch('/api/battles/rules').then(r => r.json()).then(d => {
  const f = d.fraud || {}, b = Object.keys(f).length, n = Object.values(f).reduce((a, x) => a + x, 0);
  el.textContent = n ? t().fraud_n.replace('{n}', n).replace('{b}', b) : t().fraud_none;
}).catch(() => {});
})();
