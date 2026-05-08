# Hop In – Campus Ride Sharing Made Simple

> Connecting college students with safe, affordable rides. Built for campus commuting.

## Why Hop In?

College students face a daily challenge: finding reliable transportation. Hop In solves this by creating a peer-to-peer ride-sharing network exclusively for verified college students. **No surge pricing. No corporate overhead. Just students helping students.**

### The Problem
- Students spend hours arranging rides
- Inconsistent pricing and availability
- Unsafe, unofficial arrangements
- Unused vehicle seats on campus

### Our Solution
A lightweight, secure platform where student drivers share their commute with fellow students—reducing costs, traffic, and environmental impact while building community.

---

## Core Features

- **Authentication:**
Custom user model with email login, Google OAuth via django-allauth, and college email verification.

- **Trip Management:**
Drivers create trips with location, direction, time, seats, and price. Smart ML-powered location suggestions if exact match not found. Real-time seat availability updates.

- **Intelligent Ride Discovery:**
Riders search and filter by location and direction. Drivers appear in alphabetical order. One-click booking with instant driver notifications.

- **Live Tracking & Route Optimization:**
Real-time location updates during rides with route geometry visualization. Haversine-based route matching ensures riders are within 2km of trip. Proportional pricing based on distance covered.

- **Secure Payments:**
Razorpay integration for encrypted transactions. Payment required before next booking. Auto-generated receipts.

- **Instant Notifications:**
Real-time AJAX polling for booking updates, ride status, and acceptance/rejection notifications.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2, PostgreSQL |
| **Frontend** | HTML5, CSS3, JavaScript, Tailwind |
| **Authentication** | Django-Allauth, Google OAuth |
| **Route Opt Algorithms** | Haversine distance, Route segmentation, Proximity matching |
| **Payments** | Razorpay |
| **Mapping** | OpenStreetMap, Leaflet |
| **Real-Time** | AJAX polling |
| **Deployment** | Gunicorn, Render |

---

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL
- Virtual environment (`venv` or `conda`)

### Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/hopin.git
cd hopin

# Create virtual environment
python -m venv hopin_env
source hopin_env/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure .env with DB URL, Google OAuth, Razorpay keys

# Start server
python manage.py runserver
```

Visit `http://localhost:8000`

---

## Project Structure

```
hopin/
├── hopin_app/              # Main application
│   ├── models.py           # User, Trip, RideRequest models
│   ├── views/              # View logic organized by feature
│   │   ├── authview.py     # Authentication
│   │   ├── driverview.py   # Driver features
│   │   ├── riderview.py    # Rider features
│   │   ├── trackingview.py # Location tracking
│   │   ├── profileview.py  # User profile management
│   │   └── locationview.py # Location services
│   ├── ml/
│   │   └── routeopt.py     # Route optimization & pricing
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, assets
├── hopin_config/           # Django settings & URLs
├── manage.py               # Django CLI
└── requirements.txt        # Dependencies
```

---

## How It Works

### For Drivers
1. Log in with college email
2. Create a trip (location, direction, time, seats, price)
3. View incoming ride requests
4. Track riders in real-time
5. Complete trip and confirm payment

### For Riders
1. Log in with college email
2. Browse available trips
3. Send booking request to driver
4. Wait for driver approval
5. Get picked up and tracked in real-time
6. Complete payment after ride

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hopin

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Razorpay
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```



## Performance & Safety

- **95%+ Reliability**: Ride booking and payment processing error rates < 5%
- **Data Security**: All sensitive data encrypted (SSL/TLS)
- **Privacy First**: Contact details hidden until booking confirmed
- **Responsive**: Search results in ~3 seconds, trip creation in ~2 seconds

---



