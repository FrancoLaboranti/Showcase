// ════════════════════════════════════════════════════════════════════
//  Arcade shell: exit / fullscreen / info wiring + orientation lock +
//  postMessage bridge to the parent shell (when the game runs embedded in the
//  Arcade's iframe). Shared by every game.
//
//  Include it in each game with:
//    <script src="../../Arcade/arcade-shell.js" data-orient="landscape"></script>
//
//  data-orient: 'landscape' | 'portrait' | 'any'. It determines whether the game requests
//  an orientation lock on entering fullscreen. 'any' = no lock.
//
//  Requirements in the game's HTML:
//   · <button id="btnExit">, the ✕ button (in the bar)
//   · <button id="btnFs">, the ⛶ button (in the bar; it carries <g class="ic-enter">/<g class="ic-exit">)
//   · <button id="btnInfo">, the ⓘ button (in the bar) [optional]
//
//  Behaviour:
//   · Embedded in the Arcade's iframe → the parent shell handles fullscreen and
//     orientation; this script only toggles/reflects via postMessage. It hides
//     the ⛶ button (toggling it inside the iframe makes no sense).
//   · Installed PWA, standalone → it tries Fullscreen + an orientation lock on load.
//   · Browser tab → the user's first touch triggers Fullscreen + the lock.
//   · iOS Safari (no lock support) → it fails silently, the default behaviour remains.
// ════════════════════════════════════════════════════════════════════
(function () {
  // Captured when the <script> is evaluated: data-orient="landscape" etc.
  const _script = document.currentScript;
  const ORIENT  = (_script && _script.dataset && _script.dataset.orient) || 'any';
  const EMBEDDED = (window.self !== window.top);
  if (EMBEDDED) document.body.classList.add('embedded');

  // ── Fullscreen + orientation ──
  const fsTarget = document.documentElement;
  const _reqFs  = fsTarget.requestFullscreen || fsTarget.webkitRequestFullscreen;
  const _exitFs = document.exitFullscreen || document.webkitExitFullscreen;
  const isFs    = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
  const isPWA   = () => (window.matchMedia && (matchMedia('(display-mode: fullscreen)').matches
                          || matchMedia('(display-mode: standalone)').matches))
                          || window.navigator.standalone === true;
  const lockOrient = () => {
    if (ORIENT === 'any') return;
    try { const so = screen.orientation; if (so && so.lock) { const p = so.lock(ORIENT); if (p && p.catch) p.catch(() => {}); } } catch {}
  };
  const unlockOrient = () => { try { screen.orientation && screen.orientation.unlock && screen.orientation.unlock(); } catch {} };
  const enterFs = () => {
    let p; try { p = _reqFs && _reqFs.call(fsTarget); } catch { p = null; }
    if (p && p.then) p.then(lockOrient, lockOrient); else lockOrient();
  };
  const exitFs  = () => { unlockOrient(); try { if (_exitFs) _exitFs.call(document); } catch {} };
  function syncFsIcon() { document.body.classList.toggle('fs-on', isFs() || EMBEDDED); }
  document.addEventListener('fullscreenchange', syncFsIcon);
  document.addEventListener('webkitfullscreenchange', syncFsIcon);
  syncFsIcon();

  function tappable(el, fn) { el && el.addEventListener('pointerdown', e => { e.preventDefault(); fn(); }); }
  tappable(document.getElementById('btnFs'), () => {
    if (EMBEDDED) {
      // Same-origin with the Arcade's shell → we call requestFullscreen() DIRECTLY on the
      // parent document to preserve the tap's user activation (postMessage lost it and
      // Chrome rejected the request silently). Falls back to postMessage if it were cross-origin.
      try {
        const topDoc = window.top.document;
        if (topDoc.fullscreenElement || topDoc.webkitFullscreenElement) {
          (topDoc.exitFullscreen || topDoc.webkitExitFullscreen).call(topDoc);
        } else {
          const el = topDoc.documentElement;
          const req = el.requestFullscreen || el.webkitRequestFullscreen;
          const p = req.call(el);
          if (p && p.catch) p.catch(() => {});
        }
      } catch (e) {
        try { window.parent.postMessage({ type: 'arcade:fullscreen' }, '*'); } catch (e2) {}
      }
      return;
    }
    isFs() ? exitFs() : enterFs();
  });
  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'arcade:fs-state') document.body.classList.toggle('fs-on', !!e.data.on);
  });
  if (!EMBEDDED && isPWA()) enterFs();
  let fsOnce = false;
  function tryAutoFs(e) {
    if (fsOnce) return;
    if (e && e.pointerType === 'mouse') return;   // on desktop we do not force it
    if (isFs()) { fsOnce = true; return; }
    enterFs();
  }
  if (!EMBEDDED) document.addEventListener('pointerdown', tryAutoFs, true);
  document.addEventListener('fullscreenchange', () => { if (isFs()) fsOnce = true; });

  // ── Direct exit (no confirmation) ──
  const btnExit = document.getElementById('btnExit');
  if (btnExit) btnExit.addEventListener('click', () => {
    if (EMBEDDED) { try { window.parent.postMessage({ type: 'arcade:exit' }, '*'); } catch (e) {} return; }
    unlockOrient();
    location.href = '../../Arcade/';
  });
})();
