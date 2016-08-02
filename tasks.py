import json
from datetime import timedelta

import requests
from celery import Celery
from redis import StrictRedis
from celery.task import periodic_task
from config import CELERY_REDIS_DB, USER_DATA_REDIS_DB, CLIENT_PERFIX

app = Celery('tasks', broker='redis://localhost:6379/%d' % CELERY_REDIS_DB)


@app.task(name='parse_url')
def parse_url(url):
    url['status'] = 'PARSED'
    url['result'] = 'OK'
    redis_db = StrictRedis(db=USER_DATA_REDIS_DB)
    redis_db.hset(CLIENT_PERFIX + url['user_id'], url['task_id'], json.dumps(url))
    requests.post('http://localhost:5566/notify', data={'user_id': url['user_id']})
    return


