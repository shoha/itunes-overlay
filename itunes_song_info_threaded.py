# Threaded imports
import threading, time, msvcrt, sys

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
        print 'server: recv_connect'

        self.request['last_track'] = get_track_info(iTunes.CurrentTrack)
        self.emit('new_player_state', self.request['last_track'])

    def recv_disconnect(self):
        print 'server: recv_disconnect'

        self.disconnect(silent=True)

    def on_new_song(self, track):
    	print 'server: new_song'

    	if self.request['last_track'] and (track['name'], track['album']) == (self.request['last_track']['name'], self.request['last_track']['album']):
    		self.request['last_track'] = track;
    		track['position'] = iTunes.PlayerPosition * 1000
    		self.broadcast_event('resume_song', track)
    	else:
	        self.request['last_track'] = track;
	        self.broadcast_event('new_song', track)


class Server(object):
    def __init__(self):

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
			socketio_manage(environ, {'/song_info': SongInfoNamespace}, self.request)
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
		print 'client: connect'

	def on_disconnect(self):
		print 'client: disconnect'

	def on_error(self, name, message):
		print 'client: error'


class iTunesEventHandler():
	def __init__(self):
		print 'client: init'

		if iTunes.CurrentTrack != None:
			self.OnPlayerPlayEvent(iTunes.CurrentTrack)

	def OnPlayerPlayingTrackChanged(self, track):
		print 'client: OnPlayerPlayingTrackChanged'
	
	def OnPlayerStopEvent(self, track):
		print 'client: OnPlayerStop'
		io_namespace.emit('player_stopped')

	def OnPlayerPlayEvent(self, track):
		print 'client: OnPlayerPlay'
		io_namespace.emit('new_song', get_track_info(track))


class ClientThread(threading.Thread):

	def run(self):
		print 'client thread'

		logging.basicConfig(level=logging.ERROR)

		print 'launching itunes'

		while True:
			time.sleep(0.1)
			pythoncom.PumpWaitingMessages()


class SocketKeepalive(threading.Thread):

	def run(self):
		print 'spinning io'
		io.wait()


def get_track_info(track):
	if track is None:
		return

	track = win32com.client.CastTo(track, 'IITTrack')
	artwork = None
	try:
		artwork_collection = win32com.client.CastTo(track.Artwork, 'IITArtworkCollection')
		artwork = win32com.client.CastTo(artwork_collection.Item(1), 'IITArtwork')
		
		artwork_path = os.path.join(os.getcwd(), 'album.jpg')
		artwork.SaveArtworkToFile(artwork_path)
	except:
		artwork = None

	artwork_encoded = None

	if artwork != None:		
		with open(artwork_path, 'rb') as a:
			data = a.read()
			artwork_encoded = data.encode("Base64")
	
	return {
		"name": track.Name,
		"album": track.Album,
		"artist": track.Artist,
		"duration": track.Duration * 1000,
		"position": iTunes.PlayerPosition * 1000,
		"artwork": artwork_encoded,
		"player_stopped": iTunes.PlayerState == 0
	}


if __name__ == '__main__':
	server_thread = ServerThread()
	server_thread.start()

	io = SocketIO('localhost', 8080, SocketEventsNamespace)
	io_namespace = io.define(SocketEventsNamespace, '/song_info')

	iTunes = win32com.client.Dispatch("iTunes.Application")
	iTunesEvents = win32com.client.WithEvents(iTunes, iTunesEventHandler)
	
	client_thread = ClientThread()
	client_thread.start()

	socket_keepalive_thread = SocketKeepalive()
	socket_keepalive_thread.start()

	while not msvcrt.kbhit():
		time.sleep(0.1)

	iTunesEvents.close()
	del iTunesEvents, iTunes
