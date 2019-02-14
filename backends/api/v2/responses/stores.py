from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class StoreSimple(serializers.Serializer):
    store_id = serializers.IntegerField(
        source='id',
        help_text=_("스토어 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("스토어명")
    )
    store_image = serializers.URLField(
        required=False,
        help_text=_("스토어 이미지")
    )


class StoreBasic(StoreSimple):
    store_image_720 = serializers.URLField(
        required=False,
        help_text=_("스토어 이미지")
    )


class StoreBanner(serializers.Serializer):
    recommend_id = serializers.IntegerField(
        source='id',
        help_text=_("배너 아이디")
    )
    link_type = serializers.IntegerField(
        help_text=_("배너 링크종류")
    )
    link_code = serializers.CharField(
        help_text=_("배너 링크값")
    )
    banner_image = serializers.URLField(
        source='store_banner_image',
        default=None,
        help_text=_("배너이미지")
    )
    banner_image_720 = serializers.URLField(
        source='store_banner_image_720',
        default=None,
        help_text=_("배너이미지")
    )


class StoreInfo(serializers.Serializer):
    name = serializers.CharField(
        max_length=None,
        help_text=_("브랜드명")
    )
    banners = StoreBanner(
        many=True,
        help_text=_("브랜드 배너 정보 ")
    )
    banner_ratio = serializers.FloatField(
        required=False,
        help_text=_("배너 이미지 비율")
    )


class StoresResponse(serializers.Serializer):
    stores = StoreBasic(
        many=True,
        help_text=("스토어 리스트")
    )
