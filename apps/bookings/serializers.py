from rest_framework import serializers
from apps.vehicles.serializers import CarListSerializer, LocationSerializer
from apps.users.serializers import UserSerializer
from .models import Booking, BookingAddon, Coupon

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'min_booking_amount', 'max_discount_amount',
            'valid_from', 'valid_until', 'is_active', 'usage_count'
        ]
        read_only_fields = ['id', 'usage_count']

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, data):
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        if valid_from and valid_until and valid_until <= valid_from:
            raise serializers.ValidationError({'valid_until': 'Expiration date must be after valid from date.'})
        return data

class BookingAddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAddon
        fields = ['id', 'name', 'daily_rate', 'total_price']

class BookingListSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    pickup_location = LocationSerializer(read_only=True)
    return_location = LocationSerializer(read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    has_reviewed = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_code', 'car', 'pickup_location', 'return_location',
            'start_date', 'end_date', 'total_days', 'daily_rate', 'rental_charge',
            'insurance_plan', 'insurance_amount', 'addons_total', 'tax_amount',
            'deposit_amount', 'discount_amount', 'total_amount', 'status',
            'payment_status', 'driver_name', 'customer_name', 'created_at'
            , 'has_reviewed', 'review'
        ]

    def get_has_reviewed(self, obj):
        return hasattr(obj, 'review')

    def get_review(self, obj):
        review = getattr(obj, 'review', None)
        if not review:
            return None
        return {
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at,
        }

class BookingDetailSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    pickup_location = LocationSerializer(read_only=True)
    return_location = LocationSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    addons = BookingAddonSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)
    has_reviewed = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_code', 'customer', 'car', 'pickup_location', 'return_location',
            'start_date', 'end_date', 'total_days', 'daily_rate', 'rental_charge',
            'insurance_plan', 'insurance_amount', 'addons', 'addons_total', 'tax_amount',
            'deposit_amount', 'discount_amount', 'coupon', 'total_amount', 'status',
            'payment_status', 'driver_name', 'driver_phone', 'driver_email',
            'driver_license', 'special_requests', 'cancellation_reason',
            'has_reviewed', 'review', 'created_at', 'updated_at'
        ]

    def get_has_reviewed(self, obj):
        return hasattr(obj, 'review')

    def get_review(self, obj):
        review = getattr(obj, 'review', None)
        if not review:
            return None
        return {
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at,
        }

class PriceQuoteRequestSerializer(serializers.Serializer):
    car_id = serializers.IntegerField(required=True)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    insurance_plan = serializers.ChoiceField(choices=['NONE', 'STANDARD', 'PREMIUM'], default='NONE')
    addons = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default='')

class BookingCreateSerializer(serializers.Serializer):
    car_id = serializers.IntegerField(required=True)
    pickup_location_id = serializers.IntegerField(required=True)
    return_location_id = serializers.IntegerField(required=True)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    insurance_plan = serializers.ChoiceField(choices=['NONE', 'STANDARD', 'PREMIUM'], default='NONE')
    addons = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default='')
    driver_name = serializers.CharField(max_length=100, required=True)
    driver_phone = serializers.CharField(max_length=30, required=True)
    driver_email = serializers.EmailField(required=False, allow_blank=True)
    driver_license = serializers.CharField(max_length=50, required=False, allow_blank=True)
    special_requests = serializers.CharField(required=False, allow_blank=True)

class CancelBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default='Customer requested cancellation')
