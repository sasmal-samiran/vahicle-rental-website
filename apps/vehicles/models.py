from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='fa-car', help_text='Icon class or identifier')
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f'{self.name}, {self.city}'

class Car(models.Model):
    TRANSMISSION_CHOICES = (
        ('AUTOMATIC', 'Automatic'),
        ('MANUAL', 'Manual'),
    )
    
    FUEL_CHOICES = (
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
    )

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('RENTED', 'Rented'),
        ('MAINTENANCE', 'In Maintenance'),
        ('INACTIVE', 'Inactive'),
    )

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='cars')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='cars')
    brand = models.CharField(max_length=50, db_index=True)
    model = models.CharField(max_length=50, db_index=True)
    year = models.PositiveIntegerField()
    license_plate = models.CharField(max_length=30, unique=True, db_index=True)
    vin_number = models.CharField(max_length=50, blank=True, null=True)

    transmission = models.CharField(max_length=15, choices=TRANSMISSION_CHOICES, default='AUTOMATIC')
    fuel_type = models.CharField(max_length=15, choices=FUEL_CHOICES, default='PETROL')
    seats = models.PositiveSmallIntegerField(default=5)
    doors = models.PositiveSmallIntegerField(default=4)
    luggage_capacity = models.PositiveSmallIntegerField(default=3, help_text='Number of bags')
    mileage_limit = models.CharField(max_length=50, default='Unlimited', help_text='Daily mileage allowance')
    engine_capacity = models.CharField(max_length=50, blank=True, null=True, default='2.0L Turbo')
    power_hp = models.PositiveIntegerField(default=200, help_text='Horsepower')

    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    
    main_image_path = models.CharField(max_length=255, blank=True, null=True, help_text="Supabase Storage path, e.g. cars/15/main.jpg")
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE', db_index=True)
    features = models.JSONField(default=list, blank=True, help_text='List of car features/amenities')
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.year} {self.brand} {self.model} ({self.license_plate})'

    @property
    def display_name(self):
        return f'{self.brand} {self.model}'

    @property
    def primary_image(self):
        from utils.supabase_storage import SupabaseStorageService
        return SupabaseStorageService.get_car_image_url(self.main_image_path)

    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 4.8

    @property
    def popularity_score(self):
        """
        Normalized base popularity score (0.0 to 10.0 scale)
        combining customer reviews (40%), booking volume (40%), and conversion rate (20%).
        """
        base_rating_score = (self.average_rating / 5.0) * 4.0  # Max 4.0 pts
        bookings_count = self.bookings.count()
        booking_score = min(4.0, bookings_count * 1.0)         # Max 4.0 pts

        conversion_bonus = 0.0
        try:
            if hasattr(self, 'popularity_metrics') and self.popularity_metrics:
                # booking_conversion_rate is percentage (0-100), scale to max 2.0 pts
                conversion_bonus = min(2.0, (self.popularity_metrics.booking_conversion_rate / 100.0) * 2.0)
        except Exception:
            conversion_bonus = 0.0

        return round(float(base_rating_score + booking_score + conversion_bonus), 2)

class CarImage(models.Model):
    VIEW_CHOICES = (
        ('FRONT', 'Front View'),
        ('SIDE', 'Side Profile'),
        ('REAR', 'Rear View'),
        ('INTERIOR', 'Interior & Seating'),
        ('DASHBOARD', 'Dashboard & Controls'),
        ('ANGLE', '3/4 Perspective View'),
        ('OTHER', 'Detail / Feature'),
    )

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image_path = models.CharField(max_length=255, blank=True, null=True, help_text="Supabase Storage path, e.g. gallery/15/1.jpg")
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES, default='OTHER', blank=True)
    caption = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_view_type_display()} for {self.car.display_name}'

    @property
    def url(self):
        from utils.supabase_storage import SupabaseStorageService
        return SupabaseStorageService.get_gallery_image_url(self.image_path)

