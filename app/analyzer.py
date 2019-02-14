from db.mongodb import db
import pprint
import pymongo
import time
print(db.flow.count())
start_time = time.time()
tmp = db.flow.find({'timestamp'},{'data'}).limit(50).sort('timestamp',pymongo.DESCENDING)
print(tmp[0])
_list = list()
_list2 = list()
for i in tmp:
    _list.append(i['data']['BZNT'])
    _list2.append(i['data']['WTC'])
print("--- %s seconds ---" % (time.time() - start_time))
