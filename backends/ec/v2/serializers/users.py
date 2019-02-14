from rest_framework import serializers

from models.users import User


class NameContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'tel')
