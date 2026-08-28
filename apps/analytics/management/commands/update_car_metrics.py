from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Car
from apps.analytics.models import CarPopularityMetrics

class Command(BaseCommand):
    help = 'Update car popularity metrics'
    
    def handle(self, *args, **kwargs):
        cars = Car.objects.all()
        now = timezone.now()
        
        for car in cars:
            metrics, created = CarPopularityMetrics.objects.get_or_create(car=car)
            
            # Calculate metrics
            metrics.views_last_7_days = car.booking_set.filter(
                created_at__gte=now - timedelta(days=7)
            ).count()
            metrics.views_last_30_days = car.booking_set.filter(
                created_at__gte=now - timedelta(days=30)
            ).count()
            metrics.bookings_last_30_days = car.booking_set.filter(
                created_at__gte=now - timedelta(days=30)
            ).count()
            
            # Update car popularity
            car.update_popularity_score()
            
            metrics.save()
            
        self.stdout.write(self.style.SUCCESS('Successfully updated car metrics'))