# lector:
from . import sonata_handler as speaker
import glob
import os
from helpers.reader_handler import PrismBackendWrapper
from prism import BackendId

"""
Esto es un gestionador de TTS. Permite manejar el uso de diferentes motores de texto a voz como:
1. Prism Accessibility Library
2. Sonata (Motor Piper gRPC)
"""
def configurar_tts(lector):
	if lector == "auto":
		return PrismBackendWrapper(is_best=True)
	elif lector == "sapi5":
		return PrismBackendWrapper(BackendId.SAPI)
	elif lector == "onecore":
		return PrismBackendWrapper(BackendId.ONE_CORE)
	elif lector == "piper":
		return speaker.piperSpeak()
	else:
		raise Exception("Lector no soportado.")

def detect_onnx_models(path):
    onnx_models = glob.glob(path + '/*/*.onnx')
    if onnx_models:
        # Filtrar encoder.onnx para no duplicar las voces RT en la UI
        onnx_models = [m for m in onnx_models if os.path.basename(m).lower() != "encoder.onnx"]
        if len(onnx_models) > 1:
            return onnx_models
        elif len(onnx_models) == 1:
            return onnx_models[0]
    return None
