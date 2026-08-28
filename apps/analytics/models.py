from django.db import models
from django.conf import settings
from apps.vehicles.models import Car
from apps.users.models import User

class SearchLog(models.Model):
    """Track user searches for improving recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=255)
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    clicked_car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        return f"{self.query} - {self.created_at}"

class RecommendationClick(models.Model):
    """Track recommendation effectiveness"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50)  # 'popular', 'similar', 'personalized'
    position = models.PositiveIntegerField()  # Position in recommendation list
    clicked = models.BooleanField(default=False)
    booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['car', 'recommendation_type']),
            models.Index(fields=['user', 'created_at']),
        ]

class CarPopularityMetrics(models.Model):
    """Cached popularity metrics for cars"""
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='popularity_metrics')
    views_last_7_days = models.PositiveIntegerField(default=0)
    views_last_30_days = models.PositiveIntegerField(default=0)
    bookings_last_30_days = models.PositiveIntegerField(default=0)
    booking_conversion_rate = models.FloatField(default=0.0)
    average_daily_views = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metrics for {self.car}"