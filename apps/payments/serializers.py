from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    booking_code = serializers.CharField(source='booking.booking_code', read_only=True)
    customer_name = serializers.CharField(source='booking.customer.get_full_name', read_only=True)
    car_name = serializers.CharField(source='booking.car.display_name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'booking_code', 'customer_name', 'car_name', 'transaction_id',
            'provider', 'gateway_order_id', 'amount', 'currency', 'status',
            'payment_method', 'created_at'
        ]

class InitiatePaymentSerializer(serializers.Serializer):
    booking_code = serializers.CharField(required=True)
    provider = serializers.CharField(default='SANDBOX')
    currency = serializers.CharField(default='INR')

class MockCheckoutSerializer(serializers.Serializer):
    booking_code = serializers.CharField(required=True)
    payment_method = serializers.CharField(default='CARD')
    card_last_four = serializers.CharField(max_length=4, default='4242')
