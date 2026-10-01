import json
from typing import Optional, List, Dict, Any
from django.db.models import Q
from langchain.tools import tool

from apps.vehicles.models import Car, Location
from apps.vehicles.serializers import parse_datetime_param, CarListSerializer
from apps.bookings.services import BookingService
from utils.logger import get_logger

logger = get_logger("booking_agent")

@tool
def collect_details(
    pickup_location: Optional[str] = None,
    pickup_date: Optional[str] = None,
    pickup_time: Optional[str] = None,
    return_location: Optional[str] = None,
    return_date: Optional[str] = None,
    return_time: Optional[str] = None,
    car_id: Optional[int] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    category: Optional[str] = None,
    seats: Optional[int] = None,
    suggest: Optional[bool] = None
) -> dict:
    """
    Collect and validate vehicle booking details such as pickup location, pickup date, return location, return date, and vehicle preferences.
    Parameters:
    - pickup_location: City or branch location where the vehicle will be picked up.
    - pickup_date: Date when the rental starts (e.g. 'YYYY-MM-DD').
    - pickup_time: Time for vehicle pickup (optional, e.g. '10:00').
    - return_location: City or branch location where the vehicle will be returned (defaults to pickup_location).
    - return_date: Date when the rental ends (e.g. 'YYYY-MM-DD').
    - return_time: Time for vehicle return (optional, e.g. '10:00').
    - car_id: Specific Vehicle ID (optional).
    - brand: Desired car brand (optional, e.g. 'BMW', 'Mercedes', 'Audi', 'Volkswagen').
    - model: Specific car model name (optional, e.g. 'M4', 'Multivan', 'Odyssey').
    - category: Desired category (optional, e.g. 'Luxury', 'SUV', 'Sedan', 'Electric').
    - seats: Required passenger seats (optional, e.g. 5, 7).
    - suggest: Whether user asked for suggestions or recommendations (optional boolean).
    Returns a dictionary indicating status, collected details, and any missing fields.
    """
    if not return_location:
        return_location = pickup_location

    missing_fields = []
    if not pickup_location or not str(pickup_location).strip():
        missing_fields.append("pickup_location")
    if not pickup_date or not str(pickup_date).strip():
        missing_fields.append("pickup_date")
    if not return_date or not str(return_date).strip():
        missing_fields.append("return_date")

    is_complete = len(missing_fields) == 0

    formatted_pickup_date = None
    if pickup_date:
        formatted_pickup_date = f"{str(pickup_date).strip()} {str(pickup_time).strip()}".strip() if pickup_time else str(pickup_date).strip()

    formatted_return_date = None
    if return_date:
        formatted_return_date = f"{str(return_date).strip()} {str(return_time).strip()}".strip() if return_time else str(return_date).strip()

    if not is_complete:
        readable_missing = [f.replace("_", " ") for f in missing_fields]
        missing_str = ", ".join(readable_missing)
        message = f"Please provide the following details to proceed with your booking: {missing_str}."
        result = {
            "status": "missing_details",
            "is_complete": False,
            "missing_fields": missing_fields,
            "pickup_location": pickup_location,
            "pickup_date": formatted_pickup_date,
            "pickup_time": pickup_time,
            "return_location": return_location,
            "return_date": formatted_return_date,
            "return_time": return_time,
            "car_id": car_id,
            "brand": brand,
            "model": model,
            "category": category,
            "seats": seats,
            "suggest": suggest,
            "message": message,
            "response": message
        }
        logger.info("collect_details identified missing fields: %s", missing_fields)
        return result

    message = f"Collected booking details: Pickup at {pickup_location} on {formatted_pickup_date}, Return at {return_location} on {formatted_return_date}."
    result = {
        "status": "complete",
        "is_complete": True,
        "missing_fields": [],
        "pickup_location": pickup_location,
        "pickup_date": formatted_pickup_date,
        "pickup_time": pickup_time,
        "return_location": return_location,
        "return_date": formatted_return_date,
        "return_time": return_time,
        "car_id": car_id,
        "brand": brand,
        "model": model,
        "category": category,
        "seats": seats,
        "suggest": suggest,
        "message": message,
        "response": message
    }
    logger.info("collect_details completed successfully for location: %s", pickup_location)
    return result


