"""
제품 관련 서비스 로직 정의
"""

import json
import os
import re

from django.conf import settings
from django.db.models import F, Max, IntegerField
from django.db.models import Q

from db.raw_queries import (
    get_cateogy_top_products, get_same_feel_products, get_product_factors,
)
from libs.aws.dynamodb import aws_dynamodb_products
from libs.openapi.naver import naver_openapi
from libs.utils import is_numeric
from models.ingredients import Ingredient
from models.product_goods import ProductGoods
from models.products import Product, ViewCategory, ProductRanking
from models.recommend_products import RecommendProduct
from models.stores import Store
from models.users import Wish
from libs.shortcuts import get_object_or_404



class ProductService:
    def get_new_products(self, this_month, limit):

        recommend_products = RecommendProduct.objects.filter(
            home_showing_type__gt=0
        ).order_by('?').all()[:limit]

        products_of_this_month = Product.objects.new_products(this_month).select_related(
            'brand', 'productgoods'
        ).all()[:limit]

        result_products = [{'product': item} for item in products_of_this_month]

        items = list(recommend_products) + result_products
        _keys = {}
        results = []
        for index, item in enumerate(items):
            _id = None
            if isinstance(item, RecommendProduct):
                _id = item.product.id
                setattr(item.product, 'is_recommended', True)
            else:
                _id = item['product'].id
                setattr(item['product'], 'is_recommended', False)
            _id = str(_id)
            if _id not in _keys.keys():
                _keys[_id] = _id
                results.append(item)

        return results[:limit]

    def get_weekly_ranking(self):
        items = ViewCategory.objects.select_related(
            'category', 'review', 'review__product', 'review__product__brand', 'review__user',
            'review__product__productgoods'
        ).order_by('-new_review_count').all()[:15]
        import random
        items = sorted(items, key=lambda x: random.random())
        categories = []

        if items:
            items = items[:4]
            for item in items:
                category = item.category
                products = ProductRanking.objects.select_related(
                    'product', 'product__brand', 'product__productgoods'
                ).filter(
                    ref_id=category.id,
                    rank_type='category'
                ).order_by('ranking').all()[:3]

                products = [item.product for item in products]
                [setattr(product, 'rank', index + 1) for index, product in enumerate(products)]
                setattr(category, 'products', products)

                item.review.contents = re.sub(r"(\s*\n)+", "\n", item.review.contents)
                setattr(category, 'review', item.review)
                categories.append(category)

        return categories

    def search_product_list(self, params, only_count=None):
        """
        제품 검색 ( EC API )
        """
        cursor = params.data.get('cursor')
        limit = params.data.get('limit')
        offset = (cursor - 1) * limit

        product_name = params.data.get('name')
        product_id = params.data.get('product_id')
        brand_id = params.data.get('brand_id')

        main_category_id = params.data.get('main_category_id')
        sub_category_id = params.data.get('sub_category_id')

        is_display = params.data.get('is_display')
        sort = params.data.get('order')

        products = Product.objects.all().select_related(
            'brand'
        ).prefetch_related(
            'categories', 'categories__main_category'
        )

        if is_display is not None:
            products = products.filter(is_display=is_display)

        if product_name:
            for word in product_name.split():
                products = products.extra(
                    where=[
                        "replace(product.productTitle, ' ', '') LIKE %s "],
                    params=['%' + word + '%'])

        if product_id:
            products = products.filter(id=product_id)

        if brand_id:
            products = products.filter(brand=brand_id)

        if sub_category_id is not None:
            products = products.filter(categories=sub_category_id)
            products = products.distinct()
        else:
            if main_category_id is not None:
                products = products.filter(categories__main_category=main_category_id)
                products = products.distinct()

        if only_count:
            return products.count()

        if sort:
            sort = tuple(s for s in sort.split())
            products = products.order_by(*sort)

        products = products[offset: offset + limit + 1]

        return products

    def get_list(self, only_count=False, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        query = kwargs.get('query')

        products = Product.objects.filter(
            is_display=True,
            brand__is_display=True,
        ).select_related(
            'brand', 'productgoods'
        )

        if query:
            products = products.filter(
                (Q(categories__is_display=True) | Q(categories__is_display=False))
            )

            q = Q()
            word_list = re.findall('([\w.]+)', query)
            if len(word_list) < 1:
                if only_count:
                    return 0
                return {
                    'list': [],
                    'next_offset': None,
                }
            elif len(word_list) == 1:
                if len(word_list[0]) == 1:
                    for sch_word in word_list:
                        q &= (Q(name__iexact=sch_word) |
                              Q(brand__name__iexact=sch_word) |
                              Q(brand__phoneme__iexact=sch_word) |
                              Q(categories__name__iexact=sch_word))
                else:
                    for sch_word in word_list:
                        products = products.extra(
                            where=[
                                "replace(product.productTitle, ' ', '') LIKE %s "
                                "OR replace(brand.brandTitle, ' ', '') LIKE %s "
                                "OR brand.brandTitleInitial LIKE %s "
                                "OR replace(secondcategory.secondCategoryText, ' ', '') LIKE %s"
                            ],
                            params=[
                                '%{}%'.format(sch_word),
                                '%{}%'.format(sch_word),
                                '%{}%'.format(sch_word),
                                '%{}%'.format(sch_word),
                            ])
            else:
                for sch_word in word_list:
                    products = products.extra(
                        where=[
                            "replace(product.productTitle, ' ', '') LIKE %s "
                            "OR replace(brand.brandTitle, ' ', '') LIKE %s "
                            "OR brand.brandTitleInitial LIKE %s "
                            "OR replace(secondcategory.secondCategoryText, ' ', '') LIKE %s"
                        ],
                        params=[
                            '%{}%'.format(sch_word),
                            '%{}%'.format(sch_word),
                            '%{}%'.format(sch_word),
                            '%{}%'.format(sch_word),
                        ])

            products = products.filter(q).distinct()

        if only_count:
            return products.count()

        if query:
            products = products.order_by('-score')

        products = products.distinct()

        if cursor and not query:
            base = products.filter(id__lt=cursor)
            results = base.all()[:limit + 1]
        else:
            cursor = int(cursor or 1)
            offset = (cursor - 1) * limit
            results = products.all()[offset: offset + limit + 1]

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
            if cursor and not query:
                next_offset = results[-2].id
            else:
                next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }

    def get_product_detail_dynamodb(self, product_id):
        results = aws_dynamodb_products.get_product(product_id)

        month_new = json.loads(results.get('month_new').get('B').decode())

        if month_new:
            month_new['id'] = month_new.get('id_monthly_product')
            month_new['link_target'] = month_new.get('link_code')
            month_new['banner_B_image'] = month_new.get('banner_image')
            month_new['banner_B_image_720'] = month_new.get('banner_thumbnail')
        else:
            month_new = None

        # 네이버 api
        if not 'naver_api_updated_at' in results:
            # initial
            blog_info, shop_info = naver_openapi.retrieve(
                results['brand_title']['S'] + " " + results['product_title']['S']
            )
            attr_update = {
                'naver_api_updated_at': {'Value': {'S': naver_openapi.get_current_time()}},
                'blog_info': {'Value': {'B': json.dumps(blog_info)}},
                'shop_info': {'Value': {'B': json.dumps(shop_info)}}
            }
            aws_dynamodb_products.update(product_id=product_id, attr_update=attr_update)
        else:
            updated_at = results['naver_api_updated_at']['S']
            if naver_openapi.check_updadted(updated_at):
                blog_info, shop_info = naver_openapi.retrieve(
                    results['brand_title']['S'] + " " + results['product_title']['S']
                )
                attr_update = {
                    'naver_api_updated_at': {'Value': {'S': naver_openapi.get_current_time()}},
                    'blog_info': {'Value': {'B': json.dumps(blog_info)}},
                    'shop_info': {'Value': {'B': json.dumps(shop_info)}}
                }
                aws_dynamodb_products.update(product_id=product_id, attr_update=attr_update)
            else:
                blog_info = json.loads(results['blog_info']['B'].decode()) if 'blog_info' in results else None
                shop_info = json.loads(results['shop_info']['B'].decode()) if 'shop_info' in results else []

        sub_categories = [{
                              'id': a['id_second_category'],
                              'name': a['second_category_text']
                          } for a in json.loads(results['second_category_list']['B'].decode())]

        awards_info = [{
                           'id': award['id_hit_products'],
                           'name': award['first_text'],
                           'awards': [{'main_category_id': detail['id_hit_first_category'],
                                       'sub_category_id': detail['id_hit_category'],
                                       'description': detail['second_text']} for detail in award['awards']]
                       } for award in json.loads(results['award_list']['B'].decode())]

        category_top_products = [
            {
                'id': p['id_product'],
                'name': p['product_title'],
                'product_image': p['product_image'],
                'product_image_160': p['product_thumbnail'],
                'rating_avg': p['rating_avg'],
                'review_count': p['review_count'],
                'rank': p['product_rank'],
                'price': p['price'],
                'volume': p['volume']
            } for p in json.loads(results['category_top_products']['B'].decode())]

        same_feel_products = [
            {
                'id': p['id_product'],
                'name': p['product_title'],
                'product_image': p['product_image'],
                'product_image_160': p['product_thumbnail'],
                'rating_avg': p['rating_avg'],
                'review_count': p['review_count'],
                'price': p['price'],
                'volume': p['volume']
            } for p in json.loads(results['same_feel_products']['B'].decode())]

        stores = [{
                      'id': store['id_store'],
                      'name': store['store_name']
                  } for store in json.loads(results['store_list']['B'].decode())]

        keywords = [{
                        'id': keyword['id_keyword'],
                        'name': keyword['keyword_text']
                    } for keyword in json.loads(results['keyword_list']['B'].decode())]

        product = {
            'id': int(results['id_product']['N']),
            'is_display': int(results['is_display']['N']),
            'name': results['product_title']['S'],
            'description': results['product_text']['S'],
            'brand': {
                'id': int(results['id_brand']['N']),
                'name': results['brand_title']['S'],
                'brand_image_160': None if 'NULL' in results['brand_thumbnail'] else results['brand_thumbnail']['S']
            },
            'volume': results['volume']['S'],
            'price': int(results['price']['N']),
            'rating_avg': float(results['rating_avg']['N']),
            'review_count': int(results['review_count']['N']),
            'wish_count': Wish.objects.filter(product_id=product_id).count(),
            'is_discontinue': int(results['is_discontinue']['N']),
            'factors_display': int(results['factors_display']['N']),
            'categories': sub_categories,
            'awards_info': awards_info,
            'stores': stores,
            'keywords': keywords,
            'month_new': month_new,
            'category_top_products': category_top_products,
            'same_feel_products': same_feel_products,
            'blog_info': blog_info if blog_info else None,
            'shop_info': shop_info,
            'color_type': None if 'NULL' in results['color_type'] else results['color_type']['S'],
            'rank_info': None if 'NULL' in results['rank_info'] else results['rank_info']['S'],
            'factors': None if 'NULL' in results['factors'] else results['factors']['S'],
            'product_image': None if 'NULL' in results['product_image'] else results['product_image']['S'],
            'product_image_160': None if 'NULL' in results['product_thumbnail'] else results['product_thumbnail']['S'],
            # 'brand_image': None if 'NULL' in results['brand_image'] else results['brand_image']['S'],
            # 'brand_image_160': None if 'NULL' in results['brand_thumbnail'] else results['brand_thumbnail']['S'],
        }

        # goods info
        try:
            product['productgoods'] = ProductGoods.objects.get(product=product_id)
        except:
            product['productgoods'] = None

        # ingredient guide
        product['ingredient_info'] = self.guide_ingredient(product_id)

        return product

    def get_product_detail(self, product):

        # factors 성분 정보
        # factors = get_product_factors(product.id)
        # setattr(product, 'factors', factors)
        setattr(product, 'ingredient_info', self.guide_ingredient(product.id))

        # 추천 신제품
        month_new = RecommendProduct.objects.filter(product_id=product.id, is_product__gt=0)[:1]

        if month_new:
            setattr(product, 'month_new', month_new[0])
        else:
            setattr(product, 'month_new', None)

        # 수상 내역
        awards_categories = product.awards_categories.all().select_related(
            'awards',
            'parent',
        ).annotate(
            rank_label=F('awardscategoryproduct__rank_label')
        )

        awards_info = list()
        for category in awards_categories:
            if category.awards.is_display:
                is_check = False
                item = dict()
                item['id'] = category.awards_id
                item['name'] = category.awards.name
                item['awards'] = list()
                t = dict()
                t['main_category_id'] = category.parent_id
                t['sub_category_id'] = category.id
                if is_numeric(category.rank_label):
                    t['description'] = "{}/{} 부문 {} 위".format(
                        category.parent.name,
                        category.name,
                        category.rank_label
                    )
                else:
                    t['description'] = "{}/{} 부문".format(
                        category.parent.name,
                        category.name
                    )

                for idx, info in enumerate(awards_info):
                    if info['id'] == category.awards_id:
                        awards_info[idx]['awards'].append(t)
                        is_check = True

                if is_check:
                    continue

                item['awards'].append(t)
                awards_info.append(item)

        setattr(product, 'awards_info', awards_info)

        # 스토어
        stores = Store.objects.filter(storesproducts__product=product)
        setattr(product, 'stores', stores)

        # category top products
        random_category = product.categories.all().order_by('?').first()
        items = get_cateogy_top_products(random_category.id, 5)
        category_top_products = list()
        for item in items:
            p = dict()
            p['id'] = item['idProduct']
            p['name'] = item['productTitle']
            p['rank'] = item['rank']
            p['review_count'] = item['rationCount']
            p['price'] = item['price']
            p['volume'] = item['volume']
            p['product_image'] = "{}{}/{}".format(settings.CDN, item['p_fileDir'], item['p_fileSaveName'])
            if p['product_image']:
                path = os.path.splitext(p['product_image'])
                p['product_image_160'] = '%s_160%s' % (path[0], path[1])
            else:
                p['product_image_160'] = None
            p['rating_avg'] = item['ratingAvg']
            p['is_discontinue'] = item['isDiscontinue']
            p['brand'] = dict()
            p['brand']['id'] = item['idBrand']
            p['brand']['name'] = item['brandTitle']

            category_top_products.append(p)

        setattr(product, 'category_top_products', category_top_products)

        # same feel products
        items = get_same_feel_products(product.id)
        same_feel_products = list()
        for item in items:
            s = dict()
            s['id'] = item['idProduct']
            s['name'] = item['productTitle']
            s['volume'] = item['volume']
            s['rating_avg'] = item['ratingAvg']
            s['review_count'] = item['rationCount']
            s['product_image'] = "{}{}/{}".format(settings.CDN, item['fileDir'], item['fileSaveName'])
            if s['product_image']:
                path = os.path.splitext(s['product_image'])
                s['product_image_160'] = '%s_160%s' % (path[0], path[1])
            else:
                s['product_image_160'] = None

            same_feel_products.append(s)

        setattr(product, 'same_feel_products', same_feel_products)

        # wish_count
        setattr(product, 'wish_count', Wish.objects.filter(product=product).count())

        return product

    def get_price_range_by_category_id(self, category_id):
        """
        카테고리별 가격범위 및 간격
        """
        query_set = Product.objects.filter(
            is_display=True,
            categories__is_display=True,
            categories=category_id
        )

        query_set = query_set.aggregate(Max('price'))

        price_max = query_set.get('price__max')
        if price_max:
            price_other = price_max % 1000

            if price_other > 0:
                price_max += 1000 - price_other

        return {
            'price_gap': 1000,
            'price_max': price_max,
            'price_range': list()
        }

    def get_price_range_by_store_id(self, store_id):
        """
        스토어별 가격범위 및 간격
        """
        query_set = Product.objects.filter(
            is_display=True,
            storesproducts__store__is_display='Y',
            storesproducts__store=store_id
        )

        query_set = query_set.aggregate(Max('price', output_field=IntegerField()))

        price_max = query_set.get('price__max')
        if price_max:
            price_other = price_max % 1000

            if price_other > 0:
                price_max += 1000 - price_other

        return {
            'price_gap': 1000,
            'price_max': price_max,
            'price_range': list()
        }

    def get_products_by_month(self, **kwargs):
        """
        release_date 값으로 제품 조회
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        ym = kwargs.get('ym')

        products = Product.objects.visible().filter(
            release_date=ym
        ).select_related(
            'brand', 'productgoods'
        ).order_by('-score', 'id')

        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit
        results = products.all()[offset: offset + limit + 1]

        for idx, product in enumerate(results):
            if product.score:
                setattr(product, 'rank', offset + idx + 1)

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

    def guide_ingredient(self, product_id):
        """
        제품 성분 가이드

        높은 위험도 - C05
        중간 위험도 - C04
        낮은 위험도 - C03
        성분 미정 - C02
        성분정보 없음 - C01
        """
        ingredient_guide = {
            'case': 'C01'
        }

        product = get_object_or_404(Product, id=product_id)

        if not product.factors_display:
            return ingredient_guide

        ingredients = Ingredient.objects.filter(productingredient__product=product_id)

        undefined_ingredients = list(filter(lambda x: x.ewg_min is None, ingredients))
        if undefined_ingredients:
            # 성분 미정
            ingredient_guide['case'] = 'C02'
            ingredient_guide['undefined_count'] = len(undefined_ingredients)

        noxious_ingredients = list(filter(
            lambda x: (x.ewg_min is not None and x.ewg_min > 6) or (x.ewg_max is not None and x.ewg_max > 6),
            ingredients
        ))
        if noxious_ingredients:
            # 7-10 등급의 성분이 1개 이상인 경우
            ingredient_guide['case'] = 'C05'
            ingredient = noxious_ingredients.pop(0)
            ingredient_guide['noxious_ingredient_name'] = ingredient.korean_name
            if noxious_ingredients:
                ingredient_guide['noxious_ingredient_count'] = len(noxious_ingredients)
        else:
            intermediate_risk_ingredients = list(filter(
                lambda x: (x.ewg_min is not None and x.ewg_min > 2) or (x.ewg_max is not None and x.ewg_max > 2),
                ingredients
            ))
            if intermediate_risk_ingredients:
                # 3-6 등급의 성분이 포함된 경우
                ingredient_guide['case'] = 'C04'
            else:
                safe_ingredients = list(filter(
                    lambda x: (x.ewg_min is not None and x.ewg_min >= 0) or (x.ewg_min is not None and x.ewg_min >= 0),
                    ingredients
                ))
                if safe_ingredients:
                    # 0-2 등급의 성분으로만 구성된 경우
                    ingredient_guide['case'] = 'C03'

        return ingredient_guide


service = ProductService()
