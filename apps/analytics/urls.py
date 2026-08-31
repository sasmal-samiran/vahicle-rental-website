from django.urls import path
from .views import (
    AdminDashboardStatsView,
    PersonalizedRecommendationsView,
    SimilarCarsRecommendationsView,
    PopularCarsRecommendationsView,
    TrendingCarsRecommendationsView,
    ContextRecommendationsView,
    TrackClickView,
    TrendingSearchesView,
    AdminRecommendationPerformanceView,
)

urlpatterns = [
    # Admin Analytics
    path('admin/analytics/dashboard/', AdminDashboardStatsView.as_view(), name='admin-analytics-dashboard'),
    path('admin/analytics/recommendation-performance/', AdminRecommendationPerformanceView.as_view(), name='admin-recommendation-performance'),

    # Recommendation Engine Endpoints
    path('analytics/recommendations/', PersonalizedRecommendationsView.as_view(), name='recommendations-default'),
    path('analytics/recommendations/personalized/', PersonalizedRecommendationsView.as_view(), name='recommendations-personalized'),
    path('analytics/recommendations/similar/<int:car_id>/', SimilarCarsRecommendationsView.as_view(), name='recommendations-similar'),
    path('analytics/recommendations/popular/', PopularCarsRecommendationsView.as_view(), name='recommendations-popular'),
    path('analytics/recommendations/trending/', TrendingCarsRecommendationsView.as_view(), name='recommendations-trending'),
    path('analytics/recommendations/context/', ContextRecommendationsView.as_view(), name='recommendations-context'),

    # Click & Search Tracking Endpoints
    path('analytics/track-click/', TrackClickView.as_view(), name='analytics-track-click'),
    path('track-click/', TrackClickView.as_view(), name='track-click-alias'),
    path('analytics/trending-searches/', TrendingSearchesView.as_view(), name='analytics-trending-searches'),
]


