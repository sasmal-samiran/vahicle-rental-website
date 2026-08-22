from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    RequestOTPView,
    VerifyOTPView,
    PasswordLoginView,
    UserProfileView,
    AdminCustomerListView,
    AdminCustomerToggleStatusView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='customer-register'),
    path('auth/otp/request/', RequestOTPView.as_view(), name='otp-request'),
    path('auth/otp/verify/', VerifyOTPView.as_view(), name='otp-verify'),
    path('auth/login/', PasswordLoginView.as_view(), name='password-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('admin/customers/', AdminCustomerListView.as_view(), name='admin-customer-list'),
    path('admin/customers/<int:pk>/toggle-status/', AdminCustomerToggleStatusView.as_view(), name='admin-customer-toggle'),
]
