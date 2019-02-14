from rest_framework import serializers


class AddressResponse(serializers.Serializer):
    zip = serializers.CharField(max_length=None)
    doromyeong_addr = serializers.CharField(max_length=None)
    etc = serializers.CharField(max_length=None)
    jibun_addr = serializers.CharField(max_length=None)

    def to_representation(self, instance):
        return {
            'zip': instance.zip,
            'doromyeong_addr': instance.doromyeong_addr + ' ' + instance.etc,
            'jibun_addr': instance.jibun_addr
        }