from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from dateutil.parser import parse
from pytz import timezone
from libs.utils import iso8601
from datetime import datetime, timedelta

class BrandTemp(serializers.Serializer):
    brand_id = serializers.IntegerField(
        help_text=_("브랜드 항번")
    )
    name = serializers.CharField(
        help_text=_("브랜드명")
    )


class MonthlyBanner(serializers.Serializer):
    recommend_id = serializers.IntegerField(
        source='id',
        help_text=_("이달의추천신제품 항번 ")
    )
    link_type = serializers.IntegerField(
        help_text=_("링크종류")
    )
    link_code = serializers.CharField(
        help_text=_("링크값")
    )
    is_custom = serializers.BooleanField(
        help_text=_("링크진입 (false:제품상세, true:해당광고링크)")
    )
    banner_image = serializers.URLField(
        required=False,
        help_text=_("배너이미지 (없으면 NULL)")
    )
    banner_image_720 = serializers.URLField(
        required=False,
        help_text=_("배너이미지 (없으면 NULL)")
    )
    banner_ratio = serializers.FloatField(
        help_text=_("이미지 비율")
    )
    end_date = serializers.SerializerMethodField(
        source='end_date',
        help_text=_("유효기간(UTC)")
    )
    def get_end_date(self, obj):
        kst = timezone('Asia/Seoul')
        utc = timezone('utc')
        try:
            end_date = obj['end_date'] if isinstance(obj, dict) else obj.end_date
            kst_dt = parse(end_date)
            # set timezone when not exist
            if kst_dt.tzinfo == None:
                kst_dt = kst.localize(kst_dt)
            utc_dt = kst_dt.astimezone(utc)
        except:
            # 방어 코드; 유효시간 한시간
            utc_dt = utc.localize(datetime.utcnow()) + timedelta(hours=1)
        return iso8601(utc_dt)


class NewMonthlyBanner(MonthlyBanner):
    banner_image = serializers.URLField(
        source='banner_A_image',
        required=False,
        help_text=_("배너이미지 (없으면 NULL)")
    )
    banner_image_720 = serializers.URLField(
        source='banner_A_image_720',
        required=False,
        help_text=_("배너이미지 (없으면 NULL)")
    )

class MonthlyProduct(MonthlyBanner):
    product_id = serializers.IntegerField(
        help_text=_("제품 항번")
    )
    name = serializers.CharField(
        max_length=None,
        help_text=_("제품명")
    )
    product_image = serializers.URLField(
        required=False,
        help_text=_("제품이미지 (없으면 NULL)")
    )
    product_image_720 = serializers.URLField(
        required=False,
        help_text=_("제품이미지 (없으면 NULL)")
    )
    brand = BrandTemp(
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


class NewMonthlyProduct(MonthlyProduct, NewMonthlyBanner):
    pass


class RecommandProduct(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=('product', 'banner'),
        help_text=_("추천제품 및 이달의추천신제품 타입 값(product, banner)")
    )
    monthly_product = MonthlyProduct(
        required=False,
        help_text=_("추천제품 및 이달의추천신제품")
    )
    monthly_banner = MonthlyBanner(
        required=False,
        help_text=_("추천제품 및 이달의추천신제품 ")
    )


class RecommendKeywordResponse(serializers.Serializer):
    placeholder = serializers.CharField(
        allow_null=True,
        help_text=_("placeholder")
    )
    keywords = serializers.ListField(
        child=serializers.CharField(
            help_text=_("추천 검색어")
        ),
        help_text=("추천 검색어 리스트")
    )
