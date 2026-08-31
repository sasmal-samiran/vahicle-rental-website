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
        max_price: 10000,
        status: '',
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
        this.bindEvents();
        this.loadLocations();
        this.loadCategories();
        this.loadTrendingSearches();

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
        if (params.get('status')) this.filters.status = params.get('status');
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
                if (priceMaxDisplay) priceMaxDisplay.innerText = `₹${e.target.value}`;
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
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.filters.search = e.target.value;
                    this.fetchCars();
                }
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

        // Status dropdown selector
        const statusSelect = document.getElementById('fleet-status-select');
        if (statusSelect) {
            if (this.filters.status) statusSelect.value = this.filters.status;
            statusSelect.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.fetchCars();
            });
        }

        // Filter chips (Status, Transmission, Fuel, Seats)
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const group = chip.dataset.group;
                const value = chip.dataset.value || '';
                
                document.querySelectorAll(`.filter-chip[data-group="${group}"]`).forEach(c => c.classList.remove('active'));
                
                if (this.filters[group] === value && value !== '') {
                    this.filters[group] = '';
                    const defaultChip = document.querySelector(`.filter-chip[data-group="${group}"][data-value=""]`);
                    if (defaultChip) defaultChip.classList.add('active');
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

        // Real-time Authentication Sync:
        // When a user logs in or registers (even after scrolling down),
        // instantly refresh recommendations for their profile without reloading the page or losing scroll position!
        document.addEventListener('auth:change', (event) => {
            const user = event?.detail?.user || API.getUser();

            // 1. Refresh Fleet Catalog grid with logged-in user recommendations
            if (document.getElementById('cars-grid-container')) {
                this.fetchCars();
                this.loadTrendingSearches();
            }

            // 2. Refresh Home Page Curated Showcase
            if (document.getElementById('featured-cars-grid')) {
                this.switchCuratedTab(this.activeCuratedTab || 'personalized');
            }

            // 3. Refresh Similar Cars in open detail modal
            if (this.activeCar && document.getElementById('car-detail-modal')?.classList.contains('active')) {
                this.loadSimilarCars(this.activeCar.id);
            }

            if (user) {
                Toast.info('✨ Personalized vehicle recommendations updated for your profile.', 'AI Matched');
            }
        });
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

    async loadTrendingSearches() {
        const container = document.getElementById('fleet-trending-searches');
        if (!container) return;

        try {
            const data = await API.get('/analytics/trending-searches/', { limit: 6 });
            const searches = (data.results || data || []);
            if (!searches.length) return;

            container.innerHTML = searches.map(item => `
                <button type="button" class="filter-chip" style="font-size:0.7rem; padding:2px 8px; margin:0; background:#f1f5f9; border:1px solid var(--border-color); cursor:pointer; font-weight:600;" onclick="Customer.quickSearch('${item.query.replace(/'/g, "\\'")}')">
                    ${item.query}
                </button>
            `).join('');
        } catch (e) {
            console.warn('Trending searches fetch notice:', e);
        }
    },

    quickSearch(term) {
        this.filters.search = term;
        const searchInput = document.getElementById('fleet-search-input');
        if (searchInput) searchInput.value = term;
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
                status: this.filters.status,
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

            if (countEl) {
                const total = this.cars.length;
                const available = this.cars.filter(c => c.status === 'AVAILABLE' && c.is_available_for_dates !== false).length;
                const bookedDates = this.cars.filter(c => c.status === 'AVAILABLE' && c.is_available_for_dates === false).length;
                const rented = this.cars.filter(c => c.status === 'RENTED').length;
                const maintenance = this.cars.filter(c => c.status === 'MAINTENANCE').length;
                let breakdownParts = [];
                if (available) breakdownParts.push(`${available} Available`);
                if (bookedDates) breakdownParts.push(`${bookedDates} Booked for Dates`);
                if (rented) breakdownParts.push(`${rented} Rented`);
                if (maintenance) breakdownParts.push(`${maintenance} In Service`);
                const breakdown = breakdownParts.length ? ` (${breakdownParts.join(', ')})` : '';
                countEl.innerText = `${total} Vehicle${total === 1 ? '' : 's'}${breakdown}`;
            }
            this.renderCars();
        } catch (err) {
            if (grid) grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--danger);">${err.message}</div>`;
        }
    },

    activeCuratedTab: 'personalized',
    curatedFilter: '',

    async switchCuratedTab(type = 'personalized') {
        this.activeCuratedTab = type;
        const grid = document.getElementById('featured-cars-grid');
        const titleEl = document.getElementById('curated-section-title');
        const descEl = document.getElementById('curated-section-desc');

        // Update tab buttons active state
        document.querySelectorAll('#curated-tabs-wrapper .category-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.getElementById(`tab-btn-${type}`);
        if (activeBtn) activeBtn.classList.add('active');

        // Update section titles
        if (type === 'personalized') {
            if (titleEl) titleEl.innerText = 'Recommended For You';
            if (descEl) descEl.innerText = 'Personalized vehicles matched to your driving preferences, past trips, and favorite vehicle classes.';
        } else if (type === 'trending') {
            if (titleEl) titleEl.innerText = 'Trending This Week';
            if (descEl) descEl.innerText = 'Vehicles experiencing the highest surge in bookings and weekly reservation momentum.';
        } else if (type === 'popular') {
            if (titleEl) titleEl.innerText = 'Most Popular Fleet';
            if (descEl) descEl.innerText = 'Customer-favorite luxury and executive vehicles with top satisfaction ratings (4.8+ Stars).';
        }

        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:50px 0;">
                    <i class="fa-solid fa-circle-notch fa-spin text-gradient" style="font-size:2rem; margin-bottom:12px;"></i>
                    <p style="color:var(--text-secondary); font-size:0.9rem;">Loading ${type} vehicles...</p>
                </div>
            `;
        }

        try {
            const data = await API.get(`/analytics/recommendations/${type}/`, { limit: 8 });
            const cars = (data.results || data || []);
            if (grid) {
                if (!cars.length) {
                    grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-muted);">No vehicles found in this collection.</div>`;
                } else {
                    grid.innerHTML = cars.map(car => this.generateCarCardHtml(car)).join('');
                }
            }
        } catch (e) {
            console.error(`Curated cars error (${type}):`, e);
            if (grid) grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:30px; color:var(--danger);">Could not load ${type} vehicles.</div>`;
        }
    },

    async selectCuratedFleet(type = '') {
        this.curatedFilter = type;
        const countEl = document.getElementById('results-count-display');
        const viewLabel = document.getElementById('curated-view-label');
        const grid = document.getElementById('cars-grid-container');

        // Update pills active state
        document.querySelectorAll('#curated-fleet-pills .filter-chip').forEach(c => c.classList.remove('active'));
        if (type === 'personalized') {
            document.getElementById('curated-recommended-chip')?.classList.add('active');
            if (viewLabel) viewLabel.innerText = 'AI Recommended Vehicles';
        } else if (type === 'trending') {
            document.getElementById('curated-trending-chip')?.classList.add('active');
            if (viewLabel) viewLabel.innerText = 'Trending This Week';
        } else if (type === 'popular') {
            document.getElementById('curated-popular-chip')?.classList.add('active');
            if (viewLabel) viewLabel.innerText = 'Most Popular Fleet';
        } else {
            document.getElementById('curated-all-chip')?.classList.add('active');
            if (viewLabel) viewLabel.innerText = 'All Available Fleet';
            this.fetchCars();
            return;
        }

        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:60px 0;">
                    <i class="fa-solid fa-circle-notch fa-spin text-gradient" style="font-size:2.5rem; margin-bottom:12px;"></i>
                    <p style="color:var(--text-secondary);">Loading curated collection...</p>
                </div>
            `;
        }

        try {
            const data = await API.get(`/analytics/recommendations/${type}/`, { limit: 20 });
            this.cars = (data.results || data || []);
            if (countEl) {
                countEl.innerText = `${this.cars.length} Curated Vehicle${this.cars.length === 1 ? '' : 's'}`;
            }
            this.renderCars();
        } catch (e) {
            console.error('Curated fleet error:', e);
            if (grid) grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--danger);">${e.message}</div>`;
        }
    },

    async fetchFeaturedCars() {
        await this.switchCuratedTab('personalized');
    },

    generateCarCardHtml(car, position = 1, source = 'search_details') {
        const isBookedForDates = car.status === 'AVAILABLE' && car.is_available_for_dates === false;
        let statusBadgeHtml = '';
        let actionBtnHtml = '';

        if (car.status === 'AVAILABLE' && !isBookedForDates) {
            statusBadgeHtml = `
                <span class="badge" style="position:absolute; top:12px; right:12px; font-weight:700; font-size:0.75rem; box-shadow:0 2px 8px rgba(16,185,129,0.35); background:#10b981; color:#ffffff; padding:4px 10px; border-radius:20px; z-index:2;">
                    <i class="fa-solid fa-circle-check"></i> Available
                </span>
            `;
            actionBtnHtml = `
                <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id}, '${source}', ${position})">
                    <i class="fa-regular fa-eye"></i> Details
                </button>
                <button class="btn btn-primary btn-sm" onclick="BookingWizard.startBooking(${car.id})">
                    <i class="fa-solid fa-calendar-check"></i> Book Now
                </button>
            `;
        } else if (isBookedForDates) {
            statusBadgeHtml = `
                <span class="badge" style="position:absolute; top:12px; right:12px; font-weight:700; font-size:0.75rem; box-shadow:0 2px 8px rgba(239,68,68,0.35); background:#ef4444; color:#ffffff; padding:4px 10px; border-radius:20px; z-index:2;">
                    <i class="fa-solid fa-calendar-xmark"></i> Reserved for Dates
                </span>
            `;
            actionBtnHtml = `
                <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id}, '${source}', ${position})">
                    <i class="fa-regular fa-eye"></i> Details
                </button>
                <button class="btn btn-secondary btn-sm" disabled style="opacity:0.75; cursor:not-allowed; background:#f1f5f9; color:var(--text-muted); border-color:var(--border-color);" title="Already reserved for your selected dates">
                    <i class="fa-solid fa-calendar-xmark"></i> Booked Dates
                </button>
            `;
        } else if (car.status === 'RENTED') {
            statusBadgeHtml = `
                <span class="badge" style="position:absolute; top:12px; right:12px; font-weight:700; font-size:0.75rem; box-shadow:0 2px 8px rgba(245,158,11,0.35); background:#f59e0b; color:#ffffff; padding:4px 10px; border-radius:20px; z-index:2;">
                    <i class="fa-solid fa-clock"></i> Currently Rented
                </span>
            `;
            actionBtnHtml = `
                <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id}, '${source}', ${position})">
                    <i class="fa-regular fa-eye"></i> Details
                </button>
                <button class="btn btn-secondary btn-sm" disabled style="opacity:0.75; cursor:not-allowed; background:#f1f5f9; color:var(--text-muted); border-color:var(--border-color);" title="Currently out on an active customer rental">
                    <i class="fa-solid fa-clock"></i> Rented Out
                </button>
            `;
        } else if (car.status === 'MAINTENANCE') {
            statusBadgeHtml = `
                <span class="badge" style="position:absolute; top:12px; right:12px; font-weight:700; font-size:0.75rem; box-shadow:0 2px 8px rgba(239,68,68,0.35); background:#ef4444; color:#ffffff; padding:4px 10px; border-radius:20px; z-index:2;">
                    <i class="fa-solid fa-screwdriver-wrench"></i> In Maintenance
                </span>
            `;
            actionBtnHtml = `
                <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id}, '${source}', ${position})">
                    <i class="fa-regular fa-eye"></i> Details
                </button>
                <button class="btn btn-secondary btn-sm" disabled style="opacity:0.75; cursor:not-allowed; background:#f1f5f9; color:var(--text-muted); border-color:var(--border-color);" title="Undergoing routine mechanical maintenance">
                    <i class="fa-solid fa-wrench"></i> In Service
                </button>
            `;
        } else {
            statusBadgeHtml = `
                <span class="badge" style="position:absolute; top:12px; right:12px; font-weight:700; font-size:0.75rem; background:#64748b; color:#ffffff; padding:4px 10px; border-radius:20px; z-index:2;">
                    ${car.status}
                </span>
            `;
            actionBtnHtml = `
                <button class="btn btn-outline btn-sm" onclick="Customer.openDetailModal(${car.id}, '${source}', ${position})">
                    <i class="fa-regular fa-eye"></i> Details
                </button>
            `;
        }

        const carImgUrl = car.primary_image || car.main_image_url;
        const carImgMarkup = carImgUrl
            ? `<img src="${carImgUrl}" alt="${car.display_name}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" /><div class="image-unavailable-placeholder" style="display:none;"><i class="fa-solid fa-car-side"></i><span>Image Unavailable</span></div>`
            : `<div class="image-unavailable-placeholder"><i class="fa-solid fa-car-side"></i><span>Image Unavailable</span></div>`;

        return `
            <div class="car-card animate-slide-in">
                <div class="car-img-wrapper" style="position:relative;">
                    ${carImgMarkup}
                    <span class="badge badge-primary car-category-badge">
                        <i class="fa-solid ${car.category?.icon || 'fa-car'}"></i> ${car.category?.name || 'Car'}
                    </span>
                    ${statusBadgeHtml}
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
                        ${actionBtnHtml}
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
                    <p style="color:var(--text-secondary); max-width:460px; margin:0 auto 20px;">Try adjusting your dates, budget slider, status, or category filters to explore more cars.</p>
                    <button class="btn btn-primary" onclick="Customer.resetFilters()">Reset All Filters</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.cars.map((car, idx) => this.generateCarCardHtml(car, idx + 1, 'search_details')).join('');
    },

    resetFilters() {
        this.filters.category = '';
        this.filters.search = '';
        this.filters.status = '';
        this.filters.max_price = 10000;
        this.filters.transmission = '';
        this.filters.fuel_type = '';
        this.filters.seats = '';
        this.filters.ordering = '';
        
        const slider = document.getElementById('price-range-slider');
        if (slider) slider.value = 10000;
        const priceMaxDisplay = document.getElementById('price-max-display');
        if (priceMaxDisplay) priceMaxDisplay.innerText = '₹10000';
        const searchInput = document.getElementById('fleet-search-input');
        if (searchInput) searchInput.value = '';

        const statusSelect = document.getElementById('fleet-status-select');
        if (statusSelect) statusSelect.value = '';
        
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        const allStatusChip = document.querySelector('.filter-chip[data-group="status"][data-value=""]');
        if (allStatusChip) allStatusChip.classList.add('active');

        document.querySelectorAll('.category-tab-btn').forEach(b => b.classList.toggle('active', b.dataset.slug === ''));
        this.fetchCars();
    },    async openDetailModal(carId, source = 'search_details', position = 1) {
        // Track click and write clicked_car to SearchLog only when details button is clicked!
        try {
            API.post('/analytics/track-click/', {
                car_id: carId,
                recommendation_type: source,
                position: position,
                clicked: true,
                search_log_id: this.currentSearchLogId || null
            }).then(res => {
                if (res && res.recommendation_click_id) {
                    this.lastRecommendationClickId = res.recommendation_click_id;
                }
            }).catch(e => console.warn('Click tracking notice:', e));
        } catch (e) {}

        try {
            const car = await API.get(`/cars/${carId}/`);
            this.activeCar = car;

            const modal = document.getElementById('car-detail-modal');
            if (!modal) return;

            let modalStatusBadge = '';
            if (car.status === 'AVAILABLE') {
                modalStatusBadge = '<span class="badge" style="background:#10b981; color:#ffffff; font-size:0.75rem; padding:3px 8px; border-radius:12px; margin-left:8px;"><i class="fa-solid fa-circle-check"></i> Available</span>';
            } else if (car.status === 'RENTED') {
                modalStatusBadge = '<span class="badge" style="background:#f59e0b; color:#ffffff; font-size:0.75rem; padding:3px 8px; border-radius:12px; margin-left:8px;"><i class="fa-solid fa-clock"></i> Currently Rented</span>';
            } else if (car.status === 'MAINTENANCE') {
                modalStatusBadge = '<span class="badge" style="background:#ef4444; color:#ffffff; font-size:0.75rem; padding:3px 8px; border-radius:12px; margin-left:8px;"><i class="fa-solid fa-wrench"></i> In Maintenance</span>';
            }

            document.getElementById('detail-car-title').innerHTML = `${car.year} ${car.brand} ${car.model} ${modalStatusBadge}`;
            document.getElementById('detail-car-price').innerHTML = `${formatCurrency(car.price_per_day)}<span style="font-size:0.8rem; font-weight:normal; color:var(--text-secondary);"> /day</span>`;
            document.getElementById('detail-car-rating').innerHTML = `<i class="fa-solid fa-star" style="color:var(--warning);"></i> ${car.average_rating} (${car.total_reviews} reviews)`;

            const thumbsContainer = document.getElementById('detail-thumbs-container');
            const mainImg = document.getElementById('detail-main-img');
            const mainPlaceholder = document.getElementById('detail-main-img-placeholder');
            const badgeEl = document.getElementById('detail-angle-badge');

            const gallery = [
                { url: car.primary_image || car.main_image_url, label: 'Main Overview' },
                ...(car.images?.map(i => ({
                    url: i.url,
                    label: i.view_type_display || i.view_type || i.caption || 'Angle View'
                })) || [])
            ].filter(item => Boolean(item.url));

            if (gallery.length && gallery[0].url) {
                if (mainImg) {
                    mainImg.style.display = 'block';
                    mainImg.src = gallery[0].url;
                }
                if (mainPlaceholder) mainPlaceholder.style.display = 'none';
                if (badgeEl) {
                    badgeEl.style.display = 'inline-flex';
                    badgeEl.innerHTML = `<i class="fa-solid fa-camera"></i> ${gallery[0].label}`;
                }
            } else {
                if (mainImg) mainImg.style.display = 'none';
                if (mainPlaceholder) mainPlaceholder.style.display = 'flex';
                if (badgeEl) badgeEl.style.display = 'none';
            }

            if (thumbsContainer) {
                if (gallery.length > 1) {
                    thumbsContainer.style.display = 'flex';
                    thumbsContainer.innerHTML = gallery.map((item, i) => `
                        <div class="gallery-thumb-wrapper ${i === 0 ? 'active' : ''}" onclick="Customer.switchGalleryImage('${item.url}', '${item.label}', this)" style="cursor:pointer; flex-shrink:0; text-align:center;">
                            <img src="${item.url}" class="gallery-thumb" style="width:70px; height:50px; object-fit:cover; border-radius:var(--radius-sm); border:2px solid ${i === 0 ? 'var(--primary)' : 'var(--border-color)'}; transition:var(--transition);" alt="${item.label}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                            <div class="image-unavailable-placeholder thumb-size" style="width:70px; height:50px; display:none; margin:0 auto;"><i class="fa-solid fa-car-side"></i></div>
                            <span style="font-size:0.65rem; color:var(--text-secondary); display:block; margin-top:2px; max-width:70px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.label}</span>
                        </div>
                    `).join('');
                } else {
                    thumbsContainer.style.display = 'none';
                    thumbsContainer.innerHTML = '';
                }
            }

            const specsContainer = document.getElementById('detail-specs-table');
            if (specsContainer) {
                specsContainer.innerHTML = `
                    <tr><td>Brand & Model</td><td>${car.brand} ${car.model}</td></tr>
                    <tr><td>Model Year</td><td>${car.year}</td></tr>
                    <tr><td>Status</td><td><strong>${car.status}</strong></td></tr>
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
                    reviewsContainer.innerHTML = reviews.map(r => {
                        const revInitial = (r.customer_name ? r.customer_name[0] : 'U').toUpperCase();
                        const revAvatar = r.customer_avatar
                            ? `<div class="user-avatar-circle" style="width:28px; height:28px; font-size:0.75rem; flex-shrink:0; overflow:hidden;"><img src="${r.customer_avatar}" alt="${r.customer_name}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" onerror="this.outerHTML='<span>${revInitial}</span>';" /></div>`
                            : `<div class="user-avatar-circle" style="width:28px; height:28px; font-size:0.75rem; flex-shrink:0; background:linear-gradient(135deg, var(--primary), var(--secondary));">${revInitial}</div>`;

                        return `
                        <div style="padding:14px 0; border-bottom:1px solid var(--border-color);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    ${revAvatar}
                                    <strong style="font-size:0.88rem;">${r.customer_name}</strong>
                                </div>
                                <div style="font-size:0.8rem; display:flex; gap:2px;">
                                    ${Array.from({length: 5}, (_, i) => `<i class="fa-solid fa-star" style="color:${i < r.rating ? '#f59e0b' : '#cbd5e1'};"></i>`).join('')}
                                </div>
                            </div>
                            <div style="font-weight:600; font-size:0.85rem; margin-bottom:2px;">${r.title || ''}</div>
                            <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.5;">${r.comment}</div>
                        </div>
                    `;
                    }).join('');
                }
            }

            const bookBtn = document.getElementById('detail-book-btn');
            if (bookBtn) {
                const isBookedForDates = car.status === 'AVAILABLE' && car.is_available_for_dates === false;
                if (car.status === 'AVAILABLE' && !isBookedForDates) {
                    bookBtn.disabled = false;
                    bookBtn.className = 'btn btn-primary';
                    bookBtn.innerHTML = '<i class="fa-solid fa-calendar-check"></i> Book This Vehicle';
                    bookBtn.title = 'Proceed to reserve this vehicle.';
                    bookBtn.onclick = () => {
                        this.closeDetailModal();
                        BookingWizard.startBooking(car.id);
                    };
                } else if (isBookedForDates) {
                    bookBtn.disabled = true;
                    bookBtn.className = 'btn btn-secondary';
                    bookBtn.innerHTML = '<i class="fa-solid fa-calendar-xmark"></i> Reserved for Selected Dates';
                    bookBtn.title = 'This vehicle is booked by another customer for your selected dates. Please choose different dates or select another car.';
                    bookBtn.onclick = null;
                } else if (car.status === 'RENTED') {
                    bookBtn.disabled = true;
                    bookBtn.className = 'btn btn-secondary';
                    bookBtn.innerHTML = '<i class="fa-solid fa-clock"></i> Currently Rented Out';
                    bookBtn.title = 'This vehicle is currently rented by another customer.';
                    bookBtn.onclick = null;
                } else if (car.status === 'MAINTENANCE') {
                    bookBtn.disabled = true;
                    bookBtn.className = 'btn btn-secondary';
                    bookBtn.innerHTML = '<i class="fa-solid fa-wrench"></i> Currently In Service';
                    bookBtn.title = 'This vehicle is undergoing routine maintenance.';
                    bookBtn.onclick = null;
                } else {
                    bookBtn.disabled = true;
                    bookBtn.className = 'btn btn-secondary';
                    bookBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Unavailable';
                    bookBtn.title = 'This vehicle is unavailable.';
                    bookBtn.onclick = null;
                }
            }

            // Load AI-matched Similar Cars using analytics recommendation engine
            this.loadSimilarCars(car.id);

            modal.classList.add('active');
        } catch (e) {
            Toast.error('Could not load car details.');
        }
    },

    async loadSimilarCars(carId) {
        const container = document.getElementById('detail-similar-cars-container');
        const section = document.getElementById('detail-similar-cars-section');
        if (!container) return;

        if (section) section.style.display = 'block';
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align:center; padding:18px 0; color:var(--text-muted); font-size:0.85rem;">
                <i class="fa-solid fa-circle-notch fa-spin text-gradient" style="margin-right:6px;"></i> Finding similar vehicles in fleet...
            </div>
        `;

        try {
            const data = await API.get(`/analytics/recommendations/similar/${carId}/`, { limit: 4 });
            const cars = data.results || data || [];

            if (!cars.length) {
                if (section) section.style.display = 'none';
                return;
            }

            if (section) section.style.display = 'block';

            container.innerHTML = cars.map((car, idx) => {
                const simImg = car.primary_image || car.main_image_url;
                const simImgHtml = simImg
                    ? `<img src="${simImg}" alt="${car.display_name}" style="width:100%; height:100%; object-fit:cover;" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" /><div class="image-unavailable-placeholder thumb-size" style="width:100%; height:100%; display:none;"><i class="fa-solid fa-car-side"></i></div>`
                    : `<div class="image-unavailable-placeholder thumb-size" style="width:100%; height:100%;"><i class="fa-solid fa-car-side"></i></div>`;

                return `
                    <div class="similar-car-card" style="background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius-md); overflow:hidden; display:flex; flex-direction:column; justify-content:space-between; transition:transform 0.2s, box-shadow 0.2s; box-shadow:0 1px 4px rgba(0,0,0,0.04);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.08)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 1px 4px rgba(0,0,0,0.04)';">
                        <div style="position:relative; width:100%; height:110px; background:#0f172a; cursor:pointer;" onclick="Customer.openDetailModal(${car.id}, 'similar', ${idx + 1})">
                            ${simImgHtml}
                            <span class="badge" style="position:absolute; top:6px; left:6px; font-size:0.65rem; background:rgba(15,23,42,0.8); color:#fff; backdrop-filter:blur(4px); padding:2px 6px; border-radius:4px;">
                                ${car.category?.name || 'Vehicle'}
                            </span>
                            <span class="badge" style="position:absolute; top:6px; right:6px; font-size:0.65rem; background:#10b981; color:#fff; padding:2px 6px; border-radius:4px;">
                                <i class="fa-solid fa-star"></i> ${car.average_rating}
                            </span>
                        </div>
                        <div style="padding:10px 12px; display:flex; flex-direction:column; flex:1; justify-content:space-between;">
                            <div>
                                <div style="font-weight:700; font-size:0.85rem; color:var(--text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; cursor:pointer;" onclick="Customer.openDetailModal(${car.id}, 'similar', ${idx + 1})" title="${car.display_name}">
                                    ${car.brand} ${car.model}
                                </div>
                                <div style="font-size:0.75rem; color:var(--text-muted); margin:3px 0 6px; display:flex; gap:6px; flex-wrap:wrap;">
                                    <span><i class="fa-solid fa-gear"></i> ${car.transmission}</span>
                                    <span>&bull;</span>
                                    <span><i class="fa-solid fa-gas-pump"></i> ${car.fuel_type}</span>
                                </div>
                            </div>
                            <div style="display:flex; align-items:center; justify-content:space-between; margin-top:6px; padding-top:6px; border-top:1px dashed var(--border-color);">
                                <div style="font-weight:800; font-size:0.88rem; color:var(--primary);">
                                    ${formatCurrency(car.price_per_day)}<small style="font-size:0.68rem; font-weight:normal; color:var(--text-secondary);"> /d</small>
                                </div>
                                <div style="display:flex; gap:4px;">
                                    <button class="btn btn-outline btn-sm" style="padding:4px 8px; font-size:0.7rem;" onclick="Customer.openDetailModal(${car.id}, 'similar', ${idx + 1})" title="View Details">
                                        <i class="fa-regular fa-eye"></i>
                                    </button>
                                    <button class="btn btn-primary btn-sm" style="padding:4px 8px; font-size:0.7rem;" onclick="BookingWizard.startBooking(${car.id})" title="Book Car">
                                        <i class="fa-solid fa-key"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {
            console.error('Similar cars error:', e);
            if (section) section.style.display = 'none';
        }
    },

    switchGalleryImage(imgUrl, label, el) {
        const mainImg = document.getElementById('detail-main-img');
        const mainPlaceholder = document.getElementById('detail-main-img-placeholder');
        const badgeEl = document.getElementById('detail-angle-badge');

        if (imgUrl) {
            if (mainImg) {
                mainImg.style.display = 'block';
                mainImg.src = imgUrl;
            }
            if (mainPlaceholder) mainPlaceholder.style.display = 'none';
            if (badgeEl && label) {
                badgeEl.style.display = 'inline-flex';
                badgeEl.innerHTML = `<i class="fa-solid fa-camera"></i> ${label}`;
            }
        } else {
            if (mainImg) mainImg.style.display = 'none';
            if (mainPlaceholder) mainPlaceholder.style.display = 'flex';
            if (badgeEl) badgeEl.style.display = 'none';
        }
        
        document.querySelectorAll('.gallery-thumb-wrapper').forEach(w => {
            w.classList.remove('active');
            const img = w.querySelector('img');
            if (img) img.style.borderColor = 'var(--border-color)';
        });
        if (el) {
            el.classList.add('active');
            const img = el.querySelector('img');
            if (img) img.style.borderColor = 'var(--primary)';
        }
    },

    closeDetailModal() {
        const modal = document.getElementById('car-detail-modal');
        if (modal) modal.classList.remove('active');
    }
};
