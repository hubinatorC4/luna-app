/* Wczesne ustalenie języka (przed CSS i obrazami). Kolejność: zapisany wybór (konto → ciasteczko/localStorage) → język urządzenia
   (navigator.languages; serwer robi to samo z Accept-Language przy pierwszym renderze) → pl. Przekierowanie tylko gdy serwer wyrenderował inny język. */
(function(){try{
var L=['pl','en','es','de','uk'],A={ru:'en',be:'en'},s=location.search,p=location.pathname,d=document.documentElement;
if(p==='/app'||p==='/index.html'||p.indexOf('/api')===0||d.hasAttribute('data-app'))return;
var q=(s.match(/[?&]lang=([a-z]{2})/)||[])[1];if(q)return;
function m(c){c=String(c||'').toLowerCase().split(/[-_]/)[0];return L.indexOf(c)>=0?c:(A[c]||'');}
var v=m(localStorage.getItem('luna.lang'));
if(!v){var n=navigator.languages||[navigator.language];for(var i=0;i<n.length&&!v;i++)v=m(n[i]);v=v||'pl';}
var cur=(d.lang||'pl').slice(0,2);
if(v!==cur){var u=new URL(location.href);u.searchParams.set('lang',v);location.replace(u);}
}catch(e){}})();
