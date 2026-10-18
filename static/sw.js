const C='luna-v4';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/app.js','/style.css','/avatar_round.png','/luna_portrait.jpg','/manifest.json'])));self.skipWaiting();});
self.addEventListener('activate',e=>self.clients.claim());
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(u.pathname.startsWith('/api/'))return;
 e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));});
