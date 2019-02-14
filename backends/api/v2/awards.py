from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from models.awards import Awards
from services.awards import service as awards_service
from .forms.paging import BasicListFormMixin
from .responses.awards import AwardsResponse, AwardsCategoryProductsResponse


class AwardView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': BasicListFormMixin,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '어워드 리스트',
                'schema': {
                    'type': 'object',
                    'properties': AwardsResponse,
                }
            },
        },
        'get_retrieve': {
            '200': {
                'description': '어워드 정보',
                'schema': {
                    'type': 'object',
                    'properties': AwardsCategoryProductsResponse,
                }
            },
        },
    }

    def list(self, request):
        """
        어워드 리스트
        """
        params = BasicListFormMixin(data=request.GET)
        params.is_valid(raise_exception=True)

        response = dict()
        results = awards_service.get_list(
            **params.validated_data
        )
        response['awards'] = results.get('list')
        response['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(
            AwardsResponse(response).data,
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, pk=None):
        """
        어워드 수상 제품 전체
        """
        try:
            results = awards_service.get_awards_products_by_dynamodb(award_id=pk)
        except:
            get_object_or_404(Awards, id=pk)
            results = awards_service.get_award_products(award_id=pk)

        response = dict()
        response['awards'] = results

        return Response(
            AwardsCategoryProductsResponse(response).data,
            status=status.HTTP_200_OK
        )


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'awards', AwardView, base_name='awards')
