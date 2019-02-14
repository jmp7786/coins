import json
import math
from django.conf import settings

from .redis import con as redis_con

def redis_get_exists_table(tables):
    for t in tables:
        if redis_con.exists(t):
            return t
    
    redis_get_exists_table()

def get_redis_tables(type=None,key='default'):
    if settings.DEBUG:
        env = 'test_'
    else :
        env = ''
    tables = {
        'user': {
            'default': ['rank_user_all', 'rank_user_all_copy'],
            'all': ['rank_user_all', 'rank_user_all_copy'],
            'this_week': ['rank_user_this_week',
                'rank_user_this_week_copy'],
            'last_week': ['rank_user_last_week', 'rank_user_last_week_copy']
        },
        'list': {
            'default': ['rank_list_all', 'rank_list_all_copy'],
            'all': ['rank_list_all', 'rank_list_all_copy'],
            'this_week': ['rank_list_this_week',
                'rank_list_this_week_copy'],
            'last_week': ['rank_list_last_week', 'rank_list_last_week_copy']
        },
        'review_is_written':{
            "default":['review_is_written']
        }
    }
    
    return [env + t for t in tables[type][key]]

def set_review_is_written(user_id,dict):
    table = get_redis_tables('review_is_written')[0]
    
    if len(dict) > 2 :
        raise Exception("Dict Parameter only required 'is_first' and 'written'")
    if type(dict['is_first']) is not bool:
        raise Exception("Dict Parameter required 'is_first'")
    if not dict['written']:
        raise Exception("Dict Parameter required 'written'")

    return redis_con.hset(table, user_id, json.dumps(dict))
    
def get_review_is_written(user_id):
    table = get_redis_tables('review_is_written')[0]
    
    result = redis_con.hget(table, user_id)
    
    if result :
        result = json.loads(result)
        
    # 한번 가져온 값은 재사용 방지를 위해 지운다.
    redis_con.hset(table, user_id, '')
    
    return result

def get_data(func, tables, *keyword, **kwargs):
    result = None
    
    for t in tables:
        value = func(t, *keyword)
        if value is not None:
            result = value
            break
    
    return result

def get_mdata(func, tables, *keyword, **kwargs):
    result = None
    
    for t in tables:
        values = func(t, *keyword, **kwargs)
        if len(values) > 0:
            result = values
            break
    
    return result

def period_hget(period, id):
    tables = get_redis_tables('user', period)
    return get_data(redis_con.hget, tables, id)

def period_hset(period, id, val):
    for t in get_redis_tables('user', period):
        redis_con.hset(t, id, val)
    return 'done'

def period_hdel(period, id):
    for t in get_redis_tables('user', period):
        redis_con.hdel(t, id)
    return 'done'

def period_hmget(period, ids):
    tables = get_redis_tables('user', period)
    return get_mdata(redis_con.hmget, tables, ids)

def period_zrevrank(period, id):
    tables = get_redis_tables('list', period)
    return get_data(redis_con.zrevrank, tables, id)

def period_zcard(period):
    tables = get_redis_tables('list', period)
    return redis_con.zcard(tables[0])

def period_zrangebyscore(period, score1, score2):
    tables = get_redis_tables('list', period)
    return get_mdata(redis_con.zrangebyscore, tables, score1, score2)

def period_zrevrange(period, score1, score2, **kwargs):
    tables = get_redis_tables('list', period)
    return get_mdata(redis_con.zrevrange, tables, score1, score2,
                     **kwargs)

def period_zincrby(period, id,point):
    for t in get_redis_tables('list', period):
        redis_con.zincrby(t, id, point)
    return 'done'

def period_zrem(period, id):
    for t in get_redis_tables('list', period):
        redis_con.zrem(t, id)
    return 'done'

def period_zscore(period, id):
    tables = get_redis_tables('list', period)
    return get_data(redis_con.zscore, tables, id)

def get_user_review_info(key, id):
    result = period_hget(key, id)
    return result and json.loads(result)['reviewCnt']

def get_user_rank(period, id):
    score = period_zscore(period, id)
    
    if score is not None:
        result = dict()
        users = period_zrangebyscore(period, score, score)
        # 인덱스가 0 부터 시작하기 떄문에 1을 더해준다.
        rank = period_zrevrank(period, users[-1]) + 1
        total = period_zcard(period)
        result['score'] = int(score)
        result['rank'] = rank
        result['ratio'] = 100 if total == 0 else \
                math.ceil(rank/total * 100)
    else:
        result = None
        
    return result
    
