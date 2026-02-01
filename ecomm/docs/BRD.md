# Business Requirements Document (BRD)

## E-Commerce Platform (KStores) — Multi-Vendor Marketplace

---

## Document Control

| Attribute | Value |
|-----------|--------|
| **Document Title** | Business Requirements Document — E-Commerce Platform (KStores) |
| **Version** | 1.0 |
| **Status** | Approved / Draft |
| **Date** | 2025-02-01 |
| **Author** | [Author Name] |
| **Reviewed By** | [Reviewer Name] |
| **Approved By** | [Approver Name] |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-02-01 | — | Initial BRD |

---

## 1. Executive Summary

This Business Requirements Document (BRD) defines the business and functional requirements for the **E-Commerce Platform (KStores)** — a multi-vendor online marketplace. The system enables multiple vendors (sellers) to list and manage products while customers browse, add to cart, checkout, and pay via **M-Pesa** (Kenya). The platform supports a three-level category hierarchy (Category → Subcategory → Mini-subcategory), product variations (color/size), reviews and ratings, wishlists, recently viewed products, and a dedicated vendor dashboard for sellers. The BRD serves as the single source of truth for business and high-level functional requirements to guide development, testing, and acceptance.

---

## 2. Business Objectives

| ID | Objective | Description |
|----|-----------|-------------|
| BO-1 | Multi-vendor marketplace | Enable multiple sellers (vendors) to list and sell products on a single platform. |
| BO-2 | Customer acquisition & conversion | Provide a clear storefront (browse, search, filter, product detail) and seamless cart/checkout to increase sales. |
| BO-3 | Local payment integration | Support M-Pesa (Kenya) for payment initiation, callback handling, and transaction status tracking. |
| BO-4 | Vendor self-service | Give vendors a dashboard to manage products, variants, orders, reviews, and shop settings without admin intervention. |
| BO-5 | Trust & engagement | Build trust through product reviews/ratings, vendor profiles, and engagement features (wishlist, recently viewed). |
| BO-6 | Operational control | Allow platform administrators to manage categories, products, vendors, and orders via Django admin. |

---

## 3. Scope

### 3.1 In Scope

- **Storefront:** Home, product list/detail, category/subcategory/mini-category browsing, search, filter, tag-based listing, vendor list/detail.
- **Catalog:** Three-level category hierarchy; product attributes (title, images, rich text description, price, old price, tags, specs, SKU, deals, featured); product variations (color/size) with per-variation price and stock.
- **Cart & checkout:** Session-based cart; add/update/remove items; checkout with saved/default address; order creation.
- **Orders:** Order history and order detail; order status flow (Processing → Shipped → Delivered).
- **Payments:** M-Pesa STK Push initiation, callback handling, transaction status query, and payment status check per order.
- **User accounts:** Email-based registration and login; profile; forgot/reset password; email activation.
- **Vendor dashboard:** Product CRUD; variant management; order list and detail; order status change; reviews; shop page; settings; change password.
- **Engagement:** Product reviews and star ratings; wishlist; recently viewed products (tracked via middleware).
- **Administration:** Django admin (Jazzmin) for categories, subcategories, mini-subcategories, products, vendors, orders, coupons, addresses, reviews, and related data.

### 3.2 Out of Scope

- Other payment methods (e.g. card, PayPal) beyond existing codebase references — not part of current BRD scope unless explicitly added later.
- Multi-currency or multi-language storefront (future enhancements).
- Native mobile apps (current scope is web application).
- Advanced analytics/reporting dashboards (beyond basic admin and vendor dashboard).
- Automated inventory replenishment or supplier integration.
- Marketplace commission/fee calculation and vendor payouts (business logic not defined in current system).

---

## 4. Stakeholders

| Role | Responsibility |
|------|----------------|
| **Platform owner / Sponsor** | Overall product vision, approval of scope and priorities. |
| **Administrator** | Manages categories, products, vendors, and platform configuration via Django admin. |
| **Vendor (Seller)** | Lists products, manages variants and orders, responds to reviews, maintains shop page and settings. |
| **Customer (Buyer)** | Browses catalog, adds to cart, checks out, pays via M-Pesa, views orders and profile. |
| **Development team** | Implements and maintains the system per this BRD and technical design. |
| **QA / UAT** | Validates functionality against this BRD and acceptance criteria. |

---

## 5. User Types and Personas

