from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from models.common_codes import CommonCodeValue
from .paging import Paging
from .products import ProductSimpleWithBrand, ProductBasic
from .scoreboards import Scoreboard
from .users import UserSimple, UserBasic


class ReviewSimple(serializers.Serializer):
    review_id = serializers.IntegerField(
        source='id',
        help_text=_("리뷰 항번 ")
    )
    rating = serializers.IntegerField(
        help_text=_("평점")
    )
    is_evaluation = serializers.BooleanField(
        help_text=_("평가단 여부")
    )
    like_count = serializers.IntegerField(
        help_text=_("좋아요 수")
    )
    contents = serializers.CharField(
        max_length=None,
        help_text=_("리뷰 컨텐츠 내용")
    )
    state = serializers.CharField(
        required=False,
        max_length=1,
        help_text=_("리뷰 상태 = ['N', 'B', 'C']")
    )
    created_at = serializers.DateTimeField(
        help_text=_("작성일")
    )


class EditorMixin(serializers.Serializer):
    editor = UserSimple(
        required=True,
        source='user',
        help_text=_("작성자 정보")
    )


class ProductMixin(serializers.Serializer):
    product = ProductSimpleWithBrand(
        required=True,
        help_text=_("제품 정보")
    )


class BlindedCauses(serializers.Serializer):
    cause = serializers.CharField(
        allow_null=True,
        help_text=_("사유")
    )
    guide = serializers.CharField(
        allow_null=True,
        help_text=_("수정가)이드")
    )


class ReportTypes(serializers.ModelSerializer):
    class Meta:
        model = CommonCodeValue
        fields = ('value_name', 'value_code')
        extra_kwargs = {
            'value_name': {
                'help_text': _("신고사유 명"),
            },
            'value_code': {
                'help_text': _("신고사유 공통코드"),
            }
        }


class ReviewBasic(ReviewSimple, EditorMixin, ProductMixin):
    pass


class UserReviews(ReviewSimple, ProductMixin):
    pass


class ProductReivews(ReviewSimple, EditorMixin):
    pass


class ReviewBlindedCauses(ProductReivews):
    blinded_causes = BlindedCauses(
        required=False,
        many=True,
        help_text=_("블라인드 된 사유 ")
    )


class ReviewsResponse(serializers.Serializer):
    reviews = ReviewBasic(
        many=True,
        help_text=_("리뷰 리스트 정보")
    )
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("전체 리뷰수")
    )
    top_reviewers = UserBasic(
        required=False,
        many=True,
        help_text=_("탑3 리뷰어 리스트 (top_reviewers 값이 True일 경우)")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class ReivewCheckResponse(serializers.Serializer):
    review = ReviewBlindedCauses(
        required=False,
        help_text=_("리뷰 정보")
    )
    product = ProductBasic(
        help_text=_("")
    )
    is_comment = serializers.BooleanField(
        help_text=_("작성여부")
    )
    message = serializers.CharField(
        required=False,
        help_text=_("팝업 메세지")
    )


class ProductReviewsResponse(ReviewsResponse):
    my_review = ReviewBasic(
        required=False,
        help_text=_("내가 등록한 리뷰")
    )
    scoreboard = Scoreboard(
        required=False,
        help_text=_("점수 정보")
    )


class UserReviewsResponse(ReviewsResponse):
    reviews = UserReviews(
        many=True,
        help_text=_("리뷰 리스트 정보")
    )
    like_count = serializers.IntegerField(
        required=False,
        help_text=_("전체 좋아요 수")
    )


class ReviewWriteResponse(serializers.Serializer):
    review_count = serializers.IntegerField(
        help_text=_("리뷰 수")
    )


class ReportTypesResponse(serializers.Serializer):
    report_types = ReportTypes(
        many=True,
        help_text=_("신고사유 리스트")
    )
    
    
class UserRankUpgrade(serializers.Serializer):
    rank = serializers.IntegerField(
        help_text=_("랭크")
    )
    score = serializers.IntegerField(
        help_text=_("점수")
    )
    ratio = serializers.IntegerField(
        help_text=_("상위 퍼센트")
    )
    upgrade_range = serializers.IntegerField(
        help_text=_("상승폭")
    )
    
    
    
class ReivewCheckRankResponse(serializers.Serializer):
    all = UserRankUpgrade(
        help_text=_("누적 랭크 업그레이드 정보")
    )
    this_week = UserRankUpgrade(
        help_text=_("이번주 랭크 업그레이드 정보")
    )
    upgrade_range_all = serializers.IntegerField(
        allow_null=True,
        help_text=_("전체 상승폭")
    )
    
class UserSimplify(serializers.Serializer):
    profile_image = serializers.URLField(
        help_text=_('프로필 이미지 URL')
    )
    nickname = serializers.CharField(
        help_text=_('닉네임')
    )
    
    
class Reward(serializers.Serializer):
    point = serializers.IntegerField(
        help_text=_('리워드 점수')
    )
    title = serializers.CharField(
        help_text=_('리워드 이름')
    )
    
    
class ReivewCheckRankRangeResponse(serializers.Serializer):
    all = UserRankUpgrade(
        allow_null=True,
        help_text=_("누적 랭크 업그레이드 정보")
    )
    this_week = UserRankUpgrade(
        allow_null=True,
        help_text=_("이번주 랭크 업그레이드 정보")
    )
    rewards = Reward(
        many=True,
        allow_null=True,
        help_text=_("이번주 랭크 업그레이드 정보")
    )
    user = UserSimplify(
        help_text='간략한 유저 정보'
    )