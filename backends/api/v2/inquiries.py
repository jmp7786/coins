from rest_framework import routers
from rest_framework import viewsets
from libs.oauth2.permissions import CustomIsAuthenticated
from models.db_common.inquiries import Inquiry
from .responses.inquiries import InquirySerializer
from rest_framework.pagination import LimitOffsetPagination


class InquiryView(viewsets.mixins.ListModelMixin, viewsets.mixins.CreateModelMixin,
                  viewsets.GenericViewSet, viewsets.mixins.DestroyModelMixin):
    """
    문의하기
    """
    response_docs = {
        'get_list': {
            '200': {
                'description': '문의하기 리스트',
                'schema': {
                    'type': 'array',
                    'items': {
                        'properties': InquirySerializer,
                    },
                }
            },

        },
        'post_create': {
            '201': {
                'description': '문의하기 등록',
                'schema': {
                    'type': 'object',
                    'properties': InquirySerializer,
                }
            },

        },
    }
    permission_classes = (CustomIsAuthenticated,)
    queryset = Inquiry.objects.prefetch_related('inquiryreply_set')
    serializer_class = InquirySerializer
    filter_fields = ['customer_id']
    pagination_class = LimitOffsetPagination

    def perform_destroy(self, instance):
        instance.is_del = True
        instance.save()


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'inquiries', InquiryView, base_name='inquiries')


