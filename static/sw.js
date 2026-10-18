// Luna – service worker. Zmień VERSION przy każdym wydaniu, aby użytkownicy zobaczyli „Dostępna nowa wersja – odśwież”.
const VERSION = '1.2.0';
const C = 'luna-' + VERSION;
const CORE = ['/', '/app.js', '/custom.js', '/music.js', '/profile.js', '/holo.js', '/livechat.js', '/admin.js', '/admin-catalog.js', '/style.css', '/manifest.json', '/avatar-256.jpg', '/avatar-512.jpg', '/icon-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(CORE)).catch(() => {})); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/') || u.pathname.startsWith('/music/')) return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok && CORE.includes(u.pathname)) { const cl = r.clone(); caches.open(C).then(c => c.put(e.request, cl)); } return r; })
    .catch(() => caches.match(e.request)));
});
