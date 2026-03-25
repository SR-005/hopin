# Push Notifications Setup Guide (Django-WebPush)

This guide explains how to set up and use Web Push notifications in the Hopin app using django-webpush.

## Backend Setup (Already Done)

✅ **Completed:**
- Added `django-webpush==0.3.3` to requirements.txt
- Added `webpush` to INSTALLED_APPS in settings.py
- Configured VAPID keys in settings.py
- Created notification utility functions in `hopin_app/notifications.py`
- Updated driver views to send notifications on request accept/reject/trip deletion
- Added Web Push subscription registration endpoint at `/register_webpush_subscription/`

## VAPID Keys Setup (Required)

### 1. Generate VAPID Keys

Install web-push CLI or use an online generator:

**Option A: Using web-push CLI**
```bash
npm install -g web-push
web-push generate-vapid-keys
```

**Option B: Using Python**
```bash
pip install pywebpush
python -c "
from py_vapid import Vapid01
vapid = Vapid01.generate()
print('Public Key:', vapid.public_key.decode('utf-8'))
print('Private Key:', vapid.private_key.decode('utf-8'))
"
```

### 2. Configure Environment Variables

Add to your `.env` file:
```
VAPID_PUBLIC_KEY=your_public_key_here
VAPID_PRIVATE_KEY=your_private_key_here
VAPID_ADMIN_EMAIL=your-email@example.com
```

**Important:** The VAPID_ADMIN_EMAIL should be a valid email address (e.g., admin@yourapp.com or your actual email).

## Frontend Setup

### 1. Service Worker File

Create a file `hopin_app/static/js/sw.js`:

```javascript
// Service Worker for handling push notifications
self.addEventListener('push', function (event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        vibrate: [200, 100, 200],
        data: data.data || {}
    };

    event.waitUntil(
        self.registration.showNotification(data.head, options)
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    // Handle notification click
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(function (clientList) {
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});

self.addEventListener('notificationclose', function (event) {
    console.log('Notification closed:', event.notification.tag);
});
```

### 2. Main Template Script

Add to your base template (e.g., `base.html`):

```html
<!-- Web Push Notification Setup -->
<script>
// Check if service workers are supported
if ('serviceWorker' in navigator && 'PushManager' in window) {
    // Register service worker
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(registration => {
            console.log('Service Worker registered:', registration);
            
            // Request notification permission
            return Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Notification permission granted');
                    subscribeUserToPush(registration);
                } else if (permission === 'default') {
                    console.log('User deferred the notification permission');
                } else {
                    console.log('Notification permission denied');
                }
            });
        })
        .catch(error => console.log('Service Worker registration failed:', error));
}

function subscribeUserToPush(registration) {
    // Get VAPID public key from server (add as data attribute on body or fetch from endpoint)
    const vapidPublicKey = document.body.dataset.vapidKey;
    
    if (!vapidPublicKey) {
        console.error('VAPID public key not found');
        return;
    }

    const subscribeOptions = {
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
    };

    registration.pushManager.subscribe(subscribeOptions)
        .then(subscription => {
            console.log('Push subscription successful:', subscription);
            
            // Send subscription to backend
            sendSubscriptionToBackend(subscription);
        })
        .catch(error => {
            console.error('Failed to subscribe to push notifications:', error);
        });
}

function sendSubscriptionToBackend(subscription) {
    fetch('/register_webpush_subscription/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            subscription: subscription
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Subscription registered with server');
        } else {
            console.error('Failed to register subscription:', data.message);
        }
    })
    .catch(error => console.error('Error registering subscription:', error));
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>
```

### 3. Update Base Template HTML

In your base template, add the VAPID public key as a data attribute:

```html
<!DOCTYPE html>
<html>
<head>
    <!-- your head content -->
</head>
<body data-vapid-key="{{ vapid_public_key }}">
    <!-- your body content -->
</body>
</html>
```

### 4. Update View Context

Update your view to pass the VAPID public key to the template:

```python
from django.conf import settings

def your_view(request):
    context = {
        'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY'],
        # ... other context
    }
    return render(request, 'template.html', context)
```

## Notification Triggers

### 1. Request Accepted
- **Trigger:** Driver accepts rider's ride request
- **Recipient:** Rider
- **Message:** "Request Accepted! Your ride request has been accepted by the driver."
- **Code Location:** `hopin_app/views/driverview.py` → `acceptride()`

### 2. Request Rejected
- **Trigger:** Driver rejects rider's ride request
- **Recipient:** Rider
- **Message:** "Request Rejected. Unfortunately, your ride request has been rejected."
- **Code Location:** `hopin_app/views/driverview.py` → `rejectride()`

### 3. Trip Deleted
- **Trigger:** Driver deletes a trip that has pending/accepted rider requests
- **Recipient:** All affected riders
- **Message:** "Trip Cancelled. The ride you requested has been cancelled by the driver."
- **Code Location:** `hopin_app/views/driverview.py` → `deleteride()`

## API Endpoints

### Register Web Push Subscription
```
POST /register_webpush_subscription/
```

