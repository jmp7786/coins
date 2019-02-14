from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .brands import BrandCategoryFilterMixin
from .paging import BasicListFormMixin
from .products import CategoryFilterMixin, CommerceFilterMixin
from .users import UserFilterMixin


class ReviewsListFormMixin(BasicListFormMixin):
    RATING_CHOICES = ('all', '1', '2', '3', '4', '5')

    order = serializers.ChoiceField(
        default='create_date_desc',
        choices=('create_date_desc', 'create_date_asc', 'like_desc', 'like_asc'),
        help_text=_(
            "정렬순서 <br>"
            "등록순 내림차순(기본값) - create_date_desc, <br>"
            "등록순 오름차순 - create_date_asc,<br>"
            "좋아요순 내림차순 - like_desc, <br>"
            "좋아요순 오름차순 - like_asc,"
        )
    )

    rating = serializers.CharField(
        default='all',
        max_length=None,
        help_text=_(
            "평점 (다중선택시 값을 콤마로 구분) <br>"
            "전체(기본값) - all, <br>"
            "짱짱(5) - 5, <br>"
            "굿굿(4) - 4, <br>"
            "쏘쏘(3) - 3, <br>"
            "별로(2) - 2, <br>"
            "최악(1) - 1"
        )
    )

    def validate_rating(self, value):
        if value:
            for rating in value.split(','):
                if rating not in self.RATING_CHOICES:
                    raise serializers.ValidationError('this field is invalid')
        return value


class ReviewCheckForm(serializers.Serializer):
    product_id = serializers.IntegerField(
        help_text=_("제품 항번")
    )


class ReviewsForm(ReviewsListFormMixin, UserFilterMixin, CategoryFilterMixin, CommerceFilterMixin):
    query = serializers.CharField(
        required=False,
        help_text=_(
            "검색어 <br>'"
            "#+{검색어}' : 태그로 리뷰검색 <br>"
            "'@+{검색어}' : 닉네임으로 리뷰검색"
        )
    )

    top_reviewers = serializers.BooleanField(
        default=False,
        help_text=_("top reviewer 포함 여부 flag")
    )


class UserReviewsForm(ReviewsListFormMixin, CategoryFilterMixin, BrandCategoryFilterMixin, CommerceFilterMixin):
    pass


class ProductReivewsForm(ReviewsListFormMixin, UserFilterMixin):
    STATE_CHOICES = ('normal', 'blinded')
    state = serializers.ChoiceField(
        default='normal',
        choices=STATE_CHOICES,
        help_text=_(
            "리뷰 상태"
            "<br>normal (default)"
            "<br>blinded"
        )
    )
    contents = serializers.CharField(
        required=False,
        help_text=_("리뷰내용 검색")
    )


class ReviewWriteForm(serializers.Serializer):
    contents = serializers.CharField(
        help_text=_("리뷰 내용")
    )
    rating = serializers.IntegerField(
        help_text=_("평점 (1, 2, 3, 4, 5) ")
    )
    product_id = serializers.IntegerField(
        help_text=_("제품 아이디")
    )


class ReviewUpdateForm(ReviewWriteForm):
    product_id = None


class ReviewReportForm(serializers.Serializer):
    report_type = serializers.CharField(
        help_text=_("신고사유(신고유형)")
    )
    contents = serializers.CharField(
        required=False,
        help_text=_("추가설명")
    )
