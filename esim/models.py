from django.db import models
from django.conf import settings


class eSIMPlan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    data_limit = models.IntegerField()  # In MB
    validity = models.IntegerField()  # In days


class eSIMActivation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(eSIMPlan, on_delete=models.CASCADE)
    activated_on = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField()
