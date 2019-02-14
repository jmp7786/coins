from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from backends.api import exceptions
from backends.api.v2.forms.picks import UserPicksForm
from backends.api.v2.forms.products import UserProductsForm
from backends.api.v2.forms.reviews import UserReviewsForm
from backends.api.v2.forms.users import UserMetaInfoForm, UsersForm,\
    UsersFromRedisForm
from backends.api.v2.responses.picks import PickListResponse
from backends.api.v2.responses.products import UserWishesResponse
from backends.api.v2.responses.reviews import UserReviewsResponse
from libs.aws.utils import delete_image_by_s3, store_profile_image
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from models.pick_likes import PickLike
from models.reviews import Review
from models.users import User, Wish
from services.picks import service as pick_service
from services.reviews import service as review_service
from services.users import service as users_service
from services.wishes import service as wish_service
from libs.utils import iso8601, user_rank_initialization_time, \
    user_rank_last_week_initialized_time
from .responses.users import (
    UserProfileResponse, UserSimple, AccountResponse, UserResponse, UsersResponse,UsersV2Response
)


class UserView(viewsets.ViewSet):
    permission_classes_by_action = {
        'list': [CustomIsAuthenticated],
        'me': [CustomIsAuthenticated],
        'retrieve': [CustomIsAuthenticated],
        'update': [CustomIsAuthenticated],
        'reviews': [CustomIsAuthenticated],
        'wishes': [CustomIsAuthenticated],
        'picks': [CustomIsAuthenticated],
        'from_redis': [CustomIsAuthenticated],
    }

    parameter_classes = {
        'get_list': UsersForm,
        'put_me': UserMetaInfoForm,
        'get_reviews': UserReviewsForm,
        'put_update': UserMetaInfoForm,
        'get_picks': UserPicksForm,
        'get_wishes': UserProductsForm,
        'get_from_redis': UsersFromRedisForm
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '회원 리스트',
                'schema': {
                    'type': 'object',
                    'properties': UsersResponse,
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
        'get_me': {
            '200': {
                'description': '로그인 회원정보',
                'schema': {
                    'type': 'object',
                    'properties': AccountResponse,
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
        'get_from_redis': {
            '200': {
                'description': '레디스에서 받아온 회원 리스트',
                'schema': {
                    'type': 'object',
                    'properties': UsersV2Response,
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
        'get_retrieve': {
            '200': {
                'description': '회원 정보',
                'schema': {
                    'type': 'object',
                    'properties': UserResponse,
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
        'put_update': {
            '200': {
                'description': '회원 정보 수정 성공',
                'schema': {
                    'type': 'object',
                    'properties': UserResponse,
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
        'get_reviews': {
            '200': {
                'schema': {
                    'type': 'object',
                    'properties': UserReviewsResponse
                }
            }
        },
        'get_picks': {
            '200': {
                'schema': {
                    'type': 'object',
                    'properties': PickListResponse
                }
            }
        }
    }

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        회원 리스트 (통합 검색, top reviewer)
        """
        params = UsersForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')
        order = params.validated_data.get('order')

        response = dict()
        users = users_service.get_list(**params.validated_data)
        response['users'] = users.get('list')
        if cursor is None and order != 'top_ranking':
            response['users_count'] = users_service.get_list(
                only_count=True,
                **params.validated_data
            )

        next_offset = users.get('next_offset')
        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(UsersResponse(response).data, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def from_redis(self, request):
        """
        회원 리스트 (ranking)
        """
        params = UsersFromRedisForm(data=request.GET)
        params.is_valid(raise_exception=True)
    
        cursor = params.validated_data.get('cursor')
        period = params.validated_data.get('period')
        response = dict()
        users = users_service.get_list_from_redis(**params.validated_data)
    
        response['users'] = users.get('list')
        if cursor is None :
            response['users_count'] = users_service\
                .get_list_from_redis(**params.validated_data, only_count=True)
    
    
        if period == 'this_week':
            response['end_time'] = iso8601(user_rank_initialization_time())
        elif period == 'last_week':
            initializated_date = user_rank_last_week_initialized_time(int(request.GET.get('tmp')))
            response['start_time'] = iso8601(initializated_date['start_time'])
            response['end_time'] = iso8601(initializated_date['end_time'])

         
        next_offset = users.get('next_offset')
        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset
    
        return Response(UsersV2Response(response).data,
                        status=status.HTTP_200_OK)
    
    @detail_route(methods=['get', 'put'])
    def profile(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        response = dict()

        if request.method == 'GET':
            response = UserProfileResponse(user)
            return Response(response.data, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            name = request.POST.get('name')
            contact = request.POST.get('contact')
            zipcode = request.POST.get('zip')
            address = request.POST.get('address')
            address_more = request.POST.get('address_more')

            user.name = name
            user.tel = contact
            user.zipcode = zipcode
            user.address = address
            user.address_more = address_more
            user.save()

        return Response(response, status=status.HTTP_200_OK)

    @list_route(methods=['get', 'put'])
    def me(self, request, *args, **kwargs):
        """
        로그인 회원 정보
        ---
        - gender:      (필수) 성별 (m: 남자, f: 여자 ) <br>
        - skin_type:       (필수) 피부타입 (dry : 건성, oily: 지성, normal : 중성, mix : 복합성, sensitive : 민감성) <br>
        - birth_year:    (필수) 출생년도 <br>

        - file:  이미지 파일 전송
        """
        # assumes the user is authenticated, handle this according your needs

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        try:
            user = User.objects.get(id=cuid)
        except User.DoesNotExist:
            raise exceptions.NoUser

        response = dict()

        if request.method == 'GET':
            setattr(user, 'wish_count', Wish.objects.filter(user=user, product__is_display=True).count())
            setattr(user, 'pick_count', PickLike.objects.filter(user=user, pick__is_display=True).count())
            setattr(user, 'review_count', Review.objects.filter(user=user, is_display=True).count())
            response['user'] = user

        elif request.method == 'PUT':
            params = UserMetaInfoForm(data=request.data)
            params.is_valid(raise_exception=True)

            user._gender = params.validated_data.get('gender')
            user._skin_type = params.validated_data.get('skin_type')
            user.birth_year = params.validated_data.get('birth_year')

            file_obj = request.FILES.get('file')

            if file_obj:
                if user.file_name_save:
                    delete_image_by_s3(
                        file_dir=user.file_dir,
                        file_name=user.file_name_save
                    )

                file_info = store_profile_image(file_obj, user.id)
                if file_info:
                    user.file_name_orig = file_info.get('file_org_name')
                    user.file_name_save = file_info.get('file_save_name')
                    user.file_dir = file_info.get('file_dir')
                    user.file_size = file_info.get('file_size')
                    user.file_type = file_info.get('file_type')
                    user.save()

            user.save()

            response['user'] = user
            response['is_success'] = True
            response['message'] = _("프로필 편집이 완료되었습니다.")

        return Response(UserResponse(response).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        회원 정보
        """
        try:
            user = User.objects.get(id=pk, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser

        response = dict()
        setattr(user, 'wish_count', Wish.objects.filter(user=user, product__is_display=True).count())
        setattr(user, 'pick_count', PickLike.objects.filter(user=user, pick__is_display=True).count())

        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        if user.id == cuid:
            setattr(user, 'review_count', Review.objects.filter(user=user, is_display=True).count())

        response['user'] = user

        return Response(UserResponse(response).data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """
        회원 정보 수정
        ---
        - gender:      (필수) 성별 (m: 남자, f: 여자 ) <br>
        - skin_type:       (필수) 피부타입 (dry : 건성, oily: 지성, normal : 중성, mix : 복합성, sensitive : 민감성) <br>
        - birth_year:    (필수) 출생년도 <br>

        - file:  이미지 파일 전송
        """
        try:
            user = User.objects.get(id=pk, is_active=True)
        except User.DoesNotExist:
            raise exceptions.NoUser

        params = UserMetaInfoForm(data=request.data)
        params.is_valid(raise_exception=True)

        file_obj = request.FILES.get('file')

        user._gender = params.validated_data.get('gender')
        user._skin_type = params.validated_data.get('skin_type')
        user.birth_year = params.validated_data.get('birth_year')

        if file_obj:
            if user.file_name_save:
                delete_image_by_s3(
                    file_dir=user.file_dir,
                    file_name=user.file_name_save
                )

            file_info = store_profile_image(file_obj, user.id)
            if file_info:
                user.file_name_orig = file_info.get('file_org_name')
                user.file_name_save = file_info.get('file_save_name')
                user.file_dir = file_info.get('file_dir')
                user.file_size = file_info.get('file_size')
                user.file_type = file_info.get('file_type')
                user.save()

        user.save()

        response = dict()

        response['user'] = UserSimple(user).data
        response['is_success'] = True
        response['message'] = _("프로필 편집이 완료되었습니다.")

        return Response(response, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def reviews(self, request, pk=None):
        """
        회원 프로필에서 리뷰 리스트
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)
        user = get_object_or_404(User, id=pk)

        params = UserReviewsForm(data=request.GET)
        params.is_valid(raise_exception=True)
        cursor = params.validated_data.get('cursor')

        response = dict()
        review_service.setter(user_id=pk)
        results = review_service.get_list(
            request_user_id=cuid,
            user_id=user.id,
            **params.validated_data)

        reviews = list(results['list'] or [])
        response['reviews'] = reviews

        if cursor is None:
            response['total_count'] = review_service.get_list(
                only_count=True,
                request_user_id=cuid,
                user_id=user.id,
                **params.validated_data
            )

        like_count = results.get('like_count')
        if like_count is not None:
            response['like_count'] = results.get('like_count')

        response['paging'] = dict()
        next_offset = results.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(UserReviewsResponse(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def wishes(self, request, pk=None):
        """
        회원 프로필에서 위시 리스트
        """

        get_object_or_404(User, id=pk)

        params = UserProductsForm(data=request.GET)
        params.is_valid(raise_exception=True)

        cursor = params.validated_data.get('cursor')

        response = dict()
        response['products'], next_offset = wish_service.get_list(pk, **params.validated_data)
        if cursor is None:
            response['total_count'] = wish_service.get_list(pk, only_count=True, **params.validated_data)
        response['paging'] = dict()
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(UserWishesResponse(response).data)

    @detail_route(methods=['get'])
    def picks(self, request, pk=None):
        """
        회원 프로필에서 캐스트(픽) 리스트
        ---
        - 마지막 항번값으로 페이징 처리를 합니다. 첫 페이지 호출할때 last_key 값을 넘기지 않아야 합니다.
        - 회원 프로필에서는 캐스트(픽) 카테고리 정보에 'is_new' 정보는 항상 없습니다.
        """
        response = {}

        get_object_or_404(User, id=pk)

        params = UserPicksForm(data=request.GET)
        params.is_valid(raise_exception=True)
        cursor = params.validated_data.get('cursor')

        if cursor is None:
            response['categories'] = pick_service.get_user_pick_categories(user_id=pk)

        picks, total_count, next_offset = pick_service.get_user_picks(user_id=pk, **params.validated_data)
        response['picks'] = picks
        response['paging'] = dict()
        if total_count:
            response['total_count'] = total_count
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(PickListResponse(response).data)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', UserView, base_name='users')
