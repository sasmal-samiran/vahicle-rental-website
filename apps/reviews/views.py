from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer

class CarReviewListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        car_id = self.kwargs.get('car_id')
        return Review.objects.filter(car_id=car_id, is_approved=True).select_related('customer', 'car')

class CreateReviewView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)

class AdminReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Review.objects.all().select_related('customer', 'car', 'booking').order_by('-created_at')
    serializer_class = ReviewSerializer
