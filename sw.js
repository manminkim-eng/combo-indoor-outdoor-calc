// Service Worker — 겸용 펌프(옥내+옥외소화전) PWA
// ★ 업데이트 시 CACHE_VERSION 숫자를 올려주세요

const CACHE_VERSION='v2.0.0';
const CACHE_NAME=`combo-indoor-outdoor-app-${CACHE_VERSION}`;
const L=['./', './index.html', './manifest.json', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png', './icons/favicon-32.png', './icons/favicon-16.png'];
const C=['https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js','https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js','https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js'];

self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE_NAME).then(async c=>{await c.addAll(L);for(const u of C){try{await c.add(u)}catch(x){}}}));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.map(k=>k!==CACHE_NAME?caches.delete(k):undefined))));self.clients.claim()});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;if(e.request.url.includes('fonts.googleapis.com')||e.request.url.includes('fonts.gstatic.com')){e.respondWith(caches.open(CACHE_NAME).then(async c=>{const d=await c.match(e.request);const f=fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r}).catch(()=>d);return d||f}));return}e.respondWith(caches.match(e.request).then(d=>{if(d)return d;return fetch(e.request).then(r=>{if(r&&r.ok){const cl=r.clone();caches.open(CACHE_NAME).then(c=>c.put(e.request,cl))}return r}).catch(()=>{if(e.request.headers.get('accept')?.includes('text/html'))return caches.match('./index.html');return new Response('offline',{status:503})})}))});
