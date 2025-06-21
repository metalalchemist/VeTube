# lector:
from accessible_output2.outputs import auto, sapi5
from .Piper import Piper, speaker
import glob
"""
Esto es un gestionador de TTS. Permite manejar el uso de diferentes motores de texto a voz como:
1. accessible output2
2. Piper
"""
def configurar_tts(lector):
	if lector == "auto":
		return auto.Auto()
	elif lector == "sapi5":
		return sapi5.SAPI5()
	elif lector == "piper":
		return speaker
	else:
		raise Exception("Lector no soportado.")

def detect_onnx_models(path):
    onnx_models = glob.glob(path + '/*/*.onnx')
    if len(onnx_models) > 1:
        return onnx_models
    elif len(onnx_models) == 1:
        return onnx_models[0]
    else:
        return None
