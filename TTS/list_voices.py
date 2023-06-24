import os
from .lector import detect_onnx_models
def piper_list_voices():
	voice_list = detect_onnx_models("piper/voices")
	# fix paths:
	if isinstance(voice_list, str):
		voice_list = [os.path.basename(voice_list)]
	elif isinstance(voice_list, list):
		voice_list = [os.path.basename(path) for path in voice_list]
	return voice_list