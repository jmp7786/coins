import json
from enum import Enum

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.common.exceptions import NotFoundException
from models.products import Product


class Sort(Enum):
    create_date_desc = '-pk'
    create_date_asc = 'pk'
    name_desc = '-name -pk'
    name_asc = 'name -pk'
    price_desc = '-price -pk'
    price_asc = 'price -pk'


def validate_is_display(value):
    if value not in [0, 1]:
        raise serializers.ValidationError("This field is not valid.")


def validate_order(value):
    if value not in Sort._member_names_:
        raise serializers.ValidationError("This param('%s') is not valid." % value)


class ProductsForm(serializers.Serializer):
    cursor = serializers.IntegerField(default=1)
    limit = serializers.IntegerField(default=20, required=False)
    order = serializers.CharField(required=False, validators=[validate_order])
    name = serializers.CharField(default=None, max_length=None)
    product_id = serializers.IntegerField(default=None)
    brand_id = serializers.IntegerField(default=None)
    is_display = serializers.IntegerField(default=None, validators=[validate_is_display])
    main_category_id = serializers.IntegerField(default=None)
    sub_category_id = serializers.IntegerField(default=None)

    def validate(self, attrs):
        if attrs.get('name') is None and \
                        attrs.get('product_id') is None and \
                        attrs.get('main_category_id') is None and \
                        attrs.get('sub_category_id') is None and \
                        attrs.get('brand_id') is None:
            raise serializers.ValidationError(
                "One of name, product_id, main_category_id, brand_id or sub_category_id is required.")

        if attrs.get('order'):
            attrs['order'] = Sort[attrs['order']].value

        return attrs


class PricingForm(serializers.Serializer):
    data = serializers.JSONField(
        help_text=_("상품 가격정보 데이터")
    )

    def validate_data(self, value):
        try:
            params = list()
            for item in value:
                if not Product.objects.filter(id=item['id']).exists():
                    raise NotFoundException(
                        "Not existed {} product".format(item['id'])
                    )
                params.append({
                    'product_id': item['id'],
                    'goods_count': item['cnt'],
                    'min_price': item['min'],
                    'max_price': item['max']
                })
        except NotFoundException:
            raise
        except:
            raise serializers.ValidationError(
                "Invalid parameter"
            )

        return params
