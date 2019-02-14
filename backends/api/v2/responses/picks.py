from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from backends.api.v2.responses.users import UserBasic
from backends.common.serializers import GlowpickSerializer

from .paging import Paging
from models.picks import Pick, PickCategory
from models.pick_likes import PickLike
from .brands import BrandSimple
from .editors import EditorSerializer
from models.pick_banners import PickBanner
from models.products import Product

"""
    <name>Serializer : Model 을 참조하는 Serializer 
    <name>Response : Response 를 위한 Serializer class 
"""



class PickProductSimpleSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='id')
    brand = BrandSimple(many=False, read_only=True)
    product_image = serializers.URLField(source='image')
    price = serializers.DecimalField(
        max_digits=None,
        decimal_places=0,
        help_text=_("가격"),
    )

    class Meta:
        model = Product

        fields = ('product_id', 'name', 'brand', 'volume', 'price', 'description',
                  'product_image', 'product_image_160')



class PickCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PickCategory
        fields = ('category_id', 'name')

class PickSerializer(serializers.ModelSerializer):
    brand_detail = BrandSimple(many=False, read_only=True)
    editor = EditorSerializer(many=False, read_only=True)
    category = PickCategorySerializer(many=False, read_only=True)

    product_count = serializers.IntegerField(source='pickproducts_set.count',
                                             read_only=True)
    thumbnail = serializers.CharField(read_only=True)
    class Meta:
        model = Pick
        fields = ('pick_id', 'brand','brand_detail', 'editor', 'category', 'product_count',
                  'created_at', 'image', 'title','contents','editor_pick',
                  'read_count', 'thumbnail','comment_count','recommend_count')

class PickSimpleResponse(serializers.Serializer):
    pick_id = serializers.IntegerField(
        help_text=_("캐스트(픽)항번")
    )
    pick_image = serializers.URLField(
        source='image',
        required=False,
        help_text=_("캐스트(픽) (없으면 NULL) ")
    )

class PickCategorySimpleResponse(serializers.Serializer):
    category_id = serializers.IntegerField(
        help_text=_("캐스트(픽) 카테고리 항번")
    )
    name = serializers.CharField(
        help_text=_("캐스트(픽) 카테고리 명")
    )
    is_new = serializers.BooleanField(
        required=False,
        help_text=_("3일 이내의 신규 컨텐츠 존재 유무")
    )

class PickCommentResponse(serializers.Serializer):
    comment_id = serializers.IntegerField(
        source='id',
        help_text=_("픽 댓글 항번")
    )
    user = UserBasic(
        help_text=_("회원 정보")
    )
    comment = serializers.CharField(
        help_text=_("댓글 내용")
    )
    created_at = serializers.DateTimeField(
        help_text=_("작성 일시")
    )

class PickListResponse(GlowpickSerializer):
    picks = PickSimpleResponse(
        many=True,
        help_text=_("캐스트(픽)리스트")
    )
    categories = PickCategorySimpleResponse(
        required=False,
        many=True,
        help_text=_("캐스트(픽) 분류")
    )
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("캐스트(픽) 전체수")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )

class PickBannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = PickBanner

        fields = ('banner_id','pick','title','link_type','link_code',
                  'sort_key','is_display','create_date','is_display',
                  'banner_image')


class PickBannerResponse(serializers.Serializer):

    banners = PickBannerSerializer(
        many=True,
        help_text=_('배너 리스트')
    )

class PickProductResponse(serializers.Serializer):

    products = PickProductSimpleSerializer(
        many=True,
        read_only=True,
        help_text=_("제품 리스트")
    )

    products_count = serializers.IntegerField(
        required=False,
        help_text=_("전체 댓글 수 (1페이지일때만 노출)")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class PickLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PickLike
        fields = ('user', 'pick', 'create_date')

class PickIntegratedResponse(serializers.Serializer):
    like = serializers.BooleanField(
        help_text=_('like 존재유무')
    )

    products = PickProductSimpleSerializer(
        many=True,
        help_text=_('제품 디테일')
    )

    pick = PickSerializer(
        help_text=_('픽 디테일')
    )

    banners = PickBannerSerializer(
        many=True,
        help_text=_('배너 리스트')
    )

class PickCommentsResponse(serializers.Serializer):
    comments = PickCommentResponse(
        many=True,
        help_text=_("댓글 리스트")
    )
    comments_count = serializers.IntegerField(
        required=False,
        help_text=_("전체 댓글 수 (1페이지일때만 노출)")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )

