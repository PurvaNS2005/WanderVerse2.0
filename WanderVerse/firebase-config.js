// firebase-auth.js

// Initialize Firebase with actual config (replace placeholders)
const firebaseConfig = {
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "YOUR_FIREBASE_AUTH_DOMAIN",
  projectId: "YOUR_FIREBASE_PROJECT_ID",
  storageBucket: "YOUR_FIREBASE_STORAGE_BUCKET",
  messagingSenderId: "YOUR_FIREBASE_MESSAGING_SENDER_ID",
  appId: "YOUR_FIREBASE_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// Helper function to get CSRF token
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

// Google Sign In
function signInWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  auth.signInWithPopup(provider)
    .then((result) => {
      const user = result.user;
      return user.getIdToken();
    })
    .then((idToken) => {
      return fetch('/accounts/verify-token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: `id_token=${idToken}`
      });
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        window.location.href = '/accounts/profile/';
      } else {
        throw new Error(data.message || 'Authentication failed');
      }
    })
    .catch((error) => {
      console.error("Error signing in with Google:", error);
    });
}

// Sign Out
function signOut() {
  auth.signOut()
    .then(() => {
      return fetch('/accounts/logout/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        }
      });
    })
    .then(() => {
      window.location.href = '/';
    })
    .catch((error) => {
      console.error("Error signing out:", error);
    });
}

// Check auth state
auth.onAuthStateChanged((user) => {
  const authButtons = document.getElementById('auth-buttons');
  const profileDropdown = document.getElementById('profile-dropdown');
  const userAvatar = document.getElementById('user-avatar');

  if (user) {
    if (authButtons) authButtons.style.display = 'none';
    if (profileDropdown) {
      profileDropdown.style.display = 'block';
      if (userAvatar) {
        userAvatar.src = user.photoURL || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(user.displayName);
      }
    }
  } else {
    if (authButtons) authButtons.style.display = 'block';
    if (profileDropdown) profileDropdown.style.display = 'none';
  }
});
