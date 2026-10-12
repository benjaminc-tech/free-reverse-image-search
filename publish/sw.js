// Service worker for one job: the Android share sheet.
// The manifest's share_target POSTs a shared photo to /share-target. There is
// no server behind this static site, so we catch that POST here, park the file
// in Cache Storage on this device, and send the page to /?shared=1 to pick it
// up. The file never leaves the device.
//
// Nothing else is cached or intercepted, so a deploy is never stuck behind a
// stale copy of the site.

const SHARE_CACHE = "ris-share";
const SHARE_KEY = "/__shared-file";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "POST" || url.origin !== location.origin || url.pathname !== "/share-target") return;

  event.respondWith((async () => {
    try {
      const form = await event.request.formData();
      const file = form.getAll("image").find((f) => f && typeof f !== "string");
      if (file) {
        const cache = await caches.open(SHARE_CACHE);
        await cache.put(SHARE_KEY, new Response(file, {
          headers: {
            "Content-Type": file.type || "application/octet-stream",
            "X-File-Name": encodeURIComponent(file.name || "shared-image")
          }
        }));
      }
    } catch (err) {
      // fall through, the page shows its normal empty state
    }
    return Response.redirect("/?shared=1", 303);
  })());
});
