from rest_framework import serializers


class BrandSimple(serializers.Serializer):
    brand_id = serializers.IntegerField(source='id')
    name = serializers.CharField(max_length=None)
