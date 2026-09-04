# lector:
import glob
import os
from logging import getLogger

from prism import BackendId

from helpers.reader_handler import PrismBackendWrapper, crear_respaldo_puente

from . import edge_handler, sherpa_handler, sonata_handler

logger = getLogger(__name__)

"""
Esto es un gestionador de TTS. Permite manejar el uso de diferentes motores de texto a voz como:
1. Prism Accessibility Library
2. Sonata (motor Piper gRPC): las voces Piper, incluidas las variantes RT.
3. Puente sherpa-onnx (habla el mismo protocolo sonata_grpc): el modelo Kokoro.
4. Edge TTS (edge-tts): voces de Microsoft Edge por red.

Los motores con servidor propio están en PUENTES y solo uno vive a la vez: al
elegir un lector se cierran los puentes de todos los demás. Eso incluye elegir
un lector que no tiene ninguno (auto, sapi5, onecore, edge): si no, el servidor
del motor anterior se quedaba en memoria con su modelo cargado hasta cerrar
VeTube. Edge no está en PUENTES porque no levanta ningún servidor: habla por
red y solo mantiene un hilo, así que elegirlo cierra los otros dos y ya está.
"""
# Motores con servidor propio: nombre en config['sistemaTTS'] -> módulo puente.
# Basta añadir una línea aquí para un motor nuevo; la regla «solo uno vivo»
# se cumple sola en vez de tener que acordarse de cerrar los otros uno por uno.
PUENTES = {
    "piper": sonata_handler,
    "kokoro": sherpa_handler,
}


def configurar_tts(lector):
    for nombre, puente in PUENTES.items():
        if nombre != lector:
            puente.detener_puente()
    if lector == "auto":
        return PrismBackendWrapper(is_best=True)
    elif lector == "sapi5":
        return PrismBackendWrapper(BackendId.SAPI)
    elif lector == "onecore":
        return PrismBackendWrapper(BackendId.ONE_CORE)
    elif lector == "piper":
        if not sonata_handler.sonata_instalado():
            # Sin el motor sonata en el equipo (las instalaciones nuevas ya no
            # lo traen: se descarga desde la release «motores»), levantar el
            # puente dejaría al usuario mudo sin explicación. Respaldo SAPI del
            # instante, sin tocar config['sistemaTTS']: en cuanto el descargador
            # lo instala, el siguiente set_tts levanta el puente de verdad.
            logger.warning(
                "El motor sonata no está instalado: las voces Piper hablarán "
                "por el respaldo SAPI hasta que se descargue."
            )
            return crear_respaldo_puente()
        return sonata_handler.piperSpeak()
    elif lector == "kokoro":
        if not sherpa_handler.sherpa_instalado():
            # Mismo caso que Piper sin sonata: el motor sherpa tampoco viaja ya
            # en el build (se descarga desde la release «motores»), así que sin
            # él levantar el puente dejaría al usuario mudo sin explicación.
            # Respaldo SAPI del instante, sin tocar config['sistemaTTS'].
            logger.warning(
                "El motor sherpa no está instalado: las voces Kokoro hablarán "
                "por el respaldo SAPI hasta que se descargue."
            )
            return crear_respaldo_puente()
        return sherpa_handler.sherpaSpeak()
    elif lector == "edge":
        return edge_handler.edgeSpeak()
    else:
        # Un sistemaTTS que no reconocemos (config de una versión anterior,
        # data.json editado a mano) no debe impedir arrancar: se cae en el
        # mejor lector disponible, que es lo que hacía quien nos llama.
        logger.warning(
            "Sistema TTS no soportado (%s): se usa el mejor lector disponible.", lector
        )
        return PrismBackendWrapper(is_best=True)


def detect_onnx_models(path):
    # Solo las carpetas «voice-*», que son las de Piper: en voices/ vive también
    # el paquete de Kokoro (voices/kokoro-multi-lang-v1_0/model.onnx), y contarlo
    # como voz de Piper dejaba mudo a quien tuviera Kokoro y ninguna voz de
    # Piper — el arranque creía que ya había una y no ofrecía descargarla.
    # Mismo criterio que piper_list_voices().
    onnx_models = glob.glob(path + "/voice-*/*.onnx")
    if onnx_models:
        # Filtrar encoder.onnx para no duplicar las voces RT: sus dos ficheros
        # viven en la misma carpeta y el que carga sonata es decoder.onnx.
        onnx_models = [
            m for m in onnx_models if os.path.basename(m).lower() != "encoder.onnx"
        ]
        if len(onnx_models) > 1:
            return onnx_models
        elif len(onnx_models) == 1:
            return onnx_models[0]
    return None
