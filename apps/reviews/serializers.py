from rest_framework import serializers
from .models import Review
from apps.bookings.models import Booking

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_avatar = serializers.SerializerMethodField()
    car_name = serializers.CharField(source='car.display_name', read_only=True)
    booking_code = serializers.CharField(source='booking.booking_code', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'car', 'car_name', 'booking', 'booking_code', 'customer',
            'customer_name', 'customer_avatar', 'rating', 'title', 'comment',
            'is_approved', 'created_at'
        ]
        read_only_fields = ['id', 'customer', 'is_approved', 'created_at']

    def get_customer_name(self, obj):
        name = obj.customer.get_full_name()
        return name if name else obj.customer.username

    def get_customer_avatar(self, obj):
        from utils.supabase_storage import SupabaseStorageService
        return SupabaseStorageService.get_profile_image_url(getattr(obj.customer, 'profile_image_path', None))

class ReviewCreateSerializer(serializers.ModelSerializer):
    booking_code = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Review
        fields = ['booking_code', 'rating', 'title', 'comment']

    def validate(self, attrs):
        user = self.context['request'].user
        booking_code = attrs.get('booking_code')

        try:
            booking = Booking.objects.get(booking_code=booking_code, customer=user)
        except Booking.DoesNotExist:
            raise serializers.ValidationError({'booking_code': 'Booking not found or not owned by you.'})

        if booking.status not in ['COMPLETED', 'ONGOING', 'CONFIRMED']:
            raise serializers.ValidationError({'booking_code': 'You can only review bookings that are confirmed or completed.'})

        if hasattr(booking, 'review'):
            raise serializers.ValidationError({'booking_code': 'You have already submitted a review for this rental.'})

        attrs['booking'] = booking
        attrs['car'] = booking.car
        attrs['customer'] = user
        return attrs

    def create(self, validated_data):
        validated_data.pop('booking_code')
        return Review.objects.create(**validated_data)

class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
