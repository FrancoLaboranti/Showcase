// ════════════════════════════════════════════════════════════════════
//  Arcade shell — exit / fullscreen / info wiring + orientation lock +
//  postMessage bridge a la shell padre (cuando el juego corre embebido en el
//  iframe del Arcade). Compartido entre todos los juegos.
//
//  Incluir en cada juego con:
//    <script src="../../Arcade/arcade-shell.js" data-orient="landscape"></script>
//
//  data-orient: 'landscape' | 'portrait' | 'any'. Determina si el juego pide
//  un lock de orientación al entrar en fullscreen. 'any' = sin lock.
//
//  Requisitos en el HTML del juego:
//   · <button id="btnExit"> — botón ✕ (en el bar)
//   · <button id="btnFs">   — botón ⛶ (en el bar; lleva <g class="ic-enter">/<g class="ic-exit">)
//   · <button id="btnInfo"> — botón ⓘ (en el bar) [opcional]
//
//  Comportamiento:
//   · Embebido en el iframe del Arcade → la shell padre maneja fullscreen y
//     orientación; este script sólo togglea/refleja vía postMessage. Oculta
//     el botón ⛶ (no tiene sentido togglearlo dentro del iframe).
//   · PWA instalada suelta → intenta Fullscreen + lock de orientación al cargar.
//   · Pestaña del browser → el primer toque del usuario dispara Fullscreen + lock.
//   · iOS Safari (no soporta lock) → falla silencioso, queda el comportamiento default.
// ════════════════════════════════════════════════════════════════════
(function () {
  // Capturado al evaluar el <script>: data-orient="landscape" etc.
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
    if (EMBEDDED) { try { window.parent.postMessage({ type: 'arcade:fullscreen' }, '*'); } catch (e) {} return; }
    isFs() ? exitFs() : enterFs();
  });
  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'arcade:fs-state') document.body.classList.toggle('fs-on', !!e.data.on);
  });
  if (!EMBEDDED && isPWA()) enterFs();
  let fsOnce = false;
  function tryAutoFs(e) {
    if (fsOnce) return;
    if (e && e.pointerType === 'mouse') return;   // en desktop no forzamos
    if (isFs()) { fsOnce = true; return; }
    enterFs();
  }
  if (!EMBEDDED) document.addEventListener('pointerdown', tryAutoFs, true);
  document.addEventListener('fullscreenchange', () => { if (isFs()) fsOnce = true; });

  // ── Exit directo (sin confirmación) ──
  const btnExit = document.getElementById('btnExit');
  if (btnExit) btnExit.addEventListener('click', () => {
    if (EMBEDDED) { try { window.parent.postMessage({ type: 'arcade:exit' }, '*'); } catch (e) {} return; }
    unlockOrient();
    location.href = '../../Arcade/';
  });
})();
