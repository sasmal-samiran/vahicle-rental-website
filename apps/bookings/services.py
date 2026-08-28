import math
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from apps.vehicles.models import Car, Location
from apps.notifications.services import NotificationService
from .models import Booking, BookingAddon, Coupon

ADDON_CATALOG = {
    'gps': {
        'name': 'GPS Navigation System',
        'daily_rate': Decimal('9.00'),
        'description': 'Offline maps with real-time turn-by-turn guidance.',
        'icon': 'fa-location-crosshairs'
    },
    'child_seat': {
        'name': 'Child Safety Seat',
        'daily_rate': Decimal('249.00'),
        'description': 'Pre-installed sanitized ISOFIX seat for infants & toddlers.',
        'icon': 'fa-baby'
    },
    'extra_driver': {
        'name': 'Additional Registered Driver',
        'daily_rate': Decimal('299.00'),
        'description': 'Authorize & legally insure secondary driver on rental agreement.',
        'icon': 'fa-user-plus'
    },
    'wifi': {
        'name': '4G LTE In-Car Wi-Fi Hotspot',
        'daily_rate': Decimal('99.00'),
        'description': 'High-speed portable Wi-Fi dongle for unlimited in-cabin connectivity.',
        'icon': 'fa-wifi'
    },
}

INSURANCE_PERCENTAGES = {
    'NONE': Decimal('0.00'),
    'STANDARD': Decimal('0.09'),  # 9% of vehicle daily rental rate
    'PREMIUM': Decimal('0.16'),   # 16% of vehicle daily rental rate
}

class PricingService:
    @staticmethod
    def get_insurance_daily_rate(car, insurance_plan):
        daily_rate = Decimal(str(car.price_per_day))
        percentage = INSURANCE_PERCENTAGES.get(insurance_plan, Decimal('0.00'))
        return (daily_rate * percentage).quantize(Decimal('1.00'))

    @staticmethod
    def get_insurance_deductible(car, insurance_plan):
        daily_rate = Decimal(str(car.price_per_day))
        if insurance_plan == 'STANDARD':
            # Dynamic deductible: ~2.5x daily rate, min 5000, capped at 50,000
            calc = (daily_rate * Decimal('2.5')).quantize(Decimal('100.00'))
            return max(Decimal('5000.00'), min(Decimal('50000.00'), calc))
        elif insurance_plan == 'PREMIUM':
            return Decimal('0.00')
        else:
            return Decimal(str(car.security_deposit))

    @staticmethod
    def calculate_quote(car, start_datetime, end_datetime, addon_keys=[], insurance_plan='NONE', coupon_code=None):
        # Calculate days (round up, minimum 1)
        duration_seconds = (end_datetime - start_datetime).total_seconds()
        total_days = max(1, math.ceil(duration_seconds / 86400))
        
        daily_rate = Decimal(str(car.price_per_day))
        rental_charge = daily_rate * total_days

        # Dynamic Insurance based on car value / daily rent
        insurance_daily_rate = PricingService.get_insurance_daily_rate(car, insurance_plan)
        insurance_total = insurance_daily_rate * total_days

        # Addons
        selected_addons = []
        addons_total = Decimal('0.00')
        for key in addon_keys:
            addon_info = ADDON_CATALOG.get(key)
            if addon_info:
                addon_price = addon_info['daily_rate'] * total_days
                addons_total += addon_price
                selected_addons.append({
                    'key': key,
                    'name': addon_info['name'],
                    'daily_rate': float(addon_info['daily_rate']),
                    'total_price': float(addon_price)
                })

        subtotal = rental_charge + insurance_total + addons_total
        
        # 10% Standard Tax
        tax_amount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        deposit_amount = Decimal(str(car.security_deposit))

        # Coupon Discount
        discount_amount = Decimal('0.00')
        applied_coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code.strip(), is_active=True)
                now = timezone.now()
                if (not coupon.valid_from or coupon.valid_from <= now) and (not coupon.valid_until or coupon.valid_until >= now):
                    if subtotal >= coupon.min_booking_amount:
                        if coupon.discount_type == 'PERCENTAGE':
                            discount = (subtotal * (coupon.discount_value / Decimal('100'))).quantize(Decimal('0.01'))
                            if coupon.max_discount_amount:
                                discount = min(discount, coupon.max_discount_amount)
                            discount_amount = discount
                        else:
                            discount_amount = min(subtotal, coupon.discount_value)
                        applied_coupon = coupon
            except Coupon.DoesNotExist:
                pass

        total_amount = max(Decimal('0.00'), subtotal + tax_amount + deposit_amount - discount_amount)

        # Available protection plans for this vehicle (Backend Single Source of Truth)
        insurance_catalog = {
            'NONE': {
                'name': 'Basic Third-Party (Included)',
                'daily_rate': 0.0,
                'deductible': float(PricingService.get_insurance_deductible(car, 'NONE')),
                'description': 'Standard minimum statutory third-party liability coverage.'
            },
            'STANDARD': {
                'name': 'Standard Protection Waiver (Recommended)',
                'daily_rate': float(PricingService.get_insurance_daily_rate(car, 'STANDARD')),
                'deductible': float(PricingService.get_insurance_deductible(car, 'STANDARD')),
                'description': f"Collision & accidental damage waiver with ₹{float(PricingService.get_insurance_deductible(car, 'STANDARD')):,.0f} max deductible."
            },
            'PREMIUM': {
                'name': 'Full Comprehensive Zero-Deductible',
                'daily_rate': float(PricingService.get_insurance_daily_rate(car, 'PREMIUM')),
                'deductible': 0.0,
                'description': 'Complete 100% zero-liability peace of mind.'
            }
        }

        # Available add-ons catalog
        addons_catalog = [
            {
                'key': k,
                'name': v['name'],
                'daily_rate': float(v['daily_rate']),
                'description': v['description'],
                'icon': v['icon']
            }
            for k, v in ADDON_CATALOG.items()
        ]

        return {
            'car_id': car.id,
            'car_name': car.display_name,
            'start_date': start_datetime,
            'end_date': end_datetime,
            'total_days': total_days,
            'daily_rate': float(daily_rate),
            'rental_charge': float(rental_charge),
            'insurance_plan': insurance_plan,
            'insurance_daily_rate': float(insurance_daily_rate),
            'insurance_amount': float(insurance_total),
            'deductible_amount': float(PricingService.get_insurance_deductible(car, insurance_plan)),
            'insurance_catalog': insurance_catalog,
            'addons_catalog': addons_catalog,
            'addons': selected_addons,
            'addons_total': float(addons_total),
            'tax_amount': float(tax_amount),
            'deposit_amount': float(deposit_amount),
            'discount_amount': float(discount_amount),
            'coupon_applied': applied_coupon.code if applied_coupon else None,
            'coupon_object': applied_coupon,
            'total_amount': float(total_amount),
        }

