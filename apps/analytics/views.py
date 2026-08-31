from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.vehicles.models import Car, Category
from apps.bookings.models import Booking
from apps.users.models import User
from apps.payments.models import Payment
from apps.vehicles.serializers import CarListSerializer
from .services import RecommendationService, AnalyticsService
from .models import SearchLog, RecommendationClick, CarPopularityMetrics

class AdminDashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_cars = Car.objects.count()
        available_cars = Car.objects.filter(status='AVAILABLE').count()
        rented_cars = Car.objects.filter(status='RENTED').count()
        maintenance_cars = Car.objects.filter(status='MAINTENANCE').count()

        utilization_rate = round((rented_cars / total_cars * 100), 1) if total_cars > 0 else 0.0

        total_bookings = Booking.objects.count()
        active_rentals = Booking.objects.filter(status='ONGOING').count()
        confirmed_bookings = Booking.objects.filter(status='CONFIRMED').count()
        completed_bookings = Booking.objects.filter(status='COMPLETED').count()
        cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()

        total_revenue_aggr = Booking.objects.filter(payment_status='PAID').aggregate(Sum('total_amount'))['total_amount__sum']
        total_revenue = float(total_revenue_aggr) if total_revenue_aggr else 0.0

        total_customers = User.objects.filter(role='CUSTOMER').count()

        # Monthly Revenue breakdown (Last 6 months)
        now = timezone.now()
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=i*30)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Rough next month
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year+1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month+1)

            month_label = month_start.strftime('%b %Y')
            month_rev = Booking.objects.filter(
                payment_status='PAID',
                created_at__gte=month_start,
                created_at__lt=next_month
            ).aggregate(Sum('total_amount'))['total_amount__sum']
            
            month_count = Booking.objects.filter(
                created_at__gte=month_start,
                created_at__lt=next_month
            ).count()

            monthly_data.append({
                'month': month_label,
                'revenue': float(month_rev) if month_rev else 0.0,
                'bookings': month_count
            })

        # Category Breakdown
        categories = Category.objects.annotate(
            total_vehicles=Count('cars'),
            total_rentals=Count('cars__bookings')
        )
        category_breakdown = [
            {
                'name': cat.name,
                'vehicles': cat.total_vehicles,
                'rentals': cat.total_rentals
            }
            for cat in categories
        ]

        # Recent Bookings Feed
        recent_bookings = Booking.objects.select_related('customer', 'car').order_by('-created_at')[:10]
        recent_list = [
            {
                'id': b.id,
                'code': b.booking_code,
                'customer': b.customer.get_full_name() or b.customer.username,
                'car': b.car.display_name,
                'start_date': b.start_date.strftime('%Y-%m-%d'),
                'end_date': b.end_date.strftime('%Y-%m-%d'),
                'total_amount': float(b.total_amount),
                'status': b.status,
                'payment_status': b.payment_status,
                'created_at': b.created_at.strftime('%b %d, %H:%M')
            }
            for b in recent_bookings
        ]

        return Response({
            'kpis': {
                'total_revenue': total_revenue,
                'total_bookings': total_bookings,
                'active_rentals': active_rentals,
                'confirmed_bookings': confirmed_bookings,
                'completed_bookings': completed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'fleet_size': total_cars,
                'available_cars': available_cars,
                'rented_cars': rented_cars,
                'maintenance_cars': maintenance_cars,
                'utilization_rate': utilization_rate,
                'total_customers': total_customers,
            },
            'charts': {
                'monthly_revenue': monthly_data,
                'category_breakdown': category_breakdown,
                'status_distribution': {
                    'CONFIRMED': confirmed_bookings,
                    'ONGOING': active_rentals,
                    'COMPLETED': completed_bookings,
                    'CANCELLED': cancelled_bookings,
                    'PENDING': Booking.objects.filter(status='PENDING').count(),
                }
            },
            'recent_bookings': recent_list
        })


# ============================================================================
# Recommendation Engine Views
# ============================================================================

