from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from backends.api.v2.responses.products import ProductBasic, ProductSimpleWithBrand


class Award(serializers.Serializer):
    award_id = serializers.IntegerField(
        source='id',
        help_text=_("어워드 항번")
    )
    name = serializers.CharField(
        help_text=_("어워드명")
    )
    award_image = serializers.URLField(
        allow_null=True,
        help_text=_("어워드 이미지")
    )
    award_image_720 = serializers.URLField(
        allow_null=True,
        help_text=_("어워드 이미지")
    )
    image_ratio = serializers.FloatField(
        help_text=_("이미지 비율")
    )


class AwardsResponse(serializers.Serializer):
    awards = Award(
        many=True,
        help_text=_("어워드 리스트")
    )


class AwardsProductSimple(ProductSimpleWithBrand):
    product_image = serializers.URLField(
        source='image',
        required=False,
        help_text=_(" 제품이미지 (없으면 NULL)")
    )

    product_image_320 = serializers.URLField(
        required=False,
        help_text=_(" 제품이미지 (없으면 NULL)")
    )


class AwardsProduct(serializers.Serializer):
    product = AwardsProductSimple(
        help_text=_("제품 정보")
    )
    rank = serializers.IntegerField(
        help_text=_("순위")
    )
    rank_label = serializers.CharField(
        help_text=_("라벨")
    )
    rating_avg = serializers.FloatField(
        help_text=_("순위 선정시 평균 평점")
    )
    review_count = serializers.IntegerField(
        help_text=_("순위 선정시 제품 전체 리뷰 수")
    )


class AwardsSubCategory(serializers.Serializer):
    sub_category_id = serializers.IntegerField(
        source='id',
        help_text=_("서브 카테고리 항번")
    )

    name = serializers.CharField(
        help_text=_("서브 카테고리 명")
    )

    summary = serializers.CharField(
        allow_null=True,
        help_text=_("어워드에서 총평")
    )
    is_rank = serializers.BooleanField()
    is_summary = serializers.BooleanField()

    products = AwardsProduct(
        many=True
    )


class AwardsMainCategory(serializers.Serializer):
    main_category_id = serializers.IntegerField(
        source='id'
    )
    name = serializers.CharField(
        help_text=_("메인 카테고리 명")
    )

    sub_categories = AwardsSubCategory(
        many=True
    )


class AwardsCategoryProducts(serializers.Serializer):
    award_id = serializers.IntegerField(
        source='id',
        required=False,
        help_text=_("어워드 항번")
    )
    name = serializers.CharField(
        help_text=_("어워드 명")
    )
    award_image = serializers.URLField(
        source='award_x_image',
        allow_null=True,
    )
    award_image_720 = serializers.URLField(
        source='award_x_image_720',
        required=False
    )
    image_ratio = serializers.FloatField(
        source='x_file_ratio',
        required=False,
        help_text=_("이미지 비율")
    )

    cover_image = serializers.URLField(
        required=False
    )
    cover_image_720 = serializers.URLField(
        required=False
    )
    cover_ratio = serializers.FloatField(
        source='cover_file_ratio',
        required=False
    )

    choice_image = serializers.URLField(
        required=False
    )
    choice_image_720 = serializers.URLField(
        required=False
    )
    choice_ratio = serializers.FloatField(
        source='choice_file_ratio',
        required=False
    )

    main_categories = AwardsMainCategory(
        many=True
    )


class AwardsCategoryProductsResponse(serializers.Serializer):
    awards = AwardsCategoryProducts(
        required=False,
        help_text=_("어워드 전체 정보")
    )
