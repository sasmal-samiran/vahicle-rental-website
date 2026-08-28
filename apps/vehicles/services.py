import os
import requests
import uuid
from django.core.files.base import ContentFile
from django.utils.text import slugify
from urllib.parse import urlparse
from .models import Car, CarImage

def rename_uploaded_image_file(uploaded_file, car, image_type='main', view_type=None):
    """Assign a safe, descriptive filename to an uploaded car image."""
    if not uploaded_file:
        return uploaded_file

    extension = os.path.splitext(uploaded_file.name or '')[1].lower() or '.jpg'
    if isinstance(car, dict):
        brand = car.get('brand', '')
        model = car.get('model', '')
        license_plate = car.get('license_plate', '')
        fallback = 'car'
    else:
        brand = car.brand
        model = car.model
        license_plate = car.license_plate
        fallback = f'car-{car.pk}'
    car_name = slugify(f'{brand}-{model}-{license_plate}') or fallback
    image_name = slugify(view_type or image_type) or 'image'
    uploaded_file.name = f'{car_name}_{image_name}_{uuid.uuid4().hex[:10]}{extension}'
    return uploaded_file

def download_and_save_car_image(car, image_url, filename=None):
    """
    Downloads an image from a URL, stores it in the server's media/cars/ folder,
    and updates the Car's main_image field in the database table with the local file path.
    """
    if not image_url:
        return None

    try:
        response = requests.get(image_url, timeout=15, headers={'User-Agent': 'CarRentalApp/1.0'})
        if response.status_code == 200:
            if not filename:
                parsed_url = urlparse(image_url)
                ext = os.path.splitext(parsed_url.path)[1]
                if not ext or len(ext) > 5:
                    ext = '.jpg'
                safe_name = f"{car.brand}_{car.model}_{car.license_plate}".lower().replace(' ', '_').replace('-', '_')
                filename = f"{safe_name}{ext}"

            # Saves the binary content to media/cars/ and persists the path in the DB table
            car.main_image.save(filename, ContentFile(response.content), save=True)
            return car.main_image.name  # e.g., 'cars/tesla_model_s_plaid_ny_tsla_01.jpg'
    except Exception as e:
        print(f"[Image Download Error] {car.display_name} -> {e}")
    return None

def download_and_save_gallery_image(car, image_url, view_type='OTHER', caption=None, filename=None):
    """
    Downloads a multi-angle photo from a URL, saves it to media/car_gallery/,
    and creates a CarImage database record linked to the car.
    """
    if not image_url:
        return None

    try:
        response = requests.get(image_url, timeout=15, headers={'User-Agent': 'CarRentalApp/1.0'})
        if response.status_code == 200:
            if not filename:
                parsed_url = urlparse(image_url)
                ext = os.path.splitext(parsed_url.path)[1]
                if not ext or len(ext) > 5:
                    ext = '.jpg'
                safe_name = f"{car.brand}_{car.model}_{view_type}".lower().replace(' ', '_')
                filename = f"{safe_name}_{os.urandom(4).hex()}{ext}"

            car_image = CarImage(
                car=car,
                view_type=view_type,
                caption=caption or f"{view_type} View"
            )
            # Saves file to media/car_gallery/ and stores the record in DB
            car_image.image.save(filename, ContentFile(response.content), save=True)
            return car_image
    except Exception as e:
        print(f"[Gallery Download Error] {car.display_name} ({view_type}) -> {e}")
    return None
