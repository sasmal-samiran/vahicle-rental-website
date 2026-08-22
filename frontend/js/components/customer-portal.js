// Customer Portal Controller
import { API } from './api.js';
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Notifications } from './notifications.js';
import { BookingWizard } from './booking.js';
import { CONFIG, formatCurrency, formatDate } from './config.js';

export const CustomerPortal = {
    bookings: [],

    async init() {
        this.bindEvents();
    },

    bindEvents() {
        document.querySelectorAll('.portal-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                document.querySelectorAll('.portal-tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                document.querySelectorAll('.portal-panel').forEach(p => {
                    p.classList.toggle('hidden', p.dataset.tab !== tab);
                });

                if (tab === 'bookings') this.loadBookings();
                if (tab === 'profile') this.loadProfile();
            });
        });
    },

    openPortalModal(initialTab = 'bookings') {
        if (!API.isAuthenticated()) {
            Toast.info('Please log in to view your portal.');
            Auth.openAuthModal('otp');
            return;
        }

        const modal = document.getElementById('customer-portal-modal');
        if (modal) {
            modal.classList.add('active');
            const tabBtn = document.querySelector(`.portal-tab-btn[data-tab="${initialTab}"]`);
            if (tabBtn) tabBtn.click();
        }
    },

    closePortalModal() {
        const modal = document.getElementById('customer-portal-modal');
        if (modal) modal.classList.remove('active');
    },

    async loadBookings() {
        const listEl = document.getElementById('portal-bookings-list');
        if (listEl) {
            listEl.innerHTML = '<div style="text-align:center; padding:40px;"><i class="fa-solid fa-circle-notch fa-spin text-gradient" style="font-size:2rem;"></i></div>';
        }

        try {
            const data = await API.get('/bookings/');
            this.bookings = data.results || data;
            this.renderBookings();
        } catch (e) {
            if (listEl) listEl.innerHTML = `<div style="color:var(--danger); padding:20px;">${e.message}</div>`;
        }
    },

    renderBookings() {
        const listEl = document.getElementById('portal-bookings-list');
        if (!listEl) return;

        if (!this.bookings.length) {
            listEl.innerHTML = `
                <div style="text-align:center; padding:40px; color:var(--text-muted);">
                    <i class="fa-solid fa-car" style="font-size:2.5rem; margin-bottom:12px;"></i>
                    <p>You haven't made any reservations yet.</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = this.bookings.map(b => {
            const statusBadges = {
                PENDING: 'badge-warning',
                CONFIRMED: 'badge-primary',
                ONGOING: 'badge-success',
                COMPLETED: 'badge-info',
                CANCELLED: 'badge-danger'
            };

            const isCompleted = b.status === 'COMPLETED';
            const isCancellable = ['PENDING', 'CONFIRMED'].includes(b.status);

            return `
                <div class="card" style="background:var(--bg-input); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:20px; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; flex-wrap:wrap; gap:10px;">
                        <div>
                            <span class="badge ${statusBadges[b.status] || 'badge-primary'}">${b.status}</span>
                            <span style="font-family:monospace; font-weight:700; margin-left:8px; font-size:0.9rem;">${b.booking_code}</span>
                            <h3 style="font-size:1.15rem; font-weight:700; margin-top:6px;">${b.car?.year || ''} ${b.car?.brand || ''} ${b.car?.model || ''}</h3>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.2rem; font-weight:800; color:#fff;">${formatCurrency(b.total_amount)}</div>
                            <span class="badge ${b.payment_status === 'PAID' ? 'badge-success' : 'badge-warning'}">${b.payment_status}</span>
                        </div>
                    </div>

                    <div class="status-tracker">
                        <div class="tracker-step ${['PENDING', 'CONFIRMED', 'ONGOING', 'COMPLETED'].includes(b.status) ? 'completed' : ''}">
                            <div class="tracker-dot"><i class="fa-solid fa-calendar-check"></i></div>
                            <span class="tracker-label">Reserved</span>
                        </div>
                        <div class="tracker-step ${['CONFIRMED', 'ONGOING', 'COMPLETED'].includes(b.status) ? 'completed' : ''}">
                            <div class="tracker-dot"><i class="fa-solid fa-circle-check"></i></div>
                            <span class="tracker-label">Confirmed</span>
                        </div>
                        <div class="tracker-step ${b.status === 'ONGOING' ? 'active' : (b.status === 'COMPLETED' ? 'completed' : '')}">
                            <div class="tracker-dot"><i class="fa-solid fa-car-side"></i></div>
                            <span class="tracker-label">Picked Up</span>
                        </div>
                        <div class="tracker-step ${b.status === 'COMPLETED' ? 'completed' : ''}">
                            <div class="tracker-dot"><i class="fa-solid fa-flag-checkered"></i></div>
                            <span class="tracker-label">Returned</span>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; font-size:0.85rem; color:var(--text-secondary); margin:14px 0; padding:10px; background:rgba(0,0,0,0.2); border-radius:var(--radius-sm);">
                        <div><i class="fa-solid fa-location-dot"></i> Pickup: ${b.pickup_location?.name || 'City Hub'}</div>
                        <div><i class="fa-solid fa-location-arrow"></i> Return: ${b.return_location?.name || 'City Hub'}</div>
                        <div><i class="fa-regular fa-clock"></i> Start: ${formatDate(b.start_date)}</div>
                        <div><i class="fa-regular fa-clock"></i> End: ${formatDate(b.end_date)}</div>
                    </div>

                    <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:14px;">
                        <button class="btn btn-outline btn-sm" onclick="CustomerPortal.viewVoucher('${b.booking_code}')">
                            <i class="fa-solid fa-file-invoice"></i> View Voucher
                        </button>
                        ${isCancellable ? `
                            <button class="btn btn-danger btn-sm" onclick="CustomerPortal.cancelBooking('${b.booking_code}')">
                                <i class="fa-solid fa-ban"></i> Cancel Booking
                            </button>
                        ` : ''}
                        ${isCompleted ? `
                            <button class="btn btn-primary btn-sm" onclick="CustomerPortal.openReviewModal('${b.booking_code}', ${b.car?.id})">
                                <i class="fa-solid fa-star"></i> Leave Review
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },

    async viewVoucher(bookingCode) {
        try {
            const b = await API.get(`/bookings/${bookingCode}/`);
            BookingWizard.activeBooking = b;
            BookingWizard.currentStep = 5;
            BookingWizard.openWizardModal();
            BookingWizard.updateStepView();
            BookingWizard.showConfirmationStep();
        } catch (e) {
            Toast.error('Could not load voucher.');
        }
    },

    async cancelBooking(bookingCode) {
        if (!confirm('Are you sure you want to cancel this booking? Any eligible refund will be returned to your original payment method.')) {
            return;
        }

        try {
            await API.post(`/bookings/${bookingCode}/cancel/`, { reason: 'Customer cancelled from portal' });
            Toast.success('Booking successfully cancelled.');
            this.loadBookings();
            Notifications.fetchNotifications();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    openReviewModal(bookingCode, carId) {
        const modal = document.getElementById('review-modal');
        if (modal) {
            document.getElementById('rev-booking-code').value = bookingCode;
            document.getElementById('rev-title').value = '';
            document.getElementById('rev-comment').value = '';
            modal.classList.add('active');
        }
    },

    closeReviewModal() {
        const modal = document.getElementById('review-modal');
        if (modal) modal.classList.remove('active');
    },

    async submitReview() {
        const bookingCode = document.getElementById('rev-booking-code').value;
        const rating = parseInt(document.querySelector('input[name="rev-rating"]:checked')?.value || 5);
        const title = document.getElementById('rev-title').value.trim();
        const comment = document.getElementById('rev-comment').value.trim();

        if (!comment) {
            Toast.error('Please write a short review comment.');
            return;
        }

        try {
            await API.post('/reviews/create/', {
                booking_code: bookingCode,
                rating,
                title,
                comment
            });
            Toast.success('Thank you! Your verified review has been submitted.');
            this.closeReviewModal();
            this.loadBookings();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    async loadProfile() {
        try {
            const user = await API.get('/auth/profile/');
            document.getElementById('prof-first-name').value = user.first_name || '';
            document.getElementById('prof-last-name').value = user.last_name || '';
            document.getElementById('prof-email').value = user.email || '';
            document.getElementById('prof-phone').value = user.phone_number || '';
            document.getElementById('prof-license').value = user.driver_license_number || '';
            document.getElementById('prof-address').value = user.address || '';
        } catch (e) {
            Toast.error('Could not load profile.');
        }
    },

    async saveProfile() {
        const data = {
            first_name: document.getElementById('prof-first-name').value.trim(),
            last_name: document.getElementById('prof-last-name').value.trim(),
            email: document.getElementById('prof-email').value.trim(),
            driver_license_number: document.getElementById('prof-license').value.trim(),
            address: document.getElementById('prof-address').value.trim()
        };

        try {
            const updated = await API.patch('/auth/profile/', data);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(updated));
            Toast.success('Profile updated successfully.');
            Auth.updateNavUser();
        } catch (e) {
            Toast.error(e.message);
        }
    }
};
