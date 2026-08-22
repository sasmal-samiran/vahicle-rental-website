import secrets
from django.db import models
from apps.bookings.models import Booking

class Payment(models.Model):
    PROVIDER_CHOICES = (
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
        ('SANDBOX', 'Built-in Sandbox / Instant Test'),
    )

    STATUS_CHOICES = (
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success / Captured'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='SANDBOX')
    
    gateway_order_id = models.CharField(max_length=150, blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=150, blank=True, null=True)
    gateway_signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED', db_index=True)
    
    payment_method = models.CharField(max_length=50, default='CARD')
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f'TXN-{secrets.token_hex(6).upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.transaction_id} ({self.provider}) -  [{self.status}]'

class Refund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    refund_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='PROCESSED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Refund {self.refund_id} for {self.payment.transaction_id}'