| User Type | Description | Primary Goals |
|-----------|-------------|---------------|
| **Guest** | Unauthenticated visitor. | Browse products, categories, vendors; view product details; add to cart (session). Checkout may require sign-in. |
| **Customer** | Registered user (email-based). | Sign in/out; manage profile; wishlist; recently viewed; cart; checkout; view order history and order detail; submit reviews. |
| **Vendor** | User linked to a Vendor (store). | Manage products (add/edit/delete); manage variants; view/update orders; view reviews; manage shop page; change password and settings. |
| **Administrator** | Staff/superuser. | Full access to Django admin: categories, subcategories, mini-subcategories, products, vendors, orders, coupons, users, transactions, and related entities. |

---

## 6. Functional Requirements

### 6.1 Storefront & Catalog

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-S1 | The system shall display a home page with categories, vendors, new products, and deals. | Must |
| FR-S2 | The system shall allow browsing products by category, subcategory, and mini-subcategory. | Must |
| FR-S3 | The system shall display product list with pagination/load-more. | Must |
| FR-S4 | The system shall display product detail including title, images, description, price, old price, specs, tags, and variation options (color/size) where applicable. | Must |
| FR-S5 | The system shall support product search and filter (e.g. price range, category). | Must |
| FR-S6 | The system shall support tag-based product listing. | Should |
| FR-S7 | The system shall list vendors and display vendor detail (profile, products, ratings). | Must |
| FR-S8 | The system shall display product variations (color/size) with per-variation price and stock where configured. | Must |

### 6.2 Cart & Checkout

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-C1 | The system shall allow adding products (and selected variation) to cart; cart may be session-based for guests. | Must |
| FR-C2 | The system shall allow updating quantity and removing items from cart. | Must |
| FR-C3 | The system shall provide a checkout flow that collects/uses shipping and billing information. | Must |
| FR-C4 | The system shall support saving and selecting a default address for logged-in users. | Should |
| FR-C5 | The system shall create an order (CartOrder and CartOrderItems) upon successful checkout. | Must |
| FR-C6 | The system shall support application of coupons (discount) where configured. | Should |

### 6.3 Orders

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-O1 | The system shall display order history for the logged-in customer. | Must |
| FR-O2 | The system shall display order detail (items, totals, status, tracking if present). | Must |
| FR-O3 | The system shall support order status values: Processing, Shipped, Delivered. | Must |
| FR-O4 | Vendors shall be able to view orders (relevant to their products) and update order status. | Must |

### 6.4 Payments (M-Pesa)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-P1 | The system shall initiate M-Pesa STK Push for payment using order amount and customer phone number. | Must |
| FR-P2 | The system shall accept and process M-Pesa callback to update transaction and order payment status. | Must |
| FR-P3 | The system shall support querying transaction status (e.g. pending, success, failed). | Must |
| FR-P4 | The system shall record transaction details (checkout_id, mpesa_code, status, error details where applicable). | Must |
| FR-P5 | The system shall direct the user to payment-completed or payment-failed page based on outcome. | Must |

### 6.5 User Authentication & Profile

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-A1 | The system shall allow registration using email (and required fields); email shall be the unique login identifier. | Must |
| FR-A2 | The system shall support email activation (e.g. link with token) for new accounts. | Should |
| FR-A3 | The system shall allow sign-in and sign-out. | Must |
| FR-A4 | The system shall support forgot-password and reset-password via email. | Should |
| FR-A5 | The system shall allow the user to update profile (e.g. image, full name, bio, phone, address, country). | Must |
| FR-A6 | The system shall create a Profile (one-to-one with User) upon user creation. | Must |

### 6.6 Vendor Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-V1 | The system shall provide a vendor dashboard accessible to users linked to a Vendor. | Must |
| FR-V2 | Vendors shall be able to add, edit, and delete products (with category/subcategory/mini-subcategory selection). | Must |
| FR-V3 | Vendors shall be able to manage product variations (color/size, price, stock, image). | Must |
| FR-V4 | Vendors shall be able to view orders and update order status. | Must |
| FR-V5 | Vendors shall be able to view product reviews. | Must |
| FR-V6 | Vendors shall be able to manage shop page and account settings (including change password). | Should |
| FR-V7 | The system shall support AJAX loading of subcategories and mini-subcategories based on parent selection. | Should |

