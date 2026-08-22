from django_filters import rest_framework as filters
from django.db.models import Q
from django.utils.dateparse import parse_datetime, parse_date
from .models import Car
from apps.bookings.models import Booking

class CarFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    category_id = filters.NumberFilter(field_name='category__id')
    location_id = filters.NumberFilter(field_name='location__id')
    city = filters.CharFilter(field_name='location__city', lookup_expr='icontains')
    transmission = filters.CharFilter(field_name='transmission', lookup_expr='iexact')
    fuel_type = filters.CharFilter(field_name='fuel_type', lookup_expr='iexact')
    min_price = filters.NumberFilter(field_name='price_per_day', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price_per_day', lookup_expr='lte')
    seats = filters.NumberFilter(field_name='seats', lookup_expr='gte')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')

    # Date overlap filters
    pickup_date = filters.CharFilter(method='filter_by_availability')
    return_date = filters.CharFilter(method='filter_noop')

    class Meta:
        model = Car
        fields = ['category', 'category_id', 'location_id', 'city', 'transmission', 'fuel_type', 'min_price', 'max_price', 'seats', 'status']

    def filter_noop(self, queryset, name, value):
        return queryset

    def filter_by_availability(self, queryset, name, value):
        pickup_str = self.data.get('pickup_date')
        return_str = self.data.get('return_date')
        
        if not pickup_str or not return_str:
            return queryset

        # Support both full ISO datetime or simple YYYY-MM-DD
        start = parse_datetime(pickup_str) or parse_date(pickup_str)
        end = parse_datetime(return_str) or parse_date(return_str)

        if not start or not end:
            return queryset

        # Find car IDs with overlapping active bookings
        # Condition for overlap: booking.start_date < requested_end AND booking.end_date > requested_start
        overlapping_car_ids = Booking.objects.filter(
            status__in=['CONFIRMED', 'ONGOING', 'PENDING'],
            start_date__lt=end,
            end_date__gt=start
        ).values_list('car_id', flat=True)

        return queryset.exclude(id__in=overlapping_car_ids)
