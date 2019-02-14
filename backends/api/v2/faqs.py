from rest_framework import viewsets
from rest_framework import routers
from rest_framework.pagination import LimitOffsetPagination
from libs.oauth2.permissions import CustomIsAuthenticated
from models.db_common.faqs import Faq
from backends.api.v2.responses.faqs import FaqSerializer
from backends.api.v2.request_filters.faqs import FaqFilter


class FaqView(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):

    response_docs = {
        'get_list': {
            '200': {
                'description': '공통 코드 리스트',
                'schema': {
                    'type': 'array',
                    'items': {
                        'properties': FaqSerializer,
                    },
                }
            },

        },
    }
    permission_classes = (CustomIsAuthenticated,)
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    filter_class = FaqFilter
    pagination_class = LimitOffsetPagination

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'faqs', FaqView, base_name='faqs')
