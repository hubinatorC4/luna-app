/* Wczesne ustalenie języka (przed CSS i obrazami). Kolejność: zapisany wybór (konto → ciasteczko/localStorage) → język urządzenia
   (navigator.languages; serwer robi to samo z Accept-Language przy pierwszym renderze) → pl. Przekierowanie tylko gdy serwer wyrenderował inny język.
   Pakiet językowy: kody jak w i18n_ext.py (pt = Portugalia, pt-br = Brazylia, zh = chiński uproszczony, no = bokmål). */
(function(){try{
var L=(document.documentElement.getAttribute('data-luna-langs')||'').split(',').filter(Boolean);if(!L.length)L=['pl','en','es','de','uk','fr','it','pt','pt-br','nl','cs','sk','ro','hu','sv','no','da','fi','el','bg','hr','sr','lt','lv','et','tr','ar','he','hi','id','vi','th','ja','ko','zh'],
A={ru:'en',be:'en',nb:'no',nn:'no',iw:'he','in':'id'},s=location.search,p=location.pathname,d=document.documentElement;
if(p==='/app'||p==='/index.html'||p.indexOf('/api')===0||d.hasAttribute('data-app'))return;
if(/[?&]lang=[a-z]{2}/.test(s))return;
function m(c){c=String(c||'').toLowerCase().replace('_','-');if(!c)return'';
 if(c.indexOf('pt-br')===0)return L.indexOf('pt-br')>=0?'pt-br':'';
 if(c.indexOf('zh')===0)return(/hant|-tw|-hk|-mo/.test(c)||L.indexOf('zh')<0)?'':'zh';
 var b=c.split('-')[0];if(L.indexOf(b)>=0)return b;var a=A[b];return a&&L.indexOf(a)>=0?a:'';}
var v=m(localStorage.getItem('luna.lang'));
if(!v){var n=navigator.languages||[navigator.language];for(var i=0;i<n.length&&!v;i++)v=m(n[i]);v=v||'pl';}
var cur=m(d.lang||'pl')||'pl';
if(v!==cur){var u=new URL(location.href);u.searchParams.set('lang',v);location.replace(u);}
}catch(e){}})();
