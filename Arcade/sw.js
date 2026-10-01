/*! © 2026 Franco Laboranti. All rights reserved. */
self.addEventListener("install",()=>{self.skipWaiting()}),self.addEventListener("activate",e=>{e.waitUntil(self.clients.claim())}),self.addEventListener("fetch",e=>{e.request.mode==="navigate"&&e.respondWith(fetch(e.request,{cache:"no-store"}).catch(()=>fetch(e.request)))});
