from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from backends.ec.v2.forms.brands import BrandsForm
from backends.ec.v2.responses.brands import BrandSimple
from services.brands import service as brands_service


class BrandView(viewsets.ViewSet):
    def list(self, request):
        params = BrandsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.data.get('cursor')
        limit = params.data.get('limit')

        brands = BrandSimple(brands_service.search_brand_list(params), many=True)

        response = dict()
        response['brands'] = brands.data

        if cursor == 1:
            response['total_count'] = brands_service.search_brand_list(params, only_count=True)

        if len(response['brands']) == limit + 1:
            next_offset = cursor + 1
            del response['brands'][-1]
        else:
            next_offset = None

        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(response, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'brands', BrandView, base_name='brands')
