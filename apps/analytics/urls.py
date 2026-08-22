from django.urls import path
from .views import AdminDashboardStatsView

urlpatterns = [
    path('admin/analytics/dashboard/', AdminDashboardStatsView.as_view(), name='admin-analytics-dashboard'),
]
