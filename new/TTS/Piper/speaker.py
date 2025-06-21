import logging
from functools import partial
from pathlib import Path
import sounddevice as sd
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
		self.device = sd.default.device[1]
		self.devices = None

	def load_model(self):
		if self.voice:
			return self.voice
		self.voice = Piper(self.model_path)

	def get_devices(self):
		if self.devices is None:
			devices = sd.query_devices()
			self.devices= [
				{'name': device["name"].replace("(", "").replace(")", "").strip(), 'id': device["index"]}
				for device in devices
				if device['max_output_channels'] > 0 and device['hostapi'] == 0
			]
		return self.devices

	def find_device_id(self, term):
		devices = self.get_devices()
		for device in devices:
			if device['name'] == term:
				return device['id']
		return sd.default.device[1]

	def set_rate(self, new_scale):
		self.length_scale = new_scale

	def set_device(self, device):
		self.device = device

	def set_speaker(self, sid):
		self.speaker_id = sid

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
		sd.play(audio_norm, sample_rate, device=self.device)