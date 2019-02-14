from settings.common import conf
import redis

host = conf['REDIS_USER']['host']
port = conf['REDIS_USER']['port']
db = conf['REDIS_USER']['db']

con = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
