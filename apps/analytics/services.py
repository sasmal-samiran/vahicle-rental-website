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
        self.available_cars = Car.objects.filter(status='AVAILABLE')
    
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
            avg_rating=Coalesce(Avg('reviews__rating', filter=Q(reviews__is_approved=True)), Value(4.5)),
            calculated_score=( 
                F('booking_count') * 0.6 + F('avg_rating') * 0.4
            )
        ).order_by('-calculated_score')[:limit]
        
        return list(popular_cars)
    
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
        
        return list(trending_cars)
    
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
        Extract user preferences from booking history and reviews
        """
        preferences = {
            'preferred_categories': [],
            'preferred_brands': [],
            'avg_price_range': None,
            'preferred_transmission': None,
            'preferred_fuel_type': None,
            'min_seats': None
        }
        
        # Get user's booking history
        user_bookings = Booking.objects.filter(user=user, status='COMPLETED')
        
        if user_bookings.exists():
            # Preferred categories
            category_counts = {}
            brand_counts = {}
            transmission_counts = {}
            fuel_counts = {}
            prices = []
            max_seats = 0
            
            for booking in user_bookings:
                car = booking.car
                if car.category:
                    category_counts[car.category.id] = category_counts.get(car.category.id, 0) + 1
                brand_counts[car.brand] = brand_counts.get(car.brand, 0) + 1
                transmission_counts[car.transmission] = transmission_counts.get(car.transmission, 0) + 1
                fuel_counts[car.fuel_type] = fuel_counts.get(car.fuel_type, 0) + 1
                prices.append(float(car.price_per_day))
                max_seats = max(max_seats, car.seats)
            
            preferences['preferred_categories'] = sorted(
                category_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
            preferences['preferred_brands'] = sorted(
                brand_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
            preferences['preferred_transmission'] = max(
                transmission_counts.items(), key=lambda x: x[1]
            )[0] if transmission_counts else None
            preferences['preferred_fuel_type'] = max(
                fuel_counts.items(), key=lambda x: x[1]
            )[0] if fuel_counts else None
            
            if prices:
                avg_price = np.mean(prices)
                std_price = np.std(prices)
                preferences['avg_price_range'] = (avg_price - std_price, avg_price + std_price)
            
            preferences['min_seats'] = max_seats
        
        return preferences
    
    def _calculate_personal_score(self, car: Car, preferences: Dict) -> float:
        """
        Calculate personalized score for a car based on user preferences
        """
        score = 0.0
        
        # Base score
        score += car.popularity_score * 0.2
        
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
                score += 1.0  # Slightly cheaper than usual
        
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