class PersonalizedRecommendationsView(APIView):
    """
    Returns AI-powered personalized car recommendations tailored to user's
    past bookings, preferred categories, price bracket, and transmission/fuel choices.
    Gracefully falls back to popular cars for unauthenticated guest visitors.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        service = RecommendationService()
        cars = service.get_recommendations_for_user(request.user, limit=limit)
        serializer = CarListSerializer(cars, many=True, context={'request': request})
        return Response({
            'status': 'success',
            'type': 'personalized' if request.user.is_authenticated else 'popular_fallback',
            'count': len(cars),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class SimilarCarsRecommendationsView(APIView):
    """
    Returns content-based similar vehicles based on category, brand, price tier,
    transmission, fuel type, seating capacity, model year, and rating.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, car_id=None, pk=None):
        target_id = car_id or pk or request.query_params.get('car_id')
        if not target_id:
            return Response({'error': 'car_id parameter or path variable is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_car = Car.objects.select_related('category', 'location').get(pk=target_id)
        except Car.DoesNotExist:
            return Response({'error': f'Car with ID {target_id} was not found.'}, status=status.HTTP_404_NOT_FOUND)

        limit = int(request.query_params.get('limit', 5))
        service = RecommendationService()
        similar_cars = service.get_similar_cars(target_car, limit=limit)
        serializer = CarListSerializer(similar_cars, many=True, context={'request': request})

        return Response({
            'status': 'success',
            'type': 'similar',
            'target_car': {
                'id': target_car.id,
                'name': target_car.display_name,
                'category': target_car.category.name if target_car.category else None,
                'price_per_day': float(target_car.price_per_day),
            },
            'count': len(similar_cars),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class PopularCarsRecommendationsView(APIView):
    """
    Returns top popular cars based on booking volume and high customer satisfaction ratings.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 30))
        service = RecommendationService()
        cars = service.get_popular_cars(limit=limit, time_range_days=days)
        serializer = CarListSerializer(cars, many=True, context={'request': request})

        return Response({
            'status': 'success',
            'type': 'popular',
            'time_range_days': days,
            'count': len(cars),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class TrendingCarsRecommendationsView(APIView):
    """
    Returns trending cars experiencing a recent spike in bookings (week-over-week growth).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        service = RecommendationService()
        cars = service.get_trending_cars(limit=limit)
        serializer = CarListSerializer(cars, many=True, context={'request': request})

        return Response({
            'status': 'success',
            'type': 'trending',
            'count': len(cars),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class ContextRecommendationsView(APIView):
    """
    Returns context-aware recommendations matching trip requirements
    (e.g., trip_type='family', 'business', 'adventure', passenger count, budget).
    Supports both GET query parameters and POST JSON request body.
    """
    permission_classes = [permissions.AllowAny]

    def _process_recommendations(self, request, data):
        trip_type = data.get('trip_type', 'family')
        try:
            passengers = int(data.get('passengers', 2))
        except (ValueError, TypeError):
            passengers = 2

        budget_raw = data.get('budget')
        budget = None
        if budget_raw is not None:
            try:
                budget = float(budget_raw)
            except (ValueError, TypeError):
                budget = None

        try:
            limit = int(data.get('limit', 10))
        except (ValueError, TypeError):
            limit = 10

        context = {
            'trip_type': trip_type,
            'passengers': passengers,
            'budget': budget
        }

        service = RecommendationService()
        cars = service.get_recommendations_by_context(context, limit=limit)
        serializer = CarListSerializer(cars, many=True, context={'request': request})

        return Response({
            'status': 'success',
            'type': 'context_aware',
            'context': context,
            'count': len(cars),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    def get(self, request):
        return self._process_recommendations(request, request.query_params)

    def post(self, request):
        return self._process_recommendations(request, request.data)


# ============================================================================
# Search Logging & Recommendation Click Tracking Views
# ============================================================================

class TrackClickView(APIView):
    """
    Tracks clicks and conversions for recommendations and searches.
    1. If recommendation_type or car_id is provided, creates/updates RecommendationClick.
    2. If details button is clicked for a car from search, records clicked_car on the SearchLog!
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        car_id = data.get('car_id')
        rec_type = data.get('recommendation_type', 'similar')
        try:
            position = int(data.get('position', 1))
        except (ValueError, TypeError):
            position = 1

        clicked = bool(data.get('clicked', True))
        booked = bool(data.get('booked', False))
        search_log_id = data.get('search_log_id')
        click_id = data.get('recommendation_click_id')

        car = None
        if car_id:
            try:
                car = Car.objects.get(pk=car_id)
            except Car.DoesNotExist:
                return Response({'error': f'Car with ID {car_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Update existing RecommendationClick if click_id is passed (e.g. marking booked=True upon booking)
        rec_click = None
        if click_id:
            try:
                rec_click = RecommendationClick.objects.get(pk=click_id)
                if booked:
                    rec_click.booked = True
                if clicked:
                    rec_click.clicked = True
                rec_click.save()
            except RecommendationClick.DoesNotExist:
                pass
        elif car and rec_type:
            rec_click = RecommendationClick.objects.create(
                user=request.user if request.user.is_authenticated else None,
                car=car,
                recommendation_type=rec_type,
                position=position,
                clicked=clicked,
                booked=booked
            )

        # 2. Update SearchLog clicked_car ONLY when details button is clicked
        updated_search_log = None
        if car:
            if search_log_id:
                try:
                    s_log = SearchLog.objects.get(pk=search_log_id)
                    s_log.clicked_car = car
                    s_log.save(update_fields=['clicked_car'])
                    updated_search_log = s_log
                except SearchLog.DoesNotExist:
                    pass

            # If no explicit search_log_id was sent, link to the most recent unclicked SearchLog for this user/session
            if not updated_search_log:
                recent_qs = SearchLog.objects.filter(clicked_car__isnull=True)
                if request.user.is_authenticated:
                    recent_qs = recent_qs.filter(user=request.user)
                elif request.session.session_key:
                    recent_qs = recent_qs.filter(session_id=request.session.session_key)
                else:
                    recent_qs = None

                if recent_qs is not None and recent_qs.exists():
                    recent_log = recent_qs.order_by('-created_at').first()
                    if recent_log:
                        recent_log.clicked_car = car
                        recent_log.save(update_fields=['clicked_car'])
                        updated_search_log = recent_log

        return Response({
            'status': 'success',
            'message': 'Click tracked successfully.',
            'recommendation_click_id': rec_click.id if rec_click else None,
            'search_log_id': updated_search_log.id if updated_search_log else None,
            'clicked_car_id': car.id if car else None
        }, status=status.HTTP_200_OK)


class TrendingSearchesView(APIView):
    """
    Returns high-frequency trending search keywords and filter trends.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 8))
        except (ValueError, TypeError):
            limit = 8

        trending = AnalyticsService.get_trending_searches(limit=limit)
        return Response({
            'status': 'success',
            'count': len(trending),
            'results': trending
        }, status=status.HTTP_200_OK)


class AdminRecommendationPerformanceView(APIView):
    """
    Returns AI recommendation conversion rate, CTR, and algorithm breakdown.
    Also recalculates and refreshes CarPopularityMetrics.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Refresh popularity metrics across all fleet
        AnalyticsService.update_all_car_metrics()
        perf = AnalyticsService.get_recommendation_performance()
        return Response({
            'status': 'success',
            'performance': perf
        }, status=status.HTTP_200_OK)



