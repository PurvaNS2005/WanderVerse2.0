/**
 * Firebase Configuration and Authentication Handler
 * 
 * This file handles Firebase initialization, authentication with Google,
 * and token verification with the Django backend.
 */

// Get Firebase config from the global variable set by Django
const firebaseConfig = window.FIREBASE_CONFIG || {
    apiKey: '{{ FIREBASE_CONFIG.apiKey }}',
    authDomain: '{{ FIREBASE_CONFIG.authDomain }}',
    projectId: '{{ FIREBASE_CONFIG.projectId }}',
    storageBucket: '{{ FIREBASE_CONFIG.storageBucket }}',
    messagingSenderId: '{{ FIREBASE_CONFIG.messagingSenderId }}',
    appId: '{{ FIREBASE_CONFIG.appId }}'
};

// Initialize Firebase - only once
let firebaseInitialized = false;
let auth = null;
let db = null;

function initializeFirebase() {
    if (firebaseInitialized) return true;
    
    try {
        if (typeof firebase !== 'undefined') {
            firebase.initializeApp(firebaseConfig);
            auth = firebase.auth();
            db = firebase.firestore();
            
            // Set persistence to LOCAL for better reliability
            auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL)
                .catch(error => console.error('Error setting persistence:', error));
                
            firebaseInitialized = true;
            return true;
        } else {
            console.error('Firebase SDK not available');
            return false;
        }
    } catch (error) {
        console.error('Error initializing Firebase:', error);
        return false;
    }
}

// Initialize Firebase when the script loads
initializeFirebase();

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Updates UI based on authentication state
 */
function updateUI(user) {
    const authButtons = document.getElementById('auth-buttons');
    const profileDropdown = document.getElementById('profile-dropdown');
    const userAvatar = document.getElementById('user-avatar');
    
    if (!authButtons || !profileDropdown) {
        console.warn('Auth UI elements not found, skipping UI update');
        return;
    }
    
    if (user) {
        console.log('Updating UI for authenticated user');
        authButtons.style.display = 'none';
        profileDropdown.style.display = 'block';
        
        if (userAvatar) {
            // Set avatar if available, otherwise use default
            userAvatar.src = user.photoURL || 
                `https://ui-avatars.com/api/?name=${encodeURIComponent(user.displayName || user.email)}&background=random`;
        }
    } else {
        console.log('Updating UI for unauthenticated user');
        authButtons.style.display = 'flex';
        profileDropdown.style.display = 'none';
    }
}

/**
 * Sign in with Google
 * Handles the Google Sign-in flow with better cross-origin handling
 */
async function signInWithGoogle() {
    // Ensure Firebase is initialized
    if (!initializeFirebase() || !auth) {
        alert('Failed to initialize Firebase. Please refresh the page and try again.');
        return;
    }
    
    // Get sign-in button and show loading state
    const signInButton = document.querySelector('#auth-buttons button');
    if (signInButton) {
        signInButton.disabled = true;
        signInButton.innerHTML = '<span class="loading loading-spinner"></span> Signing in...';
    }
    
    try {
        // Ensure we have a valid CSRF token
        await fetch('/accounts/get-csrf-token/', {
            method: 'GET',
            credentials: 'include'
        });
        
        // Create Google auth provider
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.addScope('email');
        provider.addScope('profile');
        
        // Sign out any existing user first
        await auth.signOut();
        
        // Use popup authentication
        const result = await auth.signInWithPopup(provider);
        
        // Get fresh token
        const idToken = await result.user.getIdToken(true);
        
        // Send token to backend for verification
        const response = await fetch('/accounts/verify-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include',
            body: JSON.stringify({ idToken })
        });
        
        if (!response.ok) {
            // Try to parse error response
            let errorMessage = 'Server verification failed';
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || `Server error: ${response.status}`;
            } catch (parseError) {
                // If parsing fails, use the response status text
                errorMessage = `Server error: ${response.status} ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }
        
        // Parse response data
        const responseData = await response.json();
        
        // Show welcome message
        if (responseData.message) {
            // Create toast message
            const toast = document.createElement('div');
            toast.className = 'toast toast-top toast-end z-50';
            toast.innerHTML = `
                <div class="alert alert-success">
                    <span>${responseData.message}</span>
                </div>
            `;
            document.body.appendChild(toast);
            
            // Remove toast after 5 seconds
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }
        
        // Update UI and reload page
        updateUI(result.user);
        window.location.reload();
        
    } catch (error) {
        console.error('Authentication error:', error);
        
        // Show user-friendly error message
        if (error.code === 'auth/popup-closed-by-user') {
            // User closed popup - no need to show error
        } else if (error.code === 'auth/popup-blocked') {
            alert('Sign-in popup was blocked. Please enable popups for this site and try again.');
        } else {
            alert('Authentication failed: ' + (error.message || 'Unknown error'));
        }
    } finally {
        // Reset button state
        if (signInButton) {
            signInButton.disabled = false;
            signInButton.innerHTML = '<svg class="w-5 h-5 mr-2" viewBox="0 0 24 24"><path fill="currentColor" d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/></svg> Sign in with Google';
        }
    }
}

/**
 * Sign out the current user
 */
async function signOut() {
    // Ensure Firebase is initialized
    if (!initializeFirebase() || !auth) {
        alert('Failed to initialize Firebase. Please refresh the page and try again.');
        return;
    }
    
    try {
        console.log('Signing out...');
        
        // Sign out from Firebase
        await auth.signOut();
        
        // Notify backend about sign out
        await fetch('/accounts/sign-out/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });
        
        // Update UI
        updateUI(null);
        
        // Reload page to ensure session is cleared
        window.location.href = '/';
    } catch (error) {
        console.error('Sign-out error:', error);
        alert('Failed to sign out: ' + error.message);
    }
}

// Listen for authentication state changes
document.addEventListener('DOMContentLoaded', () => {
    if (initializeFirebase() && auth) {
        auth.onAuthStateChanged(user => {
            updateUI(user);
        });
    }
});
 