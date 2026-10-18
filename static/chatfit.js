/* Po pierwszej wiadomości w czacie dodaje body.chatting (zwija hero na telefonach, więcej miejsca na rozmowę). */
(() => { const c = document.getElementById('chat'); if (!c) return;
  const f = () => document.body.classList.toggle('chatting', c.querySelectorAll('.msgrow').length > 1);
  new MutationObserver(f).observe(c, {childList: true}); f(); })();
