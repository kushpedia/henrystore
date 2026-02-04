from django.urls import path
from useradmin import views

app_name = "useradmin"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
	path("products/", views.products, name="dashboard-products"),
	path("add-products/", views.add_product, name="dashboard-add-products"),
	path('get-variation-options/', views.get_variation_options, name='get-variation-options'),
	path("edit-products/<pid>/", views.dashboard_edit_products, name="dashboard-edit-products"),
	path("delete-products/<pid>/", views.delete_product, name="dashboard-delete-products"),
	path("orders/", views.orders, name="orders"),
    path("order_detail/<id>/", views.order_detail, name="order_detail"),
	path("change_order_status/<oid>/", views.change_order_status, name="change_order_status"),
	path("shop_page/", views.shop_page, name="shop_page"),
    path("reviews/", views.reviews, name="reviews"),
	path("settings/", views.settings, name="settings"),
	path("change_password/", views.change_password, name="change_password"),
	# select subcategory ajax
	path('get-subcategories/', views.get_subcategories, name='get_subcategories'),
	path('get-mini-subcategories/', views.get_mini_subcategories, name='get_mini_subcategories'),
	path('contact-messages/', views.contact_messages, name='dashboard-contact-messages'),

	# API endpoints
    path('api/contact/<int:message_id>/', views.api_contact_detail, name='api-contact-detail'),
    path('api/contact/<int:message_id>/mark-read/', views.api_mark_as_read, name='api-mark-read'),
    path('api/contact/<int:message_id>/toggle-read/', views.api_toggle_read, name='api-toggle-read'),
    path('api/contact/mark-all-read/', views.api_mark_all_read, name='api-mark-all-read'),
    path('api/contact/<int:message_id>/reply/', views.api_send_reply, name='api-send-reply'),
    path('api/contact/<int:message_id>/delete/', views.api_delete_message, name='api-delete-message'),
    path('api/contact/delete-all-read/', views.api_delete_all_read, name='api-delete-all-read'),
    path('api/contact/export/', views.api_export_messages, name='api-export-messages'),
    path('api/contact/unread-count/', views.api_unread_count, name='api-unread-count'),
    
    # Row click functionality
    path('contact-messages/<int:message_id>/view/', views.mark_and_view_message, name='view-message'),
]