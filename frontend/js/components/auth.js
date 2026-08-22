// Authentication Controller
import { CONFIG } from './config.js';
import { API } from './api.js';
import { Toast } from './toast.js';

export const Auth = {
    timerInterval: null,
    countdownSeconds: 60,

    init() {
        this.bindEvents();
        this.updateNavUser();
    },

    bindEvents() {
        document.addEventListener('auth:change', () => this.updateNavUser());

        // OTP box auto focus jumping
        const otpBoxes = document.querySelectorAll('.otp-box');
        otpBoxes.forEach((box, index) => {
            box.addEventListener('input', (e) => {
                if (e.target.value.length === 1 && index < otpBoxes.length - 1) {
                    otpBoxes[index + 1].focus();
                }
            });
            box.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpBoxes[index - 1].focus();
                }
            });
        });
    },

    openAuthModal(tab = 'otp') {
        const modal = document.getElementById('auth-modal');
        if (modal) {
            modal.classList.add('active');
            this.switchTab(tab);
        }
    },

    closeAuthModal() {
        const modal = document.getElementById('auth-modal');
        if (modal) modal.classList.remove('active');
    },

    openRegisterModal() {
        this.closeAuthModal();
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.add('active');
    },

    closeRegisterModal() {
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.remove('active');
    },
    async handleRegister() {
        const firstName = document.getElementById('reg-first-name')?.value.trim();
        const lastName = document.getElementById('reg-last-name')?.value.trim();
        const phone = document.getElementById('reg-phone')?.value.trim();
        const email = document.getElementById('reg-email')?.value.trim();
        const license = document.getElementById('reg-license')?.value.trim();
        const password = document.getElementById('reg-password')?.value;
        const confirmPassword = document.getElementById('reg-confirm-password')?.value;
        if (password !== confirmPassword) {
            Toast.error('Passwords do not match.');
            return;
        }
        const btn = document.getElementById('reg-submit-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';
        try {
            const res = await API.post('/auth/register/', {
                first_name: firstName,
                last_name: lastName,
                phone_number: phone,
                email: email,
                driver_license_number: license,
                password: password
            });
            localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, res.tokens.access);
            localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, res.tokens.refresh);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(res.user));
            Toast.success(`Welcome to DriveLuxe, ${res.user.first_name || res.user.username}!`);
            this.closeRegisterModal();
            this.updateNavUser();
            document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: res.user } }));
        } catch (err) {
            Toast.error(err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';
        }
    },

    switchTab(tabName) {
        document.querySelectorAll('.auth-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        document.getElementById('otp-login-form')?.classList.toggle('hidden', tabName !== 'otp');
        document.getElementById('password-login-form')?.classList.toggle('hidden', tabName !== 'password');
    },

    async handleRequestOTP() {
        const identifier = document.getElementById('otp-identifier')?.value.trim();
        if (!identifier) {
            Toast.error('Please enter your phone number or email.');
            return;
        }

        const btn = document.getElementById('send-otp-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending OTP...';

        try {
            const res = await API.post('/auth/otp/request/', { identifier, purpose: 'LOGIN' });
            Toast.success(`Verification code sent to ${identifier}`);

            document.getElementById('otp-step-1').classList.add('hidden');
            document.getElementById('otp-step-2').classList.remove('hidden');
            document.getElementById('otp-display-identifier').innerText = identifier;

            if (res.dev_otp) {
                const previewEl = document.getElementById('dev-otp-preview');
                if (previewEl) {
                    previewEl.innerHTML = `Demo Code: <span class="text-gradient" style="font-weight:800; font-size:1.1rem;">${res.dev_otp}</span>`;
                    previewEl.classList.remove('hidden');
                }
            }

            this.startCountdown();
            document.querySelector('.otp-box')?.focus();
        } catch (err) {
            Toast.error(err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Send Verification Code';
        }
    },

    startCountdown() {
        clearInterval(this.timerInterval);
        this.countdownSeconds = 60;
        const timerEl = document.getElementById('otp-timer');
        const resendBtn = document.getElementById('resend-otp-btn');
        if (resendBtn) resendBtn.disabled = true;

        this.timerInterval = setInterval(() => {
            this.countdownSeconds--;
            if (timerEl) timerEl.innerText = `Resend in ${this.countdownSeconds}s`;

            if (this.countdownSeconds <= 0) {
                clearInterval(this.timerInterval);
                if (timerEl) timerEl.innerText = '';
                if (resendBtn) {
                    resendBtn.disabled = false;
                    resendBtn.innerText = 'Resend Code';
                }
            }
        }, 1000);
    },

    async handleVerifyOTP() {
        const identifier = document.getElementById('otp-identifier')?.value.trim();
        const otpBoxes = document.querySelectorAll('.otp-box');
        let code = '';
        otpBoxes.forEach(box => code += box.value);

        if (code.length < 6) {
            Toast.error('Please enter all 6 digits.');
            return;
        }

        const btn = document.getElementById('verify-otp-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';

        try {
            const res = await API.post('/auth/otp/verify/', {
                identifier,
                otp_code: code,
                purpose: 'LOGIN'
            });

            localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, res.tokens.access);
            localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, res.tokens.refresh);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(res.user));

            Toast.success(`Welcome, ${res.user.full_name || res.user.username}!`);
            this.closeAuthModal();
            document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: res.user } }));

            if (res.user.role === 'ADMIN' && window.location.pathname.includes('admin')) {
                window.location.reload();
            }
        } catch (err) {
            Toast.error(err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Verify & Continue';
        }
    },

    async handlePasswordLogin() {
        const usernameInput = document.getElementById('login-username');
        const passwordInput = document.getElementById('login-password');

        const username_or_phone = usernameInput?.value.trim();
        const password = passwordInput?.value;

        if (!username_or_phone || !password) {
            Toast.error('Please fill in username and password.');
            return;
        }

        const btn = document.getElementById('password-login-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in...';

        try {
            const res = await API.post('/auth/login/', { username_or_phone, password });
            localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, res.tokens.access);
            localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, res.tokens.refresh);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(res.user));

            Toast.success(`Welcome back, ${res.user.full_name || res.user.username}!`);
                
            usernameInput.value = '';
            passwordInput.value = '';
            this.closeAuthModal();
            document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: res.user } }));

            if (res.user.role === 'ADMIN' && window.location.pathname.includes('admin')) {
                window.location.reload();
            }
        } catch (err) {
            Toast.error(err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Sign In';
        }
    },

    updateNavUser() {
        const user = API.getUser();
        const authBtn = document.getElementById('nav-auth-btn');
        const notifContainer = document.getElementById('nav-notif-container');
        const userMenu = document.getElementById('nav-user-menu');
        const userNameEl = document.getElementById('nav-user-name');
        const userAvatarEl = document.getElementById('nav-user-avatar');
        const adminPortalLink = document.getElementById('nav-admin-link');

        if (user && API.isAuthenticated()) {
            if (authBtn) {
                authBtn.classList.add('hidden');
                authBtn.style.display = 'none';
            }
            if (notifContainer) {
                notifContainer.classList.remove('hidden');
                notifContainer.style.display = 'block';
            }
            if (userMenu) {
                userMenu.classList.remove('hidden');
                userMenu.style.display = 'block';
            }
            if (userNameEl) userNameEl.innerText = user.first_name || user.username;
            if (userAvatarEl) userAvatarEl.innerText = (user.first_name ? user.first_name[0] : user.username[0]).toUpperCase();
            if (adminPortalLink) {
                const isAdmin = user.role === 'ADMIN' || user.is_staff || user.is_superuser;
                adminPortalLink.classList.toggle('hidden', !isAdmin);
                adminPortalLink.style.display = isAdmin ? '' : 'none';
            }
        } else {
            if (authBtn) {
                authBtn.classList.remove('hidden');
                authBtn.style.display = '';
            }
            if (notifContainer) {
                notifContainer.classList.add('hidden');
                notifContainer.style.display = 'none';
            }
            if (userMenu) {
                userMenu.classList.add('hidden');
                userMenu.style.display = 'none';
            }
            if (adminPortalLink) {
                adminPortalLink.classList.add('hidden');
                adminPortalLink.style.display = 'none';
            }
        }
    },

    logout() {
        API.clearAuth();
        Toast.info('You have been signed out.');
        this.updateNavUser();
        if (window.location.pathname.includes('admin-portal')) {
            window.location.href = '/';
        }
    }
};
