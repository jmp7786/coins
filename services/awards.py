from django.conf import settings

from libs.aws.dynamodb import aws_dynamodb_etc_items
from models.awards import Awards


class AwardService:
    def get_list(self, **kwargs):
        cursor = kwargs.get('cursor')
        limit = kwargs.get('limit')

        awards = Awards.objects.filter(isdisplay='1').order_by('-create_date')
        offset = (int(cursor or 1) - 1) * limit
        results = awards.all()[offset: offset + limit + 1]

        if not results:
            return {
                'list': [],
                'next_offset': None,
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
            }

        if len(results) == limit + 1:
            results = list(results)
            next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }

    def get_award_products(self, award_id):
        # 어워드 정보
        awards = Awards.objects.prefetch_related(
            'awardscategory_set',
        ).get(isdisplay='1', id=award_id)

        # 어워드 메인 카테고리
        mains = awards.awardscategory_set.filter(parent_id=0)
        for main in mains:
            # 어워드 서브 카테고리
            subs = awards.awardscategory_set.exclude(
                parent_id=0
            ).filter(
                parent=main
            ).prefetch_related(
                'awardscategoryproduct_set',
            ).extra(
                select={
                    'is_rank':
                        "IF((SELECT COUNT(*) "
                        "FROM hitcategorymapping hm "
                        "WHERE hm.idHitCategory = hitcategory.idHitCategory) = 3 AND "
                        "(SELECT SUM(hm.sortKey) "
                        "FROM hitcategorymapping hm "
                        "WHERE hm.idHitCategory = hitcategory.idHitCategory) = 6, 1, 0)"}
            )

            for sub in subs:
                setattr(sub, 'products', sub.awardscategoryproduct_set.all().select_related(
                    'product', 'product__brand'
                ))
            setattr(main, 'sub_categories', subs)
        setattr(awards, 'main_categories', mains)

        return awards

    def get_awards_products_by_dynamodb(self, award_id):

        results = aws_dynamodb_etc_items.get_award_products(award_id=award_id)

        awards = dict()
        awards['id'] = None
        awards['name'] = results.get('hitText')
        awards['award_x_image'] = '{}{}'.format(settings.CDN, results.get('image'))
        awards['award_x_image_720'] = '{}{}'.format(settings.CDN, results.get('thumbnail'))
        awards['x_file_ratio'] = results.get('ratio')
        awards['cover_image'] = '{}{}'.format(settings.CDN, results.get('coverImage'))
        awards['cover_image_720'] = '{}{}'.format(settings.CDN, results.get('coverImage'))
        choice_image = results.get('choiceImage')
        if choice_image:
            awards['choice_image'] = '{}{}'.format(settings.CDN, results.get('choiceImage'))
            awards['choice_image_720'] = '{}{}'.format(settings.CDN, results.get('choiceImage'))

        awards['main_categories'] = list()
        for main in results.get('firstCategoryList'):
            main_category = dict()
            main_category['id'] = main.get('id')
            main_category['name'] = main.get('categoryText')
            main_category['sub_categories'] = list()
            for sub in main.get('secondCategoryList'):
                sub_category = dict()
                sub_category['id'] = sub.get('id')
                sub_category['name'] = sub.get('categoryText')
                sub_category['summary'] = sub.get('categorySummary')
                sub_category['is_summary'] = sub.get('isSummary')
                sub_category['is_rank'] = sub.get('isRank')
                sub_category['products'] = list()
                for pdt in sub.get('productList'):
                    item = dict()
                    item['product'] = dict()
                    item['product']['id'] = pdt.get('idProduct')
                    item['product']['name'] = pdt.get('productTitle')
                    item['product']['image'] = '{}{}'.format(settings.CDN, pdt.get('image'))
                    item['product']['product_image_320'] = '{}{}'.format(settings.CDN, pdt.get('thumbnail'))
                    item['product']['brand'] = dict()
                    item['product']['brand']['id'] = 0
                    item['product']['brand']['name'] = pdt.get('brandTitle')
                    item['rank'] = pdt.get('rank')
                    item['rank_label'] = pdt.get('rankLabel')
                    item['rating_avg'] = pdt.get('ratingAvg')
                    item['review_count'] = pdt.get('reviewCount')
                    sub_category['products'].append(item)
                main_category['sub_categories'].append(sub_category)
            awards['main_categories'].append(main_category)

        return awards

service = AwardService()
