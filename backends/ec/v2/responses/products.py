from rest_framework import serializers

from backends.ec.v2.responses.brands import BrandSimple
from backends.ec.v2.responses.categories import SubCategoryBaseSerializer, ProductCategoryResponse


class ProductSimple(serializers.Serializer):
    product_id = serializers.IntegerField(source='id', help_text='제품 항번')
    name = serializers.CharField(max_length=None, help_text='제품명')
    product_image = serializers.URLField(source='product_image_160', required=False, help_text='제품 이미지')


class ProductBasic(ProductSimple):
    brand = BrandSimple(required=True, help_text='브랜드 정보')
    rating_avg = serializers.FloatField(required=False, help_text='평점')
    price = serializers.DecimalField(required=False, max_digits=None, decimal_places=0, help_text='가격')
    is_display = serializers.BooleanField(required=False, help_text='노출 여부')
    categories = ProductCategoryResponse(required=False, many=True, help_text='제품 카테고리')


class ProductDetail(ProductBasic):
    review_count = serializers.IntegerField(help_text='리뷰 수')
    rank_info = serializers.CharField(required=False, help_text='제품 순위 정보')
