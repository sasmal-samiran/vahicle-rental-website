import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Car, CarImage

@receiver(post_delete, sender=CarImage)
def delete_car_image_file_on_delete(sender, instance, **kwargs):
    # Deletes physical file from media storage when a CarImage DB record is deleted.
    if instance.image:
        try:
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove gallery file {instance.image}: {e}')

@receiver(post_delete, sender=Car)
def delete_car_main_image_file_on_delete(sender, instance, **kwargs):
    # Deletes physical main_image file from media storage when a Car DB record is deleted.
    if instance.main_image:
        try:
            if os.path.isfile(instance.main_image.path):
                os.remove(instance.main_image.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove main image file {instance.main_image}: {e}')

@receiver(pre_save, sender=Car)
def delete_old_main_image_on_update(sender, instance, **kwargs):
    # Deletes old physical file from media storage when main_image is replaced with a new file.
    if not instance.pk:
        return

    try:
        old_car = Car.objects.get(pk=instance.pk)
    except Car.DoesNotExist:
        return

    if old_car.main_image and old_car.main_image != instance.main_image:
        try:
            if os.path.isfile(old_car.main_image.path):
                os.remove(old_car.main_image.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove old main image file: {e}')

@receiver(pre_save, sender=CarImage)
def delete_old_gallery_image_on_update(sender, instance, **kwargs):
    # Deletes old physical file from media storage when gallery image is replaced with a new file.
    if not instance.pk:
        return

    try:
        old_img = CarImage.objects.get(pk=instance.pk)
    except CarImage.DoesNotExist:
        return

    if old_img.image and old_img.image != instance.image:
        try:
            if os.path.isfile(old_img.image.path):
                os.remove(old_img.image.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove old gallery image file: {e}')
