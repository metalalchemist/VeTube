from sound_lib import stream
from sound_lib.output import Output
from sound_lib.main import BassError

class playsound:
	def __init__(self):
		try:
			output = Output(device=-1)
		except BassError as e:
			#print(e)
			if e.code == 14:
				#print("Already initialized.")
				Output.free()
				output = Output(device=-1)
			else:
				pass
		output.start()
		# Setup:
		self.output = output
		self.sound = None
		self.devicenames = self.output.get_device_names()
		self.device = 1

	def setdevice(self, device):
		if device > 0 or device < len(self.devicenames):
			self.device = device
		else:
			raise Exception("device is less than 1 or greater than the available devices.")

	def playsound(self, filename, block = False):
		if self.sound is not None and hasattr(self.sound, 'is_playing') and self.sound.is_playing:
			self.sound.stop()
		if self.device != self.output.get_device():
			self.output.set_device(self.device)
		try:
			self.sound = stream.FileStream(file=filename)
		except BassError as e:
			if e.code == 2 and (filename.startswith("http://") or filename.startswith("https://")):
				try:
					self.sound = stream.URLStream(url=filename)
				except:
					raise e
			else:
				raise e
		if not block:
			self.sound.play()
		else:
			self.sound.play_blocking()

	def toggle_player(self):
		if self.sound.is_playing: self.sound.pause()
		else: self.sound.play()

	def atrasar(self, seconds):
		if not self.sound: return
		current_pos = self.sound.get_position()
		bytes_to_move = self.sound.seconds_to_bytes(seconds)
		new_pos = current_pos - bytes_to_move
		if new_pos < 0:
			new_pos = 0
		self.sound.set_position(new_pos)

	def adelantar(self, seconds):
		if not self.sound: return
		current_pos = self.sound.get_position()
		total_length = self.sound.get_length()
		bytes_to_move = self.sound.seconds_to_bytes(seconds)
		new_pos = current_pos + bytes_to_move
		if new_pos > total_length:
			new_pos = total_length
		self.sound.set_position(new_pos)

	def get_volume(self):
		"""Devuelve el volumen actual del reproductor (0.0 a 1.0)."""
		if self.sound:
			return self.sound.volume
		return 1.0 # Default volume

	def set_volume(self, volume):
		"""Establece el volumen del reproductor."""
		if self.sound:
			# Asegurarse de que el volumen esté en el rango de 0.0 a 1.0
			vol = max(0.0, min(1.0, volume))
			self.sound.volume = vol

	def volume_up(self, step=0.1):
		"""Sube el volumen."""
		current_volume = self.get_volume()
		new_volume = current_volume + step
		self.set_volume(new_volume)

	def volume_down(self, step=0.1):
		"""Baja el volumen."""
		current_volume = self.get_volume()
		new_volume = current_volume - step
		self.set_volume(new_volume)

	def release(self):
		self.sound.free()
