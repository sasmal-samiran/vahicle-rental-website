from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    LocationViewSet,
    CarListView,
    CarDetailView,
    CheckCarAvailabilityView,
    AdminCarViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'admin/cars', AdminCarViewSet, basename='admin-cars')

urlpatterns = [
    path('', include(router.urls)),
    path('cars/', CarListView.as_view(), name='car-list'),
    path('cars/<int:pk>/', CarDetailView.as_view(), name='car-detail'),
    path('cars/<int:pk>/check-availability/', CheckCarAvailabilityView.as_view(), name='car-check-availability'),
    path('cars/check-availability/', CheckCarAvailabilityView.as_view(), name='cars-check-availability'),
]
