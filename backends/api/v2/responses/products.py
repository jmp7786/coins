from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from backends.api.v2.responses.recommends import NewMonthlyProduct
from backends.common.serializers import GlowpickSerializer
from models.product_goods import ProductGoods
from .banners import Banner
from .brands import BrandSimple, BrandInfo
from .categories import SubCategorySimple, CategoryInfo
from .filters import StoreSimple, KeywordSimple, StoreBasic, ProductCategoryFlat
from .paging import Paging
from .stores import StoreInfo
from dateutil.parser import parse
from pytz import timezone, utc
from libs.utils import iso8601
from datetime import datetime, timedelta


class Goods(serializers.ModelSerializer):
    class Meta:
        model = ProductGoods
        fields = ('goods_count', 'max_price', 'min_price')
        extra_kwargs = {
            'goods_count': {
                'help_text': _("맵핑된 상품 수"),
            },
            'max_price': {
                'help_text': _("상품 최고가격"),
            },
            'min_price': {
                'help_text': _("상품 최저가격"),
            },
        }


class ProductSimple(serializers.Serializer):
    product_id = serializers.IntegerField(
        source='id',
        help_text=_("제품 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("제품명")
    )
    product_image = serializers.URLField(
        source='product_image_160',
        required=False,
        help_text=_(" 제품이미지 (없으면 NULL)")
    )

    goods_info = Goods(
        source='productgoods',
        default=None,
        help_text=_("상품 구매 정보")
    )


class ProductSimpleWithBrand(ProductSimple):
    brand = BrandSimple(
        required=True,
        help_text=_("브랜드 정보")
    )


class ProductBasic(ProductSimple):
    brand = BrandSimple(
        required=False,
        help_text=_("브랜드 정보")
    )
    rating_avg = serializers.FloatField(
        required=False,
        help_text=_("평점")
    )
    review_count = serializers.IntegerField(
        required=False,
        help_text=_("리뷰건수")
    )
    volume = serializers.CharField(
        max_length=None,
        required=False,
        help_text=_("용량")
    )
    price = serializers.DecimalField(
        required=False,
        max_digits=None,
        decimal_places=0,
        help_text=_("가격")
    )
    is_discontinue = serializers.BooleanField(
        required=False,
        help_text=_("단종여부")
    )
    rank = serializers.IntegerField(
        required=False,
        help_text=_("순위")
    )


class ProductBasicWithRankByReleaseDate(ProductBasic):
    rank = serializers.IntegerField(required=False)
    rank_change_type = serializers.CharField(default='hide')


class ShopInfo(serializers.Serializer):
    """
    네이버 최저가 정보
    """
    shop_lprice = serializers.IntegerField(
        required=False,
        help_text=_("최저가격")
    )
    shop_hprice = serializers.IntegerField(
        required=False,
        help_text=_("최고가격")
    )
    shop_title = serializers.CharField(
        required=False,
        help_text=_("최저가명")
    )
    shop_link = serializers.URLField(
        required=False,
        help_text=_("최저가링크")
    )
    shop_mallName = serializers.CharField(
        required=False,
        help_text=_("쇼핑몰명")
    )
    shop_image = serializers.CharField(
        required=False,
        help_text=_("최저가이미지")
    )


class BlogInfo(serializers.Serializer):
    """
    네이버 블로그 정보
    """
    blog_title = serializers.CharField(
        required=False,
        help_text=_("블로그명")
    )
    blog_description = serializers.CharField(
        required=False,
        help_text=_("블로그설명")
    )
    blogger_name = serializers.CharField(
        required=False,
        help_text=_("블로거명")
    )
    blog_link = serializers.URLField(
        required=False,
        help_text=_("블로그링크")
    )
    blogger_link = serializers.URLField(
        required=False,
        help_text=_("블로거링크")
    )


class AwardsDetailInfo(serializers.Serializer):
    """
    어워즈 상세 정보
    """
    main_category_id = serializers.IntegerField(
        help_text=_("어워드 대분류 항번")
    )
    sub_category_id = serializers.IntegerField(
        help_text=_("어워드 소분류 항번")
    )
    description = serializers.CharField(
        help_text=_("수상 내용")
    )


class AwardsInfo(serializers.Serializer):
    """
    어워즈 정보
    """
    awards_id = serializers.IntegerField(
        source='id',
        help_text=_("어워드 아이디")
    )
    name = serializers.CharField(
        help_text=_("어워드명")
    )
    awards = AwardsDetailInfo(
        many=True,
        help_text=_("수상 정보")
    )


class IngredientInfo(serializers.Serializer):
    """
    성분 정보 가이드
    """
    case = serializers.CharField(
        help_text=_(
            "가이드 유형"
            "<br>높은 위험도 - C05"
            "<br>중간 위험도 - C04"
            "<br>낮은 위험도 - C03"
            "<br>성분 미정 - C02"
            "<br>성분정보 없음 - C01"
        )
    )
    undefined_count = serializers.IntegerField(
        required=False,
        help_text=_("성분 미정 개수")
    )
    noxious_ingredient_name = serializers.CharField(
        required=False,
        help_text=_("대표 유해 성분 이름")
    )
    noxious_ingredient_count = serializers.IntegerField(
        required=False,
        help_text=_("유해성분 개수")
    )


class MonthNewProduct(serializers.Serializer):
    recommend_id = serializers.IntegerField(
        source='id',
        help_text=_("이달의추천신제품 항번")
    )
    link_type = serializers.IntegerField(
        help_text=_("링크종류")
    )
    link_code = serializers.CharField(
        source='link_target',
        help_text=_("링크값")
    )
    banner_image = serializers.URLField(
        source='banner_B_image_720',
        default=None,
        help_text=_("배너이미지")
    )
    banner_ratio = serializers.FloatField(
        required=False,
        help_text=_("배너비율")
    )
    end_date = serializers.SerializerMethodField(
        source='end_date',
        help_text=_("유효기간(UTC)")
    )
    def get_end_date(self, obj):
        kst = timezone('Asia/Seoul')
        utc = timezone('utc')
        try:
            kst_dt = parse(obj['end_date'])
            # set timezone when not exist
            if kst_dt.tzinfo == None:
                kst_dt = kst.localize(kst_dt)
            utc_dt = kst_dt.astimezone(utc)
        except:
            # 방어코드; 유효시간 1시간
            utc_dt = utc.localize(datetime.utcnow()) + timedelta(hours=1)
        return iso8601(utc_dt)


class ProductDetail(ProductBasic):
    product_image = serializers.URLField(
        required=False,
        help_text=_(" 제품이미지 (없으면 NULL)")
    )

    color_type = serializers.CharField(
        help_text=_("컬러타입")
    )
    description = serializers.CharField(
        help_text=_("제품설명")
    )
    rank_info = serializers.CharField(
        required=False,
        help_text=_("제품 순위 정보")
    )
    # factors_display = serializers.BooleanField(
    #     help_text=_("성분여부")
    # )
    # factors = serializers.CharField(
    #     help_text=_("성분정보")
    # )
    shop_info = ShopInfo(
        required=False,
        many=True,
        help_text=_("최저가정보")
    )
    blog_info = BlogInfo(
        required=False,
        help_text=_("블로그정보")
    )
    awards_info = AwardsInfo(
        required=False,
        many=True,
        help_text=_("어워드 리스트 정보")
    )
    ingredient_info = IngredientInfo(
        required=False,
        help_text=_("성분정보 가이드")
    )
    month_new = MonthNewProduct(
        required=False,
        help_text=_("이달의추천신제품 배너 정보")
    )
    category_top_products = ProductBasic(
        required=False,
        many=True,
        help_text=_("이 카테고리의 탑5 제품 리스트 정보")
    )
    same_feel_products = ProductBasic(
        required=False,
        many=True,
        help_text=_("같은느낌 다른제품 리스트 정보")
    )
    sub_categories = SubCategorySimple(
        source='categories',
        required=False,
        many=True,
        help_text=_("2차카테고리 리스트정보")
    )
    stores = StoreSimple(
        required=False,
        many=True,
        help_text=_("스토어 정보")
    )
    keywords = KeywordSimple(
        required=False,
        many=True,
        help_text=_("키워드 정보")
    )
    wish_count = serializers.IntegerField(
        required=False,
        help_text=_("위시 카운트")
    )


class ProductRanking(ProductBasic):
    rank_change_type = serializers.ChoiceField(
        required=False,
        choices=('show', 'new', 'hide'),
        help_text=_("랭킹변동유형 = ['show', 'new', 'hide'],")
    )
    rank_change = serializers.IntegerField(
        required=False,
        help_text=_("순위변동")
    )


class Ingredient(serializers.Serializer):
    ingredient_id = serializers.IntegerField(
        source='id',
        help_text=_("성분 아이디")
    )
    korean_name = serializers.CharField(
        allow_null=True,
        help_text=_("성분명 (한글)")
    )
    english_name = serializers.CharField(
        allow_null=True,
        help_text=_("성분명 (영어)")
    )
    ewg = serializers.CharField(
        allow_null=True,
        help_text=_("성분 안정도 등급")
    )
    purpose = serializers.CharField(
        allow_null=True,
        help_text=_("성분 설명")
    )


class RecommendProduct(serializers.Serializer):
    recommend_id = serializers.IntegerField(
        source='id',
        required=False,
        help_text=_("이달의추천신제품 항번 ")
    )
    link_type = serializers.IntegerField(
        required=False,
        help_text=_("링크종류")
    )
    link_code = serializers.CharField(
        required=False,
        help_text=_("링크값")
    )
    is_custom = serializers.BooleanField(
        required=False,
        help_text=_("링크진입 (false:제품상세, true:해당광고링크)")
    )
    product_id = serializers.IntegerField(
        help_text=_("제품 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("제품명")
    )
    product_image = serializers.URLField(
        required=False,
        source='product_image_160',
        help_text=_("제품이미지 (없으면 NULL)")
    )
    brand = BrandSimple(
        required=False,
        help_text=_("브랜드 정보")
    )
    rating_avg = serializers.FloatField(
        required=False,
        help_text=_("평점")
    )
    review_count = serializers.IntegerField(
        required=False,
        help_text=_("리뷰건수")
    )
    volume = serializers.CharField(
        max_length=None,
        required=False,
        help_text=_("용량")
    )
    price = serializers.DecimalField(
        required=False,
        max_digits=None,
        decimal_places=0,
        help_text=_("가격")
    )
    is_discontinue = serializers.BooleanField(
        required=False,
        help_text=_("단종여부")
    )
    product_type = serializers.ChoiceField(
        required=False,
        choices=('like', 'editor'),
        help_text=_(
            "like : 이달의 추천 제품, editor : 에디터 선정 추천 제품 "
        )
    )

    goods_info = Goods(
        source='productgoods',
        default=None,
        help_text=_("상품 구매 정보")
    )

    end_date = serializers.SerializerMethodField(
        source='end_date',
        help_text=_("유효기간(UTC)")
    )
    def get_end_date(self, obj):
        kst = timezone('Asia/Seoul')
        utc = timezone('utc')
        try:
            kst_dt = parse(obj['end_date'])
            # set timezone when not exist
            if kst_dt.tzinfo == None:
                kst_dt = kst.localize(kst_dt)
            utc_dt = kst_dt.astimezone(utc)
        except:
            # 방어코드; 유효시간 1시간
            utc_dt = utc.localize(datetime.utcnow()) + timedelta(hours=1)
        return iso8601(utc_dt)


class WeeklyProduct(serializers.Serializer):
    weekly_count = serializers.IntegerField(
        help_text=_("1위를 유지한 주간")
    )
    is_top = serializers.BooleanField(
        help_text=_("최고 1위 유지 주")
    )
    product = ProductBasic(
        help_text=_("제품 정보")
    )
    sub_category = SubCategorySimple(
        help_text=_("제품 2차 카테고리 정보")
    )


class MainNewProduct(ProductSimple):
    volume = serializers.CharField(max_length=None, required=False)
    price = serializers.DecimalField(required=False, max_digits=None, decimal_places=0)
    rank = serializers.IntegerField(required=False)
    is_recommended = serializers.BooleanField(required=False)
    brand = BrandSimple()


class MainRankingProduct(ProductSimple):
    rank = serializers.IntegerField()
    brand = BrandSimple()


class ProductWithBanner(GlowpickSerializer):
    ads_id = serializers.IntegerField(source='id', required=False)
    product = MainNewProduct()
    banner = Banner(required=False)


class NewProductResponse(GlowpickSerializer):
    total_count = serializers.IntegerField()
    items = ProductWithBanner(many=True)


class UserWishesResponse(serializers.Serializer):
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("위시 전체수")
    )
    products = ProductBasic(
        many=True,
        help_text=_("위시리스트 ")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class ProductDetailResponse(serializers.Serializer):
    from .reviews import ReviewSimple
    product = ProductDetail(
        help_text=_("제품 정보")
    )
    is_review_type = serializers.ChoiceField(
        choices=('ok', 'wrote', 'more', 'join'),
        help_text=_("리뷰작성가능타입 (ok:가능 / wrote:이미 작성 / more:추가정보필요 / join:회원가입필요)")
    )
    is_review_message = serializers.CharField(
        required=False,
        help_text=_("리뷰작성가능여부에 대한 메세지")
    )
    is_wish = serializers.BooleanField(
        help_text=_("위시여부 (true:위시 / false:비위시)")
    )
    my_review = ReviewSimple(
        required=False,
        help_text=_("로그인 유저의 리뷰")
    )


class CategoryProductsResponse(serializers.Serializer):
    products = ProductRanking(
        many=True,
        help_text=_("제품리스트")
    )
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("리뷰 카운팅 (1페이지일때만 노출, rank X) ")
    )
    recommend_products = RecommendProduct(
        required=False,
        many=True,
        help_text=_("카테고리별 추천제품 및 이달의추천신제품 (1페이지일때만 노출)")
    )
    category_info = CategoryInfo(
        required=False,
        help_text=_("카테고리 정보")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class BrandProductsResponse(serializers.Serializer):
    products = ProductRanking(
        many=True,
        help_text=_("제품리스트")
    )
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("리뷰 카운팅 (1페이지일때만 노출, rank X) ")
    )
    brand_info = BrandInfo(
        required=False,
        help_text=_("브랜드 정보")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class StoreProductsResponse(serializers.Serializer):
    products = ProductRanking(
        many=True,
        help_text=_("제품리스트")
    )
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("리뷰 카운팅 (1페이지일때만 노출, rank X) ")
    )
    store_info = StoreInfo(
        required=False,
        help_text=_("스토어 정보 (1페이지일때만 노출)")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class ProductsResponse(serializers.Serializer):
    total_count = serializers.IntegerField(
        required=False,
        help_text=_("제품 카운팅 (1페이지일때만 노출)")
    )
    products = ProductBasic(
        many=True,
        help_text=_("제품 리스트")
    )
    brands = BrandSimple(
        required=False,
        many=True,
        help_text=_("브랜드 리스트 (1페이지일때만 노출)")
    )
    brands_count = serializers.IntegerField(
        required=False,
        help_text=_("브랜드 카운팅 (1페이지일때만 노출)")
    )
    categories = ProductCategoryFlat(
        required=False,
        many=True,
        help_text=_("제품 카테고리 리스트 (1페이지일때만 노출)")
    )
    categories_count = serializers.IntegerField(
        required=False,
        help_text=_("카테고리 카운팅 (1페이지일때만 노출)")
    )
    stores = StoreBasic(
        required=False,
        many=True,
        help_text=_("스토어 리스트 (1페이지일때만 노출) ")
    )
    stores_count = serializers.IntegerField(
        required=False,
        help_text=_("스토어 카운팅 (1페이지일때만 노출) ")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class ProductIngredientsResponse(serializers.Serializer):
    product = ProductBasic(
        help_text=_("제품 정보")
    )
    ingredients = Ingredient(
        many=True,
        help_text=_("성분 리스트")
    )


class MonthProductsResponse(serializers.Serializer):
    products = ProductBasicWithRankByReleaseDate(
        many=True,
        help_text=_("제품 리스트")
    )
    recommend_products = NewMonthlyProduct(
        required=False,
        many=True,
        help_text=_("추천제품 및 이달의추천신제품")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )


class WeeklyProductsResponse(serializers.Serializer):
    weekly_products = WeeklyProduct(
        many=True,
        help_text=_("제품 리스트")
    )
    paging = Paging(
        help_text=_("페이징 정보")
    )
