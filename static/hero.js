(() => { const b = document.getElementById('heroListen'), a = document.getElementById('heroAudio'), r = document.querySelector('.sh-ring') || document.querySelector('.sc-hero');
if (!b || !a) return;
b.onclick = () => { if (a.paused){ a.currentTime = 0; a.play().catch(() => {}); } else a.pause(); };
a.onplay = () => { if (r) r.classList.add('speaking'); }; a.onpause = a.onended = () => { if (r) r.classList.remove('speaking'); }; })();
