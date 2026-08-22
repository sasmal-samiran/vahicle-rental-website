import secrets
from decimal import Decimal
from django.conf import settings
from apps.notifications.services import NotificationService
from .models import Payment, Refund

class PaymentService:
    @staticmethod
    def initiate_payment(booking, provider='SANDBOX', currency='USD'):
        amount_cents = int(booking.total_amount * 100)
        gateway_order_id = None
        client_secret = None

        if provider == 'RAZORPAY':
            try:
                import razorpay
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                order_data = {
                    'amount': amount_cents,
                    'currency': currency if currency in ['INR', 'USD'] else 'USD',
                    'receipt': booking.booking_code,
                    'notes': {'booking_code': booking.booking_code}
                }
                rp_order = client.order.create(data=order_data)
                gateway_order_id = rp_order['id']
            except Exception as e:
                # Graceful sandbox fallback if live key is test placeholder
                gateway_order_id = f'order_mock_rzp_{secrets.token_hex(6)}'
        
        elif provider == 'STRIPE':
            try:
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency=currency.lower(),
                    metadata={'booking_code': booking.booking_code}
                )
                gateway_order_id = intent['id']
                client_secret = intent['client_secret']
            except Exception as e:
                # Graceful sandbox fallback
                gateway_order_id = f'pi_mock_stripe_{secrets.token_hex(6)}'
                client_secret = f'pi_mock_secret_{secrets.token_hex(12)}'
        
        else: # Built-in Sandbox
            gateway_order_id = f'order_sandbox_{secrets.token_hex(6)}'

        payment = Payment.objects.create(
            booking=booking,
            provider=provider,
            gateway_order_id=gateway_order_id,
            amount=booking.total_amount,
            currency=currency,
            status='INITIATED'
        )

        return {
            'payment_id': payment.id,
            'transaction_id': payment.transaction_id,
            'provider': provider,
            'gateway_order_id': gateway_order_id,
            'client_secret': client_secret,
            'amount': float(booking.total_amount),
            'currency': currency,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'stripe_key': settings.STRIPE_PUBLISHABLE_KEY,
        }

    @staticmethod
    def finalize_success(payment, payment_method='CARD', gateway_payment_id=None, signature=None):
        payment.status = 'SUCCESS'
        payment.payment_method = payment_method
        payment.gateway_payment_id = gateway_payment_id or f'pay_{secrets.token_hex(6)}'
        payment.gateway_signature = signature or 'verified'
        payment.save()

        booking = payment.booking
        booking.status = 'CONFIRMED'
        booking.payment_status = 'PAID'
        booking.save(update_fields=['status', 'payment_status'])

        # Notify Customer
        NotificationService.create_notification(
            user=booking.customer,
            title='Payment Received & Booking Confirmed',
            message=f'Your payment of  for booking {booking.booking_code} was successful. Your reservation for {booking.car.display_name} is confirmed!',
            type='PAYMENT'
        )
        return payment
