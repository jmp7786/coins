import random

from django.db.models import Avg
from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.routers import Route

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.utils import request_ads, local_now
from models.ingredients import Ingredient
from models.products import Product
from models.reviews import Review
from models.users import User, Wish
from services.brands import service as brands_service
from services.categories import service as categories_service
from services.products import service as products_service
from services.reviews import service as review_service
from services.stores import service as stores_service
from services.recommends import service as recommend_service
from services.ranking import service as ranking_service
from .forms.products import ProductsForm, ProductsMonthForm, WeeklyProductsForm
from .forms.reviews import ProductReivewsForm
from .responses.products import ProductDetailResponse, ProductsResponse, ProductIngredientsResponse, \
    MonthProductsResponse, WeeklyProductsResponse
from .responses.reviews import ProductReviewsResponse
from .responses.common import SuccessMessageResponse


class ProductView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': ProductsForm,
        'get_reviews': ProductReivewsForm,
        'get_month': ProductsMonthForm,
        'get_weekly': WeeklyProductsForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '제품 리스트 (검색)',
                'schema': {
                    'type': 'object',
                    'properties': ProductsResponse,
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

        'get_retrieve': {
            '200': {
                'description': '제품 상세 정보',
                'schema': {
                    'type': 'object',
                    'properties': ProductDetailResponse
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
        'get_reviews': {
            '200': {
                'description': '제품 리뷰 정보',
                'schema': {
                    'type': 'object',
                    'properties': ProductReviewsResponse,
                }
            },
        },
        'get_wish': {
            '200': {
                'description': '위시 가능 여부',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse,
                }
            },
        },
        'post_wish': {
            '200': {
                'description': '위시 추가',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse,
                }
            },
        },
        'delete_wish': {
            '200': {
                'description': '위시 삭제',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse,
                }
            },
        },

        'get_ingredients': {
            '200': {
                'description': '제품 성분 리스트',
                'schema': {
                    'type': 'object',
                    'properties': ProductIngredientsResponse,
                }
            },
        },

        'get_month': {
            '200': {
                'description': '이달의 제품 리스트',
                'schema': {
                    'type': 'object',
                    'properties': MonthProductsResponse,
                }
            },
        },
        'get_weekly': {
            '200': {
                'description': '명예의 전당 제품 리스트',
                'schema': {
                    'type': 'object',
                    'properties': WeeklyProductsResponse,
                }
            },
        },
    }

    def list(self, request):
        """
        제품 리스트 (통합 검색)
        """
        # 파라미터
        params = ProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        response = dict()
        results = products_service.get_list(**params.validated_data)
        response['products'] = results.get('list')
        if params.validated_data.get('cursor') is None:
            response['total_count'] = products_service.get_list(
                only_count=True,
                **params.validated_data
            )

            brands = brands_service.get_brands(**params.validated_data)
            response['brands'] = brands
            response['brands_count'] = len(brands)

            categories = categories_service.get_product_categories(**params.validated_data)
            response['categories'] = categories
            response['categories_count'] = len(categories)

            stores = stores_service.get_list(**params.validated_data)
            response['stores'] = stores
            response['stores_count'] = len(stores)

        response['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(ProductsResponse(response).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        제품 상세 정보
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        product = get_object_or_404(Product, id=pk)

        product.read_count += 1
        product.save()

        response = dict()

        ads_id = None
        try:
            response['product'] = products_service.get_product_detail_dynamodb(product.id)
            month_new = response['product'].get('month_new')
            if month_new:
                ads_id = month_new.get('id')
        except:
            response['product'] = products_service.get_product_detail(product)
            month_new = getattr(response['product'], 'month_new')
            if month_new:
                ads_id = month_new.id

        # ads server
        if ads_id:
            request_ads('GP0010', str(ads_id))

        if cuid > 0:
            user = User.objects.get(id=cuid)

            response['is_wish'] = user.wishes.filter(id=pk).exists()
            if (user._gender is None) or (user._skin_type is None):
                response['is_review_type'] = 'more'
                response['is_review_message'] = _("내정보에서 추가정보를 입력하셔야 작성이 가능합니다.")
            elif Review.objects.filter(user=user, product=product).exists():
                response['is_review_type'] = 'wrote'
                response['is_review_message'] = _("이미 리뷰를 작성한 제품입니다:(\n다른 제품에도 솔직평가 남겨주세요!")
                response['my_review'] = Review.objects.get(user=user, product=product)
            else:
                response['is_review_type'] = 'ok'
        else:
            response['is_wish'] = False
            response['is_review_type'] = "join"
            response['is_review_message'] = _("회원가입이 필요합니다.")

        qs = Review.objects.filter(
            product=pk, is_display=True, state='N', user__is_blinded=0
        )
        rating_avg = qs.aggregate(Avg('rating'))
        if isinstance(response['product'], dict):
            response['product']['rating_avg'] = round(float(rating_avg.get('rating__avg') or 0), 2)
            response['product']['review_count'] = qs.count()
        else:
            setattr(response['product'], 'rating_avg', round(float(rating_avg.get('rating__avg') or 0), 2))
            setattr(response['product'], 'review_count', qs.count())

        return Response(ProductDetailResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def reviews(self, request, pk=None):
        """
        제품 리뷰 정보
        """

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        params = ProductReivewsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')
        state = params.validated_data.get('state')

        review_service.setter(product_id=pk)

        results = review_service.get_list(**params.validated_data)
        res = dict()

        reviews = list(results['list'] or [])

        if cursor is None:
            res['total_count'] = review_service.get_list(only_count=True, **params.validated_data)

        # 정상 상태일때만 자기 자신의 리뷰를 리스트에서 제외시킨다.
        if state == 'normal':
            for review in reviews:
                if review.user_id == cuid:
                    reviews.remove(review)

        res['reviews'] = reviews

        if state != 'blinded' and not cursor:
            res['scoreboard'] = dict()

            blinded = review_service.get_list(only_count=True, state='blinded')
            res['scoreboard']['blinded'] = blinded

            res['scoreboard']['ratings'] = dict()
            res['scoreboard']['ratings']['point_1'] = 0
            res['scoreboard']['ratings']['point_2'] = 0
            res['scoreboard']['ratings']['point_3'] = 0
            res['scoreboard']['ratings']['point_4'] = 0
            res['scoreboard']['ratings']['point_5'] = 0
            rating_points = results.get('rating_points')

            if rating_points:
                for item in rating_points:
                    for k, v in item.items():
                        if k == 'rating':
                            key = 'point_%d' % v
                        if k == 'count':
                            val = v
                    res['scoreboard']['ratings'][key] = val

            my_review = review_service.get_my_review(cuid, pk, **params.validated_data)
            if my_review:
                res['my_review'] = my_review

        res['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            res['paging']['next'] = next_offset

        return Response(ProductReviewsResponse(res).data)

    @detail_route(methods=['get', 'post', 'delete'])
    def wish(self, request, pk=None):
        """
        위시 확인 / 추가 / 삭제
        ---
        - IDREGISTER:        (필수) 회원 항번 <br>
        """

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=cuid)
        product = get_object_or_404(Product, id=pk)

        response = dict()
        if request.method == 'GET':
            if Wish.objects.filter(user=user, product=product).exists():
                response['is_success'] = False
                response['message'] = _("이미 위시리스트에 있습니다.")
            else:
                response['is_success'] = True
                response['message'] = _("위시리스트에 추가할 수 있습니다.")

        elif request.method == 'POST':
            if Wish.objects.filter(user=user, product=product).exists():
                response['is_success'] = False
                response['message'] = _("이미 위시리스트에 있습니다.")
            else:
                try:
                    now = local_now().strftime('%Y%m%d%H%M%S')
                    Wish(user=user, product=product, create_date=now).save()
                    response['is_success'] = True
                    msg_arr = [
                        _("지름신 팍팍! 위시리스트 등록 완료"),
                        _("코덕으로 가는 지름길! 위시리스트 등록 완료~")
                    ]
                    response['message'] = random.choice(msg_arr)
                except:
                    response['is_success'] = False
                    response['message'] = _("추가에 실패하였습니다.")

        elif request.method == 'DELETE':
            qs = Wish.objects.filter(user=user, product=product)
            if qs.exists():
                qs.delete()
                response['is_success'] = True
                response['message'] = _("위시리스트가 삭제되었습니다.")
            else:
                response['is_success'] = False
                response['message'] = _("이미 삭제되었습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['get'])
    def ingredients(self, request, pk=None):
        """
        제품 성분 리스트
        """
        product = get_object_or_404(Product, id=pk)
        ingredients = Ingredient.objects.filter(
            productingredient__product=pk
        ).order_by(
            'productingredient__seq'
        )

        response = dict()
        response['product'] = product
        response['ingredients'] = ingredients

        return Response(
            ProductIngredientsResponse(response).data,
            status=status.HTTP_200_OK
        )

    @list_route(methods=['get'])
    def weekly(self, request):
        """
        명예의 전당 제품 리스트
        """
        params = WeeklyProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        response = dict()
        products = ranking_service.get_weekly_ranking_products(
            **params.validated_data
        )
        response['weekly_products'] = products.get('list')
        response['paging'] = dict()
        next_offset = products.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(
            WeeklyProductsResponse(response).data,
            status=status.HTTP_200_OK
        )

    def month(self, request, ym=None):
        """
        이달의 신제품
        ---
        - ym : yyyymm  (년도, 월)
        """
        params = ProductsMonthForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        d = datetime.strptime(ym, '%Y%m')

        response = dict()
        products = products_service.get_products_by_month(
            ym=d.strftime('%Y%m'),
            **params.validated_data
        )
        response['products'] = products.get('list')

        if not response['products']:
            d -= relativedelta(months=1)
            products = products_service.get_products_by_month(
                ym=d.strftime('%Y%m'),
                **params.validated_data
            )
            response['products'] = products.get('list')

        response['paging'] = dict()
        next_offset = products.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        if cursor is None:
            recommend_products = recommend_service.get_recommend_products()
            response['recommend_products'] = recommend_products
            for recommend in recommend_products:
                request_ads('GP0011', str(recommend.id))

        return Response(
            MonthProductsResponse(response).data,
            status=status.HTTP_200_OK
        )


router = routers.DefaultRouter(trailing_slash=False)
router.routes.append(
    Route(
        url=r'{prefix}/month/(?P<ym>[0-9]+)$',
        name='{basename}-month',
        mapping={
            'get': 'month',
        },
        initkwargs={}
    ),
)
router.register(r'products', ProductView, base_name='products')
