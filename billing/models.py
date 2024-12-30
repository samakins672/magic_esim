import uuid
from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
        ('WALLET', 'Wallet'),
    ]

    ref_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # Auto-generate UUID
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CARD')
    payment_gateway = models.CharField(max_length=50, default='Stripe')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_paid = models.DateTimeField(default=now)

    def __str__(self):
        return f"Payment by {self.user.email} for plan {self.plan.name} - {self.status}"
