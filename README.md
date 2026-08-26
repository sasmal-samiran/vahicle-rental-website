# 🚗 DriveLuxe AI — Intelligent Vehicle Rental & Smart Fleet Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15%2B-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Swagger / OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](http://127.0.0.1:8000/api/docs/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**DriveLuxe AI** is a state-of-the-art, full-stack **AI-Powered Online Vehicle Rental & Fleet Operations Platform**. Engineered with **Django, Django REST Framework, PostgreSQL/SQLite**, and modern responsive web technologies, the platform blends robust end-to-end rental management with next-generation **Artificial Intelligence** capabilities — including AI smart recommendations, dynamic pricing algorithms, computer vision damage inspection, and predictive fleet optimization.

---

## 📑 Table of Contents

- [🤖 AI-Powered Capabilities & Smart Features](#-ai-powered-capabilities--smart-features)
- [🌟 Core Platform Features](#-core-platform-features)
  - [👤 Customer Experience](#-customer-experience)
  - [🛡️ Admin Operational Dashboard](#️-admin-operational-dashboard)
- [🏛️ System Architecture](#️-system-architecture)
- [💻 Tech Stack](#-tech-stack)
- [📂 Project Directory Structure](#-project-directory-structure)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [🔑 Demo Accounts & Test Credentials](#-demo-accounts--test-credentials)
- [🏷️ Promotional Discount Coupons](#️-promotional-discount-coupons)
- [📡 REST API Reference & Documentation](#-rest-api-reference--documentation)
- [🧪 Running Automated Tests](#-running-automated-tests)
- [🗺️ Future Roadmap](#️-future-roadmap)
- [📄 License](#-license)

---

## 🤖 AI-Powered Capabilities & Smart Features

```
                   ┌─────────────────────────────────────────┐
                   │        DriveLuxe AI Intelligence        │
                   └────────────────────┬────────────────────┘
                                        │
     ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
     ▼                  ▼                               ▼                  ▼
┌──────────────┐ ┌──────────────┐              ┌────────────────┐ ┌────────────────┐
│  Smart Fleet │ │  AI Dynamic  │              │ Computer Vision│ │   Predictive   │
│ Recommend-AI │ │  Pricing     │              │ Damage Scan    │ │   Maintenance  │
│  (Trip Match)│ │  (Yield Opt) │              │ (Pre/Post Trip)│ │ & Demand Pred  │
└──────────────┘ └──────────────┘              └────────────────┘ └────────────────┘
```

### 1. 🧠 AI Smart Fleet Recommendation Engine
* **Contextual Trip Matching**: Analyzes user intent (family road trip, executive business travel, weekend getaway, off-road adventure, eco-commute), budget constraints, and party size to automatically rank and recommend optimal vehicles.
* **Personalized Preference Learning**: Adapts to customer historical bookings, preferred transmission types, fuel preferences (Electric / Hybrid / Petrol), and amenity choices.

### 2. 📈 AI Dynamic Pricing & Yield Management
* **Real-Time Demand Sensing**: Intelligently adjusts daily rental rates based on multi-variable inputs:
  * Fleet hub capacity & real-time utilization rates
  * Seasonality and high-demand holiday weekends
  * Advance booking window (last-minute vs. early bird)
  * Local weather patterns and regional high-traffic events
* **Maximizes Fleet Revenue**: Balances high occupancy during low seasons while capturing maximum yield during peak demand spikes.

### 3. 🔍 Computer Vision Vehicle Damage Inspection
* **Pre- & Post-Rental Automated Audits**: Drivers upload 360° exterior photos during pickup and dropoff.
* **Anomaly & Dent Detection**: AI models segment and compare photo sets to detect newly introduced scratches, dents, paint chips, or windshield cracks, eliminating manual disputes and speeding up security deposit returns.

### 4. 💬 AI Conversational Rental Assistant & Copilot
* **Natural Language Search**: Enables intuitive search prompts like *"Find me a luxury 7-seater SUV in Downtown from Friday to Monday under ₹120/day"*.
* **24/7 Intelligent Virtual Concierge**: Answers policy inquiries, handles booking modifications, calculates instant quotes, and provides local driving recommendations.

### 5. 📊 Predictive Fleet Demand & Maintenance Forecasting
* **Predictive Fleet Telemetry**: Analyzes mileage increments, rental frequency, and driving wear-and-tear to proactively schedule maintenance before breakdowns occur.
* **Inter-Hub Fleet Rebalancing**: Forecasts geographic supply vs. demand mismatches between pickup and dropoff hubs, recommending proactive vehicle relocation routes.

### 6. 🛡️ AI Fraud & Driver Risk Assessment
* **Driver's License OCR & Verification**: Extracts and validates credentials directly from uploaded identification documents.
* **Risk Scoring**: Identifies anomalous booking patterns, suspicious payment profiles, or unauthorized driver mismatches.

---

## 🌟 Core Platform Features

### 👤 Customer Experience
* **⚡ Passwordless OTP & Dual-Auth**: Instant 6-digit SMS/Email OTP flow with auto-focus PIN navigation, cooldown timer, and standard password fallback.
* **📍 Multi-Hub Pickup & Dropoff Routing**: Select different pickup and return branches across regional locations.
* **⏱️ Real-Time Date-Overlap Availability**: High-concurrency booking engine prevents double-booking using mathematical window overlap queries (`start_date < requested_end AND end_date > requested_start`).
* **🔍 Multi-Faceted Fleet Search & Filter**:
  * Category chips (*Luxury, Electric, SUV, Sports, Sedan, Compact*) with live vehicle counts
  * Interactive price slider (₹40 to ₹350+/day)
  * Transmission (*Automatic, Manual*) and Fuel Type (*Electric, Hybrid, Petrol, Diesel*)
  * Seating capacity and horsepower sorting
* **📸 Car Detail Modal & Specs Sheet**: High-res multi-angle photo gallery, mechanical specs (horsepower, luggage capacity, engine, transmission), included amenities, and verified renter reviews.
* **🧙 Multi-Step Booking Wizard**:
  * **Step 1**: Protection tier selection (*Basic, Standard Damage Waiver, Zero-Deductible Full Comprehensive*) and add-on equipment (*GPS Navigation, Child Safety Seat, Additional Driver*).
  * **Step 2**: Primary driver credentials and driver's license entry.
  * **Step 3**: Real-time discount coupon validator (e.g. `DRIVE20`) with transparent fee breakdown (rental fees, taxes, security deposit, discounts).
  * **Step 4**: Secure checkout via **Razorpay**, **Stripe**, or **1-Click Sandbox Test Gateway**.
  * **Step 5**: Instant printable digital rental voucher with unique alphanumeric reference code (`CR-2026-XXXXXX`).
* **📱 Customer Dashboard**:
  * Live rental pipeline status tracker (`Reserved` ➔ `Confirmed` ➔ `Picked Up / Active` ➔ `Returned / Completed`)
  * Booking history and voucher retrieval
  * Self-service cancellation with automated refund processing
  * Post-rental verified review submission
  * Profile management & driver's license updates
* **🔔 In-App Live Notifications**: Real-time notification center with unread badge counter and instant mark-as-read actions.

---

### 🛡️ Admin Operational Dashboard (`/admin-portal/`)
* **📊 Real-Time Operations KPIs**: Live tracking of Net Paid Revenue, Total Bookings, Active On-Road Vehicles, Total Fleet Count, Fleet Utilization Rate (%), and Registered Customer Base.
* **📈 Interactive Chart.js Analytics**:
  * 6-Month Monthly Revenue vs. Booking Volume trends
  * Vehicle Category Distribution doughnut visualizer
* **🚘 Fleet Inventory Management**:
  * Create, edit, and archive vehicles with specs, daily pricing, security deposits, and photo galleries
  * Instant status switcher (`Available`, `Rented`, `In Maintenance`, `Inactive`)
* **📅 Booking Management & Lifecycle Pipeline**:
  * Filter reservations by status (`Pending`, `Confirmed`, `Ongoing`, `Completed`, `Cancelled`)
  * Full lifecycle actions: *Confirm Reservation* ➔ *Mark Picked Up (Start Rental)* ➔ *Mark Returned (Complete Rental)* ➔ *Cancel / Refund*
* **👥 Customer Directory**:
  * View customer profiles, contact info, total trips, lifetime spend, and account status toggles (`Active` / `Blocked`)
* **💳 Financial Ledger & Audit Trail**:
  * Complete transaction records, payment gateway reference IDs (Stripe, Razorpay, Sandbox), amounts, and payment statuses
* **⭐ Review Moderation Queue**:
  * Moderate, approve, or hide customer vehicle reviews before public display

---

## 🏛️ System Architecture

```
                                  ┌───────────────────────────────┐
                                  │      Client Applications      │
                                  │  (Customer Web / Admin Portal)│
                                  └───────────────┬───────────────┘
                                                  │ HTTPS / JSON
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │   Django REST Framework API   │
                                  │    (SimpleJWT, Cors, OpenAPI) │
                                  └───────────────┬───────────────┘
                                                  │
          ┌───────────────────────┼───────────────────────────────┼───────────────────────┐
          │                       │                               │                       │
          ▼                       ▼                               ▼                       ▼
┌───────────────────┐   ┌───────────────────┐           ┌───────────────────┐   ┌───────────────────┐
│   Core Modules    │   │  AI / ML Services │           │ Payment Gateways  │   │  Database Storage │
│ ───────────────── │   │ ───────────────── │           │ ───────────────── │   │ ───────────────── │
│ • Users & OTP     │   │ • Dynamic Pricing │           │ • Stripe API      │   │ • PostgreSQL /    │
│ • Fleet & Search  │   │ • Recommendation  │           │ • Razorpay API    │   │   SQLite DB       │
│ • Booking Wizard  │   │ • Computer Vision │           │ • 1-Click Sandbox │   │ • Media & Images  │
│ • Notifications   │   │ • Maintenance ML  │           │                   │   │                   │
└───────────────────┘   └───────────────────┘           └───────────────────┘   └───────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technologies Used |
|---|---|
| **Backend Framework** | [Python 3.10+](https://www.python.org/), [Django 5.0+](https://www.djangoproject.com/), [Django REST Framework 3.15+](https://www.django-rest-framework.org/) |
| **Authentication & Security** | [SimpleJWT (JSON Web Tokens)](https://django-rest-framework-simplejwt.readthedocs.io/), OTP Verification Service, CORS Headers |
| **API Documentation** | [DRF Spectacular (OpenAPI 3.0 / Swagger UI & Redoc)](https://drf-spectacular.readthedocs.io/) |
| **Database** | [PostgreSQL](https://www.postgresql.org/) (Production) / [SQLite3](https://www.sqlite.org/) (Zero-config local fallback) |
| **Frontend UI** | Modern Semantic HTML5, Custom Responsive CSS3 Variables & Tokens, ES6+ JavaScript, [FontAwesome 6](https://fontawesome.com/) |
| **Data Visualizations** | [Chart.js 4.x](https://www.chartjs.org/) for executive admin analytics |
| **Payments Integration** | [Stripe](https://stripe.com/), [Razorpay](https://razorpay.com/), and Built-in Mock Sandbox |
| **AI / ML Integration Layer** | Python AI services for dynamic pricing algorithms, recommendation heuristics, and CV inspection pipelines |

---

## 📂 Project Directory Structure

```
online_car_rental_system/
├── manage.py                          # Django management CLI script
├── requirements.txt                   # Project Python dependencies
├── .env.example                       # Environment variables template
├── car_rental_backend/                # Core Django project settings & routing
│   ├── settings.py                    # Django, DRF, JWT, Database & Media config
│   ├── urls.py                        # Master routing, Swagger docs & View templates
│   ├── wsgi.py                        # WSGI server entry point
│   └── asgi.py                        # ASGI asynchronous server entry point
├── apps/                              # Modular Django applications
│   ├── users/                         # Custom User, OTP auth service, profile & JWT endpoints
│   ├── vehicles/                      # Car, Category, Location, CarImage models & availability engine
│   ├── bookings/                      # Booking engine, Pricing service, Coupons, Addons & Lifecycle
│   ├── payments/                      # Stripe, Razorpay & Sandbox payment processing
│   ├── reviews/                       # Verified customer reviews & admin moderation
│   ├── notifications/                 # In-app notification dispatcher & user inbox
│   └── analytics/                     # Admin KPIs, revenue calculations & fleet utilization
├── frontend/                          # Single Page / Multi-view Frontend Assets
│   ├── base.html                      # Customer Marketplace & Booking layout
│   ├── fleet.html                     # Full Fleet Catalog page
│   ├── admin.html                     # Admin Operational Portal layout
│   ├── css/
│   │   ├── styles.css                 # Design tokens, typography, navigation, toast notifications
│   │   ├── customer.css               # Hero search, vehicle cards, booking modal wizard
│   │   └── admin.css                  # Admin layout, KPI widgets, data tables, chart containers
│   └── js/
│       ├── components/
│       │   ├── config.js              # API endpoints, formatting utilities, storage keys
│       │   ├── toast.js               # Floating toast alert notification system
│       │   ├── api.js                 # Unified Fetch client with JWT authorization interceptors
│       │   ├── auth.js                # OTP request, PIN input handling, login/register & session
│       │   ├── customer.js            # Fleet search, filter slider, availability checker, details modal
│       │   ├── booking.js             # 5-Step booking wizard, coupon validation, checkout handler
│       │   ├── customer-portal.js     # User booking management, live pipeline tracker, cancellation
│       │   ├── notifications.js       # Notification polling bell & unread counter
│       │   ├── admin.js               # Admin dashboard KPIs, Chart.js graphs, Fleet CRUD, booking actions
│       │   └── app.js                 # Global application initializer & event delegates
│       └── scripts.js
└── tests/                             # Comprehensive automated test suite
    └── test_rental_system.py          # API & workflow integration tests
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure you have the following installed on your machine:
* **Python**: `3.10` or higher ([Download Python](https://www.python.org/downloads/))
* **Git**: ([Download Git](https://git-scm.com/))
* **PostgreSQL** *(Optional — system defaults to SQLite if no PostgreSQL credentials are configured)*

---

### 2. Clone Repository & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/online_car_rental_system.git
cd online_car_rental_system

# Create a virtual environment
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the sample environment file to `.env`:

```bash
# On Windows (PowerShell):
copy .env.example .env

# On Linux/macOS:
cp .env.example .env
```

*(Optional)* Open `.env` in your text editor and update configuration keys for PostgreSQL, Stripe, or Razorpay if desired.

---

### 5. Run Migrations & Seed Sample Fleet Data

```bash
# Apply database migrations
python manage.py migrate

# Seed database with demo luxury/sports/electric fleet, categories, hubs, users, and coupons
python manage.py seed_data
```

---

### 6. Start the Development Server

```bash
python manage.py runserver 8000
```

Open your browser and navigate to:
* 🌐 **Customer Marketplace & Booking Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* 🚘 **Fleet Catalog**: [http://127.0.0.1:8000/fleet/](http://127.0.0.1:8000/fleet/)
* 🛡️ **Admin Operations Portal**: [http://127.0.0.1:8000/admin-portal/](http://127.0.0.1:8000/admin-portal/)
* 📚 **Interactive Swagger API Documentation**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
* 📖 **ReDoc API Documentation**: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
* ⚙️ **Django Standard Admin**: [http://127.0.0.1:8000/django-admin/](http://127.0.0.1:8000/django-admin/)

---

## 🔑 Demo Accounts & Test Credentials

| Role | Username / Phone Identifier | Password | Permitted Access |
|---|---|---|---|
| **System Admin** | `admin` / `+18005550199` | `admin123` | Full Admin Operations Dashboard, Fleet CRUD, Booking Pipeline |
| **Customer User 1** | `alex_morgan` / `+15551234567` | `user123` | Customer Marketplace, Booking Wizard, Reviews, Portal |
| **Customer User 2** | `sarah_j` / `+15559876543` | `user123` | Customer Marketplace, Booking Wizard, Portal |

> 💡 **Passwordless OTP Testing**: When requesting an OTP login, the secure 6-digit code is automatically printed to your running server terminal and rendered in the demo pill on the modal for instant, frictionless local testing.

---

## 🏷️ Promotional Discount Coupons

Test the checkout pricing engine using these pre-seeded coupon codes:

| Coupon Code | Discount Type | Value | Minimum Spend | Description |
|---|---|---|---|---|
| **`DRIVE20`** | Percentage | **20% OFF** | ₹50.00 | 20% discount on total rental amount |
| **`WELCOME10`** | Percentage | **10% OFF** | ₹0.00 | First-time renter welcome discount |
| **`WEEKEND50`** | Fixed Amount | **₹50.00 OFF** | ₹200.00 | Flat ₹50 discount on premium/weekend trips |

---

## 📡 REST API Reference & Documentation

The system includes a fully documented OpenAPI 3.0 schema accessible via Swagger UI at `/api/docs/`.

### Key API Endpoints Summary

| Module | HTTP Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/auth/otp/request/` | Request 6-digit login/register OTP |
| **Auth** | `POST` | `/api/auth/otp/verify/` | Verify OTP and obtain JWT tokens |
| **Auth** | `POST` | `/api/auth/login/` | Password-based JWT authentication |
| **Auth** | `GET` / `PUT` | `/api/auth/profile/` | Retrieve / update authenticated user profile |
| **Vehicles** | `GET` | `/api/vehicles/cars/` | List and search cars (category, fuel, price, availability) |
| **Vehicles** | `GET` | `/api/vehicles/cars/{id}/` | Detailed car specs, images & verified reviews |
| **Vehicles** | `GET` | `/api/vehicles/categories/` | List vehicle categories with fleet counts |
| **Vehicles** | `GET` | `/api/vehicles/locations/` | List rental pickup and dropoff hubs |
| **Vehicles** | `GET` | `/api/vehicles/available/` | Check date-overlap vehicle availability |
| **Bookings** | `POST` | `/api/bookings/calculate/` | Live pricing calculator (rates, protection, coupon, tax) |
| **Bookings** | `GET` / `POST`| `/api/bookings/` | List user bookings or create a new reservation |
| **Bookings** | `POST` | `/api/bookings/{id}/cancel/`| Cancel booking and initiate refund calculation |
| **Payments** | `POST` | `/api/payments/create-intent/` | Initialize Stripe / Razorpay / Sandbox transaction |
| **Payments** | `POST` | `/api/payments/verify/` | Verify payment signature and confirm booking |
| **Reviews** | `GET` / `POST`| `/api/reviews/` | List approved reviews or submit post-rental review |
| **Notifications**| `GET` | `/api/notifications/` | Fetch user notifications with unread count |
| **Analytics** | `GET` | `/api/analytics/admin-kpi/` | Admin KPIs (Revenue, fleet utilization, bookings) |
| **Analytics** | `GET` | `/api/analytics/revenue-chart/`| 6-Month revenue & booking time-series data |

---

## 🧪 Running Automated Tests

Run the full automated test suite covering authentication, vehicle availability queries, booking price calculations, and admin workflows:

```bash
# Run tests via Django test runner
python manage.py test tests
```

---

## 🗺️ Future Roadmap

- [ ] **AI-Powered Mobile Application**: Native iOS & Android application with offline keyless entry.
- [ ] **Connected Telemetry (IoT)**: Real-time GPS tracking, remote lock/unlock, battery/fuel telemetry via OBD-II integration.
- [ ] **Multimodal Gemini AI Voice Booking**: Book cars via conversational voice prompts directly in-app.
- [ ] **Automated Toll & Fuel Settlement**: Dynamic billing for highway tolls and fuel difference upon return.

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).

---

<p align="center">
  <b>Built with ❤️ for modern mobility and AI-driven car rental operations.</b>
</p>
