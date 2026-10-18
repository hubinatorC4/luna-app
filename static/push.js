/* Luna – zapis na powiadomienia push (przypomnienia o Luna Live, nowe wideo, aktualizacje). Przyciski: [data-push]. */
(() => {
const ok = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
const b64 = s => { const p = '='.repeat((4 - s.length % 4) % 4); const r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...r].map(c => c.charCodeAt(0))); };
let key = null, enabled = false;
const btns = () => document.querySelectorAll('[data-push]');
function label(t, on){ btns().forEach(b => { b.textContent = t; b.classList.toggle('on', !!on); }); }
async function current(){ if (!ok) return null; const r = await navigator.serviceWorker.getRegistration('/'); return r ? r.pushManager.getSubscription() : null; }
async function state(){
  if (!ok){ label('🔔 Powiadomienia niedostępne w tej przeglądarce'); return; }
  if (!enabled){ label('🔔 Powiadomienia – wkrótce'); return; }
  if (Notification.permission === 'denied'){ label('🔕 Powiadomienia zablokowane w przeglądarce'); return; }
  const s = await current(); label(s ? '🔔 Powiadomienia włączone' : '🔔 Powiadom mnie', !!s);
}
async function toggle(){
  if (!ok || !enabled) return alert(!ok ? 'Ta przeglądarka nie obsługuje powiadomień push. Na iPhonie dodaj Lunę do ekranu początkowego.' : 'Powiadomienia push zostaną uruchomione wkrótce.');
  const s = await current();
  if (s){ if (!confirm('Wyłączyć powiadomienia od Luny?')) return; await fetch('/api/push/unsubscribe', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({sub: s.toJSON()})}); await s.unsubscribe(); return state(); }
  const perm = await Notification.requestPermission(); if (perm !== 'granted') return state();
  const reg = await navigator.serviceWorker.register('/sw.js'); await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64(key)});
  const r = await fetch('/api/push/subscribe', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({sub: sub.toJSON(), topics: ['live', 'video', 'update']})});
  if (!r.ok){ await sub.unsubscribe(); alert('Nie udało się zapisać na powiadomienia.'); }
  state();
}
document.addEventListener('click', e => { const b = e.target.closest('[data-push]'); if (b){ e.preventDefault(); toggle().catch(err => alert('Błąd: ' + err.message)); } });
fetch('/api/push/key').then(r => r.json()).then(d => { enabled = d.enabled; key = d.key; state(); }).catch(() => state());
window.LunaPushState = state;
})();
