from django.contrib import admin
from django.urls import path, include
from . import views
app_name = 'core'
urlpatterns = [
	path('', views.index, name='index'),
	path("products/", views.product_list_view, name="product-list"),
    path("product/<pid>/", views.product_detail_view, name="product-detail"),
    path("category/", views.category_list_view, name="category-list"),
	path("category/<cid>/", views.category_product_list__view, name="category-product-list"),
	# subcategory
	path('subcategory/<cid>/', views.sub_category_product_list_view, name='subcategory-products'),
	path('minicategory/<cid>/', views.mini_category_product_list_view, name='minicategory-products'),




	path("vendors/", views.vendor_list_view, name="vendor-list"),
	path("vendor/<vid>/", views.vendor_detail_view, name="vendor-detail"),
	# tagged products
	path("products/tag/<slug:tag_slug>/", views.tag_list, name="tags"),
	# add Review

	path("ajax-add-review/<int:pid>/", views.ajax_add_review, name="ajax-add-review"),
	# search
	path("search/", views.search_view, name="search"),
	# filter products
	path("filter-products/", views.filter_product, name="filter-product"),
	# add to cart
	path("add-to-cart/", views.add_to_cart, name="add-to-cart"),
	# cart page
	path("cart/", views.cart_view, name="cart"),
	# delete from cart
	path("delete-from-cart/", views.delete_item_from_cart, name="delete-from-cart"),
	# update cart
	path("update-cart/", views.update_cart, name="update-cart"),
	# checkout
	path("new_checkout/<oid>/", views.newCheckout, name="new_checkout"),
	path("checkout/", views.checkout, name="checkout"),
	# paypal urls
	path('paypal/', include('paypal.standard.ipn.urls')),
	# payment process urls
	path("payment-completed/<oid>/", views.payment_completed_view, name="payment-completed"),
	path("payment-failed/", views.payment_failed_view, name="payment-failed"),
	# stripe payment
	path("api/create_checkout_session/<oid>/", views.create_checkout_session, name="api_checkout_session"),
	# dashboard
	path("dashboard/", views.customer_dashboard, name="dashboard"),
	# order deatails
	path("dashboard/order/<int:id>", views.order_detail, name="order-detail"),
	# make-default-address
    path("make-default-address/", views.make_address_default, name="make-default-address"),

	# wishlist
	path("wishlist/", views.wishlist_view, name="wishlist"),
	path("add-to-wishlist/", views.add_to_wishlist, name="add-to-wishlist"),
	path("remove-from-wishlist/", views.remove_wishlist, name="remove-from-wishlist"),

	# other pages
	path("contact/", views.contact, name="contact"),
	path("ajax-contact-form/", views.ajax_contact_form, name="ajax-contact-form"),

	path("save_checkout_info/", views.save_checkout_info, name="save_checkout_info"),


    ]
