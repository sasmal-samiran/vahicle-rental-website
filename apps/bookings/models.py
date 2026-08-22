import secrets
import math
from django.db import models
from django.conf import settings
from apps.vehicles.models import Car, Location

class Coupon(models.Model):
    DISCOUNT_CHOICES = (
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED', 'Fixed Amount Discount'),
    )

    code = models.CharField(max_length=30, unique=True, db_index=True)
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_CHOICES, default='PERCENTAGE')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text='Percentage (e.g. 20 for 20%) or Fixed dollar amount')
    min_booking_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.code} ({self.discount_value}% if percentage)'

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed & Reserved'),
        ('ONGOING', 'Active / Picked Up'),
        ('COMPLETED', 'Completed & Returned'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    )

    INSURANCE_CHOICES = (
        ('NONE', 'Basic Third-Party (Included)'),
        ('STANDARD', 'Standard Damage Waiver (+/day)'),
        ('PREMIUM', 'Full Comprehensive & Zero Deductible (+/day)'),
    )

    booking_code = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name='bookings')

    pickup_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='pickup_bookings')
    return_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='return_bookings')

    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True)
    total_days = models.PositiveIntegerField(default=1)

    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    rental_charge = models.DecimalField(max_digits=10, decimal_places=2)
    
    insurance_plan = models.CharField(max_length=20, choices=INSURANCE_CHOICES, default='NONE')
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    addons_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID', db_index=True)

    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=30)
    driver_email = models.EmailField(blank=True, null=True)
    driver_license = models.CharField(max_length=50, blank=True, null=True)

    special_requests = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = f'CR-2026-{secrets.token_hex(3).upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.booking_code} - {self.car.display_name} ({self.customer.get_full_name() or self.customer.username})'

class BookingAddon(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=100)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.name} for {self.booking.booking_code}'
