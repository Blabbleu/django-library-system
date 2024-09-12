"""
Signals module for the users app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import CustomUser, Reader
from books_db.models import BookList

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when a new User instance is created.
    """
    if created:
        Reader.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def set_is_staff(sender, instance, **kwargs):
    """
    Ensure is_staff is set correctly for CustomUser instances.
    """
    if instance.is_staff == instance.is_reader:
        # Disconnect the signal
        post_save.disconnect(set_is_staff, sender=CustomUser)

        # Update is_staff and save
        instance.is_staff = not instance.is_reader
        instance.save(update_fields=['is_staff'])

        # Reconnect the signal
        post_save.connect(set_is_staff, sender=CustomUser)

@receiver(post_save, sender=Reader)
def create_default_lists(sender, instance, created, **kwargs):
    """
    Create default book lists when a new Reader instance is created.
    """
    if created:
        BookList.objects.get_or_create(user=instance, name='Favorites', slug='favorites')
        BookList.objects.get_or_create(user=instance, name='Read Later', slug='read-later')
        BookList.objects.get_or_create(user=instance, name='Read', slug='read')