### 6.7 Engagement & Trust

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-E1 | The system shall allow logged-in users to submit product reviews with a star rating (1–5). | Must |
| FR-E2 | The system shall display product reviews and aggregate rating on product detail. | Must |
| FR-E3 | The system shall allow users to add/remove products from a wishlist. | Should |
| FR-E4 | The system shall track recently viewed products for logged-in users and display them (e.g. on home or sidebar). | Should |
| FR-E5 | The system shall provide a contact form and store/process contact submissions. | Should |

### 6.8 Administration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AD1 | The system shall provide an admin interface (Django admin with Jazzmin) for platform administrators. | Must |
| FR-AD2 | Administrators shall be able to manage categories, subcategories, and mini-subcategories. | Must |
| FR-AD3 | Administrators shall be able to manage products, product images, and product variations. | Must |
| FR-AD4 | Administrators shall be able to manage vendors and link them to users. | Must |
| FR-AD5 | Administrators shall be able to view and manage orders, coupons, addresses, and transactions. | Must |
| FR-AD6 | Administrators shall be able to manage users, profiles, and contact submissions. | Should |

---

## 7. Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-1 | The system shall use HTTPS in production. | Security |
| NFR-2 | Passwords shall be hashed and validated per Django password validators. | Security |
| NFR-3 | The system shall protect against CSRF and use secure session handling. | Security |
| NFR-4 | Sensitive configuration (e.g. SECRET_KEY, DB password, M-Pesa credentials) shall be externalized (e.g. environment variables). | Security |
| NFR-5 | The system shall support deployment behind a production WSGI server (e.g. Gunicorn). | Performance / Deployment |
| NFR-6 | Static and media files shall be configurable for CDN or dedicated serving in production. | Performance |
| NFR-7 | The system shall use a relational database (PostgreSQL) for persistence. | Data |
| NFR-8 | The system shall use a standard time zone (e.g. Africa/Nairobi) for order and transaction timestamps. | Compliance / Localization |
| NFR-9 | The system shall support logging (e.g. Django logging to file/console) for troubleshooting. | Operability |

---

## 8. Assumptions

- M-Pesa API (STK Push, callback, query) is available and credentials (consumer key, secret, passkey) are provided by the business.
- Email delivery (SMTP) is configured and reliable for activation and password reset.
- Vendors are created and linked to users by administrators (or through a defined onboarding process).
- Categories, subcategories, and mini-subcategories are created by administrators before vendors list products.
- Customers have access to a M-Pesa-enabled phone number for payment.
- The primary deployment target is web (desktop and mobile browsers); no native app is in scope.
- Product catalog and order data are stored in the project database; no external PIM or OMS is assumed.

---

## 9. Constraints

- Payment integration is currently scoped to M-Pesa (Kenya); adding other gateways may require additional BRD updates.
- Vendor dashboard access is tied to a User–Vendor relationship; one user per vendor (or as per current data model).
- Cart for guests is session-based; cart is not persisted across devices until the user logs in and checkout creates an order.
- Rich text and file uploads (product images, CKEditor) are subject to configured file size and type limits (Django/media server).
- Django admin is the primary back-office; no separate custom “super admin” portal is in scope.

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **Vendor** | A seller/store on the platform; has a profile and sells products. |
| **CartOrder** | An order created at checkout; contains CartOrderItems and payment/shipping info. |
| **Product variation** | A specific combination of product + optional color/size with its own SKU, price, and stock. |
| **Mini-subcategory** | The lowest level in the category hierarchy (Category → Subcategory → Mini-subcategory). |
| **STK Push** | M-Pesa “push” flow that prompts the customer to enter PIN on their phone. |
| **Callback** | HTTP callback from M-Pesa to the platform to report payment result. |
| **SKU** | Stock Keeping Unit; unique identifier for a product or variation. |
| **Coupon** | A discount code that can be applied at checkout. |

---

## 11. Appendix

### 11.1 Reference Documents

- [README.md](../README.md) — Project overview and quick start  
- [ARCHITECTURE.md](ARCHITECTURE.md) — Applications, models, URLs, middleware  
- [SETUP.md](SETUP.md) — Installation and configuration  
- [ROUTES.md](ROUTES.md) — URL route reference  

### 11.2 Priority Legend

- **Must:** Critical for launch; system is incomplete without it.  
- **Should:** Important; can be deferred to a later release if necessary.  

---

*End of Business Requirements Document*
