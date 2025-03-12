from django.urls import path
from django.urls import include

from paymentsApp.api import check_payment_status

urlpatterns = [
    path('payment/', include('paymentsApp.urls')),
    path('api/check_payment/', check_payment_status, name='check_payment_status'),
]
