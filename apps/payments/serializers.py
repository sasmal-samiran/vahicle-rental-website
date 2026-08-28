from rest_framework import serializers
from .models import Payment, Refund

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
    provider = serializers.ChoiceField(choices=['RAZORPAY', 'STRIPE', 'SANDBOX'], default='SANDBOX')
    currency = serializers.CharField(default='INR')

class VerifyRazorpaySerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(required=True)
    razorpay_payment_id = serializers.CharField(required=True)
    razorpay_order_id = serializers.CharField(required=True)
    razorpay_signature = serializers.CharField(required=False, default='')

class VerifyStripeSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(required=True)
    payment_intent_id = serializers.CharField(required=True)

class MockCheckoutSerializer(serializers.Serializer):
    booking_code = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(choices=['CARD', 'UPI', 'NETBANKING', 'APPLE_PAY', 'GOOGLE_PAY'], default='CARD')
    card_last_four = serializers.CharField(max_length=4, default='4242')
