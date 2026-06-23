const CACHE = "mundialiyo-v2"
const ASSETS = [
  "/",
  "/static/css/worldcup2026.css",
  "/static/js/main.js",
  "/static/img/favicon.svg",
  "/static/manifest.json",
  "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
]

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  )
})

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(resp => resp || fetch(event.request))
  )
})
