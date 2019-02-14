from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.utils import request_ads
from models.products import SubCategory
from services.categories import service as categories_service
from services.ranking import service as ranking_service
from .forms.products import CategoryProductsForm
from .responses.categories import CategoriesResponse
from .responses.products import CategoryProductsResponse


class CategoryView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_products': CategoryProductsForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '전체 제품 카테고리 리스트',
                'schema': {
                    'type': 'object',
                    'properties': CategoriesResponse,
                }
            },

        },
        'get_products': {
            '200': {
                'description': '전체 제품 카테고리 리스트',
                'schema': {
                    'type': 'object',
                    'properties': CategoryProductsResponse,
                }
            },
        },
    }

    def list(self, request):
        """
        전체 카테고리 리스트 ( 통합 검색 )
        ---
        카테고리 이미지와 추천 제품 광고 정보를 포함한 전체 카테고리 리스트 정보
        """
        response = dict()

        try:
            categories = categories_service.get_all_product_categories_by_dynamodb()
            response['categories'] = categories
        except:
            response['categories'] = categories_service.get_all_product_categories()

        return Response(CategoriesResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def products(self, request, pk=None):
        """
        카테고리별 제품 순위 리스트
        """

        category = get_object_or_404(SubCategory, id=pk)

        params = CategoryProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        response = dict()
        results = ranking_service.get_products_ranking_by_category_id(
            category_id=pk,
            **params.validated_data
        )

        response['products'] = results.get('list')
        response['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        if cursor is None:
            response['category_info'] = category

            products_count = results.get('products_count')
            if products_count:
                response['total_count'] = products_count

            recommend_product = ranking_service.get_recommend_product_by_sub_category_id(
                category_id=pk
            )
            if recommend_product:
                response['recommend_products'] = [recommend_product]

                # ads server
                ad_type = recommend_product.get('product_type')
                if ad_type == 'like':
                    request_ads('GP0009', str(recommend_product.get('id')))
                elif ad_type == 'editor':
                    request_ads('GP0012', str(recommend_product.get('product_id')))

        return Response(CategoryProductsResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'categories', CategoryView, base_name='categories')
