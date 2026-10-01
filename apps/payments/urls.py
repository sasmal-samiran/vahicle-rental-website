from django.urls import path
from .views import (
    InitiatePaymentView,
    MockCheckoutView,
    AdminPaymentListView
)

urlpatterns = [
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/mock-checkout/', MockCheckoutView.as_view(), name='payment-mock-checkout'),
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payment-list'),
]
