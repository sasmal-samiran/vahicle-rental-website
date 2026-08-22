// REST API Client
import { CONFIG } from './config.js';

export const API = {
    getHeaders(contentType = true) {
        const headers = {};
        if (contentType) headers['Content-Type'] = 'application/json';
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    },

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${CONFIG.API_BASE}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(!(options.body instanceof FormData)),
                ...options.headers
            }
        };

        try {
            let response = await fetch(url, config);

            if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/token/refresh')) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    config.headers['Authorization'] = `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN)}`;
                    response = await fetch(url, config);
                } else {
                    this.clearAuth();
                }
            }

            if (response.status === 204) return null;
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const errorMsg = data.error || data.detail || (data.non_field_errors ? data.non_field_errors[0] : null) || 'An error occurred.';
                throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
            }
            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    },

    async get(endpoint, params = null) {
        let url = endpoint;
        if (params) {
            const searchParams = new URLSearchParams();
            Object.keys(params).forEach(key => {
                if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                    searchParams.append(key, params[key]);
                }
            });
            const qs = searchParams.toString();
            if (qs) url += (url.includes('?') ? '&' : '?') + qs;
        }
        return this.request(url, { method: 'GET' });
    },

    async post(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: body instanceof FormData ? body : JSON.stringify(body)
        });
    },

    async patch(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: body instanceof FormData ? body : JSON.stringify(body)
        });
    },

    async put(endpoint, body = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: body instanceof FormData ? body : JSON.stringify(body)
        });
    },

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    async refreshToken() {
        const refresh = localStorage.getItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
        if (!refresh) return false;
        try {
            const res = await fetch(`${CONFIG.API_BASE}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });
            if (res.ok) {
                const data = await res.json();
                localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, data.access);
                if (data.refresh) localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, data.refresh);
                return true;
            }
        } catch (e) {
            console.error('Refresh token failed:', e);
        }
        return false;
    },

    clearAuth() {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
        document.dispatchEvent(new CustomEvent('auth:change', { detail: { user: null } }));
    },

    getUser() {
        try {
            const userStr = localStorage.getItem(CONFIG.STORAGE_KEYS.USER);
            return userStr ? JSON.parse(userStr) : null;
        } catch (e) {
            return null;
        }
    },

    isAuthenticated() {
        return !!localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    },

    isAdmin() {
        const user = this.getUser();
        return user && (user.role === 'ADMIN' || user.is_staff || user.is_superuser);
    }
};
