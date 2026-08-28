// Customer Portal Controller
import { API } from './api.js';
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Notifications } from './notifications.js';
import { BookingWizard } from './booking.js';
import { CONFIG, formatCurrency, formatDate } from './config.js';

export const CustomerPortal = {
    bookings: [],
    currentUser: null,
    editingReview: false,
    activeStatusFilter: 'ALL',
    selectedAvatarFile: null,
    removeAvatarFlag: false,

    async init() {
        const isPortalPage = !!document.getElementById('customer-portal-container');

        if (isPortalPage) {
            this.bindEvents();
            this.bindReviewRating();

            if (!API.isAuthenticated()) {
                this.renderUnauthenticatedState();
                return;
            }

            await this.loadProfileHeader();
            await this.loadBookings();

            // Check initial URL tab parameter (e.g. ?tab=profile or ?tab=reviews)
            const params = new URLSearchParams(window.location.search);
            const initialTab = params.get('tab') || 'bookings';
            this.switchTab(initialTab);
        } else {
            this.bindReviewRating();
        }
    },

    handleAvatarFileSelect(event) {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
            Toast.error('Please upload a valid JPEG, PNG, or WEBP image.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            Toast.error('Profile photo size exceeds 5MB limit.');
            return;
        }

        this.selectedAvatarFile = file;
        this.removeAvatarFlag = false;

        const reader = new FileReader();
        reader.onload = (e) => {
            const previewEl = document.getElementById('prof-avatar-preview');
            const headerAvatarEl = document.getElementById('portal-header-avatar');
            const removeBtn = document.getElementById('prof-avatar-remove-btn');

            if (previewEl) {
                previewEl.innerHTML = `<img src="${e.target.result}" alt="Preview" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />`;
            }
            if (headerAvatarEl) {
                headerAvatarEl.innerHTML = `<img src="${e.target.result}" alt="Preview" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />`;
            }
            if (removeBtn) removeBtn.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    },

    removeAvatar() {
        this.selectedAvatarFile = null;
        this.removeAvatarFlag = true;

        const fileInput = document.getElementById('prof-avatar-input');
        if (fileInput) fileInput.value = '';

        const previewEl = document.getElementById('prof-avatar-preview');
        const headerAvatarEl = document.getElementById('portal-header-avatar');
        const removeBtn = document.getElementById('prof-avatar-remove-btn');

        const initial = (this.currentUser?.first_name ? this.currentUser.first_name[0] : 'U').toUpperCase();
        if (previewEl) previewEl.innerHTML = `<span>${initial}</span>`;
        if (headerAvatarEl) headerAvatarEl.innerHTML = `<span>${initial}</span>`;
        if (removeBtn) removeBtn.classList.add('hidden');
    },

    async loadProfileHeader() {
        try {
            const user = await API.get('/auth/profile/');
            this.currentUser = user;

            const nameEl = document.getElementById('portal-header-name');
            const avatarEl = document.getElementById('portal-header-avatar');
            const previewEl = document.getElementById('prof-avatar-preview');
            const removeBtn = document.getElementById('prof-avatar-remove-btn');
            const emailEl = document.getElementById('portal-header-email');
            const phoneEl = document.getElementById('portal-header-phone');
            const joinedEl = document.getElementById('portal-header-joined');
            const badgeEl = document.getElementById('portal-license-badge');

            const displayName = (user.first_name || user.last_name)
                ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                : (user.phone_number || 'Valued Customer');

            const initial = (user.first_name ? user.first_name[0] : (displayName[0] || 'U')).toUpperCase();

            if (nameEl) nameEl.innerText = displayName;

            if (avatarEl) {
                if (user.profile_picture) {
                    avatarEl.innerHTML = `<img src="${user.profile_picture}" alt="${displayName}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />`;
                } else {
                    avatarEl.innerHTML = `<span>${initial}</span>`;
                }
            }

            if (previewEl) {
                if (user.profile_picture) {
                    previewEl.innerHTML = `<img src="${user.profile_picture}" alt="${displayName}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />`;
                    if (removeBtn) removeBtn.classList.remove('hidden');
                } else {
                    previewEl.innerHTML = `<span>${initial}</span>`;
                    if (removeBtn) removeBtn.classList.add('hidden');
                }
            }

            if (emailEl) emailEl.innerHTML = `<i class="fa-regular fa-envelope"></i> ${user.email || 'No email attached'}`;
            if (phoneEl) phoneEl.innerHTML = `<i class="fa-solid fa-phone"></i> ${user.phone_number || '--'}`;
            if (joinedEl && user.date_joined) {
                joinedEl.innerHTML = `<i class="fa-regular fa-calendar"></i> Member since ${new Date(user.date_joined).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}`;
            }

            if (badgeEl) {
                if (user.driver_license_number) {
                    badgeEl.className = 'portal-license-badge verified';
                    badgeEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> License Verified (${user.driver_license_number})`;
                } else {
                    badgeEl.className = 'portal-license-badge';
                    badgeEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Driver License Pending`;
                }
            }

            this.fillProfileForm(user);
        } catch (e) {
            console.error('Could not load profile header:', e);
        }
    },

    bindEvents() {
        document.querySelectorAll('.portal-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
    },

    switchTab(tabName) {
        document.querySelectorAll('.portal-tab-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tabName);
        });

        document.querySelectorAll('.portal-tab-panel').forEach(p => {
            p.classList.toggle('hidden', p.dataset.tab !== tabName);
        });

        // Update URL query parameter without full reload
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('tab', tabName);
        window.history.replaceState({}, '', newUrl);

        if (tabName === 'bookings') {
            this.renderBookings();
        } else if (tabName === 'profile') {
            this.loadProfile();
        } else if (tabName === 'reviews') {
            this.renderReviews();
        }
    },

    bindReviewRating() {
        const ratingInputs = document.querySelectorAll('input[name="rev-rating"]');
        ratingInputs.forEach(input => {
            input.addEventListener('change', () => this.updateReviewRating(input.value));
        });
        const selected = document.querySelector('input[name="rev-rating"]:checked');
        if (selected) this.updateReviewRating(selected.value);
    },

    updateReviewRating(rating) {
        const selectedRating = Number(rating);
        document.querySelectorAll('.review-rating-star').forEach(star => {
            star.classList.toggle('selected', Number(star.dataset.rating) <= selectedRating);
        });
    },

    // Backward compatibility wrapper
    openPortalModal(initialTab = 'bookings') {
        window.location.href = `/customer-portal/?tab=${initialTab}`;
    },

    fillProfileForm(user) {
        if (!user) return;
        const fn = document.getElementById('prof-first-name');
        const ln = document.getElementById('prof-last-name');
        const em = document.getElementById('prof-email');
        const ph = document.getElementById('prof-phone');
        const lc = document.getElementById('prof-license');
        const ad = document.getElementById('prof-address');
        const previewEl = document.getElementById('prof-avatar-preview');
        const removeBtn = document.getElementById('prof-avatar-remove-btn');

        if (fn) fn.value = user.first_name || '';
        if (ln) ln.value = user.last_name || '';
        if (em) em.value = user.email || '';
        if (ph) ph.value = user.phone_number || '';
        if (lc) lc.value = user.driver_license_number || '';
        if (ad) ad.value = user.address || '';

        const displayName = (user.first_name || user.last_name)
            ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
            : (user.phone_number || 'Valued Customer');
        const initial = (user.first_name ? user.first_name[0] : (displayName[0] || 'U')).toUpperCase();

        if (previewEl) {
            if (user.profile_picture) {
                previewEl.innerHTML = `<img src="${user.profile_picture}" alt="${displayName}" style="width:100%; height:100%; object-fit:cover; border-radius:50%; display:block;" />`;
                if (removeBtn) removeBtn.classList.remove('hidden');
            } else {
                previewEl.innerHTML = `<span>${initial}</span>`;
                if (removeBtn) removeBtn.classList.add('hidden');
            }
        }
    },

    async loadProfile() {
        if (!this.currentUser) {
            await this.loadProfileHeader();
        } else {
            this.fillProfileForm(this.currentUser);
        }
    },

    async loadBookings() {
        const listEl = document.getElementById('portal-bookings-list');
        if (listEl) {
            listEl.innerHTML = '<div style="text-align:center; padding:60px 0;"><i class="fa-solid fa-circle-notch fa-spin text-gradient" style="font-size:2.4rem;"></i><p style="margin-top:14px; color:var(--text-secondary);">Loading your reservations...</p></div>';
        }

        try {
            const data = await API.get('/bookings/');
            this.bookings = data.results || data;
            this.updateKPICounters();
            this.renderBookings();
            this.renderReviews();
        } catch (e) {
            if (listEl) listEl.innerHTML = `<div style="color:var(--danger); padding:20px; text-align:center;">${e.message}</div>`;
        }
    },

    updateKPICounters() {
        const activeCount = this.bookings.filter(b => ['CONFIRMED', 'ONGOING'].includes(b.status)).length;
        const totalCount = this.bookings.length;
        const completedCount = this.bookings.filter(b => b.status === 'COMPLETED').length;
        const totalSpent = this.bookings
            .filter(b => b.status !== 'CANCELLED')
            .reduce((sum, b) => sum + parseFloat(b.total_amount || 0), 0);

        const reviewCount = this.bookings.filter(b => b.has_reviewed && b.review).length;

        const kpiActive = document.getElementById('portal-kpi-active');
        const kpiTotal = document.getElementById('portal-kpi-total');
        const kpiCompleted = document.getElementById('portal-kpi-completed');
        const kpiSpent = document.getElementById('portal-kpi-spent');
        const tabBookingsCount = document.getElementById('portal-tab-bookings-count');
        const tabReviewsCount = document.getElementById('portal-tab-reviews-count');

        if (kpiActive) kpiActive.innerText = activeCount;
        if (kpiTotal) kpiTotal.innerText = totalCount;
        if (kpiCompleted) kpiCompleted.innerText = completedCount;
        if (kpiSpent) kpiSpent.innerText = formatCurrency(totalSpent);
        if (tabBookingsCount) tabBookingsCount.innerText = totalCount;
        if (tabReviewsCount) tabReviewsCount.innerText = reviewCount;
    },

    filterBookings(filterType, pillBtn) {
        this.activeStatusFilter = filterType;
        if (pillBtn) {
            document.querySelectorAll('.portal-filter-pill').forEach(p => p.classList.remove('active'));
            pillBtn.classList.add('active');
        }
        this.renderBookings();
    },

    renderBookings() {
        const listEl = document.getElementById('portal-bookings-list');
        if (!listEl) return;

        let displayBookings = this.bookings;
        if (this.activeStatusFilter === 'ACTIVE') {
            displayBookings = this.bookings.filter(b => ['PENDING', 'CONFIRMED', 'ONGOING'].includes(b.status));
        } else if (this.activeStatusFilter === 'COMPLETED') {
            displayBookings = this.bookings.filter(b => b.status === 'COMPLETED');
        } else if (this.activeStatusFilter === 'CANCELLED') {
            displayBookings = this.bookings.filter(b => b.status === 'CANCELLED');
        }

        if (!displayBookings.length) {
            listEl.innerHTML = `
                <div style="text-align:center; padding:60px 20px; background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius-lg);">
                    <i class="fa-solid fa-car" style="font-size:3rem; margin-bottom:16px; color:var(--text-muted); opacity:0.6;"></i>
                    <h4 style="font-size:1.2rem; font-weight:700; color:var(--text-primary); margin-bottom:6px;">No reservations found</h4>
                    <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px; margin:0 auto 20px;">
                        ${this.activeStatusFilter === 'ALL'
                            ? "You haven't made any reservations yet. Browse our premium fleet and book your first drive!"
                            : `You do not have any ${this.activeStatusFilter.toLowerCase()} reservations at this time.`}
                    </p>
                    <a href="/fleet/" class="btn btn-primary btn-sm">
                        <i class="fa-solid fa-magnifying-glass"></i> Browse Available Vehicles
                    </a>
                </div>
            `;
            return;
        }

        listEl.innerHTML = displayBookings.map(b => {
            const statusBadges = {
                PENDING: 'badge-warning',
                CONFIRMED: 'badge-primary',
                ONGOING: 'badge-success',
                COMPLETED: 'badge-info',
                CANCELLED: 'badge-danger'
            };

            const isCompleted = b.status === 'COMPLETED';
            const isCancellable = ['PENDING', 'CONFIRMED'].includes(b.status);

            const carImage = b.car?.primary_image || b.car?.main_image_url || '/static/images/car_placeholder.jpg';

            return `
                <div class="card" style="background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:24px; margin-bottom:20px; box-shadow:var(--shadow-sm);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
                        <div style="display:flex; gap:16px; align-items:center;">
                            <img src="${carImage}" alt="${b.car?.display_name || 'Vehicle'}" style="width:90px; height:60px; object-fit:cover; border-radius:var(--radius-sm); border:1px solid var(--border-color);" />
                            <div>
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <span class="badge ${statusBadges[b.status] || 'badge-primary'}">${b.status}</span>
                                    <span style="font-family:monospace; font-weight:700; font-size:0.9rem; color:var(--text-secondary);">#${b.booking_code}</span>
                                </div>
                                <h3 style="font-size:1.25rem; font-weight:800; margin-top:4px; color:var(--text-primary);">
                                    ${b.car?.year || ''} ${b.car?.brand || ''} ${b.car?.model || ''}
                                </h3>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.35rem; font-weight:800; color:var(--text-primary);">${formatCurrency(b.total_amount)}</div>
                            <span class="badge ${b.payment_status === 'PAID' ? 'badge-success' : 'badge-warning'}">
                                <i class="fa-solid fa-credit-card"></i> ${b.payment_status}
                            </span>
                        </div>
                    </div>

                    <!-- 4-Stage Reservation Tracker -->
                    <div class="status-tracker" style="margin:20px 0;">
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

                    <!-- Itinerary Hub Grid -->
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; font-size:0.85rem; color:var(--text-secondary); margin:16px 0; padding:14px; background:#f8fafc; border-radius:var(--radius-md); border:1px solid #e2e8f0;">
                        <div><strong style="color:var(--text-primary);"><i class="fa-solid fa-location-dot" style="color:var(--primary);"></i> Pickup Hub:</strong> ${b.pickup_location?.name || 'City Hub'}</div>
                        <div><strong style="color:var(--text-primary);"><i class="fa-solid fa-location-arrow" style="color:var(--info);"></i> Return Hub:</strong> ${b.return_location?.name || 'City Hub'}</div>
                        <div><strong style="color:var(--text-primary);"><i class="fa-regular fa-calendar"></i> Pickup:</strong> ${formatDate(b.start_date)}</div>
                        <div><strong style="color:var(--text-primary);"><i class="fa-regular fa-calendar-check"></i> Return:</strong> ${formatDate(b.end_date)}</div>
                    </div>

                    <!-- Action Bar -->
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-top:16px; border-top:1px solid var(--border-color); padding-top:14px;">
                        <div style="font-size:0.85rem; color:var(--text-muted);">
                            <i class="fa-solid fa-shield-halved"></i> Comprehensive Insurance Coverage Included
                        </div>
                        <div style="display:flex; gap:10px; flex-wrap:wrap;">
                            <button class="btn btn-outline btn-sm" onclick="CustomerPortal.viewVoucher('${b.booking_code}')">
                                <i class="fa-solid fa-file-invoice"></i> View Voucher
                            </button>
                            ${isCancellable ? `
                                <button class="btn btn-danger btn-sm" onclick="CustomerPortal.cancelBooking('${b.booking_code}')">
                                    <i class="fa-solid fa-ban"></i> Cancel Booking
                                </button>
                            ` : ''}
                            ${isCompleted && !b.has_reviewed ? `
                                <button class="btn btn-primary btn-sm" onclick="CustomerPortal.openReviewModal('${b.booking_code}', ${b.car?.id})">
                                    <i class="fa-solid fa-star"></i> Leave Review
                                </button>
                            ` : b.has_reviewed && b.review ? `
                                <button class="btn btn-outline btn-sm" onclick="CustomerPortal.openEditReviewModal('${b.booking_code}')">
                                    <i class="fa-solid fa-pen"></i> Edit Review (${b.review.rating}/5 <i class="fa-solid fa-star" style="color:#f59e0b; font-size:0.8rem;"></i>)
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderStars(rating) {
        const r = Math.max(0, Math.min(5, Number(rating) || 0));
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= r) {
                stars += '<i class="fa-solid fa-star" style="color:#f59e0b;"></i>';
            } else {
                stars += '<i class="fa-solid fa-star" style="color:#cbd5e1;"></i>';
            }
        }
        return stars;
    },

    renderReviews() {
        const listEl = document.getElementById('portal-reviews-list');
        if (!listEl) return;

        const reviewedBookings = this.bookings.filter(b => b.has_reviewed && b.review);

        if (!reviewedBookings.length) {
            listEl.innerHTML = `
                <div style="text-align:center; padding:60px 20px; background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius-lg);">
                    <i class="fa-solid fa-star" style="font-size:3rem; margin-bottom:16px; color:#f59e0b; opacity:0.6;"></i>
                    <h4 style="font-size:1.2rem; font-weight:700; color:var(--text-primary); margin-bottom:6px;">No reviews left yet</h4>
                    <p style="color:var(--text-secondary); font-size:0.9rem; max-width:420px; margin:0 auto 20px;">
                        Once you complete a rental, you can share your experience and rate the vehicle right here.
                    </p>
                    <button type="button" class="btn btn-outline btn-sm" onclick="CustomerPortal.switchTab('bookings')">
                        <i class="fa-solid fa-calendar-check"></i> View Completed Reservations
                    </button>
                </div>
            `;
            return;
        }

        listEl.innerHTML = reviewedBookings.map(b => {
            const r = b.review;
            return `
                <div class="card" style="background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:24px; margin-bottom:18px; box-shadow:var(--shadow-sm);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
                        <div>
                            <div style="display:flex; gap:4px; font-size:1.1rem; margin-bottom:6px;">
                                ${this.renderStars(r.rating)}
                            </div>
                            <h4 style="font-size:1.15rem; font-weight:800; color:var(--text-primary); margin-bottom:4px;">
                                ${r.title || 'Verified Rental Experience'}
                            </h4>
                            <div style="font-size:0.85rem; color:var(--text-muted);">
                                Vehicle: <strong>${b.car?.year || ''} ${b.car?.brand || ''} ${b.car?.model || ''}</strong> &bull; Booking: #${b.booking_code}
                            </div>
                        </div>
                        <button class="btn btn-outline btn-sm" onclick="CustomerPortal.openEditReviewModal('${b.booking_code}')">
                            <i class="fa-solid fa-pen"></i> Edit Feedback
                        </button>
                    </div>
                    <p style="font-size:0.95rem; color:var(--text-secondary); line-height:1.6; margin:0; padding:14px; background:#f8fafc; border-radius:var(--radius-md); border-left:3px solid var(--primary);">
                        "${r.comment}"
                    </p>
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
            await this.loadBookings();
            Notifications.fetchNotifications();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    openReviewModal(bookingCode, carId) {
        const modal = document.getElementById('review-modal');
        if (modal) {
            this.editingReview = false;
            modal.querySelector('.modal-title').innerText = 'Review Your Rental Experience';
            modal.querySelector('.modal-footer .btn-primary').innerHTML = 'Submit Review';
            document.getElementById('rev-booking-code').value = bookingCode;
            const defaultRating = document.querySelector('input[name="rev-rating"][value="5"]');
            if (defaultRating) {
                defaultRating.checked = true;
                this.updateReviewRating(5);
            }
            document.getElementById('rev-title').value = '';
            document.getElementById('rev-comment').value = '';
            modal.classList.add('active');
        }
    },

    openEditReviewModal(bookingCode) {
        const modal = document.getElementById('review-modal');
        if (!modal) return;

        const booking = this.bookings.find(item => item.booking_code === bookingCode);
        const review = booking?.review;
        if (!review) return;

        this.editingReview = true;
        modal.querySelector('.modal-title').innerText = 'Edit Your Review';
        modal.querySelector('.modal-footer .btn-primary').innerHTML = 'Save Changes';
        document.getElementById('rev-booking-code').value = bookingCode;
        const targetRatingInput = document.querySelector(`input[name="rev-rating"][value="${review.rating}"]`);
        if (targetRatingInput) {
            targetRatingInput.checked = true;
        }
        this.updateReviewRating(review.rating);
        document.getElementById('rev-title').value = review.title || '';
        document.getElementById('rev-comment').value = review.comment || '';
        modal.classList.add('active');
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
            const reviewData = { rating, title, comment };
            if (this.editingReview) {
                await API.patch(`/reviews/${bookingCode}/update/`, reviewData);
                Toast.success('Your review has been updated.');
            } else {
                await API.post('/reviews/create/', { booking_code: bookingCode, ...reviewData });
                Toast.success('Thank you! Your verified review has been submitted.');
            }
            this.closeReviewModal();
            this.editingReview = false;
            await this.loadBookings();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    async saveProfile() {
        const saveBtn = document.getElementById('prof-save-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Saving...';
        }

        const formData = new FormData();
        formData.append('first_name', document.getElementById('prof-first-name')?.value.trim() || '');
        formData.append('last_name', document.getElementById('prof-last-name')?.value.trim() || '');
        formData.append('email', document.getElementById('prof-email')?.value.trim() || '');
        formData.append('driver_license_number', document.getElementById('prof-license')?.value.trim() || '');
        formData.append('address', document.getElementById('prof-address')?.value.trim() || '');

        if (this.selectedAvatarFile) {
            formData.append('profile_picture', this.selectedAvatarFile);
        } else if (this.removeAvatarFlag) {
            formData.append('profile_picture', '');
        }

        try {
            const updated = await API.patch('/auth/profile/', formData);
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(updated));
            this.currentUser = updated;
            this.selectedAvatarFile = null;
            this.removeAvatarFlag = false;

            Toast.success('Profile and photo updated successfully.');
            Auth.updateNavUser();
            await this.loadProfileHeader();
        } catch (e) {
            Toast.error(e.message);
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Profile Changes';
            }
        }
    }
};
