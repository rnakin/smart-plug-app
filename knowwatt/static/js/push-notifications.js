// ═══════════════════════════════════════════════════════════════════════════
// FCM PUSH NOTIFICATION REGISTRATION
// ═══════════════════════════════════════════════════════════════════════════

const FCM_VAPID_KEY = null; // Set this if using VAPID for web push

async function registerFCMToken() {
  if (!('serviceWorker' in navigator)) {
    console.log('Service Worker not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/static/js/sw.js');
    console.log('Service Worker registered:', registration.scope);

    // Request notification permission
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('Notification permission denied');
      return null;
    }

    // Get FCM token (requires Firebase SDK in frontend)
    // For now, we'll use the existing API to register tokens from mobile app
    return registration;
  } catch (err) {
    console.error('Service Worker registration failed:', err);
    return null;
  }
}

// Register push token with backend
async function sendPushTokenToBackend(fcmToken, platform = 'fcm', deviceLabel = 'Web Browser') {
  const accessToken = localStorage.getItem('access');
  if (!accessToken) {
    console.log('No access token found');
    return;
  }

  if (!fcmToken) {
    console.log('No FCM token provided');
    return;
  }

  try {
    const res = await fetch('/api/alerts/push-token/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + accessToken
      },
      body: JSON.stringify({
        token: fcmToken,
        platform: platform,
        device_label: deviceLabel
      })
    });

    if (res.ok) {
      console.log('Push token registered successfully');
    } else {
      console.error('Failed to register push token:', res.status);
    }
  } catch (err) {
    console.error('Failed to register push token:', err);
  }
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Auto-register if permission already granted
    if (Notification.permission === 'granted') {
      registerFCMToken();
    }
  });
}
