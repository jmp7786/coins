import re
import json

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from db.raw_queries import counting_for_user_score
from libs.aws.dynamodb import aws_dynamodb_etc_list
from libs.utils import get_age_range
from models.users import User, SkinTypeCode, Gender, SkinTypeKor
from cash_db.redis_utils import period_zrevrange, period_zcard, period_hmget, \
    get_user_rank
from backends.api import exceptions
class UserService:
    def get_user_score_info(self, user_id):
        """
        # 회원 리뷰건수, 좋아요건수, 인기도(score)
        """
        counting = counting_for_user_score(user_id)
        review_count = counting.get('review_count')
        like_count = counting.get('like_count')
        score = review_count + like_count * 2

        return {
            'review_count': review_count,
            'like_count': like_count,
            'score': score,
        }

    def get_list(self, only_count=None, top3=False, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        order = kwargs.get('order')

        gender = kwargs.get('gender')
        age = kwargs.get('age')
        skin_type = kwargs.get('skin_type')

        nickname = kwargs.get('query')

        users = User.objects.filter(
            is_active=True,
            type='USER',
        )

        if order == 'review_desc':
            sort = '-review_count'
        elif order == 'review_asc':
            sort = 'review_count'
        elif order == 'like_desc':
            sort = '-like_count'
        elif order == 'like_asc':
            sort = 'like_count'
        elif order == 'top_ranking':
            sort = '-score'
        else:
            sort = '-review_count'

        if order != 'top_ranking':
            if nickname:
                q = Q()
                word_list = re.findall('([\w.]+)', nickname)

                if len(word_list) < 1:
                    if only_count is not None:
                        return 0
                    return {
                        'list': [],
                        'next_offset': None,
                    }

                for sch_word in word_list:
                    q &= Q(nickname__icontains=sch_word)

                users = users.filter(q)
        else:
            users = users.filter(is_blinded=0)

        if gender is not None and gender != 'all':
            users = users.filter(_gender=Gender[gender].value)

        if age is not None and age != 'all':
            age_arr = age.split(',')
            q_age = Q()
            for generation in age_arr:
                min_year, max_year = get_age_range(generation)
                q_age |= Q(birth_year__range=(min_year, max_year))
            users = users.filter(q_age)

        if skin_type is not None and skin_type != 'all':
            skin_types = skin_type.split(",")
            skin_types = [SkinTypeCode[s].value for s in skin_types]
            users = users.filter(_skin_type__in=skin_types)

        if only_count:
            return users.count()

        users = users.order_by(sort)

        if top3:
            results = users.all()[:3]
        else:
            cursor = int(cursor or 1)
            offset = (cursor - 1) * limit
            rank_range = range(offset + 1, offset + 22)
            results = users.all()[offset: offset + limit + 1]
            if order == 'top_ranking':
                for idx, user in enumerate(results):
                    setattr(user, 'rank', rank_range[idx])

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

    def get_top_users_by_dynamo(self):
        """
        화원 랭킹 1 ~ 3 위 정보 (dynamoDB 로부터 데이터 얻기)
        """
        users = aws_dynamodb_etc_list.get_top_users()

        results = list()
        for user in users:
            skin_type = int(user["skinType"]['N'] or None)
            gender = int(user["gender"]['N'] or None)
            birth_year = int(user['birthYear']['N'] or None)
            if birth_year:
                age = timezone.localtime(timezone.now()).year - birth_year + 1
            else:
                age = None

            results.append({
                'id': int(user['idRegister']['N']),
                'nickname': user['nickName']['S'],
                'gender': Gender(gender).name,
                'birth_year': birth_year,
                'age': age,
                'skin_type': getattr(SkinTypeKor, SkinTypeCode(skin_type).name).value,
                'rank': int(user['rank']['N']),
                'review_count': int(user['reviewCount']['N']),
                'like_count': int(user['likeCount']['N']),
                'profile_image': settings.CDN + user['image']['S'],
                'register_thumbnail': settings.CDN + user['thumbnail']['S']
            })

        return results
    

    def get_list_from_redis(self, only_count=None, **kwargs):
        next_offset = None
        
        limit = kwargs.get('limit') or 20
        cursor = kwargs.get('cursor') or 1
    
        period = kwargs.get('period')
    
        # only_count 옵션이 있으면 총 유저수를 반환한다.
        if only_count:
            return period_zcard(period)
        
        #  cursor 가 첫번쨰가 아닌경우 이전 페이지에 마지막 유저과 포인트가 같을 때
        # 같은 랭크를 표현해야 함으로 앞 페이지의 마지막 유저값을 가져와서 비교하도록 한다.
        #  redis 의 index 는 0 부터 시작함 아래는 22개의 row 가 나오는 것이 정상이다.
        start = limit * (cursor - 1) - 1 if cursor > 1 else limit * (cursor - 1)
        end = limit * cursor
        
        user_id_and_scores = period_zrevrange(
            period, start , end, withscores=True)
        
        if user_id_and_scores:
            user_ids = list(r[0] for r in user_id_and_scores)
            # user 정보는 all로 통합하여 참고하도록 한다.
            users = period_hmget('all', user_ids)
            results = list()
            # profile_image 이미지를 만들어서 반환한다.
            for idx, val in enumerate(users):
                if val is not None:
                    val = json.loads(val)
                    val['profile_image'] = \
                        val['fileDir'] and val['fileSaveName'] \
                    and  "{}{}/{}".format(
                        settings.CDN, val['fileDir'],val['fileSaveName'])
                    #  hash map 을 업데이트할 때 자신의 점수만 계산해서 넣기 때문에
                     #  sorted set 의 list 를 기준으로 랭킹을 정함으로
                    # rank 를 다시 계산해서 넣어준다.
                    #  중복값을 표현하기 위해 바로 전 인덱스의 포인트와 현 포인트가 같으면
                    # 랭크를 같게 표현한다.
                    user_info = get_user_rank(
                            period, val['idRegister'])
                    val['rank'] = user_info['rank']
                    val['score'] = user_info['score']
                    val['ratio'] = user_info['ratio']
                    
                else:
                    val = dict()
                    _user_id = user_ids[idx]
                    try:
                        _user = User.objects.get(id=_user_id)
                    except User.DoesNotExist:
                        continue
                    val['profile_image'] = \
                        _user.file_dir and _user.file_name_save \
                        and "{}{}/{}".format(
                            settings.CDN, _user.file_dir, _user.file_name_save)
                    val['idRegister'] = _user.id
                    val['nickname'] = _user.nickname
                    user_info = get_user_rank(
                        period, _user_id)
                    val['rank'] = user_info['rank']
                    val['score'] = user_info['score']
                    val['ratio'] = user_info['ratio']
                    
                results.append(val)
                
                
            # 처음
            if cursor == 1:
                results = results[:limit]
            # 중간
            elif len(results) == limit + 2 :
                next_offset = cursor + 1
                results = results[1:limit+1]
            # 끝
            else:
                results = results[1:]
                
        else:
            results = list()
            
        return {
            'list': results,
            'next_offset': next_offset,
        }
        
service = UserService()
