from rest_framework import serializers


class BrandsForm(serializers.Serializer):
    cursor = serializers.IntegerField(default=1)
    limit = serializers.IntegerField(default=20, required=False)
    name = serializers.CharField(max_length=None)
