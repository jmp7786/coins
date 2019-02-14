from rest_framework import serializers


class UserResponse(serializers.Serializer):
    user_id = serializers.IntegerField(source='id', required=False)
