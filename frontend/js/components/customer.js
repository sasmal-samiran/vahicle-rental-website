// Customer Fleet Browser, Filter Engine & Car Detail Controller
import { API } from './api.js';
import { Toast } from './toast.js';
import { BookingWizard } from './booking.js';
import { formatCurrency, formatForInput } from './config.js';

export const Customer = {
    cars: [],
    categories: [],
    locations: [],
    filters: {
        category: '',
        search: '',
        min_price: 0,
        max_price: 350,
        transmission: '',
        fuel_type: '',
        seats: '',
        ordering: '',
        pickup_location_id: '',
        dropoff_location_id: '',
        pickup_date: '',
        return_date: ''
    },
    activeCar: null,

    async init() {
        this.parseUrlParams();
        this.setDefaultDates();
        await this.loadLocations();
        await this.loadCategories();
        this.bindEvents();
        
        if (document.getElementById('cars-grid-container')) {
            await this.fetchCars();
        } else if (document.getElementById('featured-cars-grid')) {
            await this.fetchFeaturedCars();
        }
    },

    parseUrlParams() {
        const params = new URLSearchParams(window.location.search);
        if (params.get('pickup_location')) this.filters.pickup_location_id = params.get('pickup_location');
        if (params.get('dropoff_location')) this.filters.dropoff_location_id = params.get('dropoff_location');
        if (params.get('pickup_date')) this.filters.pickup_date = params.get('pickup_date');
        if (params.get('return_date')) this.filters.return_date = params.get('return_date');
        if (params.get('category')) this.filters.category = params.get('category');
        if (params.get('search')) this.filters.search = params.get('search');
    },

    setDefaultDates() {
        const now = new Date();
        now.setHours(10, 0, 0, 0);
        const pickup = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        const dropoff = new Date(now.getTime() + 4 * 24 * 60 * 60 * 1000);

        const pickupInput = document.getElementById('search-pickup-date');
        const returnInput = document.getElementById('search-return-date');

        if (!this.filters.pickup_date) {
            this.filters.pickup_date = pickup.toISOString();
            if (pickupInput) pickupInput.value = formatForInput(pickup);
        } else {
            if (pickupInput) pickupInput.value = formatForInput(new Date(this.filters.pickup_date));
        }

        if (!this.filters.return_date) {
            this.filters.return_date = dropoff.toISOString();
            if (returnInput) returnInput.value = formatForInput(dropoff);
        } else {
            if (returnInput) returnInput.value = formatForInput(new Date(this.filters.return_date));
        }
    },

    bindEvents() {
        // Price Slider
        const priceSlider = document.getElementById('price-range-slider');
        const priceMaxDisplay = document.getElementById('price-max-display');
        if (priceSlider) {
            priceSlider.addEventListener('input', (e) => {
                this.filters.max_price = e.target.value;
                if (priceMaxDisplay) priceMaxDisplay.innerText = `$${e.target.value}`;
                this.applyFiltersDebounced();
            });
        }

        // Search text input
        const searchInput = document.getElementById('fleet-search-input');
        if (searchInput) {
            if (this.filters.search) searchInput.value = this.filters.search;
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
                this.applyFiltersDebounced();
            });
        }

        // Sort selector
        const sortSelect = document.getElementById('fleet-sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.filters.ordering = e.target.value;
                this.fetchCars();
            });
        }

        // Filter chips (Transmission, Fuel, Seats)
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const group = chip.dataset.group;
                const value = chip.dataset.value;
                document.querySelectorAll(`.filter-chip[data-group="${group}"]`).forEach(c => c.classList.remove('active'));
                
                if (this.filters[group] === value) {
                    this.filters[group] = '';
                } else {
                    chip.classList.add('active');
                    this.filters[group] = value;
                }
                this.fetchCars();
            });
        });

        // Search widget form
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearchForm();
            });
        }

        // Same location checkbox
        const sameLocCheckbox = document.getElementById('same-location-checkbox');
        const dropoffContainer = document.getElementById('dropoff-location-container');
        if (sameLocCheckbox && dropoffContainer) {
            sameLocCheckbox.addEventListener('change', (e) => {
                dropoffContainer.classList.toggle('hidden', e.target.checked);
            });
        }
    },

    debounceTimer: null,
    applyFiltersDebounced() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.fetchCars(), 300);
    },

    async loadLocations() {
        try {
            const data = await API.get('/locations/');
            this.locations = data.results || data;
            const pickupSelect = document.getElementById('search-pickup-location');
            const dropoffSelect = document.getElementById('search-dropoff-location');

            const optionsHtml = this.locations.map(loc => `
                <option value="${loc.id}" ${String(loc.id) === String(this.filters.pickup_location_id) ? 'selected' : ''}>${loc.name} (${loc.city})</option>
            `).join('');

            if (pickupSelect) pickupSelect.innerHTML = `<option value="">All Hub Locations</option>` + optionsHtml;
            if (dropoffSelect) dropoffSelect.innerHTML = `<option value="">Same as Pickup</option>` + optionsHtml;
        } catch (e) {
            console.error('Locations error:', e);
        }
    },

    async loadCategories() {
        try {
            const data = await API.get('/categories/');
            this.categories = data.results || data;
            const container = document.getElementById('category-tabs-container');
            if (!container) return;

            container.innerHTML = `
                <button class="category-tab-btn ${!this.filters.category ? 'active' : ''}" data-slug="" onclick="Customer.selectCategory('')">
                    <i class="fa-solid fa-layer-group"></i> All Fleet
                </button>
            ` + this.categories.map(cat => `
                <button class="category-tab-btn ${this.filters.category === cat.slug ? 'active' : ''}" data-slug="${cat.slug}" onclick="Customer.selectCategory('${cat.slug}')">
                    <i class="fa-solid ${cat.icon || 'fa-car'}"></i> ${cat.name}
                    <span class="category-count">${cat.car_count}</span>
                </button>
            `).join('');
        } catch (e) {
            console.error('Categories error:', e);
        }
    },

    selectCategory(slug) {
        this.filters.category = slug;
        document.querySelectorAll('.category-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.slug === slug);
        });
        if (document.getElementById('cars-grid-container')) {
            this.fetchCars();
        } else {
            window.location.href = `/fleet/?category=${slug}`;
        }
    },

    handleSearchForm() {
        const pickupLoc = document.getElementById('search-pickup-location')?.value || '';
        const dropoffLoc = document.getElementById('search-dropoff-location')?.value || '';
        const pickupDate = document.getElementById('search-pickup-date')?.value;
        const returnDate = document.getElementById('search-return-date')?.value;

        let pDateIso = '';
        let rDateIso = '';

        if (pickupDate && returnDate) {
            if (new Date(returnDate) <= new Date(pickupDate)) {
                Toast.error('Return date must be after pickup date.');
                return;
            }
            pDateIso = new Date(pickupDate).toISOString();
            rDateIso = new Date(returnDate).toISOString();
            this.filters.pickup_date = pDateIso;
            this.filters.return_date = rDateIso;
        }

        this.filters.pickup_location_id = pickupLoc;
        this.filters.dropoff_location_id = dropoffLoc;

        // If on Home Page, route to the dedicated /fleet/ search page with parameters
        if (!document.getElementById('cars-grid-container')) {
            const params = new URLSearchParams();
            if (pickupLoc) params.set('pickup_location', pickupLoc);
            if (dropoffLoc) params.set('dropoff_location', dropoffLoc);
            if (pDateIso) params.set('pickup_date', pDateIso);
            if (rDateIso) params.set('return_date', rDateIso);
            window.location.href = `/fleet/?${params.toString()}`;
            return;
        }

        // If already on /fleet/, fetch immediately
        this.fetchCars();
    },

    async fetchCars() {
        const grid = document.getElementById('cars-grid-container');
        const countEl = document.getElementById('results-count-display');
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:60px 0;">
                    <i class="fa-solid fa-circle-notch fa-spin text-gradient" style="font-size:2.5rem; margin-bottom:12px;"></i>
                    <p style="color:var(--text-secondary);">Searching available fleet in real time...</p>
                </div>
            `;
        }

        try {
            const params = {
                category: this.filters.category,
                search: this.filters.search,
                max_price: this.filters.max_price,
                transmission: this.filters.transmission,
                fuel_type: this.filters.fuel_type,
                seats: this.filters.seats,
                ordering: this.filters.ordering,
                location_id: this.filters.pickup_location_id,
                pickup_date: this.filters.pickup_date,
                return_date: this.filters.return_date
            };

            const data = await API.get('/cars/', params);
            this.cars = data.results || data;

            if (countEl) countEl.innerText = `${this.cars.length} Vehicle${this.cars.length === 1 ? '' : 's'} Available`;
            this.renderCars();
        } catch (err) {
            if (grid) grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--danger);">${err.message}</div>`;
        }
    },

    async fetchFeaturedCars() {
        const grid = document.getElementById('featured-cars-grid');
        if (!grid) return;
        try {
            const data = await API.get('/cars/', { ordering: '-price_per_day' });
            const cars = (data.results || data).slice(0, 4);
            grid.innerHTML = cars.map(car => this.generateCarCardHtml(car)).join('');
        } catch (e) {
            console.error('Featured cars error:', e);
        }
    },

    generateCarCardHtml(car) {
        return `
            <div class="car-card animate-slide-in">
                <div class="car-img-wrapper">
                    <img src="${car.primary_image || car.main_image_url}" alt="${car.display_name}" loading="lazy" />
                    <span class="badge badge-primary car-category-badge">
                        <i class="fa-solid ${car.category?.icon || 'fa-car'}"></i> ${car.category?.name || 'Car'}
                    </span>
                    <div class="car-price-tag">
                        ${formatCurrency(car.price_per_day)}<span> /day</span>
                    </div>
                </div>
                <div class="car-content">
                    <div class="car-header-row">
                        <div>
                            <h3 class="car-title">${car.brand} ${car.model}</h3>
                            <span class="car-year">${car.year}</span>
                        </div>
                        <div class="car-rating">
                            <i class="fa-solid fa-star"></i> ${car.average_rating} <span>(${car.total_reviews})</span>
                        </div>
                    </div>
                    <div class="car-location-tag">
                        <i class="fa-solid fa-location-dot"></i> ${car.location ? `${car.location.name}` : 'Main Branch'}
                    </div>
                    <div class="car-specs-grid">
                        <div class="car-spec-item"><i class="fa-solid fa-gear"></i> ${car.transmission}</div>
                        <div class="car-spec-item"><i class="fa-solid fa-gas-pump"></i> ${car.fuel_type}</div>
                        <div class="car-spec-item"><i class="fa-solid fa-user-group"></i> ${car.seats} Seats</div>
                        <div class="car-spec-item"><i class="fa-solid fa-bolt"></i> ${car.power_hp} HP</div>
                    </div>
                    <div class="car-card-actions">
                        <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id})">
                            <i class="fa-regular fa-eye"></i> Details
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="BookingWizard.startBooking(${car.id})">
                            <i class="fa-solid fa-key"></i> Book Now
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    renderCars() {
        const grid = document.getElementById('cars-grid-container');
        if (!grid) return;

        if (!this.cars.length) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:70px 20px; background:var(--bg-card); border-radius:var(--radius-lg); border:1px solid var(--border-color);">
                    <i class="fa-solid fa-car-side" style="font-size:3rem; color:var(--text-muted); margin-bottom:16px;"></i>
                    <h3 style="font-size:1.4rem; font-weight:700; margin-bottom:8px;">No Vehicles Match Your Search</h3>
                    <p style="color:var(--text-secondary); max-width:460px; margin:0 auto 20px;">Try adjusting your dates, budget slider, or category filters to explore more cars.</p>
                    <button class="btn btn-primary" onclick="Customer.resetFilters()">Reset All Filters</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.cars.map(car => this.generateCarCardHtml(car)).join('');
    },

    resetFilters() {
        this.filters.category = '';
        this.filters.search = '';
        this.filters.max_price = 350;
        this.filters.transmission = '';
        this.filters.fuel_type = '';
        this.filters.seats = '';
        this.filters.ordering = '';
        
        const slider = document.getElementById('price-range-slider');
        if (slider) slider.value = 350;
        const searchInput = document.getElementById('fleet-search-input');
        if (searchInput) searchInput.value = '';
        
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.category-tab-btn').forEach(b => b.classList.toggle('active', b.dataset.slug === ''));
        this.fetchCars();
    },

    async openDetailModal(carId) {
        try {
            const car = await API.get(`/cars/${carId}/`);
            this.activeCar = car;

            const modal = document.getElementById('car-detail-modal');
            if (!modal) return;

            document.getElementById('detail-car-title').innerText = `${car.year} ${car.brand} ${car.model}`;
            document.getElementById('detail-car-price').innerHTML = `${formatCurrency(car.price_per_day)}<span style="font-size:0.8rem; font-weight:normal; color:var(--text-secondary);"> /day</span>`;
            document.getElementById('detail-car-rating').innerHTML = `<i class="fa-solid fa-star" style="color:var(--warning);"></i> ${car.average_rating} (${car.total_reviews} reviews)`;

            const mainImg = document.getElementById('detail-main-img');
            if (mainImg) mainImg.src = car.primary_image || car.main_image_url;

            const thumbsContainer = document.getElementById('detail-thumbs-container');
            const gallery = [car.primary_image, ...(car.images?.map(i => i.url) || [])].filter(Boolean);
            if (thumbsContainer) {
                thumbsContainer.innerHTML = gallery.map((imgUrl, i) => `
                    <img src="${imgUrl}" class="gallery-thumb ${i === 0 ? 'active' : ''}" onclick="Customer.switchGalleryImage('${imgUrl}', this)" alt="Thumb" />
                `).join('');
            }

            const specsContainer = document.getElementById('detail-specs-table');
            if (specsContainer) {
                specsContainer.innerHTML = `
                    <tr><td>Brand & Model</td><td>${car.brand} ${car.model}</td></tr>
                    <tr><td>Model Year</td><td>${car.year}</td></tr>
                    <tr><td>Transmission</td><td>${car.transmission}</td></tr>
                    <tr><td>Engine / Powertrain</td><td>${car.engine_capacity || 'N/A'}</td></tr>
                    <tr><td>Horsepower</td><td>${car.power_hp} HP</td></tr>
                    <tr><td>Fuel Type</td><td>${car.fuel_type}</td></tr>
                    <tr><td>Seating Capacity</td><td>${car.seats} Passengers</td></tr>
                    <tr><td>Luggage Capacity</td><td>${car.luggage_capacity} Bags</td></tr>
                    <tr><td>Daily Mileage</td><td>${car.mileage_limit}</td></tr>
                    <tr><td>Security Deposit</td><td>${formatCurrency(car.security_deposit)}</td></tr>
                    <tr><td>Location</td><td>${car.location?.name || 'City Hub'}</td></tr>
                `;
            }

            const featuresContainer = document.getElementById('detail-features-container');
            if (featuresContainer) {
                const feats = car.features || ['Apple CarPlay', 'GPS Navigation', 'Rearview Camera', 'Keyless Entry'];
                featuresContainer.innerHTML = feats.map(f => `
                    <div class="feature-pill"><i class="fa-solid fa-circle-check"></i> ${f}</div>
                `).join('');
            }

            const descEl = document.getElementById('detail-description');
            if (descEl) descEl.innerText = car.description || 'Premium rental vehicle in flawless showroom condition.';

            const reviewsContainer = document.getElementById('detail-reviews-container');
            if (reviewsContainer) {
                const reviews = car.recent_reviews || [];
                if (!reviews.length) {
                    reviewsContainer.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">No customer reviews yet.</p>';
                } else {
                    reviewsContainer.innerHTML = reviews.map(r => `
                        <div style="padding:14px 0; border-bottom:1px solid var(--border-color);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <strong style="font-size:0.9rem;">${r.customer_name}</strong>
                                <div style="color:var(--warning); font-size:0.8rem;">
                                    ${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}
                                </div>
                            </div>
                            <div style="font-weight:600; font-size:0.85rem; margin-bottom:2px;">${r.title || ''}</div>
                            <div style="font-size:0.85rem; color:var(--text-secondary);">${r.comment}</div>
                        </div>
                    `).join('');
                }
            }

            const bookBtn = document.getElementById('detail-book-btn');
            if (bookBtn) {
                bookBtn.onclick = () => {
                    this.closeDetailModal();
                    BookingWizard.startBooking(car.id);
                };
            }

            modal.classList.add('active');
        } catch (e) {
            Toast.error('Could not load car details.');
        }
    },

    switchGalleryImage(imgUrl, el) {
        const mainImg = document.getElementById('detail-main-img');
        if (mainImg) mainImg.src = imgUrl;
        document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
        if (el) el.classList.add('active');
    },

    closeDetailModal() {
        const modal = document.getElementById('car-detail-modal');
        if (modal) modal.classList.remove('active');
    }
};
