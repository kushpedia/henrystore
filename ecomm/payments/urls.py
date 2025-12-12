from django.contrib import admin
from django.urls import path, include
from . import views
app_name = 'mpesa'
urlpatterns = [
    path('accesstoken/', views.get_access_token, name='get_access_token'),
    path('initiate/', views.initiate_stk_push, name='initiate_stk_push'),
    path('query/', views.query_stk_status, name='query_stk_status'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('check-status/<str:order_id>/', views.check_payment_status, name='check_payment_status'),  # Add this
]