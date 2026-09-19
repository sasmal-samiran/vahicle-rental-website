// Lightweight SPA Router for Seamless View Swapping
import { Customer } from './customer.js';
import { CustomerPortal } from './customer-portal.js';
import { Admin } from './admin.js';

export const Router = {
    isNavigating: false,

    init() {
        window.addEventListener('popstate', () => {
            this.navigate(window.location.pathname + window.location.search, { pushState: false });
        });

        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:') || 
                href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:') || 
                link.target === '_blank' || link.hasAttribute('download')) {
                return;
            }

            if (href.startsWith('/') && !href.startsWith('/admin/')) {
                const targetUrl = new URL(href, window.location.origin);
                if (targetUrl.pathname === window.location.pathname && targetUrl.hash) {
                    return;
                }
                e.preventDefault();
                this.navigate(href);
            }
        });
    },

    async navigate(url, options = { pushState: true }) {
        if (this.isNavigating) return;
        this.isNavigating = true;

        try {
            const targetUrl = new URL(url, window.location.origin);
            const response = await fetch(targetUrl.href);
            if (!response.ok) {
                window.location.href = url;
                return;
            }

            const html = await response.text();
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const newContainer = doc.getElementById('app-main-container');
            const currentContainer = document.getElementById('app-main-container');

            if (!newContainer || !currentContainer) {
                window.location.href = url;
                return;
            }

            currentContainer.innerHTML = newContainer.innerHTML;
            document.title = doc.title || document.title;

            if (options.pushState !== false) {
                window.history.pushState({}, document.title, url);
            }

            // Bind Search Widget Toggle if present
            const searchWidget = currentContainer.querySelector('.search-widget-card');
            const searchWidgetToggle = currentContainer.querySelector('#search-widget-toggle');
            if (searchWidget && searchWidgetToggle) {
                searchWidgetToggle.addEventListener('click', () => {
                    const isOpen = searchWidget.classList.toggle('search-widget-open');
                    searchWidgetToggle.setAttribute('aria-expanded', String(isOpen));
                });
            }

            // Initialize Destination Components
            if (document.getElementById('cars-grid-container') || document.getElementById('featured-cars-grid')) {
                await Customer.init();
            }

            if (document.getElementById('customer-portal-container')) {
                await CustomerPortal.init();
            }

            if (document.getElementById('revenueTrendChart')) {
                await Admin.init();
            }

            // Scroll Handling
            if (targetUrl.hash) {
                const el = document.querySelector(targetUrl.hash);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }

            window.dispatchEvent(new Event('scroll'));
            window.dispatchEvent(new CustomEvent('spa:navigated', { detail: { url } }));
        } catch (error) {
            console.error('SPA Navigation fallback to hard reload:', error);
            window.location.href = url;
        } finally {
            this.isNavigating = false;
        }
    }
};
