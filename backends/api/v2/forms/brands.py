from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from backends.common.exceptions import InvalidParameterException
from .paging import BasicListFormMixin


class BrandCategoryFilterMixin(serializers.Serializer):
    brand_category_id = serializers.IntegerField(
        required=False,
        help_text=_("브랜드 카테고리 항번")
    )
    brand_id = serializers.IntegerField(
        required=False,
        help_text=_("브랜드 항번")
    )


class BrandsForm(BasicListFormMixin):
    brand_category_id = serializers.IntegerField(
        required=False,
        help_text=_("브랜드 카테고리 항번")
    )

    initial = serializers.IntegerField(
        required=False,
        help_text=_(
            "이니셜 (IOS용)"
            "<br>1 ~ 14 - ㄱ~ㅎ"
            "<br>15 - a-zA-Z, 0-9"
        )
    )

    def validate_initial(self, value):
        if value < 1 or value > 15:
            raise InvalidParameterException(
                _('Value out of range. Must be between 1 and 15.')
            )

        return value
