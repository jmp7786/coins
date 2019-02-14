"""
제품 랭킹관련 로직 정의
카테고리별 제품 랭킹 리스트
브랜드별 제품 랭킹 리스트
스토어별 제품 랭킹 리스트
"""
import random

from db.raw_queries import (
    get_monthly_product_by_sub_category, get_editor_product_by_sub_category,
    get_prodcuts_ranking_by_brand_id_with_user_conditions, get_prodcuts_ranking_by_brand_id_without_user_conditions,
    get_products_ranking_by_brand_id, get_prodcuts_by_brand_id, get_prodcuts_by_store_id,
    get_prodcuts_ranking_by_category_id_with_user_conditions,
    get_prodcuts_ranking_by_category_id_without_user_conditions, get_products_ranking_by_category_id,
    get_prodcuts_by_category_id)
from models.products import Product, WeeklyRanking


class RankingService:
    def get_products_ranking_by_category_id(self, **kwargs):
        """
        카테고리별 제품 순위 리스트
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        custom_conditions = ['gender', 'age', 'skin_type', 'rank_term']
        etc_conditions = ['brand_id', 'brand_category_id', 'max_price', 'min_price', 'keywords', 'is_commerce']
        order = kwargs.get('order')

        products_count = None
        if order == 'rank':
            is_custom_conditions = False
            for key in custom_conditions:
                if kwargs.get(key) != 'all':
                    is_custom_conditions = True
                    break

            if is_custom_conditions:
                products = get_prodcuts_ranking_by_category_id_with_user_conditions(**kwargs)
            else:
                is_etc_conditions = False
                for key in etc_conditions:
                    if kwargs.get(key):
                        is_etc_conditions = True
                        break

                if is_etc_conditions:
                    products = get_prodcuts_ranking_by_category_id_without_user_conditions(**kwargs)
                else:
                    products = get_products_ranking_by_category_id(**kwargs)
        else:
            results = get_prodcuts_by_category_id(**kwargs)
            products = results.get('products')
            products_count = results.get('total_count')

        # response format
        for product in products:
            product['rank'] = product.get('product_rank')
            product['brand'] = dict()
            product['brand']['id'] = product.get('brand_id')
            product['brand']['name'] = product.get('brand_name')
            product['brand']['brand_image'] = product.get('brand_image')
            product['brand']['brand_image_160'] = product.get('brand_image_160')

            goods_count = product.get('goods_count')
            if goods_count:
                product['productgoods'] = dict()
                product['productgoods']['goods_count'] = product.get('goods_count')
                product['productgoods']['min_price'] = product.get('min_price')
                product['productgoods']['max_price'] = product.get('max_price')
            else:
                product['productgoods'] = None

        if not len(products):
            return {
                'list': [],
                'next_offset': None,
                'products_count': products_count
            }

        if len(products) == limit + 1:
            next_offset = int(cursor or 1) + 1
            del products[-1]
        else:
            next_offset = None

        return {
            'list': products,
            'next_offset': next_offset,
            'products_count': products_count
        }

    def get_recommend_product_by_sub_category_id(self, **kwargs):
        """
        sub 카테고리 아이디로 추천 제품 중 랜덤으로 하나 가져오기
        """

        sub_category_id = kwargs.get('category_id')
        monthly_product = get_monthly_product_by_sub_category(sub_category_id)
        editor_product = get_editor_product_by_sub_category(sub_category_id)

        recommend_products = list()
        if monthly_product:
            recommend_products.append(monthly_product)

        if editor_product:
            recommend_products.append(editor_product)

        product = None
        if len(recommend_products) > 0:
            product = random.choice(recommend_products)

            # response format
            product['brand'] = dict()
            product['brand']['id'] = product.get('brand_id')
            product['brand']['name'] = product.get('brand_name')
            product['brand']['brand_image'] = product.get('brand_image')
            product['brand']['brand_image_160'] = product.get('brand_image_160')

            goods_count = product.get('goods_count')
            if goods_count:
                product['productgoods'] = dict()
                product['productgoods']['goods_count'] = product.get('goods_count')
                product['productgoods']['min_price'] = product.get('min_price')
                product['productgoods']['max_price'] = product.get('max_price')
            else:
                product['productgoods'] = None

        return product

    def get_products_ranking_by_brand_id(self, **kwargs):
        """
        브랜드별 제품 순위 리스트
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        custom_conditions = ['gender', 'age', 'skin_type', 'rank_term']
        etc_conditions = ['main_category_id', 'sub_category_id', 'is_commerce']
        order = kwargs.get('order')

        products_count = None
        if order == 'rank':
            is_custom_conditions = False
            for key in custom_conditions:
                if kwargs.get(key) != 'all':
                    is_custom_conditions = True
                    break

            if is_custom_conditions:
                products = get_prodcuts_ranking_by_brand_id_with_user_conditions(**kwargs)
            else:
                is_etc_conditions = False
                for key in etc_conditions:
                    if kwargs.get(key):
                        is_etc_conditions = True
                        break

                if is_etc_conditions:
                    products = get_prodcuts_ranking_by_brand_id_without_user_conditions(**kwargs)
                else:
                    products = get_products_ranking_by_brand_id(**kwargs)
        else:
            results = get_prodcuts_by_brand_id(**kwargs)
            products = results.get('products')
            products_count = results.get('total_count')

        # response format
        for product in products:
            product['rank'] = product.get('product_rank')
            product['brand'] = dict()
            product['brand']['id'] = product.get('brand_id')
            product['brand']['name'] = product.get('brand_name')
            product['brand']['brand_image'] = product.get('brand_image')
            product['brand']['brand_image_160'] = product.get('brand_image_160')

            goods_count = product.get('goods_count')
            if goods_count:
                product['productgoods'] = dict()
                product['productgoods']['goods_count'] = product.get('goods_count')
                product['productgoods']['min_price'] = product.get('min_price')
                product['productgoods']['max_price'] = product.get('max_price')
            else:
                product['productgoods'] = None

        if not len(products):
            return {
                'list': [],
                'next_offset': None,
                'products_count': products_count
            }

        if len(products) == limit + 1:
            next_offset = int(cursor or 1) + 1
            del products[-1]
        else:
            next_offset = None

        return {
            'list': products,
            'next_offset': next_offset,
            'products_count': products_count
        }

    def get_products_ranking_by_store_id(self, **kwargs):
        """
        스토어별 제품 순위 리스트
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        results = get_prodcuts_by_store_id(**kwargs)

        products = results.get('products')
        products_count = results.get('total_count')

        # response format
        for product in products:
            product['rank'] = product.get('product_rank')
            product['brand'] = dict()
            product['brand']['id'] = product.get('brand_id')
            product['brand']['name'] = product.get('brand_name')
            product['brand']['brand_image'] = product.get('brand_image')
            product['brand']['brand_image_160'] = product.get('brand_image_160')

            goods_count = product.get('goods_count')
            if goods_count:
                product['productgoods'] = dict()
                product['productgoods']['goods_count'] = product.get('goods_count')
                product['productgoods']['min_price'] = product.get('min_price')
                product['productgoods']['max_price'] = product.get('max_price')
            else:
                product['productgoods'] = None

        if not len(products):
            return {
                'list': [],
                'next_offset': None,
                'products_count': products_count
            }

        if len(products) == limit + 1:
            next_offset = int(cursor or 1) + 1
            del products[-1]
        else:
            next_offset = None

        return {
            'list': products,
            'next_offset': next_offset,
            'products_count': products_count
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
            'brand'
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

    def get_weekly_ranking_products(self, **kwargs):
        """
        명예의 전당 제품 리스트 (일정 주간이상 1위를 유지한 제품 리스트)
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        weekly_count = kwargs.get('weekly_count')

        products = WeeklyRanking.objects.filter(
            weekly_count__gte=weekly_count
        ).select_related(
            'product', 'product__brand', 'sub_category'
        ).extra(
            select={'is_top': "IF((SELECT MAX(weeklyCount) FROM weeklyRanking) = weeklyCount, 1, 0)"}
        ).order_by(
            '-weekly_count'
        )

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
            next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }


service = RankingService()
