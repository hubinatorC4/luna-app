/* Wczesne przekierowanie na zapamiętany język (przed pobraniem CSS i obrazów). Reszta: langswitch.js. */
(function(){try{
var L=['pl','en','es','de','uk'],s=location.search,p=location.pathname;
if(p==='/app'||p==='/index.html'||p.indexOf('/api')===0||document.documentElement.hasAttribute('data-app'))return;
var q=(s.match(/[?&]lang=([a-z]{2})/)||[])[1];if(q)return;
var v=localStorage.getItem('luna.lang');
if(!v){var n=(navigator.language||'pl').slice(0,2).toLowerCase();v=L.indexOf(n)>=0?n:'pl';localStorage.setItem('luna.lang',v);}
if(v!=='pl'&&L.indexOf(v)>=0){var u=new URL(location.href);u.searchParams.set('lang',v);location.replace(u);}
}catch(e){}})();
