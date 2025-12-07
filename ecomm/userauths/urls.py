from django.contrib import admin
from django.urls import path
from . import views
app_name = 'userauths'
urlpatterns = [
	path('sign-up/', views.register_view, name='sign-up'),
	path("sign-in/", views.login_view, name="sign-in"),
	path("sign-out/", views.logout_view, name="sign-out"),

	path("profile/update/", views.profile_update, name="profile-update"),

	path('activate/<uidb64>/<token>', views.activate, name='activate'),
	path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    ]