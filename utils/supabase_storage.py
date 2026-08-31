import os
import mimetypes
import logging
from io import BytesIO
from typing import Optional, Tuple, Union
from PIL import Image

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File, ContentFile
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

# Constants & Defaults (Optimized for Free Tier: 1GB Quota)
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_CAR_IMAGE_SIZE_BYTES = 2 * 1024 * 1024      # 2 MB (fits ~2,000+ crisp 1080p web images)
MAX_PROFILE_IMAGE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB (fits ~10,000+ user avatars)


class SupabaseStorageService:
    """
    Centralized service for managing image uploads, deletions, and dynamic URL generation
    via Supabase Storage buckets.
    """

    _client = None

    @classmethod
    def _reload_env_if_needed(cls):
        """Helper to ensure .env is read if environment variables were not loaded."""
        try:
            from dotenv import load_dotenv
            base_dir = getattr(settings, 'BASE_DIR', None)
            if base_dir:
                env_file = os.path.join(base_dir, '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file)
        except Exception:
            pass

    @classmethod
    def _get_supabase_url(cls) -> str:
        val = getattr(settings, 'SUPABASE_URL', None) or os.environ.get('SUPABASE_URL', '')
        if not val:
            cls._reload_env_if_needed()
            val = getattr(settings, 'SUPABASE_URL', None) or os.environ.get('SUPABASE_URL', '')
        return val or ''

    @classmethod
    def _get_supabase_key(cls) -> str:
        val = getattr(settings, 'SUPABASE_KEY', None) or os.environ.get('SUPABASE_KEY', '')
        if not val:
            cls._reload_env_if_needed()
            val = getattr(settings, 'SUPABASE_KEY', None) or os.environ.get('SUPABASE_KEY', '')
        return val or ''

    @classmethod
    def get_client(cls):
        """Initializes and returns the Supabase client singleton."""
        supabase_url = cls._get_supabase_url()
        supabase_key = cls._get_supabase_key()

        if not supabase_url or not supabase_key:
            logger.warning(
                "[Supabase Storage] SUPABASE_URL or SUPABASE_KEY is missing. "
                "Storage operations requiring authentication will fail."
            )
            return None

        if cls._client is None:
            try:
                from supabase import create_client
                cls._client = create_client(supabase_url, supabase_key)
            except Exception as e:
                logger.error(f"[Supabase Storage] Failed to initialize Supabase client: {e}")
                return None

        return cls._client

    @classmethod
    def get_car_bucket_name(cls) -> str:
        return getattr(settings, 'SUPABASE_CAR_BUCKET', 'car-images') or 'car-images'

    @classmethod
    def get_profile_bucket_name(cls) -> str:
        return getattr(settings, 'SUPABASE_PROFILE_BUCKET', 'profile-images') or 'profile-images'

    # =========================================================================
    # Validation Utilities
    # =========================================================================

    @classmethod
    def validate_image_file(
        cls,
        file_obj: Union[UploadedFile, File, bytes, BytesIO],
        filename: Optional[str] = None,
        max_size_bytes: int = MAX_CAR_IMAGE_SIZE_BYTES
    ) -> Tuple[bytes, str, str]:
        """
        Validates:
        1. Non-empty file
        2. File size <= max_size_bytes
        3. Allowed extension (.jpg, .jpeg, .png, .webp)
        4. Valid image payload using Pillow
        5. Proper MIME content type

        Returns: (file_bytes, clean_filename, content_type)
        """
        if file_obj is None:
            raise ValidationError("No file provided.")

        raw_filename = filename or getattr(file_obj, 'name', '') or 'image.jpg'
        ext = os.path.splitext(raw_filename)[1].lower()

        if not ext or ext not in ALLOWED_EXTENSIONS:
            allowed_str = ', '.join(ALLOWED_EXTENSIONS)
            raise ValidationError(f"Unsupported file format '{ext}'. Allowed formats: {allowed_str}")

        # Read binary bytes
        if isinstance(file_obj, bytes):
            file_bytes = file_obj
        elif hasattr(file_obj, 'read'):
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            file_bytes = file_obj.read()
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
        else:
            raise ValidationError("Invalid file object provided.")

        if not file_bytes or len(file_bytes) == 0:
            raise ValidationError("Uploaded file is empty.")

        if len(file_bytes) > max_size_bytes:
            size_mb = len(file_bytes) / (1024 * 1024)
            limit_mb = max_size_bytes / (1024 * 1024)
            raise ValidationError(f"File size ({size_mb:.2f} MB) exceeds limit of {limit_mb:.1f} MB.")

        # Validate image integrity with Pillow
        try:
            with Image.open(BytesIO(file_bytes)) as img:
                img.verify()
                img_format = (img.format or '').upper()
                format_map = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
                if img_format not in format_map and ext not in ALLOWED_EXTENSIONS:
                    raise ValidationError(f"Invalid image content format: {img_format}")
        except Exception as e:
            raise ValidationError(f"Corrupted or invalid image file: {e}")

        # Determine MIME type
        content_type = getattr(file_obj, 'content_type', None)
        if not content_type or content_type not in ALLOWED_MIME_TYPES:
            guessed_type, _ = mimetypes.guess_type(raw_filename)
            content_type = guessed_type if guessed_type in ALLOWED_MIME_TYPES else 'image/jpeg'

        return file_bytes, raw_filename, content_type

    # =========================================================================
    # Car Main Images (Public Bucket: car-images)
    # Target Path: cars/{car_id}/main.{ext}
    # =========================================================================

    @classmethod
    def upload_car_image(
        cls,
        car_id: Union[int, str],
        file_obj: Union[UploadedFile, File, bytes, BytesIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Uploads or replaces the main image for a vehicle in the 'car-images' bucket.
        Path: cars/{car_id}/main.{ext}
        Returns the relative storage path (e.g. 'cars/15/main.jpg').
        """
        file_bytes, orig_name, detected_content_type = cls.validate_image_file(file_obj, filename)
        ct = content_type or detected_content_type
        ext = os.path.splitext(orig_name)[1].lower() or '.jpg'

        storage_path = f"cars/{car_id}/main{ext}"
        bucket_name = cls.get_car_bucket_name()

        client = cls.get_client()
        if not client:
            raise RuntimeError("Supabase client is not configured. Please check SUPABASE_URL and SUPABASE_KEY.")

        try:
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": ct, "upsert": "true"}
            )
            logger.info(f"[Supabase Storage] Uploaded car main image to {bucket_name}/{storage_path}")
            return storage_path
        except Exception as e:
            logger.error(f"[Supabase Storage] Failed to upload car image {storage_path}: {e}")
            raise RuntimeError(f"Failed to upload vehicle image to Supabase Storage: {e}")

    @classmethod
    def delete_car_image(cls, storage_path: Optional[str]) -> bool:
        """Deletes a car main image from the 'car-images' bucket."""
        if not storage_path or storage_path.startswith(('http://', 'https://')):
            return False

        client = cls.get_client()
        if not client:
            return False

        bucket_name = cls.get_car_bucket_name()
        try:
            client.storage.from_(bucket_name).remove([storage_path])
            logger.info(f"[Supabase Storage] Deleted car main image: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"[Supabase Storage] Error deleting car image {storage_path}: {e}")
            return False

    @classmethod
    def get_car_image_url(cls, storage_path: Optional[str]) -> str:
        """
        Returns the public URL for a vehicle main image from Supabase Storage.
        If storage_path is a full URL, returns it directly.
        If storage_path is empty or Supabase is not configured, returns '' (no fallback images).
        """
        if not storage_path:
            return ''

        if storage_path.startswith(('http://', 'https://')):
            return storage_path

        supabase_url = cls._get_supabase_url()
        bucket_name = cls.get_car_bucket_name()

        if supabase_url:
            clean_base = supabase_url.rstrip('/')
            clean_path = storage_path.lstrip('/')
            return f"{clean_base}/storage/v1/object/public/{bucket_name}/{clean_path}"

        return ''

    # =========================================================================
    # Car Gallery Images (Public Bucket: car-images)
    # Target Path: gallery/{car_id}/{filename}.{ext}
    # =========================================================================

    @classmethod
    def upload_gallery_image(
        cls,
        car_id: Union[int, str],
        file_obj: Union[UploadedFile, File, bytes, BytesIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Uploads a multi-angle gallery image for a vehicle to the 'car-images' bucket.
        Path: gallery/{car_id}/{filename}
        Returns the relative storage path (e.g. 'gallery/15/1.jpg').
        """
        file_bytes, orig_name, detected_content_type = cls.validate_image_file(file_obj, filename)
        ct = content_type or detected_content_type
        
        safe_name = filename or orig_name
        safe_name = os.path.basename(safe_name)

        storage_path = f"gallery/{car_id}/{safe_name}"
        bucket_name = cls.get_car_bucket_name()

        client = cls.get_client()
        if not client:
            raise RuntimeError("Supabase client is not configured. Please check SUPABASE_URL and SUPABASE_KEY.")

        try:
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": ct, "upsert": "true"}
            )
            logger.info(f"[Supabase Storage] Uploaded gallery image to {bucket_name}/{storage_path}")
            return storage_path
        except Exception as e:
            logger.error(f"[Supabase Storage] Failed to upload gallery image {storage_path}: {e}")
            raise RuntimeError(f"Failed to upload gallery image to Supabase Storage: {e}")

    @classmethod
    def delete_gallery_image(cls, storage_path: Optional[str]) -> bool:
        """Deletes a gallery image from the 'car-images' bucket."""
        if not storage_path or storage_path.startswith(('http://', 'https://')):
            return False

        client = cls.get_client()
        if not client:
            return False

        bucket_name = cls.get_car_bucket_name()
        try:
            client.storage.from_(bucket_name).remove([storage_path])
            logger.info(f"[Supabase Storage] Deleted gallery image: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"[Supabase Storage] Error deleting gallery image {storage_path}: {e}")
            return False

    @classmethod
    def get_gallery_image_url(cls, storage_path: Optional[str]) -> str:
        """
        Returns the public URL for a vehicle gallery image from Supabase Storage.
        Returns '' if storage_path is empty or Supabase is not configured (no fallback images).
        """
        if not storage_path:
            return ''

        if storage_path.startswith(('http://', 'https://')):
            return storage_path

        supabase_url = cls._get_supabase_url()
        bucket_name = cls.get_car_bucket_name()

        if supabase_url:
            clean_base = supabase_url.rstrip('/')
            clean_path = storage_path.lstrip('/')
            return f"{clean_base}/storage/v1/object/public/{bucket_name}/{clean_path}"

        return ''

    # =========================================================================
    # User Profile Images (Private Bucket: profile-images)
    # Target Path: profiles/{user_id}/profile.{ext}
    # =========================================================================

    @classmethod
    def upload_profile_image(
        cls,
        user_id: Union[int, str],
        file_obj: Union[UploadedFile, File, bytes, BytesIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Uploads or replaces a user profile avatar in the 'profile-images' bucket.
        Path: profiles/{user_id}/profile{ext}
        Returns the relative storage path (e.g. 'profiles/42/profile.jpg').
        """
        file_bytes, orig_name, detected_content_type = cls.validate_image_file(
            file_obj, filename, max_size_bytes=MAX_PROFILE_IMAGE_SIZE_BYTES
        )
        ct = content_type or detected_content_type
        ext = os.path.splitext(orig_name)[1].lower() or '.jpg'

        storage_path = f"profiles/{user_id}/profile{ext}"
        bucket_name = cls.get_profile_bucket_name()

        client = cls.get_client()
        if not client:
            raise RuntimeError("Supabase client is not configured. Please check SUPABASE_URL and SUPABASE_KEY.")

        try:
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": ct, "upsert": "true"}
            )
            logger.info(f"[Supabase Storage] Uploaded profile image to {bucket_name}/{storage_path}")
            return storage_path
        except Exception as e:
            logger.error(f"[Supabase Storage] Failed to upload profile image {storage_path}: {e}")
            raise RuntimeError(f"Failed to upload profile picture to Supabase Storage: {e}")

    @classmethod
    def delete_profile_image(cls, storage_path: Optional[str]) -> bool:
        """Deletes a profile picture from the 'profile-images' bucket."""
        if not storage_path or storage_path.startswith(('http://', 'https://')):
            return False

        client = cls.get_client()
        if not client:
            return False

        bucket_name = cls.get_profile_bucket_name()
        try:
            client.storage.from_(bucket_name).remove([storage_path])
            logger.info(f"[Supabase Storage] Deleted profile image: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"[Supabase Storage] Error deleting profile image {storage_path}: {e}")
            return False

    @classmethod
    def get_profile_image_url(cls, storage_path: Optional[str], expires_in: int = 3600) -> Optional[str]:
        """
        Returns a signed URL for a private user profile avatar.
        Falls back to public URL if signed URL creation is unavailable.
        """
        if not storage_path:
            return None

        if storage_path.startswith(('http://', 'https://')):
            return storage_path

        client = cls.get_client()
        bucket_name = cls.get_profile_bucket_name()

        if client:
            try:
                res = client.storage.from_(bucket_name).create_signed_url(
                    path=storage_path,
                    expires_in=expires_in
                )
                if isinstance(res, dict) and 'signedURL' in res:
                    return res['signedURL']
                elif hasattr(res, 'signed_url') and res.signed_url:
                    return res.signed_url
                elif isinstance(res, dict) and 'signed_url' in res:
                    return res['signed_url']
            except Exception as e:
                logger.warning(f"[Supabase Storage] Could not generate signed URL for {storage_path}: {e}")

        # Fallback to direct URL if client not ready
        supabase_url = cls._get_supabase_url()
        if supabase_url:
            clean_base = supabase_url.rstrip('/')
            clean_path = storage_path.lstrip('/')
            return f"{clean_base}/storage/v1/object/public/{bucket_name}/{clean_path}"

        return None
