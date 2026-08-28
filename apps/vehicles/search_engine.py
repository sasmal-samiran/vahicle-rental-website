from django.db.models import Q,F, Value, FloatField, Case, When, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
import re
from typing import List, Dict, Any, Optional
from .models import Car, Category


class CarSearchService:
    """Search Engine for cars..."""
    def __init__(self):
        self.queryset = Car.objects.select_related(
            'category', 'location'
        ).prefetch_related('images', 'reviews')

    def search(self, query: str = None, filters: Dict = None) -> List[Car]:
        queryset = self.queryset.filter(status='AVAILABLE')
        if query:
            queryset = self.full_text_search(queryset, query)
        if filters:
            queryset = self.apply_filters(queryset, filters)
        return queryset

    def full_text_search(self, queryset, query: str):
        query = query.strip().lower()
        # terms = re.split(r'\s+', query)
        terms = query.split()

        q_objects = Q()
        for term in terms:
            q_objects |= (
                Q(brand__icontains=term) |
                Q(model__icontains=term) |
                Q(year__icontains=term) |
                Q(category__name__icontains=term) |
                Q(location__city__icontains=term) |
                Q(features__icontains=term) |
                Q(search_keywords__icontains=term) |
                Q(description__icontains=term) |
                Q(transmission__icontains=term) |
                Q(fuel_type__icontains=term)
            )

        # for fuzzy matching 
        for term in terms:
            if len(term) > 3:
                fuzzy_pattern = term[:2] + term[2:-1] + term[-1]
                q_objects |= (
                    Q(brand__icontains=fuzzy_pattern) |
                    Q(model__icontains=fuzzy_pattern)
                )
        return queryset.filter(q_objects).distinct()
    def apply_filters(self, queryset, filters: Dict):
        if filters.get('price_range'):
            min_price, max_price = filters['price_range']
            queryset = queryset.filter(price_per_day__range=(min_price, max_price))
        if filters.get('seats'):
            queryset = queryset.filter(seats__gte=filters['seats'])
        if filters.get('transmission'):
            queryset = queryset.filter(transmission__iexact=filters['transmission'])
        
        if filters.get('fuel_type'):
            queryset = queryset.filter(fuel_type__iexact=filters['fuel_type'])
        
        if filters.get('year_range'):
            min_year, max_year = filters['year_range']
            queryset = queryset.filter(year__range=(min_year, max_year))
        
        if filters.get('location_city'):
            queryset = queryset.filter(location__city__iexact=filters['location_city'])
        
        return queryset
    def search_with_relevance(self, query: str) -> List[Dict]:
        cars = self.search(query=query)
        results = []
        for car in cars:
            relevance_score = self._calculate_relevance(car, query)
            results.append({
                'car': car,
                'relevance_score': relevance_score,
                'match_details': self._get_match_details(car, query)
            })
        # Sort by relevance score...
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    def _calculate_relevance(self, car: Car, query: str) -> float:
        score = 0.0
        query_terms = query.lower().split()
        
        car_text = f"{car.brand} {car.model} {car.year} {car.category.name if car.category else''}"
        car_text += f"{car.location.city if car.location else ''} {car.description or ''}"

        for term in query_terms:
            # exact brand match...
            if term == car.brand.lower():
                score += 10.0
            # exact model match...
            elif term == car.model.lower():
                score += 8.0
            # category match...
            elif car.category and term in car.category.name.lower():
                score += 6.0
            # partial match in description...
            elif term in car_text.lower():
                score += 3.0
            # fuzzy match...
            elif self._fuzzy_match(term, car_text):
                score += 1.5
        
        # Boost by popularity and rating
        score += car.popularity_score * 0.1
        if car.average_rating > 4.5:
            score += 2.0
        return score
    def _fuzzy_match(self, term: str, text: str) -> bool:
        if len(term) < 4:
            return False
        # Check for common typos
        for word in text.lower().split():
            if abs(len(term) - len(word)) <= 1:
                # Simple Levenshtein distance check
                if self._levenshtein_distance(term, word) <= 2:
                    return True
        return False
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    def _get_match_details(self, car: Car, query: str) -> List[str]:
        """Get details about what matched in the search"""
        matches = []
        query_lower = query.lower()
        
        if query_lower in car.brand.lower():
            matches.append(f"Brand: {car.brand}")
        if query_lower in car.model.lower():
            matches.append(f"Model: {car.model}")
        if car.category and query_lower in car.category.name.lower():
            matches.append(f"Category: {car.category.name}")
        if car.location and query_lower in car.location.city.lower():
            matches.append(f"Location: {car.location.city}")
        
        return matches
