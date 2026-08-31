import os
import requests
import uuid
import re
from datetime import timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import Car, CarImage, Category
from django.db.models import Q,F, Value, FloatField, Case, When, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone

from utils.supabase_storage import SupabaseStorageService

class VehicleService:
    """Service class for vehicle media operations, image processing, and business utilities via Supabase Storage."""

    @staticmethod
    def rename_uploaded_image(uploaded_file, car, image_type='main', view_type=None):
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
        uploaded_file.name = f'{car_name}_{image_name}_{uuid.uuid4().hex[:8]}{extension}'
        return uploaded_file

    @staticmethod
    def upload_and_save_main_image(car, file_obj, filename=None):
        """Uploads car main image directly to Supabase Storage and updates car.main_image_path."""
        if not file_obj:
            return None
        storage_path = SupabaseStorageService.upload_car_image(car.id, file_obj, filename=filename)
        car.main_image_path = storage_path
        car.save(update_fields=['main_image_path', 'updated_at'])
        return storage_path

    @staticmethod
    def download_and_save_main_image(car, image_url, filename=None):
        """
        Downloads an image from a URL, uploads to Supabase Storage bucket 'car-images',
        and updates the Car's main_image_path in PostgreSQL.
        """
        if not image_url:
            return None

        try:
            response = requests.get(image_url, timeout=15, headers={'User-Agent': 'CarRentalApp/1.0'})
            if response.status_code == 200:
                parsed_url = urlparse(image_url)
                ext = os.path.splitext(parsed_url.path)[1].lower()
                if not ext or len(ext) > 5 or ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    ext = '.jpg'
                safe_name = filename or f"main{ext}"

                storage_path = SupabaseStorageService.upload_car_image(
                    car.id,
                    response.content,
                    filename=safe_name,
                    content_type=response.headers.get('Content-Type', 'image/jpeg')
                )
                car.main_image_path = storage_path
                car.save(update_fields=['main_image_path', 'updated_at'])
                return storage_path
        except Exception as e:
            print(f"[Image Download Error] {car.display_name} -> {e}")
        return None

    @staticmethod
    def download_and_save_gallery_image(car, image_url, view_type='OTHER', caption=None, filename=None):
        """
        Downloads a photo from a URL, uploads to Supabase Storage bucket 'car-images' (gallery/ folder),
        and creates a CarImage database record linked to the car.
        """
        if not image_url:
            return None

        try:
            response = requests.get(image_url, timeout=15, headers={'User-Agent': 'CarRentalApp/1.0'})
            if response.status_code == 200:
                parsed_url = urlparse(image_url)
                ext = os.path.splitext(parsed_url.path)[1].lower()
                if not ext or len(ext) > 5 or ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                    ext = '.jpg'
                safe_name = filename or f"{slugify(view_type).lower()}_{uuid.uuid4().hex[:6]}{ext}"

                storage_path = SupabaseStorageService.upload_gallery_image(
                    car.id,
                    response.content,
                    filename=safe_name,
                    content_type=response.headers.get('Content-Type', 'image/jpeg')
                )
                car_image = CarImage.objects.create(
                    car=car,
                    image_path=storage_path,
                    view_type=view_type,
                    caption=caption or f"{view_type} View"
                )
                return car_image
        except Exception as e:
            print(f"[Gallery Download Error] {car.display_name} ({view_type}) -> {e}")
        return None

    @staticmethod
    def handle_gallery_uploads(car, gallery_files, view_types=None, captions=None):
        """
        Processes and uploads a list of gallery image files to Supabase Storage and creates CarImage records.
        """
        if not gallery_files:
            return []

        view_types = view_types or []
        captions = captions or []
        created_images = []

        for idx, img_file in enumerate(gallery_files):
            v_type = view_types[idx] if idx < len(view_types) else 'OTHER'
            cap = captions[idx] if idx < len(captions) else ''
            
            ext = os.path.splitext(getattr(img_file, 'name', '') or '')[1].lower() or '.jpg'
            file_name = f"{slugify(v_type).lower()}_{idx + 1}_{uuid.uuid4().hex[:6]}{ext}"

            storage_path = SupabaseStorageService.upload_gallery_image(
                car.id,
                img_file,
                filename=file_name
            )
            car_img = CarImage.objects.create(
                car=car,
                image_path=storage_path,
                view_type=v_type,
                caption=cap or f"{v_type.replace('_', ' ').title()} View"
            )
            created_images.append(car_img)

        return created_images

class CarSearchService:
    """Search Engine and intelligent fallback matching service for vehicles."""

    def get_fallback_matches(self, query: str = None, base_queryset = None):
        """
        Fallback engine when standard exact search returns 0 results:
        1. Evaluates all vehicles in base_queryset with fuzzy relevance scoring (typo tolerance, brand/model/category fuzzy matching).
        2. If fuzzy candidate cars with score > 0 are identified, returns them sorted by descending relevance.
        3. If no fuzzy matches exist (e.g. completely unrecognized search term), returns top available cars in the fleet.
        """
        qs = base_queryset if base_queryset is not None else self.queryset.filter(status='AVAILABLE')

        if query and query.strip():
            clean_query = query.strip()
            scored_candidates = []
            for car in qs:
                score = self._calculate_relevance(car, clean_query)
                if score > 0:
                    scored_candidates.append((score, car))

            if scored_candidates:
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                car_ids = [car.id for _, car in scored_candidates]
                preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(car_ids)])
                return qs.filter(id__in=car_ids).order_by(preserved_order)

        # Fallback default: Top available fleet
        return qs.filter(status='AVAILABLE')

    def _calculate_relevance(self, car: Car, query: str) -> float:
        score = 0.0
        query_terms = query.lower().split()

        car_text = f"{car.brand} {car.model} {car.year} {car.category.name if car.category else ''}"
        car_text += f" {car.location.city if car.location else ''} {car.description or ''}"

        for term in query_terms:
            # Exact brand match
            if term == car.brand.lower():
                score += 10.0
            # Exact model match
            elif term == car.model.lower():
                score += 8.0
            # Category match
            elif car.category and term in car.category.name.lower():
                score += 6.0
            # Partial match in description/specs
            elif term in car_text.lower():
                score += 3.0
            # Fuzzy match for typos (e.g. telsa, lamborgini, porsh)
            elif self._fuzzy_match(term, car_text):
                score += 4.0

        return score

    def _fuzzy_match(self, term: str, text: str) -> bool:
        if len(term) < 3:
            return False
        # Check for common typos & close distances
        for word in text.lower().split():
            if abs(len(term) - len(word)) <= 2:
                # Levenshtein distance check (max 2 character edits for words >= 4 chars, 1 edit for 3 chars)
                max_dist = 2 if len(term) >= 4 else 1
                if self._levenshtein_distance(term, word) <= max_dist:
                    return True
        return False

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
