import json
import uuid
from datetime import datetime
from tornado.gen import coroutine, Task
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler

from config import CLIENT_PERFIX
from tasks import parse_url
import tornadoredis

DATAFORMAT = '%y-%m-%dT%H:%M'
handlers = {}


class InitParserHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    def prepare(self):
        self.redis_db = tornadoredis.Client(selected_db=7)
        self.redis_db.connect()

    @coroutine
    def on_finish(self):
        yield Task(self.redis_db.disconnect)

    def get(self):
        client_id = self.get_cookie('user_id')
        if not client_id:
            client_id = str(uuid.uuid4())
            self.set_cookie('user_id', value=client_id)
        handlers[client_id] = None
        self.render('home.html', client_id=client_id)

    @coroutine
    def post(self):
        # parse urls
        body = str(self.request.body)[2:-1]
        urls = json.loads(body)
        client_id = str(self.get_cookie('user_id'))
        for url in urls:
            url['user_id'] = client_id
            url['task_id'] = str(uuid.uuid4())
            pushed = False
            if not url.get('date'):
                url['date'] = datetime.now().strftime(DATAFORMAT)
            else:
                try:
                    my_date = datetime.strptime(url['date'], DATAFORMAT)
                    if my_date > datetime.now():
                        # push to time quuen now
                        url['status'] = 'WAITING'
                        pushed = True
                        yield Task(self.redis_db.lpush, 'date:' + url['date'], json.dumps(url))
                except ValueError:
                    url['date'] = datetime.now().strftime(DATAFORMAT)
            if pushed is False:
                # push to quuen now
                url['status'] = 'IN_QUEEN'
                parse_url.delay(url)
            yield Task(self.redis_db.hset, CLIENT_PERFIX + client_id, url['task_id'], json.dumps(url))
        print('post', urls, client_id)
        if handlers[client_id]:
            print('call_notify')
            handlers[client_id].notify_client()


class NotifierHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    def post(self, *args, **kwargs):
        user_id = self.get_body_argument('user_id')
        handler = handlers.get(user_id)
        if not handler:
            self.set_status(status_code=404)
            return
        handler.notify_client()


class DownloadProgressHandler(WebSocketHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super(DownloadProgressHandler, self).__init__(application, request, **kwargs)
        self.client_id = ''

    def open(self, client_id):
        print('open websocet', client_id)
        self.client_id = client_id
        handlers[self.client_id] = self
        self.notify_client()

    def on_message(self, message):
        print('message', message)

    def on_close(self):
        print('ws_clode', self.client_id)
        handlers[self.client_id] = None

    @coroutine
    def notify_client(self):
        redis_db = tornadoredis.Client(selected_db=7)
        redis_db.connect()
        data = yield Task(redis_db.hgetall, CLIENT_PERFIX+ self.client_id)
        yield Task(redis_db.disconnect)
        del redis_db
        print('notify_data', data)
        self.write_message(json.dumps(data))



def make_app():
    return Application([
        (r"/notify", NotifierHandler),
        (r"/(.+)", DownloadProgressHandler),
        (r"/", InitParserHandler),


    ])