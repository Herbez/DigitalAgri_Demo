document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const toggleLoginPassword = document.getElementById('toggleLoginPassword');
    const toggleSignupPassword = document.getElementById('toggleSignupPassword');
    const loginPassword = document.getElementById('loginPassword');
    const signupPassword = document.getElementById('signupPassword');

    if (toggleLoginPassword) {
        toggleLoginPassword.addEventListener('click', function() {
            const type = loginPassword.getAttribute('type') === 'password' ? 'text' : 'password';
            loginPassword.setAttribute('type', type);
            this.innerHTML = type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        });
    }

    if (toggleSignupPassword) {
        toggleSignupPassword.addEventListener('click', function() {
            const type = signupPassword.getAttribute('type') === 'password' ? 'text' : 'password';
            signupPassword.setAttribute('type', type);
            this.innerHTML = type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        });
    }

    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const rememberMe = document.getElementById('rememberMe').checked;

            // Basic validation
            if (!email || !password) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }

            // Email validation
            if (!isValidEmail(email)) {
                showAlert('Please enter a valid email address', 'danger');
                return;
            }

            // Simulate login (replace with actual authentication)
            console.log('Login attempt:', { email, password, rememberMe });
            
            // Show success message
            showAlert('Login successful! Redirecting...', 'success');
            
            // Close modal after delay
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('authModal'));
                modal.hide();
                loginForm.reset();
            }, 1500);
        });
    }

    // Signup form submission
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('signupName').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const agreeTerms = document.getElementById('agreeTerms').checked;

            // Basic validation
            if (!name || !email || !password || !confirmPassword) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }

            // Email validation
            if (!isValidEmail(email)) {
                showAlert('Please enter a valid email address', 'danger');
                return;
            }

            // Password validation
            if (password.length < 6) {
                showAlert('Password must be at least 6 characters long', 'danger');
                return;
            }

            // Password confirmation
            if (password !== confirmPassword) {
                showAlert('Passwords do not match', 'danger');
                return;
            }

            // Terms agreement
            if (!agreeTerms) {
                showAlert('Please agree to the terms and conditions', 'danger');
                return;
            }

            // Simulate signup (replace with actual registration)
            console.log('Signup attempt:', { name, email, password });
            
            // Show success message
            showAlert('Account created successfully! Please login.', 'success');
            
            // Switch to login tab after delay
            setTimeout(() => {
                const loginTab = new bootstrap.Tab(document.getElementById('login-tab'));
                loginTab.show();
                signupForm.reset();
            }, 1500);
        });
    }

    // Email validation helper
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Show alert helper
    function showAlert(message, type) {
        // Remove existing alerts
        const existingAlert = document.querySelector('.auth-alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show auth-alert`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of modal body
        const modalBody = document.querySelector('.modal-body');
        modalBody.insertBefore(alertDiv, modalBody.firstChild);

        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Clear form when modal is hidden
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.addEventListener('hidden.bs.modal', function() {
            if (loginForm) loginForm.reset();
            if (signupForm) signupForm.reset();
            
            // Remove any alerts
            const alerts = document.querySelectorAll('.auth-alert');
            alerts.forEach(alert => alert.remove());
            
            // Reset to login tab
            const loginTab = new bootstrap.Tab(document.getElementById('login-tab'));
            loginTab.show();
        });
    }
});
