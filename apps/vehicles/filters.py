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
    status = filters.CharFilter(method='filter_status')
    available_only = filters.BooleanFilter(method='filter_available_only')

    pickup_date = filters.CharFilter(method='filter_noop')
    return_date = filters.CharFilter(method='filter_noop')

    class Meta:
        model = Car
        fields = ['category', 'category_id', 'location_id', 'city', 'transmission', 'fuel_type', 'min_price', 'max_price', 'seats', 'status', 'available_only']

    def filter_noop(self, queryset, name, value):
        return queryset

    def filter_status(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip().upper()
        if val == 'AVAILABLE':
            pickup_str = self.data.get('pickup_date')
            return_str = self.data.get('return_date')
            if pickup_str and return_str:
                from .serializers import parse_datetime_param
                start = parse_datetime_param(pickup_str, is_end=False)
                end = parse_datetime_param(return_str, is_end=True)
                if start and end:
                    overlapping_car_ids = Booking.objects.filter(
                        status__in=['CONFIRMED', 'ONGOING', 'PENDING'],
                        start_date__lt=end,
                        end_date__gt=start
                    ).values_list('car_id', flat=True)
                    return queryset.filter(status='AVAILABLE').exclude(id__in=overlapping_car_ids)
            return queryset.filter(status='AVAILABLE')
        elif val in ['RESERVED', 'RESERVED_FOR_DATES', 'BOOKED', 'RESERVED_DATES']:
            pickup_str = self.data.get('pickup_date')
            return_str = self.data.get('return_date')
            if pickup_str and return_str:
                from .serializers import parse_datetime_param
                start = parse_datetime_param(pickup_str, is_end=False)
                end = parse_datetime_param(return_str, is_end=True)
                if start and end:
                    overlapping_car_ids = Booking.objects.filter(
                        status__in=['CONFIRMED', 'ONGOING', 'PENDING'],
                        start_date__lt=end,
                        end_date__gt=start
                    ).values_list('car_id', flat=True)
                    return queryset.filter(status='AVAILABLE', id__in=overlapping_car_ids)
            booked_car_ids = Booking.objects.filter(
                status__in=['CONFIRMED', 'ONGOING', 'PENDING']
            ).values_list('car_id', flat=True)
            return queryset.filter(id__in=booked_car_ids)
        return queryset.filter(status=val)

    def filter_available_only(self, queryset, name, value):
        if not value:
            return queryset
        return self.filter_status(queryset, 'status', 'AVAILABLE')
