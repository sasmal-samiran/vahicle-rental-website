from .tools import create_tools

def get_public_tools(user=None):
    tools = create_tools(user=user)
    return [
        tools["search_cars"],
        tools["show_car_details"],
        tools["get_car_specs"],
        tools["open_login_modal"],
    ]

def get_private_tools(user=None):
    tools = create_tools(user=user)
    return [
        tools["search_cars"],
        tools["show_car_details"],
        tools["get_car_specs"],
        tools["get_my_reservations"],
        tools["open_booking_wizard"],
    ]