from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import User
from utils.supabase_storage import SupabaseStorageService

@receiver(post_delete, sender=User)
def delete_user_profile_picture_on_delete(sender, instance, **kwargs):
    """Deletes profile avatar from Supabase Storage when user is deleted."""
    if instance.profile_image_path:
        SupabaseStorageService.delete_profile_image(instance.profile_image_path)

@receiver(pre_save, sender=User)
def delete_old_profile_picture_on_update(sender, instance, **kwargs):
    """Deletes old profile avatar from Supabase Storage when profile_image_path changes."""
    if not instance.pk:
        return
    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old_user.profile_image_path and old_user.profile_image_path != instance.profile_image_path:
        SupabaseStorageService.delete_profile_image(old_user.profile_image_path)

