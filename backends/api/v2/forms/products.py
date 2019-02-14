from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.common.exceptions import InvalidParameterException
from .brands import BrandCategoryFilterMixin
from .paging import BasicListFormMixin
from .users import UserFilterMixin


class ProductsListFormMixin(BasicListFormMixin):
    pass


class CategoryFilterMixin(serializers.Serializer):
    main_category_id = serializers.IntegerField(
        required=False,
        help_text=_("1차카테고리 항번")
    )

    sub_category_id = serializers.IntegerField(
        required=False,
        help_text=_("2차카테고리 항번")
    )


class CommerceFilterMixin(serializers.Serializer):
    is_commerce = serializers.BooleanField(
        required=False,
        help_text=_("구매가능 여부")
    )


class ProductsForm(ProductsListFormMixin):
    query = serializers.CharField(
        required=False,
        help_text=_(
            "검색어 <br>'"
            "(제품명, 브랜드명, 2차 카테고리명)<br>"
        )
    )


class ProductsMonthForm(BasicListFormMixin):
    pass


class WeeklyProductsForm(BasicListFormMixin):
    weekly_count = serializers.IntegerField(
        default=10,
        help_text=_("명예의 전당에 오를 최소 1위 유지 주간")
    )


class CategoryProductsForm(BasicListFormMixin, UserFilterMixin, BrandCategoryFilterMixin, CommerceFilterMixin):
    ORDER_CHOICES = (
        'rank',
        'review_asc', 'review_desc',
        'rating_avg_asc', 'rating_avg_desc',
        'price_asc', 'price_desc'
    )
    TERM_CHOICES = ('all', '3month', '6month')

    order = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        default='rank',
        help_text=_(
            "정렬순서"
            "<br>랭킹순(기본값) - rank,"
            "<br>리뷰수 오름차순 - review_asc,"
            "<br>리뷰수 내림차순 - review_desc,"
            "<br>평점 오름차순 - rating_avg_asc,"
            "<br>평점 내림차순 - rating_avg_desc,"
            "<br>가격 오름차순 - price_asc,"
            "<br>가격 내림차순 - price_desc"
        )
    )

    rank_term = serializers.ChoiceField(
        choices=TERM_CHOICES,
        default='all',
        help_text=_(
            "랭킹집계기간"
            "<br>전체(기본값) - all,"
            "<br>3개월 - 3month,"
            "<br>6개월 - 6month"
        )
    )

    min_price = serializers.IntegerField(
        required=False,
        help_text=_("가격최소값")
    )

    max_price = serializers.IntegerField(
        required=False,
        help_text=_("가격최대값")
    )

    keywords = serializers.CharField(
        required=False,
        help_text=_("키워드항번 (다중선택시 값을 콤마로 구분)")
    )

    def validate_keywords(self, value):
        if value:
            keyword_ids = list()
            for keyword in value.split(','):
                try:
                    keyword_ids.append(int(keyword))
                except ValueError:
                    raise InvalidParameterException(
                        _("keywords is invalid")
                    )

        return keyword_ids


class BrandProductsForm(BasicListFormMixin, UserFilterMixin, CategoryFilterMixin, CommerceFilterMixin):
    ORDER_CHOICES = (
        'rank',
        'review_asc', 'review_desc',
        'rating_avg_asc', 'rating_avg_desc',
        'price_asc', 'price_desc'
    )
    TERM_CHOICES = ('all', '3month', '6month')

    order = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        default='rank',
        help_text=_(
            "정렬순서"
            "<br>랭킹순(기본값) - rank,"
            "<br>리뷰수 오름차순 - review_asc,"
            "<br>리뷰수 내림차순 - review_desc,"
            "<br>평점 오름차순 - rating_avg_asc,"
            "<br>평점 내림차순 - rating_avg_desc,"
            "<br>가격 오름차순 - price_asc,"
            "<br>가격 내림차순 - price_desc"
        )
    )

    rank_term = serializers.ChoiceField(
        choices=TERM_CHOICES,
        default='all',
        help_text=_(
            "랭킹집계기간"
            "<br>전체(기본값) - all,"
            "<br>3개월 - 3month,"
            "<br>6개월 - 6month"
        )
    )


class StoreProductsForm(BasicListFormMixin, UserFilterMixin, CategoryFilterMixin, CommerceFilterMixin):
    ORDER_CHOICES = (
        'rank',
        'review_asc', 'review_desc',
        'rating_avg_asc', 'rating_avg_desc',
        'price_asc', 'price_desc'
    )
    TERM_CHOICES = ('all', '3month', '6month')

    order = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        default='rank',
        help_text=_(
            "정렬순서"
            "<br>랭킹순(기본값) - rank,"
            "<br>리뷰수 오름차순 - review_asc,"
            "<br>리뷰수 내림차순 - review_desc,"
            "<br>평점 오름차순 - rating_avg_asc,"
            "<br>평점 내림차순 - rating_avg_desc,"
            "<br>가격 오름차순 - price_asc,"
            "<br>가격 내림차순 - price_desc"
        )
    )

    rank_term = serializers.ChoiceField(
        choices=TERM_CHOICES,
        default='all',
        help_text=_(
            "랭킹집계기간"
            "<br>전체(기본값) - all,"
            "<br>3개월 - 3month,"
            "<br>6개월 - 6month"
        )
    )

    min_price = serializers.IntegerField(
        required=False,
        help_text=_("가격최소값")
    )

    max_price = serializers.IntegerField(
        required=False,
        help_text=_("가격최대값")
    )


class UserProductsForm(BasicListFormMixin, CategoryFilterMixin, BrandCategoryFilterMixin, CommerceFilterMixin):
    """
    회원 wish 리스트
    """
    ORDER_CHOICES = (
        'create_date_desc', 'create_date_asc',
        'rating_avg_desc', 'rating_avg_asc',
    )

    order = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        default='create_date_desc',
        help_text=_(
            "정렬순서"
            "<br>랭킹순(기본값) - rank,"
            "<br>리뷰수 오름차순 - review_asc,"
            "<br>리뷰수 내림차순 - review_desc,"
            "<br>평점 오름차순 - rating_avg_asc,"
            "<br>평점 내림차순 - rating_avg_desc,"
            "<br>가격 오름차순 - price_asc,"
            "<br>가격 내림차순 - price_desc"
        )
    )

    store_id = serializers.CharField(
        required=False,
        help_text=_("스토어 항번<br>(다중선택시 값을 콤마로 구분)")
    )
