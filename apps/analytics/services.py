# analytics/services.py
from django.db.models import Q, Avg, Count, F, FloatField, Case, When, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
import numpy as np
from typing import List, Dict, Any, Optional
from apps.vehicles.models import Car, Category
from apps.bookings.models import Booking
from apps.reviews.models import Review
from apps.users.models import User

class RecommendationService:
    """AI-powered recommendation engine"""
    
    def __init__(self):
        self.available_cars = Car.objects.filter(status='AVAILABLE').select_related('category', 'location').prefetch_related('images', 'reviews')
    
    def get_recommendations_for_user(self, user: User, limit: int = 10) -> List[Car]:
        """
        Get personalized recommendations for a user
        """
        if not user.is_authenticated:
            return self.get_popular_cars(limit)
        
        # Get user preferences
        user_preferences = self._get_user_preferences(user)
        
        # Calculate scores for all available cars
        scored_cars = []
        for car in self.available_cars:
            score = self._calculate_personal_score(car, user_preferences)
            scored_cars.append((car, score))
        
        # Sort by score 
        scored_cars.sort(key=lambda x: x[1], reverse=True)
        return [car for car, score in scored_cars[:limit]]
    
    def get_similar_cars(self, car: Car, limit: int = 5) -> List[Car]:
        """
        Get cars similar to the given car (content-based filtering)
        """
        # Calculate similarity scores
        similar_cars = []
        for candidate in self.available_cars.exclude(id=car.id):
            similarity = self._calculate_similarity(car, candidate)
            similar_cars.append((candidate, similarity))
        
        similar_cars.sort(key=lambda x: x[1], reverse=True)
        return [c for c, s in similar_cars[:limit]]
    
    def get_popular_cars(self, limit: int = 10, time_range_days: int = 30) -> List[Car]:
        """
        Get popular cars based on bookings and ratings
        """
        cutoff_date = timezone.now() - timedelta(days=time_range_days)
        
        popular_cars = self.available_cars.annotate(
            booking_count=Count('bookings', filter=Q(bookings__created_at__gte=cutoff_date)),
            avg_rating=Coalesce(Avg('reviews__rating', filter=Q(reviews__is_approved=True)), Value(4.5), output_field=FloatField()),
            calculated_score=( 
                F('booking_count') * 0.6 + F('avg_rating') * 0.4
            )
        ).order_by('-calculated_score')[:limit]
        
        results = list(popular_cars)
        if not results:
            results = list(self.available_cars.order_by('-created_at')[:limit])
        return results
    
    def get_trending_cars(self, limit: int = 10) -> List[Car]:
        """
        Get trending cars (recent spike in bookings)
        """
        recent_start = timezone.now() - timedelta(days=7)
        previous_start = timezone.now() - timedelta(days=14)
        previous_end = timezone.now() - timedelta(days=7)
        
        trending_cars = self.available_cars.annotate(
            recent_bookings=Count('bookings', filter=Q(bookings__created_at__gte=recent_start)),
            previous_bookings=Count('bookings', filter=Q(
                bookings__created_at__gte=previous_start,
                bookings__created_at__lt=previous_end
            )),
            trend_score=F('recent_bookings') - F('previous_bookings')
        ).filter(
            trend_score__gt=0
        ).order_by('-trend_score')[:limit]
        
        results = list(trending_cars)
        if not results:
            results = self.get_popular_cars(limit=limit, time_range_days=14)
        return results
    
    def get_recommendations_by_context(self, context: Dict, limit: int = 10) -> List[Car]:
        """
        Context-aware recommendations (e.g., family trip, business trip)
        """
        scored_cars = []
        
        for car in self.available_cars:
            score = self._calculate_context_score(car, context)
            scored_cars.append((car, score))
        
        scored_cars.sort(key=lambda x: x[1], reverse=True)
        return [car for car, score in scored_cars[:limit]]
    
    def _get_user_preferences(self, user: User) -> Dict:
        """
        Extract user preferences from:
        1. Past confirmed & completed bookings (High Weight)
        2. Recent SearchLog queries, applied filters, and clicked cars (Medium-High Weight)
        3. RecommendationClick interactions (Immediate Interest Boost)
        """
        from .models import SearchLog, RecommendationClick

        preferences = {
            'preferred_categories': [],
            'preferred_brands': [],
            'avg_price_range': None,
            'preferred_transmission': None,
            'preferred_fuel_type': None,
            'min_seats': None,
            'preferred_car_ids': set()
        }

        category_counts = {}
        brand_counts = {}
        transmission_counts = {}
        fuel_counts = {}
        prices = []
        max_seats = 0

        # 1. Extract from Booking History (Weight: 3x per booking)
        user_bookings = Booking.objects.filter(
            customer=user
        ).filter(
            Q(status='COMPLETED') | Q(status='CONFIRMED') | Q(status='ONGOING')
        ).select_related('car', 'car__category')

        if user_bookings.exists():
            for booking in user_bookings:
                car = booking.car
                if car.category:
                    category_counts[car.category.id] = category_counts.get(car.category.id, 0) + 3
                brand_counts[car.brand] = brand_counts.get(car.brand, 0) + 3
                transmission_counts[car.transmission] = transmission_counts.get(car.transmission, 0) + 3
                fuel_counts[car.fuel_type] = fuel_counts.get(car.fuel_type, 0) + 3
                prices.append(float(car.price_per_day))
                max_seats = max(max_seats, car.seats)
                preferences['preferred_car_ids'].add(car.id)

        # 2. Extract from SearchLog (Queries, Filters, and Clicked Cars) (Weight: 1.5x)
        recent_searches = SearchLog.objects.filter(user=user).select_related('clicked_car', 'clicked_car__category').order_by('-created_at')[:25]
        for s_log in recent_searches:
            # If user clicked on a car details from search
            if s_log.clicked_car:
                c_car = s_log.clicked_car
                preferences['preferred_car_ids'].add(c_car.id)
                if c_car.category:
                    category_counts[c_car.category.id] = category_counts.get(c_car.category.id, 0) + 2
                brand_counts[c_car.brand] = brand_counts.get(c_car.brand, 0) + 2
                transmission_counts[c_car.transmission] = transmission_counts.get(c_car.transmission, 0) + 2
                fuel_counts[c_car.fuel_type] = fuel_counts.get(c_car.fuel_type, 0) + 2
                prices.append(float(c_car.price_per_day))

            # Extract from active search filters
            if isinstance(s_log.filters, dict):
                f_trans = s_log.filters.get('transmission')
                if f_trans:
                    transmission_counts[f_trans] = transmission_counts.get(f_trans, 0) + 1
                f_fuel = s_log.filters.get('fuel_type')
                if f_fuel:
                    fuel_counts[f_fuel] = fuel_counts.get(f_fuel, 0) + 1
                f_seats = s_log.filters.get('seats')
                if f_seats:
                    try:
                        max_seats = max(max_seats, int(f_seats))
                    except (ValueError, TypeError):
                        pass
                f_price = s_log.filters.get('max_price')
                if f_price:
                    try:
                        prices.append(float(f_price))
                    except (ValueError, TypeError):
                        pass

            # Extract brand/category from raw search query string
            if s_log.query:
                q_lower = s_log.query.lower()
                for brand in ['audi', 'bmw', 'mercedes', 'tesla', 'porsche', 'toyota', 'hyundai', 'ford', 'tata', 'lamborghini', 'rolls-royce']:
                    if brand in q_lower:
                        brand_title = brand.title()
                        brand_counts[brand_title] = brand_counts.get(brand_title, 0) + 2

        # 3. Extract from RecommendationClick Interactions (Weight: 2x)
        recent_clicks = RecommendationClick.objects.filter(user=user, clicked=True).select_related('car', 'car__category').order_by('-created_at')[:20]
        for r_click in recent_clicks:
            rc_car = r_click.car
            preferences['preferred_car_ids'].add(rc_car.id)
            if rc_car.category:
                category_counts[rc_car.category.id] = category_counts.get(rc_car.category.id, 0) + 2
            brand_counts[rc_car.brand] = brand_counts.get(rc_car.brand, 0) + 2
            transmission_counts[rc_car.transmission] = transmission_counts.get(rc_car.transmission, 0) + 1
            fuel_counts[rc_car.fuel_type] = fuel_counts.get(rc_car.fuel_type, 0) + 1
            prices.append(float(rc_car.price_per_day))

        # Aggregate Top Preferences
        if category_counts:
            preferences['preferred_categories'] = sorted(
                category_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
        if brand_counts:
            preferences['preferred_brands'] = sorted(
                brand_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
        if transmission_counts:
            preferences['preferred_transmission'] = max(
                transmission_counts.items(), key=lambda x: x[1]
            )[0]
        if fuel_counts:
            preferences['preferred_fuel_type'] = max(
                fuel_counts.items(), key=lambda x: x[1]
            )[0]

        if prices:
            avg_price = float(np.mean(prices))
            std_price = float(np.std(prices)) if len(prices) > 1 else avg_price * 0.25
            preferences['avg_price_range'] = (max(0, avg_price - std_price), avg_price + std_price)

        preferences['min_seats'] = max_seats
        return preferences

    def _calculate_personal_score(self, car: Car, preferences: Dict) -> float:
        """
        Calculate personalized score for a car based on blended user preferences
        """
        score = 0.0

        # Base popularity score
        score += car.popularity_score * 0.2

        # Direct clicked/viewed car boost (implicit high interest!)
        if car.id in preferences.get('preferred_car_ids', set()):
            score += 3.5

        # Category preference
        if car.category and car.category.id in [c[0] for c in preferences['preferred_categories']]:
            score += 3.0

        # Brand preference
        if car.brand in [b[0] for b in preferences['preferred_brands']]:
            score += 2.5

        # Price preference
        if preferences['avg_price_range']:
            min_price, max_price = preferences['avg_price_range']
            if min_price <= float(car.price_per_day) <= max_price:
                score += 2.0
            elif float(car.price_per_day) < min_price:
                score += 1.0  # Slightly cheaper than usual budget

        # Transmission preference
        if preferences['preferred_transmission'] and car.transmission == preferences['preferred_transmission']:
            score += 1.5

        # Fuel type preference
        if preferences['preferred_fuel_type'] and car.fuel_type == preferences['preferred_fuel_type']:
            score += 1.5

        # Seats requirement
        if preferences['min_seats'] and car.seats >= preferences['min_seats']:
            score += 1.0

        # Rating boost
        if car.average_rating >= 4.5:
            score += 1.0

        return score
    
    def _calculate_similarity(self, car1: Car, car2: Car) -> float:
        """
        Calculate similarity between two cars using multiple features
        """
        similarity = 0.0
        
        # Category similarity
        if car1.category and car2.category and car1.category.id == car2.category.id:
            similarity += 3.0
        elif car1.category and car2.category:
            similarity += 1.0
        
        # Brand similarity
        if car1.brand == car2.brand:
            similarity += 2.5
        
        # Price similarity (closer prices = more similar)
        price_diff = abs(float(car1.price_per_day) - float(car2.price_per_day))
        if price_diff < 20:
            similarity += 2.0
        elif price_diff < 50:
            similarity += 1.0
        elif price_diff < 100:
            similarity += 0.5
        
        # Transmission similarity
        if car1.transmission == car2.transmission:
            similarity += 1.0
        
        # Fuel type similarity
        if car1.fuel_type == car2.fuel_type:
            similarity += 1.0
        
        # Seats similarity
        if abs(car1.seats - car2.seats) <= 1:
            similarity += 0.5
        
        # Year similarity
        if abs(car1.year - car2.year) <= 2:
            similarity += 0.5
        
        # Rating similarity
        if abs(car1.average_rating - car2.average_rating) < 0.5:
            similarity += 1.0
        
        return similarity
    
    def _calculate_context_score(self, car: Car, context: Dict) -> float:
        """
        Calculate score based on context (e.g., trip type, passengers, budget)
        """
        score = 0.0
        trip_type = context.get('trip_type', '').lower()
        passengers = context.get('passengers', 1)
        budget = context.get('budget', None)
        
        # Trip type specific scoring
        if trip_type == 'family':
            if car.seats >= passengers:
                score += 3.0
            if car.luggage_capacity >= 3:
                score += 2.0
            if car.fuel_type in ['HYBRID', 'ELECTRIC']:
                score += 1.0
        elif trip_type == 'business':
            if car.transmission == 'AUTOMATIC':
                score += 2.0
            if car.category and 'luxury' in car.category.name.lower():
                score += 3.0
            if car.power_hp > 200:
                score += 1.0
        elif trip_type == 'adventure':
            if car.transmission == 'MANUAL':
                score += 1.0
            if car.fuel_type in ['DIESEL', 'HYBRID']:
                score += 2.0
            if car.year >= 2020:
                score += 1.0
        
        # Budget constraint
        if budget:
            if float(car.price_per_day) <= budget:
                score += 2.0
            elif float(car.price_per_day) <= budget * 1.2:
                score += 1.0
        
        # Passenger requirement
        if car.seats >= passengers:
            score += 2.0

        return score


class AnalyticsService:
    """
    Analytics operations for popularity metrics, AI recommendation conversion (CTR/CVR),
    and high-demand search intelligence.
    """

    @staticmethod
    def update_all_car_metrics():
        """
        Computes and caches CarPopularityMetrics for every car in the fleet.
        """
        from .models import CarPopularityMetrics, RecommendationClick
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        cars = Car.objects.all()
        metrics_list = []

        for car in cars:
            views_7 = RecommendationClick.objects.filter(car=car, clicked=True, created_at__gte=seven_days_ago).count()
            views_30 = RecommendationClick.objects.filter(car=car, clicked=True, created_at__gte=thirty_days_ago).count()
            bookings_30 = Booking.objects.filter(car=car, status__in=['CONFIRMED', 'COMPLETED', 'ONGOING'], created_at__gte=thirty_days_ago).count()

            cvr = round((bookings_30 / views_30 * 100), 2) if views_30 > 0 else 0.0
            avg_daily = round(views_30 / 30.0, 2)

            metrics, _ = CarPopularityMetrics.objects.update_or_create(
                car=car,
                defaults={
                    'views_last_7_days': views_7,
                    'views_last_30_days': views_30,
                    'bookings_last_30_days': bookings_30,
                    'booking_conversion_rate': cvr,
                    'average_daily_views': avg_daily
                }
            )
            metrics_list.append(metrics)

        return metrics_list

    @staticmethod
    def get_recommendation_performance():
        """
        Calculates CTR, CVR, and booking conversion breakdown per recommendation algorithm.
        """
        from .models import RecommendationClick
        rec_types = ['personalized', 'similar', 'trending', 'popular', 'context', 'search_details']
        breakdown = []

        total_clicks = 0
        total_bookings = 0

        for r_type in rec_types:
            clicks = RecommendationClick.objects.filter(recommendation_type=r_type, clicked=True).count()
            bookings = RecommendationClick.objects.filter(recommendation_type=r_type, booked=True).count()
            cvr = round((bookings / clicks * 100), 1) if clicks > 0 else 0.0

            total_clicks += clicks
            total_bookings += bookings

            breakdown.append({
                'type': r_type,
                'display_name': r_type.replace('_', ' ').title(),
                'clicks': clicks,
                'bookings': bookings,
                'cvr_percent': cvr
            })

        overall_cvr = round((total_bookings / total_clicks * 100), 1) if total_clicks > 0 else 0.0

        return {
            'total_recommendation_clicks': total_clicks,
            'total_recommendation_bookings': total_bookings,
            'overall_cvr_percent': overall_cvr,
            'breakdown': breakdown
        }

    @staticmethod
    def get_trending_searches(limit: int = 8):
        """
        Aggregates popular searches from:
        1. Frequently selected filter parameters (categories, fuel types, transmission, seats).
        2. Free-text search queries (if typed).
        3. Most frequently inspected/clicked vehicle models.
        """
        from .models import SearchLog, RecommendationClick
        from django.db.models import Count

        counts = {}

        # 1. Aggregate non-empty text queries
        query_qs = SearchLog.objects.exclude(query='').values('query').annotate(total=Count('id')).order_by('-total')[:10]
        for q in query_qs:
            text = q['query'].strip().title()
            if text and len(text) >= 3:
                counts[text] = counts.get(text, 0) + q['total'] * 2

        # 2. Aggregate active filter selections from SearchLog
        all_logs = SearchLog.objects.exclude(filters={}).order_by('-created_at')[:100]
        for s in all_logs:
            if isinstance(s.filters, dict):
                cat = s.filters.get('category')
                if cat:
                    label = cat.replace('_', ' ').title()
                    counts[label] = counts.get(label, 0) + 1

                fuel = s.filters.get('fuel_type')
                if fuel:
                    label = f"{fuel.title()} Fleet" if fuel in ['ELECTRIC', 'HYBRID'] else fuel.title()
                    counts[label] = counts.get(label, 0) + 1

                trans = s.filters.get('transmission')
                if trans:
                    label = f"{trans.title()} Transmission"
                    counts[label] = counts.get(label, 0) + 1

                seats = s.filters.get('seats')
                if seats and str(seats) in ['6', '7', '8']:
                    label = "7+ Seater SUV"
                    counts[label] = counts.get(label, 0) + 1

        # 3. Aggregate top clicked cars
        clicked_qs = RecommendationClick.objects.filter(clicked=True).values('car__brand', 'car__model').annotate(total=Count('id')).order_by('-total')[:5]
        for c in clicked_qs:
            label = f"{c['car__brand']} {c['car__model']}"
            counts[label] = counts.get(label, 0) + c['total'] * 2

        # Sort combined search trends by count
        sorted_trends = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        trending_queries = [{'query': term, 'count': count} for term, count in sorted_trends]

        # Fallback defaults if search log is still growing
        if len(trending_queries) < 4:
            defaults = ['Electric Fleet', 'Luxury & Exotic', 'Audi A4', 'Automatic', '7+ Seater SUV', 'Sports Coupes']
            existing = {q['query'].lower() for q in trending_queries}
            for d in defaults:
                if d.lower() not in existing:
                    trending_queries.append({'query': d, 'count': 1})
                if len(trending_queries) >= limit:
                    break

        return trending_queries
