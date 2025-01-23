from django.db import models
from django.conf import settings
from billing.models import Payment


class eSIMPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    package_code = models.CharField(max_length=25)
    slug = models.CharField(max_length=25)
    currency_code = models.CharField(max_length=25)
    speed = models.CharField(max_length=25)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.CharField(max_length=255)  # In Bytes
    volume_used = models.CharField(max_length=255, default=None, blank=True, null=True)  # In Bytes
    duration = models.IntegerField()  # In days
    duration_unit = models.CharField(max_length=25)
    support_top_up_type = models.IntegerField()  # In days
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='esim_plans')
    esim_status = models.CharField(max_length=25, default='PAID')
    smdp_status = models.CharField(max_length=25, default='RELEASED')
    seller = models.CharField(max_length=25, default='esimaccess')
    order_no = models.CharField(max_length=25, default=None, blank=True, null=True)
    location_code = models.CharField(max_length=25, default=None, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    activated_on = models.DateTimeField(default=None, blank=True, null=True)
    expires_on = models.DateTimeField()

    def __str__(self):
        return f"eSIM Plan {self.name} ({self.esim_status})"