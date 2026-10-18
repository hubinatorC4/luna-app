/* Klient bezpieczeństwa Luny (dołączany przez serwer do stron HTML, bez zmian w innych skryptach):
   1) 2FA: gdy logowanie zwróci „totp_required”, pyta o 6-cyfrowy kod i ponawia logowanie;
   2) Cloudflare Turnstile (darmowa alternatywa CAPTCHA) – działa TYLKO, gdy serwer ma klucze TURNSTILE_SITEKEY/SECRET;
      dokłada świeży token do rejestracji, logowania i formularzy. */
(() => {
  const PROTECTED = ['/api/account/signup', '/api/account/login', '/api/join', '/api/testers/signup', '/api/tickets'];
  const orig = window.fetch.bind(window); let ready = null, wid = null, waiters = [];
  function load(sitekey){
    if (ready) return ready;
    ready = new Promise((res, rej) => {
      window.__lunaTs = () => {
        const box = document.createElement('div'); box.id = 'luna-ts';
        box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483000;border-radius:14px;overflow:hidden';
        document.body.appendChild(box);
        wid = turnstile.render(box, {sitekey, execution: 'execute', appearance: 'interaction-only', theme: 'dark',
          callback: t => { const w = waiters; waiters = []; w.forEach(f => f(t)); },
          'error-callback': () => { const w = waiters; waiters = []; w.forEach(f => f('')); }});
        res();
      };
      const s = document.createElement('script');
      s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__lunaTs'; s.async = true; s.onerror = rej;
      document.head.appendChild(s);
    });
    return ready;
  }
  let key = null, cfg = null;  /* konfigurację pobieramy dopiero przy pierwszym chronionym formularzu */
  async function token(){
    cfg = cfg || orig('/api/config').then(r => r.json()).then(c => (key = c.turnstile || '')).catch(() => (key = ''));
    await cfg; if (!key) return '';
    try { await load(key); } catch(e){ return ''; }
    return new Promise(res => { waiters.push(res); try { turnstile.reset(wid); turnstile.execute(wid); } catch(e){ res(''); } setTimeout(() => res(''), 30000); });
  }
  window.fetch = async (input, init) => {
    try {
      const url = new URL(typeof input === 'string' ? input : input.url, location.href);
      const m = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
      if (m === 'POST' && url.origin === location.origin && PROTECTED.includes(url.pathname)){
        const t = await token();
        if (t){ init = Object.assign({}, init); const h = new Headers((init && init.headers) || {}); h.set('CF-Turnstile-Response', t); init.headers = h; }
      }
    } catch(e){}
    let r = await orig(input, init);
    try {
      const url = new URL(typeof input === 'string' ? input : input.url, location.href);
      if (url.pathname === '/api/account/login' && r.status === 401 && init && typeof init.body === 'string'){
        const d = await r.clone().json();
        if (d && d.totp_required){
          const L = (document.documentElement.lang || 'pl').slice(0, 2);
          const q = {pl: 'Kod 2FA z aplikacji uwierzytelniającej (6 cyfr):', en: '2FA code from your authenticator app (6 digits):', de: '2FA-Code aus deiner Authenticator-App (6 Ziffern):', es: 'Código 2FA de tu app de autenticación (6 dígitos):', uk: 'Код 2FA із застосунку автентифікації (6 цифр):'}[L] || '2FA code:';
          const code = (window.prompt(q) || '').replace(/\s/g, '');
          if (/^\d{6}$/.test(code)){ const b = JSON.parse(init.body); b.totp = code; return window.fetch(input, Object.assign({}, init, {body: JSON.stringify(b)})); }
        }
      }
    } catch(e){}
    return r;
  };
})();
