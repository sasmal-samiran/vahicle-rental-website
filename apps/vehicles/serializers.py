import datetime
import json
from django.db.models import Avg
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from rest_framework import serializers
from utils.supabase_storage import SupabaseStorageService
from .models import Category, Location, Car, CarImage

def parse_datetime_param(val, is_end=False):
    if not val:
        return None
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

class CategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description', 'image_url']

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
        fields = ['id', 'car', 'image_path', 'url', 'view_type', 'view_type_display', 'caption', 'is_primary']

    def get_url(self, obj):
        return SupabaseStorageService.get_gallery_image_url(obj.image_path)

class CarListSerializer(serializers.ModelSerializer):
    category = CategorySimpleSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    images = CarImageSerializer(many=True, read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source='location', write_only=True, required=False, allow_null=True
    )
    primary_image = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    is_available_for_dates = serializers.SerializerMethodField()
    main_image = serializers.FileField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'display_name', 'year', 'license_plate',
            'category', 'category_id', 'location', 'location_id',
            'transmission', 'fuel_type', 'seats', 'doors', 'luggage_capacity',
            'mileage_limit', 'engine_capacity', 'power_hp', 'price_per_day',
            'security_deposit', 'main_image_path', 'primary_image', 'main_image_url', 'main_image', 'images', 'status',
            'is_available_for_dates',
            'features', 'description', 'average_rating', 'total_reviews', 'created_at'
        ]

    def create(self, validated_data):
        main_image = validated_data.pop('main_image', None)
        car = super().create(validated_data)
        if main_image:
            from apps.vehicles.services import VehicleService
            VehicleService.upload_and_save_main_image(car, main_image)
        return car

    def update(self, instance, validated_data):
        main_image = validated_data.pop('main_image', None)
        car = super().update(instance, validated_data)
        if main_image:
            from apps.vehicles.services import VehicleService
            VehicleService.upload_and_save_main_image(car, main_image)
        return car

    def validate_features(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [f.strip() for f in value.split(',') if f.strip()]
        return value

    def get_primary_image(self, obj):
        return SupabaseStorageService.get_car_image_url(obj.main_image_path)

    def get_main_image_url(self, obj):
        return self.get_primary_image(obj)

    def get_average_rating(self, obj):
        if hasattr(obj, 'annotated_avg_rating'):
            return round(float(obj.annotated_avg_rating), 1) if obj.annotated_avg_rating is not None else 4.8
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 4.8

    def get_total_reviews(self, obj):
        if hasattr(obj, 'annotated_total_reviews'):
            return obj.annotated_total_reviews or 0
        return obj.reviews.filter(is_approved=True).count()

    def get_is_available_for_dates(self, obj):
        if obj.status != 'AVAILABLE':
            return False

        booked_car_ids = self.context.get('booked_car_ids')
        if booked_car_ids is not None:
            return obj.id not in booked_car_ids

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
    category = CategorySimpleSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source='location', write_only=True, required=False, allow_null=True
    )
    images = CarImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    is_available_for_dates = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    main_image = serializers.FileField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'display_name', 'year', 'license_plate', 'vin_number',
            'category', 'category_id', 'location', 'location_id', 'transmission', 'fuel_type', 'seats', 'doors',
            'luggage_capacity', 'mileage_limit', 'engine_capacity', 'power_hp',
            'price_per_day', 'security_deposit', 'main_image_path', 'primary_image', 'main_image_url', 'main_image',
            'images', 'status', 'is_available_for_dates', 'features', 'description', 'average_rating',
            'total_reviews', 'recent_reviews', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        main_image = validated_data.pop('main_image', None)
        car = super().create(validated_data)
        if main_image:
            from apps.vehicles.services import VehicleService
            VehicleService.upload_and_save_main_image(car, main_image)
        return car

    def update(self, instance, validated_data):
        main_image = validated_data.pop('main_image', None)
        car = super().update(instance, validated_data)
        if main_image:
            from apps.vehicles.services import VehicleService
            VehicleService.upload_and_save_main_image(car, main_image)
        return car

    def validate_features(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [f.strip() for f in value.split(',') if f.strip()]
        return value

    def get_primary_image(self, obj):
        return SupabaseStorageService.get_car_image_url(obj.main_image_path)

    def get_main_image_url(self, obj):
        return self.get_primary_image(obj)

    def get_average_rating(self, obj):
        if hasattr(obj, 'annotated_avg_rating') and obj.annotated_avg_rating is not None:
            return round(float(obj.annotated_avg_rating), 1)
        return 4.9

    def get_total_reviews(self, obj):
        if hasattr(obj, 'annotated_total_reviews') and obj.annotated_total_reviews is not None:
            return obj.annotated_total_reviews
        return 0

    def get_is_available_for_dates(self, obj):
        if obj.status != 'AVAILABLE':
            return False

        booked_car_ids = self.context.get('booked_car_ids')
        if booked_car_ids is not None:
            return obj.id not in booked_car_ids

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
        if hasattr(obj, 'approved_reviews'):
            reviews = obj.approved_reviews[:5]
        else:
            reviews = obj.reviews.filter(is_approved=True).select_related('customer').order_by('-created_at')[:5]
        return ReviewSerializer(reviews, many=True).data

