// Modern Toast Notifications
export const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', title = '', duration = 4000) {
        this.init();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-slide-in`;

        const icons = {
            success: 'fa-circle-check',
            error: 'fa-circle-exclamation',
            warning: 'fa-triangle-exclamation',
            info: 'fa-circle-info'
        };

        const iconClass = icons[type] || icons.info;
        toast.innerHTML = `
            <div class="toast-icon"><i class="fa-solid ${iconClass}"></i></div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;

        toast.querySelector('.toast-close').onclick = () => this.dismiss(toast);
        this.container.appendChild(toast);

        setTimeout(() => this.dismiss(toast), duration);
    },

    success(msg, title = 'Success') { this.show(msg, 'success', title); },
    error(msg, title = 'Error') { this.show(msg, 'error', title, 6000); },
    warning(msg, title = 'Warning') { this.show(msg, 'warning', title); },
    info(msg, title = 'Information') { this.show(msg, 'info', title); },

    dismiss(toast) {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentElement) toast.parentElement.removeChild(toast);
        }, 300);
    }
};
