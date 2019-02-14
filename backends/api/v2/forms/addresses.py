from rest_framework import serializers


class AddressForm(serializers.Serializer):
    cursor = serializers.IntegerField(default=None)
    limit = serializers.IntegerField(default=None, required=False)
    query = serializers.CharField(max_length=None)
