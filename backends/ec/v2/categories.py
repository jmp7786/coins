from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from backends.ec.v2.responses.categories import MainCategoryBaseSerializer, SubCategoryBaseSerializer
from models.products import MainCategory, SubCategory


class MainCategoryView(viewsets.ViewSet):
    def list(self, request):
        qs = MainCategory.objects.filter(is_display=True)
        main_categories = MainCategoryBaseSerializer(qs, many=True)

        response = dict()
        response['main_categories'] = main_categories.data

        return Response(response, status=status.HTTP_200_OK)


class SubCategoryView(viewsets.ViewSet):
    @detail_route()
    def sub_categories(self, request, pk=None):
        qs = SubCategory.objects.filter(is_display=True, main_category=pk)
        sub_categories = SubCategoryBaseSerializer(qs, many=True)

        response = dict()
        response['sub_categories'] = sub_categories.data

        return Response(response, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'categories/main_categories', MainCategoryView, base_name='main_category')
router.register(r'categories/main_categories', SubCategoryView, base_name='sub_category')
