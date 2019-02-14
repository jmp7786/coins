from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .categories import SubCategorySimple
from .brands import BrandSimple


class ProductCategorySimple(serializers.Serializer):
    main_category_id = serializers.IntegerField(
        source='id',
        help_text=_("1차 카테고리 항번 ")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("1차 카테고리 명")
    )
    sub_categories = SubCategorySimple(
        many=True,
        help_text=_("2차 카테고리 리스트 ")
    )


class ProductCategoryFlat(serializers.Serializer):
    main_category_id = serializers.IntegerField(
        help_text=_("1차 카테고리 항번")
    )
    main_category_name = serializers.CharField(
        help_text=_("1차 카테고리명")
    )
    sub_category_id = serializers.IntegerField(
        help_text=_("2차 카테고리 항번")
    )
    sub_category_name = serializers.CharField(
        help_text=_("2차 카테고리명")
    )


class BrandCategorySimple(serializers.Serializer):
    brand_category_id = serializers.IntegerField(
        source='id',
        help_text=_("브랜드카테고리 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("브랜드카테고리명")
    )
    brands = BrandSimple(
        many=True,
        help_text=_("해당 브랜드카테고리 브랜드 리스트")
    )


class StoreSimple(serializers.Serializer):
    store_id = serializers.IntegerField(
        source='id',
        help_text=_("스토어 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("스토어명")
    )


class StoreBasic(StoreSimple):
    store_image = serializers.URLField(
        required=False,
        help_text=_("스토어 이미지")
    )


class KeywordSimple(serializers.Serializer):
    keyword_id = serializers.IntegerField(
        source='id',
        help_text=_("키워드항번")
    )
    name = serializers.CharField(
        help_text=_("키워드명")
    )


class PriceRangeInfo(serializers.Serializer):
    price_gap = serializers.IntegerField(
        help_text=_("가격 스크롤 간격")
    )
    price_max = serializers.IntegerField(
        allow_null=True,
        help_text=_("가격 최대값")
    )
    price_range = serializers.ListField(
        child=serializers.IntegerField(),
        help_text=_("가격 자동선택 리스트 정보")
    )


class FilterResponse(serializers.Serializer):
    categories = ProductCategorySimple(
        many=True,
        required=False,
        help_text=_("제품 카테고리 목록")
    )
    brand_categories = BrandCategorySimple(
        many=True,
        required=False,
        help_text=_("브랜드 목록")
    )
    stores = StoreSimple(
        many=True,
        required=False,
        help_text=_("스토어 목록")
    )
    keywords = KeywordSimple(
        many=True,
        required=False,
        help_text=_("카테고리에 해당하는 키워드 정보 ")
    )
    price_range_info = PriceRangeInfo(
        required=False,
        help_text=_("카테고리에 해당하는 가격 정보")
    )
