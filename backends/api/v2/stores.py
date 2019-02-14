from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.utils import request_ads
from services.stores import service as store_service
from services.ranking import service as ranking_service
from .forms.products import StoreProductsForm
from .responses.products import StoreProductsResponse
from .responses.stores import StoresResponse


class StoreView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_products': StoreProductsForm
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '전체 스토어 리스트',
                'schema': {
                    'type': 'object',
                    'properties': StoresResponse,
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
        'get_products': {
            '200': {
                'description': '스토어별 랭킹에서의 제품리스트',
                'schema': {
                    'type': 'object',
                    'properties': StoreProductsResponse,
                }
            },
            '400': {
                'description': '유효하지 않은 요청 파라미터',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'detail': {
                            'type': 'string'
                        },
                        'message': {
                            'type': 'string'
                        },
                        'code': {
                            'type': 'string'
                        }
                    }
                },
            },
        },
    }

    def list(self, request):
        """
        전체 스토어 리스트
        """
        response = dict()
        try:
            response['stores'] = store_service.get_all_stores_by_dynamodb()
        except:
            response['stores'] = store_service.get_list()

        return Response(StoresResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def products(self, request, pk=None):
        """
        스토어별 제품 순위 리스트
        """
        params = StoreProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        response = dict()
        results = ranking_service.get_products_ranking_by_store_id(
            store_id=pk,
            **params.validated_data
        )

        response['products'] = results.get('list')
        response['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        if cursor is None:
            products_count = results.get('products_count')
            if products_count:
                response['total_count'] = products_count

            store_info = store_service.get_store_banners(store_id=pk)
            if store_info:
                response['store_info'] = store_info

                # ads server
                banners = getattr(store_info, 'banners')
                if banners:
                    store_banner_ids = ",".join([str(banner.id) for banner in banners])
                    request_ads('GP0006', store_banner_ids)

        return Response(StoreProductsResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'stores', StoreView, base_name='stores')
