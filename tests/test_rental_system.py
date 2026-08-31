import os
import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.vehicles.models import Category, Location, Car, CarImage
from apps.bookings.models import Booking, Coupon
from apps.bookings.services import PricingService, BookingService
from apps.users.services import OTPService
from apps.payments.models import Payment

User = get_user_model()

class CarRentalSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            phone_number='+18000000001',
            password='AdminPassword123'
        )
        self.customer = User.objects.create_user(
            username='customer_test',
            email='customer@test.com',
            phone_number='+15550000001',
            password='CustomerPassword123',
            role='CUSTOMER'
        )

        # Location & Category
        self.category = Category.objects.create(name='Electric', slug='electric')
        self.location = Location.objects.create(name='Downtown Hub', city='New York', address='123 Main St')

        # Car
        self.car = Car.objects.create(
            brand='Tesla',
            model='Model S Plaid',
            year=2024,
            license_plate='TEST-TSLA-01',
            category=self.category,
            location=self.location,
            transmission='AUTOMATIC',
            fuel_type='ELECTRIC',
            seats=5,
            price_per_day=Decimal('150.00'),
            security_deposit=Decimal('200.00'),
            status='AVAILABLE'
        )

        # Coupon
        self.coupon = Coupon.objects.create(
            code='DRIVE20',
            discount_type='PERCENTAGE',
            discount_value=Decimal('20.00'),
            min_booking_amount=Decimal('50.00'),
            is_active=True
        )

    def test_customer_registration(self):
        # 1. Register new customer
        data = {
            'first_name': 'Emma',
            'last_name': 'Watson',
            'email': 'emma@test.com',
            'phone_number': '+15559990001',
            'driver_license_number': 'DL-NY-847291',
            'password': 'SecurePassword123'
        }
        res = self.client.post('/api/auth/register/', data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])
        self.assertEqual(res.data['user']['email'], 'emma@test.com')
        self.assertEqual(res.data['user']['role'], 'CUSTOMER')

        # 2. Duplicate registration should fail
        dup_res = self.client.post('/api/auth/register/', data)
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_registration_with_otp_verification(self):
        phone = '+15558880001'
        email = 'ron@test.com'

        # 1. Request Registration OTP
        req_res = self.client.post('/api/auth/otp/request/', {'identifier': phone, 'purpose': 'REGISTER'})
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)
        self.assertIn('dev_otp', req_res.data)
        otp = req_res.data['dev_otp']

        # 2. Verify Registration OTP
        verify_res = self.client.post('/api/auth/otp/verify/', {
            'identifier': phone,
            'otp_code': otp,
            'purpose': 'REGISTER'
        })
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_res.data.get('verified'))

        # 3. Complete Registration
        reg_res = self.client.post('/api/auth/register/', {
            'first_name': 'Ron',
            'last_name': 'Weasley',
            'email': email,
            'phone_number': phone,
            'password': 'SecurePassword123'
        })
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', reg_res.data)
        self.assertTrue(reg_res.data['user']['is_phone_verified'])

    def test_unregistered_user_cannot_login(self):
        # Request OTP for non-existent user should return 404
        response = self.client.post('/api/auth/otp/request/', {'identifier': '+19999999999', 'purpose': 'LOGIN'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_otp_flow(self):
        # 1. Request OTP for existing registered customer
        response = self.client.post('/api/auth/otp/request/', {'identifier': '+15550000001', 'purpose': 'LOGIN'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dev_otp', response.data)
        otp_code = response.data['dev_otp']

        # 2. Verify OTP
        verify_res = self.client.post('/api/auth/otp/verify/', {
            'identifier': '+15550000001',
            'otp_code': otp_code,
            'purpose': 'LOGIN'
        })
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', verify_res.data)
        self.assertIn('access', verify_res.data['tokens'])

    def test_pricing_and_coupon_calculation(self):
        now = timezone.now()
        start = now + datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=4) # 3 days

        quote = PricingService.calculate_quote(
            car=self.car,
            start_datetime=start,
            end_datetime=end,
            addon_keys=['gps'], # 199/day * 3 = 597
            insurance_plan='STANDARD', # 9% of 150 = 13.50 -> quantized 14/day * 3 = 42 or dynamic rate
            coupon_code='DRIVE20' # 20% off
        )

        self.assertEqual(quote['total_days'], 3)
        self.assertEqual(quote['rental_charge'], 450.0) # 3 * 150
        self.assertEqual(quote['insurance_amount'], quote['insurance_daily_rate'] * 3)
        self.assertEqual(quote['addons_total'], 597.0) # 3 * 199
        
        subtotal = 450.0 + quote['insurance_amount'] + 597.0
        expected_discount = round(subtotal * 0.20, 2)
        self.assertEqual(quote['discount_amount'], expected_discount)

    def test_date_overlap_availability_logic(self):
        now = timezone.now()
        # Booking: Day 5 to Day 8
        b_start = now + datetime.timedelta(days=5)
        b_end = now + datetime.timedelta(days=8)

        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            pickup_location=self.location,
            return_location=self.location,
            start_date=b_start,
            end_date=b_end,
            total_days=3,
            daily_rate=self.car.price_per_day,
            rental_charge=Decimal('450.00'),
            total_amount=Decimal('500.00'),
            status='CONFIRMED',
            payment_status='PAID',
            driver_name='Alex Test',
            driver_phone='+15550000001'
        )

        # 1. Query during overlap window (Day 6 to Day 7) -> Should NOT be available
        avail_overlapping = BookingService.is_car_available(
            car=self.car,
            start_datetime=now + datetime.timedelta(days=6),
            end_datetime=now + datetime.timedelta(days=7)
        )
        self.assertFalse(avail_overlapping)

        # 2. Query before booking (Day 1 to Day 4) -> Should BE available
        avail_before = BookingService.is_car_available(
            car=self.car,
            start_datetime=now + datetime.timedelta(days=1),
            end_datetime=now + datetime.timedelta(days=4)
        )
        self.assertTrue(avail_before)

        # 3. Query after booking (Day 9 to Day 12) -> Should BE available
        avail_after = BookingService.is_car_available(
            car=self.car,
            start_datetime=now + datetime.timedelta(days=9),
            end_datetime=now + datetime.timedelta(days=12)
        )
        self.assertTrue(avail_after)

        # 4. API /api/cars/ preserves all cars in fleet but marks is_available_for_dates accordingly
        p_date = (now + datetime.timedelta(days=6)).isoformat()
        r_date = (now + datetime.timedelta(days=7)).isoformat()
        api_res = self.client.get(f'/api/cars/?pickup_date={p_date}&return_date={r_date}')
        self.assertEqual(api_res.status_code, status.HTTP_200_OK)
        cars_data = api_res.data if isinstance(api_res.data, list) else api_res.data.get('results', [])
        car_item = next(c for c in cars_data if c['id'] == self.car.id)
        self.assertFalse(car_item['is_available_for_dates']) # Car is NOT excluded from list, but marked unavailable for those dates

        # 5. Test status=RESERVED_FOR_DATES filter returns the reserved car
        reserved_res = self.client.get(f'/api/cars/?pickup_date={p_date}&return_date={r_date}&status=RESERVED_FOR_DATES')
        self.assertEqual(reserved_res.status_code, status.HTTP_200_OK)
        res_cars = reserved_res.data if isinstance(reserved_res.data, list) else reserved_res.data.get('results', [])
        self.assertIn(self.car.id, [c['id'] for c in res_cars])

        # 6. Test status=AVAILABLE filter explicitly excludes reserved cars
        avail_filter_res = self.client.get(f'/api/cars/?pickup_date={p_date}&return_date={r_date}&status=AVAILABLE')
        self.assertEqual(avail_filter_res.status_code, status.HTTP_200_OK)
        avail_cars = avail_filter_res.data if isinstance(avail_filter_res.data, list) else avail_filter_res.data.get('results', [])
        self.assertNotIn(self.car.id, [c['id'] for c in avail_cars])

    def test_search_fallback_with_carsearchservice(self):
        # 1. Exact match works normally
        exact_res = self.client.get(f'/api/cars/?search={self.car.brand}')
        self.assertEqual(exact_res.status_code, status.HTTP_200_OK)
        exact_cars = exact_res.data if isinstance(exact_res.data, list) else exact_res.data.get('results', [])
        self.assertIn(self.car.id, [c['id'] for c in exact_cars])

        # 2. Typo in brand (e.g. 'Telsa' for 'Tesla') fails standard SearchFilter but is rescued by CarSearchService fallback
        typo_res = self.client.get('/api/cars/?search=Telsa')
        self.assertEqual(typo_res.status_code, status.HTTP_200_OK)
        typo_cars = typo_res.data if isinstance(typo_res.data, list) else typo_res.data.get('results', [])
        self.assertTrue(len(typo_cars) > 0)
        self.assertIn(self.car.id, [c['id'] for c in typo_cars])

        # 3. Completely unrecognized query triggers fleet fallback recommendations
        unrecognized_res = self.client.get('/api/cars/?search=nonexistentfuturevehicle')
        self.assertEqual(unrecognized_res.status_code, status.HTTP_200_OK)
        fallback_cars = unrecognized_res.data if isinstance(unrecognized_res.data, list) else unrecognized_res.data.get('results', [])
        self.assertTrue(len(fallback_cars) > 0)

    def test_booking_creation_and_payment_flow(self):
        self.client.force_authenticate(user=self.customer)
        now = timezone.now()
        start = now + datetime.timedelta(days=10)
        end = now + datetime.timedelta(days=13)

        # 1. Create Booking
        res = self.client.post('/api/bookings/', {
            'car_id': self.car.id,
            'pickup_location_id': self.location.id,
            'return_location_id': self.location.id,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'insurance_plan': 'STANDARD',
            'driver_name': 'Test Driver',
            'driver_phone': '+15550000001'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking_code = res.data['booking_code']

        # 2. Process Checkout
        pay_res = self.client.post('/api/payments/mock-checkout/', {
            'booking_code': booking_code,
            'payment_method': 'CARD'
        })
        self.assertEqual(pay_res.status_code, status.HTTP_200_OK)
        self.assertTrue(pay_res.data['success'])

        # 3. Verify booking status changed to CONFIRMED
        booking = Booking.objects.get(booking_code=booking_code)
        self.assertEqual(booking.status, 'CONFIRMED')
        self.assertEqual(booking.payment_status, 'PAID')

    def test_admin_dashboard_stats(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/admin/analytics/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('kpis', res.data)
        self.assertIn('charts', res.data)
        self.assertGreaterEqual(res.data['kpis']['fleet_size'], 1)

    def test_admin_car_image_upload(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=self.admin)

        def make_image(color=(220, 38, 38)):
            f = BytesIO()
            img = Image.new('RGB', (100, 100), color=color)
            img.save(f, 'PNG')
            f.seek(0)
            return f.getvalue()

        main_img = SimpleUploadedFile(name='main.png', content=make_image((200, 0, 0)), content_type='image/png')
        side_img = SimpleUploadedFile(name='side.png', content=make_image((0, 200, 0)), content_type='image/png')
        interior_img = SimpleUploadedFile(name='interior.png', content=make_image((0, 0, 200)), content_type='image/png')

        car_data = {
            'brand': 'Porsche',
            'model': '911 GT3 RS',
            'year': 2024,
            'license_plate': 'TEST-PORSCHE-911',
            'category_id': self.category.id,
            'location_id': self.location.id,
            'transmission': 'AUTOMATIC',
            'fuel_type': 'PETROL',
            'seats': 2,
            'power_hp': 518,
            'price_per_day': '450.00',
            'security_deposit': '1000.00',
            'description': 'Track monster with uploaded media photo.',
            'main_image': main_img,
            'gallery_images': [side_img, interior_img],
            'gallery_view_types': ['SIDE', 'INTERIOR']
        }

        from unittest.mock import patch
        with patch('utils.supabase_storage.SupabaseStorageService.upload_car_image', return_value='cars/99/main.png'), \
             patch('utils.supabase_storage.SupabaseStorageService.upload_gallery_image', side_effect=['gallery/99/side_1.png', 'gallery/99/interior_2.png']), \
             patch('utils.supabase_storage.SupabaseStorageService.delete_gallery_image', return_value=True):

            res = self.client.post('/api/admin/cars/', car_data, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertIn('primary_image', res.data)
            car_id = res.data['id']

            # Verify car detail has the multi-angle views and storage paths
            detail_res = self.client.get(f'/api/cars/{car_id}/')
            self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
            self.assertEqual(len(detail_res.data['images']), 2)
            self.assertEqual(detail_res.data['images'][0]['view_type'], 'SIDE')
            self.assertEqual(detail_res.data['images'][0]['image_path'], 'gallery/99/side_1.png')

            # Test deleting a gallery image
            image_id = detail_res.data['images'][0]['id']
            del_res = self.client.delete(f'/api/admin/cars/{car_id}/gallery/{image_id}/')
            self.assertEqual(del_res.status_code, status.HTTP_200_OK)

            # Verify DB count decreased to 1
            detail_after = self.client.get(f'/api/cars/{car_id}/')
            self.assertEqual(len(detail_after.data['images']), 1)

    def test_download_and_save_image_from_url(self):
        from unittest.mock import patch, MagicMock
        from apps.vehicles.services import VehicleService
        from io import BytesIO
        from PIL import Image

        img_byte_io = BytesIO()
        img = Image.new('RGB', (100, 100), color=(10, 80, 180))
        img.save(img_byte_io, 'JPEG')
        sample_img_bytes = img_byte_io.getvalue()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = sample_img_bytes
        mock_resp.headers = {'Content-Type': 'image/jpeg'}

        with patch('requests.get', return_value=mock_resp), \
             patch('utils.supabase_storage.SupabaseStorageService.upload_car_image', return_value=f'cars/{self.car.id}/main.jpg'), \
             patch('utils.supabase_storage.SupabaseStorageService.upload_gallery_image', return_value=f'gallery/{self.car.id}/front_1.jpg'):

            stored_path = VehicleService.download_and_save_main_image(self.car, 'https://example.com/downloaded_car.jpg')
            self.assertIsNotNone(stored_path)
            self.assertTrue(stored_path.startswith('cars/'))
            
            # Verify database record has the storage path
            self.car.refresh_from_db()
            self.assertEqual(self.car.main_image_path, f'cars/{self.car.id}/main.jpg')

            # Test gallery image download
            gal_img = VehicleService.download_and_save_gallery_image(self.car, 'https://example.com/front_view.jpg', view_type='FRONT')
            self.assertIsNotNone(gal_img)
            self.assertEqual(gal_img.view_type, 'FRONT')
            self.assertEqual(gal_img.image_path, f'gallery/{self.car.id}/front_1.jpg')

    def test_admin_coupon_crud_flow(self):
        # 1. Non-admin customer forbidden from accessing admin coupons endpoint
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/admin/coupons/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin creates a new promo coupon
        self.client.force_authenticate(user=self.admin)
        create_res = self.client.post('/api/admin/coupons/', {
            'code': 'festive25',
            'discount_type': 'PERCENTAGE',
            'discount_value': 25.0,
            'min_booking_amount': 2500.0,
            'max_discount_amount': 1500.0,
            'is_active': True
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_res.data['code'], 'FESTIVE25') # Uppercase verified
        coupon_id = create_res.data['id']

        # 3. Admin lists coupons with search query
        list_res = self.client.get('/api/admin/coupons/?search=FESTIVE')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        results = list_res.data.get('results', list_res.data)
        self.assertTrue(any(c['code'] == 'FESTIVE25' for c in results))

        # 4. Admin deactivates the coupon
        patch_res = self.client.patch(f'/api/admin/coupons/{coupon_id}/', {'is_active': False})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertFalse(patch_res.data['is_active'])

        # 5. Admin permanently deletes the coupon
        del_res = self.client.delete(f'/api/admin/coupons/{coupon_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Coupon.objects.filter(id=coupon_id).exists())


