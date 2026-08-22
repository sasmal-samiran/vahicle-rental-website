// Multi-Step Booking Wizard & Payment Launcher
import { API } from './api.js';
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Notifications } from './notifications.js';
import { formatCurrency, formatDate, formatDateTime } from './config.js';

export const BookingWizard = {
    currentStep: 1,
    car: null,
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

    async startBooking(carId) {
        if (!API.isAuthenticated()) {
            Toast.info('Please log in or enter your phone/email to continue booking.');
            Auth.openAuthModal('otp');
            return;
        }

        try {
            this.car = await API.get(`/cars/${carId}/`);
            this.bookingData.car_id = carId;

            const pickupDate = document.getElementById('search-pickup-date')?.value;
            const returnDate = document.getElementById('search-return-date')?.value;
            const pickupLoc = document.getElementById('search-pickup-location')?.value || this.car.location?.id || 1;
            const dropoffLoc = document.getElementById('search-dropoff-location')?.value || pickupLoc;

            this.bookingData.pickup_location_id = parseInt(pickupLoc);
            this.bookingData.return_location_id = parseInt(dropoffLoc);
            this.bookingData.start_date = new Date(pickupDate).toISOString();
            this.bookingData.end_date = new Date(returnDate).toISOString();

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
            await this.refreshQuote();
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

        if (this.currentStep === 2) {
            document.getElementById('b-driver-name').value = this.bookingData.driver_name;
            document.getElementById('b-driver-phone').value = this.bookingData.driver_phone;
            document.getElementById('b-driver-email').value = this.bookingData.driver_email;
            document.getElementById('b-driver-license').value = this.bookingData.driver_license;
            document.getElementById('b-special-requests').value = this.bookingData.special_requests;
        }
    },

    async nextStep() {
        if (this.currentStep === 1) {
            this.currentStep = 2;
            this.updateStepView();
            await this.refreshQuote();
        } else if (this.currentStep === 2) {
            const name = document.getElementById('b-driver-name')?.value.trim();
            const phone = document.getElementById('b-driver-phone')?.value.trim();
            if (!name || !phone) {
                Toast.error('Please enter the primary driver name and phone number.');
                return;
            }
            this.bookingData.driver_name = name;
            this.bookingData.driver_phone = phone;
            this.bookingData.driver_email = document.getElementById('b-driver-email')?.value.trim();
            this.bookingData.driver_license = document.getElementById('b-driver-license')?.value.trim();
            this.bookingData.special_requests = document.getElementById('b-special-requests')?.value.trim();

            this.currentStep = 3;
            this.updateStepView();
            await this.refreshQuote();
        } else if (this.currentStep === 3) {
            this.currentStep = 4;
            this.updateStepView();
        }
    },

    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepView();
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
            this.renderQuoteSummary();
        } catch (e) {
            console.error('Quote error:', e);
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
                    provider: 'RAZORPAY'
                });
                
                if (window.Razorpay && initRes.gateway_order_id && !initRes.gateway_order_id.includes('mock')) {
                    const options = {
                        key: initRes.razorpay_key,
                        amount: initRes.amount * 100,
                        currency: 'USD',
                        name: 'Premium Car Rental',
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
        }

        Notifications.fetchNotifications();
    }
};
