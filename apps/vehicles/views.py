from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils.dateparse import parse_datetime, parse_date
from .models import Category, Location, Car, CarImage
from .serializers import (
    CategorySerializer,
    LocationSerializer,
    CarListSerializer,
    CarDetailSerializer,
    CarImageSerializer
)
from .filters import CarFilter
from apps.bookings.models import Booking

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class CarListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CarListSerializer
    filterset_class = CarFilter
    search_fields = ['brand', 'model', 'category__name', 'location__city', 'location__name', 'description']
    ordering_fields = ['price_per_day', 'year', 'created_at']

    def get_queryset(self):
        queryset = Car.objects.select_related('category', 'location').prefetch_related('images', 'reviews')
        # If not admin, show only AVAILABLE cars by default (unless filtered)
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            if 'status' not in self.request.query_params:
                queryset = queryset.filter(status='AVAILABLE')
        return queryset

class CarDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CarDetailSerializer
    queryset = Car.objects.select_related('category', 'location').prefetch_related('images', 'reviews__customer')

class CheckCarAvailabilityView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        car_id = pk or request.data.get('car_id')
        pickup_str = request.data.get('pickup_date') or request.data.get('start_date')
        return_str = request.data.get('return_date') or request.data.get('end_date')

        if not pickup_str or not return_str:
            return Response(
                {'error': 'Both pickup_date and return_date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start = parse_datetime(pickup_str) or parse_date(pickup_str)
        end = parse_datetime(return_str) or parse_date(return_str)

        if not start or not end:
            return Response({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)

        if end <= start:
            return Response({'error': 'Return date must be after pickup date.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            car = Car.objects.get(pk=car_id)
        except Car.DoesNotExist:
            return Response({'error': 'Car not found.'}, status=status.HTTP_404_NOT_FOUND)

        if car.status != 'AVAILABLE':
            return Response({
                'is_available': False,
                'car_id': car.id,
                'reason': f'Vehicle is currently marked as {car.get_status_display()}.'
            })

        has_overlap = Booking.objects.filter(
            car=car,
            status__in=['CONFIRMED', 'ONGOING', 'PENDING'],
            start_date__lt=end,
            end_date__gt=start
        ).exists()

        return Response({
            'is_available': not has_overlap,
            'car_id': car.id,
            'car_name': car.display_name,
            'pickup_date': start,
            'return_date': end,
            'daily_rate': float(car.price_per_day),
            'reason': 'Available for selected dates.' if not has_overlap else 'Vehicle has an existing reservation during this timeframe.'
        })

class AdminCarViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Car.objects.all().order_by('-id')
    serializer_class = CarListSerializer
    filterset_class = CarFilter
    search_fields = ['brand', 'model', 'license_plate', 'category__name', 'location__name']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return CarDetailSerializer
        return CarListSerializer
