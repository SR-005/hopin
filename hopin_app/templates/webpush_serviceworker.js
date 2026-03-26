// Register event listener for the 'push' event.
self.addEventListener("push", function (event) {
  const fallbackPayload = {
    head: "No Content",
    body: "No Content",
    icon: ""
  };
  const rawPayload = event.data ? event.data.text() : JSON.stringify(fallbackPayload);
  const data = JSON.parse(rawPayload);
  const head = data.head;
  const body = data.body;
  const icon = data.icon;
  const url = data.url ? data.url : self.location.origin;
  const tag = data.tag ? data.tag : [head, body, url].join("|");

  event.waitUntil(
    self.registration.showNotification(head, {
      body: body,
      icon: icon,
      data: { url: url },
      tag: tag,
      renotify: false
    })
  );
});

self.addEventListener("notificationclick", function (event) {
  event.waitUntil(
    event.preventDefault(),
    event.notification.close(),
    self.clients.openWindow(event.notification.data.url)
  );
});
