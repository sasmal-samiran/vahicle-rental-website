from rest_framework import generics, viewsets, permissions, status, parsers
from rest_framework.decorators import action
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
from .services import VehicleService, CarSearchService
from apps.analytics.services import RecommendationService
from apps.bookings.models import Booking
from apps.analytics.models import SearchLog

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class CarListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CarListSerializer
    pagination_class = None
    filterset_class = CarFilter
    search_fields = ['brand', 'model', 'category__name', 'location__city', 'location__name', 'description']
    ordering_fields = ['price_per_day', 'year', 'created_at']

    def get_queryset(self):
        queryset = Car.objects.select_related('category', 'location').prefetch_related('images', 'reviews')
        # Public view excludes INACTIVE cars, showing AVAILABLE, RENTED, and MAINTENANCE cars
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.exclude(status='INACTIVE')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        search_query = request.query_params.get('search', '').strip()
        ordering_param = request.query_params.get('ordering', '').strip()

        # Fallback mechanism: If search query yielded no results, invoke CarSearchService fallback
        if search_query and not queryset.exists():
            search_service = CarSearchService()
            fallback_qs = search_service.get_fallback_matches(
                query=search_query,
                base_queryset=self.get_queryset()
            )
            if fallback_qs.exists():
                queryset = fallback_qs

        # Default to AI Recommended ranking if no manual sorting or search query is specified
        car_list = None
        if not ordering_param and not search_query and queryset.exists():
            service = RecommendationService()
            recommended_cars = service.get_recommendations_for_user(request.user, limit=200)
            rec_id_order = {car.id: idx for idx, car in enumerate(recommended_cars)}

            car_list = list(queryset)
            car_list.sort(key=lambda c: rec_id_order.get(c.id, 9999))
            serializer = self.get_serializer(car_list, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        # Search Logging: Write to SearchLog on every search or filter query
        query_text = search_query or ''
        active_filters = {}
        for key in ['category', 'status', 'max_price', 'transmission', 'fuel_type', 'seats', 'location_id', 'pickup_date', 'return_date']:
            val = request.query_params.get(key)
            if val:
                active_filters[key] = val

        search_log_id = None
        if query_text or active_filters:
            session_id = request.session.session_key
            if not session_id:
                try:
                    request.session.save()
                    session_id = request.session.session_key
                except Exception:
                    session_id = None

            try:
                res_count = len(car_list) if car_list is not None else (len(queryset) if isinstance(queryset, list) else queryset.count())
                log_entry = SearchLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    query=query_text,
                    filters=active_filters,
                    results_count=res_count,
                    clicked_car=None,  # Only added when details button is clicked!
                    session_id=session_id
                )
                search_log_id = log_entry.id
            except Exception as e:
                print(f"[SearchLog Error] {e}")

        response = Response(serializer.data)
        if search_log_id:
            response['X-Search-Log-Id'] = str(search_log_id)
        return response

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
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    pagination_class = None
    queryset = Car.objects.all().order_by('-id')
    serializer_class = CarListSerializer
    filterset_class = CarFilter
    search_fields = ['brand', 'model', 'license_plate', 'category__name', 'location__name']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return CarDetailSerializer
        return CarListSerializer

    def perform_create(self, serializer):
        car = serializer.save()
        self._handle_gallery_uploads(car)

    def perform_update(self, serializer):
        car = serializer.save()
        self._handle_gallery_uploads(car)

    def _handle_gallery_uploads(self, car):
        # Handle multiple uploaded gallery images from form-data
        gallery_files = self.request.FILES.getlist('gallery_images')
        view_types = self.request.data.getlist('gallery_view_types') if hasattr(self.request.data, 'getlist') else []
        captions = self.request.data.getlist('gallery_captions') if hasattr(self.request.data, 'getlist') else []
        VehicleService.handle_gallery_uploads(car, gallery_files, view_types, captions)

    @action(detail=True, methods=['delete'], url_path='gallery/(?P<image_id>[0-9]+)')
    def delete_gallery_image(self, request, pk=None, image_id=None):
        car = self.get_object()
        try:
            from utils.supabase_storage import SupabaseStorageService
            image = car.images.get(pk=image_id)
            if image.image_path:
                SupabaseStorageService.delete_gallery_image(image.image_path)
            image.delete()
            return Response({'detail': 'Image removed successfully.'}, status=status.HTTP_200_OK)
        except CarImage.DoesNotExist:
            return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)

