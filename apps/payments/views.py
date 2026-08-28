import secrets
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.bookings.models import Booking
from .models import Payment
from .serializers import (
    PaymentSerializer,
    InitiatePaymentSerializer,
    VerifyRazorpaySerializer,
    VerifyStripeSerializer,
    MockCheckoutSerializer
)
from .services import PaymentService

class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            booking = Booking.objects.get(booking_code=data['booking_code'])
            if not request.user.is_staff and booking.customer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
            if booking.payment_status == 'PAID':
                return Response({'error': 'This booking has already been paid.'}, status=status.HTTP_400_BAD_REQUEST)

            res = PaymentService.initiate_payment(
                booking=booking,
                provider=data.get('provider', 'SANDBOX'),
                currency=data.get('currency', 'INR')
            )
            return Response(res, status=status.HTTP_200_OK)

        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

class VerifyRazorpayView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifyRazorpaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payment = Payment.objects.get(pk=data['payment_id'])
            if not request.user.is_staff and payment.booking.customer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            payment = PaymentService.finalize_success(
                payment=payment,
                payment_method='RAZORPAY',
                gateway_payment_id=data['razorpay_payment_id'],
                signature=data.get('razorpay_signature')
            )
            return Response({
                'success': True,
                'detail': 'Payment verified and booking confirmed!',
                'payment': PaymentSerializer(payment).data
            })
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

class VerifyStripeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifyStripeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payment = Payment.objects.get(pk=data['payment_id'])
            if not request.user.is_staff and payment.booking.customer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            payment = PaymentService.finalize_success(
                payment=payment,
                payment_method='STRIPE_CARD',
                gateway_payment_id=data['payment_intent_id']
            )
            return Response({
                'success': True,
                'detail': 'Stripe payment verified and booking confirmed!',
                'payment': PaymentSerializer(payment).data
            })
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

class MockCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MockCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            booking = Booking.objects.get(booking_code=data['booking_code'])
            if not request.user.is_staff and booking.customer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            if booking.payment_status == 'PAID':
                return Response({'error': 'Booking is already paid.'}, status=status.HTTP_400_BAD_REQUEST)

            payment = Payment.objects.create(
                booking=booking,
                provider='SANDBOX',
                gateway_order_id='mock_ord_' + secrets.token_hex(4),
                amount=booking.total_amount,
                currency='INR',
                status='INITIATED'
            )

            p_method = data['payment_method'] + ' (Ending in ' + data['card_last_four'] + ')'
            payment = PaymentService.finalize_success(
                payment=payment,
                payment_method=p_method,
                gateway_payment_id='mock_pay_' + secrets.token_hex(6)
            )

            return Response({
                'success': True,
                'detail': 'Payment processed successfully in test sandbox!',
                'payment': PaymentSerializer(payment).data
            })
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

class AdminPaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all().select_related('booking__customer', 'booking__car').order_by('-created_at')
    search_fields = ['transaction_id', 'booking__booking_code', 'booking__customer__username']
    filterset_fields = ['status', 'provider']
