from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from backends.api.v2.responses.recommends import RecommandProduct


class SubCategorySimple(serializers.Serializer):
    sub_category_id = serializers.IntegerField(
        source='id',
        help_text=_("2차카테고리 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("2차카테고리명")
    )


class SubCategoryBasic(SubCategorySimple):
    is_new = serializers.BooleanField(
        help_text=_("New 표시 여부")
    )


class MainCategorySimple(serializers.Serializer):
    main_category_id = serializers.IntegerField(
        source='id',
        help_text=_("1차 카테고리 항번")
    )
    name = serializers.CharField(
        help_text=_("1차 카테고리 명")
    )


class MainCategoryBasic(MainCategorySimple):
    main_category_image = serializers.URLField(
        source='image',
        allow_null=True,
        help_text=_("1차 카테고리 이미지")
    )
    is_new = serializers.BooleanField(
        help_text=_("New 표시 여부")
    )
    sub_categories = SubCategoryBasic(
        many=True,
        help_text=_("2차 카테고리 리스트")
    )


class CategoryInfo(SubCategorySimple):
    sub_category_id = serializers.IntegerField(
        source='id',
        help_text=_("2차카테고리 항번")
    )
    main_category = MainCategorySimple(
        help_text=_("main 카테고리 정보")
    )


class BrandCategorySimple(serializers.Serializer):
    brand_category_id = serializers.IntegerField(
        source='id',
        help_text=_("브랜드 카테고리 항번 ")
    )
    name = serializers.CharField(
        help_text=_("브랜드 카테고리명")
    )
    brand_category_image = serializers.URLField(
        source='brand_category_image_160',
        help_text=_("브랜드 카테고리 이미지 ")
    )


class AllCateogires(MainCategoryBasic):
    monthly = RecommandProduct(
        required=False,
        help_text=_("추천제품 및 이달의추천신제품")
    )


class CategoriesResponse(serializers.Serializer):
    categories = AllCateogires(
        many=True,
        help_text=_("전체 카테고리 리스트")
    )


class BrandCategoriesResponse(serializers.Serializer):
    categories = BrandCategorySimple(
        many=True,
        help_text=_("전체 브랜드 카테고리 리스트")
    )
