from rest_framework import serializers
from .models import User, OTPVerification

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    total_bookings = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'first_name', 'last_name',
            'full_name', 'role', 'driver_license_number', 'address', 'city',
            'profile_picture', 'is_phone_verified', 'is_active', 'total_bookings',
            'total_spent', 'created_at'
        ]
        read_only_fields = ['id', 'role', 'is_phone_verified', 'created_at']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip() or obj.username

    def get_total_bookings(self, obj):
        if hasattr(obj, 'bookings'):
            return obj.bookings.count()
        return 0

    def get_total_spent(self, obj):
        if hasattr(obj, 'bookings'):
            from django.db.models import Sum
            total = obj.bookings.filter(payment_status='PAID').aggregate(Sum('total_amount'))['total_amount__sum']
            return float(total) if total else 0.0
        return 0.0

class OTPRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=100, required=True, help_text='Phone number or email address')
    purpose = serializers.ChoiceField(choices=['LOGIN', 'REGISTER', 'VERIFY'], default='LOGIN')

class OTPVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=100, required=True)
    otp_code = serializers.CharField(max_length=6, required=True)
    purpose = serializers.ChoiceField(choices=['LOGIN', 'REGISTER', 'VERIFY'], default='LOGIN')
    first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

class PasswordLoginSerializer(serializers.Serializer):
    username_or_phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    driver_license_number = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'password', 'driver_license_number', 'address', 'city'
        ]

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email address already exists. Please sign in.")
        return normalized

    def validate_phone_number(self, value):
        cleaned = value.strip()
        if User.objects.filter(phone_number=cleaned).exists():
            raise serializers.ValidationError("An account with this phone number already exists. Please sign in.")
        return cleaned

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email', '')
        base_username = email.split('@')[0] if email else 'user'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            password=password,
            role='CUSTOMER',
            is_phone_verified=True,
            **validated_data
        )
        return user

