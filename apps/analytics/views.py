from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from apps.vehicles.models import Car
from apps.vehicles.search_engine import CarSearchService
from .services import RecommendationService
from .models import SearchLog, RecommendationClick
from apps.vehicles.serializers import CarListSerializer

class SearchCarsView(APIView):
    """Enhanced search endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        query = request.GET.get('q', '')
        search_service = CarSearchService()
        
        # Log the search
        if query or request.GET:
            SearchLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query,
                filters=dict(request.GET),
                results_count=0  # Will update after search
            )
        
        # Perform search
        results = search_service.search_with_relevance(query)
        
        # Serialize results
        cars = [result['car'] for result in results]
        serializer = CarListSerializer(cars, many=True)
        
        # Add relevance scores to response
        response_data = []
        for i, result in enumerate(results):
            car_data = serializer.data[i]
            car_data['relevance_score'] = result['relevance_score']
            car_data['match_details'] = result['match_details']
            response_data.append(car_data)
        
        return Response(response_data)

class GetRecommendationsView(APIView):
    """Get personalized recommendations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        limit = int(request.GET.get('limit', 10))
        rec_type = request.GET.get('type', 'personalized')
        
        rec_service = RecommendationService()
        
        if rec_type == 'popular':
            cars = rec_service.get_popular_cars(limit)
        elif rec_type == 'trending':
            cars = rec_service.get_trending_cars(limit)
        elif rec_type == 'similar':
            car_id = request.GET.get('car_id')
            if not car_id:
                return Response(
                    {'error': 'car_id is required for similar cars'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            car = get_object_or_404(Car, id=car_id)
            cars = rec_service.get_similar_cars(car, limit)
        else:
            cars = rec_service.get_recommendations_for_user(request.user, limit)
        
        serializer = CarListSerializer(cars, many=True)
        return Response(serializer.data)

class ContextRecommendationsView(APIView):
    """Get context-aware recommendations"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        context = {
            'trip_type': request.GET.get('trip_type', ''),
            'passengers': int(request.GET.get('passengers', 1)),
            'budget': float(request.GET.get('budget', 0)) if request.GET.get('budget') else None
        }
        
        rec_service = RecommendationService()
        cars = rec_service.get_recommendations_by_context(context)
        
        serializer = CarListSerializer(cars, many=True)
        return Response(serializer.data)