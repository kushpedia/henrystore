# Architecture

This document describes the application structure, models, URL layout, middleware, and context processors.

---

## 1. Applications Overview

| App | Purpose |
|-----|--------|
| **core** | Storefront: home, product/category/vendor views, cart, checkout, orders, reviews, wishlist, search, contact |
| **userauths** | User authentication (email-based), registration, login, profile, password reset, email activation |
| **useradmin** | Vendor dashboard: products CRUD, variants, orders, reviews, shop page, settings |
| **payments** | M-Pesa integration: access token, STK push, callback, query status, check payment status |

**Note:** If the vendor dashboard (`/useradmin/`) is used, ensure `useradmin` is listed in `INSTALLED_APPS` in `ecomm/settings.py`.

---

## 2. Models

### 2.1 Core (`core.models`)

**Catalog**

| Model | Description |
|-------|-------------|
| `Category` | Top-level category (e.g. Electronics); has `subcategories` |
| `SubCategory` | Belongs to `Category`; has `mini_subcategories` |
| `MiniSubCategory` | Belongs to `SubCategory`; has `products` |
| `Vendor` | Store/seller; linked to `User`; has `product` set |
| `Color` | Color option (name, hex_code) for product variations |
| `Size` | Size option for product variations |
| `Product` | Belongs to `Vendor` and `MiniSubCategory`; title, image, description (rich text), price, old_price, tags, status, featured, digital, SKU, deal fields, `has_variations`, M2M to `Color`/`Size` |
| `ProductImages` | Extra images for a product |
| `ProductVariation` | Product + optional Color/Size; SKU, price, old_price, stock_count, image, is_active |

**Tracking & engagement**

| Model | Description |
|-------|-------------|
| `ProductView` | User + Product + viewed_on; used for recently viewed |
| `ProductReview` | User, Product, review text, rating (1–5), date |
| `wishlist_model` | User + Product + date |

**Cart & orders**

| Model | Description |
|-------|-------------|
| `CartOrder` | User, price, paid_status, order_date, product_status (processing/shipped/delivered), shipping/billing fields, coupons, tracking, oid, stripe_payment_intent, date |
| `CartOrderItems` | Order, product_id, variation (FK to ProductVariation), original_title, image, qty, price, total, color/size (display) |

**Other**

| Model | Description |
|-------|-------------|
| `Address` | User, mobile, address, status (default address) |
| `Coupon` | code, discount, active |

**Constants:** `STATUS_CHOICE` (order: processing/shipped/delivered), `STATUS` (product: draft/disabled/rejected/in_review/published), `RATING` (1–5 stars).

---

### 2.2 Userauths (`userauths.models`)

| Model | Description |
|-------|-------------|
| `User` | AbstractUser; email unique, `USERNAME_FIELD = "email"`, username, bio |
| `Profile` | OneToOne User; image, full_name, bio, phone, address, country, verified (created via signal on User save) |
| `ContactUs` | full_name, email, phone, subject, message |
| `LoginAttempt` | OneToOne User; attempts, lockout_until, last_attempt |

---

### 2.3 Payments (`payments.models`)

| Model | Description |
|-------|-------------|
| `Transaction` | order_id, amount, checkout_id, mpesa_code, phone_number, status (Pending/Processing/Success/Failed/Cancelled/Expired), result_code, result_desc, error_category, user_action, timestamps |

---

### 2.4 Useradmin (`useradmin.models`)

No custom models; uses `core` and `userauths` models (e.g. Product, Vendor, CartOrder).

---

## 3. URL Structure

**Root** (`ecomm/urls.py`): `admin/`, `''` → core, `users/` → userauths, `useradmin/` → useradmin, `ckeditor/`, `payments/` → payments. Static/media in DEBUG.

### 3.1 Core (namespace `core`)

