from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='payment_webhook'),
    path('success/', views.payment_success, name='payment_success'),
    path('error/', views.payment_error, name='payment_error'),
]