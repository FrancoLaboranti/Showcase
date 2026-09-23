// Minimal service worker: it makes the PWA "installable" (Chrome requires a SW with a
// 'fetch' handler) and keeps the shell ALWAYS FRESH. The app is small and online, so we do
// not cache; the opposite — we force documents to be fetched with no cache so a deploy shows
// up instantly (without having to clear the site's cache by hand).
// CAREFUL: the SW only controls its scope (/Arcade/); the games live outside it and refresh
// through the iframe's cache-buster (see launch() in index.html).

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Navigations (the shell): network-first with no cache → always the latest version.
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request, { cache: 'no-store' }).catch(() => fetch(e.request)));
  }
  // Everything else passes through (letting the browser use its cache for static assets).
});
