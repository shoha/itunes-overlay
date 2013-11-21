# Threaded imports
import threading, time

# BBFreeze Imports
import pkg_resources
import win32com.server.util

# Server imports

from gevent import monkey; monkey.patch_all()

from socketio import socketio_manage
from socketio.server import SocketIOServer
import socketio.namespace
from socketio.mixins import BroadcastMixin

# Client imports
import win32com.client, pythoncom, time, tempfile, logging, os
from socketIO_client import SocketIO, BaseNamespace


# Server classes

class SongInfoNamespace(socketio.namespace.BaseNamespace, BroadcastMixin):

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


class Server(object):
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

            try:
                return open('index.html').read()
            except Exception:
	            start_response('404 Not Found', [])
	            return ['<h1>Not Found</h1>']

        if path.startswith('static/'):
            try:
                data = open(path, 'rb').read()
            except Exception:
	            start_response('404 Not Found', [])
	            return ['<h1>Not Found</h1>']

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
            start_response('404 Not Found', [])
            return ['<h1>Not Found</h1>']

class ServerThread(threading.Thread):

	def run(self):
		print 'server thread'
		print 'Listening on port 8080 and on port 843 (flash policy server)'
		SocketIOServer(('localhost', 8080), Server(),
			resource="socket.io", policy_server=True,
			policy_listener=('localhost', 10843)).serve_forever()


#Client classes

class SocketEventsNamespace(BaseNamespace):
	def on_connect(self):
		print 'Connected'

	def on_disconnect(self):
		print 'Disconnected'

	def on_error(self, name, message):
		print 'Error'

class iTunesEventHandler():
	def __init__(self):
		self.quitting = False

	def OnPlayerStopEvent(self, track):
		print 'stopped'
		try:
		 io.emit('player_stopped')
		except Exception, e:
			io = SocketIO('localhost', 8080, SocketEventsNamespace)
			io.emit('player_stopped');


	def OnPlayerPlayEvent(self, track):
		print 'playing'
		track = win32com.client.CastTo(track, 'IITTrack')
		
		artwork_collection = win32com.client.CastTo(track.Artwork, 'IITArtworkCollection')
		artwork = win32com.client.CastTo(artwork_collection.Item(1), 'IITArtwork')

		artwork_path = os.path.join(os.getcwd(), 'album.jpg')
		artwork.SaveArtworkToFile(artwork_path)
		artwork_encoded = ''

		with open(artwork_path, 'rb') as a:
			data = a.read()
			artwork_encoded = data.encode("Base64")

		try:
			io.emit('new_song', {
				"name": track.Name,
				"album": track.Album,
				"artist": track.Artist,
				"duration": track.Duration * 1000,
				"position": iTunes.PlayerPosition * 1000,
				"artwork": artwork_encoded
			})
		except Exception, e:
			io = SocketIO('localhost', 8080, SocketEventsNamespace)
			io.emit('new_song', {
				"name": track.Name,
				"album": track.Album,
				"artist": track.Artist,
				"duration": track.Duration * 1000,
				"position": iTunes.PlayerPosition * 1000,
				"artwork": artwork_encoded
			})

class ClientThread(threading.Thread):

	def run(self):
		print 'client thread'

		logging.basicConfig(level=logging.ERROR)

		print 'launching itunes'
		
		itunesEvents = win32com.client.WithEvents(iTunes, iTunesEventHandler)

		while True:
			time.sleep(0.1)
			pythoncom.PumpWaitingMessages()


if __name__ == '__main__':
	server_thread = ServerThread()


	server_thread.start()

	iTunes = win32com.client.Dispatch("iTunes.Application")
	io = SocketIO('localhost', 8080, SocketEventsNamespace)

	client_thread = ClientThread()
	client_thread.start()

	while True:
		time.sleep(0.1)