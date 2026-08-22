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
    
    main_image_url = models.URLField(max_length=500, blank=True, null=True)
    main_image = models.ImageField(upload_to='cars/', blank=True, null=True)
    
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
        if self.main_image:
            return self.main_image.url
        if self.main_image_url:
            return self.main_image_url
        return 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_gallery/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    caption = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Image for {self.car.display_name}'

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.image_url or ''
