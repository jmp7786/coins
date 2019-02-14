from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.common.exceptions import InvalidParameterException


class FiltersForm(serializers.Serializer):
    TYPE_CHOICES = (
        'user-review', 'user-wish',
        'category-rank', 'brand-rank', 'store-rank',
        'review'
    )

    TYPE_PARAMETER = {}
    for type in TYPE_CHOICES:
        TYPE_PARAMETER[type] = type.split('-')[0] + '_id'

    type = serializers.ChoiceField(
        choices=TYPE_CHOICES,
        help_text=_(
            "필터의 종류"
            "<br> user-reivew : 회원프로필 리뷰 리스트"
            "<br> user-wish : 회원프로필 위시 리스트"
            "<br> category-rank : 카테고리별 제품 순위 리스트"
            "<br> brand-rank : 브랜드별 제품 순위 리스트"
            "<br> store-rank : 스토어별 제품 순위 리스트"
            "<br> review : 리뷰 리스트"
        )
    )

    user_id = serializers.IntegerField(
        required=False,
        help_text=_(
            "회원 항번"
            "<br><b>type 값이 'user-reivew' 혹은 'user-wish' 일경우 필수</b>"
        )
    )

    category_id = serializers.IntegerField(
        required=False,
        help_text=_(
            "제품 카테고리 항번"
            "<br><b>type 값이 'category-rank' 일경우 필수</b>"
        )
    )

    brand_id = serializers.IntegerField(
        required=False,
        help_text=_(
            "브랜드 항번"
            "<br><b>type 값이 'brand-rank' 일경우 필수</b>"
        )
    )

    store_id = serializers.IntegerField(
        required=False,
        help_text=_(
            "스토어 항번"
            "<br><b>type 값이 'store-rank' 일경우 필수</b>"
        )
    )

    def validate(self, attrs):

        filter_type = attrs.get('type')
        required_parameter = self.TYPE_PARAMETER.get(filter_type)

        if required_parameter != 'review_id' and not attrs.get(required_parameter):
            raise InvalidParameterException(
                _("{} is required".format(self.TYPE_PARAMETER.get(filter_type)))
            )

        return attrs
