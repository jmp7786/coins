from django.db.models import F

from libs.aws.dynamodb import aws_dynamodb_etc_list
from libs.utils import local_now
from models.recommend_products import RecommendProduct
from models.recommend_words import RecommendWord


class RecommendService:
    def get_recommend_words(self, **kwargs):
        """
        추천 검색어
        """
        recommend_type = kwargs.get('type')
        placeholder = '{}_placeholder'.format(recommend_type)
        limit = kwargs.get('limit')
        now = local_now().strftime('%Y%m%d%H%M%S')

        words = RecommendWord.objects.filter(is_display=True)
        placeholder = words.filter(
            recommend_type=placeholder,
            start_date__lt=now,
            end_date__gt=now
        ).values('contents').first()

        words = words.filter(
            recommend_type=recommend_type,
            start_date__lt=now,
            end_date__gt=now
        )
        words = words.values_list('contents', flat=True)
        words = words.order_by('?')
        words = words[:limit]

        res = dict()
        res['placeholder'] = placeholder.get('contents') if placeholder else None
        res['keywords'] = list(words)

        return res

    def get_recommend_words_by_dynamodb(self, **kwargs):
        """
        추천 검색어 ( dynamoDB )
        """
        recommend_type = kwargs.get('type')
        limit = kwargs.get('limit')

        results = aws_dynamodb_etc_list.get_recommend_keywords(recommend_type)
        recommend_list = list()

        if len(results) == 0:
            return {
                'placeholder': None,
                'keywords': []
            }

        recommend_list.append(results[0]['recommendText']['S'])
        del results[0]

        # 리스트가 limit 를 넘지 않게함
        limit = limit if len(results) > limit else len(results)

        from random import shuffle
        shuffle(results)

        for index in range(0, limit):
            recommend_list.append(results[index]['recommendText']['S'])

        res = dict()
        res['placeholder'] = recommend_list[0]
        del recommend_list[0]
        res['keywords'] = recommend_list

        return res

    def get_recommend_products(self):
        """
        이달의 추천 신제품 목록
        """

        recommend_products = RecommendProduct.objects.filter(
            is_month__gt=0
        ).annotate(
            name=F('product__name')
        ).order_by(
            '?'
        )[:1]

        for product in recommend_products:
            setattr(product, 'banner_ratio', 0.2495)
            setattr(product, 'is_custom', product.is_month == 2)

        return recommend_products


service = RecommendService()
