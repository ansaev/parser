import json
import requests
from bs4 import BeautifulSoup
from celery import Celery
from redis import StrictRedis
from celery.task import periodic_task
from config import CELERY_REDIS_DB, USER_DATA_REDIS_DB, CLIENT_PERFIX

app = Celery('tasks', broker='redis://localhost:6379/%d' % CELERY_REDIS_DB)


@app.task(name='parse_url')
def parse_url(url):
    try:
        url['status'] = 'PARSED'
        resp = requests.get(url['url'])
        soup = BeautifulSoup(resp._content, 'html.parser')
        url['result'] = 'title: %s, h1: %s, img: %s' % (str(soup.title.text), str(soup.h1.text), str(soup.img['src']))
    except BaseException:
        url['status'] = 'FAILED'
    redis_db = StrictRedis(db=USER_DATA_REDIS_DB)
    redis_db.hset(CLIENT_PERFIX + url['user_id'], url['task_id'], json.dumps(url))
    requests.post('http://localhost:5566/notify', data={'user_id': url['user_id']})
    del redis_db
    return


