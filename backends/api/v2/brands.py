from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.utils import request_ads
from services.brands import service as brands_service
from services.ranking import service as ranking_service
from .forms.brands import BrandsForm
from .forms.products import BrandProductsForm
from .responses.brands import BrandsResponse
from .responses.categories import BrandCategoriesResponse
from .responses.products import BrandProductsResponse


class BrandView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': BrandsForm,
        'get_products': BrandProductsForm
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '전체 브랜드 리스트',
                'schema': {
                    'type': 'object',
                    'properties': BrandsResponse,
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
        'get_categories': {
            '200': {
                'description': '전체 브랜드 카테고리 리스트',
                'schema': {
                    'type': 'object',
                    'properties': BrandCategoriesResponse,
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
                'description': '브랜드별 랭킹에서의 제품리스트',
                'schema': {
                    'type': 'object',
                    'properties': BrandProductsResponse,
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
        전체 브랜드 리스트
        """
        params = BrandsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')
        initial = params.validated_data.get('initial')
        brand_category_id = params.validated_data.get('brand_category_id')

        response = dict()
        brands = brands_service.get_all_brands(**params.validated_data)
        response['brands'] = brands.get('list')

        if cursor is None:
            if not initial or initial == 1:
                if not brand_category_id:
                    recommend_brands = brands_service.get_recommend_brands()
                    response['recommend_brands'] = recommend_brands

        response['paging'] = dict()
        next_offset = brands.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(BrandsResponse(response).data, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def categories(self, request):
        """
        전체 브랜드 카테고리 리스트
        """
        response = dict()
        response['categories'] = brands_service.get_all_brand_categorise()

        return Response(BrandCategoriesResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def products(self, request, pk=None):
        """
        브랜드별 제품 순위 리스트
        """
        params = BrandProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        response = dict()
        results = ranking_service.get_products_ranking_by_brand_id(
            brand_id=pk,
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

            brand_info = brands_service.get_brand_banner(brand_id=pk)
            if brand_info:
                response['brand_info'] = brand_info

                # ads server
                banners = getattr(brand_info, 'banners')
                if banners:
                    brand_banner_ids = ",".join([str(banner.id) for banner in banners])
                    request_ads('GP0003', brand_banner_ids)

        return Response(BrandProductsResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'brands', BrandView, base_name='brands')
