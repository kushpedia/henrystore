# URL Routes Reference

Quick reference for all URL patterns. Use in templates as `{% url 'namespace:name' %}` or with reverse.

---

## Root (`ecomm/urls.py`)

| Prefix | Includes |
|--------|----------|
| `/admin/` | Django admin |
| `/` | core |
| `/users/` | userauths |
| `/useradmin/` | useradmin |
| `/ckeditor/` | ckeditor_uploader |
| `/payments/` | payments |

Static and media are appended when `DEBUG=True`.

---

## Core (`core`)

| URL | Name |
|-----|------|
| `/` | `core:index` |
| `/products/` | `core:product-list` |
| `/products/load-more/` | `core:product-list-ajax` |
| `/product/<pid>/` | `core:product-detail` |
| `/category/` | `core:category-list` |
| `/category/<cid>/` | `core:category-product-list` |
| `/subcategory/<cid>/` | `core:subcategory-products` |
| `/minicategory/<cid>/` | `core:minicategory-products` |
| `/vendors/` | `core:vendor-list` |
| `/vendor/<vid>/` | `core:vendor-detail` |
| `/products/tag/<slug:tag_slug>/` | `core:tags` |
| `/search/` | `core:search` |
| `/filter-products/` | `core:filter-product` |
| `/add-to-cart/` | `core:add-to-cart` |
| `/cart/` | `core:cart` |
| `/delete-from-cart/` | `core:delete-from-cart` |
| `/update-cart/` | `core:update-cart` |
| `/new_checkout/<oid>/` | `core:new_checkout` |
| `/payment-completed/<oid>/` | `core:payment-completed` |
| `/payment-failed/` | `core:payment-failed` |
| `/dashboard/` | `core:dashboard` |
| `/dashboard/order/<id>` | `core:order-detail` |
| `/make-default-address/` | `core:make-default-address` |
| `/wishlist/` | `core:wishlist` |
| `/add-to-wishlist/` | `core:add-to-wishlist` |
| `/remove-from-wishlist/` | `core:remove-from-wishlist` |
| `/contact/` | `core:contact` |
| `/ajax-add-review/<int:pid>/` | `core:ajax-add-review` |
| `/ajax-contact-form/` | `core:ajax-contact-form` |
| `/save_checkout_info/` | `core:save_checkout_info` |

---

## Userauths (`userauths`)

| URL | Name |
|-----|------|
| `/users/sign-up/` | `userauths:sign-up` |
| `/users/sign-in/` | `userauths:sign-in` |
| `/users/sign-out/` | `userauths:sign-out` |
| `/users/profile/update/` | `userauths:profile-update` |
| `/users/activate/<uidb64>/<token>` | `userauths:activate` |
| `/users/forgot-password/` | `userauths:forgot_password` |
| `/users/reset-password/<uidb64>/<token>/` | `userauths:reset_password` |

---

## Useradmin (`useradmin`)

| URL | Name |
|-----|------|
| `/useradmin/` | `useradmin:dashboard` |
| `/useradmin/products/` | `useradmin:dashboard-products` |
| `/useradmin/add-products/` | `useradmin:dashboard-add-products` |
| `/useradmin/edit-products/<pid>/` | `useradmin:dashboard-edit-products` |
| `/useradmin/delete-products/<pid>/` | `useradmin:dashboard-delete-products` |
| `/useradmin/get-variation-options/` | `useradmin:get-variation-options` |
| `/useradmin/orders/` | `useradmin:orders` |
| `/useradmin/order_detail/<id>/` | `useradmin:order_detail` |
| `/useradmin/change_order_status/<oid>/` | `useradmin:change_order_status` |
| `/useradmin/shop_page/` | `useradmin:shop_page` |
| `/useradmin/reviews/` | `useradmin:reviews` |
| `/useradmin/settings/` | `useradmin:settings` |
| `/useradmin/change_password/` | `useradmin:change_password` |
| `/useradmin/get-subcategories/` | `useradmin:get_subcategories` |
| `/useradmin/get-mini-subcategories/` | `useradmin:get_mini_subcategories` |

---

## Payments (`mpesa`)

| URL | Name |
|-----|------|
| `/payments/accesstoken/` | `mpesa:get_access_token` |
| `/payments/initiate/` | `mpesa:initiate_stk_push` |
| `/payments/query/` | `mpesa:query_stk_status` |
| `/payments/callback/` | `mpesa:payment_callback` |
| `/payments/check-status/<str:order_id>/` | `mpesa:check_payment_status` |

---

For full architecture (models, middleware, context processors), see [ARCHITECTURE.md](ARCHITECTURE.md).
