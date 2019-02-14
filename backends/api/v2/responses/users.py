from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.api.v2.responses.common import SuccessMessageResponse
from backends.api.v2.responses.paging import Paging
from models.users import User


class UserProfileResponse(serializers.Serializer):
    user_id = serializers.IntegerField(source='id', required=False)
    name = serializers.CharField(max_length=45)
    contact = serializers.CharField(source='tel', max_length=45)
    zip = serializers.CharField(source='zipcode', max_length=7)
    address = serializers.CharField(max_length=300)
    address_more = serializers.CharField(max_length=300)


class UserLoginResponse(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source='id',
        help_text=_("회원 항번")
    )
    contact = serializers.CharField(
        source='tel',
        max_length=45,
        help_text=_("연락처")
    )

    class Meta:
        model = User
        fields = (
            'user_id', 'email', 'nickname', 'name', 'contact',
            'age', 'birth_year',
            'gender', 'skin_type',
            'review_count',
            'profile_image'
        )
        extra_kwargs = {
            'email': {
                'help_text': _("이메일 (회원 아이디)"),
            },
            'nickname': {
                'help_text': _("회원 닉네임"),
            },
            'name': {
                'help_text': _("회원 이름"),
            },
            'age': {
                'help_text': _("회원 나이"),
            },
            'gender': {
                'help_text': _("성별['f', 'm'],"),
            },
            'skin_type': {
                'help_text': _("피부타입 = ['건성', '지성', '중성', '복합성', '민감성']"),
            },
            'birth_year': {
                'help_text': _("출생년도"),
            },
            'review_count': {
                'help_text': _("리뷰건수"),
            },
            'profile_image': {
                'help_text': _("회원 썸네일"),
            },
        }


class UserSimple(UserLoginResponse):
    rank = serializers.IntegerField()
    is_blinded = serializers.IntegerField()

    # profile = UserProfileResponse(required=False)

    class Meta(UserLoginResponse.Meta):
        fields = (
            'user_id', 'email', 'nickname',
            'age', 'birth_year',
            'gender', 'skin_type',
            'review_count',
            'profile_image',
            'rank', 'is_blinded',
        )


class UserBasic(serializers.Serializer):
    user_id = serializers.IntegerField(
        source='id',
        help_text=_("회원 항번")
    )
    profile_image = serializers.URLField(
        help_text=_("회원 이미지")
    )
    nickname = serializers.CharField(
        help_text=_("회원 닉네임")
    )
    gender = serializers.CharField(
        allow_null=True,
        help_text=_("성별['f', 'm']")
    )
    skin_type = serializers.CharField(
        allow_null=True,
        help_text=_("피부타입 = ['건성', '지성', '중성', '복합성', '민감성']")
    )
    birth_year = serializers.IntegerField(
        allow_null=True,
        help_text=_("출생년도")
    )
    age = serializers.IntegerField(
        allow_null=True,
        help_text=("회원 나이")
    )
    review_count = serializers.IntegerField(
        help_text=_("리뷰건수")
    )
    like_count = serializers.IntegerField(
        help_text=_("좋아요 수")
    )
    rank = serializers.IntegerField(
        help_text=_("회원랭킹")
    )


class ReviewResponse(serializers.Serializer):
    rank = serializers.IntegerField(
        help_text=_("회원랭킹")
    )
    
    review_point = serializers.IntegerField(
        source='score',
        help_text=_("리뷰 포인트")
    )
    
    ratio = serializers.FloatField(
        help_text=_("랭킹 퍼센트")
    )
    

class UserDetail(UserSimple):
    wish_count = serializers.IntegerField(
        required=False,
        help_text=_("위시 키운트")
    )
    pick_count = serializers.IntegerField(
        required=False,
        help_text=_("캐스트(픽) 카운트")
    )

    review_this_week = ReviewResponse(
        allow_null=True,
        help_text=_("이번주 리뷰")
    )
    
    review_last_week = ReviewResponse(
        allow_null=True,
        help_text=_("지난주 리뷰")
    )
    
    review_all = ReviewResponse(
        allow_null=True,
        help_text=_("전체 리뷰")
    )
    
    class Meta(UserSimple.Meta):
        fields = (
            'user_id', 'email', 'nickname',
            'age', 'birth_year',
            'gender', 'skin_type',
            'review_count',
            'profile_image',
            'rank', 'is_blinded',
            'wish_count', 'pick_count',
            'review_last_week',
            'review_this_week',
            'review_all'
        )


class AccountResponse(serializers.Serializer):
    user = UserLoginResponse(
        help_text=_("로그인 사용자 정보")
    )


class UserResponse(SuccessMessageResponse):
    user = UserDetail(
        help_text=_("사용자 정보")
    )
    
class User_extra_RankResponse(SuccessMessageResponse):
    user = UserDetail(
        help_text=_("사용자 정보")
    )


class UsersResponse(serializers.Serializer):
    users = UserBasic(
        many=True,
        help_text=_("회원 리스트")
    )
    users_count = serializers.IntegerField(
        required=False,
        help_text=_("회원 카운팅 (1페이지일때만 노출) ")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )
    
    
class UserV2Basic(serializers.Serializer):
    
    user_id = serializers.IntegerField(
        source='idRegister',
        help_text=_("회원 항번")
    )
    profile_image = serializers.URLField(
        help_text=_("회원 이미지")
    )
    nickname = serializers.CharField(
        help_text=_("회원 닉네임")
    )
    review_point = serializers.IntegerField(
        source='score',
        help_text=_("리뷰 점수")
    )
    rank = serializers.IntegerField(
        help_text=_("회원랭킹")
    )
    ratio = serializers.FloatField(
        help_text=_("회원랭킹 백분위")
    )
    


class UsersV2Response(UsersResponse):
    users = UserV2Basic(
        many=True,
        help_text=_("회원 리스트")
    )
    start_time = serializers.DateTimeField(
        required=False,
        help_text='시작 시간'
    )
    end_time = serializers.DateTimeField(
        required=False,
        help_text='끝 시간'
    )
    
    
    
