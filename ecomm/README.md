# E-Commerce Platform (Kstores)

A **multi-vendor e-commerce platform** built with Django. Sellers can list products and manage their shops; customers browse, cart, checkout, and pay via **M-Pesa** (Kenya). The project includes a three-level category hierarchy, product variations (color/size), reviews, wishlists, and a vendor dashboard.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Configuration](#configuration)
- [License](#license)

---

## Features

| Area | Description |
|------|-------------|
| **Storefront** | Home, product list/detail, category/subcategory/mini-category browsing, search, filter, tag-based listing, vendor list/detail |
| **Catalog** | Categories → Subcategories → Mini-subcategories; products with images, rich text, tags, specs, SKU, deals, featured |
| **Product variations** | Color and size options with per-variation price, stock, and images |
| **Cart & checkout** | Session-based cart, add/update/remove, checkout with saved address, order creation |
| **Orders** | Order history, order detail, status flow: Processing → Shipped → Delivered |
| **Payments** | M-Pesa STK Push, callback handling, transaction status and error tracking |
| **User accounts** | Email-based auth, sign up, sign in, sign out, profile, forgot/reset password, email activation |
| **Vendor dashboard** | Product CRUD, variant management, orders, reviews, shop page, settings, change password |
| **Engagement** | Product reviews and star ratings, wishlist, recently viewed products (middleware + context) |
| **Admin** | Django admin with Jazzmin theme; full management of categories, products, vendors, orders, etc. |

---

## Tech Stack

- **Backend:** Django 5.2
- **Database:** PostgreSQL
- **Auth:** Custom user model (email as `USERNAME_FIELD`)
- **Admin:** Django Admin + Jazzmin
- **Rich text:** django-ckeditor
- **Tags:** django-taggit
- **IDs:** shortuuid
- **Payments:** M-Pesa (STK Push, callbacks)
- **Email:** SMTP (e.g. Gmail)
- **Env:** environs + python-dotenv
- **Deployment:** gunicorn (in requirements)

---

## Project Structure

```
ecomm/
├── ecomm/                 # Project settings & root URLs
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                   # Storefront, catalog, cart, orders, reviews, wishlist
│   ├── models.py           # Category, Product, Vendor, Cart, Order, Review, etc.
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── context_processor.py
│   ├── middleware.py       # Recently viewed products
│   └── ...
├── userauths/              # User auth & profile
│   ├── models.py           # User, Profile, ContactUs, LoginAttempt
│   ├── views.py
│   └── urls.py
├── useradmin/              # Vendor dashboard (products, orders, reviews, shop)
│   ├── views.py
│   ├── urls.py
│   └── ...
├── payments/               # M-Pesa integration
│   ├── models.py           # Transaction
│   ├── views.py            # STK push, callback, query, check status
│   └── urls.py
├── templates/              # Global templates
│   ├── partials/
│   ├── core/
│   ├── userauths/
│   └── useradmin/
├── static/                 # CSS, JS, images
├── media/                  # User uploads (product images, etc.)
├── manage.py
└── requirements.txt
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for apps, models, and URL reference.

---

## Quick Start

1. **Clone and create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Environment variables**  
   Create a `.env` in the project root (see [docs/SETUP.md](docs/SETUP.md)):
   - `EMAIL_ID`, `EMAIL_PASSWORD` (SMTP)
   - `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASS_KEY`

3. **Database**
   - Create PostgreSQL database `ecoms_db` (or match name in `settings.py`).
   - Update `DATABASES` in `ecomm/settings.py` if needed (user, password, host, port).

4. **Django setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

5. **Optional:** Add sample data via management commands (e.g. `add_sample_variations` if present).

Full steps, env vars, and troubleshooting: [docs/SETUP.md](docs/SETUP.md).

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/BRD.md](docs/BRD.md) | **Business Requirements Document (BRD)** — objectives, scope, stakeholders, functional/non-functional requirements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Apps, models, URLs, middleware, context processors |
| [docs/SETUP.md](docs/SETUP.md) | Installation, environment, database, running the app |
| [docs/ROUTES.md](docs/ROUTES.md) | URL route reference (storefront, auth, dashboard, payments) |

---

## Configuration

- **Time zone:** `Africa/Nairobi`
- **Custom user:** `AUTH_USER_MODEL = 'userauths.User'`
- **Login URL:** `userauths:sign-in`
- **Static:** `STATIC_URL`, `STATIC_ROOT`, `STATICFILES_DIRS`
- **Media:** `MEDIA_URL`, `MEDIA_ROOT`
- **CKEditor uploads:** `CKEDITOR_UPLOAD_PATH = "uploads/"`

For production: set `DEBUG = False`, configure `ALLOWED_HOSTS`, `SECRET_KEY`, and static/media serving (e.g. WhiteNoise, CDN, reverse proxy).

---

## License

Proprietary / All rights reserved (adjust as needed).
