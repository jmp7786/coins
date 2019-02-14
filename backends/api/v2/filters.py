from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from services.brands import service as brand_service
from services.categories import service as categories_service
from services.stores import service as store_service
from services.products import service as product_service
from .forms.filters import FiltersForm
from .responses.filters import FilterResponse


class FilterView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': FiltersForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '리스트 필터 데이터',
                'schema': {
                    'type': 'object',
                    'properties': FilterResponse,
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
        리스트 필터
        ---
        <b>type 에 따라 응답 값이 다름 </b>
        <pre>
        <br> user-review : categoires
        <br>               brand_categories
        <br>
        <br> user-wish : stores
        <br>             categories
        <br>             brand_categories
        <br>
        <br> category-rank : brand_categoires
        <br>                 keywords
        <br>                 price_range_info
        <br>
        <br> brand-rank : categories
        <br>
        <br> store-rank : categories
        <br>              price_range_info
        <br>
        <br> review : categories
        </pre>
        """
        params = FiltersForm(data=request.GET)
        params.is_valid(raise_exception=True)

        filter_type = params.validated_data.get('type')

        response = {}
        if filter_type == 'user-review':
            user_id = params.validated_data.get('user_id')
            response['categories'] = categories_service.get_user_reviews_categories(user_id)
            response['brand_categories'] = brand_service.get_user_reviews_categories(user_id)

        elif filter_type == 'user-wish':
            user_id = params.validated_data.get('user_id')
            response['stores'] = store_service.get_list()
            response['categories'] = categories_service.get_user_wishes_categories(user_id)
            response['brand_categories'] = brand_service.get_user_wishes_categories(user_id)

        elif filter_type == 'category-rank':
            category_id = params.validated_data.get('category_id')
            brand_categories = brand_service.get_product_category_rank_categories(category_id)
            response['brand_categories'] = brand_categories
            response['price_range_info'] = product_service.get_price_range_by_category_id(category_id)
            response['keywords'] = categories_service.get_keywords_by_category_id(category_id)

        elif filter_type == 'brand-rank':
            brand_id = params.validated_data.get('brand_id')
            response['categories'] = categories_service.get_categoires_by_brand_id(brand_id)

        elif filter_type == 'store-rank':
            store_id = params.validated_data.get('store_id')
            response['categories'] = categories_service.get_categories_by_store_id(store_id)
            response['price_range_info'] = product_service.get_price_range_by_store_id(store_id)

        elif filter_type == 'review':
            response['categories'] = categories_service.get_all_product_categories(filter_format=True)

        return Response(FilterResponse(response).data, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'filters', FilterView, base_name='filters')
