from django.db import models
from django.utils.text import slugify
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import json


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='fa-car', help_text='Icon class or identifier')
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Added fields...
    search_count = models.IntegerField(default=0, db_index=True)
    click_count = models.IntegerField(default=0)
    booking_count = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    def increment_search_count(self):
        """Increment search count and update cache"""
        Category.objects.filter(id=self.id).update(search_count=models.F('search_count') + 1)
        cache.delete(f'category_popularity_{self.id}')  

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

    # Added fields...
    search_count = models.IntegerField(default=0, db_index=True)
    click_count = models.IntegerField(default=0)
    booking_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f'{self.name}, {self.city}'

    @property
    def latitude_float(self):                                           # Added
        """Return latitude as float for Elasticsearch"""
        return float(self.latitude) if self.latitude else None
    
    @property
    def longitude_float(self):                                          # Added  
        """Return longitude as float for Elasticsearch"""
        return float(self.longitude) if self.longitude else None

class Brand(models.Model):
    """It will be a foreign key in Car model...That does not effect your system heavily..."""
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    search_count = models.IntegerField(default=0, db_index=True)
    click_count = models.IntegerField(default=0)
    booking_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Brands'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    @property
    def popularity_score(self):
        """Calculate popularity score for ranking..."""
        return (self.search_count * 2) + (self.click_count * 3) + (self.booking_count * 5)

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
    brand = models.CharField(max_length=50, db_index=True)    # Optional(unnecessary)
    brand_ref = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='cars', help_text='Optional reference to Brand model') # ForeignKey to Brand model

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


    # Added fields...
    search_count = models.IntegerField(default=0, db_index=True)
    click_count = models.IntegerField(default=0)
    booking_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    review_count = models.IntegerField(default=0)

    # Search optimization fields
    slug = models.SlugField(max_length=120, unique=True, blank=True, db_index=True)
    search_keywords = models.JSONField(default=list, blank=True, help_text='Additional keywords for search')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['status', 'category']),
            models.Index(fields=['-search_count']),
            models.Index(fields=['-booking_count']),
        ]
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

    # Added properties...
    @property
    def full_name(self):                        
        """Full name for search purposes"""
        return f'{self.year} {self.brand} {self.model}'
    @property
    def popularity_score(self):
        """Calculate popularity score for ranking"""
        return (
            (self.search_count * 1) + 
            (self.click_count * 2) + 
            (self.booking_count * 5) + 
            (float(self.average_rating) * self.review_count * 0.5)
        )
    @property
    def click_through_rate(self):
        """Calculate CTR"""
        if self.search_count > 0:
            return self.click_count / self.search_count
        return 0.0
    def save(self, *args, **kwargs):
        # Generate slug if not exists...
        if not self.slug:
            self.slug = slugify(f'{self.brand}-{self.model}-{self.year}')
        
        # Auto-populate search keywords
        if not self.search_keywords:
            self.search_keywords = self._generate_search_keywords()
        
        super().save(*args, **kwargs)
        
        # Sync with Brand model if exists
        if not self.brand_ref:
            brand, created = Brand.objects.get_or_create(
                name=self.brand,
                defaults={'country': self._guess_brand_country()}
            )
            if not created and not self.brand_ref:
                Car.objects.filter(id=self.id).update(brand_ref=brand)
    def _generate_search_keywords(self):
        """Generate search keywords for better searchability"""
        keywords = []
        
        # Add basic info
        keywords.extend([
            self.brand.lower(),
            self.model.lower(),
            f'{self.brand} {self.model}'.lower(),
            str(self.year)
        ])
        
        # Add category
        if self.category:
            keywords.append(self.category.name.lower())
        
        # Add fuel type
        if self.fuel_type:
            keywords.append(self.get_fuel_type_display().lower())
        
        # Add transmission
        if self.transmission:
            keywords.append(self.get_transmission_display().lower())
        
        # Add features
        if self.features:
            keywords.extend([f.lower() for f in self.features if isinstance(f, str)])
        
        # Add common search terms
        if self.seats >= 7:
            keywords.append('7 seater')
            keywords.append('family car')
        if self.fuel_type == 'ELECTRIC':
            keywords.append('electric')
            keywords.append('ev')
        if self.fuel_type == 'HYBRID':
            keywords.append('hybrid')
            keywords.append('eco friendly')
        if self.price_per_day and self.price_per_day < 50:
            keywords.append('budget')
            keywords.append('economy')
        if self.price_per_day and self.price_per_day > 200:
            keywords.append('luxury')
            keywords.append('premium')
        
        # Remove duplicates and empty strings...
        return list(set([k for k in keywords if k]))
    def _guess_brand_country(self):
        """Guess brand country based on brand name"""
        country_map = {                       # This will be updated with more brands in future...
            'toyota': 'Japan',
            'honda': 'Japan',
            'nissan': 'Japan',
            'bmw': 'Germany',
            'mercedes': 'Germany',
            'audi': 'Germany',
            'volkswagen': 'Germany',
            'tata': 'India',
            'mahindra': 'India',
            'hyundai': 'South Korea',
            'kia': 'South Korea',
            'tesla': 'USA',
            'ford': 'USA',
            'chevrolet': 'USA',
        }
        return country_map.get(self.brand.lower(), '')
    def increment_search_count(self):
        """Increment search count efficiently"""
        Car.objects.filter(id=self.id).update(search_count=models.F('search_count') + 1)
        # Invalidate cache
        cache.delete(f'car_popularity_{self.id}')
    
    def increment_click_count(self):
        """Increment click count efficiently"""
        Car.objects.filter(id=self.id).update(click_count=models.F('click_count') + 1)
        cache.delete(f'car_popularity_{self.id}')

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
    image = models.ImageField(upload_to='car_gallery/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES, default='OTHER', blank=True)
    caption = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_view_type_display()} for {self.car.display_name}'

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.image_url or ''

# Signal handlers for cache invalidation
""" This ensures that after a Car, Category, or Location is changed,
the application will fetch fresh data instead of showing outdated cache data."""
@receiver(post_save, sender=Car)
def invalidate_car_cache(sender, instance, **kwargs):
    """Invalidate cache when car is updated"""
    cache.delete(f'car_popularity_{instance.id}')
    cache.delete(f'car_details_{instance.id}')


@receiver(post_save, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate cache when category is updated"""
    cache.delete(f'category_popularity_{instance.id}')


@receiver(post_save, sender=Location)
def invalidate_location_cache(sender, instance, **kwargs):
    """Invalidate cache when location is updated"""
    cache.delete(f'location_popularity_{instance.id}')