@tool
def resolve_booking_car(
    pickup_location: str,
    pickup_date: Optional[str] = None,
    return_date: Optional[str] = None,
    car_id: Optional[int] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    category: Optional[str] = None,
    seats: Optional[int] = None,
    suggest: Optional[bool] = False
) -> dict:
    """
    Dynamically resolve, disambiguate, or recommend a specific car ID for a rental booking.
    Parameters:
    - pickup_location: City or location name where the user wants to rent.
    - pickup_date: Rental pickup date.
    - return_date: Rental return date.
    - car_id: Specific Vehicle ID if requested or known.
    - brand: Desired car brand.
    - model: Desired model name.
    - category: Desired vehicle category.
    - seats: Number of seats required.
    - suggest: True if the user asks for vehicle recommendations or suggestions.
    """
    loc_clean = (pickup_location or "").strip()

    # 1. If explicit car_id is given, verify it against the fleet and location
    if car_id:
        try:
            car = Car.objects.select_related("category", "location").get(id=car_id)
        except Car.DoesNotExist:
            fallback_cars = Car.objects.filter(status="AVAILABLE").select_related("location")[:5]
            car_list_str = "\n".join([f"• **{c.brand} {c.model}** ({c.location.city if c.location else 'Main Hub'})" for c in fallback_cars])
            msg = f"The requested vehicle was not found in our fleet.\n\nAvailable vehicles:\n{car_list_str}\n\nPlease reply with the vehicle model you would like to book."
            return {
                "status": "not_found",
                "is_car_resolved": False,
                "car_id": None,
                "message": msg,
                "response": msg
            }

        # Check location match if pickup_location was specified
        car_city = (car.location.city or "").lower() if car.location else ""
        car_loc_name = (car.location.name or "").lower() if car.location else ""
        loc_str = loc_clean.lower()

        if loc_clean and loc_str not in car_city and loc_str not in car_loc_name and car_city not in loc_str and car_loc_name not in loc_str:
            # Car exists but is at a different location
            local_cars = list(Car.objects.filter(
                Q(status="AVAILABLE") &
                (Q(location__city__icontains=loc_clean) | Q(location__name__icontains=loc_clean) | Q(location__address__icontains=loc_clean))
            ).select_related("location", "category")[:8])

            serialized_local = CarListSerializer(local_cars, many=True).data if local_cars else []

            msg = (
                f"⚠️ Note: **{car.brand} {car.model}** is located at our **{car.location.name}, {car.location.city}** branch, "
                f"not in **{loc_clean}**.\n\n"
                f"I have displayed the vehicles available in **{loc_clean}** in the fleet catalog on your screen. "
                f"Would you like to change your pickup location to **{car.location.city}**, or choose one of the available cars on screen?"
            )
            return {
                "status": "location_mismatch",
                "is_car_resolved": False,
                "car_id": car.id,
                "action": "show_fleet_cars",
                "location": loc_clean,
                "candidate_cars": serialized_local,
                "message": msg,
                "response": msg
            }

        # Car ID is verified and valid for the location
        return {
            "status": "resolved",
            "is_car_resolved": True,
            "car_id": car.id,
            "car": {
                "id": car.id,
                "brand": car.brand,
                "model": car.model,
                "year": car.year,
                "price_per_day": float(car.price_per_day),
                "security_deposit": float(car.security_deposit),
                "location": car.location.name if car.location else None,
                "city": car.location.city if car.location else None,
            },
            "message": f"Confirmed vehicle: {car.brand} {car.model}.",
            "response": f"Confirmed vehicle: {car.brand} {car.model}."
        }

    # 2. When car_id is NOT provided: search available cars at pickup_location
    q = Q(status="AVAILABLE")
    if loc_clean:
        q &= (Q(location__city__icontains=loc_clean) | Q(location__name__icontains=loc_clean) | Q(location__address__icontains=loc_clean))
    if brand and str(brand).strip():
        b_str = str(brand).strip()
        b_words = b_str.split()
        brand_q = Q(brand__icontains=b_str) | Q(model__icontains=b_str)
        for w in b_words:
            if len(w) > 2:
                brand_q |= Q(brand__icontains=w) | Q(model__icontains=w)
        q &= brand_q
    if model and str(model).strip():
        m_str = str(model).strip()
        m_words = m_str.split()
        model_q = Q(model__icontains=m_str) | Q(brand__icontains=m_str)
        for w in m_words:
            if len(w) > 2:
                model_q |= Q(model__icontains=w) | Q(brand__icontains=w)
        q &= model_q
    if category and str(category).strip():
        c_str = str(category).strip()
        q &= (Q(category__slug__iexact=c_str) | Q(category__name__icontains=c_str))
    if seats:
        try:
            q &= Q(seats__gte=int(seats))
        except (ValueError, TypeError):
            pass

    matching_cars = list(Car.objects.filter(q).select_related("location", "category").order_by("-price_per_day")[:8])

    # Fallback if filters were too specific
    if not matching_cars and loc_clean:
        matching_cars = list(Car.objects.filter(
            Q(status="AVAILABLE") &
            (Q(location__city__icontains=loc_clean) | Q(location__name__icontains=loc_clean))
        ).select_related("location", "category").order_by("-price_per_day")[:8])

    # No cars found in location
    if not matching_cars:
        available_cities = list(Location.objects.filter(is_active=True).values_list("city", flat=True).distinct())
        cities_str = ", ".join(available_cities[:6])
        msg = f"We currently do not have vehicles available in **{loc_clean}**. Our active rental hubs are in: {cities_str}. Would you like to select another location?"
        return {
            "status": "no_cars",
            "is_car_resolved": False,
            "car_id": None,
            "message": msg,
            "response": msg
        }

    # Exactly 1 car found
    if len(matching_cars) == 1 and not suggest:
        car = matching_cars[0]
        return {
            "status": "resolved",
            "is_car_resolved": True,
            "car_id": car.id,
            "car": {
                "id": car.id,
                "brand": car.brand,
                "model": car.model,
                "year": car.year,
                "price_per_day": float(car.price_per_day),
                "security_deposit": float(car.security_deposit),
                "location": car.location.name if car.location else None,
                "city": car.location.city if car.location else None,
            },
            "message": f"Selected {car.brand} {car.model}.",
            "response": f"Selected {car.brand} {car.model}."
        }

    # Multiple cars found OR user requested suggestions
    top_car = matching_cars[0]
    serialized_cars = CarListSerializer(matching_cars, many=True).data

    if suggest or (brand and len(matching_cars) > 1):
        msg = (
            f"I have updated the fleet catalog on your screen with our recommended luxury vehicles in **{loc_clean}**! "
            f"⭐ **Top Recommendation:** **{top_car.brand} {top_car.model}** ({top_car.year}) at ₹{float(top_car.price_per_day):,.0f}/day.\n\n"
            f"Please choose your preferred vehicle from the fleet to proceed with your booking."
        )
    else:
        msg = (
            f"Multiple vehicles are available in **{loc_clean}** for your dates. "
            f"I have updated the fleet catalog on your screen with the available options—please choose the vehicle you would like to book."
        )

    return {
        "status": "multiple_cars",
        "is_car_resolved": False,
        "car_id": None,
        "action": "show_fleet_cars",
        "location": loc_clean,
        "candidate_cars": serialized_cars,
        "message": msg,
        "response": msg
    }


