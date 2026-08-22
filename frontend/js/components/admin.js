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

            // Populate Category and Location dropdowns in Car modal
            const catSelect = document.getElementById('car-modal-category');
            const locSelect = document.getElementById('car-modal-location');
            if (catSelect) {
                catSelect.innerHTML = this.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
            if (locSelect) {
                locSelect.innerHTML = this.locations.map(l => `<option value="${l.id}">${l.name} (${l.city})</option>`).join('');
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
        } catch (e) {
            console.error('Analytics error:', e);
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
                        label: 'Revenue ($)',
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
            if (this.categoryChart) this.categoryChart.destroy();
            const labels = chartsData.category_breakdown.map(c => c.name);
            const counts = chartsData.category_breakdown.map(c => c.vehicles);

            this.categoryChart = new Chart(catCtx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: ['#0e4d5c', '#d96b27', '#10b981', '#d97706', '#0284c7', '#64748b'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#4b5563', boxWidth: 12 } }
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
            this.renderFleetTable();
        } catch (e) {
            Toast.error('Could not load fleet.');
        }
    },

    renderFleetTable() {
        const tbody = document.getElementById('admin-fleet-tbody');
        if (!tbody) return;

        tbody.innerHTML = this.fleet.map(car => `
            <tr>
                <td>
                    <img src="${car.primary_image || car.main_image_url}" class="table-thumb" alt="${car.display_name}" />
                </td>
                <td>
                    <strong>${car.brand} ${car.model}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${car.year} • ${car.transmission}</div>
                </td>
                <td><span class="badge badge-primary">${car.category?.name || 'Standard'}</span></td>
                <td><span style="font-family:monospace; font-weight:700;">${car.license_plate}</span></td>
                <td>${car.location?.city || 'Hub'}</td>
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
                        <button class="btn btn-outline btn-sm" onclick="Admin.openEditCarModal(${car.id})"><i class="fa-solid fa-pen"></i></button>
                        <button class="btn btn-danger btn-sm" onclick="Admin.deleteCar(${car.id})"><i class="fa-solid fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    openAddCarModal() {
        document.getElementById('car-modal-id').value = '';
        document.getElementById('car-form').reset();
        document.getElementById('car-modal-title').innerText = 'Add New Vehicle to Fleet';
        document.getElementById('admin-car-modal').classList.add('active');
    },

    openEditCarModal(carId) {
        const car = this.fleet.find(c => c.id === carId);
        if (!car) return;

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
        document.getElementById('car-modal-image').value = car.main_image_url || '';
        document.getElementById('car-modal-desc').value = car.description || '';

        document.getElementById('car-modal-title').innerText = `Edit ${car.brand} ${car.model}`;
        document.getElementById('admin-car-modal').classList.add('active');
    },

    closeCarModal() {
        document.getElementById('admin-car-modal').classList.remove('active');
    },

    async saveCar() {
        const id = document.getElementById('car-modal-id').value;
        const data = {
            brand: document.getElementById('car-modal-brand').value.trim(),
            model: document.getElementById('car-modal-model').value.trim(),
            year: parseInt(document.getElementById('car-modal-year').value),
            license_plate: document.getElementById('car-modal-plate').value.trim(),
            price_per_day: parseFloat(document.getElementById('car-modal-price').value),
            security_deposit: parseFloat(document.getElementById('car-modal-deposit').value || 200),
            category_id: parseInt(document.getElementById('car-modal-category').value),
            location_id: parseInt(document.getElementById('car-modal-location').value),
            transmission: document.getElementById('car-modal-transmission').value,
            fuel_type: document.getElementById('car-modal-fuel').value,
            seats: parseInt(document.getElementById('car-modal-seats').value),
            power_hp: parseInt(document.getElementById('car-modal-hp').value || 200),
            main_image_url: document.getElementById('car-modal-image').value.trim(),
            description: document.getElementById('car-modal-desc').value.trim(),
            features: ['Apple CarPlay', 'GPS Navigation', 'Rearview Camera', 'Keyless Entry', 'Bluetooth']
        };

        try {
            if (id) {
                await API.patch(`/admin/cars/${id}/`, data);
                Toast.success('Vehicle details updated.');
            } else {
                await API.post('/admin/cars/', data);
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
                <td><span style="color:var(--warning);">${'★'.repeat(r.rating)}</span> (${r.rating}/5)</td>
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
    }
};
