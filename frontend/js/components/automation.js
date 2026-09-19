// Webpage Automation Manager for AI Assistant & Interactive Triggers
import { Customer } from './customer.js';
import { Router } from './router.js';
import { BookingWizard } from './booking.js';
import { Auth } from './auth.js';
import { CustomerPortal } from './customer-portal.js';

export const Automation = {
    async execute(toolName, input = {}, output = '') {
        try {
            let parsedOutput = null;
            if (output && typeof output === 'string') {
                try { parsedOutput = JSON.parse(output); } catch (e) { }
            } else if (output && typeof output === 'object') {
                parsedOutput = output;
            }

            const cust = Customer || window.Customer;
            const router = Router || window.Router;
            const wizard = BookingWizard || window.BookingWizard;
            const auth = Auth || window.Auth;
            const portal = CustomerPortal || window.CustomerPortal;

            switch (toolName) {
                case 'show_car_details':
                case 'get_car_specs': {
                    let carId = input.car_id || input.carId || input.id || (parsedOutput && (parsedOutput.car_id || parsedOutput.id));
                    if (!carId && typeof output === 'string') {
                        const m = output.match(/ID:\s*(\d+)/i) || output.match(/car_id["':\s]+(\d+)/i);
                        if (m) carId = m[1];
                    }
                    if (carId && cust?.openDetailModal) {
                        cust.openDetailModal(Number(carId), 'ai_assistant');
                    }
                    break;
                }

                case 'open_booking_wizard': {
                    let carId = input.car_id || input.carId || input.id || (parsedOutput && (parsedOutput.car_id || parsedOutput.id));
                    if (!carId && typeof output === 'string') {
                        const m = output.match(/ID:\s*(\d+)/i) || output.match(/car_id["':\s]+(\d+)/i);
                        if (m) carId = m[1];
                    }
                    if (carId && wizard?.startBooking) {
                        wizard.startBooking(Number(carId));
                    }
                    break;
                }

                case 'show_fleet_cars':
                case 'resolve_booking_car':
                case 'search_cars': {
                    let candidateCars = null;
                    if (parsedOutput && Array.isArray(parsedOutput.candidate_cars)) {
                        candidateCars = parsedOutput.candidate_cars;
                    } else if (Array.isArray(parsedOutput)) {
                        candidateCars = parsedOutput;
                    } else if (parsedOutput && Array.isArray(parsedOutput.results)) {
                        candidateCars = parsedOutput.results;
                    } else if (parsedOutput && Array.isArray(parsedOutput.cars)) {
                        candidateCars = parsedOutput.cars;
                    }

                    const category = (input.category || input.category_name || (parsedOutput && parsedOutput.category) || '').toLowerCase().trim();
                    const brand = (input.brand || input.make || (parsedOutput && parsedOutput.brand) || '').trim();
                    const location = (input.location || input.pickup_location || input.city || (parsedOutput && (parsedOutput.location || parsedOutput.pickup_location)) || '').trim();
                    const query = (input.query || input.search || input.model || (parsedOutput && parsedOutput.model) || '').trim();
                    const minPrice = input.min_price !== undefined && input.min_price !== null ? Number(input.min_price) : (input.minPrice ? Number(input.minPrice) : null);
                    const maxPrice = input.max_price !== undefined && input.max_price !== null ? Number(input.max_price) : (input.maxPrice ? Number(input.maxPrice) : null);
                    const fuelType = (input.fuel_type || input.fuelType || '').toUpperCase().trim();
                    const transmission = (input.transmission || '').toUpperCase().trim();
                    const status = (input.status || '').toUpperCase().trim();
                    const seats = input.seats ? Number(input.seats) : null;
                    const searchTerm = [brand, query, location].filter(Boolean).join(' ').trim();

                    const filterPayload = {};
                    if (category) filterPayload.category = category;
                    if (searchTerm) filterPayload.search = searchTerm;
                    if (minPrice && !isNaN(minPrice)) filterPayload.min_price = minPrice;
                    if (maxPrice && !isNaN(maxPrice)) filterPayload.max_price = maxPrice;
                    if (fuelType) filterPayload.fuel_type = fuelType;
                    if (transmission) filterPayload.transmission = transmission;
                    if (seats) filterPayload.seats = seats;
                    if (status) filterPayload.status = status;

                    const params = new URLSearchParams();
                    Object.entries(filterPayload).forEach(([k, v]) => {
                        if (v !== null && v !== undefined && v !== '') params.set(k, v);
                    });
                    const queryStr = params.toString();
                    const targetUrl = `/fleet/${queryStr ? '?' + queryStr : ''}`;

                    const isFleetPage = !!document.getElementById('cars-grid-container') || 
                                        window.location.pathname.replace(/\/+$/, '').endsWith('/fleet');

                    // If not on the fleet page, dynamically navigate to /fleet/ without reloading the window
                    if (!isFleetPage) {
                        if (router?.navigate) {
                            await router.navigate(targetUrl);
                        } else {
                            window.location.href = targetUrl;
                            return;
                        }
                    } else if (queryStr) {
                        window.history.replaceState({}, document.title, targetUrl);
                    }

                    // On the fleet page: apply filter payload to Customer state & DOM controls
                    if (cust) {
                        cust.setFilters(filterPayload);
                        cust.currentPage = 1;

                        if (Array.isArray(candidateCars) && candidateCars.length > 0) {
                            cust.cars = candidateCars;
                            cust.totalCount = candidateCars.length;
                            cust.totalPages = Math.max(1, Math.ceil(candidateCars.length / (cust.pageSize || 9)));
                            cust.renderCars();
                            cust.updateResultsCountDisplay();
                            if (cust.updatePaginationUI) cust.updatePaginationUI();
                        } else {
                            cust.isFetching = false;
                            cust.fetchCars(1, false);
                        }

                        // Smooth scroll to catalog grid
                        const gridEl = document.getElementById('cars-grid-container') || document.getElementById('featured-cars-grid');
                        if (gridEl) {
                            gridEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }

                    // If single exact car returned in search, open its detail modal
                    if (Array.isArray(candidateCars) && candidateCars.length === 1 && candidateCars[0].id) {
                        if (cust?.openDetailModal) {
                            cust.openDetailModal(candidateCars[0].id, 'ai_assistant');
                        }
                    }
                    break;
                }

                case 'get_my_reservations': {
                    if (!document.getElementById('customer-portal-container')) {
                        if (router?.navigate) {
                            await router.navigate('/customer-portal/?tab=bookings');
                        } else {
                            window.location.href = '/customer-portal/?tab=bookings';
                            return;
                        }
                    }
                    if (portal) {
                        portal.switchTab('bookings');
                        document.getElementById('customer-portal-container')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                    break;
                }

                case 'open_login_modal': {
                    if (auth?.openAuthModal) {
                        auth.openAuthModal('password');
                    }
                    break;
                }
            }
        } catch (e) {
            console.warn('Webpage automation execution notice:', e);
        }
    }
};

export const executeWebpageAction = (toolName, input = {}, output = '') => {
    return Automation.execute(toolName, input, output);
};
