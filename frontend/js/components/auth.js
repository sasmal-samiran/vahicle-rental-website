// Authentication Controller
import { CONFIG } from './config.js';
import { API } from './api.js';
import { Toast } from './toast.js';

export const Auth = {
    timerInterval: null,
    countdownSeconds: 60,
    regTimerInterval: null,
    regCountdownSeconds: 60,
    pendingRegistrationData: null,

    init() {
        this.bindEvents();
        this.updateNavUser();
    },

    setupOtpBoxJumping(containerSelector, boxSelector) {
        const boxes = document.querySelectorAll(boxSelector);
        boxes.forEach((box, index) => {
            box.addEventListener('input', (e) => {
                if (e.target.value.length === 1 && index < boxes.length - 1) {
                    boxes[index + 1].focus();
                }
                // Auto submit when all 6 digits entered
                const allFilled = Array.from(boxes).every(b => b.value.length === 1);
                if (allFilled) {
                    if (containerSelector === '#auth-modal') {
                        Auth.handleVerifyOTP();
                    } else if (containerSelector === '#register-modal') {
                        Auth.handleVerifyRegisterOTP();
                    }
                }
            });
            box.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    boxes[index - 1].focus();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (containerSelector === '#auth-modal') {
                        Auth.handleVerifyOTP();
                    } else if (containerSelector === '#register-modal') {
                        Auth.handleVerifyRegisterOTP();
                    }
                }
            });
        });
    },

    togglePasswordVisibility(inputId, btnEl) {
        const input = document.getElementById(inputId);
        if (!input) return;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        const icon = btnEl?.querySelector('i');
        if (icon) {
            icon.className = isPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
        }
    },

    bindEvents() {
        document.addEventListener('auth:change', () => this.updateNavUser());

        // OTP box auto focus jumping for login and register
        this.setupOtpBoxJumping('#auth-modal', '#auth-modal .otp-box');
        this.setupOtpBoxJumping('#register-modal', '.reg-otp-box');

        // Enter key to submit on inputs
        document.getElementById('otp-identifier')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handleRequestOTP();
            }
        });

        document.getElementById('login-username')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const pwd = document.getElementById('login-password');
                if (pwd && !pwd.value) {
                    pwd.focus();
                } else {
                    this.handlePasswordLogin();
                }
            }
        });

        document.getElementById('login-password')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handlePasswordLogin();
            }
        });

        // Clear inline errors on input
        document.getElementById('login-password')?.addEventListener('input', () => {
            this.clearFieldError('login-password', 'login-password-error');
        });
        document.getElementById('login-username')?.addEventListener('input', () => {
            this.clearFieldError('login-password', 'login-password-error');
        });
        document.getElementById('otp-identifier')?.addEventListener('input', () => {
            this.clearFieldError('otp-identifier', 'otp-identifier-error');
        });
        document.querySelectorAll('#auth-modal .otp-box').forEach(box => {
            box.addEventListener('input', () => {
                const errEl = document.getElementById('login-otp-error');
                if (errEl) errEl.classList.add('hidden');
                document.querySelectorAll('#auth-modal .otp-box').forEach(b => b.style.borderColor = '');
            });
        });
        document.getElementById('reg-password')?.addEventListener('input', () => {
            this.clearFieldError('reg-password', 'reg-password-error');
            this.clearFieldError('reg-confirm-password', 'reg-password-error');
        });
        document.getElementById('reg-confirm-password')?.addEventListener('input', () => {
            this.clearFieldError('reg-password', 'reg-password-error');
            this.clearFieldError('reg-confirm-password', 'reg-password-error');
        });
        document.querySelectorAll('.reg-otp-box').forEach(box => {
            box.addEventListener('input', () => {
                const errEl = document.getElementById('reg-otp-error');
                if (errEl) errEl.classList.add('hidden');
                document.querySelectorAll('.reg-otp-box').forEach(b => b.style.borderColor = '');
            });
        });
    },

    showFieldError(fieldId, errorElId, message) {
        const errorEl = document.getElementById(errorElId);
        if (errorEl) {
            errorEl.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${message}`;
            errorEl.classList.remove('hidden');
        }
        const field = document.getElementById(fieldId);
        if (field) {
            field.style.borderColor = 'var(--danger, #ef4444)';
        }
    },

    clearFieldError(fieldId, errorElId) {
        const errorEl = document.getElementById(errorElId);
        if (errorEl) {
            errorEl.classList.add('hidden');
            errorEl.innerHTML = '';
        }
        const field = document.getElementById(fieldId);
        if (field) {
            field.style.borderColor = '';
        }
    },

    openAuthModal(tab = 'otp') {
        const modal = document.getElementById('auth-modal');
        if (modal) {
            modal.classList.add('active');
            this.clearFieldError('login-password', 'login-password-error');
            this.clearFieldError('otp-identifier', 'otp-identifier-error');
            const otpErr = document.getElementById('login-otp-error');
            if (otpErr) otpErr.classList.add('hidden');
            this.switchTab(tab);
        }
    },

    closeAuthModal() {
        const modal = document.getElementById('auth-modal');
        if (modal) modal.classList.remove('active');
        this.clearFieldError('login-password', 'login-password-error');
        this.clearFieldError('otp-identifier', 'otp-identifier-error');
        const otpErr = document.getElementById('login-otp-error');
        if (otpErr) otpErr.classList.add('hidden');
    },

    openRegisterModal() {
        this.closeAuthModal();
        this.backToRegisterForm();
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.add('active');
    },

    closeRegisterModal() {
        const modal = document.getElementById('register-modal');
        if (modal) modal.classList.remove('active');
        this.backToRegisterForm();
    },

    backToRegisterForm() {
        document.getElementById('reg-step-1')?.classList.remove('hidden');
        document.getElementById('reg-step-2')?.classList.add('hidden');
        clearInterval(this.regTimerInterval);
        document.querySelectorAll('.reg-otp-box').forEach(b => {
            b.value = '';
            b.style.borderColor = '';
        });
        this.clearFieldError('reg-password', 'reg-password-error');
        const regOtpErr = document.getElementById('reg-otp-error');
        if (regOtpErr) regOtpErr.classList.add('hidden');
    },

    async handleRegister() {
        this.clearFieldError('reg-password', 'reg-password-error');

        const firstName = document.getElementById('reg-first-name')?.value.trim();
        const lastName = document.getElementById('reg-last-name')?.value.trim();
        const phone = document.getElementById('reg-phone')?.value.trim();
        const email = document.getElementById('reg-email')?.value.trim();
        const license = document.getElementById('reg-license')?.value.trim();
        const password = document.getElementById('reg-password')?.value;
        const confirmPassword = document.getElementById('reg-confirm-password')?.value;

        if (!firstName || !lastName || !phone || !email || !password) {
            this.showFieldError('reg-password', 'reg-password-error', 'Please fill in all required fields.');
            return;
        }

        if (password !== confirmPassword) {
            this.showFieldError('reg-confirm-password', 'reg-password-error', 'Passwords do not match.');
            return;
        }

        if (password.length < 8) {
            this.showFieldError('reg-password', 'reg-password-error', 'Password must be at least 8 characters long.');
            return;
        }

        this.pendingRegistrationData = {
            first_name: firstName,
            last_name: lastName,
            phone_number: phone,
            email: email,
            driver_license_number: license,
            password: password
        };

        await this.handleRequestRegisterOTP();
    },

    async handleRequestRegisterOTP() {
        if (!this.pendingRegistrationData || !this.pendingRegistrationData.phone_number) {
            this.showFieldError('reg-password', 'reg-password-error', 'Registration details missing. Please try again.');
            return;
        }

        const phone = this.pendingRegistrationData.phone_number;
        const btn = document.getElementById('reg-submit-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending OTP...';
        }

        try {
            const res = await API.post('/auth/otp/request/', {
                identifier: phone,
                purpose: 'REGISTER'
            });

            Toast.success(`Verification code sent to ${phone}`);

            document.getElementById('reg-step-1')?.classList.add('hidden');
            document.getElementById('reg-step-2')?.classList.remove('hidden');
            
            const displayIdEl = document.getElementById('reg-otp-display-identifier');
            if (displayIdEl) displayIdEl.innerText = phone;

            if (res.dev_otp) {
                const previewEl = document.getElementById('reg-dev-otp-preview');
                if (previewEl) {
                    previewEl.innerHTML = `Demo Code: <span class="text-gradient" style="font-weight:800; font-size:1.1rem;">${res.dev_otp}</span>`;
                    previewEl.classList.remove('hidden');
                }
            }

            this.startRegisterCountdown();
            document.querySelectorAll('.reg-otp-box').forEach(b => {
                b.value = '';
                b.style.borderColor = '';
            });
            document.querySelector('.reg-otp-box')?.focus();
        } catch (err) {
            this.showFieldError('reg-password', 'reg-password-error', err.message);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-arrow-right"></i> Continue to Verification';
            }
        }
    },

    startRegisterCountdown() {
        clearInterval(this.regTimerInterval);
        this.regCountdownSeconds = 60;
        const timerEl = document.getElementById('reg-otp-timer');
        const resendBtn = document.getElementById('reg-resend-otp-btn');
        if (resendBtn) resendBtn.disabled = true;

        this.regTimerInterval = setInterval(() => {
            this.regCountdownSeconds--;
            if (timerEl) timerEl.innerText = `Resend in ${this.regCountdownSeconds}s`;

            if (this.regCountdownSeconds <= 0) {
                clearInterval(this.regTimerInterval);
                if (timerEl) timerEl.innerText = '';
                if (resendBtn) {
                    resendBtn.disabled = false;
                    resendBtn.innerText = 'Resend Code';
                }
            }
        }, 1000);
    },

    async handleVerifyRegisterOTP() {
        const regOtpErr = document.getElementById('reg-otp-error');
        if (regOtpErr) regOtpErr.classList.add('hidden');
        document.querySelectorAll('.reg-otp-box').forEach(b => b.style.borderColor = '');

        if (!this.pendingRegistrationData) {
            if (regOtpErr) {
                regOtpErr.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Registration session expired. Please fill the form again.';
                regOtpErr.classList.remove('hidden');
            }
            this.backToRegisterForm();
            return;
        }

        const otpBoxes = document.querySelectorAll('.reg-otp-box');
        let code = '';
        otpBoxes.forEach(box => code += box.value);

        if (code.length < 6) {
            if (regOtpErr) {
                regOtpErr.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Please enter all 6 digits.';
                regOtpErr.classList.remove('hidden');
            }
            otpBoxes.forEach(b => b.style.borderColor = 'var(--danger, #ef4444)');
            return;
        }

        const btn = document.getElementById('reg-verify-otp-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying & Creating Account...';

        try {
            // 1. Verify OTP with REGISTER purpose
            await API.post('/auth/otp/verify/', {
                identifier: this.pendingRegistrationData.phone_number,
                otp_code: code,
                purpose: 'REGISTER'
            });

            // 2. Create the registered user account
            const res = await API.post('/auth/register/', this.pendingRegistrationData);

            localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, res.tokens.access);
            localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, res.tokens.refresh);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(res.user));

            Toast.success(`Welcome to DriveLuxe, ${res.user.first_name || res.user.username}! Your account is verified.`);
            this.closeRegisterModal();
            this.updateNavUser();
            document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: res.user } }));
        } catch (err) {
            if (regOtpErr) {
                regOtpErr.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${err.message || 'Invalid verification code.'}`;
                regOtpErr.classList.remove('hidden');
            }
            otpBoxes.forEach(b => b.style.borderColor = 'var(--danger, #ef4444)');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verify & Complete Registration';
        }
    },

    switchTab(tabName) {
        document.querySelectorAll('.auth-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        document.getElementById('otp-login-form')?.classList.toggle('hidden', tabName !== 'otp');
        document.getElementById('password-login-form')?.classList.toggle('hidden', tabName !== 'password');
        this.clearFieldError('login-password', 'login-password-error');
        this.clearFieldError('otp-identifier', 'otp-identifier-error');
        const otpErr = document.getElementById('login-otp-error');
        if (otpErr) otpErr.classList.add('hidden');
    },

    async handleRequestOTP() {
        this.clearFieldError('otp-identifier', 'otp-identifier-error');
        const identifier = document.getElementById('otp-identifier')?.value.trim();
        if (!identifier) {
            this.showFieldError('otp-identifier', 'otp-identifier-error', 'Please enter your phone number or email.');
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
            document.querySelectorAll('#auth-modal .otp-box').forEach(b => {
                b.value = '';
                b.style.borderColor = '';
            });
            document.querySelector('.otp-box')?.focus();
        } catch (err) {
            this.showFieldError('otp-identifier', 'otp-identifier-error', err.message);
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
        const otpErrorEl = document.getElementById('login-otp-error');
        if (otpErrorEl) otpErrorEl.classList.add('hidden');
        const otpBoxes = document.querySelectorAll('#auth-modal .otp-box');
        otpBoxes.forEach(b => b.style.borderColor = '');

        const identifier = document.getElementById('otp-identifier')?.value.trim();
        let code = '';
        otpBoxes.forEach(box => code += box.value);

        if (code.length < 6) {
            if (otpErrorEl) {
                otpErrorEl.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Please enter all 6 digits of the code.';
                otpErrorEl.classList.remove('hidden');
            }
            otpBoxes.forEach(b => b.style.borderColor = 'var(--danger, #ef4444)');
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
            if (otpErrorEl) {
                otpErrorEl.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${err.message || 'Invalid or expired verification code.'}`;
                otpErrorEl.classList.remove('hidden');
            }
            otpBoxes.forEach(b => b.style.borderColor = 'var(--danger, #ef4444)');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Verify & Continue';
        }
    },

    async handlePasswordLogin() {
        this.clearFieldError('login-password', 'login-password-error');
        const usernameInput = document.getElementById('login-username');
        const passwordInput = document.getElementById('login-password');

        const username_or_phone = usernameInput?.value.trim();
        const password = passwordInput?.value;

        if (!username_or_phone || !password) {
            this.showFieldError('login-password', 'login-password-error', 'Please fill in both username and password.');
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
            this.showFieldError('login-password', 'login-password-error', err.message || 'Invalid username/phone or password.');
            if (passwordInput) passwordInput.focus();
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
            if (userAvatarEl) {
                const initial = (user.first_name ? user.first_name[0] : (user.username ? user.username[0] : 'U')).toUpperCase();
                if (user.profile_picture) {
                    userAvatarEl.innerHTML = `<img src="${user.profile_picture}" alt="${user.username}" style="width:100%; height:100%; object-fit:cover; border-radius:50%; display:block;" onerror="this.outerHTML='<span style=\\'font-weight:800;\\'>${initial}</span>';" />`;
                } else {
                    userAvatarEl.innerHTML = `<span style="font-weight:800;">${initial}</span>`;
                }
            }
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
        document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: null } }));

        const isCustomerPortal = window.location.pathname.includes('customer-portal') || !!document.getElementById('customer-portal-container');
        const isAdminPortal = window.location.pathname.includes('admin-portal');

        if (isCustomerPortal || isAdminPortal) {
            const portalContainer = document.getElementById('customer-portal-container');
            if (portalContainer) portalContainer.style.display = 'none';
            window.location.href = '/';
        }
    }
};
