from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from backends.common.exceptions import NotFoundException
from backends.common.exceptions import FailedPreconditionException,ConflictException,ForbiddenException
from libs.aws.dynamodb import aws_dynamodb_etc_list, aws_dynamodb_event_participants, aws_dynamodb_events
from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_raise_404, get_object_or_raise_404
from libs.utils import get_image_ratio, get_client_ip, local_now
from models.events import Event, EventParticipants, EventComment
from models.users import User
from services.events import service as event_service
from services.event_comments import service as event_comment_service
from .forms.events import EventListForm, EventCommentListForm, EventCommentForm
from .responses.events import EventsResponse, EventRespose, EventCommentsResonse, EventCommentJoin
from .responses.common import SuccessMessageResponse


class EventView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': EventListForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '이벤트 리스트',
                'schema': {
                    'type': 'object',
                    'properties': EventsResponse,
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
                'description': '이벤트 상세',
                'schema': {
                    'type': 'object',
                    'properties': EventRespose,
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
        이벤트 리스트
        """
        params = EventListForm(data=request.GET)
        params.is_valid(raise_exception=True)

        term = params.validated_data.get('term')

        response = dict()
        response['paging'] = dict()
        if term == 'ongoing':
            try:
                events = event_service.get_ongoing_events_by_dynamodb(**params.validated_data)
                response['events'] = events.get('list')
                response['totalArticleCount'] = events.get('total_row_count')
            except:
                events = event_service.get_list(**params.validated_data)
                response['events'] = events.get('list')
                response['totalArticleCount'] = events.get('total_row_count')
        else:
            events = event_service.get_list(**params.validated_data)
            response['events'] = events.get('list')
            response['totalArticleCount'] = events.get('total_row_count')

        next_offset = events.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(EventsResponse(response).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        이벤트 조회
        """
        event = get_object_or_raise_404(Event, id=pk)

        response = dict()
        try:
            response['event'] = event_service.get_event_by_dynamodb(event_id=pk)
        except:
            setattr(event, 'brand_name', event.brand.name)
            setattr(event, 'comments_count', event.users.count())
            setattr(event, 'ratio', get_image_ratio(path=event.event_image, is_url=True))
            response['event'] = event
        try:
            response['checked'] = self.check(request, pk=pk).data
        except (NotFoundException,):
            response['checked'] = {'is_success': False, 'message': '비회원'}

        event.hits_count += 1
        event.save()

        return Response(EventRespose(response).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def join(self, request, pk=None):
        """
        이벤트 참여추가
        ---
        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        event = get_object_or_raise_404(Event, id=pk)
        user = get_object_or_raise_404(User, id=cuid)

        if EventParticipants.objects.filter(user=user, event=event).exists():
            raise ConflictException(
                _("이미 이벤트에 참여하셨습니다.")
            )

        if user.review_count < event._condition:
            raise FailedPreconditionException(
                _("{} 개 이상의 리뷰를 작성한 회원만 참여할 수 있는 이벤트 입니다.\n"
                  "회원님께서는 {} 개의 리뷰를 더 작성하셔야 합니다.".format(
                    event._condition, event._condition - user.review_count))
            )

        response = dict()
        user_ip = get_client_ip(request)
        now = local_now().strftime('%Y%m%d%H%M%S')

        try:
            with transaction.atomic():
                # RDS
                EventComment(
                    event=event,
                    user=user,
                    comment="참가신청 완료",
                    ip_address=user_ip,
                    create_date=now
                ).save()

                EventParticipants(
                    user=user,
                    event=event,
                    create_date=now
                ).save()

                _count = event.users.count() + 1

                # dynamo DB
                aws_dynamodb_etc_list.update_events_comment(
                    seq=event.seq,
                    comment_count=_count
                )

                aws_dynamodb_event_participants.update_event(
                    event_id=event.id,
                    user_id=user.id,
                    created_at=now
                )

                aws_dynamodb_events.update_event_comments_count(
                    event_id=event.id,
                    _count=_count
                )

            response['is_success'] = True
            response['message'] = _("이벤트에 참여되었습니다.")
        except:
            response['is_success'] = False
            response['message'] = _("등록에 실패하였습니다.")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_201_CREATED
        )

    @detail_route(methods=['post'])
    def check(self, request, pk=None):
        """
        이벤트 참여 여부 확인
        ---
        - is_success (True : 참여, False : 불참여)
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        event = get_object_or_raise_404(Event, id=pk)
        user = get_object_or_raise_404(User, id=cuid)

        response = dict()

        try:
            res = aws_dynamodb_event_participants.get_event(
                event_id=event.id,
                user_id=user.id
            )
            if res:
                response['is_success'] = True
                response['message'] = _("참여완료")
            else:
                response['is_success'] = False
                response['message'] = _("참여가능")
        except:
            is_existed = EventParticipants.objects.filter(
                event=event,
                user=user
            ).exists()
            if is_existed:
                response['is_success'] = True
                response['message'] = _("참여완료")
            else:
                response['is_success'] = False
                response['message'] = _("참여가능")

        return Response(
            SuccessMessageResponse(response).data,
            status=status.HTTP_200_OK
        )


class EventCommentView(viewsets.ViewSet):
    permission_classes = (CustomIsAuthenticated,)

    parameter_classes = {
        'get_list': EventCommentListForm,
        'post_create': EventCommentForm,
    }

    response_docs = {
        'get_list': {
            '200': {
                'description': '이벤트 댓글 리스트',
                'schema': {
                    'type': 'object',
                    'properties': EventsResponse,
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
                'description': '이벤트 댓글 등록',
                'schema': {
                    'type': 'object',
                    'properties': EventCommentJoin,
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

    def list(self, request, event_id=None):
        """
        이벤트 댓글 리스트
        """

        params = EventCommentListForm(data=request.GET)
        params.is_valid(raise_exception=True)

        comments = event_comment_service.get_list(
            event_id=event_id,
            **params.validated_data
        )

        response = dict()
        response['comments'] = comments.get('list')
        response['count'] = comments.get('count')
        response['paging'] = dict()
        next_offset = comments.get('next_offset')
        if next_offset:
            response['paging']['next'] = next_offset

        return Response(
            EventCommentsResonse(response).data,
            status=status.HTTP_200_OK
        )

    def create(self, request, event_id=None):
        """
        이벤트 댓글 추가
        ---
        <br>
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>
        """
        cuid = int(request.META.get('HTTP_IDREGISTER') or 0)

        params = EventCommentForm(data=request.data)
        params.is_valid(raise_exception=True)

        comment = params.validated_data.get('comment')

        event = get_object_or_raise_404(Event, id=event_id)
        user = get_object_or_raise_404(User, id=cuid)

        if EventComment.objects.filter(user=user, event=event).exists():
            raise ConflictException(
                _("이미 이벤트에 참여하셨습니다.")
            )

        if user.review_count < event._condition:
            raise FailedPreconditionException(
                _("{} 개 이상의 리뷰를 작성한 회원만 참여할 수 있는 이벤트 입니다.\n"
                  "회원님께서는 {} 개의 리뷰를 더 작성하셔야 합니다.".format(
                    event._condition, event._condition - user.review_count))
            )

        response = dict()
        user_ip = get_client_ip(request)
        now = local_now().strftime('%Y%m%d%H%M%S')

        try:
            with transaction.atomic():
                # RDS
                EventComment(
                    event=event,
                    user=user,
                    comment=comment,
                    ip_address=user_ip,
                    create_date=now
                ).save()

                _count = event.users.count() + 1

                # dynamo DB
                aws_dynamodb_etc_list.update_events_comment(
                    seq=event.seq,
                    comment_count=_count
                )

                aws_dynamodb_event_participants.update_event(
                    event_id=event.id,
                    user_id=user.id,
                    created_at=now
                )

                aws_dynamodb_events.update_event_comments_count(
                    event_id=event.id,
                    _count=_count
                )

            response['is_success'] = True
            response['message'] = _(
                "당첨을 기다리며, 지금 등록되어 있는 \n"
                "연락처와 주소를 한 번 더 확인해주세요!"
            )
            if user.zipcode:
                response['user_address'] = _(
                    "연락처 : {}\n"
                    "주소 : ({}) {} {}".format(
                        user.tel, user.zipcode, user.address, user.address_more)
                )
            else:
                response['user_address'] = _(
                    "연락처 : {}\n"
                    "주소 : {} {}".format(
                        user.tel, user.address, user.address_more)
                )
        except:
            response['is_success'] = False
            response['message'] = _("등록에 실패하였습니다.")

        return Response(EventCommentJoin(response).data, status=status.HTTP_201_CREATED)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'events', EventView, base_name='events')
router.register(r'events/(?P<event_id>[0-9]+)/comments', EventCommentView, base_name='event_comments')
