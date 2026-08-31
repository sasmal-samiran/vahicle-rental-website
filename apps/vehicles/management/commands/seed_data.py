import os
import datetime
from decimal import Decimal
from django.core.files import File
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.vehicles.models import Category, Location, Car, CarImage
from apps.vehicles.services import VehicleService
from apps.bookings.models import Booking, BookingAddon, Coupon
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with rich, realistic car rental demo data'

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')

        # 1. Admin & Customer Users
        admin_user1, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin1@gmail.com',
                'phone_number': '9000000001',
                'first_name': 'Admin',
                'last_name': 'System',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_phone_verified': True
            }
        )
        admin_user1.set_password('admin123')
        admin_user1.save()

        rahul, _ = User.objects.get_or_create(
            username='rahul',
            defaults={
                'email': 'rahul@example.com',
                'phone_number': '9835754632',
                'first_name': 'Rahul',
                'last_name': 'Morgan',
                'role': 'CUSTOMER',
                'driver_license_number': 'DL-NY-9847291',
                'address': '12 Park Street',
                'city': 'Kolkata',
                'is_phone_verified': True
            }
        )
        rahul.set_password('rahul123')
        rahul.save()

        priya, _ = User.objects.get_or_create(
            username='priya',
            defaults={
                'email': 'priya@example.com',
                'phone_number': '8567439521',
                'first_name': 'Priya',
                'last_name': 'Jenkins',
                'role': 'CUSTOMER',
                'driver_license_number': 'DL-CA-4491028',
                'address': 'Jadavpur',
                'city': 'Kolkata',
                'is_phone_verified': True
            }
        )
        priya.set_password('priya123')
        priya.save()

        # 2. Categories
        categories_data = [
            {'name': 'Luxury & Executive', 'slug': 'luxury', 'icon': 'fa-crown', 'description': 'Premium luxury sedans and executive cruisers with supreme comfort.', 'image_url': 'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Electric & Hybrid', 'slug': 'electric', 'icon': 'fa-bolt', 'description': 'Eco-friendly high-tech zero-emission vehicles with instant torque.', 'image_url': 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=600&q=80'},
            {'name': 'SUVs & Crossovers', 'slug': 'suv', 'icon': 'fa-mountain', 'description': 'Spacious and capable vehicles suited for family trips and mountain adventures.', 'image_url': 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=600&q=80'},
            {
        'name': '7-Seater & Family',
        'slug': 'family',
        'icon': 'fa-users',
        'description': 'Comfortable family vehicles with extra seating and luggage space for group travel and holidays.',
        'image_url': 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=600&q=80'
    },
            {'name': 'Sedans', 'slug': 'sedan', 'icon': 'fa-car-side', 'description': 'Comfortable, fuel-efficient daily commuter sedans with modern amenities.', 'image_url': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Compact & Hatchback', 'slug': 'compact', 'icon': 'fa-car', 'description': 'Agile, easy to park, and extremely fuel-efficient city cars.', 'image_url': 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=600&q=80'},
        ]
        
        cat_map = {}
        for cat in categories_data:
            c_obj, _ = Category.objects.get_or_create(slug=cat['slug'], defaults=cat)
            cat_map[cat['slug']] = c_obj

        # 3. Hub Locations
        locations_data = [
    # ==================== KOLKATA ====================
    {
        'name': 'Kolkata Airport Hub',
        'city': 'Kolkata',
        'address': 'Netaji Subhas Chandra Bose International Airport, Kolkata, West Bengal 700052',
        'phone': '+91 90000 10001',
        'email': 'airport@driveluxe.in'
    },
    {
        'name': 'Park Street Hub',
        'city': 'Kolkata',
        'address': 'Park Street, Kolkata, West Bengal 700016',
        'phone': '+91 90000 10002',
        'email': 'parkstreet@driveluxe.in'
    },
    {
        'name': 'Salt Lake Sector V Hub',
        'city': 'Kolkata',
        'address': 'Sector V, Bidhannagar, Kolkata, West Bengal 700091',
        'phone': '+91 90000 10003',
        'email': 'saltlake@driveluxe.in'
    },
    {
        'name': 'New Town Hub',
        'city': 'Kolkata',
        'address': 'New Town, Kolkata, West Bengal 700156',
        'phone': '+91 90000 10004',
        'email': 'newtown@driveluxe.in'
    },
    {
        'name': 'Howrah Station Hub',
        'city': 'Howrah',
        'address': 'Howrah Railway Station Area, Howrah, West Bengal 711101',
        'phone': '+91 90000 10005',
        'email': 'howrah@driveluxe.in'
    },
    {
        'name': 'Garia Hub',
        'city': 'Kolkata',
        'address': 'Garia, Kolkata, West Bengal 700084',
        'phone': '+91 90000 10006',
        'email': 'garia@driveluxe.in'
    },
    {
        'name': 'Behala Hub',
        'city': 'Kolkata',
        'address': 'Behala, Kolkata, West Bengal 700034',
        'phone': '+91 90000 10007',
        'email': 'behala@driveluxe.in'
    },

    # ==================== SOUTH BENGAL ====================
    {
        'name': 'Durgapur Hub',
        'city': 'Durgapur',
        'address': 'City Centre, Durgapur, West Bengal 713216',
        'phone': '+91 90000 10008',
        'email': 'durgapur@driveluxe.in'
    },
    {
        'name': 'Asansol Hub',
        'city': 'Asansol',
        'address': 'Asansol, West Bengal 713304',
        'phone': '+91 90000 10009',
        'email': 'asansol@driveluxe.in'
    },
    {
        'name': 'Bardhaman Hub',
        'city': 'Bardhaman',
        'address': 'Bardhaman, West Bengal 713101',
        'phone': '+91 90000 10010',
        'email': 'bardhaman@driveluxe.in'
    },
    {
        'name': 'Kharagpur Hub',
        'city': 'Kharagpur',
        'address': 'Kharagpur, West Bengal 721301',
        'phone': '+91 90000 10011',
        'email': 'kharagpur@driveluxe.in'
    },
    {
        'name': 'Haldia Hub',
        'city': 'Haldia',
        'address': 'Haldia, Purba Medinipur, West Bengal 721607',
        'phone': '+91 90000 10012',
        'email': 'haldia@driveluxe.in'
    },
    {
        'name': 'Digha Coastal Hub',
        'city': 'Digha',
        'address': 'Digha, Purba Medinipur, West Bengal 721428',
        'phone': '+91 90000 10013',
        'email': 'digha@driveluxe.in'
    },
    {
        'name': 'Mandarmani Hub',
        'city': 'Mandarmani',
        'address': 'Mandarmani, Purba Medinipur, West Bengal 721423',
        'phone': '+91 90000 10014',
        'email': 'mandarmani@driveluxe.in'
    },

    # ==================== CENTRAL / CULTURAL ====================
    {
        'name': 'Shantiniketan Hub',
        'city': 'Bolpur',
        'address': 'Bolpur-Shantiniketan, Birbhum, West Bengal 731204',
        'phone': '+91 90000 10015',
        'email': 'shantiniketan@driveluxe.in'
    },
    {
        'name': 'Bishnupur Heritage Hub',
        'city': 'Bishnupur',
        'address': 'Bishnupur, Bankura, West Bengal 722122',
        'phone': '+91 90000 10016',
        'email': 'bishnupur@driveluxe.in'
    },
    {
        'name': 'Murshidabad Heritage Hub',
        'city': 'Murshidabad',
        'address': 'Murshidabad, West Bengal 742149',
        'phone': '+91 90000 10017',
        'email': 'murshidabad@driveluxe.in'
    },
    {
        'name': 'Krishnanagar Hub',
        'city': 'Krishnanagar',
        'address': 'Krishnanagar, Nadia, West Bengal 741101',
        'phone': '+91 90000 10018',
        'email': 'krishnanagar@driveluxe.in'
    },

    # ==================== NORTH BENGAL ====================
    {
        'name': 'Siliguri Hub',
        'city': 'Siliguri',
        'address': 'Siliguri, West Bengal 734001',
        'phone': '+91 90000 10019',
        'email': 'siliguri@driveluxe.in'
    },
    {
        'name': 'Bagdogra Airport Hub',
        'city': 'Bagdogra',
        'address': 'Bagdogra Airport Area, West Bengal 734421',
        'phone': '+91 90000 10020',
        'email': 'bagdogra@driveluxe.in'
    },
    {
        'name': 'Darjeeling Hub',
        'city': 'Darjeeling',
        'address': 'Darjeeling, West Bengal 734101',
        'phone': '+91 90000 10021',
        'email': 'darjeeling@driveluxe.in'
    },
    {
        'name': 'Kalimpong Hub',
        'city': 'Kalimpong',
        'address': 'Kalimpong, West Bengal 734301',
        'phone': '+91 90000 10022',
        'email': 'kalimpong@driveluxe.in'
    },
    {
        'name': 'Jalpaiguri Hub',
        'city': 'Jalpaiguri',
        'address': 'Jalpaiguri, West Bengal 735101',
        'phone': '+91 90000 10023',
        'email': 'jalpaiguri@driveluxe.in'
    },
    {
        'name': 'Cooch Behar Hub',
        'city': 'Cooch Behar',
        'address': 'Cooch Behar, West Bengal 736101',
        'phone': '+91 90000 10024',
        'email': 'coochbehar@driveluxe.in'
    },
    {
        'name': 'Malda Hub',
        'city': 'Malda',
        'address': 'Malda, West Bengal 732101',
        'phone': '+91 90000 10025',
        'email': 'malda@driveluxe.in'
    },

    # ==================== HILL / NATURE ====================
    {
        'name': 'Dooars Hub',
        'city': 'Lataguri',
        'address': 'Lataguri, Jalpaiguri, West Bengal 735219',
        'phone': '+91 90000 10026',
        'email': 'dooars@driveluxe.in'
    },
    {
        'name': 'Sundarbans Gateway Hub',
        'city': 'Canning',
        'address': 'Canning, South 24 Parganas, West Bengal 743329',
        'phone': '+91 90000 10027',
        'email': 'sundarbans@driveluxe.in'
    }
]

        loc_objs = []

        for loc in locations_data:
            l_obj, _ = Location.objects.get_or_create(
                name=loc['name'],
                defaults=loc
            )
            loc_objs.append(l_obj)

        loc_kolkata_airport = loc_objs[0]
        loc_park_street = loc_objs[1]
        loc_salt_lake = loc_objs[2]
        loc_new_town = loc_objs[3]
        loc_howrah = loc_objs[4]
        loc_garia = loc_objs[5]
        loc_behala = loc_objs[6]

        loc_durgapur = loc_objs[7]
        loc_asansol = loc_objs[8]
        loc_bardhaman = loc_objs[9]
        loc_kharagpur = loc_objs[10]
        loc_haldia = loc_objs[11]
        loc_digha = loc_objs[12]
        loc_mandarmani = loc_objs[13]

        loc_shantiniketan = loc_objs[14]
        loc_bishnupur = loc_objs[15]
        loc_murshidabad = loc_objs[16]
        loc_krishnanagar = loc_objs[17]

        loc_siliguri = loc_objs[18]
        loc_bagdogra = loc_objs[19]
        loc_darjeeling = loc_objs[20]
        loc_kalimpong = loc_objs[21]
        loc_jalpaiguri = loc_objs[22]
        loc_cooch_behar = loc_objs[23]
        loc_malda = loc_objs[24]

        loc_dooars = loc_objs[25]
        loc_sundarbans = loc_objs[26]

        # 4. Fleet of Cars
        cars_data = [
    # ==================== PREMIUM & LUXURY ====================
    {
        'brand': 'Toyota', 'model': 'Camry', 'year': 2024, 'license_plate': 'WB-01-LUX-01',
        'category': cat_map['luxury'], 'location': loc_park_street,
        'transmission': 'AUTOMATIC', 'fuel_type': 'HYBRID', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '250 km/day',
        'engine_capacity': '2.5L Petrol Hybrid', 'power_hp': 215,
        'price_per_day': Decimal('6500.00'), 'security_deposit': Decimal('15000.00'),
        # 'main_image_path': 'media/cars/toyota_camry.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/camry_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/camry_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/camry_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Leather Seats', 'Panoramic Sunroof', 'Adaptive Cruise Control',
            'Automatic Climate Control', 'Wireless Charging', 'Premium Audio'
        ],
        'description': 'Premium hybrid sedan ideal for executive travel, business meetings and comfortable long-distance journeys.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Mercedes-Benz', 'model': 'C-Class', 'year': 2024, 'license_plate': 'WB-02-LUX-02',
        'category': cat_map['luxury'], 'location': loc_new_town,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '200 km/day',
        'engine_capacity': '1.5L Turbo Petrol', 'power_hp': 201,
        'price_per_day': Decimal('9500.00'), 'security_deposit': Decimal('25000.00'),
        # 'main_image_path': 'media/cars/mercedes_c_class.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/mercedes_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/mercedes_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/mercedes_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'MBUX Infotainment', 'Leather Interior', 'Panoramic Sunroof',
            'Ambient Lighting', '360-Degree Camera', 'Wireless Apple CarPlay'
        ],
        'description': 'Luxury executive sedan designed for premium city travel, corporate journeys and special occasions.',
        'status': 'AVAILABLE'
    },

    # ==================== ELECTRIC & HYBRID ====================
    {
        'brand': 'Tata', 'model': 'Nexon EV', 'year': 2025, 'license_plate': 'WB-03-EV-01',
        'category': cat_map['electric'], 'location': loc_salt_lake,
        'transmission': 'AUTOMATIC', 'fuel_type': 'ELECTRIC', 'seats': 5, 'doors': 5,
        'luggage_capacity': 2, 'mileage_limit': '250 km/day',
        'engine_capacity': 'Electric Motor', 'power_hp': 145,
        'price_per_day': Decimal('2200.00'), 'security_deposit': Decimal('7000.00'),
        # 'main_image_path': 'media/cars/tata_nexon_ev.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/nexon_ev_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/nexon_ev_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/nexon_ev_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Fast Charging', 'Touchscreen Infotainment', 'Connected Car Technology',
            'Automatic Climate Control', 'Reverse Camera', 'Regenerative Braking'
        ],
        'description': 'Practical electric SUV for eco-friendly Kolkata commuting and short-distance trips.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'MG', 'model': 'ZS EV', 'year': 2024, 'license_plate': 'WB-04-EV-02',
        'category': cat_map['electric'], 'location': loc_kolkata_airport,
        'transmission': 'AUTOMATIC', 'fuel_type': 'ELECTRIC', 'seats': 5, 'doors': 5,
        'luggage_capacity': 3, 'mileage_limit': '250 km/day',
        'engine_capacity': 'Electric Motor', 'power_hp': 174,
        'price_per_day': Decimal('3000.00'), 'security_deposit': Decimal('8000.00'),
        # 'main_image_path': 'media/cars/mg_zs_ev.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/mg_zs_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/mg_zs_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/mg_zs_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Panoramic Sunroof', 'Wireless Charging', '360-Degree Camera',
            'Connected Car Features', 'Cruise Control', 'Premium Interior'
        ],
        'description': 'Premium electric SUV suitable for airport transfers, city travel and comfortable family journeys.',
        'status': 'AVAILABLE'
    },

    # ==================== SUVs & MUVs ====================
    {
        'brand': 'Toyota', 'model': 'Innova Crysta', 'year': 2024, 'license_plate': 'WB-05-SUV-01',
        'category': cat_map['suv'], 'location': loc_howrah,
        'transmission': 'MANUAL', 'fuel_type': 'DIESEL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '2.4L Diesel', 'power_hp': 148,
        'price_per_day': Decimal('3200.00'), 'security_deposit': Decimal('9000.00'),
        # 'main_image_path': 'media/cars/innova_crysta.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/innova_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/innova_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/innova_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '7 Seats', 'Captain Seats', 'Rear AC', 'Touchscreen Infotainment',
            'Cruise Control', 'Large Luggage Space'
        ],
        'description': 'Spacious and reliable MUV ideal for family vacations, railway pickups and West Bengal intercity travel.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Mahindra', 'model': 'XUV700', 'year': 2025, 'license_plate': 'WB-06-SUV-02',
        'category': cat_map['suv'], 'location': loc_durgapur,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '2.0L Turbo Petrol', 'power_hp': 197,
        'price_per_day': Decimal('3500.00'), 'security_deposit': Decimal('10000.00'),
        # 'main_image_path': 'media/cars/mahindra_xuv700.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/xuv700_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/xuv700_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/xuv700_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'ADAS', 'Panoramic Sunroof', '7 Seats', '360-Degree Camera',
            'Connected Car Technology', 'Dual-Zone Climate Control'
        ],
        'description': 'Powerful and feature-rich SUV for family road trips, highways and long-distance travel.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Mahindra', 'model': 'Scorpio-N', 'year': 2024, 'license_plate': 'WB-07-SUV-03',
        'category': cat_map['suv'], 'location': loc_siliguri,
        'transmission': 'MANUAL', 'fuel_type': 'DIESEL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '2.2L Diesel', 'power_hp': 172,
        'price_per_day': Decimal('3000.00'), 'security_deposit': Decimal('9000.00'),
        # 'main_image_path': 'media/cars/scorpio_n.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1544829099-b9a0c07fad1a?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/scorpio_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/scorpio_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/scorpio_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '7 Seats', 'High Ground Clearance', 'Terrain Modes',
            'Hill Hold Assist', 'Cruise Control', 'Large Cabin'
        ],
        'description': 'Rugged SUV suited for North Bengal, Darjeeling, Kalimpong and challenging road conditions.',
        'status': 'AVAILABLE'
    },

    # ==================== SEDANS ====================
    {
        'brand': 'Honda', 'model': 'City', 'year': 2024, 'license_plate': 'WB-08-SED-01',
        'category': cat_map['sedan'], 'location': loc_park_street,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.5L Petrol', 'power_hp': 119,
        'price_per_day': Decimal('2000.00'), 'security_deposit': Decimal('6000.00'),
        # 'main_image_path': 'media/cars/honda_city.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/city_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/city_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/city_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Honda Sensing', 'Sunroof', 'Automatic Climate Control',
            'Rear Camera', 'Cruise Control', 'Wireless Android Auto'
        ],
        'description': 'Comfortable and refined sedan for Kolkata city travel, business trips and intercity journeys.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Hyundai', 'model': 'Verna', 'year': 2025, 'license_plate': 'WB-09-SED-02',
        'category': cat_map['sedan'], 'location': loc_new_town,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.5L Turbo Petrol', 'power_hp': 158,
        'price_per_day': Decimal('2300.00'), 'security_deposit': Decimal('6500.00'),
        # 'main_image_path': 'media/cars/hyundai_verna.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/verna_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/verna_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/verna_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'ADAS', 'Ventilated Seats', 'Electric Sunroof',
            'Dual-Zone Climate Control', '360-Degree Camera', 'Wireless Charging'
        ],
        'description': 'Modern turbocharged sedan combining performance, comfort and advanced safety features.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Skoda', 'model': 'Slavia', 'year': 2024, 'license_plate': 'WB-10-SED-03',
        'category': cat_map['sedan'], 'location': loc_durgapur,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.5L TSI Petrol', 'power_hp': 148,
        'price_per_day': Decimal('2400.00'), 'security_deposit': Decimal('7000.00'),
        # 'main_image_path': 'media/cars/skoda_slavia.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/slavia_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/slavia_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/slavia_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Turbo Petrol Engine', 'Ventilated Seats', 'Sunroof',
            'Cruise Control', 'Touchscreen Infotainment', 'Large Boot'
        ],
        'description': 'Premium European-style sedan suitable for highway travel and comfortable intercity journeys.',
        'status': 'AVAILABLE'
    },

    # ==================== HATCHBACK & COMPACT ====================
    {
        'brand': 'Maruti Suzuki', 'model': 'Swift', 'year': 2025, 'license_plate': 'WB-11-CMP-01',
        'category': cat_map['compact'], 'location': loc_garia,
        'transmission': 'MANUAL', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 5,
        'luggage_capacity': 2, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.2L Petrol', 'power_hp': 80,
        'price_per_day': Decimal('1200.00'), 'security_deposit': Decimal('4000.00'),
        # 'main_image_path': 'media/cars/maruti_swift.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/swift_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/swift_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/swift_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Fuel Efficient', 'Reverse Parking Sensors', 'Touchscreen Infotainment',
            'Android Auto', 'Air Conditioning', 'Compact Design'
        ],
        'description': 'Affordable and fuel-efficient hatchback ideal for everyday Kolkata commuting and city traffic.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Hyundai', 'model': 'i20', 'year': 2024, 'license_plate': 'WB-12-CMP-02',
        'category': cat_map['compact'], 'location': loc_behala,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 5,
        'luggage_capacity': 2, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.2L Petrol', 'power_hp': 82,
        'price_per_day': Decimal('1500.00'), 'security_deposit': Decimal('4500.00'),
        # 'main_image_path': 'media/cars/hyundai_i20.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1550355291-bbee04a92027?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/i20_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/i20_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/i20_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Automatic Transmission', 'Sunroof', 'Touchscreen Infotainment',
            'Cruise Control', 'Rear Camera', 'Wireless Android Auto'
        ],
        'description': 'Premium compact hatchback that is easy to drive and park in busy Kolkata city traffic.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Tata', 'model': 'Altroz', 'year': 2024, 'license_plate': 'WB-13-CMP-03',
        'category': cat_map['compact'], 'location': loc_howrah,
        'transmission': 'MANUAL', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 5,
        'luggage_capacity': 2, 'mileage_limit': '250 km/day',
        'engine_capacity': '1.2L Petrol', 'power_hp': 86,
        'price_per_day': Decimal('1300.00'), 'security_deposit': Decimal('4000.00'),
        # 'main_image_path': 'media/cars/tata_altroz.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/altroz_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/altroz_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/altroz_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '5-Star Safety Rating', 'Touchscreen Infotainment',
            'Cruise Control', 'Rear Camera', 'Automatic Climate Control'
        ],
        'description': 'Safety-focused compact hatchback suitable for affordable daily and weekend travel.',
        'status': 'AVAILABLE'
    },

    # ==================== 7-SEATER & FAMILY ====================
    {
        'brand': 'Maruti Suzuki', 'model': 'Ertiga', 'year': 2024, 'license_plate': 'WB-14-FAM-01',
        'category': cat_map['family'], 'location': loc_siliguri,
        'transmission': 'MANUAL', 'fuel_type': 'PETROL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '1.5L Petrol', 'power_hp': 102,
        'price_per_day': Decimal('2200.00'), 'security_deposit': Decimal('6000.00'),
        # 'main_image_path': 'media/cars/maruti_ertiga.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/ertiga_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/ertiga_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/ertiga_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '7 Seats', 'Large Luggage Space', 'Rear AC',
            'Touchscreen Infotainment', 'Fuel Efficient', 'Multiple USB Ports'
        ],
        'description': 'Practical 7-seater MPV for families travelling to Darjeeling, Dooars and other West Bengal destinations.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Kia', 'model': 'Carens', 'year': 2024, 'license_plate': 'WB-15-FAM-02',
        'category': cat_map['family'], 'location': loc_bagdogra,
        'transmission': 'AUTOMATIC', 'fuel_type': 'DIESEL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '1.5L Diesel', 'power_hp': 113,
        'price_per_day': Decimal('2800.00'), 'security_deposit': Decimal('7500.00'),
        # 'main_image_path': 'media/cars/kia_carens.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/carens_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/carens_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/carens_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '7 Seats', 'Ventilated Seats', 'Rear AC',
            'Panoramic Sunroof', 'Cruise Control', 'Large Cabin'
        ],
        'description': 'Comfortable family MPV particularly suited for airport pickups and North Bengal holiday trips.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Toyota', 'model': 'Innova HyCross', 'year': 2025, 'license_plate': 'WB-16-FAM-03',
        'category': cat_map['family'], 'location': loc_darjeeling,
        'transmission': 'AUTOMATIC', 'fuel_type': 'HYBRID', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '300 km/day',
        'engine_capacity': '2.0L Petrol Hybrid', 'power_hp': 183,
        'price_per_day': Decimal('4000.00'), 'security_deposit': Decimal('12000.00'),
        # 'main_image_path': 'media/cars/innova_hycross.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/hycross_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/hycross_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/hycross_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Hybrid Powertrain', '7 Seats', 'Captain Seats',
            'Panoramic Sunroof', 'ADAS', 'Premium Interior'
        ],
        'description': 'Premium hybrid family vehicle for comfortable long-distance journeys across West Bengal.',
        'status': 'AVAILABLE'
    },

    # ==================== TOURIST / NORTH BENGAL ====================
    {
        'brand': 'Toyota', 'model': 'Fortuner', 'year': 2024, 'license_plate': 'WB-17-TUR-01',
        'category': cat_map['suv'], 'location': loc_darjeeling,
        'transmission': 'AUTOMATIC', 'fuel_type': 'DIESEL', 'seats': 7, 'doors': 5,
        'luggage_capacity': 4, 'mileage_limit': '250 km/day',
        'engine_capacity': '2.8L Turbo Diesel', 'power_hp': 201,
        'price_per_day': Decimal('5000.00'), 'security_deposit': Decimal('15000.00'),
        # 'main_image_path': 'media/cars/toyota_fortuner.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/fortuner_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/fortuner_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/fortuner_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            '4x4 Capability', '7 Seats', 'High Ground Clearance',
            'Cruise Control', 'Terrain Assist', 'Premium Interior'
        ],
        'description': 'Premium rugged SUV suitable for North Bengal road trips, mountain travel and large family groups.',
        'status': 'AVAILABLE'
    },

    # ==================== ECONOMICAL INTERCITY ====================
    {
        'brand': 'Maruti Suzuki', 'model': 'Dzire', 'year': 2025, 'license_plate': 'WB-18-ECO-01',
        'category': cat_map['sedan'], 'location': loc_digha,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '300 km/day',
        'engine_capacity': '1.2L Petrol', 'power_hp': 80,
        'price_per_day': Decimal('1400.00'), 'security_deposit': Decimal('4000.00'),
        # 'main_image_path': 'media/cars/maruti_dzire.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/dzire_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/dzire_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/dzire_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Excellent Fuel Economy', 'Automatic Transmission',
            'Rear Camera', 'Touchscreen Infotainment', 'Large Boot'
        ],
        'description': 'Budget-friendly sedan ideal for affordable weekend trips to Digha, Mandarmani and nearby destinations.',
        'status': 'AVAILABLE'
    },

    {
        'brand': 'Hyundai', 'model': 'Creta', 'year': 2025, 'license_plate': 'WB-19-TRIP-01',
        'category': cat_map['suv'], 'location': loc_shantiniketan,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 5,
        'luggage_capacity': 3, 'mileage_limit': '300 km/day',
        'engine_capacity': '1.5L Petrol', 'power_hp': 113,
        'price_per_day': Decimal('2700.00'), 'security_deposit': Decimal('7500.00'),
        # 'main_image_path': 'media/cars/hyundai_creta.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/creta_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/creta_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/creta_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Panoramic Sunroof', 'ADAS', 'Ventilated Seats',
            '360-Degree Camera', 'Cruise Control', 'Connected Car Technology'
        ],
        'description': 'Comfortable crossover SUV ideal for weekend trips to Shantiniketan, Bishnupur and other destinations.',
        'status': 'AVAILABLE'
    },

    # ==================== ADDITIONAL PREMIUM CAR ====================
    {
        'brand': 'Audi', 'model': 'A4', 'year': 2024, 'license_plate': 'WB-20-LUX-03',
        'category': cat_map['luxury'], 'location': loc_new_town,
        'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
        'luggage_capacity': 3, 'mileage_limit': '200 km/day',
        'engine_capacity': '2.0L TFSI Turbo Petrol', 'power_hp': 187,
        'price_per_day': Decimal('8500.00'), 'security_deposit': Decimal('22000.00'),
        # 'main_image_path': 'media/cars/audi_a4.jpg',
        'main_image_url': 'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1200&q=80',
        # 'gallery_image_paths': [
        #     {'path': 'media/car_gallery/audi_a4_front.jpg', 'view_type': 'FRONT'},
        #     {'path': 'media/car_gallery/audi_a4_side.jpg', 'view_type': 'SIDE'},
        #     {'path': 'media/car_gallery/audi_a4_interior.jpg', 'view_type': 'INTERIOR'},
        # ],
        'features': [
            'Virtual Cockpit', 'Leather Seats', 'LED Matrix Headlights',
            'Premium Audio', 'Cruise Control', 'Wireless Charging'
        ],
        'description': 'Premium executive sedan for corporate travel, weddings, events and luxury journeys in Kolkata.',
        'status': 'AVAILABLE'
    },
]

        created_cars = []
        for cdata in cars_data:
            data = cdata.copy()
            main_image_path = data.pop('main_image_path', None) or data.pop('image_location', None)
            main_image_url = data.pop('main_image_url', None)
            gallery_paths = data.pop('gallery_image_paths', []) or data.pop('gallery_locations', [])
            gallery_urls = data.pop('gallery_urls', [])

            license_plate = data['license_plate']
            car_obj, created = Car.objects.get_or_create(license_plate=license_plate, defaults=data)

            # 1. Attach Local File if path provided and exists
            image_saved = False
            if main_image_path:
                resolved_path = main_image_path if os.path.isabs(main_image_path) else os.path.join(settings.BASE_DIR, main_image_path)
                if os.path.isfile(resolved_path):
                    with open(resolved_path, 'rb') as f:
                        VehicleService.upload_and_save_main_image(car_obj, f, filename=os.path.basename(resolved_path))
                    image_saved = True

            # 2. If no local image and car has no main_image_path, download from URL and upload to Supabase
            if not image_saved and not car_obj.main_image_path:
                if main_image_url:
                    VehicleService.download_and_save_main_image(car_obj, main_image_url)
                else:
                    # Deterministic storage path fallback
                    car_obj.main_image_path = f"cars/{car_obj.id}/main.jpg"
                    car_obj.save(update_fields=['main_image_path'])

            # 3. Attach Local Gallery Files
            for g_item in gallery_paths:
                g_path = g_item if isinstance(g_item, str) else g_item.get('path')
                v_type = 'OTHER' if isinstance(g_item, str) else g_item.get('view_type', 'OTHER')
                if g_path:
                    res_g_path = g_path if os.path.isabs(g_path) else os.path.join(settings.BASE_DIR, g_path)
                    if os.path.isfile(res_g_path) and not car_obj.images.filter(view_type=v_type).exists():
                        with open(res_g_path, 'rb') as gf:
                            VehicleService.handle_gallery_uploads(car_obj, [gf], [v_type], [f"{v_type} View"])

            # 4. Download Gallery Images from URLs if provided
            for idx, g_url_item in enumerate(gallery_urls):
                u_url = g_url_item if isinstance(g_url_item, str) else g_url_item.get('url')
                v_type = 'OTHER' if isinstance(g_url_item, str) else g_url_item.get('view_type', 'OTHER')
                if u_url and not car_obj.images.filter(view_type=v_type).exists():
                    VehicleService.download_and_save_gallery_image(car_obj, u_url, view_type=v_type)

            created_cars.append(car_obj)

        # 5. Coupons
        Coupon.objects.get_or_create(
            code='DRIVE20',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('20.00'),
                'min_booking_amount': Decimal('3000.00'),
                'max_discount_amount': Decimal('1500.00'),
                'is_active': True
            }
        )

        Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('10.00'),
                'min_booking_amount': Decimal('1000.00'),
                'max_discount_amount': Decimal('1000.00'),
                'is_active': True
            }
        )

        Coupon.objects.get_or_create(
            code='WEEKEND500',
            defaults={
                'discount_type': 'FIXED',
                'discount_value': Decimal('500.00'),
                'min_booking_amount': Decimal('3000.00'),
                'is_active': True
            }
        )

        Coupon.objects.get_or_create(
            code='TRIP1000',
            defaults={
                'discount_type': 'FIXED',
                'discount_value': Decimal('1000.00'),
                'min_booking_amount': Decimal('7000.00'),
                'is_active': True
            }
        )

        Coupon.objects.get_or_create(
            code='WESTBENGAL15',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('15.00'),
                'min_booking_amount': Decimal('5000.00'),
                'max_discount_amount': Decimal('2000.00'),
                'is_active': True
            }
        )
        
        # 6. Sample Bookings & Reviews
        swift_car = created_cars[0]       # Maruti Suzuki Swift
        city_car = created_cars[1]        # Honda City
        creta_car = created_cars[2]       # Hyundai Creta
        innova_car = created_cars[3]      # Toyota Innova Crysta

        now = timezone.now()

        # ============================================================
        # Completed Booking 1 - Rahul (Maruti Suzuki Swift)
        # ============================================================
        b1, _ = Booking.objects.get_or_create(
            booking_code='DL-2026-SWFT01',
            defaults={
                'customer': rahul,
                'car': swift_car,
                'pickup_location': loc_kolkata_airport,
                'return_location': loc_kolkata_airport,
                'start_date': now - datetime.timedelta(days=12),
                'end_date': now - datetime.timedelta(days=9),
                'total_days': 3,
                'daily_rate': swift_car.price_per_day,
                'rental_charge': swift_car.price_per_day * 3,
                'insurance_plan': 'STANDARD',
                'insurance_amount': Decimal('450.00'),
                'tax_amount': Decimal('630.00'),
                'deposit_amount': Decimal('5000.00'),
                'total_amount': (
                    swift_car.price_per_day * 3
                    + Decimal('450.00')
                    + Decimal('630.00')
                ),
                'status': 'COMPLETED',
                'payment_status': 'PAID',
                'driver_name': 'Rahul Sharma',
                'driver_phone': '+919876543210',
                'driver_email': 'rahul.sharma@example.com',
                'driver_license': 'WB-0120260012345'
            }
        )

        Payment.objects.get_or_create(
            booking=b1,
            defaults={
                'transaction_id': 'TXN-DL-001',
                'provider': 'RAZORPAY',
                'amount': b1.total_amount,
                'currency': 'INR',
                'status': 'SUCCESS',
                'payment_method': 'UPI'
            }
        )

        Review.objects.get_or_create(
            booking=b1,
            defaults={
                'car': swift_car,
                'customer': rahul,
                'rating': 5,
                'title': 'Perfect car for Kolkata city travel',
                'comment': (
                    'The Swift was clean and well maintained. Pickup at Kolkata '
                    'Airport was smooth and the car was very easy to drive through '
                    'Kolkata traffic. The booking process was quick and convenient.'
                ),
                'is_approved': True
            }
        )


        # ============================================================
        # Completed Booking 2 - Priya (Honda City)
        # ============================================================
        b2, _ = Booking.objects.get_or_create(
            booking_code='DL-2026-CITY02',
            defaults={
                'customer': priya,
                'car': city_car,
                'pickup_location': loc_park_street,
                'return_location': loc_park_street,
                'start_date': now - datetime.timedelta(days=8),
                'end_date': now - datetime.timedelta(days=5),
                'total_days': 3,
                'daily_rate': city_car.price_per_day,
                'rental_charge': city_car.price_per_day * 3,
                'insurance_plan': 'PREMIUM',
                'insurance_amount': Decimal('900.00'),
                'tax_amount': Decimal('1100.00'),
                'deposit_amount': Decimal('10000.00'),
                'total_amount': (
                    city_car.price_per_day * 3
                    + Decimal('900.00')
                    + Decimal('1100.00')
                ),
                'status': 'COMPLETED',
                'payment_status': 'PAID',
                'driver_name': 'Priya Banerjee',
                'driver_phone': '+919876543211',
                'driver_email': 'priya.banerjee@example.com',
                'driver_license': 'WB-0220260067890'
            }
        )

        Payment.objects.get_or_create(
            booking=b2,
            defaults={
                'transaction_id': 'TXN-DL-002',
                'provider': 'RAZORPAY',
                'amount': b2.total_amount,
                'currency': 'INR',
                'status': 'SUCCESS',
                'payment_method': 'VISA (•••• 4242)'
            }
        )

        Review.objects.get_or_create(
            booking=b2,
            defaults={
                'car': city_car,
                'customer': priya,
                'rating': 5,
                'title': 'Excellent car for a weekend trip',
                'comment': (
                    'The Honda City was comfortable and smooth throughout the trip. '
                    'We used it for a Kolkata to Shantiniketan journey. The pickup '
                    'and return process was simple and the vehicle was in excellent condition.'
                ),
                'is_approved': True
            }
        )


        # ============================================================
        # Active Ongoing Booking - Arjun (Hyundai Creta)
        # ============================================================
        b3, _ = Booking.objects.get_or_create(
            booking_code='DL-2026-CRET03',
            defaults={
                'customer': priya,
                'car': creta_car,
                'pickup_location': loc_siliguri,
                'return_location': loc_darjeeling,
                'start_date': now - datetime.timedelta(days=1),
                'end_date': now + datetime.timedelta(days=3),
                'total_days': 4,
                'daily_rate': creta_car.price_per_day,
                'rental_charge': creta_car.price_per_day * 4,
                'insurance_plan': 'PREMIUM',
                'insurance_amount': Decimal('1200.00'),
                'tax_amount': Decimal('1500.00'),
                'deposit_amount': Decimal('15000.00'),
                'total_amount': (
                    creta_car.price_per_day * 4
                    + Decimal('1200.00')
                    + Decimal('1500.00')
                ),
                'status': 'ONGOING',
                'payment_status': 'PAID',
                'driver_name': 'Arjun Das',
                'driver_phone': '+919876543212',
                'driver_email': 'arjun.das@example.com',
                'driver_license': 'WB-0320260045678'
            }
        )

        Payment.objects.get_or_create(
            booking=b3,
            defaults={
                'transaction_id': 'TXN-DL-003',
                'provider': 'RAZORPAY',
                'amount': b3.total_amount,
                'currency': 'INR',
                'status': 'SUCCESS',
                'payment_method': 'RAZORPAY UPI'
            }
        )


        # ============================================================
        # Upcoming Booking - Sneha (Toyota Innova Crysta)
        # ============================================================
        b4, _ = Booking.objects.get_or_create(
            booking_code='DL-2026-INNV04',
            defaults={
                'customer': rahul,
                'car': innova_car,
                'pickup_location': loc_new_town,
                'return_location': loc_digha,
                'start_date': now + datetime.timedelta(days=3),
                'end_date': now + datetime.timedelta(days=6),
                'total_days': 3,
                'daily_rate': innova_car.price_per_day,
                'rental_charge': innova_car.price_per_day * 3,
                'insurance_plan': 'PREMIUM',
                'insurance_amount': Decimal('1500.00'),
                'tax_amount': Decimal('1800.00'),
                'deposit_amount': Decimal('20000.00'),
                'total_amount': (
                    innova_car.price_per_day * 3
                    + Decimal('1500.00')
                    + Decimal('1800.00')
                ),
                'status': 'CONFIRMED',
                'payment_status': 'PAID',
                'driver_name': 'Sneha Mukherjee',
                'driver_phone': '+919876543213',
                'driver_email': 'sneha.mukherjee@example.com',
                'driver_license': 'WB-0420260098765'
            }
        )

        Payment.objects.get_or_create(
            booking=b4,
            defaults={
                'transaction_id': 'TXN-DL-004',
                'provider': 'RAZORPAY',
                'amount': b4.total_amount,
                'currency': 'INR',
                'status': 'SUCCESS',
                'payment_method': 'UPI'
            }
        )


        # ============================================================
        # Notifications
        # ============================================================

        Notification.objects.get_or_create(
            user=priya,
            title='Upcoming Return Reminder',
            defaults={
                'message': (
                    f'Your ongoing rental for {creta_car.display_name} is scheduled '
                    'for return at Darjeeling Hub in 3 days.'
                ),
                'type': 'REMINDER'
            }
        )

        Notification.objects.get_or_create(
            user=rahul,
            title='Booking Confirmed',
            defaults={
                'message': (
                    f'Your booking for {innova_car.display_name} from New Town '
                    'to Digha has been confirmed successfully.'
                ),
                'type': 'BOOKING'
            }
        )

        Notification.objects.get_or_create(
            user=rahul,
            title='Special 20% Off Promotion',
            defaults={
                'message': (
                    'Use promo code DRIVE20 on your next booking and enjoy '
                    '20% off on selected vehicles!'
                ),
                'type': 'PROMO'
            }
        )

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('Admin Login: asim / asim123 (or OTP with 9734635590)'))
        self.stdout.write(self.style.SUCCESS('Customer Login: rahul / rahul123 (or OTP with 9835754632)'))