| Path | Name | Purpose |
|------|------|--------|
| `/` | index | Home |
| `/products/` | product-list | Product list (with optional load-more) |
| `/product/<pid>/` | product-detail | Product detail |
| `/category/` | category-list | Category list |
| `/category/<cid>/` | category-product-list | Products by category |
| `/subcategory/<cid>/` | subcategory-products | Products by subcategory |
| `/minicategory/<cid>/` | minicategory-products | Products by mini-subcategory |
| `/vendors/` | vendor-list | Vendor list |
| `/vendor/<vid>/` | vendor-detail | Vendor detail |
| `/products/tag/<tag_slug>/` | tags | Products by tag |
| `/search/` | search | Search |
| `/filter-products/` | filter-product | Filter products (e.g. AJAX) |
| `/add-to-cart/` | add-to-cart | Add to cart |
| `/cart/` | cart | Cart page |
| `/delete-from-cart/` | delete-from-cart | Remove from cart |
| `/update-cart/` | update-cart | Update cart |
| `/new_checkout/<oid>/` | new_checkout | Checkout |
| `/payment-completed/<oid>/` | payment-completed | Payment success |
| `/payment-failed/` | payment-failed | Payment failure |
| `/dashboard/` | dashboard | Customer dashboard |
| `/dashboard/order/<id>` | order-detail | Order detail |
| `/make-default-address/` | make-default-address | Set default address |
| `/wishlist/` | wishlist | Wishlist |
| `/add-to-wishlist/` | add-to-wishlist | Add to wishlist |
| `/remove-from-wishlist/` | remove-from-wishlist | Remove from wishlist |
| `/contact/` | contact | Contact page |
| `/ajax-add-review/<pid>/` | ajax-add-review | Add product review |
| `/ajax-contact-form/` | ajax-contact-form | Contact form submit |
| `/save_checkout_info/` | save_checkout_info | Save checkout info |

### 3.2 Userauths (namespace `userauths`)

| Path | Name |
|------|------|
| `/users/sign-up/` | sign-up |
| `/users/sign-in/` | sign-in |
| `/users/sign-out/` | sign-out |
| `/users/profile/update/` | profile-update |
| `/users/activate/<uidb64>/<token>` | activate |
| `/users/forgot-password/` | forgot_password |
| `/users/reset-password/<uidb64>/<token>/` | reset_password |

### 3.3 Useradmin (namespace `useradmin`)

| Path | Name |
|------|------|
| `/useradmin/` | dashboard |
| `/useradmin/products/` | dashboard-products |
| `/useradmin/add-products/` | dashboard-add-products |
| `/useradmin/edit-products/<pid>/` | dashboard-edit-products |
| `/useradmin/delete-products/<pid>/` | dashboard-delete-products |
| `/useradmin/get-variation-options/` | get-variation-options |
| `/useradmin/orders/` | orders |
| `/useradmin/order_detail/<id>/` | order_detail |
| `/useradmin/change_order_status/<oid>/` | change_order_status |
| `/useradmin/shop_page/` | shop_page |
| `/useradmin/reviews/` | reviews |
| `/useradmin/settings/` | settings |
| `/useradmin/change_password/` | change_password |
| `/useradmin/get-subcategories/` | get_subcategories |
| `/useradmin/get-mini-subcategories/` | get_mini_subcategories |

### 3.4 Payments (namespace `mpesa`)

| Path | Name |
|------|------|
| `/payments/accesstoken/` | get_access_token |
| `/payments/initiate/` | initiate_stk_push |
| `/payments/query/` | query_stk_status |
| `/payments/callback/` | payment_callback |
| `/payments/check-status/<order_id>/` | check_payment_status |

---

## 4. Middleware

| Middleware | Order | Purpose |
|------------|--------|--------|
| SecurityMiddleware | 1 | Security headers |
| SessionMiddleware | 2 | Sessions |
| **RecentlyViewedMiddleware** (core) | 3 | On product-detail view, records ProductView for authenticated user (via `RecentViews.add_product_view`) |
| CommonMiddleware | 4 | Common handling |
| CsrfViewMiddleware | 5 | CSRF |
| AuthenticationMiddleware | 6 | request.user |
| MessageMiddleware | 7 | Messages |
| XFrameOptionsMiddleware | 8 | Clickjacking |

---

## 5. Context Processors

| Processor | Purpose |
|-----------|--------|
| `core.context_processor.default` | categories, vendors, new_products, deals_products, min_max_price, wishlist (if auth), address (if auth) |
| `core.context_processor.recently_viewed_products` | Recently viewed products for the current user |
| request | Built-in |
| auth | Built-in |
| messages | Built-in |

---

## 6. Key Conventions

- **IDs:** ShortUUID used for `pid`, `cid`, `vid`, `oid`, SKUs, etc.
- **Cart:** Session-based (`cart_data_obj`) for anonymous; order created at checkout.
- **Auth:** Email as login; custom user `userauths.User`.
- **Media:** Product/vendor images under `media/`; CKEditor uploads under `uploads/`.
- **Admin:** Jazzmin for Django admin; core models registered in `core.admin`.
