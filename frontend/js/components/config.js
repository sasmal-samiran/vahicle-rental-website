// Configuration
export const CONFIG = {
    API_BASE: window.location.origin + '/api',
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'cr_access_token',
        REFRESH_TOKEN: 'cr_refresh_token',
        USER: 'cr_user_profile',
        SEARCH_PARAMS: 'cr_search_params'
    },
    CURRENCY: '₹'
};

export function formatCurrency(amount) {
    const num = parseFloat(amount) || 0;
    return CONFIG.CURRENCY + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function formatForInput(date) {
    const d = date ? new Date(date) : new Date();
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
}
