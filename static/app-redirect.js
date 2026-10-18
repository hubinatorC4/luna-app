/* v1.4: zainstalowana aplikacja (Google Play / ekran początkowy) otwiera nową powłokę /app.html. Strona w przeglądarce działa bez zmian. */
(function(){try{
  var q = location.search, top = window.top === window.self;
  var installed = /[?&]source=(twa|pwa)\b/.test(q) || document.documentElement.classList.contains('twa') || (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  if (top && installed && !/[?&](embed|classic)=/.test(q)) location.replace('/app.html' + q + location.hash);
  else if (!top) document.documentElement.classList.add('embedded');
  else if (!/[?&]lang=/.test(q)){ var sv = localStorage.getItem('luna.lang'); if (sv && sv !== 'pl' && /^(en|es|de|uk)$/.test(sv)) location.replace(location.pathname + (q ? q + '&' : '?') + 'lang=' + sv + location.hash); }
}catch(e){}})();
