from django.db import transaction
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from backends.ec.v2.forms.products import ProductsForm, PricingForm
from backends.ec.v2.responses.products import ProductBasic, ProductDetail
from libs.elasticsearch.reviews import elasticsearch_reviews
from libs.shortcuts import get_object_or_404
from models.product_goods import ProductGoods
from models.products import Product
from services.products import service as products_service


class ProductView(viewsets.ViewSet):
    parameter_classes = {
        'get_list': ProductsForm,
        'put_pricing': PricingForm
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': 'Return the list of the Test objects.',
                'schema': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': ProductBasic,
                    }
                }
            },
            '404': {
                'description': 'Not found',
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
            }
        },
        'get_detail': {
            '200': {
                'description': 'Return single Test object.',
                'schema': {
                    'type': 'object',
                    'properties': ProductDetail
                }
            },
            '404': {
                'description': 'Not found.',
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
            }
        },
        'put_pricing': {
            '404': {
                'description': 'Not found.',
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
            }
        }
    }

    def list(self, request):
        """
        제품 리스트 (검색)
        """
        params = ProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.data.get('cursor')
        limit = params.data.get('limit')

        products = ProductBasic(products_service.search_product_list(params), many=True)

        response = dict()
        response['products'] = products.data

        response['total_count'] = products_service.search_product_list(params, only_count=True)

        if len(response['products']) == limit + 1:
            next_offset = cursor + 1
            del response['products'][-1]
        else:
            next_offset = None

        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(response, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def detail(self, request, pk=None):
        """
        제품 상세 정보
        """
        product = get_object_or_404(Product, id=pk)

        product.read_count += 1
        product.save()

        response = dict()
        try:
            res = products_service.get_product_detail_dynamodb(product.id)
            response['product'] = ProductDetail(res).data
        except:
            response['product'] = ProductDetail(product).data

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=['put'])
    def pricing(self, request):
        """
        제품 최저/최고 가격
        ---
        json 형태의 파라미터 <br>
        data = [{ <br>
        'id': Integer, <br>
        'cnt': Integer, <br>
        'min': Interger, <br>
        'max': Interger <br>
        } <br>
        ... <br>
        ]
        """
        params = PricingForm(data=request.data)
        params.is_valid(raise_exception=True)

        for product in params.validated_data.get('data'):
            product_id = product.get('product_id')

            with transaction.atomic():
                info, created = ProductGoods.objects.get_or_create(product_id=product_id)
                if created:
                    info.goods_count = product.get('goods_count')
                    info.min_price = product.get('min_price')
                    info.max_price = product.get('max_price')
                    info.save()
                else:
                    info.goods_count = product.get('goods_count')
                    info.min_price = product.get('min_price')
                    info.max_price = product.get('max_price')
                    info.save()

                body = {"query": {'match': {'idProduct': product_id}}}
                sample = elasticsearch_reviews.search(body=body)
                size = sample.get('hits').get('total')
                res = elasticsearch_reviews.search(body=body, _size=size)
                hits = res.get('hits')

                data = []
                for item in hits.get('hits'):
                    body = {
                        "_op_type": 'update',
                        "_index": 'review_ko',
                        "_type": 'reviews',
                        "_id": item.get('_id'),
                        "doc": {
                            'goods_info': {
                                'goods_count': product.get('goods_count'),
                                'min_price': product.get('min_price'),
                                'max_price': product.get('max_price')
                            }
                        },
                        'doc_as_upsert': True
                    }
                    data.append(body)
                    # elasticsearch_reviews.update(_id=item.get('_id'), body=body)
                if data:
                    elasticsearch_reviews.bulk(data)

        return Response({}, status=status.HTTP_200_OK)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'products', ProductView, base_name='products')
