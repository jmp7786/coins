from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.api.v2.forms.paging import BasicListFormMixin
from models.users import SkinTypeCode, Gender


class UserMetaInfoForm(serializers.Serializer):
    skin_type = serializers.CharField()
    gender = serializers.CharField()
    birth_year = serializers.IntegerField()

    def validate(self, attrs):
        if attrs.get('skin_type') in [e.name for e in SkinTypeCode]:
            attrs['skin_type'] = getattr(SkinTypeCode, attrs.get('skin_type')).value
        else:
            raise serializers.ValidationError("skin_type field is not valid.")

        if attrs.get('gender') in [e.name for e in Gender]:
            attrs['gender'] = getattr(Gender, attrs.get('gender')).value

        return attrs


class UsersListFormMixin(BasicListFormMixin):
    SORTING = ('review_desc', 'review_asc', 'like_desc', 'like_asc', 'top_ranking')

    order = serializers.ChoiceField(
        default='review_desc',
        choices=SORTING,
        help_text=_(
            "정렬순서 <br>"
            "리뷰수 내림차순(기본값) - review_desc, <br>"
            "리뷰수 오름차순 - review_asc,<br>"
            "좋아요순 내림차순 - like_desc, <br>"
            "좋아요순 오름차순 - like_asc, <br>"
            "누적 탑 리뷰어 - top_ranking <br>"
            "이번주 탑 리뷰어 - current_week_top_ranking <br>"
            "지번주 탑 리뷰어 - last_week_top_ranking"
        )
    )
    

class UserFilterMixin(serializers.Serializer):
    GENDER_CHOICES = ('all', 'f', 'm')
    SKIN_TYPE_CHOICES = ('all', 'dry', 'oily', 'normal', 'mix', 'sensitive')
    AGE_CHOICES = ('all', '10s', '20early', '20late', '30early', '30late')

    gender = serializers.ChoiceField(
        default='all',
        choices=GENDER_CHOICES,
        help_text=_(
            "성별 <br>"
            "전체(기본값) - all, <br>"
            "여자 - f, <br>"
            "남자 - m"
        )
    )

    skin_type = serializers.CharField(
        default='all',
        max_length=None,
        help_text=_(
            "피부타입 (다중선택시 값을 콤마로 구분) <br>"
            "전체(기본값) - all, <br>"
            "건성(8) - dry, <br>"
            "지성(9) - oily, <br>"
            "중성(10) - normal, <br>"
            "복합성(11) - mix, <br>"
            "민감성(12) - sensitive"
        )
    )

    age = serializers.CharField(
        default='all',
        max_length=None,
        help_text=_(
            "연령 (다중선택시 값을 콤마로 구분) <br>"
            "전체(기본값) - all, <br>"
            "10대 - 10s, <br>"
            "20대초반 - 20early, <br>"
            "20대후반 - 20late, <br>"
            "30대초반 - 30early, <br>"
            "30대후반 - 30late"
        )
    )

    def validate_skin_type(self, value):
        if value:
            for skin_type in value.split(','):
                if skin_type not in self.SKIN_TYPE_CHOICES:
                    raise serializers.ValidationError('this field is invalid')
        return value

    def validate_age(self, value):
        if value:
            for age in value.split(','):
                if age not in self.AGE_CHOICES:
                    raise serializers.ValidationError('this field is invalid')
        return value


class UsersForm(UsersListFormMixin, UserFilterMixin):
    query = serializers.CharField(
        required=False,
        help_text=_(
            "검색어 <br>'"
            "(회원 닉네임)<br>"
        )
    )
    
class UsersFromRedisForm(BasicListFormMixin):
    PERIOD = ('all', 'last_week', 'this_week')
    
    period = serializers.ChoiceField(
        default='all',
        choices=PERIOD,
        help_text=_(
            "기간을 선택<br>"
            "all, last_week, this_week"
        )
    )
    