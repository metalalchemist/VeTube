# lector:
from . import sherpa_handler
from . import edge_handler
import glob
import os
from helpers.reader_handler import PrismBackendWrapper
from prism import BackendId

"""
Esto es un gestionador de TTS. Permite manejar el uso de diferentes motores de texto a voz como:
1. Prism Accessibility Library
2. Puente sherpa-onnx (protocolo sonata_grpc): voces Piper y modelo Kokoro
   con un único proceso nativo compartido.
3. Edge TTS (edge-tts): voces de Microsoft Edge por red.
"""
def configurar_tts(lector):
	if lector == "auto":
		return PrismBackendWrapper(is_best=True)
	elif lector == "sapi5":
		return PrismBackendWrapper(BackendId.SAPI)
	elif lector == "onecore":
		return PrismBackendWrapper(BackendId.ONE_CORE)
	elif lector in ("piper", "kokoro"):
		return sherpa_handler.sherpaSpeak()
	elif lector == "edge":
		return edge_handler.edgeSpeak()
	else:
		raise Exception("Lector no soportado.")

def detect_onnx_models(path):
    # Solo las carpetas «voice-*», que son las de Piper: en voices/ vive también
    # el paquete de Kokoro (voices/kokoro-multi-lang-v1_0/model.onnx), y contarlo
    # como voz de Piper dejaba mudo a quien tuviera Kokoro y ninguna voz de
    # Piper — el arranque creía que ya había una y no ofrecía descargarla.
    # Mismo criterio que piper_list_voices().
    onnx_models = glob.glob(path + '/voice-*/*.onnx')
    if onnx_models:
        # Los ficheros de las antiguas voces RT (encoder/decoder) no son voces
        # completas: sin este filtro contarían como instaladas y el arranque
        # intentaría cargarlas en vano.
        onnx_models = [m for m in onnx_models if os.path.basename(m).lower() not in ("encoder.onnx", "decoder.onnx")]
        if len(onnx_models) > 1:
            return onnx_models
        elif len(onnx_models) == 1:
            return onnx_models[0]
    return None
