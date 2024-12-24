from rest_framework import serializers

class eSIMPlanFilterSerializer(serializers.Serializer):
    locationCode = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    packageCode = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)


class eSIMProfileSerializer(serializers.Serializer):
    orderNo = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)
    pager = serializers.DictField(child=serializers.IntegerField(), required=False)
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['pager'] = {
            "pageNum": 1,
            "pageSize": 20
        }
        return representation