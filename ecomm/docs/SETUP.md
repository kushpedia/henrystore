# Setup Guide

This guide covers environment setup, database configuration, and running the E-Commerce Platform.

---

## 1. Prerequisites

- **Python** 3.10+ (project uses Django 5.2)
- **PostgreSQL** (database)
- **pip** and **venv** (or virtualenv)

---

## 2. Repository and Virtual Environment

```bash
# Clone or navigate to project root
cd d:\ecommerce\ecomm

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Environment Variables

Create a `.env` file in the project root (same folder as `manage.py`). Do not commit this file.

### 3.1 Required for core functionality

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_ID` | SMTP login (e.g. Gmail) | your-email@gmail.com |
| `EMAIL_PASSWORD` | SMTP password or app password | your-app-password |

Used for: sign-up activation, forgot/reset password, and any other transactional email.

### 3.2 Required for M-Pesa (payments)

| Variable | Description |
|----------|-------------|
| `MPESA_CONSUMER_KEY` | M-Pesa API consumer key |
| `MPESA_CONSUMER_SECRET` | M-Pesa API consumer secret |
| `MPESA_PASS_KEY` | M-Pesa passkey (Lipa Na M-Pesa) |

The app reads these via `environs` in `ecomm/settings.py`. Without them, payment-related views will fail when initiating or checking M-Pesa.

### 3.3 Example `.env`

```env
EMAIL_ID=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_PASS_KEY=your-passkey
```

---

## 4. Database

### 4.1 Create PostgreSQL database

```sql
CREATE DATABASE ecoms_db;
```

(Or use another name and update `settings.py` accordingly.)

### 4.2 Configure Django

In `ecomm/settings.py`, the default database block is:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': "ecoms_db",
        'USER': "postgres",
        'PASSWORD': "your-password",
        'HOST': "localhost",
        'PORT': 5432,
    }
}
```

Update `USER`, `PASSWORD`, and optionally `HOST`/`PORT`/`NAME` to match your environment. For production, use environment variables instead of hardcoding credentials.

### 4.3 Migrations

```bash
python manage.py migrate
```

Run from the project root so `manage.py` and `ecomm/settings.py` are found.

---

## 5. Static and Media Files

- **Static:** Collected to `staticfiles/` with `python manage.py collectstatic` (for production). Development uses `STATICFILES_DIRS` (e.g. `static/`).
- **Media:** User uploads (product images, etc.) go to `media/` as set by `MEDIA_ROOT`. Ensure the app has write permission to this directory.

No extra steps are required for local development if `DEBUG=True` and static/media are served as in the default `ecomm/urls.py`.

---

## 6. Create Superuser (optional)

```bash
python manage.py createsuperuser
```

Use this account to access Django admin at `/admin/` and to create categories, products, and vendors if needed.

---

## 7. Run the Application

```bash
python manage.py runserver
```

Default URL: **http://127.0.0.1:8000/**

- **Home:** `/`
- **Admin:** `/admin/`
- **Sign in:** `/users/sign-in/`
- **Vendor dashboard:** `/useradmin/` (requires vendor/user setup)

---

## 8. Vendor Dashboard (useradmin)

The vendor dashboard is mounted at `/useradmin/`. If you get import or 404 errors for those URLs, ensure `useradmin` is in `INSTALLED_APPS` in `ecomm/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'core',
    'userauths',
    'payments',
    'useradmin',  # add if missing
]
```

Then run migrations again if needed:

```bash
python manage.py migrate
```

---

## 9. Optional: Sample Data

- **Categories / products:** Create them via Django admin or custom management commands (e.g. `core.management.commands.add_sample_variations`).
- **Vendor:** Link a user to a `Vendor` in admin so that user can use the vendor dashboard.

---

## 10. Production Checklist

- Set `DEBUG = False`.
- Set `SECRET_KEY` from environment; do not commit it.
- Set `ALLOWED_HOSTS` to your domain(s).
- Use a dedicated database user with limited privileges.
- Serve static files (e.g. WhiteNoise or reverse proxy) and configure media serving (e.g. Nginx/Apache or object storage).
- Use HTTPS and set `SECURE_*` and `SESSION_*` settings as per Django security docs.
- Restrict `MPESA_*` and `EMAIL_*` to server environment only.

---

## 11. Troubleshooting

| Issue | Suggestion |
|-------|------------|
| `ModuleNotFoundError: useradmin` or 404 on `/useradmin/` | Add `useradmin` to `INSTALLED_APPS` and ensure `path("useradmin/", include("useradmin.urls"))` is in `ecomm/urls.py`. |
| Database connection error | Check PostgreSQL is running, and that `NAME`, `USER`, `PASSWORD`, `HOST`, `PORT` in `DATABASES` are correct. |
| Env vars not found | Ensure `.env` is in the project root and that `env.read_env()` is called in `settings.py` (e.g. via `environs`). |
| M-Pesa errors | Verify `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASS_KEY` and that the callback URL is reachable (e.g. ngrok for local testing). |
| Email not sending | Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and that less-secure/app password is used if required (e.g. Gmail). |

For URL and app structure, see [ARCHITECTURE.md](ARCHITECTURE.md). For a quick route list, see [ROUTES.md](ROUTES.md).