**Content-Type:** `application/json`

**Request Body:**
```json
{
    "subscription": {
        "endpoint": "https://fcm.googleapis.com/...",
        "expirationTime": null,
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
}
```

**Response (Success):**
```json
{
    "status": "success",
    "message": "Subscription registered successfully"
}
```

**Response (Error):**
```json
{
    "status": "error",
    "message": "No subscription provided"
}
```

## Testing Notifications

### Manual Testing via Django Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from hopin_app.notifications import send_generic_notification

User = get_user_model()
rider = User.objects.get(id=1)

send_generic_notification(
    rider, 
    "Test Notification", 
    "This is a test message"
)
```

### Test Accept Notification

```python
from hopin_app.notifications import send_request_accepted_notification

User = get_user_model()
rider = User.objects.get(id=1)

send_request_accepted_notification(rider)
```

### Via Admin Panel

1. Go to Django Admin: `/admin/webpush/`
2. View registered subscriptions in `PushInformation`
3. Check `SubscriptionInfo` for endpoint details

## Database Models

The `django-webpush` package creates the following models:

- **SubscriptionInfo:** Stores subscription endpoint and encryption keys
  - `endpoint` (URLField)
  - `browser` (CharField)
  - `auth` (CharField)
  - `p256dh` (CharField)

- **Group:** For grouping subscriptions
  - `name` (CharField)

- **PushInformation:** Links users/groups to subscriptions
  - `user` (ForeignKey to User) - optional
  - `group` (ForeignKey to Group) - optional
  - `subscription` (ForeignKey to SubscriptionInfo)

Access via Django admin:
```
/admin/webpush/
```

## Troubleshooting

### Push notifications not received

1. **Check Service Worker registration:**
   - Open DevTools → Application → Service Workers
   - Verify the SW is active and running

2. **Verify VAPID keys:**
   - Check `.env` file has valid VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY
   - Keys must form a valid pair

3. **Check subscription registration:**
   - Go to Django admin → Webpush → PushInformation
   - Verify your user has registered subscriptions
   - Check SubscriptionInfo for valid endpoints

4. **Browser console:**
   - Open DevTools → Console
   - Look for any JavaScript errors
   - Check for CORS issues

5. **Server logs:**
   - Check Django console for notification sending errors
   - Look for WebPushException errors

### Service Worker not registering

1. Check HTTPS is enabled (required except on localhost)
2. Verify service worker file exists at `/static/js/sw.js`
3. Check browser console for registration errors
4. Ensure proper file permissions

### "NotificationPermission.requestPermission is not a function"

This usually means the browser doesn't support Web Push. Ensure you're using:
- Chrome/Edge v50+
- Firefox v48+
- Safari v16+

### "Failed to send notification"

Possible causes:
1. User's browser hasn't registered subscription
2. Subscription has expired
3. Invalid VAPID keys
4. Push service is unreachable

### Database errors during subscription save

Ensure migrations have been applied:
```bash
python manage.py migrate webpush
```

## Security Notes

- Keep VAPID private key secure
- Never expose private key in frontend code
- Use HTTPS in production
- Validate user permissions before sending notifications
- Implement rate limiting for notification sending

## Performance Tips

1. **Batch notifications:** Group multiple notifications when possible
2. **Implement efficient sending:** Use send_notification in loops with try-except
3. **Clean up old subscriptions:** Implement periodic cleanup of invalid subscriptions
4. **Monitor delivery:** Track notification delivery success/failure

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | v50+ |
| Firefox | ✅ Full | v48+ |
| Edge | ✅ Full | All versions |
| Safari | ⚠️ Limited | iOS 16+, macOS 13+ |
| Opera | ✅ Full | v37+ |
| Internet Explorer | ❌ None | Not supported |

## References

- [django-webpush Documentation](https://github.com/safwanrahman/django-webpush)
- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)

## Useful Commands

```bash
# Install dependencies
pip install django-webpush six pywebpush

# Generate VAPID keys
python -c "
from py_vapid import Vapid01
v=Vapid01.generate()
print(f'Public: {v.public_key.decode()}')
print(f'Private: {v.private_key.decode()}')
"

# Run migrations
python manage.py migrate webpush

# Django shell
python manage.py shell

# Run tests
python manage.py test

# Check Django system
python manage.py check
```

## Common Questions

**Q: How frequently can I send notifications?**
A: There's no hard limit, but consider user experience. Excessive notifications lead to opt-out. Implement sensible rate limiting.

**Q: Can users disable notifications?**
A: Yes, they control it through their browser settings. Your app can also provide an opt-out mechanism in the UI.

**Q: How long do subscriptions last?**
A: Indefinitely, unless the user revokes permission or clears browser data. Invalid subscriptions will raise WebPushException when sending.

**Q: Can I send notifications to offline users?**
A: Yes! That's the power of Web Push. Push services store messages temporarily and deliver when the browser comes online.

**Q: How do I handle failed notifications?**
A: Wrap send_notification calls in try-except blocks. Failed subscriptions can be cleaned up and re-added on next visit.
