import json
import uuid

from tornado.gen import coroutine
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler

clients = {}


class InitParserHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    def get(self):
        client_id = self.get_cookie('user_id')
        if not client_id:
            client_id = str(uuid.uuid4())
            self.set_cookie('user_id', value=client_id)
        clients[client_id] = {
            'handler': None,
            'urls': []
        }
        self.render('home.html', client_id=client_id)
        if clients[client_id]['handler']:
            clients[client_id]['handler'].notify_clent()

    def post(self):
        # parse urls
        body = str(self.request.body)[2:-1]
        print('body', type(body), body)
        urls = json.loads(body)
        print('urls', urls)
        client_id = self.get_cookie('user_id')
        self.write(json.dumps(urls))
        print('post', urls, client_id)
        print('client keys', clients.keys())
        clients[client_id]['urls'] = urls
        clients[client_id]['handler'].notify_clent()


class DownloadProgressHandler(WebSocketHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super(DownloadProgressHandler, self).__init__(application, request, **kwargs)
        self.client_id = ''

    def open(self, client_id):
        print('open websocet', client_id)
        self.client_id = client_id
        clients[self.client_id]['handler'] = self

    def on_message(self, message):
        print('message', message)

    def on_close(self):
        clients[self.client_id]['handler'] = None

    def notify_clent(self):
        client_data = {'urls': clients.get(self.client_id, {}).get('urls', [])}
        self.write_message(json.dumps(client_data))



def make_app():
    return Application([
        (r"/", InitParserHandler),
        (r"/(.+)", DownloadProgressHandler)
    ])