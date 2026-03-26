var isPushEnabled = false,
    registration,
    subBtn;

function notifyPushState(status) {
  document.dispatchEvent(new CustomEvent('hopin:webpush-state', {
    detail: { status: status }
  }));
}

function markSubscribed() {
  subBtn.textContent = 'Unsubscribe from Push Messaging';
  subBtn.disabled = false;
  isPushEnabled = true;
  notifyPushState('subscribed');
}

function markUnsubscribed(shouldNotify) {
  subBtn.textContent = 'Subscribe to Push Messaging';
  subBtn.disabled = false;
  isPushEnabled = false;
  if (shouldNotify !== false) {
    notifyPushState('unsubscribed');
  }
}

window.addEventListener('load', function () {
  subBtn = document.getElementById('webpush-subscribe-button');

  if (!subBtn) {
    return;
  }

  subBtn.disabled = true;

  subBtn.addEventListener('click', function () {
    subBtn.disabled = true;
    showMessage('Working on browser subscription...');

    if (isPushEnabled) {
      return unsubscribe(registration);
    }
    return subscribe(registration);
  });

  if ('serviceWorker' in navigator) {
    var serviceWorkerMeta = document.querySelector('meta[name="service-worker-js"]');
    if (!serviceWorkerMeta || !serviceWorkerMeta.content) {
      showMessage('Service worker URL is missing.');
      subBtn.disabled = false;
      return;
    }

    navigator.serviceWorker.register(serviceWorkerMeta.content).then(function (reg) {
      registration = reg;
      initialiseState(reg);
    }).catch(function (error) {
      console.error('Service worker registration failed.', error);
      showMessage('Service worker registration failed. Check browser console.');
      subBtn.disabled = false;
    });
  } else {
    showMessage('Service Worker is not supported in your browser.');
    subBtn.disabled = true;
  }

  function initialiseState(reg) {
    if (!reg.showNotification) {
      markUnsubscribed(false);
      showMessage('Notifications are not supported in this browser.');
      notifyPushState('unsupported');
      return;
    }

    if (Notification.permission === 'denied') {
      markUnsubscribed(false);
      showMessage('Browser notifications are blocked for this site.');
      notifyPushState('permission-denied');
      return;
    }

    if (!('PushManager' in window)) {
      markUnsubscribed(false);
      showMessage('Push messaging is not available in this browser.');
      notifyPushState('unsupported');
      return;
    }

    reg.pushManager.getSubscription().then(function (subscription) {
      if (!subscription) {
        markUnsubscribed();
        return;
      }

      postSubscribeObj('subscribe', subscription).then(function (response) {
        if (response.ok) {
          markSubscribed();
          return;
        }

        showMessage('Subscription exists in browser but server rejected it (' + response.status + ').');
        subBtn.disabled = false;
      }).catch(function (error) {
        console.error('Failed to sync existing subscription.', error);
        showMessage('Could not sync existing subscription with server.');
        subBtn.disabled = false;
      });
    }).catch(function (error) {
      console.error('Failed to read existing subscription.', error);
      showMessage('Could not inspect browser push subscription.');
      subBtn.disabled = false;
    });
  }
});

function showMessage(message) {
  var messageBox = document.getElementById('webpush-message');
  if (messageBox) {
    messageBox.hidden = false;
    messageBox.style.display = 'block';
    messageBox.classList.add('text-sm', 'font-semibold', 'text-[#191265]');
    messageBox.textContent = message;
  }
}

function ensureRegistration() {
  if (registration) {
    return Promise.resolve(registration);
  }

  if (!('serviceWorker' in navigator)) {
    return Promise.reject(new Error('Service workers are not supported in this browser.'));
  }

  return navigator.serviceWorker.ready.then(function (reg) {
    registration = reg;
    return reg;
  });
}

function subscribe(reg) {
  ensureRegistration().then(function (readyReg) {
    return readyReg.pushManager.getSubscription();
  }).then(function (subscription) {
    var metaObj, applicationServerKey, options;
    if (subscription) {
      return subscription;
    }

    metaObj = document.querySelector('meta[name="django-webpush-vapid-key"]');
    applicationServerKey = metaObj ? metaObj.content : '';
    options = {
      userVisibleOnly: true
    };

    if (applicationServerKey) {
      options.applicationServerKey = urlB64ToUint8Array(applicationServerKey);
    }

    return registration.pushManager.subscribe(options);
  }).then(function (subscription) {
    if (!subscription) {
      throw new Error('Browser did not return a push subscription.');
    }

    return postSubscribeObj('subscribe', subscription).then(function (response) {
      if (response.ok) {
        markSubscribed();
        showMessage('Successfully subscribed for push notifications.');
        return;
      }

      throw new Error('Server returned status ' + response.status);
    });
  }).catch(function (error) {
    console.error('Subscription error.', error);
    showMessage('Subscription failed. Open DevTools Console and Network for details.');
    subBtn.disabled = false;
  });
}

function urlB64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - base64String.length % 4) % 4);
  var base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  var rawData = window.atob(base64);
  var outputArray = new Uint8Array(rawData.length);

  for (var i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function unsubscribe(reg) {
  ensureRegistration().then(function (readyReg) {
    return readyReg.pushManager.getSubscription();
  }).then(function (subscription) {
    if (!subscription) {
      subBtn.disabled = false;
      showMessage('No active subscription found in this browser.');
      return;
    }

    postSubscribeObj('unsubscribe', subscription).then(function (response) {
      if (!response.ok) {
        throw new Error('Server returned status ' + response.status);
      }

      return subscription.unsubscribe().then(function () {
        markUnsubscribed();
        showMessage('Successfully unsubscribed from push notifications.');
      });
    }).catch(function (error) {
      console.error('Unsubscribe error.', error);
      showMessage('Unsubscribe failed. Check browser console.');
      subBtn.disabled = false;
    });
  }).catch(function (error) {
    console.error('Failed to load current subscription for unsubscribe.', error);
    showMessage('Could not load browser subscription for unsubscribe.');
    subBtn.disabled = false;
  });
}

function postSubscribeObj(statusType, subscription) {
  var browserMatch = navigator.userAgent.match(/(firefox|msie|chrome|safari|trident|edg)/ig);
  var browser = browserMatch ? browserMatch[0].toLowerCase() : 'unknown';
  var data = {
    status_type: statusType,
    subscription: subscription.toJSON(),
    browser: browser,
    group: subBtn.dataset.group || ''
  };

  return fetch(subBtn.dataset.url, {
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include'
  }).then(function (response) {
    if (!response.ok) {
      console.error('Push subscription endpoint rejected request.', response.status);
    }
    return response;
  });
}
