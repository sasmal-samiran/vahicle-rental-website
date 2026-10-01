from django.db.models import Q, Avg, Count
from apps.vehicles.models import Car
from apps.bookings.models import Booking
from apps.vehicles.serializers import CarListSerializer, CarDetailSerializer
from apps.analytics.services import RecommendationService

def search_available_cars(user=None, location=None, category=None, brand=None, model=None, min_price=None, max_price=None, fuel_type=None, seats=None, limit=12):
    q = Q(status="AVAILABLE")
    if location and str(location).strip():
        loc_str = str(location).strip()
        q &= (Q(location__address__icontains=loc_str) | Q(location__name__icontains=loc_str) | Q(location__city__icontains=loc_str))
    if category and str(category).strip():
        cat_str = str(category).strip()
        q &= (Q(category__slug__iexact=cat_str) | Q(category__name__icontains=cat_str))
    if brand and str(brand).strip():
        b_str = str(brand).strip()
        q &= (Q(brand__icontains=b_str) | Q(model__icontains=b_str))
    if model and str(model).strip():
        b_str = str(model).strip()
        q &= (Q(model__icontains=b_str))
    if fuel_type and str(fuel_type).strip():
        f_str = str(fuel_type).strip()
        q &= (Q(fuel_type__icontains=f_str))
    if seats:
        try:
            q &= Q(seats=int(seats))
        except (ValueError, TypeError):
            pass
    if min_price is not None:
        try:
            min_val = float(min_price)
            if min_val > 0:
                q &= Q(price_per_day__gte=min_val)
        except (ValueError, TypeError):
            pass
    if max_price is not None:
        try:
            max_val = float(max_price)
            if max_val > 0:
                q &= Q(price_per_day__lte=max_val)
        except (ValueError, TypeError):
            pass

    # 1. Fetch matching candidate cars with annotated rating & booking metrics
    candidate_cars = list(
        Car.objects.filter(q)
        .select_related("category", "location", "popularity_metrics")
        .prefetch_related("images")
        .annotate(
            annotated_avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            annotated_total_reviews=Count("reviews", filter=Q(reviews__is_approved=True)),
            annotated_bookings_count=Count("bookings", filter=Q(bookings__status__in=["CONFIRMED", "COMPLETED", "ONGOING"]))
        )
    )
    if not candidate_cars:
        return []

    # 2. Rank candidates via RecommendationService (personalized if authenticated, popularity-ranked if anonymous)
    try:
        rec_service = RecommendationService()
        recommended_cars = rec_service.get_recommendations_for_user(
            user=user,
            limit=limit,
            candidate_cars=candidate_cars
        )
    except Exception:
        recommended_cars = candidate_cars

    cars = CarListSerializer(recommended_cars, many=True).data
    result = []
    for car in cars:
        if not car["location"]["is_active"]:
            continue
        details = {
            "id": car["id"],
            "brand": car["brand"],
            "model":car["model"],
            "year":car["year"],
            "category":car["category"]["slug"],
            "location": car["location"]["name"],
            "main_image_url": car["main_image_url"],
            "transmission": car["transmission"],
            "fuel_type": car["fuel_type"],
            "seats": car["seats"],
            "luggage_capacity": car["luggage_capacity"],
            "price_per_day": car["price_per_day"],
            "status": car["status"],
            "is_available_for_dates": car["is_available_for_dates"],
            "features": car["features"],
            "description": car["description"],
            "average_rating": car["average_rating"],
            "total_reviews": car["total_reviews"]
        }
        result.append(details)
        
    return result

def get_car_by_id(car_id):
    try:
        car = Car.objects.select_related("category", "location").prefetch_related("images", "reviews").get(id=car_id)
        return CarDetailSerializer(car).data
    except Car.DoesNotExist:
        return None

def get_bookings_for_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return []
    
    bookings = Booking.objects.filter(customer=user).select_related("car", "pickup_location").order_by("-created_at")
    results = []
    for b in bookings:
        results.append({
            "booking_code": b.booking_code,
            "car_name": f"{b.car.brand} {b.car.model}",
            "status": b.status,
            "payment_status": b.payment_status,
            "pickup_date": b.start_date.strftime("%b %d, %Y %H:%M") if b.start_date else "",
            "return_date": b.end_date.strftime("%b %d, %Y %H:%M") if b.end_date else "",
            "start_date": b.start_date.strftime("%b %d, %Y %H:%M") if b.start_date else "",
            "end_date": b.end_date.strftime("%b %d, %Y %H:%M") if b.end_date else "",
            "total_days": b.total_days,
            "total_amount": float(b.total_amount),
            "pickup_location": b.pickup_location.name if b.pickup_location else "Main Branch"
        })
    return results