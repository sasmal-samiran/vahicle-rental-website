from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CalculateQuoteView,
    ValidateCouponView,
    CustomerBookingListCreateView,
    BookingDetailView,
    CancelBookingView,
    AdminBookingViewSet
)

router = DefaultRouter()
router.register(r'admin/bookings', AdminBookingViewSet, basename='admin-bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('bookings/quote/', CalculateQuoteView.as_view(), name='booking-quote'),
    path('bookings/validate-coupon/', ValidateCouponView.as_view(), name='validate-coupon'),
    path('bookings/', CustomerBookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<str:booking_code>/', BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<str:booking_code>/cancel/', CancelBookingView.as_view(), name='booking-cancel'),
]
