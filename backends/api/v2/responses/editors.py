from rest_framework import serializers
from models.editors import Editor


class EditorSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(read_only=True)

    class Meta:
        model = Editor
        fields = ('user_id', 'nickname', 'profile_image', 'thumbnail')
