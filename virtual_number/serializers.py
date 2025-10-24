from rest_framework import serializers
from .models import NumberRequests

class NumberRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberRequests
        fields = ['full_name', 'email', 'nationality', 'purpose', 'service_country']


class NumberRequestResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)
    errors = serializers.JSONField(required=False, allow_null=True)