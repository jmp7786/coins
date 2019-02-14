from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from rest_framework import routers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from libs.oauth2.permissions import CustomIsAuthenticated
from libs.shortcuts import get_object_or_404
from libs.utils import utc_now
from models.messages import MessageBox, MessageCheck
from models.users import User
from .responses.messages import MessageSerializer, MessageReadSerializer, MessageTargetSerializer


class MessagePagination(LimitOffsetPagination):
    default_limit = 10


class MessageView(viewsets.mixins.ListModelMixin,
                  viewsets.mixins.CreateModelMixin,
                  viewsets.mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """
    알림 메세지
    """
    response_docs = {
        'get_list': {
            '200': {
                'description': '알림 메세지 리스트',
                'schema': {
                    'type': 'array',
                    'items': {
                        'properties': MessageSerializer,
                    },
                }
            },

        },
        'post_create': {
            '201': {
                'description': '알림 메세지 등록',
                'schema': {
                    'type': 'object',
                    'properties': MessageSerializer,
                }
            },

        },
        'put_update': {
            '201': {
                'description': '알림 메세지 수정',
                'schema': {
                    'type': 'object',
                    'properties': MessageSerializer,
                }
            },

        },
        'post_target': {
            '201': {
                'description': '알림 메세지 랜딩 타겟',
                'schema': {
                    'type': 'object',
                    'properties': MessageTargetSerializer,
                }
            },

        },
    }
    permission_classes = (CustomIsAuthenticated,)
    queryset = MessageBox.objects.active().select_related('user', 'category')
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_IDREGISTER')

        user = get_object_or_404(User, id=user_id)
        joined_at = user.date_joined - timedelta(hours=9)

        query_set = super(MessageView, self).get_queryset()
        query_set = query_set.select_related(
            'category'
        ).filter(
            created_at__range=(joined_at, utc_now())
        ).filter(
            Q(user_id=user_id) | Q(user_id__isnull=True, group_id__isnull=True)
        ).exclude(messagecheck__in=MessageCheck.objects.filter(user=user, deleted_at__isnull=False)).distinct()

        return query_set

    def list(self, request, *args, **kwargs):
        """
        알림 메세지 리스트
        ---
        <b>헤더</b>
        - IDREGISTER:        (필수) 회원 항번 <br>

        """
        user_id = self.request.META.get('HTTP_IDREGISTER')
        user = get_object_or_404(User, id=user_id)

        response = super(MessageView, self).list(request, *args, **kwargs)
        query_set = self.get_queryset()
        latest_checked_at = utc_now() - timedelta(days=14)
        query_set = query_set.exclude(
            id__in=[checked.message_id for checked in
                    MessageCheck.objects.filter(user=user, checked_at__gte=latest_checked_at)]
        )

        MessageCheck.objects.bulk_create(
            [MessageCheck(user=user, message=message) for message in query_set]
        )

        return response

    def perform_destroy(self, instance):
        user_id = self.request.META.get('HTTP_IDREGISTER')
        deleted_at = utc_now()
        MessageCheck.objects.filter(
            user_id=user_id,
            message=instance
        ).update(deleted_at=deleted_at)

        if instance.user:
            instance.is_active = False
            instance.save()

    @list_route(methods=['delete'])
    def all(self, request):
        """
        알림함 메세지 전체 삭제
        ---
        """
        user_id = self.request.META.get('HTTP_IDREGISTER')

        query_set = self.get_queryset()

        deleted_at = utc_now()
        MessageCheck.objects.filter(
            user_id=user_id,
            message__in=[message for message in query_set]
        ).update(deleted_at=deleted_at)
        query_set.filter(user__isnull=False).update(is_active=False)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['delete'])
    def read(self, request):
        """
        알림함 읽은 메세지 삭제
        ---
        """
        user_id = self.request.META.get('HTTP_IDREGISTER')

        query_set = self.get_queryset()
        query_set = query_set.filter(messagecheck__read_at__isnull=False)

        deleted_at = utc_now()
        MessageCheck.objects.filter(
            user_id=user_id,
            message__in=[message for message in query_set]
        ).update(deleted_at=deleted_at)

        query_set.filter(user__isnull=False).update(is_active=False)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'])
    def count(self, request):
        """
        알림함 뱃지 카운트
        ---
        """
        # 14일 지난 메세지 삭제 처리
        last_created_at = utc_now() - timedelta(days=14)
        user_id = self.request.META.get('HTTP_IDREGISTER')
        if user_id is None or user_id == '0':
            return Response({'count': 0}, status=status.HTTP_200_OK)
        MessageBox.objects.filter(
            Q(user_id=user_id) | Q(user_id__isnull=True, group_id__isnull=True)
        ).filter(
            updated_at__lt=last_created_at, is_active=True
        ).update(is_active=False)

        user = get_object_or_404(User, id=user_id)
        joined_at = user.date_joined - timedelta(hours=9)

        query_set = MessageBox.objects.filter(
            Q(user_id=user_id) | Q(user_id__isnull=True, group_id__isnull=True)
        ).filter(
            created_at__range=(joined_at, utc_now()), is_active=True
        ).distinct()
        count = query_set.exclude(messagecheck__user_id=user_id).count()
        return Response({'count': count}, status=status.HTTP_200_OK)

    @transaction.atomic
    @detail_route(methods=['put'])
    def check(self, request, pk=None):
        """
        알림함 메세지 체크
        ---
        """
        user_id = self.request.META.get('HTTP_IDREGISTER')
        user = get_object_or_404(User, id=user_id)
        message = get_object_or_404(MessageBox, id=pk)

        obj, created = MessageCheck.objects.get_or_create(user=user, message=message)
        obj.read_at = utc_now()
        obj.save()

        return Response(MessageReadSerializer(obj).data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def target(self, request, pk=None):
        """
        메세지 랜딩 타겟
        ---
        """
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        request.data['message'] = int(pk)
        serializer = MessageTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'messages', MessageView, base_name='messages')
