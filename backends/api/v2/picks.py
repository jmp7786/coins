from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import mixins
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.routers import Route, DefaultRouter
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError
from django.http.response import Http404
from backends.api.v2.responses.common import SuccessMessageResponse
from backends.common.exceptions import InvalidParameterException
from libs.aws.dynamodb import aws_dynamodb_pick
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.utils import request_ads, get_client_ip, local_now, iso8601
from models.pick_comments import PickComment
from models.pick_likes import PickLike
from models.picks import Pick
from models.users import User
from services.pick_comments import service as pick_comment_service
from services.picks import service as picks_service
from services.pick_banners import service as pick_banner_service
from services.pick_products import service as pick_product_service
from .forms.picks import PickCommentsForm, PickCommentForm, PicksForm, PickProductsForm

from .responses.picks import PickBannerResponse, PickProductResponse, PickLikeSerializer, PickIntegratedResponse, PickSerializer,PickListResponse, PickCommentsResponse
from backends.common import exceptions as glow_exceptions

class PickView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': PicksForm,
    }
    response_docs = {
        'get_list': {
            '200': {
                'description': '캐스트(픽) 리스트',
                'schema': {
                    'type': 'object',
                    'properties': PickListResponse,
                }
            },
            '400': {
                'description': 'Invalid Parameter',
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

    queryset = Pick.objects.all().select_related(
        'brand', 'editor', 'category'
    ).prefetch_related('pickproducts_set', 'pickcomment_set')
    serializer_class = PickSerializer
    pagination_class = None

    def list(self, request):
        """
        픽 (캐스트) 리스트
        """

        params = PicksForm(data=request.GET)
        params.is_valid(raise_exception=True)

        results = picks_service.get_list(**params.validated_data)

        # for requesting ads
        pick_ids = ",".join(str(pick.pick_id) for pick in results['picks'])
        request_ads('GP0007', pick_ids)

        results['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            results['paging']['next'] = next_offset

        return Response(PickListResponse(results).data)

    def retrieve(self, request, pk=None):
        """
        픽 (캐스트) 조회
        """
        response = {}
        response['pick'] = super().retrieve(request, pk=pk).data
        response['products'] =  pick_product_service.get_list(pick_id=pk,**{'cursor': None, 'limit': 20})\
            .get('list')

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        response['like'] = len(PickLike.objects.filter(user=cuid, pick=pk)) > 0

        response['banners'] = pick_banner_service.get_list(pick_id=pk).get('list')
        
        picks_service.increase_hits_count(pick_id=pk)
        
        return Response(PickIntegratedResponse(response).data, status=status.HTTP_200_OK)


class PickCommentView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': PickCommentsForm,
        'post_create': PickCommentForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '픽 (캐스트) 댓글 리스트',
                'schema': {
                    'type': 'object',
                    'properties': PickCommentsResponse,
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

        'post_create': {
            '200': {
                'description': '댓글 추가',
                'schema': {
                    'type': 'object',
                    'properties': SuccessMessageResponse,
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
    }

    def list(self, request, pick_id=None):
        """
        픽 (캐스트) 댓글 리스트
        """
        params = PickCommentsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        comments = pick_comment_service.get_list(
            pick_id=pick_id,
            **params.validated_data
        )

        response = dict()
        response['comments'] = comments.get('list')
        if cursor is None:
            response['comments_count'] = pick_comment_service.get_list(
                only_count=True,
                pick_id=pick_id,
                **params.validated_data
            )

        response['paging'] = dict()
        next_offset = comments.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(PickCommentsResponse(response).data, status=status.HTTP_200_OK)

    def create(self, request, pick_id=None):
        """
        픽 (캐스트) 댓글 추가
        ---
        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=cuid)
        pick = get_object_or_404(Pick, pick_id=pick_id)

        params = PickCommentForm(data=request.data)
        params.is_valid(raise_exception=True)

        if not (user.gender and user.skin_type and user.birth_year):
            raise InvalidParameterException(
                _("프로필 편집에서 추가정보를 입력하셔야 참여가 가능합니다.")
            )

        response = dict()
        try:
            with transaction.atomic():
                PickComment(
                    pick=pick,
                    user=user,
                    comment=params.validated_data.get('comment'),
                    ip_address=get_client_ip(request),
                    create_date=local_now().strftime('%Y%m%d%H%M%S')
                ).save()

                # 픽상세 뷰용 업데이트
                aws_dynamodb_pick.update_comment_count(
                    pick_id=pick_id,
                    comment_count=PickComment.objects.filter(pick=pick_id, is_display=True).count() + 1
                )
            response['is_success'] = True
            response['message'] = _("댓글 등록 완료!")
        except:
            response['is_success'] = False
            response['message'] = _("등록에 실패하였습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, pick_id=None, pk=None):
        """
        픽 (캐스트) 댓글 삭제
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        pick_comment_service.remove_comment(pk, cuid)

        response = dict()
        response['is_success'] = False
        response['message'] = _("삭제되었습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_202_ACCEPTED
        )


class PickBannerView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    def list(self, request, pick_id):

        """
        픽 배너 리스트
        """

        banners = pick_banner_service.get_list(
            pick_id=pick_id,
        )
        response = dict()
        response['banners'] = banners.get('list')

        return Response(PickBannerResponse(response).data, status=status.HTTP_200_OK)


class PickProductView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': PickProductsForm
    }

    def list(self, request, pick_id):
        """ 픽 제품 조회"""
        params = PickCommentsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        products = pick_product_service.get_list(
            pick_id=pick_id,
            **params.validated_data
        )

        response = dict()
        response['products'] = products.get('list')
        if cursor is None:
            response['products_count'] = pick_product_service.get_list(
                only_count=True,
                pick_id=pick_id,
                **params.validated_data
            )
        response['paging'] = dict()
        next_offset = products.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(PickProductResponse(response).data, status=status.HTTP_200_OK)



class PickLikeView(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    """
        픽 좋아요 조회 추가 삭제
        ---
        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
    """
    permission_classes = (CustomIsAuthenticated,)
    queryset = PickLike.objects
    serializer_class = PickLikeSerializer
    lookup_field = 'pick_id'
    response_docs = {
        'get_list': {
            '200': {
                'description': '픽 위시 카운트',
                'schema': {
                    'type': 'object',
                    'properties': PickLikeSerializer,
                }
            },
        },
        'get_retrieve': {
            '200': {
                'description': '픽 위시여부 체크',
                'schema': {
                    'type': 'object',
                    'properties': PickLikeSerializer,
                }
            },
        },
    }

    def retrieve(self, request, pick_id):
        """픽 좋아요 조회"""
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        self.queryset = self.queryset.filter(user=cuid, pick=pick_id)
        try:
            response =super().retrieve(request)
        except Http404 as e:
            response = Response({'is_success':False,'message':_("좋아요가 없습니다.")},status.HTTP_404_NOT_FOUND)
        return response

    def create(self, request, pick_id):
        """픽 좋아요 등록"""
        response = {}

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        data = dict(user=cuid, create_date=local_now().strftime('%Y%m%d%H%M%S'), pick=pick_id)
        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if 'non_field_errors' in e.detail:
                return Response({'is_success':False,'message':_("좋아요가 이미 있습니다.")},status=status.HTTP_409_CONFLICT)
            else:
                raise glow_exceptions.ServiceUnavailableException
        except Exception:
            raise glow_exceptions.ServiceUnavailableException


        try:
            with transaction.atomic():

                self.perform_create(serializer)
                aws_dynamodb_pick.update_recommend_count(
                    pick_id=pick_id,
                    recommend_count=self.queryset.filter(pick=pick_id).count()+1
                )
            response['is_success'] = True
            response['message'] = _("좋아요 등록 완료!")
        except Exception:
            raise glow_exceptions.ServiceUnavailableException

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, pick_id):
        """픽 좋아요 삭제"""
        response = {}

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        self.queryset = self.queryset.filter(user=cuid, pick=pick_id)

        try:
            instance = self.get_object()
        except Http404 as e:
            pass
            # response['is_success'] = False
            # response['message'] = "좋아요가 없습니다."
            # return Response(response, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                self.perform_destroy(instance)
                aws_dynamodb_pick.update_recommend_count(
                    pick_id=pick_id,
                    recommend_count=self.queryset.filter(pick=pick_id).count() - 1
                )
            response['is_success'] = True
            # response['message'] = _("좋아요 삭제 완료!")
            response['message'] = _("좋아요 삭제 완료!")
            status_code = status.HTTP_202_ACCEPTED
        except Exception as e:
            response['is_success'] = False
            response['message'] = _("좋아요 삭제 실패.")
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(response, status = status_code)









router = routers.DefaultRouter(trailing_slash=False)
router.register(r'picks', PickView, base_name='picks')
router.register(r'picks/(?P<pick_id>[0-9]+)/comments', PickCommentView, base_name='pick_comments')
router.register(r'picks/(?P<pick_id>[0-9]+)/banners', PickBannerView, base_name='pick_banners')
router.register(r'picks/(?P<pick_id>[0-9]+)/products', PickProductView, base_name='pick_products')


class LikeRouter(DefaultRouter):
    routes = [
        Route(
            url=r'^picks/{lookup}/{prefix}$',
            mapping={'get': 'retrieve',
                     'post': 'create',
                     'delete': 'destroy',
                     },
            name='{basename}-detail',
            initkwargs={}
        )
    ]


like_router = LikeRouter(trailing_slash=False)
like_router.register('like', PickLikeView, base_name='pick_likes')
router.urls.extend(like_router.urls)