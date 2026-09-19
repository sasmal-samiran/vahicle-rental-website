from langchain.tools import tool
from typing import Optional
import json

from apps.rental_agent.services import (
    search_available_cars,
    get_car_by_id,
    get_bookings_for_user
)

def create_tools(user=None):
    @tool
    def search_cars(
        location: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        model: Optional[str]=None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        fuel_type: Optional[str] = None,
        seats: Optional[int]=None
    ) -> str:
        """
        Search available rental cars in the DriveLuxe fleet and filter the fleet catalog on the webpage.
        always take the starting location and search based on that.
        Parameters:
        - location: City or pickup location name (e.g. 'Kolkata', 'Digha', 'Darjeeling').
        - category: Vehicle class (e.g. 'Luxury', 'SUV', 'Electric', 'Sedan').
        - brand: Car brand (e.g. 'Audi', 'BMW', 'Mercedes', 'Porsche').
        - model: Model name of that car's brand.
        - min_price: Minimum daily rental rate.
        - max_price: Maximum daily rental rate.
        - fuel_type: Powertrain ('Electric', 'Hybrid', 'Petrol')
        """
        cars = search_available_cars(
            user=user,
            location=location,
            category=category,
            brand=brand,
            model= model,
            min_price=min_price,
            max_price=max_price,
            fuel_type=fuel_type,
            seats= seats,
        )
        if not cars:
            criteria = []
            if location: criteria.append(f"location='{location}'")
            if category: criteria.append(f"category='{category}'")
            if brand: criteria.append(f"brand='{brand}'")
            if model: criteria.append(f"model='{model}'")
            if fuel_type: criteria.append(f"fuel type='{fuel_type}'")
            if seats: criteria.append(f"Seats= '{seats}'")
            crit_str = " with " + ", ".join(criteria) if criteria else ""
            return f"No available cars found in our fleet{crit_str}. Please suggest alternative dates, nearby branches, or different categories."
        return json.dumps(cars)

    @tool
    def show_car_details(car_id: int) -> str:
        """
        Open the full vehicle details modal on the webpage to display high-resolution photos, 
        complete technical specifications, features, customer reviews, and pricing for a specific car ID.
        Call this whenever recommending a specific car or when the user asks to see/view car details.
        """
        details = get_car_by_id(car_id)
        if not details:
            return f"Vehicle with ID {car_id} was not found in our fleet."
        return json.dumps(details)

    @tool
    def get_car_specs(car_id: int) -> str:
        """
        Get detailed vehicle specifications, pricing, power, and security deposit info for a specific car ID.
        Also opens the vehicle detail modal on the webpage.
        """
        details = get_car_by_id(car_id)
        if not details:
            return f"Vehicle with ID {car_id} was not found in our fleet."
        return json.dumps(details)

    @tool
    def open_booking_wizard(car_id: int) -> str:
        """
        Open the interactive booking and reservation wizard modal on the webpage for a specific vehicle ID.
        Call this when the user expresses clear intent to book, reserve, or rent a specific vehicle.
        """
        details = get_car_by_id(car_id)
        if not details:
            return json.dumps({"status": "error", "message": "Selected vehicle was not found."})
        return json.dumps({
            "status": "success",
            "action": "open_booking_wizard",
            "car_id": car_id,
            "brand": details.get("brand"),
            "model": details.get("model"),
            "price_per_day": details.get("price_per_day"),
            "message": f"Successfully opened booking wizard on webpage for {details.get('brand')} {details.get('model')}."
        })

    @tool
    def open_login_modal() -> str:
        """
        Open the sign-in modal on the webpage to allow the user to authenticate or register.
        """
        return "Opened login modal on webpage."

    @tool
    def get_my_reservations() -> str:
        """
        Retrieve the current user's active, upcoming, and past vehicle reservations and switch to the bookings tab on the customer portal.
        """
        bookings = get_bookings_for_user(user)
        if not bookings:
            return "You currently have no active or previous reservations on file."
        return json.dumps(bookings)

    return {
        "search_cars": search_cars,
        "show_car_details": show_car_details,
        "get_car_specs": get_car_specs,
        "get_my_reservations": get_my_reservations,
        "open_booking_wizard": open_booking_wizard,
        "open_login_modal": open_login_modal,
    }