from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Car, CarImage
from utils.supabase_storage import SupabaseStorageService

@receiver(post_delete, sender=CarImage)
def delete_car_image_file_on_delete(sender, instance, **kwargs):
    """Deletes object from Supabase Storage when a CarImage record is deleted."""
    if instance.image_path:
        SupabaseStorageService.delete_gallery_image(instance.image_path)

@receiver(post_delete, sender=Car)
def delete_car_main_image_file_on_delete(sender, instance, **kwargs):
    """Deletes object from Supabase Storage when a Car record is deleted."""
    if instance.main_image_path:
        SupabaseStorageService.delete_car_image(instance.main_image_path)

@receiver(pre_save, sender=Car)
def delete_old_main_image_on_update(sender, instance, **kwargs):
    """Deletes old object from Supabase Storage when main_image_path is replaced."""
    if not instance.pk:
        return

    try:
        old_car = Car.objects.get(pk=instance.pk)
    except Car.DoesNotExist:
        return

    if old_car.main_image_path and old_car.main_image_path != instance.main_image_path:
        SupabaseStorageService.delete_car_image(old_car.main_image_path)

@receiver(pre_save, sender=CarImage)
def delete_old_gallery_image_on_update(sender, instance, **kwargs):
    """Deletes old object from Supabase Storage when image_path is replaced."""
    if not instance.pk:
        return

    try:
        old_img = CarImage.objects.get(pk=instance.pk)
    except CarImage.DoesNotExist:
        return

    if old_img.image_path and old_img.image_path != instance.image_path:
        SupabaseStorageService.delete_gallery_image(old_img.image_path)

