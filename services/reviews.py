import re
import math
import json
from datetime import datetime, timedelta
from enum import Enum

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models import Q, Count, Sum
from django.utils import timezone

from backends.api import exceptions
from cash_db.redis_utils import redis_get_exists_table, get_redis_tables, get_user_review_info, get_user_rank,\
    period_zincrby, period_hget, period_hset, period_zcard, period_zrem
from libs.elasticsearch.reviews import elasticsearch_reviews
from libs.utils import local_now, iso8601, get_age_range, utc_now
from models.common_codes import CommonCodeValue
from models.messages import MessageBox, MessageCategory, MessageCheck
from models.product_goods import ProductGoods
from models.report_reviews import ReportReview
from models.reviews import Review, Reviewlike, Review_first_log
from models.tags import TagObject
from models.users import Gender, SkinTypeCode, User
from models.points import Point

class Sort(Enum):
    like_desc = 'popular'
    like_asc = 'unpopular'
    create_date_desc = 'latest'
    create_date_asc = 'oldest'


class ReviewService:
    query_set = Review.objects.filter(is_display=True)
    list_type = None

    def setter(self, **kwargs):
        user_id = kwargs.get('user_id')
        product_id = kwargs.get('product_id')

        if user_id and product_id:
            raise ValueError

        self.query_set = Review.objects.filter(is_display=True)
        self.list_type = None

        if user_id:
            # 유저를 기반으로 리뷰 리스트
            self.query_set = self.query_set.filter(user=user_id)
            self.list_type = 'user_reviews'

        if product_id:
            # 제품을 기반으로 리뷰 리스트
            self.query_set = self.query_set.filter(product=product_id)
            self.list_type = 'product_reviews'

    def _set_conditions(self, query_set, **kwargs):
        """
        파라미터를 가지고 쿼리 셋의 조건을 세팅한다.
        """
        if self.list_type == 'product_reviews':
            return self._set_product_detail_conditions(query_set, **kwargs)
        elif self.list_type == 'user_reviews':
            return self._set_user_profile_conditions(query_set, **kwargs)

        query_set = self._set_reviews_conditions(query_set, **kwargs)

        return query_set

    def _set_reviews_conditions(self, query_set, **kwargs):
        """
        리뷰 리스트 검색 필터
        """
        gender = kwargs.get('gender')
        age = kwargs.get('age')
        skin_type = kwargs.get('skin_type')
        contents = kwargs.get('query')
        rating = kwargs.get('rating')
        main_category_id = kwargs.get('main_category_id')
        sub_category_id = kwargs.get('sub_category_id')

        is_commerce = kwargs.get('is_commerce')

        # basic
        base = query_set.filter(
            Q(state='N'),
            (Q(user__is_blinded=0) | Q(user__isnull=True)),
            (Q(product__is_display=True) | Q(product=None))
        )

        if rating and rating != 'all':
            points = rating.split(",")
            base = base.filter(rating__in=points)

        if gender and gender != 'all':
            base = base.filter(user___gender=Gender[gender].value)

        if skin_type and skin_type != 'all':
            skin_types = skin_type.split(",")
            skin_types = [SkinTypeCode[s].value for s in skin_types]
            base = base.filter(user___skin_type__in=skin_types)

        if contents:
            base = base.filter(contents__icontains=contents)

        if age and age != 'all':
            min_year, max_year = get_age_range(age)
            base = base.filter(user__birth_year__range=(min_year, max_year))

        if sub_category_id and sub_category_id != 0:
            base = base.filter(product__productcategory__sub_category=sub_category_id)
        else:
            if main_category_id and main_category_id != 0:
                base = base.filter(product__productcategory__sub_category__main_category=main_category_id)

        if is_commerce:
            base = base.filter(product__productgoods__goods_count__gt=0)

        query_set = base

        return query_set

    def _set_product_detail_conditions(self, query_set, **kwargs):
        """
        제품 상세 리뷰 리스트 검색 필터
        """
        state = kwargs.get('state')

        gender = kwargs.get('gender')
        age = kwargs.get('age')
        skin_type = kwargs.get('skin_type')
        contents = kwargs.get('contents')
        rating = kwargs.get('rating')

        base = query_set

        # 정상 상태인 리뷰에서만 필터 검색이 가능하다.
        if state == 'normal':
            base = base.filter(Q(user__is_blinded=0) & Q(state='N'))

            if rating and rating != 'all':
                points = rating.split(",")
                base = base.filter(rating__in=points)

            if gender and gender != 'all':
                base = base.filter(user___gender=Gender[gender].value)

            if skin_type and skin_type != 'all':
                skin_types = skin_type.split(",")
                skin_types = [SkinTypeCode[s].value for s in skin_types]
                base = base.filter(user___skin_type__in=skin_types)

            if contents:
                base = base.filter(contents__icontains=contents)

            if age and age != 'all':
                min_year, max_year = get_age_range(age)
                base = base.filter(user__birth_year__range=(min_year, max_year))
        else:
            base = base.filter(Q(user__is_blinded__gt=0) | ~Q(state='N'))

        query_set = base

        return query_set

    def _set_user_profile_conditions(self, query_set, **kwargs):
        """
        회원 프로필 리뷰 리스트 필터
        """
        # 유저 프로필 > 로그인 유저 아이디
        request_user_id = kwargs.get('request_user_id')
        user_id = kwargs.get('user_id')

        rating = kwargs.get('rating')
        main_category_id = kwargs.get('main_category_id')
        sub_category_id = kwargs.get('sub_category_id')
        brand_category_id = kwargs.get('brand_category_id')
        brand_id = kwargs.get('brand_id')

        is_commerce = kwargs.get('is_commerce')

        base = query_set

        if rating and rating != 'all':
            points = rating.split(",")
            base = base.filter(rating__in=points)

        if sub_category_id and sub_category_id != 0:
            base = base.filter(product__productcategory__sub_category=sub_category_id)
        else:
            if main_category_id and main_category_id != 0:
                base = base.filter(product__productcategory__sub_category__main_category=main_category_id)

        if brand_id and brand_id != 0:
            base = base.filter(product__brand=brand_id)
        else:
            if brand_category_id and brand_category_id != 0:
                base = base.filter(product__brand__brandcategories__brand_category=brand_category_id)

        if is_commerce:
            base = base.filter(product__productgoods__goods_count__gt=0)

        # 본인의 프로필이 아닐 경우 블라인드 리뷰는 필터링
        if request_user_id != user_id:
            base = base.filter(Q(user__is_blinded=0) & Q(state='N'))
        query_set = base

        return query_set

    def _set_sorting(self, query_set, **kwargs):
        """
        파라미터를 가지고 쿼리 셋의 정렬을 세팅한다.
        """
        order = kwargs.get('order')

        default_sort = Sort.create_date_desc.value

        if self.list_type == 'product_reviews':
            state = kwargs.get('state')
            if state == 'normal':
                default_sort = Sort.like_desc.value

        sort = Sort[order].value if order else default_sort

        base = query_set

        if sort == 'popular':
            base = base.order_by('-like_count', '-_created_at')
        elif sort == 'unpopular':
            base = base.order_by('like_count', '-_created_at')
        elif sort == 'latest':
            base = base.order_by('-_created_at')
        elif sort == 'oldest':
            base = base.order_by('_created_at')

        query_set = base

        return query_set, sort

    def get_list(self, *, only_count=False, **kwargs):
        """
        리뷰 리스트
        """

        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        rating_points = None
        like_count = None

        # conditions by parameters
        base = self._set_conditions(self.query_set, **kwargs)

        if self.list_type == 'product_reviews':
            if only_count:
                base = base.force_index('reviewcomment_product_count_index')
            else:
                base = base.force_index('reviewcomment_product_review_index')

            state = kwargs.get('state')
            # 정상 상태인 리뷰에서만 필터 검색이 가능하다.
            if state == 'normal':
                rating_points = base.values('rating').all().annotate(count=Count('id'))

        if only_count:
            return base.all().count()

        if self.list_type == 'user_reviews':
            if cursor is None:
                results = base.all().aggregate(likes=Sum(F('like_count')))
                like_count = results['likes']

        # sorting by parameters
        base, sort = self._set_sorting(base, **kwargs)

        base = base.select_related(
            'user', 'product', 'product__brand', 'product__productgoods'
        )

        if cursor and sort == 'latest':
            base = base.filter(id__lt=cursor)
            results = base.all()[:limit + 1]
        else:
            cursor = int(cursor or 1)
            offset = (cursor - 1) * limit
            results = base.all()[offset: offset + limit + 1]

        if not results:
            return {
                'list': [],
                'next_offset': None,
                'rating_points': None,
                'like_count': 0
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
                'rating_points': None,
                'like_count': 0
            }

        if len(results) == limit + 1:
            results = list(results)
            if sort == 'latest':
                next_offset = results[-2].id
            else:
                next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset,
            'rating_points': rating_points,
            'like_count': like_count
        }

    def get_list_elacticsearch(self, **kwargs):
        """
        리뷰 리스트 (ElasticSearch)
        """
        # parameter

        es_must = list()
        es_must.append({'match': {'isDisplay': 1}})
        es_must.append({'match': {'isBlind': 0}})
        es_must.append({'match': {'productIsDisplay': 1}})

        # 성별
        gender = kwargs.get('gender')

        if gender:
            if gender == 'm':
                es_must.append({'match': {'gender': 6}})
            elif gender == 'f':
                es_must.append({'match': {'gender': 7}})

        # 연령
        age = kwargs.get('age')
        if age:
            if age != 'all':
                should = list()
                age_arr = age.split(',')
                for val in age_arr:
                    min_year, max_year = get_age_range(val)
                    should.append({'range': {'birthYear': {'gte': min_year, 'lte': max_year}}})
                es_must.append({'bool': {'should': should}})

        # 피부타입
        skin_type = kwargs.get('skin_type')
        if skin_type:
            if skin_type != 'all':
                skin_list = list()
                skin_arr = skin_type.split(',')

                skin_map_desc = {
                    "dry": 8,
                    "oily": 9,
                    "normal": 10,
                    "mix": 11,
                    "sensitive": 12,
                }

                for val in skin_arr:
                    skin_list.append({'term': {'skinType': skin_map_desc.get(val)}})

                es_must.append({'bool': {'should': skin_list}})

        # 평점
        rating = kwargs.get('rating')
        if rating:
            if rating != 'all':
                rating_list = list()
                rating_arr = rating.split(',')

                for val in rating_arr:
                    rating_list.append({'term': {'rating': val}})

                es_must.append({'bool': {'should': rating_list}})

        # 제품 카테고리
        sub_category_id = kwargs.get('sub_category_id')
        main_category_id = kwargs.get('main_category_id')

        if sub_category_id is not None:
            es_must.append({'match': {'secondCategoryList': '[' + str(sub_category_id) + ']'}})
        elif main_category_id is not None:
            es_must.append({'match': {'firstCategoryList': '[' + str(main_category_id) + ']'}})

        # 브랜드 아이디
        brand_id = kwargs.get('brand_id')
        if brand_id:
            es_must.append({'match': {'idBrand': brand_id}})

        # 구매가능
        is_commerce = kwargs.get('is_commerce')
        if is_commerce:
            es_must.append({'range': {'goods_count': {'gt': 0}}})

        # 검색어
        query = kwargs.get('query')
        if query:
            query_row = query.split()
            query_string = list()

            for q in query_row:
                if q[0] != '#' and q[0] != '@':
                    q = ''.join(re.findall('([\w.]+)', q))
                    q = q.lower()
                    query_string.append(
                        {
                            "query_string": {
                                "fields": ['brandTitle', 'productTitle', 'reviewText.koreanText'],
                                "query": q,
                                "default_operator": "AND"
                            }
                        }
                    )

                elif q[0] == '#' and len(q) > 1:
                    q = ''.join(re.findall('([\w.]+)', q[1:]))
                    es_must.append(
                        {'term': {'tag': q}}
                    )

                elif q[0] == '@' and len(q) > 1:
                    q = ''.join(re.findall('([\w.]+)', q[1:]))
                    q = q.lower()
                    es_must.append({"query_string": {"fields": ["nickName"], "query": q, "default_operator": "AND"}})

            if len(query_string) > 0:
                es_must.append(
                    {"bool": {"must": query_string}}
                )

        # 정렬순서
        sort = kwargs.get('order')
        if sort == 'like_desc':
            order = "likeCount:desc"
        elif sort == 'like_asc':
            order = "likeCount:asc"
        elif sort == 'create_date_asc':
            order = "create_date:asc"
        else:
            order = "create_date:desc"

        cursor = kwargs.get('cursor')
        limit = kwargs.get('limit', 20)

        if cursor and order == "create_date:desc":
            es_must.append({'range': {"idreviewcomment": {"lt": cursor}}})
            body = {'query': {'bool': {'must': es_must}}}
            es_data = elasticsearch_reviews.get_list(order, limit + 1, body)
        else:
            offset = (int(cursor or 1) - 1) * limit
            body = {'query': {'bool': {'must': es_must}}}
            es_data = elasticsearch_reviews.get_list(order, limit + 1, body, offset)

        skin_map = {
            8: "건성",
            9: "지성",
            10: "중성",
            11: "복합성",
            12: "민감성",
        }

        gender_map = {
            6: "m",
            7: "f"
        }

        review_list = []
        product_id_list = []
        for hit in es_data['hits']:
            es_item = hit["_source"]
            # prodcut image
            if es_item["productFileSaveName"] is not None and es_item["productFileSaveName"] != "":
                product_image = "{}{}/{}".format(
                    settings.CDN, es_item["productFileDir"], es_item["productFileSaveName"]
                )
                file_split = es_item["productFileSaveName"].split('.')
                product_image_160 = "{}{}/{}_160.{}".format(
                    settings.CDN, es_item["productFileDir"], file_split[0], file_split[1]
                )
            else:
                product_image = None
                product_image_160 = None

            # register image
            if es_item["registerFileSaveName"] is not None and es_item["registerFileSaveName"] != "":
                register_image = "{}{}/{}".format(
                    settings.CDN, es_item["registerFileDir"], es_item["registerFileSaveName"]
                )
                file_split = es_item["registerFileSaveName"].split('.')
                register_image_160 = "{}{}/{}_160.{}".format(
                    settings.CDN, es_item["registerFileDir"], file_split[0], file_split[1]
                )
            else:
                register_image = None
                register_image_160 = None

            item = dict()
            item['id'] = int(es_item["idreviewcomment"])
            item['rating'] = int(es_item["rating"])
            item['contents'] = es_item["reviewText"]
            item['like_count'] = int(es_item["likeCount"])
            item['is_evaluation'] = int(es_item["isEvaluation"])
            item['created_at'] = iso8601(datetime.strptime(es_item["create_date"], "%Y%m%d%H%M%S"))

            item['user'] = dict()
            item['user']['id'] = int(es_item["idRegister"])
            item['user']['email'] = None
            item['user']['nickname'] = es_item["nickName"]
            item['user']['profile_image'] = register_image_160
            item['user']['gender'] = gender_map.get(int(es_item["gender"] if es_item['gender'] is not None else 0))
            item['user']['skin_type'] = skin_map.get(int(es_item["skinType"] if es_item['skinType'] is not None else 0))
            item['user']['birth_year'] = int(es_item["birthYear"]) if es_item['birthYear'] is not None else None
            item['user']['rank'] = int(es_item["registerRank"])
            item['user']['is_blinded'] = int(es_item["isBlind"])

            item['product'] = dict()
            item['product']['id'] = int(es_item["idProduct"])
            item['product']['name'] = es_item["productTitle"]
            item['product']['product_image_160'] = product_image_160
            item['product']['brand'] = dict()
            item['product']['brand']['id'] = int(es_item["idBrand"])
            item['product']['brand']['name'] = es_item["brandTitle"]

            product_id_list.append(item['product']['id'])

            review_list.append(item)

        for goods in ProductGoods.objects.filter(product_id__in=product_id_list):
            for review in review_list:
                if review['product']['id'] == goods.product_id:
                    review['product']['productgoods'] = goods

        row = es_data['total']

        if len(review_list) == limit + 1:
            if order == "create_date:desc":
                next_offset = review_list[-2].get('id')
            else:
                next_offset = int(cursor or 1) + 1
            del review_list[-1]
        else:
            next_offset = None

        return {"review_list": review_list, "total_count": row, "next_offset": next_offset}

    def get_my_review(self, user_id, product_id, **kwargs):
        gender = kwargs.get('gender')
        age = kwargs.get('age')
        skin_type = kwargs.get('skin_type')
        contents = kwargs.get('contents')
        rating = kwargs.get('rating')

        base = Review.objects. \
            filter(is_display=True, product=product_id, user=user_id)

        if rating and rating != 'all':
            points = rating.split(",")
            base = base.filter(rating__in=points)

        if gender and gender != 'all':
            base = base.filter(user___gender=Gender[gender].value)

        if skin_type and skin_type != 'all':
            skin_types = skin_type.split(",")
            skin_types = [SkinTypeCode[s].value for s in skin_types]
            base = base.filter(user___skin_type__in=skin_types)

        if contents:
            base = base.filter(contents__icontains=contents)

        if age and age != 'all':
            min_year, max_year = get_age_range(age)
            base = base.filter(user__birth_year__range=(min_year, max_year))

        return base.first()

    def delete_tags(self, review_id):
        """
        태그와 리뷰와의 연결 제거
        """
        object_tags = TagObject.objects.select_related('tag').filter(type='review', object_id=review_id)
        now = local_now().strftime('%Y%m%d%H%M%S')
        # tag count update
        for _obj in object_tags:
            _obj.tag.count -= 1
            _obj.tag.modified_date = now
            _obj.tag.save()
        # delete tag mapping
        if object_tags.exists():
            object_tags.delete()

    def create_report(self, review_id, user_id, client_ip, report_type, contents, editor_id):
        """
        리뷰 신고
        """
        ReportReview(review_id=review_id, user_id=user_id, ip_address=client_ip, editor_id=editor_id,
                     review_report_type_cd=report_type, contents=contents).save()

    def has_report(self, review_id, user_id):
        """
        리뷰 신고 확인
        """
        return ReportReview.objects.filter(review_id=review_id, user_id=user_id, state='W').exists()

    def get_report_types(self, common_code):
        """
        리뷰 신고 유형 목록
        """
        common_code_values = CommonCodeValue.objects.filter(common_code=common_code)
        common_code_values = common_code_values.order_by('seq')
        common_code_values = common_code_values.values('value_code', 'value_name')
        return common_code_values

    @transaction.atomic
    def make_like_message(self, review_id, register_id, created_at=None):
        """
        좋아요 알림함 메세지 생성
        """
        review = Review.objects.select_related(
            'user', 'product', 'product__brand'
        ).get(
            id=review_id
        )

        if not created_at:
            created_at = utc_now()
        two_week_ago = created_at.astimezone(tz=timezone.get_current_timezone()) - timedelta(days=14)

        obj, created = MessageBox.objects.get_or_create(
            user_id=review.user_id,
            category=MessageCategory.objects.get(name='좋아요'),
            reference_id=review_id,
            is_active=True
        )

        if created:
            register = User.objects.get(id=register_id)
            obj.message = "{}님이 내 리뷰를 좋아합니다.\n{} - {}".format(
                register.nickname, review.product.brand.name, review.product.name
            )
            obj.created_at = created_at
            obj.updated_at = created_at
            obj.save()
        else:
            MessageCheck.objects.filter(user_id=review.user_id, message=obj.id).delete()
            likes = Reviewlike.objects.filter(
                writer=review.user, product=review.product,
                create_date__gte=two_week_ago.strftime('%Y%m%d%H%M%S'),
            )
            likes = likes.filter(
                create_date__gte=obj.created_at.astimezone(tz=timezone.get_current_timezone()).strftime('%Y%m%d%H%M%S')
            ).order_by(
                'create_date'
            )
            likes = likes.values(
                'register__nickname',
            )
            count = likes.count()
            if count == 2:
                nickname1 = likes[1].get('register__nickname')
                nickname2 = likes[0].get('register__nickname')
                obj.message = "{}, {}님이 내 리뷰를 좋아합니다.\n{} - {}".format(
                    nickname1, nickname2, review.product.brand.name, review.product.name
                )

            elif count > 2:
                likes = list(likes)
                nickname = likes[-1].get('register__nickname')
                obj.message = "{}님 외 {}명이 내 리뷰를 좋아합니다.\n{} - {}".format(
                    nickname, count - 1, review.product.brand.name, review.product.name
                )
            obj.updated_at = created_at
            obj.save()
    
    def get_review_count(self,id):
        return Review.objects.filter(
            user__id=id, state='N', when_seceded=0, is_display=1).count()
    
    def get_this_week_review_count(self,id):
        return Review.objects.filter(
            _created_at__gte=kst_last_week_friday_18_00().strftime(
                '%Y%m%d%H%M%S'), user__id=id, state='N',
            when_seceded=0, is_display=1).count()
    
    def update_rank_point(self, period, user_id, is_multiple, is_first):
        result = None
        
        # 현재 랭킹을 가져온다.
        previous_rank_info = get_user_rank(period, user_id)

        points = self.get_review_points()
        # 점수를 계산한 후 반영한다.
        # 기본 10 점 + review_count가 3으로 떨어지면 3 점 + 처음 리뷰 3 점
        point = points['review_point']
        bonus = (is_multiple * points['multiple_bonus_point']) + \
                (is_first * points['first_bonus_point'])

        point_and_bonus = point + bonus
        is_first_review = False
        
        if previous_rank_info is not None:
            previous_rank = previous_rank_info['rank']
            
            # 변경 사항은 원본과 복사본 모두에 적용한다.
            # 랭킹 포인트 업데이트
            period_zincrby(period, user_id, point_and_bonus)
            # 업데이트 후 랭킹을 다시 가져온다.
            updated_rank_info = get_user_rank(period, user_id)
            
            updated_rank = updated_rank_info['rank']
            updated_score = updated_rank_info['score']
            updated_ratio = updated_rank_info['ratio']
            upgrade_range = previous_rank - updated_rank
        else:
            is_first_review = True
            period_zincrby(period, user_id, point_and_bonus)
            updated_rank_info = get_user_rank(period, user_id)
            total_count = period_zcard(period)
            
            updated_rank = updated_rank_info['rank']
            updated_score = updated_rank_info['score']
            updated_ratio = updated_rank_info['ratio']
            upgrade_range = total_count - updated_rank
            
            
        if is_first_review:
            result = dict()
            result['rank'] = updated_rank
            result['score'] = updated_score
            result['upgrade_range'] = upgrade_range
            result['ratio'] = updated_ratio
            
        elif upgrade_range is not 0:
            # 팝업을 띄울 것인지 조절한다.
            is_insert = False
            
            if 1 <= updated_rank < 10:
                if updated_rank in (5, 3, 2, 1):
                    is_insert = True
            elif 10 <= updated_rank < 100:
                if previous_rank // 10 != updated_rank // 10:
                    is_insert = True
            elif 100 <= updated_rank < 1000:
                if previous_rank // 100 != updated_rank // 100:
                    is_insert = True
            elif 1000 <= updated_rank < 10000:
                if previous_rank // 1000 != updated_rank // 1000:
                    is_insert = True
            else:
                if previous_rank // 10000 != updated_rank // 10000:
                    is_insert = True
            
            if is_insert is True:
                result = dict()
                result['rank'] = updated_rank
                result['score'] = updated_score
                result['upgrade_range'] = upgrade_range
                result['ratio'] = updated_ratio
        
            
        return result
    
    def get_rewards(self, multiple_all, is_first):
        points = self.get_review_points()
        
        result = list()
        
        default_reward = dict({
                'title':'리뷰쓰기 완료',
                'point':points['review_point']
            })
        
        result.append(default_reward)
        
        bonus = 0
        if multiple_all is True:
            bonus += points['multiple_bonus_point']
        if is_first is True:
            bonus += points['first_bonus_point']
        
        if bonus > 0:
            result.append(dict({
                'title': '보너스',
                'point': bonus
            }))
        
        return result if len(result) > 0 else None

    def get_review_points(self):
        result = dict()
        points = Point.objects.filter(name__in=(
            'review_point', 'first_bonus_point', 'multiple_bonus_point')).all()
        for r in points:
            _point = r.point
        
            if r.event_start_date and r.event_end_date and r.event_point and \
                    r.event_start_date < utc_now() < r.event_end_date:
                _point = r.event_point
        
            if r.name == 'review_point':
                result['review_point'] = _point
        
            if r.name == 'multiple_bonus_point':
                result['multiple_bonus_point'] = _point
        
            if r.name == 'first_bonus_point':
                result['first_bonus_point'] = _point
    
        return result
    
    def reset_rank(self,user_id):
        """
        rank 를 리셋한다.
        :return:
        """
        period_zrem('all',user_id)
        period_zrem('this_week',user_id)
        
        reviews = Review.objects.filter(
            user_id=user_id, state='N', when_seceded=0,
            is_display=1, user__is_blinded=0, user__is_black=0,
            user__is_active=1).all()

        user_review_count = len(reviews)
        
        if user_review_count <= 0:
            return ''

        review_points = self.get_review_points()

        review_first_logs = Review_first_log.objects.filter(
                user_id=user_id).all()

        first_count = len(review_first_logs)
        
        this_week_first_count = 0
        for r in review_first_logs:
            # 해당 리뷰가 이번주에 쓴 것이라면 this_week_first_count 에도 넣어준다.
            if r.created_at > iso8601(kst_last_week_friday_18_00()):
                this_week_first_count += 1

        this_week_review = [r for r in reviews
            if r.created_at > iso8601(kst_last_week_friday_18_00())]

        user_this_week_review_count = len(this_week_review)

        score = (user_review_count * review_points['review_point']) + \
                ((user_review_count // 3) * \
                 review_points['multiple_bonus_point']) + \
                (first_count * review_points['first_bonus_point'])
        
        if score > 0:
            period_zincrby('all',user_id,score)

        this_week_score = \
            (user_this_week_review_count *
             review_points['review_point']) + \
            ((user_review_count // 3 - (user_review_count - user_this_week_review_count) // 3) * \
             review_points['multiple_bonus_point']) + \
            (this_week_first_count * review_points['first_bonus_point'])

        if this_week_score > 0:
            period_zincrby('this_week', user_id, this_week_score)

service = ReviewService()
