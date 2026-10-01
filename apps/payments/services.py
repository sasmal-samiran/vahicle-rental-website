import secrets
from apps.notifications.services import NotificationService
from .models import Payment

class PaymentService:
    @staticmethod
    def initiate_payment(booking, provider='SANDBOX', currency='INR'):
        gateway_order_id = f'order_sandbox_{secrets.token_hex(6)}'

        payment = Payment.objects.create(
            booking=booking,
            provider='SANDBOX',
            gateway_order_id=gateway_order_id,
            amount=booking.total_amount,
            currency=currency,
            status='INITIATED'
        )

        return {
            'payment_id': payment.id,
            'transaction_id': payment.transaction_id,
            'provider': 'SANDBOX',
            'gateway_order_id': gateway_order_id,
            'amount': float(booking.total_amount),
            'currency': currency,
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
            message=f'Your payment for booking {booking.booking_code} was successful. Your reservation for {booking.car.display_name} is confirmed!',
            type='PAYMENT'
        )
        return payment
