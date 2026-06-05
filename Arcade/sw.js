// Service worker mínimo para que la PWA sea "instalable" (Chrome/Edge requieren
// un SW registrado con al menos un handler de 'fetch'). No cachea nada todavía:
// todas las requests pasan a la red. Cuando agregués caching offline, hacelo
// con un Cache + fetch handler que devuelva del cache para los assets del shell.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', () => {
  // network-only por ahora — no interceptamos
});
