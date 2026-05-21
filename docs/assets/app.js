/* ------------------------------------------------------------------ *
 *  awesome-skills — site interactions
 *  - copy buttons
 *  - scroll-triggered reveal
 * ------------------------------------------------------------------ */

(() => {
  'use strict';

  /* ----- copy buttons -------------------------------------------- */
  const tiles = document.querySelectorAll('[data-copy]');
  tiles.forEach((tile) => {
    const btn = tile.querySelector('[data-copy-btn]');
    if (!btn) return;
    const text = tile.getAttribute('data-copy');
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(text);
        const prev = btn.textContent;
        btn.textContent = 'Copied';
        btn.setAttribute('data-state', 'copied');
        setTimeout(() => {
          btn.textContent = prev;
          btn.removeAttribute('data-state');
        }, 1600);
      } catch (e) {
        btn.textContent = 'Press ⌘C';
        setTimeout(() => (btn.textContent = 'Copy'), 1600);
      }
    });
  });

  /* ----- reveal on scroll ---------------------------------------- */
  const targets = document.querySelectorAll('.reveal, .reveal-stagger');
  if ('IntersectionObserver' in window && targets.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
    );
    targets.forEach((t) => io.observe(t));
  } else {
    targets.forEach((t) => t.classList.add('in'));
  }
})();
