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
	path("checkout/", views.checkout, name="checkout"),
	# paypal urls
	path('paypal/', include('paypal.standard.ipn.urls')),
	# payment process urls
	path("payment-completed/", views.payment_completed_view, name="payment-completed"),
	path("payment-failed/", views.payment_failed_view, name="payment-failed"),

	# dashboard
	path("dashboard/", views.customer_dashboard, name="dashboard"),
	# order deatails
	path("dashboard/order/<int:id>", views.order_detail, name="order-detail"),
    ]
