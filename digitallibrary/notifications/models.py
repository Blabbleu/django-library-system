# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # Use timezone.now for default value
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.username}"
