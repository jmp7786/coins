from rest_framework import serializers


class Banner(serializers.Serializer):
    banner_id = serializers.IntegerField(source='id', required=False)
    title = serializers.CharField()
    link_type = serializers.CharField()
    link_target = serializers.CharField()
    banner_image = serializers.URLField(source='image', required=False)
    seq = serializers.IntegerField(required=False)
