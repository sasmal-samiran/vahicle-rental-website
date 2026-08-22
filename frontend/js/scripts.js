import { API } from './components/api.js';
import { Toast } from './components/toast.js';
import { Auth } from './components/auth.js';
import { Notifications } from './components/notifications.js';
import { Customer } from './components/customer.js';
import { BookingWizard } from './components/booking.js';
import { CustomerPortal } from './components/customer-portal.js';
import { Admin } from './components/admin.js';
import './components/app.js';

Object.assign(window, {
    API,
    Toast,
    Auth,
    Notifications,
    Customer,
    BookingWizard,
    CustomerPortal,
    Admin
});

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type="datetime-local"]').forEach(input => {
        input.addEventListener('click', () => {
            input.showPicker();
        });
    });
});