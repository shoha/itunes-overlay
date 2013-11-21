import win32com.client, pythoncom, time, tempfile, logging, os

from socketIO_client import SocketIO, BaseNamespace

io = ''

class SocketEventsNamespace(BaseNamespace):
	def on_connect(self):
		print 'Connected'

	def on_disconnect(self):
		print 'Disconnected'

	def on_error(self, name, message):
		print 'Error'

class iTunesEventHandler():
	def __init(self):
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



if __name__ == '__main__':
	logging.basicConfig(level=logging.ERROR)

	io = SocketIO('localhost', 8080, SocketEventsNamespace)

	print 'launching itunes'
	iTunes = win32com.client.Dispatch("iTunes.Application")
	itunesEvents = win32com.client.WithEvents(iTunes, iTunesEventHandler)

	while True:
		time.sleep(0.1)
		pythoncom.PumpWaitingMessages()


