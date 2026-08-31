// Admin Operational Dashboard Controller
import { API } from './api.js';
import { Auth } from './auth.js';
import { Toast } from './toast.js';
import { formatCurrency, formatDate, formatDateTime } from './config.js';

export const Admin = {
    revenueChart: null,
    categoryChart: null,
    fleet: [],
    bookings: [],
    customers: [],
    payments: [],
    reviews: [],
    coupons: [],
    categories: [],
    locations: [],

    async init() {
        if (!API.isAuthenticated() || !API.isAdmin()) {
            sessionStorage.setItem(
                'authRedirectMessage',
                'Admin privileges required. Please sign in as an administrator.'
            );
            window.location.href = '/?auth=required';
            return;
        }

        this.bindEvents();
        await this.loadInitialMetadata();
        await this.loadDashboardAnalytics();
    },

    bindEvents() {
        document.querySelectorAll('.sidebar-link[data-view]').forEach(link => {
            link.addEventListener('click', () => {
                const view = link.dataset.view;
                document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                document.querySelectorAll('.admin-view-panel').forEach(p => {
                    p.classList.toggle('hidden', p.dataset.view !== view);
                });

                document.getElementById('admin-page-title').innerText = link.querySelector('span')?.innerText || 'Dashboard';

                if (view === 'dashboard') this.loadDashboardAnalytics();
                if (view === 'fleet') this.loadFleet();
                if (view === 'bookings') this.loadBookings();
                if (view === 'customers') this.loadCustomers();
                if (view === 'payments') this.loadPayments();
                if (view === 'reviews') this.loadReviews();
                if (view === 'coupons') this.loadCoupons();
            });
        });
    },

    async loadInitialMetadata() {
        try {
            const [catData, locData] = await Promise.all([
                API.get('/categories/'),
                API.get('/locations/')
            ]);
            this.categories = catData.results || catData;
            this.locations = locData.results || locData;

            // Populate Category and Location dropdowns in Car modal & Fleet Filter toolbar
            const catSelect = document.getElementById('car-modal-category');
            const locSelect = document.getElementById('car-modal-location');
            const filterCatSelect = document.getElementById('fleet-filter-category');
            const filterLocSelect = document.getElementById('fleet-filter-location');

            if (catSelect) {
                catSelect.innerHTML = this.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
            if (locSelect) {
                locSelect.innerHTML = this.locations.map(l => `<option value="${l.id}">${l.name} (${l.city})</option>`).join('');
            }
            if (filterCatSelect) {
                filterCatSelect.innerHTML = '<option value="">All Categories</option>' + this.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
            if (filterLocSelect) {
                filterLocSelect.innerHTML = '<option value="">All Locations</option>' + this.locations.map(l => `<option value="${l.id}">${l.name} (${l.city})</option>`).join('');
            }
        } catch (e) {
            console.error('Metadata error:', e);
        }
    },

    async loadDashboardAnalytics() {
        try {
            const data = await API.get('/admin/analytics/dashboard/');
            const kpis = data.kpis;

            document.getElementById('kpi-revenue').innerText = formatCurrency(kpis.total_revenue);
            document.getElementById('kpi-bookings').innerText = kpis.total_bookings;
            document.getElementById('kpi-active-rentals').innerText = kpis.active_rentals;
            document.getElementById('kpi-fleet-size').innerText = `${kpis.fleet_size} (${kpis.available_cars} Avail)`;
            document.getElementById('kpi-utilization').innerText = `${kpis.utilization_rate}%`;
            document.getElementById('kpi-customers').innerText = kpis.total_customers;

            this.renderCharts(data.charts);
            this.renderRecentBookings(data.recent_bookings || []);
            this.loadRecommendationPerformance();
        } catch (e) {
            console.error('Analytics error:', e);
        }
    },

    async loadRecommendationPerformance() {
        const tbody = document.getElementById('ai-rec-performance-tbody');
        const listContainer = document.getElementById('ai-trending-searches-list');

        try {
            const [perfData, searchData] = await Promise.all([
                API.get('/admin/analytics/recommendation-performance/'),
                API.get('/analytics/trending-searches/', { limit: 6 })
            ]);

            // 1. Populate Algorithm Conversion Breakdown Table
            if (tbody && perfData.performance) {
                const breakdown = perfData.performance.breakdown || [];
                if (!breakdown.length) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:15px; color:var(--text-muted);">No recommendation click data logged yet.</td></tr>';
                } else {
                    tbody.innerHTML = breakdown.map(item => `
                        <tr>
                            <td><strong>${item.display_name}</strong></td>
                            <td><span class="badge" style="background:#f1f5f9; color:var(--text-main); font-weight:700;">${item.clicks}</span></td>
                            <td><span class="badge" style="background:rgba(16,185,129,0.15); color:var(--success); font-weight:700;">${item.bookings}</span></td>
                            <td><strong style="color:${item.cvr_percent > 0 ? 'var(--primary)' : 'var(--text-muted)'};">${item.cvr_percent}%</strong></td>
                        </tr>
                    `).join('');
                }
            }

            // 2. Populate High-Demand Customer Searches List
            if (listContainer) {
                const searches = searchData.results || searchData || [];
                if (!searches.length) {
                    listContainer.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">No user searches recorded yet.</p>';
                } else {
                    listContainer.innerHTML = searches.map(s => `
                        <div style="display:flex; justify-content:space-between; align-items:center; background:#f8fafc; border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:8px 12px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <i class="fa-solid fa-magnifying-glass" style="font-size:0.8rem; color:var(--primary);"></i>
                                <span style="font-weight:600; font-size:0.88rem; color:var(--text-main);">${s.query}</span>
                            </div>
                            <span class="badge" style="background:rgba(14,77,92,0.12); color:var(--primary); font-size:0.75rem; font-weight:700;">
                                ${s.count} search${s.count === 1 ? '' : 'es'}
                            </span>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            console.error('AI Performance load error:', e);
        }
    },

    renderCharts(chartsData) {
        if (!window.Chart) return;

        // 1. Monthly Revenue Line Chart
        const revCtx = document.getElementById('revenueTrendChart')?.getContext('2d');
        if (revCtx) {
            if (this.revenueChart) this.revenueChart.destroy();
            const labels = chartsData.monthly_revenue.map(d => d.month);
            const revenues = chartsData.monthly_revenue.map(d => d.revenue);

            this.revenueChart = new Chart(revCtx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: revenues,
                        borderColor: '#0e4d5c',
                        backgroundColor: 'rgba(14, 77, 92, 0.12)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#165b6d',
                        pointBorderColor: '#0e4d5c',
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(0,0,0,0.06)' }, ticks: { color: '#4b5563' } },
                        y: { grid: { color: 'rgba(0,0,0,0.06)' }, ticks: { color: '#4b5563' } }
                    }
                }
            });
        }

        // 2. Category Distribution Doughnut Chart
        const catCtx = document.getElementById('categoryDoughnutChart')?.getContext('2d');

        if (catCtx) {

            if (this.categoryChart) {
                this.categoryChart.destroy();
            }

            const labels = chartsData.category_breakdown.map(c =>
                `${c.name} — Vehicles: ${c.vehicles}, Rentals: ${c.rentals}`
            );

            const counts = chartsData.category_breakdown.map(c => c.vehicles);

            this.categoryChart = new Chart(catCtx, {
                type: 'doughnut',

                data: {
                    labels,

                    datasets: [{
                        data: counts,

                        backgroundColor: [
                            '#0e4d5c',
                            '#d96b27',
                            '#10b981',
                            '#d97706',
                            '#0284c7',
                            '#64748b'
                        ],

                        borderWidth: 0
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            position: 'bottom',

                            labels: {
                                color: '#4b5563',
                                boxWidth: 12
                            }
                        },

                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const category =
                                        chartsData.category_breakdown[context.dataIndex];

                                    return [
                                        `Vehicles: ${category.vehicles}`,
                                        `Rentals: ${category.rentals}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        }
    },

    renderRecentBookings(list) {
        const tbody = document.getElementById('recent-bookings-tbody');
        if (!tbody) return;
        if (!list.length) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No recent booking activity.</td></tr>';
            return;
        }

        tbody.innerHTML = list.map(b => `
            <tr>
                <td><span style="font-family:monospace; font-weight:700;">${b.code}</span></td>
                <td><strong>${b.customer}</strong></td>
                <td>${b.car}</td>
                <td>${b.start_date} → ${b.end_date}</td>
                <td><strong>${formatCurrency(b.total_amount)}</strong></td>
                <td><span class="badge ${b.status === 'COMPLETED' ? 'badge-info' : (b.status === 'ONGOING' ? 'badge-success' : 'badge-primary')}">${b.status}</span></td>
                <td><span class="badge ${b.payment_status === 'PAID' ? 'badge-success' : 'badge-warning'}">${b.payment_status}</span></td>
            </tr>
        `).join('');
    },

    // Fleet Management
    async loadFleet() {
        const tbody = document.getElementById('admin-fleet-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const data = await API.get('/admin/cars/');
            this.fleet = data.results || data;
            this.applyFleetFilters();
        } catch (e) {
            Toast.error('Could not load fleet.');
        }
    },

    applyFleetFilters() {
        const searchQuery = (document.getElementById('fleet-filter-search')?.value || '').trim().toLowerCase();
        const categoryId = document.getElementById('fleet-filter-category')?.value || '';
        const locationId = document.getElementById('fleet-filter-location')?.value || '';
        const status = document.getElementById('fleet-filter-status')?.value || '';
        const fuel = document.getElementById('fleet-filter-fuel')?.value || '';
        const transmission = document.getElementById('fleet-filter-transmission')?.value || '';
        const sortBy = document.getElementById('fleet-filter-sort')?.value || 'newest';

        let filtered = this.fleet.filter(car => {
            if (searchQuery) {
                const combined = `${car.brand} ${car.model} ${car.license_plate} ${car.category?.name || ''} ${car.location?.name || ''} ${car.location?.city || ''}`.toLowerCase();
                if (!combined.includes(searchQuery)) return false;
            }
            if (categoryId && String(car.category?.id) !== String(categoryId)) return false;
            if (locationId && String(car.location?.id) !== String(locationId)) return false;
            if (status && car.status !== status) return false;
            if (fuel && car.fuel_type !== fuel) return false;
            if (transmission && car.transmission !== transmission) return false;
            return true;
        });

        // Sorting
        if (sortBy === 'price_asc') {
            filtered.sort((a, b) => parseFloat(a.price_per_day) - parseFloat(b.price_per_day));
        } else if (sortBy === 'price_desc') {
            filtered.sort((a, b) => parseFloat(b.price_per_day) - parseFloat(a.price_per_day));
        } else if (sortBy === 'brand_asc') {
            filtered.sort((a, b) => a.brand.localeCompare(b.brand));
        } else if (sortBy === 'year_desc') {
            filtered.sort((a, b) => b.year - a.year);
        } else {
            // newest (by id desc)
            filtered.sort((a, b) => b.id - a.id);
        }

        const countEl = document.getElementById('fleet-filter-count');
        if (countEl) {
            countEl.innerText = `Showing ${filtered.length} of ${this.fleet.length} vehicles`;
        }

        this.renderFleetTable(filtered);
    },

    resetFleetFilters() {
        const search = document.getElementById('fleet-filter-search');
        const cat = document.getElementById('fleet-filter-category');
        const loc = document.getElementById('fleet-filter-location');
        const stat = document.getElementById('fleet-filter-status');
        const fuel = document.getElementById('fleet-filter-fuel');
        const trans = document.getElementById('fleet-filter-transmission');
        const sort = document.getElementById('fleet-filter-sort');

        if (search) search.value = '';
        if (cat) cat.value = '';
        if (loc) loc.value = '';
        if (stat) stat.value = '';
        if (fuel) fuel.value = '';
        if (trans) trans.value = '';
        if (sort) sort.value = 'newest';

        this.applyFleetFilters();
    },

    renderFleetTable(list = null) {
        const tbody = document.getElementById('admin-fleet-tbody');
        if (!tbody) return;

        const displayList = list !== null ? list : this.fleet;
        if (!displayList.length) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:32px 16px; color:var(--text-muted);"><i class="fa-solid fa-car-side" style="font-size:2rem; margin-bottom:8px; display:block; opacity:0.5;"></i>No vehicles match your active filter criteria. <button type="button" class="btn btn-outline btn-sm" style="margin-left:8px;" onclick="Admin.resetFleetFilters()">Reset Filters</button></td></tr>';
            return;
        }

        tbody.innerHTML = displayList.map(car => {
            const imgUrl = car.primary_image || car.main_image_url;
            const thumbMarkup = imgUrl
                ? `<img src="${imgUrl}" class="table-thumb" alt="${car.display_name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" /><div class="image-unavailable-placeholder thumb-size" style="display:none;"><i class="fa-solid fa-car-side"></i></div>`
                : `<div class="image-unavailable-placeholder thumb-size"><i class="fa-solid fa-car-side"></i></div>`;

            return `
            <tr>
                <td>
                    ${thumbMarkup}
                </td>
                <td>
                    <strong>${car.brand} ${car.model}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${car.year} • ${car.transmission} • ${car.fuel_type}</div>
                </td>
                <td><span class="badge badge-primary">${car.category?.name || 'Standard'}</span></td>
                <td><span style="font-family:monospace; font-weight:700;">${car.license_plate}</span></td>
                <td>${car.location?.name || car.location?.city || 'Hub'}</td>
                <td><strong>${formatCurrency(car.price_per_day)}</strong></td>
                <td>
                    <select class="form-control" style="padding:4px 8px; font-size:0.8rem;" onchange="Admin.updateCarStatus(${car.id}, this.value)">
                        <option value="AVAILABLE" ${car.status === 'AVAILABLE' ? 'selected' : ''}>Available</option>
                        <option value="RENTED" ${car.status === 'RENTED' ? 'selected' : ''}>Rented</option>
                        <option value="MAINTENANCE" ${car.status === 'MAINTENANCE' ? 'selected' : ''}>Maintenance</option>
                        <option value="INACTIVE" ${car.status === 'INACTIVE' ? 'selected' : ''}>Inactive</option>
                    </select>
                </td>
                <td>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-outline btn-sm" title="Edit Vehicle" onclick="Admin.openEditCarModal(${car.id})"><i class="fa-solid fa-pen"></i></button>
                        <button class="btn btn-danger btn-sm" title="Delete Vehicle" onclick="Admin.deleteCar(${car.id})"><i class="fa-solid fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');
    },

    pendingGalleryFiles: [],
    existingGalleryImages: [],

    handleImageFileSelect(event) {
        const file = event.target.files?.[0];
        const previewContainer = document.getElementById('car-image-preview-container');
        const previewImg = document.getElementById('car-image-preview-img');
        const previewName = document.getElementById('car-image-preview-name');

        if (file) {
            if (previewImg) previewImg.src = URL.createObjectURL(file);
            if (previewName) previewName.innerText = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
            if (previewContainer) {
                previewContainer.classList.remove('hidden');
                previewContainer.style.display = 'flex';
            }
        }
    },

    handleGalleryFilesSelect(event) {
        const files = Array.from(event.target.files || []);
        files.forEach((file) => {
            this.pendingGalleryFiles.push({
                file,
                url: URL.createObjectURL(file),
                viewType: 'OTHER',
                caption: ''
            });
        });
        this.renderGalleryPreviews();
        event.target.value = '';
    },

    removePendingGalleryFile(index) {
        this.pendingGalleryFiles.splice(index, 1);
        this.renderGalleryPreviews();
    },

    async deleteExistingGalleryImage(carId, imageId) {
        if (!confirm('Remove this photo view from the vehicle gallery?')) return;
        try {
            await API.delete(`/admin/cars/${carId}/gallery/${imageId}/`);
            this.existingGalleryImages = this.existingGalleryImages.filter(img => img.id !== imageId);
            this.renderGalleryPreviews();
            Toast.success('Gallery photo removed.');
            this.loadFleet();
        } catch (err) {
            Toast.error(err.message || 'Could not delete photo.');
        }
    },

    renderGalleryPreviews() {
        const grid = document.getElementById('gallery-previews-grid');
        const emptyHint = document.getElementById('gallery-empty-hint');
        if (!grid) return;

        const totalImages = this.existingGalleryImages.length + this.pendingGalleryFiles.length;
        if (emptyHint) emptyHint.style.display = totalImages === 0 ? 'block' : 'none';

        const carId = document.getElementById('car-modal-id')?.value;

        const existingHtml = this.existingGalleryImages.map((img) => `
            <div style="position: relative; border-radius: var(--radius-sm); overflow: hidden; border: 1px solid var(--border-color); background: #1f293d;">
                <img src="${img.url}" alt="${img.caption || 'Car Angle'}" style="width: 100%; height: 75px; object-fit: cover; display: block;" />
                <div style="padding: 4px 6px; font-size: 0.7rem; color: var(--text-secondary); background: rgba(0,0,0,0.7); display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: #818cf8;">${img.view_type_display || img.view_type || 'Angle'}</span>
                    ${carId ? `<button type="button" style="background: none; border: none; color: var(--danger); cursor: pointer; padding: 0;" title="Delete Photo" onclick="Admin.deleteExistingGalleryImage(${carId}, ${img.id})"><i class="fa-solid fa-trash"></i></button>` : ''}
                </div>
            </div>
        `).join('');

        const pendingHtml = this.pendingGalleryFiles.map((item, idx) => `
            <div style="position: relative; border-radius: var(--radius-sm); overflow: hidden; border: 1px dashed var(--primary); background: #1f293d;">
                <img src="${item.url}" alt="Preview" style="width: 100%; height: 75px; object-fit: cover; display: block;" />
                <div style="padding: 4px; background: rgba(0,0,0,0.85);">
                    <select class="form-control" style="padding: 2px 4px; font-size: 0.65rem; height: 22px; margin-bottom: 2px;" onchange="Admin.pendingGalleryFiles[${idx}].viewType = this.value">
                        <option value="FRONT">Front View</option>
                        <option value="SIDE">Side Profile</option>
                        <option value="REAR">Rear View</option>
                        <option value="INTERIOR">Interior</option>
                        <option value="DASHBOARD">Dashboard</option>
                        <option value="ANGLE">3/4 Angle</option>
                        <option value="OTHER" selected>Other Detail</option>
                    </select>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.65rem; color: #10b981; font-weight: 600;">Pending</span>
                        <button type="button" style="background: none; border: none; color: var(--danger); cursor: pointer; padding: 0;" title="Remove" onclick="Admin.removePendingGalleryFile(${idx})">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        grid.innerHTML = existingHtml + pendingHtml;
    },

    openAddCarModal() {
        document.getElementById('car-modal-id').value = '';
        document.getElementById('car-form').reset();

        this.pendingGalleryFiles = [];
        this.existingGalleryImages = [];
        this.renderGalleryPreviews();

        const fileInput = document.getElementById('car-modal-image-file');
        if (fileInput) fileInput.value = '';
        const galleryInput = document.getElementById('car-modal-gallery-files');
        if (galleryInput) galleryInput.value = '';

        const previewContainer = document.getElementById('car-image-preview-container');
        if (previewContainer) {
            previewContainer.classList.add('hidden');
            previewContainer.style.display = 'none';
        }

        document.getElementById('car-modal-title').innerText = 'Add New Vehicle to Fleet';
        document.getElementById('admin-car-modal').classList.add('active');
    },

    openEditCarModal(carId) {
        const car = this.fleet.find(c => c.id === carId);
        if (!car) return;

        this.pendingGalleryFiles = [];
        this.existingGalleryImages = car.images || [];

        document.getElementById('car-modal-id').value = car.id;
        document.getElementById('car-modal-brand').value = car.brand;
        document.getElementById('car-modal-model').value = car.model;
        document.getElementById('car-modal-year').value = car.year;
        document.getElementById('car-modal-plate').value = car.license_plate;
        document.getElementById('car-modal-price').value = car.price_per_day;
        document.getElementById('car-modal-deposit').value = car.security_deposit;
        document.getElementById('car-modal-category').value = car.category?.id || '';
        document.getElementById('car-modal-location').value = car.location?.id || '';
        document.getElementById('car-modal-transmission').value = car.transmission;
        document.getElementById('car-modal-fuel').value = car.fuel_type;
        document.getElementById('car-modal-seats').value = car.seats;
        document.getElementById('car-modal-hp').value = car.power_hp;
        document.getElementById('car-modal-desc').value = car.description || '';

        const fileInput = document.getElementById('car-modal-image-file');
        if (fileInput) fileInput.value = '';
        const galleryInput = document.getElementById('car-modal-gallery-files');
        if (galleryInput) galleryInput.value = '';

        const previewContainer = document.getElementById('car-image-preview-container');
        const previewImg = document.getElementById('car-image-preview-img');
        const previewName = document.getElementById('car-image-preview-name');

        const currentImg = car.primary_image || car.main_image_url;
        if (currentImg && previewContainer && previewImg) {
            previewImg.style.display = 'block';
            previewImg.src = currentImg;
            previewImg.onerror = function() {
                this.style.display = 'none';
                if (previewName) previewName.innerText = `Image Unavailable (Path: ${car.main_image_path || 'None'})`;
            };
            if (previewName) previewName.innerText = `Current Image: ${car.brand} ${car.model}`;
            previewContainer.classList.remove('hidden');
            previewContainer.style.display = 'flex';
        } else if (previewContainer) {
            previewContainer.classList.add('hidden');
            previewContainer.style.display = 'none';
        }

        this.renderGalleryPreviews();

        document.getElementById('car-modal-title').innerText = `Edit ${car.brand} ${car.model}`;
        document.getElementById('admin-car-modal').classList.add('active');
    },

    closeCarModal() {
        document.getElementById('admin-car-modal').classList.remove('active');
    },

    async saveCar() {
        const id = document.getElementById('car-modal-id').value;
        const formData = new FormData();

        formData.append('brand', document.getElementById('car-modal-brand').value.trim());
        formData.append('model', document.getElementById('car-modal-model').value.trim());
        formData.append('year', document.getElementById('car-modal-year').value);
        formData.append('license_plate', document.getElementById('car-modal-plate').value.trim());
        formData.append('price_per_day', document.getElementById('car-modal-price').value);
        formData.append('security_deposit', document.getElementById('car-modal-deposit').value || '0');
        formData.append('category_id', document.getElementById('car-modal-category').value);
        formData.append('location_id', document.getElementById('car-modal-location').value);
        formData.append('transmission', document.getElementById('car-modal-transmission').value);
        formData.append('fuel_type', document.getElementById('car-modal-fuel').value);
        formData.append('seats', document.getElementById('car-modal-seats').value || '4');
        formData.append('power_hp', document.getElementById('car-modal-hp').value || '200');
        formData.append('description', document.getElementById('car-modal-desc').value.trim());
        formData.append('features', JSON.stringify(['Apple CarPlay', 'GPS Navigation', 'Rearview Camera', 'Keyless Entry', 'Bluetooth']));

        const fileInput = document.getElementById('car-modal-image-file');
        if (fileInput && fileInput.files && fileInput.files[0]) {
            formData.append('main_image', fileInput.files[0]);
        }

        this.pendingGalleryFiles.forEach((item) => {
            formData.append('gallery_images', item.file);
            formData.append('gallery_view_types', item.viewType || 'OTHER');
            formData.append('gallery_captions', item.caption || '');
        });

        try {
            if (id) {
                await API.patch(`/admin/cars/${id}/`, formData);
                Toast.success('Vehicle details updated.');
            } else {
                await API.post('/admin/cars/', formData);
                Toast.success('New vehicle successfully added to fleet.');
            }
            this.closeCarModal();
            this.loadFleet();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    async updateCarStatus(carId, status) {
        try {
            await API.patch(`/admin/cars/${carId}/`, { status });
            Toast.success(`Vehicle status updated to ${status}.`);
        } catch (e) {
            Toast.error(e.message);
        }
    },

    async deleteCar(carId) {
        if (!confirm('Are you sure you want to remove this vehicle from the fleet?')) return;
        try {
            await API.delete(`/admin/cars/${carId}/`);
            Toast.success('Vehicle removed from fleet.');
            this.loadFleet();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    // Bookings Management
    async loadBookings(statusFilter = '') {
        const tbody = document.getElementById('admin-bookings-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const params = statusFilter ? { status: statusFilter } : {};
            const data = await API.get('/admin/bookings/', params);
            this.bookings = data.results || data;
            this.renderBookingsTable();
        } catch (e) {
            Toast.error('Could not load bookings.');
        }
    },

    renderBookingsTable() {
        const tbody = document.getElementById('admin-bookings-tbody');
        if (!tbody) return;

        tbody.innerHTML = this.bookings.map(b => `
            <tr>
                <td><span style="font-family:monospace; font-weight:700;">${b.booking_code}</span></td>
                <td>
                    <strong>${b.customer?.full_name || b.driver_name}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${b.driver_phone}</div>
                </td>
                <td>${b.car?.display_name || 'Vehicle'}</td>
                <td>${formatDate(b.start_date)} → ${formatDate(b.end_date)}</td>
                <td><strong>${formatCurrency(b.total_amount)}</strong></td>
                <td>
                    <select class="form-control" style="padding:4px 8px; font-size:0.8rem;" onchange="Admin.updateBookingStatus('${b.booking_code}', this.value)">
                        <option value="PENDING" ${b.status === 'PENDING' ? 'selected' : ''}>Pending</option>
                        <option value="CONFIRMED" ${b.status === 'CONFIRMED' ? 'selected' : ''}>Confirmed</option>
                        <option value="ONGOING" ${b.status === 'ONGOING' ? 'selected' : ''}>Ongoing</option>
                        <option value="COMPLETED" ${b.status === 'COMPLETED' ? 'selected' : ''}>Completed</option>
                        <option value="CANCELLED" ${b.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td><span class="badge ${b.payment_status === 'PAID' ? 'badge-success' : 'badge-warning'}">${b.payment_status}</span></td>
            </tr>
        `).join('');
    },

    async updateBookingStatus(code, status) {
        try {
            const booking = this.bookings.find(b => b.booking_code === code);
            if (booking) {
                await API.patch(`/admin/bookings/${booking.id}/`, { status });
                Toast.success(`Booking ${code} status updated to ${status}.`);
                this.loadBookings();
            }
        } catch (e) {
            Toast.error(e.message);
        }
    },

    // Customers Management
    async loadCustomers() {
        const tbody = document.getElementById('admin-customers-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const data = await API.get('/admin/customers/');
            this.customers = data.results || data;
            this.renderCustomersTable();
        } catch (e) {
            Toast.error('Could not load customer list.');
        }
    },

    renderCustomersTable() {
        const tbody = document.getElementById('admin-customers-tbody');
        if (!tbody) return;

        tbody.innerHTML = this.customers.map(c => `
            <tr>
                <td><strong>${c.full_name || c.username}</strong></td>
                <td>${c.email || 'N/A'}</td>
                <td>${c.phone_number || 'N/A'}</td>
                <td>${c.driver_license_number || 'N/A'}</td>
                <td><span class="badge badge-primary">${c.total_bookings || 0} Trips</span></td>
                <td><strong>${formatCurrency(c.total_spent || 0)}</strong></td>
                <td>
                    <button class="btn ${c.is_active ? 'btn-danger' : 'btn-success'} btn-sm" onclick="Admin.toggleCustomerStatus(${c.id})">
                        ${c.is_active ? 'Block' : 'Activate'}
                    </button>
                </td>
            </tr>
        `).join('');
    },

    async toggleCustomerStatus(id) {
        try {
            const res = await API.patch(`/admin/customers/${id}/toggle-status/`);
            Toast.success(res.detail);
            this.loadCustomers();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    // Payments Ledger
    async loadPayments() {
        const tbody = document.getElementById('admin-payments-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const data = await API.get('/admin/payments/');
            this.payments = data.results || data;
            this.renderPaymentsTable();
        } catch (e) {
            Toast.error('Could not load payments.');
        }
    },

    renderPaymentsTable() {
        const tbody = document.getElementById('admin-payments-tbody');
        if (!tbody) return;

        tbody.innerHTML = this.payments.map(p => `
            <tr>
                <td><span style="font-family:monospace; font-weight:700;">${p.transaction_id}</span></td>
                <td><span style="font-family:monospace;">${p.booking_code}</span></td>
                <td>${p.customer_name || 'Customer'}</td>
                <td><span class="badge badge-info">${p.provider}</span></td>
                <td><strong>${formatCurrency(p.amount)}</strong></td>
                <td><span class="badge ${p.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}">${p.status}</span></td>
                <td>${formatDateTime(p.created_at)}</td>
            </tr>
        `).join('');
    },

    // Reviews Moderation
    async loadReviews() {
        const tbody = document.getElementById('admin-reviews-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const data = await API.get('/admin/reviews/');
            this.reviews = data.results || data;
            this.renderReviewsTable();
        } catch (e) {
            Toast.error('Could not load reviews.');
        }
    },

    renderReviewsTable() {
        const tbody = document.getElementById('admin-reviews-tbody');
        if (!tbody) return;

        tbody.innerHTML = this.reviews.map(r => `
            <tr>
                <td><strong>${r.customer_name}</strong></td>
                <td>${r.car_name}</td>
                <td><span style="display:inline-flex; gap:2px; align-items:center;">${Array.from({length: 5}, (_, i) => `<i class="fa-solid fa-star" style="color:${i < r.rating ? '#f59e0b' : '#cbd5e1'}; font-size:0.75rem;"></i>`).join('')}</span> <span style="font-size:0.8rem; color:var(--text-muted); margin-left:4px;">(${r.rating}/5)</span></td>
                <td>
                    <strong>${r.title || ''}</strong>
                    <div style="font-size:0.8rem; color:var(--text-secondary); max-width:300px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${r.comment}</div>
                </td>
                <td><span class="badge ${r.is_approved ? 'badge-success' : 'badge-warning'}">${r.is_approved ? 'Approved' : 'Pending'}</span></td>
                <td>${formatDate(r.created_at)}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="Admin.toggleReviewApproval(${r.id}, ${!r.is_approved})">
                        ${r.is_approved ? 'Hide' : 'Approve'}
                    </button>
                </td>
            </tr>
        `).join('');
    },

    async toggleReviewApproval(id, approve) {
        try {
            await API.patch(`/admin/reviews/${id}/`, { is_approved: approve });
            Toast.success(`Review ${approve ? 'approved' : 'hidden'}.`);
            this.loadReviews();
        } catch (e) {
            Toast.error(e.message);
        }
    },

    // Coupons & Promos Management
    async loadCoupons() {
        const tbody = document.getElementById('admin-coupons-tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px;"><i class="fa-solid fa-spinner fa-spin text-gradient" style="font-size:2rem;"></i></td></tr>';

        try {
            const search = document.getElementById('coupon-search-input')?.value.trim() || '';
            const status = document.getElementById('coupon-status-filter')?.value || '';
            
            const params = {};
            if (search) params.search = search;
            if (status !== '') params.is_active = status;

            const data = await API.get('/admin/coupons/', params);
            this.coupons = data.results || data;
            this.renderCouponsTable();
        } catch (e) {
            Toast.error('Could not load coupons.');
        }
    },

    filterCoupons() {
        this.loadCoupons();
    },

    resetCouponFilters() {
        const searchInput = document.getElementById('coupon-search-input');
        if (searchInput) searchInput.value = '';
        const statusFilter = document.getElementById('coupon-status-filter');
        if (statusFilter) statusFilter.value = '';
        this.loadCoupons();
    },

    renderCouponsTable() {
        const tbody = document.getElementById('admin-coupons-tbody');
        if (!tbody) return;

        if (!this.coupons.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align:center; padding:40px 20px; color:var(--text-muted);">
                        <i class="fa-solid fa-tags" style="font-size:2rem; margin-bottom:8px; display:block; opacity:0.5;"></i>
                        No coupons found matching your search.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.coupons.map(c => {
            const isPercentage = c.discount_type === 'PERCENTAGE';
            const discountLabel = isPercentage
                ? `<span class="badge badge-primary" style="font-weight:700;"><i class="fa-solid fa-percent"></i> ${parseFloat(c.discount_value)}% OFF</span>`
                : `<span class="badge badge-info" style="font-weight:700;"><i class="fa-solid fa-tag"></i> ${formatCurrency(c.discount_value)} OFF</span>`;

            const minSpend = parseFloat(c.min_booking_amount) > 0 ? formatCurrency(c.min_booking_amount) : 'None';
            const maxCap = c.max_discount_amount && parseFloat(c.max_discount_amount) > 0 ? formatCurrency(c.max_discount_amount) : 'Unlimited';

            let validityText = 'No Expiry (Always Valid)';
            if (c.valid_from && c.valid_until) {
                validityText = `${formatDate(c.valid_from)} – ${formatDate(c.valid_until)}`;
            } else if (c.valid_until) {
                validityText = `Expires: ${formatDate(c.valid_until)}`;
            } else if (c.valid_from) {
                validityText = `From: ${formatDate(c.valid_from)}`;
            }

            const now = new Date();
            const isExpired = c.valid_until && new Date(c.valid_until) < now;
            let statusBadge = c.is_active
                ? `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Active</span>`
                : `<span class="badge badge-danger"><i class="fa-solid fa-circle-xmark"></i> Inactive</span>`;
            if (isExpired) {
                statusBadge = `<span class="badge" style="background:#64748b; color:#fff;"><i class="fa-solid fa-clock"></i> Expired</span>`;
            }

            return `
                <tr>
                    <td>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-family:monospace; font-weight:800; font-size:1rem; letter-spacing:0.5px; background:rgba(0,0,0,0.06); padding:4px 8px; border-radius:var(--radius-sm);">${c.code}</span>
                            <button type="button" class="btn btn-outline btn-sm" style="padding:2px 6px; font-size:0.7rem;" onclick="navigator.clipboard.writeText('${c.code}'); Toast.success('Copied coupon code ${c.code}!');" title="Copy code">
                                <i class="fa-regular fa-copy"></i>
                            </button>
                        </div>
                    </td>
                    <td>${discountLabel}</td>
                    <td>
                        <div style="font-size:0.85rem;"><strong>Min:</strong> ${minSpend}</div>
                        <div style="font-size:0.8rem; color:var(--text-secondary);"><strong>Cap:</strong> ${maxCap}</div>
                    </td>
                    <td>
                        <span style="font-size:0.85rem; color:${isExpired ? 'var(--danger)' : 'var(--text-primary)'};">${validityText}</span>
                    </td>
                    <td>
                        <span class="badge" style="background:#f1f5f9; color:var(--text-primary); font-weight:700; border:1px solid var(--border-color);">${c.usage_count || 0} Uses</span>
                    </td>
                    <td>${statusBadge}</td>
                    <td>
                        <div style="display:flex; gap:6px; align-items:center;">
                            <button class="btn btn-outline btn-sm" onclick="Admin.openCouponModal(${c.id})" title="Edit coupon settings">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn btn-sm ${c.is_active ? 'btn-outline' : 'btn-primary'}" onclick="Admin.toggleCouponStatus(${c.id}, ${!c.is_active})" title="${c.is_active ? 'Deactivate coupon' : 'Activate coupon'}">
                                <i class="fa-solid ${c.is_active ? 'fa-pause' : 'fa-play'}"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="Admin.deleteCoupon(${c.id}, '${c.code}')" title="Delete coupon">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    },

    onCouponTypeChange() {
        const type = document.getElementById('coupon-modal-type')?.value;
        const valLabel = document.getElementById('coupon-val-label');
        const capGroup = document.getElementById('coupon-cap-group');
        const valInput = document.getElementById('coupon-modal-value');

        if (type === 'PERCENTAGE') {
            if (valLabel) valLabel.innerText = 'Discount Percentage (%) *';
            if (valInput) {
                valInput.placeholder = '20';
                valInput.max = '100';
            }
            if (capGroup) capGroup.style.display = 'block';
        } else {
            if (valLabel) valLabel.innerText = 'Flat Discount Amount (₹) *';
            if (valInput) {
                valInput.placeholder = '500.00';
                valInput.removeAttribute('max');
            }
            if (capGroup) capGroup.style.display = 'none';
        }
    },

    openCouponModal(couponId = null) {
        const modal = document.getElementById('admin-coupon-modal');
        if (!modal) return;

        const form = document.getElementById('coupon-form');
        if (form) form.reset();

        document.getElementById('coupon-modal-id').value = '';
        document.getElementById('coupon-modal-title').innerText = 'Create Promo Coupon';
        document.getElementById('coupon-modal-code').disabled = false;
        document.getElementById('coupon-modal-active').checked = true;
        this.onCouponTypeChange();

        if (couponId) {
            const coupon = this.coupons.find(c => c.id === couponId);
            if (coupon) {
                document.getElementById('coupon-modal-id').value = coupon.id;
                document.getElementById('coupon-modal-title').innerText = `Edit Coupon: ${coupon.code}`;
                document.getElementById('coupon-modal-code').value = coupon.code;
                document.getElementById('coupon-modal-type').value = coupon.discount_type;
                this.onCouponTypeChange();

                document.getElementById('coupon-modal-value').value = coupon.discount_value;
                document.getElementById('coupon-modal-min').value = coupon.min_booking_amount || '0.00';
                document.getElementById('coupon-modal-cap').value = coupon.max_discount_amount || '';
                
                if (coupon.valid_from) {
                    const fromDate = new Date(coupon.valid_from);
                    document.getElementById('coupon-modal-from').value = fromDate.toISOString().slice(0, 16);
                }
                if (coupon.valid_until) {
                    const untilDate = new Date(coupon.valid_until);
                    document.getElementById('coupon-modal-until').value = untilDate.toISOString().slice(0, 16);
                }

                document.getElementById('coupon-modal-active').checked = Boolean(coupon.is_active);
            }
        }

        modal.classList.add('active');
    },

    closeCouponModal() {
        const modal = document.getElementById('admin-coupon-modal');
        if (modal) modal.classList.remove('active');
    },

    async saveCoupon() {
        const id = document.getElementById('coupon-modal-id')?.value;
        const code = document.getElementById('coupon-modal-code')?.value.trim().toUpperCase();
        const discount_type = document.getElementById('coupon-modal-type')?.value;
        const discount_value = document.getElementById('coupon-modal-value')?.value;
        const min_booking_amount = document.getElementById('coupon-modal-min')?.value || '0.00';
        const max_discount_amount = document.getElementById('coupon-modal-cap')?.value || null;
        const valid_from_val = document.getElementById('coupon-modal-from')?.value;
        const valid_until_val = document.getElementById('coupon-modal-until')?.value;
        const is_active = document.getElementById('coupon-modal-active')?.checked;

        if (!code || !discount_value) {
            Toast.error('Please enter coupon code and discount value.');
            return;
        }

        const payload = {
            code,
            discount_type,
            discount_value: parseFloat(discount_value),
            min_booking_amount: parseFloat(min_booking_amount) || 0.0,
            max_discount_amount: max_discount_amount ? parseFloat(max_discount_amount) : null,
            valid_from: valid_from_val ? new Date(valid_from_val).toISOString() : null,
            valid_until: valid_until_val ? new Date(valid_until_val).toISOString() : null,
            is_active: Boolean(is_active)
        };

        const saveBtn = document.getElementById('coupon-save-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
        }

        try {
            if (id) {
                await API.put(`/admin/coupons/${id}/`, payload);
                Toast.success(`Coupon ${code} updated successfully.`);
            } else {
                await API.post('/admin/coupons/', payload);
                Toast.success(`Coupon ${code} created successfully.`);
            }
            this.closeCouponModal();
            this.loadCoupons();
        } catch (err) {
            Toast.error(err.message || 'Failed to save coupon.');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Save Coupon';
            }
        }
    },

    async toggleCouponStatus(id, isActive) {
        try {
            await API.patch(`/admin/coupons/${id}/`, { is_active: isActive });
            Toast.success(`Coupon ${isActive ? 'activated' : 'deactivated'}.`);
            this.loadCoupons();
        } catch (e) {
            Toast.error(e.message || 'Could not update coupon status.');
        }
    },

    async deleteCoupon(id, code) {
        if (!confirm(`Are you sure you want to permanently delete coupon "${code}"?`)) return;

        try {
            await API.delete(`/admin/coupons/${id}/`);
            Toast.success(`Coupon ${code} deleted.`);
            this.loadCoupons();
        } catch (e) {
            Toast.error(e.message || 'Could not delete coupon.');
        }
    }
};
