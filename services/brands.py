import re

from django.conf import settings
from django.db.models import Case, IntegerField
from django.db.models import F
from django.db.models import Q
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Substr

from libs.utils import local_now
from models.brands import Brand, BrandCategory, Brandbanner
from models.reviews import Review
from models.users import User


class BrandService:
    def search_brand_list(self, params, only_count=None):
        """
        브랜드 검색 ( EC API )
        """
        cursor = params.data.get('cursor')
        limit = params.data.get('limit')
        offset = (cursor - 1) * limit

        brand_name = params.data.get('name')

        brands = Brand.objects.filter(is_display=True)

        if brand_name:
            q = Q()
            word_list = re.findall('([\w.]+)', brand_name)
            if len(word_list) < 1:
                return []

            elif len(word_list) == 1:
                if len(word_list[0]) == 1:
                    q &= (Q(name__iexact=word_list[0]) | Q(phoneme__iexact=word_list[0]))
                    brands = brands.filter(q)
                else:
                    for sch_word in word_list:
                        brands = brands.extra(
                            where=["replace(brandTitle, ' ', '') LIKE %s OR brandTitleInitial LIKE %s "],
                            params=[sch_word + '%', sch_word + '%'])
            else:
                for sch_word in word_list:
                    brands = brands.extra(
                        where=["replace(brandTitle, ' ', '') LIKE %s OR brandTitleInitial LIKE %s "],
                        params=[sch_word + '%', sch_word + '%'])

        if only_count:
            return brands.count()

        brands = brands.order_by('name').distinct()
        brands = brands[offset: offset + limit + 1]

        return brands

    def get_brands(self, **kwargs):
        """
        브랜드 리스트 ( 검색 )
        """
        cursor = kwargs.get('cursor')
        limit = kwargs.get('limit')
        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit

        query = kwargs.get('query')

        brands = Brand.objects.filter(is_display=True)

        if query:
            q = Q()
            word_list = re.findall('([\w.]+)', query)
            if len(word_list) < 1:
                return []

            elif len(word_list) == 1:
                if len(word_list[0]) == 1:
                    q &= (Q(name__iexact=word_list[0]) | Q(phoneme__iexact=word_list[0]))
                    brands = brands.filter(q)
                else:
                    for sch_word in word_list:
                        brands = brands.extra(
                            where=[
                                "replace(brandTitle, ' ', '') LIKE %s "
                                "OR brandTitleInitial LIKE %s "
                            ],
                            params=[
                                '%' + sch_word + '%',
                                '%' + sch_word + '%'
                            ])
            else:
                for sch_word in word_list:
                    brands = brands.extra(
                        where=[
                            "replace(brandTitle, ' ', '') LIKE %s "
                            "OR brandTitleInitial LIKE %s "
                        ],
                        params=[
                            '%' + sch_word + '%',
                            '%' + sch_word + '%'
                        ])

            brands = brands.extra(select={
                'sort_key': 'CASE '
                            'WHEN ASCII(SUBSTRING(brandTitle,1)) BETWEEN 48 AND 57 THEN 3 '
                            'WHEN ASCII(SUBSTRING(brandTitle,1)) < 128 THEN 2 '
                            'ELSE 1 '
                            'END'
            })

            brands = brands.order_by(
                'sort_key', 'name'
            ).distinct()

        brands = brands[offset: offset + limit]

        return brands

    def get_all_brands(self, **kwargs):
        """
        전체 브랜드 리스트 *(initial 혹은 cursor 값으로 paging )
        """
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        brand_category_id = kwargs.get('brand_category_id')
        initial = kwargs.get('initial')

        brands = Brand.objects.filter(is_display=True)

        if initial:
            sch_filter = [
                None,
                Q(name__regex=r'(ㄱ|ㄲ)') | Q(name__gte='가', name__lt='나'),
                Q(name__regex=r'ㄴ') | Q(name__gte='나', name__lt='다'),
                Q(name__regex=r'(ㄷ|ㄸ)') | Q(name__gte='다', name__lt='라'),
                Q(name__regex=r'ㄹ') | Q(name__gte='라', name__lt='마'),
                Q(name__regex=r'ㅁ') | Q(name__gte='마', name__lt='바'),
                Q(name__regex=r'ㅂ') | Q(name__gte='바', name__lt='사'),
                Q(name__regex=r'(ㅅ|ㅆ)') | Q(name__gte='사', name__lt='아'),
                Q(name__regex=r'ㅇ') | Q(name__gte='아', name__lt='자'),
                Q(name__regex=r'(ㅈ|ㅉ)') | Q(name__gte='자', name__lt='차'),
                Q(name__regex=r'ㅊ') | Q(name__gte='차', name__lt='카'),
                Q(name__regex=r'ㅋ') | Q(name__gte='카', name__lt='타'),
                Q(name__regex=r'ㅌ') | Q(name__gte='타', name__lt='파'),
                Q(name__regex=r'ㅍ') | Q(name__gte='파', name__lt='하'),
                Q(name__regex=r'ㅎ') | Q(name__gte='하'),
                Q(name__regex=r'^[a-zA-Z]') | Q(name__regex=r'^[0-9]')
            ]
            brands = brands.filter(sch_filter[initial])

        if brand_category_id:
            brands = brands.filter(categories__id=brand_category_id)

        brands = brands.annotate(
            init=Substr('name', 1),
        )
        brands = brands.annotate(
            custom_order=Case(
                When(Q(init__gte=chr(48)) & Q(init__lt=chr(57)), then=Value(3)),
                When(Q(init__lt=chr(128)), then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )

        brands = brands.order_by('custom_order', 'name').distinct()

        if not initial:
            cursor = int(cursor or 1)
            offset = (cursor - 1) * limit
            brands = brands.all()[offset: offset + limit + 1]

        if not brands:
            return {
                'list': [],
                'next_offset': None,
            }

        if not len(brands):
            return {
                'list': [],
                'next_offset': None,
            }

        if len(brands) == limit + 1 and not initial:
            results = list(brands)
            next_offset = cursor + 1
            del results[-1]
        else:
            results = list(brands)
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
        }

    def _make_categories_response(self, query_set):
        """
        브랜드 카테고리 리스트를 응답 형태로 가공함
        """
        categories = list()
        categories.append({
            'id': 0,
            'name': '전체 브랜드',
            'brands': [
                {'id': 0, 'name': '브랜드명'}
            ]
        })

        for row in query_set.iterator():
            b_main = True

            for category in categories:
                if row['brand_category_id'] == category['id']:
                    category['brands'].append({'id': row['brand_id'], 'name': row['brand_name']})
                    categories[0]['brands'].append(
                        {'id': row['brand_id'], 'name': row['brand_name']})
                    b_main = False
                    break

            if b_main:
                categories.append({
                    'id': row['brand_category_id'],
                    'name': row['brand_category_name'],
                    'brands': [
                        {'id': 0, 'name': '브랜드명'},
                        {'id': row['brand_id'], 'name': row['brand_name']}
                    ]
                })

        return categories

    def get_user_reviews_categories(self, user_id):
        """
        회원이 작성한 리뷰가 포함된 브랜드 카테고리 리스트
        리스트 필터의 데이터
        """
        query_set = Review.objects.filter(
            user_id=user_id,
            is_display=True,
            product__is_display=True
        )
        query_set = query_set.filter(
            product__brand__is_display=True,
            product__brand__categories__is_display=True
        )
        query_set = query_set.annotate(
            brand_id=F('product__brand_id'),
            brand_name=F('product__brand__name'),
            brand_category_id=F('product__brand__categories'),
            brand_category_name=F('product__brand__categories__name')
        )
        query_set = query_set.values(
            'brand_id', 'brand_name', 'brand_category_id', 'brand_category_name'
        )
        query_set = query_set.distinct()

        return self._make_categories_response(query_set)

    def get_user_wishes_categories(self, user_id):
        """
        회원의 위시리스트의 제품이 포함된 브랜드 카테고리 리스트
        리스트 필터의 데이터
        """

        query_set = User.objects.get(id=user_id).wishes.visible()
        query_set = query_set.filter(
            brand__is_display=True,
            brand__categories__is_display=True
        )
        query_set = query_set.annotate(
            brand_name=F('brand__name'),
            brand_category_id=F('brand__categories'),
            brand_category_name=F('brand__categories__name')
        )
        query_set = query_set.values(
            'brand_id', 'brand_name', 'brand_category_id', 'brand_category_name'
        )
        query_set = query_set.distinct()

        return self._make_categories_response(query_set)

    def get_all_brand_categorise(self):
        """
        전체 브랜드 카테고리 리스트
        """
        brand_categories = BrandCategory.objects.filter(
            is_display=True
        ).order_by(
            'seq'
        )

        file_dir = '/home/glowmee/upload/api'
        file_name = 'all.png'

        res = list(brand_categories)

        res.insert(
            0,
            {
                'id': 0,
                'name': '전체',
                'brand_category_image_160': '{}{}/{}'.format(
                    settings.CDN, file_dir, file_name
                ),
            })

        return res

    def get_recommend_brands(self):
        """
        추천 브랜드
        """
        now = local_now().strftime('%Y%m%d%H%M%S')

        brands = Brand.objects.filter(
            is_display=True,
            is_recommended=True,
            start_date__lt=now,
            end_date__gt=now,
        ).order_by(
            'seq',
            '?'
        )

        return brands

    def get_product_category_rank_categories(self, category_id):
        """
        브랜드 카테고리 리스트 ( sub_category id )
        """
        query_set = BrandCategory.objects.filter(
            is_display=True,
            brand__product__categories=category_id,
            brand__product__categories__is_display=True,
        ).prefetch_related(
            'brand_set'
        )
        query_set = query_set.annotate(
            brand_id=F('brand'),
            brand_name=F('brand__name'),
            brand_category_id=F('id'),
            brand_category_name=F('name')
        )

        query_set = query_set.values(
            'brand_id', 'brand_name', 'brand_category_id', 'brand_category_name'
        )
        query_set = query_set.distinct()

        return self._make_categories_response(query_set)

    def get_brand_banner(self, brand_id):
        """
        브랜드 배너 정보를 포함한 브랜드 정보
        (facebook, twitter, youtube, homepage, ...)
        """
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return None

        now = local_now().strftime('%Y%m%d%H%M%S')
        banners = Brandbanner.objects.filter(
            is_display=True,
            brand_id=brand_id,
            brand__start_date__lt=now,
            brand__end_date__gt=now,
        )
        setattr(brand, 'banners', banners)
        if banners:
            setattr(brand, 'banner_ratio', 0.42)
        else:
            setattr(brand, 'banner_ratio', 0)

        return brand


service = BrandService()
