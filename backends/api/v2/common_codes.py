from rest_framework import routers
from rest_framework import viewsets
from backends.api.v2.request_filters.common_codes import CommonCodeValueFilter, CommonCodeFilter
from models.db_common.common_codes import CommonCodeValues, CommonCodes
from .responses.common_codes import CommonCodeValueSerializer, CommonCodesSerializer


class CommonCodeValueView(viewsets.ReadOnlyModelViewSet):

    """상세 공통 코드"""
    queryset = CommonCodeValues.objects.select_related('common_codes').all()
    serializer_class = CommonCodeValueSerializer
    filter_class = CommonCodeValueFilter


class CommonCodeView(viewsets.ReadOnlyModelViewSet):

    response_docs = {
        'get_list': {
            '200': {
                'description': '공통 코드 리스트',
                'schema': {
                    'type': 'array',
                    'items': {
                        'properties': CommonCodesSerializer,
                    },
                }
            },

        },
        'get_retrieve': {
            '200': {
                'description': '공통 코드',
                'schema': {
                    'type': 'object',
                    'properties': CommonCodesSerializer,
                }
            },

        },
    }
    """공통 코드"""
    queryset = CommonCodes.objects.prefetch_related('commoncodevalues_set').all()
    serializer_class = CommonCodesSerializer
    filter_class = CommonCodeFilter

router = routers.DefaultRouter(trailing_slash=False)
#router.register(r'common_code_values', CommonCodeValueView, base_name='common_code_values')
router.register(r'common_codes', CommonCodeView, base_name='common_codes')

