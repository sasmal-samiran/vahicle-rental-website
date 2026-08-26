import os
import datetime
from decimal import Decimal
from django.core.files import File
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.vehicles.models import Category, Location, Car, CarImage
from apps.vehicles.services import download_and_save_car_image, download_and_save_gallery_image
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
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@carrental.com',
                'phone_number': '+18005550199',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_phone_verified': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        alex, _ = User.objects.get_or_create(
            username='alex_morgan',
            defaults={
                'email': 'alex@example.com',
                'phone_number': '+15551234567',
                'first_name': 'Alex',
                'last_name': 'Morgan',
                'role': 'CUSTOMER',
                'driver_license_number': 'DL-NY-9847291',
                'address': '742 Evergreen Terrace',
                'city': 'New York',
                'is_phone_verified': True
            }
        )
        alex.set_password('user123')
        alex.save()

        sarah, _ = User.objects.get_or_create(
            username='sarah_j',
            defaults={
                'email': 'sarah@example.com',
                'phone_number': '+15559876543',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'role': 'CUSTOMER',
                'driver_license_number': 'DL-CA-4491028',
                'address': '120 Ocean Avenue',
                'city': 'Los Angeles',
                'is_phone_verified': True
            }
        )
        sarah.set_password('user123')
        sarah.save()

        # 2. Categories
        categories_data = [
            {'name': 'Luxury & Executive', 'slug': 'luxury', 'icon': 'fa-crown', 'description': 'Premium luxury sedans and executive cruisers with supreme comfort.', 'image_url': 'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Electric & Hybrid', 'slug': 'electric', 'icon': 'fa-bolt', 'description': 'Eco-friendly high-tech zero-emission vehicles with instant torque.', 'image_url': 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=600&q=80'},
            {'name': 'SUVs & Crossovers', 'slug': 'suv', 'icon': 'fa-mountain', 'description': 'Spacious and capable vehicles suited for family trips and mountain adventures.', 'image_url': 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Sports & Performance', 'slug': 'sports', 'icon': 'fa-fire', 'description': 'Exhilarating acceleration, precise handling, and pure driving thrill.', 'image_url': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Sedans', 'slug': 'sedan', 'icon': 'fa-car-side', 'description': 'Comfortable, fuel-efficient daily commuter sedans with modern amenities.', 'image_url': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=600&q=80'},
            {'name': 'Compact & Hatchback', 'slug': 'compact', 'icon': 'fa-car', 'description': 'Agile, easy to park, and extremely fuel-efficient city cars.', 'image_url': 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=600&q=80'},
        ]
        
        cat_map = {}
        for cat in categories_data:
            c_obj, _ = Category.objects.get_or_create(slug=cat['slug'], defaults=cat)
            cat_map[cat['slug']] = c_obj

        # 3. Hub Locations
        locations_data = [
            {'name': 'Downtown Manhattan Hub', 'city': 'New York', 'address': '450 Lexington Ave, New York, NY 10017', 'phone': '+1 (212) 555-0144', 'email': 'manhattan@carrental.com'},
            {'name': 'JFK International Airport (T4)', 'city': 'New York', 'address': 'JFK Terminal 4 Rental Concourse, Jamaica, NY 11430', 'phone': '+1 (718) 555-0192', 'email': 'jfk@carrental.com'},
            {'name': 'LAX Airport Fleet Hub', 'city': 'Los Angeles', 'address': '9217 Airport Blvd, Los Angeles, CA 90045', 'phone': '+1 (310) 555-0188', 'email': 'lax@carrental.com'},
            {'name': 'San Francisco Union Square', 'city': 'San Francisco', 'address': '333 Post St, San Francisco, CA 94108', 'phone': '+1 (415) 555-0120', 'email': 'sf@carrental.com'},
            {'name': 'Miami South Beach Hub', 'city': 'Miami', 'address': '1100 Ocean Drive, Miami Beach, FL 33139', 'phone': '+1 (305) 555-0177', 'email': 'miami@carrental.com'},
            {'name': 'Chicago O\'Hare Airport Hub', 'city': 'Chicago', 'address': '10000 W O\'Hare Ave, Chicago, IL 60666', 'phone': '+1 (773) 555-0163', 'email': 'chicago@carrental.com'},
        ]

        loc_objs = []
        for loc in locations_data:
            l_obj, _ = Location.objects.get_or_create(name=loc['name'], defaults=loc)
            loc_objs.append(l_obj)

        loc_ny = loc_objs[0]
        loc_jfk = loc_objs[1]
        loc_lax = loc_objs[2]
        loc_sf = loc_objs[3]
        loc_miami = loc_objs[4]
        loc_chicago = loc_objs[5]

        # 4. Fleet of Cars
        cars_data = [
            {
                'brand': 'Tesla', 'model': 'Model S Plaid', 'year': 2024, 'license_plate': 'NY-TSLA-01',
                'category': cat_map['electric'], 'location': loc_ny,
                'transmission': 'AUTOMATIC', 'fuel_type': 'ELECTRIC', 'seats': 5, 'doors': 4,
                'luggage_capacity': 4, 'mileage_limit': 'Unlimited', 'engine_capacity': 'Tri-Motor All-Wheel Drive',
                'power_hp': 1020, 'price_per_day': Decimal('189.00'), 'security_deposit': Decimal('300.00'),
                'main_image_path': 'media/cars/tesla_model_s.jpg',  # Provide local file path / image location here
                'main_image_url': 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=1200&q=80',
                'gallery_image_paths': [
                    {'path': 'media/car_gallery/tesla_front.jpg', 'view_type': 'FRONT'},
                    {'path': 'media/car_gallery/tesla_side.jpg', 'view_type': 'SIDE'},
                    {'path': 'media/car_gallery/tesla_interior.jpg', 'view_type': 'INTERIOR'},
                ],
                'features': ['Full Self-Driving Capability', 'Yoke Steering Wheel', '17-inch Cinematic Display', 'Panoramic Glass Roof', 'Ventilated Heated Seats', 'Wireless Phone Charging', 'Premium 22-Speaker Audio'],
                'description': 'Experience supercar performance in a whisper-quiet luxury electric sedan. 0-60 mph in 1.99s with over 390 miles of range.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Porsche', 'model': '911 Carrera S', 'year': 2024, 'license_plate': 'CA-PRSH-911',
                'category': cat_map['sports'], 'location': loc_lax,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 4, 'doors': 2,
                'luggage_capacity': 2, 'mileage_limit': '200 miles/day', 'engine_capacity': '3.0L Twin-Turbo Boxer 6',
                'power_hp': 443, 'price_per_day': Decimal('249.00'), 'security_deposit': Decimal('500.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80',
                'features': ['Sport Chrono Package', 'PDK 8-Speed Dual-Clutch', 'Bose Surround Sound', 'Active Suspension (PASM)', 'Sport Exhaust System', 'Apple CarPlay & Android Auto', 'Keyless Entry'],
                'description': 'The definitive sports car. Unmatched balance, iconic silhouette, razor-sharp throttle response, and breathtaking handling.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'BMW', 'model': 'M4 Competition Coupe', 'year': 2024, 'license_plate': 'NY-BMWM-04',
                'category': cat_map['sports'], 'location': loc_jfk,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 4, 'doors': 2,
                'luggage_capacity': 3, 'mileage_limit': '250 miles/day', 'engine_capacity': '3.0L BMW M TwinPower Turbo',
                'power_hp': 503, 'price_per_day': Decimal('195.00'), 'security_deposit': Decimal('400.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1200&q=80',
                'features': ['M Carbon Bucket Seats', 'Harman Kardon Audio', 'Head-Up Display', 'M xDrive AWD System', 'Adaptive M Suspension', 'Carbon Fiber Roof'],
                'description': 'High-performance coupe precision engineered by BMW M GmbH. Exhilarating power meets daily drivability.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Mercedes-Benz', 'model': 'C300 4MATIC AMG Line', 'year': 2023, 'license_plate': 'FL-MBZ-300',
                'category': cat_map['luxury'], 'location': loc_miami,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
                'luggage_capacity': 3, 'mileage_limit': 'Unlimited', 'engine_capacity': '2.0L Inline-4 Turbo w/ Mild Hybrid',
                'power_hp': 255, 'price_per_day': Decimal('115.00'), 'security_deposit': Decimal('200.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1200&q=80',
                'features': ['Burmester 3D Surround Sound', '64-Color Ambient Lighting', 'MBUX Augmented Video Navigation', 'Panoramic Sunroof', 'Blind Spot Assist', 'Heated Steering Wheel'],
                'description': 'Sophisticated German engineering with cutting-edge digital cockpit and smooth, responsive driving dynamics.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Audi', 'model': 'Q7 55 TFSI Prestige', 'year': 2024, 'license_plate': 'IL-AUDI-07',
                'category': cat_map['suv'], 'location': loc_chicago,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 7, 'doors': 4,
                'luggage_capacity': 5, 'mileage_limit': 'Unlimited', 'engine_capacity': '3.0L V6 Turbocharged Quattro',
                'power_hp': 335, 'price_per_day': Decimal('155.00'), 'security_deposit': Decimal('250.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1541348263662-e0c866c5c9e1?auto=format&fit=crop&w=1200&q=80',
                'features': ['3 Rows / 7 Passenger Seating', 'Audi Virtual Cockpit Plus', 'Bang & Olufsen 3D Premium Sound', 'Adaptive Air Suspension', 'Top-View 360 Camera', 'Wireless Apple CarPlay'],
                'description': 'The ultimate luxury 3-row family SUV with Quattro all-weather confidence and premium acoustic glass cabin.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Land Rover', 'model': 'Range Rover Sport HSE', 'year': 2024, 'license_plate': 'CA-RRSP-88',
                'category': cat_map['luxury'], 'location': loc_sf,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
                'luggage_capacity': 4, 'mileage_limit': 'Unlimited', 'engine_capacity': '3.0L Turbocharged i6 MHEV',
                'power_hp': 395, 'price_per_day': Decimal('220.00'), 'security_deposit': Decimal('400.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1606016159991-dfe4f2746ad5?auto=format&fit=crop&w=1200&q=80',
                'features': ['Dynamic Air Suspension', 'Meridian Signature Sound System', 'Pivi Pro Curved Touchscreen', 'Terrain Response 2', 'Massage Seats', 'Soft-Close Doors'],
                'description': 'Peerless luxury meets commanding all-terrain capability. Effortless power and refined road manners.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Ford', 'model': 'Mustang GT 5.0 V8 Convertible', 'year': 2023, 'license_plate': 'FL-MSTG-50',
                'category': cat_map['sports'], 'location': loc_miami,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 4, 'doors': 2,
                'luggage_capacity': 2, 'mileage_limit': 'Unlimited', 'engine_capacity': '5.0L Ti-VCT Coyote V8',
                'power_hp': 450, 'price_per_day': Decimal('130.00'), 'security_deposit': Decimal('250.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=1200&q=80',
                'features': ['Power Retractable Soft-Top', 'Active Valve Performance Exhaust', 'Brembo 6-Piston Brakes', 'B&O 12-Speaker Sound', 'Digital Instrument Cluster'],
                'description': 'Iconic American muscle car with a roaring 5.0L V8 and open-top cruising thrill perfect for the coast.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Tesla', 'model': 'Model Y Long Range AWD', 'year': 2024, 'license_plate': 'CA-TSLA-0Y',
                'category': cat_map['electric'], 'location': loc_sf,
                'transmission': 'AUTOMATIC', 'fuel_type': 'ELECTRIC', 'seats': 5, 'doors': 4,
                'luggage_capacity': 5, 'mileage_limit': 'Unlimited', 'engine_capacity': 'Dual Motor All-Wheel Drive',
                'power_hp': 384, 'price_per_day': Decimal('129.00'), 'security_deposit': Decimal('200.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1561580125-028ee3bd62eb?auto=format&fit=crop&w=1200&q=80',
                'features': ['Autopilot Convenience Features', 'Huge Glass Roof', '330 Miles Range', 'HEPA Filtration System', 'Camp Mode & Dog Mode', 'Supercharger Access'],
                'description': 'The world’s best-selling electric crossover. Superb efficiency, maximum cargo versatility, and instant acceleration.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Toyota', 'model': 'RAV4 Hybrid XSE AWD', 'year': 2024, 'license_plate': 'NY-TYTA-04',
                'category': cat_map['suv'], 'location': loc_ny,
                'transmission': 'AUTOMATIC', 'fuel_type': 'HYBRID', 'seats': 5, 'doors': 4,
                'luggage_capacity': 4, 'mileage_limit': 'Unlimited', 'engine_capacity': '2.5L 4-Cylinder Hybrid System',
                'power_hp': 219, 'price_per_day': Decimal('75.00'), 'security_deposit': Decimal('150.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1581540222194-0def2dda95b8?auto=format&fit=crop&w=1200&q=80',
                'features': ['40 MPG City/Highway', 'Toyota Safety Sense 2.5', 'JBL Premium Audio', 'Heated Front Seats', 'Apple CarPlay & Android Auto'],
                'description': 'Reliable, highly fuel-efficient hybrid SUV ideal for road trips and city adventures alike.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Hyundai', 'model': 'Ioniq 5 Limited AWD', 'year': 2024, 'license_plate': 'IL-HYUN-05',
                'category': cat_map['electric'], 'location': loc_chicago,
                'transmission': 'AUTOMATIC', 'fuel_type': 'ELECTRIC', 'seats': 5, 'doors': 4,
                'luggage_capacity': 4, 'mileage_limit': 'Unlimited', 'engine_capacity': 'Dual Electric Motor AWD',
                'power_hp': 320, 'price_per_day': Decimal('95.00'), 'security_deposit': Decimal('200.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1200&q=80',
                'features': ['Ultra-Fast 800V DC Charging', 'Vehicle-to-Load (V2L) Power', 'Sliding Center Console', 'Head-Up Display with AR', 'Smart Cruise Control'],
                'description': 'Award-winning futuristic electric SUV with spacious lounge interior and lightning-fast charging capability.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Honda', 'model': 'Civic Touring Sedan', 'year': 2023, 'license_plate': 'CA-HND-10',
                'category': cat_map['sedan'], 'location': loc_lax,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
                'luggage_capacity': 3, 'mileage_limit': 'Unlimited', 'engine_capacity': '1.5L Turbo 4-Cylinder',
                'power_hp': 180, 'price_per_day': Decimal('59.00'), 'security_deposit': Decimal('150.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1590362891991-f776e747a588?auto=format&fit=crop&w=1200&q=80',
                'features': ['Leather Trimmed Seats', 'Bose 12-Speaker Audio', 'Wireless Apple CarPlay', 'Honda Sensing Suite', 'Moonroof'],
                'description': 'Smooth, comfortable, and economic executive compact sedan with class-leading safety features.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Volkswagen', 'model': 'Golf GTI Autobahn', 'year': 2024, 'license_plate': 'NY-VW-GTI',
                'category': cat_map['compact'], 'location': loc_jfk,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 5, 'doors': 4,
                'luggage_capacity': 3, 'mileage_limit': 'Unlimited', 'engine_capacity': '2.0L TSI Turbocharged 4-Cyl',
                'power_hp': 241, 'price_per_day': Decimal('68.00'), 'security_deposit': Decimal('150.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1200&q=80',
                'features': ['Sport Tuned Suspension', 'DCC Adaptive Chassis Control', 'Panoramic Sunroof', 'Harman Kardon Audio', 'Clark Plaid Interior Accents'],
                'description': 'The original hot hatchback. Practical 5-door daily driver with sports-car agility and turbo punch.',
                'status': 'AVAILABLE'
            },
            {
                'brand': 'Cadillac', 'model': 'Escalade ESV Premium Luxury', 'year': 2023, 'license_plate': 'FL-CAD-09',
                'category': cat_map['luxury'], 'location': loc_miami,
                'transmission': 'AUTOMATIC', 'fuel_type': 'PETROL', 'seats': 8, 'doors': 4,
                'luggage_capacity': 6, 'mileage_limit': 'Unlimited', 'engine_capacity': '6.2L V8 Engine',
                'power_hp': 420, 'price_per_day': Decimal('275.00'), 'security_deposit': Decimal('500.00'),
                'main_image_url': 'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=80',
                'features': ['38-inch Curved OLED Display', 'AKG Studio 36-Speaker Audio', 'Rear Seat Entertainment', 'Super Cruise Hands-Free Driving', 'Magnetic Ride Control'],
                'description': 'The pinnacle of American full-size luxury SUVs. Seating for 8 VIPs with immense luggage volume.',
                'status': 'AVAILABLE'
            },
        ]

        created_cars = []
        for cdata in cars_data:
            data = cdata.copy()
            main_image_path = data.pop('main_image_path', None) or data.pop('image_location', None)
            main_image_url = data.get('main_image_url')
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
                        car_obj.main_image.save(os.path.basename(resolved_path), File(f), save=True)
                    image_saved = True
                else:
                    self.stdout.write(self.style.WARNING(f'Notice: Local image file not found at {resolved_path}.'))

            # 2. If no local image, download from main_image_url, save to media/cars/ and store path in DB
            if not image_saved and main_image_url and not car_obj.main_image:
                self.stdout.write(f'Downloading image for {car_obj.display_name} from URL...')
                download_and_save_car_image(car_obj, main_image_url)

            # 3. Attach Local Gallery Files
            for g_item in gallery_paths:
                g_path = g_item if isinstance(g_item, str) else g_item.get('path')
                v_type = 'OTHER' if isinstance(g_item, str) else g_item.get('view_type', 'OTHER')
                if g_path:
                    res_g_path = g_path if os.path.isabs(g_path) else os.path.join(settings.BASE_DIR, g_path)
                    if os.path.isfile(res_g_path):
                        with open(res_g_path, 'rb') as gf:
                            CarImage.objects.get_or_create(
                                car=car_obj,
                                view_type=v_type,
                                defaults={'image': File(gf, name=os.path.basename(res_g_path))}
                            )

            # 4. Download Gallery Images from URLs if provided
            for g_url_item in gallery_urls:
                u_url = g_url_item if isinstance(g_url_item, str) else g_url_item.get('url')
                v_type = 'OTHER' if isinstance(g_url_item, str) else g_url_item.get('view_type', 'OTHER')
                if u_url and not car_obj.images.filter(view_type=v_type).exists():
                    download_and_save_gallery_image(car_obj, u_url, view_type=v_type)

            created_cars.append(car_obj)

        # 5. Coupons
        Coupon.objects.get_or_create(
            code='DRIVE20',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('20.00'),
                'min_booking_amount': Decimal('50.00'),
                'max_discount_amount': Decimal('200.00'),
                'is_active': True
            }
        )
        Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('10.00'),
                'min_booking_amount': Decimal('30.00'),
                'is_active': True
            }
        )
        Coupon.objects.get_or_create(
            code='WEEKEND50',
            defaults={
                'discount_type': 'FIXED',
                'discount_value': Decimal('50.00'),
                'min_booking_amount': Decimal('200.00'),
                'is_active': True
            }
        )

        # 6. Sample Bookings & Reviews
        tesla_car = created_cars[0] # Tesla Model S
        porsche_car = created_cars[1] # Porsche 911
        bmw_car = created_cars[2] # BMW M4
        mbz_car = created_cars[3] # Mercedes C300

        now = timezone.now()

        # Completed Booking 1 for Alex (Tesla)
        b1, _ = Booking.objects.get_or_create(
            booking_code='CR-2026-TSLA01',
            defaults={
                'customer': alex,
                'car': tesla_car,
                'pickup_location': loc_ny,
                'return_location': loc_ny,
                'start_date': now - datetime.timedelta(days=12),
                'end_date': now - datetime.timedelta(days=9),
                'total_days': 3,
                'daily_rate': tesla_car.price_per_day,
                'rental_charge': tesla_car.price_per_day * 3,
                'insurance_plan': 'PREMIUM',
                'insurance_amount': Decimal('84.00'),
                'tax_amount': Decimal('65.10'),
                'deposit_amount': Decimal('300.00'),
                'total_amount': Decimal('1016.10'),
                'status': 'COMPLETED',
                'payment_status': 'PAID',
                'driver_name': 'Alex Morgan',
                'driver_phone': '+15551234567',
                'driver_email': 'alex@example.com',
                'driver_license': 'DL-NY-9847291'
            }
        )
        Payment.objects.get_or_create(
            booking=b1,
            defaults={
                'transaction_id': 'TXN-DEMO-001',
                'provider': 'SANDBOX',
                'amount': b1.total_amount,
                'currency': 'USD',
                'status': 'SUCCESS',
                'payment_method': 'VISA (•••• 4242)'
            }
        )
        Review.objects.get_or_create(
            booking=b1,
            defaults={
                'car': tesla_car,
                'customer': alex,
                'rating': 5,
                'title': 'Unbelievable acceleration and flawless booking experience!',
                'comment': 'The Tesla Model S Plaid was in pristine showroom condition with 100% battery at pickup. The instant OTP login and digital checkout took less than 2 minutes. Will definitely rent again!',
                'is_approved': True
            }
        )

        # Completed Booking 2 for Sarah (Porsche)
        b2, _ = Booking.objects.get_or_create(
            booking_code='CR-2026-PRSH02',
            defaults={
                'customer': sarah,
                'car': porsche_car,
                'pickup_location': loc_lax,
                'return_location': loc_lax,
                'start_date': now - datetime.timedelta(days=6),
                'end_date': now - datetime.timedelta(days=4),
                'total_days': 2,
                'daily_rate': porsche_car.price_per_day,
                'rental_charge': porsche_car.price_per_day * 2,
                'insurance_plan': 'STANDARD',
                'insurance_amount': Decimal('30.00'),
                'tax_amount': Decimal('52.80'),
                'deposit_amount': Decimal('500.00'),
                'total_amount': Decimal('1080.80'),
                'status': 'COMPLETED',
                'payment_status': 'PAID',
                'driver_name': 'Sarah Jenkins',
                'driver_phone': '+15559876543',
                'driver_email': 'sarah@example.com',
                'driver_license': 'DL-CA-4491028'
            }
        )
        Payment.objects.get_or_create(
            booking=b2,
            defaults={
                'transaction_id': 'TXN-DEMO-002',
                'provider': 'STRIPE',
                'amount': b2.total_amount,
                'currency': 'USD',
                'status': 'SUCCESS',
                'payment_method': 'MASTERCARD (•••• 8812)'
            }
        )
        Review.objects.get_or_create(
            booking=b2,
            defaults={
                'car': porsche_car,
                'customer': sarah,
                'rating': 5,
                'title': 'Drove down Pacific Coast Highway - unforgettable!',
                'comment': 'The Carrera S was pure perfection on PCH. Pick up at LAX was frictionless and customer support was wonderful.',
                'is_approved': True
            }
        )

        # Active Ongoing Booking (BMW M4)
        b3, _ = Booking.objects.get_or_create(
            booking_code='CR-2026-BMWM03',
            defaults={
                'customer': alex,
                'car': bmw_car,
                'pickup_location': loc_jfk,
                'return_location': loc_jfk,
                'start_date': now - datetime.timedelta(days=1),
                'end_date': now + datetime.timedelta(days=2),
                'total_days': 3,
                'daily_rate': bmw_car.price_per_day,
                'rental_charge': bmw_car.price_per_day * 3,
                'insurance_plan': 'PREMIUM',
                'insurance_amount': Decimal('84.00'),
                'tax_amount': Decimal('66.90'),
                'deposit_amount': Decimal('400.00'),
                'total_amount': Decimal('1135.90'),
                'status': 'ONGOING',
                'payment_status': 'PAID',
                'driver_name': 'Alex Morgan',
                'driver_phone': '+15551234567',
                'driver_email': 'alex@example.com',
                'driver_license': 'DL-NY-9847291'
            }
        )
        Payment.objects.get_or_create(
            booking=b3,
            defaults={
                'transaction_id': 'TXN-DEMO-003',
                'provider': 'RAZORPAY',
                'amount': b3.total_amount,
                'currency': 'USD',
                'status': 'SUCCESS',
                'payment_method': 'RAZORPAY_UPI'
            }
        )

        # Notifications
        Notification.objects.get_or_create(
            user=alex,
            title='Upcoming Return Reminder',
            defaults={
                'message': f'Your ongoing rental for {bmw_car.display_name} is scheduled for return at JFK Airport in 2 days.',
                'type': 'REMINDER'
            }
        )
        Notification.objects.get_or_create(
            user=alex,
            title='Special 20% Off Promotion',
            defaults={
                'message': 'Use promo code DRIVE20 on your next booking to enjoy 20% off any vehicle!',
                'type': 'PROMO'
            }
        )

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('Admin Login: admin / admin123 (or OTP with +18005550199)'))
        self.stdout.write(self.style.SUCCESS('Customer Login: alex_morgan / user123 (or OTP with +15551234567)'))
