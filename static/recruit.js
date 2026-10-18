/* Przypięte u góry kanału: „Pilnie szukamy nowych agentek!” + zapowiedź „Bitwy agentek – już wkrótce”.
   Bitwy ruszą dopiero, gdy będą co najmniej 2 zatwierdzone agentki – do tego czasu bez głosowania, bez fikcyjnych rywalek i głosów. */
(() => {
const L = (document.documentElement.lang || 'pl').slice(0, 2); const lq = L === 'pl' ? '' : '?lang=' + L;
const T = {
 pl: ['Pilnie szukamy nowych agentek!', 'Masz ciepły, wyraźny głos? Zgłoś się do castingu – to zajmie 2 minuty.', 'Zgłoś się do castingu', 'Bitwy agentek – już wkrótce', 'Dwie agentki, dwa nagrania głosu, jeden głos od Ciebie. Wystartujemy, gdy w obsadzie będą co najmniej dwie agentki.', 'Głosować będą tylko prawdziwe konta.'],
 en: ['We urgently need new agents!', 'Got a warm, clear voice? Apply for the casting – it takes 2 minutes.', 'Apply for the casting', 'Agent battles – coming soon', 'Two agents, two voice clips, one vote from you. We’ll start once at least two agents are on board.', 'Only real accounts will be able to vote.'],
 es: ['¡Buscamos nuevas agentes con urgencia!', '¿Tienes una voz cálida y clara? Apúntate al casting: son 2 minutos.', 'Apúntate al casting', 'Batallas de agentes: muy pronto', 'Dos agentes, dos clips de voz y un voto tuyo. Empezaremos cuando haya al menos dos agentes.', 'Solo votarán cuentas reales.'],
 de: ['Wir suchen dringend neue Agentinnen!', 'Du hast eine warme, klare Stimme? Bewirb dich zum Casting – dauert 2 Minuten.', 'Zum Casting bewerben', 'Agentinnen-Battles – bald verfügbar', 'Zwei Agentinnen, zwei Stimmproben, deine Stimme entscheidet. Start, sobald mindestens zwei Agentinnen dabei sind.', 'Abstimmen können nur echte Konten.'],
 uk: ['Терміново шукаємо нових агенток!', 'Маєте теплий, чіткий голос? Подайте заявку на кастинг – це 2 хвилини.', 'Подати заявку', 'Битви агенток – незабаром', 'Дві агентки, два голосові записи, один ваш голос. Стартуємо, щойно в команді буде щонайменше дві агентки.', 'Голосувати зможуть лише справжні акаунти.']}[L] || null;
const t = T || {}; const x = T || ['Pilnie szukamy nowych agentek!', '', 'Zgłoś się', 'Bitwy agentek – już wkrótce', '', ''];
function build(){
  const el = document.createElement('section'); el.className = 'recruit-pin'; el.id = 'casting-pilne'; el.dataset.track = 'sec:recruit';
  el.innerHTML = `<div class="rc-urgent"><span class="rc-badge">📣 ${L === 'pl' ? 'Przypięte' : L === 'de' ? 'Angeheftet' : L === 'es' ? 'Fijado' : L === 'uk' ? 'Закріплено' : 'Pinned'}</span>
      <h2>${x[0]}</h2><p>${x[1]}</p><a class="pill primary big" href="/twarz.html${lq}#castForm">🎙️ ${x[2]}</a></div>
    <div class="rc-battle" id="bitwy" aria-label="${x[3]}"><div class="rc-vs" aria-hidden="true"><span class="rc-slot">🎙️</span><b>VS</b><span class="rc-slot q">?</span></div>
      <h3>⚔️ ${x[3]}</h3><p>${x[4]}</p><small>🛡️ ${x[5]}</small></div>`;
  return el;
}
function place(){
  if (document.getElementById('casting-pilne')) return true;
  const host = document.getElementById('feedHost') || (document.getElementById('feed') && document.getElementById('feed').parentNode);
  if (!host) return false;
  const first = document.getElementById('feedHost') ? host.firstElementChild : document.getElementById('feed');
  host.insertBefore(build(), first); return true;
}
if (!place()) document.addEventListener('DOMContentLoaded', place);
})();
