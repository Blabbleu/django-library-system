# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CustomUser, Reader

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        CustomUser.objects.create(user=instance)
        Reader.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.CustomUser.save()
    instance.readerprofile.save()


@receiver(post_save, sender=CustomUser)
def set_is_staff(sender, instance, **kwargs):
    if instance.is_staff == instance.is_reader:
        # Disconnect the signal
        post_save.disconnect(set_is_staff, sender=CustomUser)
        
        # Update is_staff and save
        instance.is_staff = not instance.is_reader
        instance.save(update_fields=['is_staff'])
        
        # Reconnect the signal
        post_save.connect(set_is_staff, sender=CustomUser)