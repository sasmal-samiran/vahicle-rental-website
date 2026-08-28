from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarReviewListView, CreateReviewView, UpdateReviewView, AdminReviewViewSet

router = DefaultRouter()
router.register(r'admin/reviews', AdminReviewViewSet, basename='admin-reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('cars/<int:car_id>/reviews/', CarReviewListView.as_view(), name='car-reviews-list'),
    path('reviews/create/', CreateReviewView.as_view(), name='review-create'),
    path('reviews/<str:booking_code>/update/', UpdateReviewView.as_view(), name='review-update'),
]
