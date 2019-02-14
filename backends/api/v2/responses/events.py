from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .common import SuccessMessageResponse
from .users import UserBasic
from .paging import Paging
from .products import ProductSimpleWithBrand


class EventSimple(serializers.Serializer):
    event_id = serializers.IntegerField(source='id')
    title = serializers.CharField()
    condition = serializers.CharField()
    product = ProductSimpleWithBrand(required=True)

class EventBasic(serializers.Serializer):
    event_id = serializers.IntegerField(
        source='id',
        help_text=_("이벤트 항번")
    )
    title = serializers.CharField(
        help_text=_("이벤트 명")
    )

    brand_name = serializers.CharField(
        help_text=_("브랜드 이름")
    )

    event_image = serializers.URLField(
        help_text=_("이벤트 이미지")
    )

    event_image_720 = serializers.URLField(
        required=False,
        help_text=_("이벤트 이미지")
    )
    ratio = serializers.FloatField(
        help_text=_("이미지 비율")
    )

    comments_count = serializers.IntegerField(
        help_text=_("댓글 수 (참여 숫자)")
    )

    started_at = serializers.DateTimeField(
        help_text=_("이벤트 시작 시점")
    )

    ended_at = serializers.DateTimeField(
        help_text=_("이벤트 종료 시점")
    )





class EventDetail(EventBasic):
    requirement_count = serializers.IntegerField(
        source='_condition',
        help_text=_("참여가능한 리뷰 작성 수")
    )

    contents = serializers.CharField(
        help_text=_("이벤트 본문")
    )

    link_type = serializers.IntegerField(
        help_text=_("링크 유형")
    )
    link_target = serializers.CharField(
        help_text=_("링크 코드")
    )


class User(serializers.Serializer):
    user_id = serializers.IntegerField(
        source='id'
    )
    nickname = serializers.CharField(
        help_text=_("닉네임")
    )
    profile_image = serializers.URLField(
        help_text=_("회원 프로필 이미지")
    )


class EventComment(serializers.Serializer):
    user = UserBasic(
        help_text=_("회원 정보")
    )
    comment_id = serializers.IntegerField(
        help_text=_("코멘트 항번")
    )
    comment = serializers.CharField(
        help_text=_("댓글")
    )
    created_at = serializers.DateTimeField(
        help_text=_("작성 일시")
    )


class HomeEventsResponse(serializers.Serializer):
    total_count = serializers.IntegerField()
    events = EventSimple(many=True)


class EventsResponse(serializers.Serializer):
    events = EventBasic(
        many=True,
        help_text=_("이벤트 리스트")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class EventRespose(serializers.Serializer):
    event = EventDetail(
        help_text=_("이벤트 정보")
    )
    checked = SuccessMessageResponse(
        help_text=_("이벤트 참여 가능 여부")
    )


class EventCommentsResonse(serializers.Serializer):
    comments = EventComment(
        many=True,
        help_text=_("댓글 리스트")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )

    count = serializers.IntegerField(
        help_text=_("댓글 양")
    )


class EventCommentJoin(SuccessMessageResponse):
    user_address = serializers.CharField(
        required=False,
        help_text=_("회원 주소")
    )
