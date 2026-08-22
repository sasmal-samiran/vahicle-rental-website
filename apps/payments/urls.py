from django.urls import path
from .views import (
    InitiatePaymentView,
    VerifyRazorpayView,
    VerifyStripeView,
    MockCheckoutView,
    AdminPaymentListView
)

urlpatterns = [
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/verify/razorpay/', VerifyRazorpayView.as_view(), name='payment-verify-razorpay'),
    path('payments/verify/stripe/', VerifyStripeView.as_view(), name='payment-verify-stripe'),
    path('payments/mock-checkout/', MockCheckoutView.as_view(), name='payment-mock-checkout'),
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payment-list'),
]
