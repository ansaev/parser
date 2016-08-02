import json
from datetime import datetime
from redis import StrictRedis
from config import USER_DATA_REDIS_DB, DATE_PERFIX, DATE_FORMAT
from tasks import parse_url

redis_db = StrictRedis(db=USER_DATA_REDIS_DB)
now = datetime.now()
search = DATE_PERFIX + now.strftime(DATE_FORMAT)
search = search[:-1] + '[' + ','.join([str(i) for i in  range(now.minute)]) + ']'
keys = redis_db.keys(search)

for key in keys:
    # TODO: make a transaction
    tasks = redis_db.lrange(key, 0, -1)
    redis_db.delete(key)
    for task in tasks:
        task = str(task)[2:-1]
        try:
            task = json.loads(str(task))

        except BaseException:
            continue
        parse_url.delay(task)
