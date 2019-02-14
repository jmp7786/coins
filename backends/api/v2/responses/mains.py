from rest_framework import serializers

from backends.common.serializers import GlowpickSerializer
from .paging import Paging
from .banners import Banner
from .events import HomeEventsResponse
from .notices import Notice
from .picks import PickSimpleResponse
from .products import (NewProductResponse, MainRankingProduct)


class CategoryProducts(serializers.Serializer):
    from .reviews import ReviewBasic

    category_id = serializers.IntegerField(source='id')
    name = serializers.CharField()
    products = MainRankingProduct(many=True)
    review = ReviewBasic()


class RankingProduct(serializers.Serializer):
    counted_at = serializers.DateTimeField()
    categories = CategoryProducts(many=True)


class StoreButton(serializers.Serializer):
    image_url = serializers.URLField(required=False)
    scale = serializers.FloatField(required=False)


class MainHomeResponse(GlowpickSerializer):
    top_banners = Banner(many=True, required=False)
    weekly_rankings = RankingProduct(required=False)
    ongoing_events = HomeEventsResponse(required=False)
    recent_notice = Notice(required=False)
    new_products = NewProductResponse(required=False)
    picks = PickSimpleResponse(many=True, required=False)
    store_button = StoreButton(required=False)
    paging = Paging()
