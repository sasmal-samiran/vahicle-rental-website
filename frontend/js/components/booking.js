// Multi-Step Booking Wizard & Payment Launcher
import { API } from './api.js';
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Notifications } from './notifications.js';
import { formatCurrency, formatDate, formatDateTime } from './config.js';

export const BookingWizard = {
    currentStep: 1,
    car: null,
    locations: [],
    isScheduleValid: true,
    bookingData: {
        car_id: null,
        pickup_location_id: 1,
        return_location_id: 1,
        start_date: null,
        end_date: null,
        insurance_plan: 'STANDARD',
        addons: [],
        coupon_code: '',
        driver_name: '',
        driver_phone: '',
        driver_email: '',
        driver_license: '',
        special_requests: '',
        payment_method: 'SANDBOX'
    },
    quote: null,
    activeBooking: null,

    populateTimeSelects() {
        const pTimeSelect = document.getElementById('b-pickup-time');
        const rTimeSelect = document.getElementById('b-return-time');
        if (!pTimeSelect || !rTimeSelect) return;

        let options = '';
        for (let h = 6; h <= 23; h++) {
            for (let m of [0, 30]) {
                const hh = String(h).padStart(2, '0');
                const mm = String(m).padStart(2, '0');
                const timeVal = `${hh}:${mm}`;
                const period = h >= 12 ? 'PM' : 'AM';
                const displayH = h % 12 === 0 ? 12 : h % 12;
                const label = `${String(displayH).padStart(2, '0')}:${mm} ${period}`;
                options += `<option value="${timeVal}">${label}</option>`;
            }
        }
        pTimeSelect.innerHTML = options;
        rTimeSelect.innerHTML = options;
    },

    populateLocationSelects() {
        const pLocSelect = document.getElementById('b-pickup-loc');
        const rLocSelect = document.getElementById('b-return-loc');
        if (!pLocSelect || !rLocSelect) return;

        const options = (this.locations || []).map(loc => `<option value="${loc.id}">${loc.name} (${loc.city})</option>`).join('');
        pLocSelect.innerHTML = options;
        rLocSelect.innerHTML = options;
    },

    async startBooking(carId) {
        if (!API.isAuthenticated()) {
            Toast.info('Please log in or enter your phone/email to continue booking.');
            Auth.openAuthModal('otp');
            return;
        }

        try {
            this.car = await API.get(`/cars/${carId}/`);
            this.bookingData.car_id = carId;

            if (!this.locations || !this.locations.length) {
                const locData = await API.get('/locations/');
                this.locations = locData.results || locData;
            }

            this.populateTimeSelects();
            this.populateLocationSelects();

            // 1. Extract values from Hero Search Widget (#search-pickup-date, #search-return-date, #search-pickup-location, #search-dropoff-location)
            const searchPDate = document.getElementById('search-pickup-date')?.value;
            const searchRDate = document.getElementById('search-return-date')?.value;
            const searchPLoc = document.getElementById('search-pickup-location')?.value;
            const searchRLoc = document.getElementById('search-dropoff-location')?.value;
            const sameLocChecked = document.getElementById('same-location-checkbox')?.checked;

            const now = new Date();
            const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
            const inFourDays = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 4);

            let pDateVal = '';
            let pTimeVal = '10:00';
            let rDateVal = '';
            let rTimeVal = '10:00';
            let pLocVal = searchPLoc || (this.car.location ? String(this.car.location.id) : (this.locations[0]?.id ? String(this.locations[0].id) : '1'));
            let rLocVal = (searchRLoc && searchRLoc !== '') ? searchRLoc : (sameLocChecked ? pLocVal : pLocVal);

            if (searchPDate) {
                if (searchPDate.includes('T')) {
                    const pParts = searchPDate.split('T');
                    pDateVal = pParts[0];
                    if (pParts[1]) pTimeVal = pParts[1].substring(0, 5);
                } else {
                    pDateVal = searchPDate;
                }
            } else {
                pDateVal = tomorrow.toISOString().split('T')[0];
            }

            if (searchRDate) {
                if (searchRDate.includes('T')) {
                    const rParts = searchRDate.split('T');
                    rDateVal = rParts[0];
                    if (rParts[1]) rTimeVal = rParts[1].substring(0, 5);
                } else {
                    rDateVal = searchRDate;
                }
            } else {
                rDateVal = inFourDays.toISOString().split('T')[0];
            }

            // Normalise time strings to HH:MM format (e.g. "09:00", "14:30")
            const findClosestTime = (timeStr) => {
                if (!timeStr) return '10:00';
                const [hStr, mStr] = timeStr.split(':');
                const h = Math.min(23, Math.max(6, parseInt(hStr || '10')));
                const m = parseInt(mStr || '0');
                const roundedM = m >= 45 ? '00' : (m >= 15 ? '30' : '00');
                const finalH = (m >= 45 && h < 23) ? h + 1 : h;
                return `${String(finalH).padStart(2, '0')}:${roundedM}`;
            };

            pTimeVal = findClosestTime(pTimeVal);
            rTimeVal = findClosestTime(rTimeVal);

            const pDateEl = document.getElementById('b-pickup-date');
            const rDateEl = document.getElementById('b-return-date');
            const pTimeEl = document.getElementById('b-pickup-time');
            const rTimeEl = document.getElementById('b-return-time');
            const pLocEl = document.getElementById('b-pickup-loc');
            const rLocEl = document.getElementById('b-return-loc');

            if (pDateEl) {
                pDateEl.value = pDateVal;
                pDateEl.min = tomorrow.toISOString().split('T')[0];
            }
            if (rDateEl) {
                rDateEl.value = rDateVal;
                rDateEl.min = tomorrow.toISOString().split('T')[0];
            }
            if (pTimeEl) {
                pTimeEl.value = pTimeVal;
            }
            if (rTimeEl) {
                rTimeEl.value = rTimeVal;
            }
            if (pLocEl) pLocEl.value = pLocVal;
            if (rLocEl) rLocEl.value = rLocVal;

            const user = API.getUser();
            if (user) {
                this.bookingData.driver_name = user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
                this.bookingData.driver_phone = user.phone_number || '';
                this.bookingData.driver_email = user.email || '';
                this.bookingData.driver_license = user.driver_license_number || '';
            }

            this.currentStep = 1;
            this.openWizardModal();
            this.updateStepView();
            await this.onScheduleChange();
        } catch (e) {
            Toast.error('Could not initiate booking.');
        }
    },

    openWizardModal() {
        const modal = document.getElementById('booking-wizard-modal');
        if (modal) modal.classList.add('active');
    },

    closeWizardModal() {
        const modal = document.getElementById('booking-wizard-modal');
        if (modal) modal.classList.remove('active');
    },

    async onScheduleChange() {
        const pDate = document.getElementById('b-pickup-date')?.value;
        const pTime = document.getElementById('b-pickup-time')?.value || '10:00';
        const rDate = document.getElementById('b-return-date')?.value;
        const rTime = document.getElementById('b-return-time')?.value || '10:00';
        const pLoc = document.getElementById('b-pickup-loc')?.value;
        const rLoc = document.getElementById('b-return-loc')?.value || pLoc;

        const banner = document.getElementById('b-availability-banner');
        const bannerText = document.getElementById('b-availability-text');
        const bannerIcon = document.getElementById('b-availability-icon');
        const badgeEl = document.getElementById('b-trip-duration-badge');

        if (!pDate || !rDate) {
            this.isScheduleValid = false;
            return;
        }

        const startDt = new Date(`${pDate}T${pTime}:00`);
        const endDt = new Date(`${rDate}T${rTime}:00`);

        if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
            this.isScheduleValid = false;
            return;
        }

        if (endDt <= startDt) {
            this.isScheduleValid = false;
            if (banner) {
                banner.style.background = 'rgba(239, 68, 68, 0.1)';
                banner.style.color = '#dc2626';
                banner.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            }
            if (bannerIcon) bannerIcon.className = 'fa-solid fa-triangle-exclamation';
            if (bannerText) bannerText.innerText = 'Return date and time must be after pickup date and time.';
            if (badgeEl) badgeEl.innerText = 'Invalid Duration';
            return;
        }

        const diffMs = endDt - startDt;
        const diffHours = Math.max(1, Math.round(diffMs / (1000 * 60 * 60)));
        const diffDays = Math.max(1, Math.ceil(diffHours / 24));

        if (badgeEl) {
            badgeEl.innerText = `${diffDays} Day${diffDays > 1 ? 's' : ''} Rental (${diffHours} Hours)`;
        }

        this.bookingData.pickup_location_id = parseInt(pLoc || 1);
        this.bookingData.return_location_id = parseInt(rLoc || pLoc || 1);
        this.bookingData.start_date = startDt.toISOString();
        this.bookingData.end_date = endDt.toISOString();

        // Check availability with backend
        try {
            if (bannerText) bannerText.innerText = 'Checking real-time vehicle availability...';
            const checkRes = await API.post('/cars/check-availability/', {
                car_id: this.bookingData.car_id,
                pickup_date: this.bookingData.start_date,
                return_date: this.bookingData.end_date
            });

            if (checkRes.is_available) {
                this.isScheduleValid = true;
                if (banner) {
                    banner.style.background = 'rgba(16, 185, 129, 0.1)';
                    banner.style.color = '#059669';
                    banner.style.borderColor = 'rgba(16, 185, 129, 0.25)';
                }
                if (bannerIcon) bannerIcon.className = 'fa-solid fa-circle-check';
                if (bannerText) bannerText.innerText = `Vehicle is Available for ${diffDays} day${diffDays > 1 ? 's' : ''} (${diffHours} hrs) handover at selected hub.`;
                await this.refreshQuote();
            } else {
                this.isScheduleValid = false;
                if (banner) {
                    banner.style.background = 'rgba(239, 68, 68, 0.1)';
                    banner.style.color = '#dc2626';
                    banner.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                }
                if (bannerIcon) bannerIcon.className = 'fa-solid fa-calendar-xmark';
                if (bannerText) bannerText.innerText = checkRes.reason || 'This vehicle is reserved for the selected schedule. Please choose different dates/times.';
            }
        } catch (e) {
            console.error('Availability check error:', e);
        }
    },

    updateStepView() {
        document.querySelectorAll('.wizard-step').forEach((stepEl, idx) => {
            const stepNum = idx + 1;
            stepEl.classList.toggle('active', stepNum === this.currentStep);
            stepEl.classList.toggle('completed', stepNum < this.currentStep);
        });

        document.querySelectorAll('.wizard-panel').forEach(panel => {
            panel.classList.toggle('hidden', parseInt(panel.dataset.step) !== this.currentStep);
        });

        const headerTitle = document.getElementById('wizard-car-header');
        if (headerTitle && this.car) {
            headerTitle.innerHTML = `<strong>${this.car.year} ${this.car.brand} ${this.car.model}</strong> • ${formatCurrency(this.car.price_per_day)}/day`;
        }

        if (this.currentStep === 3) {
            document.getElementById('b-driver-name').value = this.bookingData.driver_name;
            document.getElementById('b-driver-phone').value = this.bookingData.driver_phone;
            document.getElementById('b-driver-email').value = this.bookingData.driver_email;
            document.getElementById('b-driver-license').value = this.bookingData.driver_license;
            document.getElementById('b-special-requests').value = this.bookingData.special_requests;
        }

        // Manage Wizard Modal Footer Buttons
        const footer = document.getElementById('wizard-modal-footer');
        const prevBtn = document.getElementById('wizard-prev-btn');
        const nextBtn = document.getElementById('wizard-next-btn');
        const payBtn = document.getElementById('pay-now-btn');

        if (footer) {
            if (this.currentStep === 5) {
                // Voucher confirmation step - hide bottom navigation footer
                footer.classList.add('hidden');
            } else {
                footer.classList.remove('hidden');

                // Prev/Back Button
                if (prevBtn) {
                    prevBtn.classList.toggle('hidden', this.currentStep === 1);
                }

                // Next vs Pay Now Button
                if (this.currentStep === 4) {
                    // Payment step
                    if (nextBtn) nextBtn.classList.add('hidden');
                    if (payBtn) {
                        payBtn.classList.remove('hidden');
                        payBtn.disabled = false;
                        const totalStr = this.quote ? ` (${formatCurrency(this.quote.total_amount)})` : '';
                        payBtn.innerHTML = `<i class="fa-solid fa-lock"></i> Pay & Confirm Reservation${totalStr}`;
                    }
                } else {
                    // Steps 1, 2, 3
                    if (nextBtn) {
                        nextBtn.classList.remove('hidden');
                        if (this.currentStep === 1) nextBtn.innerText = 'Continue to Protection';
                        else if (this.currentStep === 2) nextBtn.innerText = 'Continue to Driver Info';
                        else if (this.currentStep === 3) nextBtn.innerText = 'Proceed to Payment';
                        else nextBtn.innerText = 'Continue';
                    }
                    if (payBtn) payBtn.classList.add('hidden');
                }
            }
        }
    },

    async nextStep() {
        if (this.currentStep === 1) {
            if (!this.isScheduleValid) {
                Toast.error('Please select an available pickup and return schedule.');
                return;
            }
            this.currentStep = 2;
            this.updateStepView();
            await this.refreshQuote();
        } else if (this.currentStep === 2) {
            this.currentStep = 3;
            this.updateStepView();
        } else if (this.currentStep === 3) {
            const name = document.getElementById('b-driver-name')?.value.trim();
            const phone = document.getElementById('b-driver-phone')?.value.trim();
            if (!name || !phone) {
                Toast.error('Please enter the primary driver full name and phone number.');
                return;
            }
            this.bookingData.driver_name = name;
            this.bookingData.driver_phone = phone;
            this.bookingData.driver_email = document.getElementById('b-driver-email')?.value.trim();
            this.bookingData.driver_license = document.getElementById('b-driver-license')?.value.trim();
            this.bookingData.special_requests = document.getElementById('b-special-requests')?.value.trim();

            this.currentStep = 4;
            this.updateStepView();
            await this.refreshQuote();
        }
    },

    prevStep() {
        if (this.currentStep > 1 && this.currentStep < 5) {
            this.currentStep--;
            this.updateStepView();
            this.refreshQuote();
        }
    },

    selectInsurance(plan) {
        this.bookingData.insurance_plan = plan;
        document.querySelectorAll('.insurance-card').forEach(c => {
            c.classList.toggle('selected', c.dataset.plan === plan);
        });
        this.refreshQuote();
    },

    toggleAddon(key) {
        const idx = this.bookingData.addons.indexOf(key);
        if (idx > -1) {
            this.bookingData.addons.splice(idx, 1);
        } else {
            this.bookingData.addons.push(key);
        }
        document.querySelectorAll(`.addon-card[data-addon="${key}"]`).forEach(c => {
            c.classList.toggle('selected', this.bookingData.addons.includes(key));
        });
        this.refreshQuote();
    },

    async applyCoupon() {
        const code = document.getElementById('b-coupon-input')?.value.trim();
        if (!code) {
            Toast.warning('Please enter a promo code.');
            return;
        }

        try {
            const res = await API.post('/bookings/validate-coupon/', {
                coupon_code: code,
                amount: this.quote?.total_amount || 100
            });
            this.bookingData.coupon_code = res.code;
            Toast.success(res.message);
            await this.refreshQuote();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    async refreshQuote() {
        if (!this.bookingData.car_id || !this.bookingData.start_date || !this.bookingData.end_date) return;
        try {
            const quote = await API.post('/bookings/quote/', {
                car_id: this.bookingData.car_id,
                start_date: this.bookingData.start_date,
                end_date: this.bookingData.end_date,
                insurance_plan: this.bookingData.insurance_plan,
                addons: this.bookingData.addons,
                coupon_code: this.bookingData.coupon_code
            });
            this.quote = quote;
            this.renderCatalogFromBackend();
            this.renderQuoteSummary();
        } catch (e) {
            console.error('Quote error:', e);
        }
    },

    renderCatalogFromBackend() {
        if (!this.quote) return;

        // Populate protection plans directly from backend API
        if (this.quote.insurance_catalog) {
            const plans = this.quote.insurance_catalog;
            if (plans.NONE) {
                const descEl = document.getElementById('plan-desc-none');
                if (descEl) descEl.innerText = plans.NONE.description;
                const priceEl = document.getElementById('plan-price-none');
                if (priceEl) priceEl.innerText = formatCurrency(plans.NONE.daily_rate);
            }
            if (plans.STANDARD) {
                const descEl = document.getElementById('plan-desc-standard');
                if (descEl) descEl.innerText = plans.STANDARD.description;
                const priceEl = document.getElementById('plan-price-standard');
                if (priceEl) priceEl.innerText = `+${formatCurrency(plans.STANDARD.daily_rate)}/day`;
            }
            if (plans.PREMIUM) {
                const descEl = document.getElementById('plan-desc-premium');
                if (descEl) descEl.innerText = plans.PREMIUM.description;
                const priceEl = document.getElementById('plan-price-premium');
                if (priceEl) priceEl.innerText = `+${formatCurrency(plans.PREMIUM.daily_rate)}/day`;
            }
        }

        // Populate add-ons directly from backend API
        if (this.quote.addons_catalog) {
            this.quote.addons_catalog.forEach(addon => {
                const priceEl = document.getElementById(`addon-price-${addon.key}`);
                if (priceEl) priceEl.innerText = `+${formatCurrency(addon.daily_rate)}/day`;
                const descEl = document.getElementById(`addon-desc-${addon.key}`);
                if (descEl && addon.description) descEl.innerText = addon.description;
            });
        }
    },

    renderQuoteSummary() {
        if (!this.quote) return;
        const container = document.getElementById('wizard-quote-summary');
        if (!container) return;

        container.innerHTML = `
            <div class="quote-row">
                <span>Rental Charge (${this.quote.total_days} Day${this.quote.total_days > 1 ? 's' : ''} @ ${formatCurrency(this.quote.daily_rate)}/day)</span>
                <span>${formatCurrency(this.quote.rental_charge)}</span>
            </div>
            ${this.quote.insurance_amount > 0 ? `
                <div class="quote-row">
                    <span>Protection Plan (${this.quote.insurance_plan})</span>
                    <span>${formatCurrency(this.quote.insurance_amount)}</span>
                </div>
            ` : ''}
            ${this.quote.addons_total > 0 ? `
                <div class="quote-row">
                    <span>Add-ons & Extras (${this.quote.addons.length})</span>
                    <span>${formatCurrency(this.quote.addons_total)}</span>
                </div>
            ` : ''}
            <div class="quote-row">
                <span>Estimated Taxes & Fees (10%)</span>
                <span>${formatCurrency(this.quote.tax_amount)}</span>
            </div>
            <div class="quote-row">
                <span>Refundable Security Deposit</span>
                <span>${formatCurrency(this.quote.deposit_amount)}</span>
            </div>
            ${this.quote.discount_amount > 0 ? `
                <div class="quote-row discount">
                    <span><i class="fa-solid fa-tags"></i> Coupon (${this.quote.coupon_applied})</span>
                    <span>-${formatCurrency(this.quote.discount_amount)}</span>
                </div>
            ` : ''}
            <div class="quote-total-row">
                <span>Total Amount Due</span>
                <span class="text-gradient">${formatCurrency(this.quote.total_amount)}</span>
            </div>
        `;
    },

    selectPaymentProvider(provider) {
        this.bookingData.payment_method = provider;
        document.querySelectorAll('.payment-card').forEach(c => {
            c.classList.toggle('selected', c.dataset.provider === provider);
        });
    },

    async processFinalPayment() {
        const payBtn = document.getElementById('pay-now-btn');
        payBtn.disabled = true;
        payBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Reservation...';

        try {
            const booking = await API.post('/bookings/', {
                car_id: this.bookingData.car_id,
                pickup_location_id: this.bookingData.pickup_location_id,
                return_location_id: this.bookingData.return_location_id,
                start_date: this.bookingData.start_date,
                end_date: this.bookingData.end_date,
                insurance_plan: this.bookingData.insurance_plan,
                addons: this.bookingData.addons,
                coupon_code: this.bookingData.coupon_code,
                driver_name: this.bookingData.driver_name,
                driver_phone: this.bookingData.driver_phone,
                driver_email: this.bookingData.driver_email,
                driver_license: this.bookingData.driver_license,
                special_requests: this.bookingData.special_requests
            });

            this.activeBooking = booking;

            if (this.bookingData.payment_method === 'RAZORPAY') {
                const initRes = await API.post('/payments/initiate/', {
                    booking_code: booking.booking_code,
                    provider: 'RAZORPAY',
                    currency: 'INR'
                });
                
                if (window.Razorpay && initRes.gateway_order_id && !initRes.gateway_order_id.includes('mock')) {
                    const options = {
                        key: initRes.razorpay_key,
                        amount: Math.round(initRes.amount * 100),
                        currency: 'INR',
                        name: 'DriveLuxe Rentals',
                        description: `Rental for ${this.car.display_name}`,
                        order_id: initRes.gateway_order_id,
                        handler: async (response) => {
                            await API.post('/payments/verify/razorpay/', {
                                payment_id: initRes.payment_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_signature: response.razorpay_signature
                            });
                            this.showConfirmationStep();
                        }
                    };
                    const rzp = new window.Razorpay(options);
                    rzp.open();
                } else {
                    await API.post('/payments/mock-checkout/', {
                        booking_code: booking.booking_code,
                        payment_method: 'RAZORPAY'
                    });
                    this.showConfirmationStep();
                }
            } else if (this.bookingData.payment_method === 'STRIPE') {
                await API.post('/payments/mock-checkout/', {
                    booking_code: booking.booking_code,
                    payment_method: 'STRIPE_CARD'
                });
                this.showConfirmationStep();
            } else {
                await API.post('/payments/mock-checkout/', {
                    booking_code: booking.booking_code,
                    payment_method: 'CARD'
                });
                this.showConfirmationStep();
            }
        } catch (err) {
            Toast.error(err.message);
            payBtn.disabled = false;
            payBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Pay & Confirm Reservation';
        }
    },

    showConfirmationStep() {
        this.currentStep = 5;
        this.updateStepView();
        Toast.success('Reservation Confirmed & Paid Successfully!', 'Success');

        if (this.activeBooking) {
            document.getElementById('v-booking-code').innerText = this.activeBooking.booking_code;
            document.getElementById('v-car-name').innerText = `${this.activeBooking.car.year} ${this.activeBooking.car.brand} ${this.activeBooking.car.model}`;
            document.getElementById('v-pickup-loc').innerText = this.activeBooking.pickup_location?.name || 'City Hub';
            document.getElementById('v-return-loc').innerText = this.activeBooking.return_location?.name || 'City Hub';
            document.getElementById('v-start-date').innerText = formatDateTime(this.activeBooking.start_date);
            document.getElementById('v-end-date').innerText = formatDateTime(this.activeBooking.end_date);
            document.getElementById('v-driver-name').innerText = this.activeBooking.driver_name;
            document.getElementById('v-total-amount').innerText = formatCurrency(this.activeBooking.total_amount);

            // Track recommendation & search conversion to booked
            try {
                API.post('/analytics/track-click/', {
                    car_id: this.activeBooking.car.id,
                    recommendation_click_id: window.Customer?.lastRecommendationClickId || null,
                    booked: true,
                    clicked: true
                }).catch(e => console.warn('Conversion tracking notice:', e));
            } catch (e) {}
        }

        Notifications.fetchNotifications();
    }
};
