// Notifications Center
import { API } from './api.js';
import { Toast } from './toast.js';
import { formatDateTime } from './config.js';

export const Notifications = {
    unreadCount: 0,
    pollInterval: null,

    init() {
        if (API.isAuthenticated()) {
            this.fetchNotifications();
            this.startPolling();
        }
        document.addEventListener('auth:change', (e) => {
            if (e.detail.user) {
                this.fetchNotifications();
                this.startPolling();
            } else {
                this.stopPolling();
                this.updateBadge(0);
            }
        });
    },

    startPolling() {
        this.stopPolling();
        this.pollInterval = setInterval(() => this.fetchNotifications(), 20000);
    },

    stopPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
    },

    async fetchNotifications() {
        if (!API.isAuthenticated()) return;
        try {
            const data = await API.get('/notifications/');
            this.unreadCount = data.unread_count || 0;
            this.updateBadge(this.unreadCount);
            this.renderList(data.notifications || []);
        } catch (e) {
            console.error('Notification error:', e);
        }
    },

    updateBadge(count) {
        const badge = document.getElementById('notif-badge');
        if (badge) {
            badge.innerText = count;
            badge.classList.toggle('hidden', count === 0);
        }
    },

    renderList(list) {
        const container = document.getElementById('notif-list-container');
        if (!container) return;

        if (!list.length) {
            container.innerHTML = '<div style="padding:24px; text-align:center; color:var(--text-muted); font-size:0.85rem;">No notifications yet.</div>';
            return;
        }

        container.innerHTML = list.map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="Notifications.markRead(${n.id})">
                <div class="notif-title">${n.title}</div>
                <div class="notif-msg">${n.message}</div>
                <div class="notif-time">${formatDateTime(n.created_at)}</div>
            </div>
        `).join('');
    },

    async markRead(id) {
        try {
            await API.patch(`/notifications/${id}/read/`);
            this.fetchNotifications();
        } catch (e) {
            console.error(e);
        }
    },

    async markAllRead() {
        try {
            await API.post('/notifications/read-all/');
            this.fetchNotifications();
            Toast.success('All notifications marked as read.');
        } catch (e) {
            console.error(e);
        }
    },

    toggleDropdown() {
        const dropdown = document.getElementById('notif-dropdown-menu');
        if (dropdown) dropdown.classList.toggle('show');
    }
};
