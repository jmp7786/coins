from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .paging import Paging


class BrandSimple(serializers.Serializer):
    brand_id = serializers.IntegerField(
        source='id',
        help_text=_("브랜드 아이디")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("브랜드명")
    )
    brand_image = serializers.URLField(
        source='brand_image_160',
        required=False,
        help_text=_("브랜드 이미지")
    )


class RecommendBrand(BrandSimple):
    promotion_contents = serializers.CharField(
        help_text=_("프로모션 내용")
    )


class BrandBanner(serializers.Serializer):
    recommend_id = serializers.IntegerField(
        source='id',
        help_text=_("배너 항번")
    )
    link_type = serializers.IntegerField(
        help_text=_("배너 링크종류")
    )
    link_code = serializers.CharField(
        help_text=_("배너 링크값")
    )
    banner_image = serializers.URLField(
        source='brand_banner_image_720',
        default=None,
        help_text=_("배너이미지")
    )


class BrandInfo(serializers.Serializer):
    name = serializers.CharField(
        max_length=None,
        help_text=_("브랜드명")
    )
    banners = BrandBanner(
        many=True,
        help_text=_("브랜드 배너 정보 ")
    )
    banner_ratio = serializers.FloatField(
        required=False,
        help_text=_("배너 이미지 비율")
    )
    facebook = serializers.URLField(
        allow_null=True,
        help_text=_("페이스북 URL")
    )
    kakaotalk = serializers.URLField(
        allow_null=True,
        help_text=_("카카오톡 URL")
    )
    youtube = serializers.URLField(
        allow_null=True,
        help_text=_("유투브 URL")
    )
    twitter = serializers.URLField(
        allow_null=True,
        help_text=_("트위터 URL")
    )
    homepage = serializers.URLField(
        source='url',
        allow_null=True,
        help_text=_("홈페이지 URL")
    )


class BrandsResponse(serializers.Serializer):
    brands = BrandSimple(
        many=True,
        help_text=_("브랜드 리스트")
    )

    recommend_brands = RecommendBrand(
        required=False,
        many=True,
        help_text=_("추천 브랜드 리스트")
    )

    paging = Paging()
