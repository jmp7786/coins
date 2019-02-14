import django_filters
from django_filters import rest_framework as filters
from models.db_common.common_codes import CommonCodeValues, CommonCodes


class CommonCodeFilter(filters.FilterSet):

    common_cd_value = django_filters.CharFilter(
        name='common_cd_value',
        help_text='공통 코드 값',
        lookup_expr='exact',
    )

    class Meta:
        model = CommonCodes
        fields = ('common_cd_value', )


class CommonCodeValueFilter(filters.FilterSet):

    common_cd_value = django_filters.CharFilter(
        name='common_codes__common_cd_value',
        help_text='common codes',
        lookup_expr='exact',
    )

    class Meta:
        model = CommonCodeValues
        fields = ('common_codes', 'common_cd_value')