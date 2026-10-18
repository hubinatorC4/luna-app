/* „▶ Posłuchaj Luny” na stronie głównej: krótkie powitanie głosem Luny z /api/tts w języku strony (plik luna_powitanie.mp3 nigdy nie istniał – był 404). */
(() => { const b = document.getElementById('heroListen'), a = document.getElementById('heroAudio'), r = document.querySelector('.sh-ring') || document.querySelector('.sc-hero');
if (!b || !a) return;
const L = (document.documentElement.lang || 'pl').slice(0, 2);
const G = {pl: ['Cześć, jestem Luna – asystentka AI. Pomogę Ci mówić pewniej i wyraźniej. Wypróbuj aplikację i sprawdź, jak brzmisz!', ''],
  en: ['Hi, I’m Luna, an AI assistant. I’ll help you speak with more confidence and clarity. Try the app and hear how you sound!', 'en-US-AvaMultilingualNeural'],
  de: ['Hallo, ich bin Luna, eine KI-Assistentin. Ich helfe dir, sicherer und deutlicher zu sprechen. Probier die App aus!', 'de-DE-SeraphinaMultilingualNeural'],
  es: ['Hola, soy Luna, una asistente de IA. Te ayudo a hablar con más seguridad y claridad. ¡Prueba la app!', 'es-ES-XimenaNeural'],
  uk: ['Привіт, я Луна, ШІ-асистентка. Я допоможу тобі говорити впевненіше й чіткіше. Спробуй застосунок!', 'en-US-AvaMultilingualNeural']}[L] || null;
const src = () => { const g = G || ['Cześć, jestem Luna – asystentka AI. Pomogę Ci mówić pewniej i wyraźniej.', '']; const p = new URLSearchParams({text: g[0]}); if (g[1]){ p.set('voice', g[1]); p.set('spanish', '0'); p.set('lisp', '0'); } return '/api/tts?' + p; };
const busy = on => { b.setAttribute('aria-busy', String(on)); b.classList.toggle('busy', on); };
b.onclick = () => {
  if (!a.paused){ a.pause(); return; }
  if (!a.dataset.ready){ a.src = src(); a.dataset.ready = '1'; busy(true); }
  a.currentTime = 0; a.play().catch(() => busy(false));
};
a.onplaying = () => busy(false); a.onerror = () => { busy(false); a.dataset.ready = ''; };
a.onplay = () => { if (r) r.classList.add('speaking'); }; a.onpause = a.onended = () => { if (r) r.classList.remove('speaking'); }; })();
