from rest_framework import serializers

class eSIMPlanFilterSerializer(serializers.Serializer):
    locationCode = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    packageCode = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)