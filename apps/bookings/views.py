from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from apps.vehicles.models import Car, Location
from .models import Booking, Coupon
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    PriceQuoteRequestSerializer,
    CancelBookingSerializer,
    CouponSerializer
)
from .services import PricingService, BookingService

class CalculateQuoteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PriceQuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            car = Car.objects.get(pk=data['car_id'])
        except Car.DoesNotExist:
            return Response({'error': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)

        if data['end_date'] <= data['start_date']:
            return Response({'error': 'Return date must be after pickup date.'}, status=status.HTTP_400_BAD_REQUEST)

        quote = PricingService.calculate_quote(
            car=car,
            start_datetime=data['start_date'],
            end_datetime=data['end_date'],
            addon_keys=data.get('addons', []),
            insurance_plan=data.get('insurance_plan', 'NONE'),
            coupon_code=data.get('coupon_code', '')
        )
        quote.pop('coupon_object', None)
        return Response(quote, status=status.HTTP_200_OK)

class ValidateCouponView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('coupon_code', '').strip()
        booking_amount = float(request.data.get('amount', 0))

        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            now = timezone.now()
            if (coupon.valid_from and coupon.valid_from > now) or (coupon.valid_until and coupon.valid_until < now):
                return Response({'error': 'This promo code has expired.'}, status=status.HTTP_400_BAD_REQUEST)

            if booking_amount < float(coupon.min_booking_amount):
                return Response({
                    'error': f'Minimum rental amount for this coupon is '
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'valid': True,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'message': f'Coupon {coupon.code} applied successfully!'
            })
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid promo coupon code.'}, status=status.HTTP_404_NOT_FOUND)

class CustomerBookingListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')
        queryset = Booking.objects.filter(customer=request.user).select_related('car', 'pickup_location', 'return_location')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            car = Car.objects.get(pk=data['car_id'])
            pickup = Location.objects.get(pk=data['pickup_location_id'])
            dropoff = Location.objects.get(pk=data['dropoff_location_id'] if 'dropoff_location_id' in data else data['return_location_id'])
        except (Car.DoesNotExist, Location.DoesNotExist) as e:
            return Response({'error': 'Invalid car or location selected.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            booking = BookingService.create_booking(
                customer=request.user,
                car=car,
                pickup_location=pickup,
                return_location=dropoff,
                start_datetime=data['start_date'],
                end_datetime=data['end_date'],
                insurance_plan=data.get('insurance_plan', 'NONE'),
                addon_keys=data.get('addons', []),
                coupon_code=data.get('coupon_code'),
                driver_data={
                    'name': data['driver_name'],
                    'phone': data['driver_phone'],
                    'email': data.get('driver_email'),
                    'license': data.get('driver_license'),
                },
                special_requests=data.get('special_requests', '')
            )
            return Response(BookingDetailSerializer(booking).data, status=status.HTTP_201_CREATED)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

class BookingDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingDetailSerializer
    lookup_field = 'booking_code'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer=self.request.user)

class CancelBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_code):
        try:
            booking = Booking.objects.get(booking_code=booking_code)
            if not request.user.is_staff and booking.customer != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            serializer = CancelBookingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            updated = BookingService.cancel_booking(
                booking=booking,
                user=request.user,
                reason=serializer.validated_data.get('reason', 'Customer requested cancellation')
            )
            return Response({
                'detail': 'Booking successfully cancelled.',
                'booking': BookingDetailSerializer(updated).data
            })
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

class AdminBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Booking.objects.all().select_related('car', 'customer', 'pickup_location', 'return_location').order_by('-created_at')
    serializer_class = BookingDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(booking_code__icontains=search) |
                Q(driver_name__icontains=search) |
                Q(car__brand__icontains=search) |
                Q(car__model__icontains=search)
            )
        return qs

    def partial_update(self, request, *args, **kwargs):
        booking = self.get_object()
        new_status = request.data.get('status')
        if new_status and new_status != booking.status:
            booking.status = new_status
            if new_status == 'ONGOING':
                booking.car.status = 'RENTED'
                booking.car.save(update_fields=['status'])
            elif new_status == 'COMPLETED':
                booking.car.status = 'AVAILABLE'
                booking.car.save(update_fields=['status'])
            booking.save()
        return Response(BookingDetailSerializer(booking).data)
