import json
from rest_framework import serializers
from django.db.models import Avg
from django.utils.dateparse import parse_datetime, parse_date
from .models import Category, Location, Car, CarImage

def parse_datetime_param(val, is_end=False):
    if not val:
        return None
    import datetime
    from django.utils import timezone
    val = str(val).strip()
    dt = parse_datetime(val)
    if dt is None and ' ' in val:
        dt = parse_datetime(val.replace(' ', '+'))
    if dt is None:
        d = parse_date(val)
        if d:
            dt = datetime.datetime.combine(d, datetime.time.max if is_end else datetime.time.min)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt

class CategorySerializer(serializers.ModelSerializer):
    car_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description', 'image_url', 'car_count']

    def get_car_count(self, obj):
        return obj.cars.exclude(status='INACTIVE').count()

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'city', 'address', 'phone', 'email', 'latitude', 'longitude', 'is_active']

class CarImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True)

    class Meta:
        model = CarImage
        fields = ['id', 'car', 'image', 'url', 'view_type', 'view_type_display', 'caption', 'is_primary']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            try:
                return request.build_absolute_uri(obj.image.url) if request else obj.image.url
            except Exception:
                return obj.image.url
        return obj.image_url or ''

class CarListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    images = CarImageSerializer(many=True, read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source='location', write_only=True, required=False, allow_null=True
    )
    primary_image = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    is_available_for_dates = serializers.SerializerMethodField()
    main_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'display_name', 'year', 'license_plate',
            'category', 'category_id', 'location', 'location_id',
            'transmission', 'fuel_type', 'seats', 'doors', 'luggage_capacity',
            'mileage_limit', 'engine_capacity', 'power_hp', 'price_per_day',
            'security_deposit', 'primary_image', 'main_image', 'main_image_url', 'images', 'status',
            'is_available_for_dates',
            'features', 'description', 'average_rating', 'total_reviews', 'created_at'
        ]

    def validate_features(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [f.strip() for f in value.split(',') if f.strip()]
        return value

    def get_primary_image(self, obj):
        request = self.context.get('request')
        if obj.main_image:
            try:
                return request.build_absolute_uri(obj.main_image.url) if request else obj.main_image.url
            except Exception:
                return obj.main_image.url
        if obj.main_image_url:
            return obj.main_image_url
        return 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'

    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 4.8

    def get_total_reviews(self, obj):
        return obj.reviews.filter(is_approved=True).count()

    def get_is_available_for_dates(self, obj):
        if obj.status != 'AVAILABLE':
            return False
        request = self.context.get('request')
        if not request:
            return True
        pickup_str = request.query_params.get('pickup_date')
        return_str = request.query_params.get('return_date')
        if not pickup_str or not return_str:
            return True

        from apps.bookings.services import BookingService
        start = parse_datetime_param(pickup_str, is_end=False)
        end = parse_datetime_param(return_str, is_end=True)

        if not start or not end:
            return True

        return BookingService.is_car_available(obj, start, end)

class CarDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source='location', write_only=True, required=False, allow_null=True
    )
    images = CarImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    is_available_for_dates = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    main_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'display_name', 'year', 'license_plate', 'vin_number',
            'category', 'category_id', 'location', 'location_id', 'transmission', 'fuel_type', 'seats', 'doors',
            'luggage_capacity', 'mileage_limit', 'engine_capacity', 'power_hp',
            'price_per_day', 'security_deposit', 'primary_image', 'main_image', 'main_image_url',
            'images', 'status', 'is_available_for_dates', 'features', 'description', 'average_rating',
            'total_reviews', 'recent_reviews', 'created_at', 'updated_at'
        ]

    def validate_features(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [f.strip() for f in value.split(',') if f.strip()]
        return value

    def get_primary_image(self, obj):
        request = self.context.get('request')
        if obj.main_image:
            try:
                return request.build_absolute_uri(obj.main_image.url) if request else obj.main_image.url
            except Exception:
                return obj.main_image.url
        if obj.main_image_url:
            return obj.main_image_url
        return 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'

    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 4.9

    def get_total_reviews(self, obj):
        return obj.reviews.filter(is_approved=True).count()

    def get_is_available_for_dates(self, obj):
        if obj.status != 'AVAILABLE':
            return False
        request = self.context.get('request')
        if not request:
            return True
        pickup_str = request.query_params.get('pickup_date')
        return_str = request.query_params.get('return_date')
        if not pickup_str or not return_str:
            return True

        from apps.bookings.services import BookingService
        start = parse_datetime_param(pickup_str, is_end=False)
        end = parse_datetime_param(return_str, is_end=True)

        if not start or not end:
            return True

        return BookingService.is_car_available(obj, start, end)

    def get_recent_reviews(self, obj):
        from apps.reviews.serializers import ReviewSerializer
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        return ReviewSerializer(reviews, many=True).data

