// Service worker mínimo: hace la PWA "instalable" (Chrome exige un SW con handler de
// 'fetch') y mantiene el shell SIEMPRE FRESCO. La app es chica y online, así que no
// cacheamos; al revés, forzamos que los documentos se traigan sin caché para que un
// deploy se vea al instante (sin tener que borrar la caché del sitio a mano).
// OJO: el SW sólo controla su scope (/Arcade/); los juegos viven fuera y se refrescan
// con el cache-buster del iframe (ver launch() en index.html).

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Navegaciones (el shell): network-first sin caché → siempre la última versión.
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request, { cache: 'no-store' }).catch(() => fetch(e.request)));
  }
  // El resto pasa normal (deja que el navegador use su caché para assets estáticos).
});
