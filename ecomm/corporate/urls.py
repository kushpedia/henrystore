from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings

app_name = 'corporate'
urlpatterns = [
	
	
	path('affiliate-program/', views.affiliate_program, name='affiliate-program'),
    
    path('our-suppliers/', views.our_suppliers, name='our-suppliers'),
    path('accessibility/', views.accessibility, name='accessibility'),
    path('promotions/', views.promotions, name='promotions'),
    path("return-policy/", views.return_policy_view, name="return-policy"),
    path("privacy-policy/", views.privacy_policy_view, name="privacy-policy"),
    path("terms-conditions/", views.terms_conditions_view, name="terms-conditions"),
]