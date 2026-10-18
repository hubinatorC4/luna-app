/* Zgłoś 🚩 – jedno okienko zgłoszeń dla całej Luny (strona i aplikacja), 5 języków.
   Przejmuje istniejące przyciski „Zgłoś/⚑” (data-report, czat bitwy, DM, znajomi), dokłada 🚩 na zdjęciach
   i otwiera animowany arkusz od dołu (sprężynka; bez animacji przy „ogranicz ruch”).
   API: window.LunaReport.open({type, id}) – type: post|cmt|agent|item|btchat|dm|user|photo. */
(() => {
  if (window.LunaReport) return;
  const L5 = ['pl', 'en', 'es', 'de', 'uk'];
  const lang = () => { const q = new URLSearchParams(location.search).get('lang'); const l = (q || document.documentElement.lang || navigator.language || 'pl').slice(0, 2); return L5.includes(l) ? l : 'pl'; };
  const S = {
    title: ['Zgłoś 🚩', 'Report 🚩', 'Denunciar 🚩', 'Melden 🚩', 'Поскаржитися 🚩'],
    sub: ['Co jest nie tak? Jedno stuknięcie wystarczy – resztą zajmie się człowiek.', 'What’s wrong? One tap is enough – a human takes it from there.', '¿Qué pasa? Basta con un toque: del resto se encarga una persona.', 'Was stimmt nicht? Ein Tipp genügt – den Rest übernimmt ein Mensch.', 'Що не так? Досить одного дотику – далі розбереться людина.'],
    about: ['Zgłaszasz:', 'You’re reporting:', 'Denuncias:', 'Du meldest:', 'Ви скаржитеся на:'],
    what: {post: ['wpis', 'a post', 'una publicación', 'einen Beitrag', 'допис'], cmt: ['komentarz', 'a comment', 'un comentario', 'einen Kommentar', 'коментар'], agent: ['profil agentki', 'an agent profile', 'un perfil de agente', 'ein Agentinnen-Profil', 'профіль агентки'],
      item: ['produkt', 'a product', 'un producto', 'ein Produkt', 'товар'], btchat: ['wiadomość na czacie bitwy', 'a battle chat message', 'un mensaje del chat de batalla', 'eine Battle-Chat-Nachricht', 'повідомлення в чаті битви'],
      dm: ['wiadomość prywatną', 'a private message', 'un mensaje privado', 'eine private Nachricht', 'приватне повідомлення'], user: ['profil użytkownika', 'a user profile', 'un perfil de usuario', 'ein Nutzerprofil', 'профіль користувача'], photo: ['zdjęcie', 'a photo', 'una foto', 'ein Foto', 'фото']},
    cats: [['harass', '😠', ['Nękanie/obrażanie', 'Harassment/insults', 'Acoso/insultos', 'Belästigung/Beleidigung', 'Цькування/образи']],
      ['spam', '🎣', ['Spam/oszustwo', 'Spam/fraud', 'Spam/estafa', 'Spam/Betrug', 'Спам/шахрайство']],
      ['fake', '🎭', ['Fałszywe konto/podszywanie', 'Fake account/impersonation', 'Cuenta falsa/suplantación', 'Fake-Konto/Identitätsdiebstahl', 'Фейковий акаунт/видавання себе за іншого']],
      ['nudity', '🙈', ['Nieodpowiednie zdjęcie/nagość', 'Inappropriate photo/nudity', 'Foto inapropiada/desnudez', 'Unangemessenes Foto/Nacktheit', 'Неприйнятне фото/оголеність']],
      ['minor', '🧸', ['Osoba niepełnoletnia', 'Minor (under 18)', 'Persona menor de edad', 'Minderjährige Person', 'Неповнолітня особа']],
      ['doxx', '🔐', ['Ujawnianie danych', 'Sharing private data', 'Divulgación de datos', 'Weitergabe privater Daten', 'Розголошення даних']],
      ['other', '💭', ['Inne', 'Other', 'Otro', 'Sonstiges', 'Інше']]],
    note: ['Dopisz coś, jeśli chcesz (opcjonalnie)', 'Add a note if you like (optional)', 'Añade algo si quieres (opcional)', 'Schreib etwas dazu, wenn du magst (optional)', 'Додайте коментар, якщо хочете (необов’язково)'],
    block: ['Zablokuj tego użytkownika', 'Block this user', 'Bloquear a este usuario', 'Diese Person blockieren', 'Заблокувати цього користувача'],
    anon: ['🤫 Zgłoszenie jest anonimowe – autor nigdy nie dowie się, kto zgłosił.', '🤫 Reports are anonymous – the author never learns who reported.', '🤫 La denuncia es anónima: el autor nunca sabrá quién fue.', '🤫 Meldungen sind anonym – die Person erfährt nie, wer gemeldet hat.', '🤫 Скарга анонімна – автор ніколи не дізнається, хто поскаржився.'],
    send: ['Wyślij zgłoszenie', 'Send report', 'Enviar denuncia', 'Meldung senden', 'Надіслати скаргу'],
    cancel: ['Anuluj', 'Cancel', 'Cancelar', 'Abbrechen', 'Скасувати'], close: ['Zamknij', 'Close', 'Cerrar', 'Schließen', 'Закрити'],
    pick: ['Wybierz powód – jedno stuknięcie 🙂', 'Pick a reason – one tap 🙂', 'Elige un motivo: un toque 🙂', 'Wähle einen Grund – ein Tipp 🙂', 'Оберіть причину – один дотик 🙂'],
    done: ['Moderator już zakłada okulary 🕵️', 'The moderator is putting on their glasses 🕵️', 'El moderador ya se está poniendo las gafas 🕵️', 'Die Moderation setzt schon die Brille auf 🕵️', 'Модератор уже надягає окуляри 🕵️'],
    done2: ['Dziękujemy! Sprawdzimy to po cichu, a o decyzji napiszemy w Skrzynce.', 'Thank you! We’ll check it quietly and tell you the decision in your Inbox.', '¡Gracias! Lo revisaremos con discreción y te contaremos la decisión en tu Buzón.', 'Danke! Wir prüfen das diskret und schreiben dir die Entscheidung ins Postfach.', 'Дякуємо! Перевіримо тихенько, а про рішення напишемо у Скриньці.'],
    strikes: ['Trzy poważne naruszenia i Luna mówi pa pa – na zawsze 👋 (a za najcięższe – od razu).', 'Three serious violations and Luna waves bye-bye – forever 👋 (the very worst: right away).', 'Tres infracciones graves y Luna dice adiós para siempre 👋 (las peores: de inmediato).', 'Drei schwere Verstöße und Luna winkt zum Abschied – für immer 👋 (bei den schlimmsten: sofort).', 'Три серйозні порушення – і Луна каже «бувай» назавжди 👋 (за найтяжчі – одразу).'],
    hidden: ['Treść jest już ukryta do czasu decyzji.', 'The content is now hidden until a decision.', 'El contenido ya está oculto hasta la decisión.', 'Der Inhalt ist bis zur Entscheidung ausgeblendet.', 'Вміст приховано до ухвалення рішення.'],
    dup: ['To już zgłosiłaś/eś – moderator ma to na liście 📝', 'You already reported this – it’s on the moderator’s list 📝', 'Ya lo denunciaste: está en la lista del moderador 📝', 'Schon gemeldet – steht auf der Liste der Moderation 📝', 'Ви вже поскаржилися – це в списку модератора 📝'],
    blocked: ['Zablokowano – ta osoba nie napisze już do Ciebie.', 'Blocked – this person can’t message you any more.', 'Bloqueado: esta persona ya no podrá escribirte.', 'Blockiert – diese Person kann dir nicht mehr schreiben.', 'Заблоковано – ця людина більше не напише вам.'],
    login: ['Zaloguj się, aby to zgłosić.', 'Sign in to report this.', 'Inicia sesión para denunciarlo.', 'Melde dich an, um das zu melden.', 'Увійдіть, щоб поскаржитися.'],
    err: ['Ups, coś nie wyszło – spróbuj za chwilę.', 'Oops, something went wrong – try again shortly.', 'Uy, algo falló: inténtalo en un momento.', 'Hoppla, das hat nicht geklappt – versuch es gleich nochmal.', 'Ой, щось пішло не так – спробуйте трохи згодом.'],
    rules: ['Zasady', 'Rules', 'Normas', 'Regeln', 'Правила'], photo: ['Zgłoś zdjęcie', 'Report photo', 'Denunciar foto', 'Foto melden', 'Поскаржитися на фото'],
  };
  const t = k => { const v = S[k]; const i = L5.indexOf(lang()); return Array.isArray(v) ? (v[i] || v[0]) : v; };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const CSS = `
.lr-back{position:fixed;inset:0;z-index:2147482000;background:rgba(8,10,14,.55);backdrop-filter:blur(3px);display:flex;align-items:flex-end;justify-content:center;opacity:0;transition:opacity .2s}
.lr-back.on{opacity:1}
.lr-sheet{width:min(560px,100%);max-height:92vh;overflow:auto;background:linear-gradient(180deg,#1d1a22,#141318);color:#f4f1f6;border-radius:28px 28px 0 0;padding:10px 18px calc(18px + env(safe-area-inset-bottom));box-shadow:0 -12px 50px rgba(0,0,0,.45);transform:translateY(105%);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.lr-back.on .lr-sheet{animation:lrUp .52s cubic-bezier(.34,1.56,.64,1) forwards}
@media (min-width:720px){.lr-back{align-items:center}.lr-sheet{border-radius:28px;transform:scale(.86)}.lr-back.on .lr-sheet{animation:lrPop .48s cubic-bezier(.34,1.56,.64,1) forwards}}
@keyframes lrUp{to{transform:translateY(0)}}@keyframes lrPop{from{transform:scale(.86);opacity:.4}to{transform:scale(1);opacity:1}}
.lr-grab{width:44px;height:5px;border-radius:9px;background:rgba(255,255,255,.22);margin:2px auto 10px}
.lr-sheet h2{margin:0 0 2px;font-size:20px}.lr-sub{margin:0 0 10px;color:#c9c2cf;font-size:14px}.lr-about{font-size:13px;color:#ffb3c7;margin:0 0 10px}
.lr-cats{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.lr-cat{display:flex;gap:8px;align-items:center;text-align:left;padding:12px 12px;border-radius:18px;border:1.5px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:inherit;font:inherit;font-size:14px;cursor:pointer;transition:transform .18s,border-color .18s,background .18s}
.lr-cat:hover{border-color:rgba(255,120,160,.5)}.lr-cat[aria-pressed=true]{border-color:#ff6f9c;background:rgba(255,111,156,.16);transform:scale(1.03)}
.lr-cat .e{font-size:20px}.lr-cat.wide{grid-column:1/-1}
.lr-note{width:100%;box-sizing:border-box;margin:10px 0 2px;min-height:64px;border-radius:16px;border:1.5px solid rgba(255,255,255,.12);background:rgba(0,0,0,.25);color:inherit;padding:10px 12px;font:inherit;resize:vertical}
.lr-cnt{font-size:12px;color:#9c94a3;text-align:right}.lr-blk{display:flex;gap:8px;align-items:center;margin:6px 0;font-size:14px}.lr-blk input{width:20px;height:20px;accent-color:#ff6f9c}
.lr-anon{font-size:12.5px;color:#b9b1bf;margin:8px 0}.lr-err{color:#ffb4a8;font-size:13.5px;min-height:1.2em;margin:4px 0}
.lr-row{display:flex;gap:10px;margin-top:8px}.lr-row button{flex:1;padding:13px 14px;border-radius:999px;border:0;font:inherit;font-weight:700;cursor:pointer}
.lr-go{background:linear-gradient(135deg,#ff6f9c,#ff9a3c);color:#1b0f14}.lr-go:disabled{opacity:.5;cursor:default}.lr-no{background:rgba(255,255,255,.08);color:inherit}
.lr-done{text-align:center;padding:14px 4px 6px}.lr-spy{position:relative;display:inline-block;font-size:64px;line-height:1;animation:lrBob 1.6s ease-in-out infinite}
.lr-spy .g{position:absolute;left:50%;top:-34px;font-size:34px;transform:translateX(-50%);animation:lrGl .9s .25s cubic-bezier(.34,1.56,.64,1) forwards}
@keyframes lrGl{to{top:14px}}@keyframes lrBob{50%{transform:translateY(-6px) rotate(-3deg)}}
.lr-done h3{margin:12px 0 4px;font-size:19px}.lr-done p{margin:4px 0;color:#d4cdd8;font-size:14px}.lr-done .lr-3{color:#ffd59e;font-size:13px}
.lr-done a{color:#ff9cbc}.lr-ts{margin:8px 0}
.lr-ph{position:absolute;top:8px;left:8px;z-index:3;width:34px;height:34px;border-radius:50%;border:0;background:rgba(10,10,14,.55);color:#fff;font-size:15px;cursor:pointer;opacity:.82;backdrop-filter:blur(4px)}
.lr-ph:hover,.lr-ph:focus-visible{opacity:1}.lr-wrap{position:relative;display:block}
.lr-gone{opacity:.45;transition:opacity .3s}
@media (prefers-reduced-motion:reduce){.lr-back,.lr-back.on .lr-sheet,.lr-spy,.lr-spy .g,.lr-cat{animation:none!important;transition:none!important}.lr-back.on .lr-sheet{transform:none}.lr-spy .g{top:14px}}`;
  let ME = null, CSRF = '', TSKEY = null;
  async function me(){ if (ME !== null) return ME;
    try { const d = await (await fetch('/api/account/me', {credentials: 'same-origin'})).json(); ME = d.user || false; CSRF = d.csrf || ''; } catch(e){ ME = false; }
    return ME; }
  async function tsKey(){ if (TSKEY !== null) return TSKEY; try { TSKEY = (await (await fetch('/api/config')).json()).turnstile || ''; } catch(e){ TSKEY = ''; } return TSKEY; }
  function parse(v){ const s = String(v || ''); const i = s.indexOf(':'); if (i < 0) return null; let type = s.slice(0, i), id = s.slice(i + 1);
    if (type === 'home') type = 'item';
    return {type, id}; }
  let open_ = null;
  async function openSheet(o, src){
    if (open_ || !o || !o.type || !o.id) return;
    if (!document.getElementById('lrCss')){ const st = document.createElement('style'); st.id = 'lrCss'; st.textContent = CSS; document.head.appendChild(st); }
    const user = await me();
    const back = document.createElement('div'); back.className = 'lr-back'; open_ = back;
    const what = (S.what[o.type] || S.what.post)[L5.indexOf(lang())] || '';
    const canBlock = !!user && ['post', 'cmt', 'btchat', 'dm', 'user', 'photo', 'agent'].includes(o.type);
    back.innerHTML = `<div class="lr-sheet" role="dialog" aria-modal="true" aria-labelledby="lrT"><div class="lr-grab" aria-hidden="true"></div>
      <h2 id="lrT">${esc(t('title'))}</h2><p class="lr-sub">${esc(t('sub'))}</p><p class="lr-about">${esc(t('about'))} <b>${esc(what)}</b></p>
      <div class="lr-cats" role="group" aria-label="${esc(t('title'))}">${S.cats.map(([k, e, n], i) => `<button type="button" class="lr-cat${i === 6 ? ' wide' : ''}" data-c="${k}" aria-pressed="false"><span class="e" aria-hidden="true">${e}</span><span>${esc(n[L5.indexOf(lang())] || n[0])}</span></button>`).join('')}</div>
      <textarea class="lr-note" maxlength="500" placeholder="${esc(t('note'))}" aria-label="${esc(t('note'))}"></textarea><div class="lr-cnt"><span>0</span>/500</div>
      ${canBlock ? `<label class="lr-blk"><input type="checkbox" class="lr-bk"> ${esc(t('block'))}</label>` : ''}
      <div class="lr-ts"></div><p class="lr-anon">${esc(t('anon'))}</p><p class="lr-err" role="alert"></p>
      <div class="lr-row"><button type="button" class="lr-no">${esc(t('cancel'))}</button><button type="button" class="lr-go" disabled>${esc(t('send'))}</button></div></div>`;
    document.body.appendChild(back); requestAnimationFrame(() => back.classList.add('on'));
    const sh = back.querySelector('.lr-sheet'); let cat = '', ts = '';
    const prev = document.activeElement;
    const close = () => { back.classList.remove('on'); setTimeout(() => back.remove(), 200); open_ = null; document.removeEventListener('keydown', key, true); try { prev && prev.focus(); } catch(e){} };
    const key = e => { if (e.key === 'Escape'){ e.preventDefault(); close(); } };
    document.addEventListener('keydown', key, true);
    back.addEventListener('click', e => { if (e.target === back) close(); });
    back.querySelector('.lr-no').onclick = close;
    const go = back.querySelector('.lr-go'), err = back.querySelector('.lr-err'), note = back.querySelector('.lr-note');
    note.oninput = () => { back.querySelector('.lr-cnt span').textContent = note.value.length; };
    back.querySelectorAll('.lr-cat').forEach(b => b.onclick = () => { cat = b.dataset.c; back.querySelectorAll('.lr-cat').forEach(x => x.setAttribute('aria-pressed', String(x === b))); go.disabled = false; err.textContent = ''; });
    setTimeout(() => { const f = back.querySelector('.lr-cat'); f && f.focus({preventScroll: true}); }, 60);
    if (!user){
      if (o.type === 'dm' || o.type === 'user'){ err.textContent = t('login'); go.disabled = true; back.querySelectorAll('.lr-cat').forEach(b => b.disabled = true); }
      const k = await tsKey();
      if (k) new Promise((ok, no) => { if (window.turnstile) return ok(); const s = document.createElement('script'); s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'; s.async = true; s.onload = ok; s.onerror = no; document.head.appendChild(s); })
        .then(() => window.turnstile.render(back.querySelector('.lr-ts'), {sitekey: k, theme: 'dark', language: lang(), callback: v => { ts = v; }})).catch(() => {});
    }
    go.onclick = async () => {
      if (!cat){ err.textContent = t('pick'); return; }
      go.disabled = true; err.textContent = '';
      const bk = back.querySelector('.lr-bk');
      const h = {'Content-Type': 'application/json'}; if (CSRF) h['X-CSRF-Token'] = CSRF;
      try {
        const r = await fetch('/api/report', {method: 'POST', credentials: 'same-origin', headers: h, body: JSON.stringify({type: o.type, id: o.id, cat, note: note.value.slice(0, 500), block: !!(bk && bk.checked), cf_turnstile: ts, website: ''})});
        const d = await r.json().catch(() => ({}));
        if (!r.ok){ err.textContent = d.login ? t('login') : (d.error || t('err')); go.disabled = false; if (window.turnstile) try { window.turnstile.reset(); } catch(e){} return; }
        sh.innerHTML = `<div class="lr-grab" aria-hidden="true"></div><div class="lr-done" role="status"><span class="lr-spy" aria-hidden="true">🕵️<span class="g">👓</span></span>
          <h3>${esc(d.dup ? t('dup') : t('done'))}</h3><p>${esc(t('done2'))}</p>${d.hidden ? `<p>${esc(t('hidden'))}</p>` : ''}${d.blocked ? `<p>${esc(t('blocked'))}</p>` : ''}
          <p class="lr-3">${esc(t('strikes'))} <a href="/regulamin.html#naruszenia" target="_blank" rel="noopener">${esc(t('rules'))}</a></p>
          <div class="lr-row"><button type="button" class="lr-go lr-x">${esc(t('close'))}</button></div></div>`;
        sh.querySelector('.lr-x').onclick = close; sh.querySelector('.lr-x').focus({preventScroll: true});
        if (src){ const c = src.closest('.bt-m, .ib-bub, [data-mid], .cmt, article, .wl-card, .post, li'); if (c) c.classList.add('lr-gone'); }
        setTimeout(() => { if (open_ === back) close(); }, 5200);
      } catch(e){ err.textContent = t('err'); go.disabled = false; }
    };
  }
  // ---- przejęcie istniejących przycisków (faza capture: stare okienka prompt/confirm się nie pokazują) ----
  function fromEl(el){
    const r = el.closest('[data-report]'); if (r) return parse(r.dataset.report);
    return null;
  }
  window.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-report], .lr-ph'); if (!b) return;
    const o = b.classList.contains('lr-ph') ? parse(b.dataset.lr) : fromEl(b); if (!o) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); openSheet(o, b);
  }, true);
  // ---- 🚩 na zdjęciach: wpisy Ścianki i profil agentki ----
  function decorate(root){
    (root.querySelectorAll ? root : document).querySelectorAll('img.wl-media, figure.media > img, .ph-grid > img, img.ph-main').forEach(img => {
      if (img.dataset.lrDone) return; img.dataset.lrDone = '1';
      const card = img.closest('article, .wl-card, .post, .ph-card, section, li') || document.body;
      const rb = card.querySelector('[data-report]'); if (!rb) return;
      const o = parse(rb.dataset.report); if (!o || !['post', 'agent'].includes(o.type)) return;
      let host = img.parentElement; if (host.tagName !== 'FIGURE'){ const w = document.createElement('span'); w.className = 'lr-wrap'; img.replaceWith(w); w.appendChild(img); host = w; }
      if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
      const f = document.createElement('button'); f.type = 'button'; f.className = 'lr-ph'; f.textContent = '🚩'; f.title = f.ariaLabel = t('photo');
      f.dataset.lr = 'photo:' + o.type + ':' + o.id; host.appendChild(f);
    });
  }
  const startObs = () => { decorate(document); new MutationObserver(m => { for (const x of m) for (const n of x.addedNodes) if (n.nodeType === 1) decorate(n); }).observe(document.body, {childList: true, subtree: true}); };
  if (!document.getElementById('lrCss')){ const st = document.createElement('style'); st.id = 'lrCss'; st.textContent = CSS; document.head.appendChild(st); }
  if (document.body) startObs(); else document.addEventListener('DOMContentLoaded', startObs);
  window.LunaReport = {open: o => openSheet(o, null), parse, S};
})();
