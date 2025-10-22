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
    seller = models.CharField(max_length=25, default=None, blank=True, null=True)
    package_code = models.CharField(max_length=25, default=None, blank=True, null=True)
    esim_plan = models.CharField(max_length=255, default=None, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CARD')
    payment_gateway = models.CharField(max_length=50, default='Stripe')
    payment_address = models.CharField(max_length=200, default=None, blank=True, null=True)
    payment_url = models.CharField(max_length=255, default=None, blank=True, null=True)
    gateway_transaction_id = models.CharField(max_length=200, default=None, blank=True, null=True)
    mpgs_success_indicator = models.CharField(max_length=200, default=None, blank=True, null=True)
    mpgs_session_version = models.CharField(max_length=200, default=None, blank=True, null=True)
    mpgs_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=None, blank=True, null=True
    )
    mpgs_order_currency = models.CharField(max_length=10, default=None, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_created = models.DateTimeField(default=now)
    expiry_datetime = models.DateTimeField(default=None, blank=True, null=True)
    date_paid = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return f"Payment by {self.user.email} - {self.status}"
