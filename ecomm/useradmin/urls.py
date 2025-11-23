from django.urls import path
from useradmin import views

app_name = "useradmin"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
	path("products/", views.products, name="dashboard-products"),
	path("add-products/", views.add_product, name="dashboard-add-products"),
	path("edit-products/<pid>/", views.edit_product, name="dashboard-edit-products"),
	path("delete-products/<pid>/", views.delete_product, name="dashboard-delete-products"),
]