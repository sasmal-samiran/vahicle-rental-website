from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('BOOKING', 'Booking Update'),
        ('PAYMENT', 'Payment Confirmation'),
        ('REMINDER', 'Trip Reminder'),
        ('ALERT', 'Important Alert'),
        ('PROMO', 'Special Promotion'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ALERT')
    is_read = models.BooleanField(default=False, db_index=True)
    link_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} for {self.user.username}'
