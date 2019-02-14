from configs.common import conf
from pymongo import MongoClient

client = MongoClient('mongodb://%s:%s@%s/%s' % (
    conf['MONGODB']['user'], conf['MONGODB']['pw'], conf['MONGODB']['host'], conf['MONGODB']['db']) , 27017)

db = client.coins
