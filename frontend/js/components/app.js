// Main App Initializer
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Notifications } from './notifications.js';
import { Customer } from './customer.js';
import { CustomerPortal } from './customer-portal.js';
import { Admin } from './admin.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Components
    Toast.init();
    Auth.init();
    Notifications.init();

    const params = new URLSearchParams(window.location.search);
    const redirectMessage = sessionStorage.getItem('authRedirectMessage');
    if (params.get('auth') === 'required') {
        Auth.openAuthModal('password');
        if (redirectMessage) {
            Toast.error(redirectMessage);
            sessionStorage.removeItem('authRedirectMessage');
        }
        window.history.replaceState({}, document.title, '/');
    }
    
    if (document.getElementById('cars-grid-container') || document.getElementById('featured-cars-grid')) {
        Customer.init();
        CustomerPortal.init();
    }

    if (document.getElementById('revenueTrendChart')) {
        Admin.init();
    }

    const searchWidget = document.querySelector('.search-widget-card');
    const searchWidgetToggle = document.getElementById('search-widget-toggle');
    if (searchWidget && searchWidgetToggle) {
        searchWidgetToggle.addEventListener('click', () => {
            const isOpen = searchWidget.classList.toggle('search-widget-open');
            searchWidgetToggle.setAttribute('aria-expanded', String(isOpen));
        });
    }

    // 2. Navbar Scroll Effect & ScrollSpy (Light Theme)
    const navbar = document.querySelector('.navbar');
    const navLinksList = document.querySelectorAll('.nav-links a');
    const currentPath = window.location.pathname;

    const updateActiveNav = () => {
        if (navbar) {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }

        if (currentPath === '/' || currentPath === '') {
            const featuresSec = document.getElementById('features-section');
            const howItWorksSec = document.getElementById('how-it-works-section');
            const scrollPos = window.scrollY + 140;

            let activeTarget = 'home';
            if (howItWorksSec && scrollPos >= howItWorksSec.offsetTop) {
                activeTarget = 'how-it-works';
            } else if (featuresSec && scrollPos >= featuresSec.offsetTop) {
                activeTarget = 'features';
            }

            navLinksList.forEach(link => {
                const href = link.getAttribute('href') || '';
                if (activeTarget === 'how-it-works' && href.includes('how-it-works')) {
                    link.classList.add('active');
                } else if (activeTarget === 'features' && href.includes('features')) {
                    link.classList.add('active');
                } else if (activeTarget === 'home' && (href === '/' || href === '')) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        } else {
            navLinksList.forEach(link => {
                const href = link.getAttribute('href') || '';
                if (href === currentPath || (href !== '/' && !href.startsWith('/#') && currentPath.startsWith(href))) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }
    };

    window.addEventListener('scroll', updateActiveNav, { passive: true });
    updateActiveNav();

    // 3. Mobile & Tablet Navigation Menu Toggle
    const mobileToggleBtn = document.getElementById('mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    if (mobileToggleBtn && navLinks) {
        mobileToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = navLinks.classList.toggle('mobile-open');
            mobileToggleBtn.innerHTML = isOpen ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>';
        });

        // Close mobile drawer on link tap
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('mobile-open');
                mobileToggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !mobileToggleBtn.contains(e.target)) {
                navLinks.classList.remove('mobile-open');
                mobileToggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
            }
        });
    }

    const adminSidebar = document.querySelector('.admin-sidebar');
    const adminMobileToggle = document.getElementById('admin-mobile-toggle');
    const adminSidebarClose = document.getElementById('admin-sidebar-close');
    const adminSidebarBackdrop = document.getElementById('admin-sidebar-backdrop');
    if (adminSidebar && adminMobileToggle) {
        const setAdminSidebarOpen = (isOpen) => {
            adminSidebar.classList.toggle('mobile-open', isOpen);
            adminSidebarBackdrop?.classList.toggle('active', isOpen);
            adminMobileToggle.setAttribute('aria-expanded', String(isOpen));
            adminMobileToggle.innerHTML = isOpen
                ? '<i class="fa-solid fa-xmark"></i>'
                : '<i class="fa-solid fa-bars"></i>';
        };

        adminMobileToggle.addEventListener('click', () => {
            setAdminSidebarOpen(!adminSidebar.classList.contains('mobile-open'));
        });
        adminSidebarClose?.addEventListener('click', () => setAdminSidebarOpen(false));
        adminSidebarBackdrop?.addEventListener('click', () => setAdminSidebarOpen(false));
        document.querySelectorAll('.sidebar-link[data-view]').forEach(link => {
            link.addEventListener('click', () => setAdminSidebarOpen(false));
        });
    }

    // 4. User Menu Dropdown Toggle
    const userAvatarBtn = document.getElementById('nav-user-btn');
    const userDropdown = document.getElementById('nav-user-dropdown-menu');
    if (userAvatarBtn && userDropdown) {
        userAvatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        document.addEventListener('click', () => userDropdown.classList.remove('show'));
    }

    // 5. Notification Menu Toggle
    const notifBtn = document.getElementById('notif-btn');
    const notifModal = document.getElementById('notification-modal');
    if (notifBtn && notifModal) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notifModal.classList.add('active');
        });
    }

    // 6. Clear modal fields only when the close button is used.
    document.querySelectorAll('.modal-close').forEach(closeButton => {
        closeButton.addEventListener('click', () => {
            const modal = closeButton.closest('.modal-backdrop');
            if (!modal) return;

            modal.querySelectorAll('input, select, textarea').forEach(field => {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    field.checked = false;
                } else {
                    field.value = '';
                }
            });

            const otpStepOne = modal.querySelector('#otp-step-1');
            const otpStepTwo = modal.querySelector('#otp-step-2');
            const otpPreview = modal.querySelector('#dev-otp-preview');
            if (otpStepOne) otpStepOne.classList.remove('hidden');
            if (otpStepTwo) otpStepTwo.classList.add('hidden');
            if (otpPreview) otpPreview.classList.add('hidden');

            const targetModalId = closeButton.dataset.closeModal;
            if (targetModalId) {
                document.getElementById(targetModalId)?.classList.remove('active');
            }
        }, true);
    });
});
