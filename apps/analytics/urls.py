from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.SearchCarsView.as_view(), name='search-cars'),
    path('recommendations/', views.GetRecommendationsView.as_view(), name='get-recommendations'),
    path('recommendations/context/', views.ContextRecommendationsView.as_view(), name='context-recommendations'),
]