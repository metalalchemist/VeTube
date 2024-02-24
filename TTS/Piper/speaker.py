import logging
from functools import partial
from pathlib import Path
from sound_lib import stream
from sound_lib import output
from sound_lib.main import BassError
from . import Piper

class piperSpeak:
	def __init__(self, model_path):
		self.model_path = model_path
		self.speaker_id = None
		self.length_scale = 1
		self.noise_scale = 0.667
		self.noise_w = 0.8
		self.synthesize = None
		self.voice = None
		# Audio:
		try:
			self.o = output.Output(device=-1)
		except BassError as e:
			if e.code == 14:
				print("Already initialized.")
				print(output.Output.free())
				self.o = output.Output(device=-1)
			else:
				pass
		#self.o.start()
		self.audio_stream=None
		self.device = 1

	def load_model(self):
		if self.voice:
			return self.voice
		self.voice = Piper(self.model_path)

	def load_audio(self, restart=False):
		if self.audio_stream is None or restart:
			self.audio_stream=stream.PushStream(freq=self.voice.config.sample_rate, chans=1)

	def set_rate(self, new_scale):
		self.length_scale = new_scale

	def set_speaker(self, sid):
		self.speaker_id = sid

	def set_device(self, device):
		if device > 0 or device < len(self.devicenames):
			self.device = device
		else:
			raise Exception("device is less than 1 or greater than the available devices.")

	def is_multispeaker(self):
		return self.voice.config.num_speakers > 1

	def list_speakers(self):
		if self.is_multispeaker():
			return self.voice.config.speaker_id_map
		else:
			raise Exception("This is not a multispeaker model!")

	def speak(self, text):
		self.synthesize = self.load_model()
		if self.speaker_id is None and self.is_multispeaker():
			self.set_speaker(0)
		audio_norm, sample_rate = self.voice.synthesize(
			text,
			self.speaker_id,
			self.length_scale,
			self.noise_scale,
			self.noise_w
		)
		if self.audio_stream is not None:
			if self.audio_stream.is_playing:
				self.audio_stream.stop()
			if self.device != self.o.get_device():
				self.o.set_device(self.device)
		self.load_audio()
		self.audio_stream.push(audio_norm)
		self.audio_stream.play()