@tool
def check_availability(car_id: int, pickup_date: str, return_date: str) -> str:
    """
    Check whether a specific car is available for the given rental pickup and return dates.
    Parameters:
    - car_id: The unique ID of the vehicle in the fleet.
    - pickup_date: Rental pickup date or datetime string (e.g. 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM').
    - return_date: Rental return date or datetime string (e.g. 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM').
    Returns a JSON string containing the availability status, car information, and pricing details.
    """
    if not car_id:
        return json.dumps({
            "status": "error",
            "available": False,
            "message": "A valid car is required."
        })

    # Parse and validate pickup and return dates
    pickup_dt = parse_datetime_param(pickup_date, is_end=False)
    return_dt = parse_datetime_param(return_date, is_end=True)

    if not pickup_dt or not return_dt:
        return json.dumps({
            "status": "error",
            "available": False,
            "message": "Invalid date format. Please provide valid pickup and return dates (e.g., 'YYYY-MM-DD')."
        })

    if return_dt <= pickup_dt:
        return json.dumps({
            "status": "error",
            "available": False,
            "message": "Return date must be after pickup date."
        })

    # Fetch vehicle
    try:
        car = Car.objects.select_related("category", "location").get(id=car_id)
    except Car.DoesNotExist:
        return json.dumps({
            "status": "error",
            "available": False,
            "message": "Selected vehicle was not found in our fleet."
        })

    # Check vehicle status and booking conflicts
    is_available = BookingService.is_car_available(car, pickup_dt, return_dt)

    response_data = {
        "status": "success",
        "available": is_available,
        "car_id": car.id,
        "brand": car.brand,
        "model": car.model,
        "car_name": f"{car.brand} {car.model}",
        "price_per_day": float(car.price_per_day),
        "security_deposit": float(car.security_deposit),
        "location": car.location.name if car.location else None,
        "city": car.location.city if car.location else None,
        "pickup_date": str(pickup_date),
        "return_date": str(return_date),
        "message": (
            f"{car.brand} {car.model} is available from {pickup_date} to {return_date} at ₹{float(car.price_per_day):,.0f}/day."
            if is_available
            else f"{car.brand} {car.model} is not available for the selected dates ({pickup_date} to {return_date})."
        )
    }

    logger.info("check_availability checked car_id=%s, dates=%s to %s: available=%s", car_id, pickup_date, return_date, is_available)
    return json.dumps(response_data)