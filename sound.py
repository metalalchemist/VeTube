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
				print("Already initialized.")
				print(Output.free())
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
		if self.sound is not None:
			if self.sound.is_playing:
				self.sound.stop()
			if self.device != self.output.get_device():
				self.output.set_device(self.device)
		self.sound = stream.FileStream(file = filename)
		if not block:
			self.sound.play()
		else:
			self.sound.play_blocking()
