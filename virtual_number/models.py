from django.db import models

class NumberRequests(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    nationality = models.CharField(max_length=255)
    purpose = models.TextField()
    service_country = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.full_name}"