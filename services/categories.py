import json
import random
import re

from django.conf import settings
from django.db.models import Case
from django.db.models import F
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Concat

from db.raw_queries import get_monthly_products_by_main_category
from libs.aws.dynamodb import aws_dynamodb_etc_items
from libs.utils import get_image_ratio, request_ads
from models.keywords import Keyword
from models.products import SubCategory, MainCategory
from models.reviews import Review
from models.users import User
from resources.preprocess_category import get_category_id


class CategoryService:
    def get_product_categories(self, **kwargs):
        """
        제품 카테고리 리스트 ( 제품 검색 )
        """
        cursor = kwargs.get('cursor')
        limit = kwargs.get('limit')
        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit

        query = kwargs.get('query')

        categories = SubCategory.objects.filter(is_display=True)

        if query:
            word_list = re.findall('([\w.]+)', query)

            ids = get_category_id(word_list)
            categories = categories.filter(id__in=ids)
            categories = categories.order_by(
                'name'
            ).distinct()

        categories = categories.annotate(
            sub_category_id=F('id'),
            sub_category_name=F('name'),
            main_category_id=F('main_category'),
            main_category_name=F('main_category__name'),
            main_category_is_new=F('main_category__is_new'),
            main_category_image=Case(
                When(main_category__file_name=None, then=None),
                default=Concat(Value(settings.CDN), 'main_category__file_dir', Value('/'), 'main_category__file_name')
            )
        )

        categories = categories[offset: offset + limit]

        return categories

    def get_all_product_categories(self, filter_format=False):
        """
        전제 제품 카테고리 리스트 ( 추전 제품 및 이달의 신제품 포함 )
        """
        categories = SubCategory.objects.filter(
            is_display=True,
            main_category__is_display=True
        )

        categories = categories.annotate(
            sub_category_id=F('id'),
            sub_category_name=F('name'),
            main_category_id=F('main_category'),
            main_category_name=F('main_category__name'),
            main_category_is_new=F('main_category__is_new'),
            main_category_image=Case(
                When(main_category__file_name=None, then=None),
                default=Concat(Value(settings.CDN), 'main_category__file_dir', Value('/'), 'main_category__file_name')
            )
        )

        categories = categories.order_by('main_category__seq')

        results = self._make_categories_response(categories.values(
            'sub_category_id', 'sub_category_name', 'is_new', 'seq',
            'main_category_id', 'main_category_name',
            'main_category_is_new', 'main_category_image'
        ), filter_format=filter_format)

        if not filter_format:
            # monthly
            for idx, category in enumerate(results):
                category['sub_categories'].sort(key=lambda x: x['seq'])

                products = get_monthly_products_by_main_category(category.get('id'))
                if len(products) > 0:
                    recommended_item = dict()
                    choice = random.choice(products)
                    if choice.get('banner_image'):
                        recommended_item['id'] = choice.get('id')
                        recommended_item['banner_image'] = choice.get('banner_image')
                        recommended_item['banner_image_720'] = choice.get('banner_image_720')
                        recommended_item['link_type'] = choice.get('link_type')
                        recommended_item['link_code'] = choice.get('link_code')

                        # 통합검색 인트로는 광고소재C가 있으면 링크 설정과 관계없이 광고링크로 연결됩니다.
                        recommended_item['is_custom'] = True
                        recommended_item['banner_ratio'] = get_image_ratio(
                            recommended_item['banner_image_720'], is_url=True
                        )
                        recommended_item['end_date'] = choice.get('end_date')
                        results[idx]['monthly'] = {
                            'type': 'banner',
                            'monthly_banner': recommended_item
                        }
                    else:
                        recommended_item['id'] = choice.get('id')
                        recommended_item['product_id'] = choice.get('product_id')
                        recommended_item['name'] = choice.get('product_name')
                        recommended_item['product_image'] = choice.get('product_image')
                        recommended_item['product_image_720'] = choice.get('product_image_720')

                        recommended_item['brand'] = dict()
                        recommended_item['brand']['brand_id'] = choice.get('brand_id')
                        recommended_item['brand']['name'] = choice.get('brand_name')

                        recommended_item['price'] = choice.get('price')
                        recommended_item['rating_avg'] = choice.get('rating_avg')
                        recommended_item['review_count'] = choice.get('review_count')
                        recommended_item['volume'] = choice.get('volume')
                        recommended_item['is_discontinue'] = choice.get('is_discontinue')

                        recommended_item['link_type'] = choice.get('link_type')
                        recommended_item['link_code'] = choice.get('link_code')
                        recommended_item['is_custom'] = False
                        recommended_item['banner_ratio'] = 0.249
                        recommended_item['end_date'] = choice.get('end_date')
                        results[idx]['monthly'] = {
                            'type': 'product',
                            'monthly_product': recommended_item
                        }

        return results

    def get_all_product_categories_by_dynamodb(self):
        results = aws_dynamodb_etc_items.get_categories()
        items = json.loads(results[0]['binary']['B'].decode())

        res = list()
        for item in items:
            # choice item (banner type c)
            if 'monthly' in item and item['monthly']:
                choice = random.choice(item['monthly'])

                if 'banner_image' in choice and choice['banner_image']:
                    item['monthly'] = {'type': 'banner', 'monthly_banner': choice}
                else:
                    item['monthly'] = {'type': 'product', 'monthly_product': choice}

            main = dict()
            main['id'] = item.get('id_first_category')
            main['name'] = item.get('first_category_text')
            main['image'] = item.get('first_category_image')
            main['is_new'] = True if item['is_new'] == "1" else False

            main['sub_categories'] = [{
                                          'id': second.get('id_second_category'),
                                          'name': second.get('second_category_text'),
                                          'is_new': True if second.get('is_new') == "1" else False
                                      } for second in item['second_category_list']]

            monthly = item.get('monthly')
            if monthly:
                main['monthly'] = dict()
                banner_type = monthly.get('type')
                main['monthly']['type'] = banner_type
                if banner_type == 'product':
                    product = monthly.get('monthly_product')
                    main['monthly']['monthly_product'] = dict()
                    main['monthly']['monthly_product']['id'] = product.get('id_monthly_product')
                    main['monthly']['monthly_product']['product_id'] = product.get('id_product')
                    main['monthly']['monthly_product']['name'] = product.get('product_title')
                    main['monthly']['monthly_product']['product_image'] = product.get('product_image')
                    main['monthly']['monthly_product']['product_image_720'] = product.get('product_thumbnail')
                    main['monthly']['monthly_product']['price'] = product.get('price')
                    main['monthly']['monthly_product']['volume'] = product.get('volume')
                    main['monthly']['monthly_product']['review_count'] = product.get('review_count')
                    main['monthly']['monthly_product']['rating_avg'] = product.get('rating_avg')
                    main['monthly']['monthly_product']['brand'] = dict()
                    main['monthly']['monthly_product']['brand']['brand_id'] = product.get('id_brand')
                    main['monthly']['monthly_product']['brand']['name'] = product.get('brand_title')

                    main['monthly']['monthly_product']['link_code'] = product.get('link_code')
                    main['monthly']['monthly_product']['link_type'] = product.get('link_type')
                    main['monthly']['monthly_product']['is_custom'] = product.get('is_category') == 'link'
                    main['monthly']['monthly_product']['banner_ratio'] = product.get('banner_ratio')
                    main['monthly']['monthly_product']['end_date'] = product.get('end_date')
                elif banner_type == 'banner':
                    banner = monthly.get('monthly_banner')
                    main['monthly']['monthly_banner'] = dict()
                    main['monthly']['monthly_banner']['id'] = banner.get('id_monthly_product')
                    main['monthly']['monthly_banner']['banner_image'] = banner.get('banner_image')
                    main['monthly']['monthly_banner']['banner_image_720'] = banner.get('banner_thumbnail')
                    main['monthly']['monthly_banner']['link_code'] = banner.get('link_code')
                    main['monthly']['monthly_banner']['link_type'] = banner.get('link_type')
                    main['monthly']['monthly_banner']['is_custom'] = banner.get('is_category') == 'link'
                    main['monthly']['monthly_banner']['banner_ratio'] = banner.get('banner_ratio')
                    main['monthly']['monthly_banner']['end_date'] = banner.get('end_date')

            res.append(main)

        return res

    def _make_categories_response(self, query_set, filter_format=True):
        """
        제품 카테고리 리스트를 응답 형태로 가공함
        """
        categories = list()
        if filter_format:
            categories.append({
                'id': 0,
                'name': '대분류 전체',
                'image': None,
                'is_new': False,
                'sub_categories': [
                    {'id': 0, 'name': '소분류 전체', 'seq': 0}
                ]
            })

        for row in query_set.iterator():
            b_main = True

            for category in categories:
                if row['main_category_id'] == category['id']:
                    new_sub = dict()
                    new_sub['id'] = row['sub_category_id']
                    new_sub['name'] = row['sub_category_name']
                    new_sub['seq'] = row['seq']
                    if not filter_format:
                        new_sub['is_new'] = row['is_new']

                    category['sub_categories'].append(new_sub)
                    b_main = False
                    break

            if b_main:
                new_main = dict()
                new_main['id'] = row['main_category_id']
                new_main['name'] = row['main_category_name']
                if not filter_format:
                    new_main['is_new'] = row['main_category_is_new']
                    new_main['image'] = row['main_category_image']

                new_main['sub_categories'] = list()
                if filter_format:
                    new_main['sub_categories'].append({
                        'id': 0,
                        'name': '소분류 전체',
                        'is_new': False,
                        'seq': 0
                    })

                new_sub = dict()
                new_sub['id'] = row['sub_category_id']
                new_sub['name'] = row['sub_category_name']
                new_sub['seq'] = row['seq']
                if not filter_format:
                    new_sub['is_new'] = row['is_new']

                new_main['sub_categories'].append(new_sub)
                categories.append(new_main)

        return categories

    def get_user_reviews_categories(self, user_id):
        """
        회원이 작성한 리뷰가 포함된 제품 카테고리 리스트
        리스트 필터의 데이터
        """
        query_set = Review.objects.filter(user_id=user_id, is_display=True, product__is_display=True)
        query_set = query_set.filter(
            product__categories__is_display=True,
            product__categories__main_category__is_display=True
        )
        query_set = query_set.annotate(
            sub_category_id=F('product__categories'),
            sub_category_name=F('product__categories__name'),
            seq=F('product__categories__seq'),
            main_category_id=F('product__categories__main_category'),
            main_category_name=F('product__categories__main_category__name')
        )

        query_set = query_set.order_by('product__categories__main_category__seq')
        query_set = query_set.distinct()

        results = self._make_categories_response(query_set.values(
            'sub_category_id', 'sub_category_name',
            'main_category_id', 'main_category_name', 'seq'
        ))

        for category in results:
            category['sub_categories'].sort(key=lambda x: x['seq'])

        return results

    def get_user_wishes_categories(self, user_id):
        """
        회원의 위시리스트의 제품이 포함된 제품 카테고리 리스트
        리스트 필터의 데이터
        """
        query_set = User.objects.get(id=user_id).wishes.visible()
        query_set = query_set.filter(
            categories__is_display=True,
            categories__main_category__is_display=True
        )
        query_set = query_set.annotate(
            sub_category_id=F('categories'),
            sub_category_name=F('categories__name'),
            seq=F('categories__seq'),
            main_category_id=F('categories__main_category'),
            main_category_name=F('categories__main_category__name')
        )
        query_set = query_set.order_by('categories__main_category__seq')
        query_set = query_set.distinct()

        results = self._make_categories_response(query_set.values(
            'sub_category_id', 'sub_category_name',
            'main_category_id', 'main_category_name', 'seq'
        ))

        for category in results:
            category['sub_categories'].sort(key=lambda x: x['seq'])

        return results

    def get_keywords_by_category_id(self, category_id):
        """
        키워드 리스트 ( sub_category id )
        """

        query_set = Keyword.objects.filter(
            subcategorykeywords__sub_category_id__exact=category_id
        )
        query_set = query_set.values(
            'id', 'name'
        ).distinct()

        return query_set

    def get_categoires_by_brand_id(self, brand_id):
        """
        특정 브랜드가 포함된 제품 카테고리 리스트
        """
        query_set = MainCategory.objects.filter(
            is_display=True,
            subcategory__is_display=True,
            subcategory__product__brand=brand_id
        ).prefetch_related(
            'subcategory_set'
        ).distinct()

        results = [
            {
                'id': 0,
                'name': "대분류 전체",
                'sub_categories': [
                    {
                        'id': 0,
                        'name': "소분류 전체"
                    }
                ]
            }
        ]
        for main in query_set:
            item = dict()
            item['id'] = main.id
            item['name'] = main.name
            item['sub_categories'] = [
                {
                    'id': 0,
                    'name': "소분류 전체"
                }
            ]
            for sub in main.subcategory_set.filter(is_display=True).all():
                sub_item = dict()
                sub_item['id'] = sub.id
                sub_item['name'] = sub.name
                item['sub_categories'].append(sub_item)

            results.append(item)

        return results

    def get_categories_by_store_id(self, store_id):
        """
        특정 스토어와 연관된 제품 카테고리 리스트
        """
        query_set = MainCategory.objects.filter(
            is_display=True,
            subcategory__is_display=True,
            subcategory__product__storesproducts__store=store_id
        ).prefetch_related(
            'subcategory_set'
        ).distinct()

        results = [
            {
                'id': 0,
                'name': "대분류 전체",
                'sub_categories': [
                    {
                        'id': 0,
                        'name': "소분류 전체"
                    }
                ]
            }
        ]
        for main in query_set:
            item = dict()
            item['id'] = main.id
            item['name'] = main.name
            item['sub_categories'] = [
                {
                    'id': 0,
                    'name': "소분류 전체"
                }
            ]
            for sub in main.subcategory_set.filter(is_display=True).all():
                sub_item = dict()
                sub_item['id'] = sub.id
                sub_item['name'] = sub.name
                item['sub_categories'].append(sub_item)

            results.append(item)

        return results


service = CategoryService()
