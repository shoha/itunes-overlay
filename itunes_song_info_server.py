from gevent import monkey; monkey.patch_all()

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

class SongInfoNamespace(BaseNamespace, BroadcastMixin):

    def recv_connect(self):
        print 'recv_connect'

    def recv_disconnect(self):
        print 'disconnected'

        self.disconnect(silent=True)

    def on_new_song(self, track):
        self.request['last_track'] = track;
        self.broadcast_event('new_song', track)

    def on_player_stopped(self):
        self.broadcast_event('player_stopped')

    def on_initialize(self):
        self.emit('new_song', self.request['last_track'])


class Application(object):
    def __init__(self):
        self.buffer = []
        # Dummy request object to maintain state between Namespace
        # initialization.
        self.request = {
            'last_track': {}
        }

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')

        if not path:
            start_response('200 OK', [('Content-Type', 'text/html')])
            # return ['<h1>Welcome. '
                # 'Try the <a href="/chat.html">chat</a> example.</h1>']
            try:
                return open('index.html').read()
            except Exception:
                return not_found(start_response)

        if path.startswith('static/'):
            try:
                data = open(path, 'rb').read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            elif path.endswith(".gif"):
                content_type = "image/gif"
            elif path.endswith(".png"):
                content_type = "image/png"
            elif path.endswith(".jpg") or path.endswith(".jpeg"):
                content_type = "image/jpeg"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'': SongInfoNamespace}, self.request)
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080 and on port 843 (flash policy server)'
    SocketIOServer(('localhost', 8080), Application(),
        resource="socket.io", policy_server=True,
        policy_listener=('localhost', 10843)).serve_forever()