from rest_framework import serializers
from .models import NumberRequests

class NumberRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberRequests
        fields = ['full_name', 'email', 'nationality', 'purpose', 'service_country']