class BookingService:
    @staticmethod
    def is_car_available(car, start_datetime, end_datetime, exclude_booking_id=None):
        if car.status != 'AVAILABLE':
            return False
        
        query = Booking.objects.filter(
            car=car,
            status__in=['CONFIRMED', 'ONGOING', 'PENDING'],
            start_date__lt=end_datetime,
            end_date__gt=start_datetime
        )
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        return not query.exists()

    @staticmethod
    def create_booking(customer, car, pickup_location, return_location, start_datetime, end_datetime,
                       insurance_plan='NONE', addon_keys=[], coupon_code=None, driver_data={}, special_requests=''):
        if not BookingService.is_car_available(car, start_datetime, end_datetime):
            raise ValueError('This vehicle is not available for the selected dates.')

        quote = PricingService.calculate_quote(
            car=car,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            addon_keys=addon_keys,
            insurance_plan=insurance_plan,
            coupon_code=coupon_code
        )

        booking = Booking.objects.create(
            customer=customer,
            car=car,
            pickup_location=pickup_location,
            return_location=return_location,
            start_date=start_datetime,
            end_date=end_datetime,
            total_days=quote['total_days'],
            daily_rate=Decimal(str(quote['daily_rate'])),
            rental_charge=Decimal(str(quote['rental_charge'])),
            insurance_plan=insurance_plan,
            insurance_amount=Decimal(str(quote['insurance_amount'])),
            addons_total=Decimal(str(quote['addons_total'])),
            tax_amount=Decimal(str(quote['tax_amount'])),
            deposit_amount=Decimal(str(quote['deposit_amount'])),
            discount_amount=Decimal(str(quote['discount_amount'])),
            coupon=quote['coupon_object'],
            total_amount=Decimal(str(quote['total_amount'])),
            status='PENDING',
            payment_status='UNPAID',
            driver_name=driver_data.get('name', customer.get_full_name() or customer.username),
            driver_phone=driver_data.get('phone', customer.phone_number or ''),
            driver_email=driver_data.get('email', customer.email or ''),
            driver_license=driver_data.get('license', customer.driver_license_number or ''),
            special_requests=special_requests
        )

        # Create Addon rows
        for addon_data in quote['addons']:
            BookingAddon.objects.create(
                booking=booking,
                name=addon_data['name'],
                daily_rate=Decimal(str(addon_data['daily_rate'])),
                total_price=Decimal(str(addon_data['total_price']))
            )

        if quote['coupon_object']:
            quote['coupon_object'].usage_count += 1
            quote['coupon_object'].save(update_fields=['usage_count'])

        # Create in-app notification
        NotificationService.create_notification(
            user=customer,
            title='Booking Initiated',
            message=f'Booking {booking.booking_code} for {car.display_name} has been created. Complete payment to secure your reservation.',
            type='BOOKING'
        )

        return booking

    @staticmethod
    def cancel_booking(booking, user, reason='Customer requested cancellation'):
        if booking.status in ['COMPLETED', 'CANCELLED']:
            raise ValueError(f'Cannot cancel a booking in {booking.get_status_display()} status.')

        booking.status = 'CANCELLED'
        booking.cancellation_reason = reason
        booking.cancelled_at = timezone.now()

        if booking.payment_status == 'PAID':
            booking.payment_status = 'REFUNDED'
            # Trigger refund log in payments service

        booking.save()

        NotificationService.create_notification(
            user=booking.customer,
            title='Booking Cancelled',
            message=f'Your reservation {booking.booking_code} for {booking.car.display_name} has been cancelled.',
            type='ALERT'
        )
        return booking
