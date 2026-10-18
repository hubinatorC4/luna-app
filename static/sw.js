// Luna – service worker. Zmień VERSION przy każdym wydaniu, aby użytkownicy zobaczyli „Dostępna nowa wersja – odśwież”.
const VERSION = '1.5.5';
const C = 'luna-' + VERSION;
const CORE = ['/app', '/app.js', '/custom.js', '/music.js', '/profile.js', '/holo.js', '/livechat.js', '/push.js', '/testers.js', '/admin.js', '/admin-catalog.js', '/style.css', '/manifest.json', '/avatar-256.jpg', '/avatar-512.jpg', '/icon-192.png', '/app.html', '/app-shell.js', '/app-shell-i18n.js', '/app-shell.css', '/app-redirect.js'];
self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(CORE)).catch(() => {})); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/') || u.pathname.startsWith('/music/')) return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok && CORE.includes(u.pathname)) { const cl = r.clone(); caches.open(C).then(c => c.put(e.request, cl)); } return r; })
    .catch(() => caches.match(e.request)));
});

// ---------- Web Push ----------
self.addEventListener('push', e => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch(x){ d = {title: 'Luna', body: e.data && e.data.text()}; }
  e.waitUntil(self.registration.showNotification(d.title || 'Luna', {body: d.body || '', icon: '/icon-192.png', badge: '/favicon-48.png', tag: d.tag || 'luna', data: {url: d.url || '/'}}));
});
self.addEventListener('notificationclick', e => {
  e.notification.close(); const url = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(cs => { for (const c of cs){ if (new URL(c.url).pathname === url && 'focus' in c) return c.focus(); } return clients.openWindow(url); }));
});
