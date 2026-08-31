# 🚗 DriveLuxe | Next-Gen Online Vehicle Rental System

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.18-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud_DB-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Storage-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Swagger](https://img.shields.io/badge/OpenAPI-Swagger_UI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](http://127.0.0.1:8000/api/docs/)

**DriveLuxe** is a production-grade, full-stack vehicle rental platform built with **Django 6.1**, **Django REST Framework**, **PostgreSQL**, and **Supabase Cloud Storage**. It delivers a frictionless, digital-first car rental experience featuring instant OTP authentication, real-time date overlap availability, tiered insurance protection, multi-gateway payments, an admin business intelligence portal, and a complete customer management hub.

---

## ✨ Key Features

### 🔑 Authentication & Profile Management
* **Dual Sign-In Modes**: Instant 6-digit SMS/Email OTP login and standard password authentication.
* **Driver KYC & Document Verification**: Driving license capture, address validation, and profile picture management backed by private **Supabase Cloud Storage** with expiring signed URLs.
* **Security & Tokens**: Stateless JWT token authentication with automated session refresh.

### 🚘 Fleet Catalog & Real-Time Availability
* **Multi-Category Fleet**: Luxury Executive, Electric/Hybrid, Family 7-Seaters, Performance Coupes, Sedans, and Hatchbacks.
* **Date Overlap Engine**: Real-time vehicle availability querying across specific pickup/return hub locations.
* **Smart Search & Trending**: AI-curated recommendations, popular search telemetry, and multi-facet filtering (price range, transmission, fuel, seating capacity).

### 🛡️ Booking Wizard & Protection Tiers
* **5-Step Interactive Wizard**: Schedule selection &rarr; Add-ons &rarr; Driver details &rarr; Review & Promo &rarr; Confirmation.
* **Collision Damage Waiver (CDW)**:
  * **Basic Cover**: Statutory third-party liability (Included free).
  * **Standard CDW**: Capped ₹10,000 deductible + 50% glass/tire protection.
  * **Premium Zero-Liability**: ₹0 zero-deductible + 100% glass/tire shield + 24/7 priority rescue.
* **In-Cabin Add-ons**: GPS Navigation, ISOFIX Child Safety Seat, Additional Driver, and 4G LTE Hotspot.
* **Promo Code Engine**: Dynamic coupon validation (e.g., `DRIVE20` for 20% off, `WELCOME10`).
* **Digital Vouchers**: Instant printable confirmed booking vouchers with unique reference codes.

### 💳 Payment Gateways & Sandboxes
* **Razorpay**: Direct checkout modal with signature verification (UPI, Cards, Netbanking).
* **Stripe**: Credit/debit card payment intent flow.
* **1-Click Sandbox**: Built-in test sandbox payment provider for immediate test verifications.

### 📊 Portals & Legal Compliance Hub
* **Customer Portal** (`/customer-portal/`): Active reservations, past trip history, security deposit refund tracking, and profile editor.
* **Admin Command Center** (`/admin-portal/`): Business intelligence KPIs, revenue analytics, fleet status management, and booking workflows.
* **Legal Center** (`/terms/`, `/privacy/`, `/legal/`): Comprehensive CEO-standard Terms of Service, Privacy Policy (DPDP & GDPR compliant), and print-ready agreement.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.12+, Django 6.1, Django REST Framework, SimpleJWT |
| **API Docs** | DRF Spectacular (OpenAPI 3.0, Swagger UI, ReDoc) |
| **Database** | PostgreSQL (Production/Dev), SQLite fallback |
| **Cloud Storage** | Supabase Storage (Private S3 buckets for car fleet & profile avatars) |
| **Payments** | Razorpay, Stripe, Sandbox Emulator |
| **Frontend** | Vanilla JavaScript (Modular ES6 Components), Responsive CSS3, FontAwesome 6, Chart.js |

---

## 🚀 Quick Setup & Installation

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/sasmal-samiran/vahicle-rental-website.git
cd online_car_rental_system

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database Configuration (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7
JWT_AUTH_HEADER_TYPES=Bearer

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-or-anon-key
SUPABASE_CAR_BUCKET=car-images
SUPABASE_PROFILE_BUCKET=profile-images

# Payment Gateways (Optional / Demo)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key
```

### 4. Run Migrations & Seed Realistic Data
```bash
# Run migrations
python manage.py migrate

# Seed rich demo data (Vehicles, Hub Locations, Admin & Customers, Bookings)
python manage.py seed_data
```

### 5. Start Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

## 👥 Demo Accounts

| Role | Username | Phone | Password | Access Level |
| :--- | :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `9000000001` | `admin123` | Full Admin Dashboard & Fleet Operations |
| **Customer** | `rahul` | `9835754632` | `rahul123` | Customer Portal & Active Bookings |
| **Customer** | `priya` | `8567439521` | `priya123` | Customer Portal & Booking History |

> 💡 *Note: In development/demo mode, entering any phone number during OTP login shows a handy simulated verification code preview box.*

---

## 📌 Main Navigation Routes

* 🏠 **Customer Home**: [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/)
* 🚗 **Fleet Catalog**: [`http://127.0.0.1:8000/fleet/`](http://127.0.0.1:8000/fleet/)
* 👤 **Customer Portal**: [`http://127.0.0.1:8000/customer-portal/`](http://127.0.0.1:8000/customer-portal/)
* ⚡ **Admin Command Center**: [`http://127.0.0.1:8000/admin-portal/`](http://127.0.0.1:8000/admin-portal/)
* 📜 **Terms of Service**: [`http://127.0.0.1:8000/terms/`](http://127.0.0.1:8000/terms/)
* 🔒 **Privacy Policy**: [`http://127.0.0.1:8000/privacy/`](http://127.0.0.1:8000/privacy/)
* 📖 **Swagger API Docs**: [`http://127.0.0.1:8000/api/docs/`](http://127.0.0.1:8000/api/docs/)

---

## 🧪 Automated Testing

Run the test suite:
```bash
python manage.py test tests
```

---

## 📄 License & Ownership
Copyright &copy; 2026 **DriveLuxe Technologies Private Limited**. All rights reserved.
