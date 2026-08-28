import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import User

@receiver(post_delete, sender=User)
def delete_user_profile_picture_on_delete(sender, instance, **kwargs):
    if instance.profile_picture:
        try:
            if os.path.isfile(instance.profile_picture.path):
                os.remove(instance.profile_picture.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove profile picture: {e}')

@receiver(pre_save, sender=User)
def delete_old_profile_picture_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old_user.profile_picture and old_user.profile_picture != instance.profile_picture:
        try:
            if os.path.isfile(old_user.profile_picture.path):
                os.remove(old_user.profile_picture.path)
        except Exception as e:
            print(f'[MEDIA CLEANUP] Could not remove old profile picture: {e}')
