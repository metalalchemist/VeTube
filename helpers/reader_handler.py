import os
from globals.data_store import config
from prism import Context, BackendId

# Instancia única del contexto de Prism para compartir recursos
_prism_context = None

def get_prism_context():
    global _prism_context
    if _prism_context is None:
        _prism_context = Context()
    return _prism_context


class PrismBackendWrapper:
    def __init__(self, backend_id=None, is_best=False):
        context = get_prism_context()
        self.backend_id = backend_id
        if is_best:
            self.backend = context.create_best()
        else:
            self.backend = context.create(backend_id)

    def speak(self, text, interrupt=False):
        if not text:
            return
        try:
            self.backend.speak(text, bool(interrupt))
        except Exception as e:
            print(f"Error en speak de Prism: {e}")

    def silence(self):
        try:
            self.backend.stop()
        except Exception as e:
            pass

    def list_voices(self):
        voices = []
        try:
            count = self.backend.voices_count
            for i in range(count):
                voices.append(self.backend.get_voice_name(i))
        except Exception as e:
            pass
        return voices

    def set_voice(self, voice_name):
        try:
            count = self.backend.voices_count
            for i in range(count):
                if self.backend.get_voice_name(i) == voice_name:
                    self.backend.voice = i
                    break
        except Exception as e:
            print(f"Error al establecer voz en Prism: {e}")

    def set_volume(self, value):
        try:
            # Mapear de 0-100 a 0.0-1.0
            self.backend.volume = float(value) / 100.0
        except Exception as e:
            pass

    def set_rate(self, value):
        try:
            # Mapear de -10 a 10 al rango 0.0-1.0 (donde 0 es 0.5 de Prism)
            self.backend.rate = (float(value) + 10.0) / 20.0
        except Exception as e:
            pass

    def set_pitch(self, value):
        try:
            if self.backend_id == BackendId.ONE_CORE:
                # OneCore: recibe posición 0-4 del slider especial
                # Mapeo directo: 0=0.6, 1=0.7, 2=0.8, 3=0.9, 4=1.0
                pitch_values = [0.6, 0.7, 0.8, 0.9, 1.0]
                idx = max(0, min(4, int(value)))
                self.backend.pitch = pitch_values[idx]
            else:
                # SAPI: mapeamos [-10, 10] a [0.0, 1.0] (0.5 = neutro)
                self.backend.pitch = (float(value) + 10.0) / 20.0
        except Exception as e:
            pass


class ReaderHandler:
    def __init__(self, lector=None):
        sistema = config['sistemaTTS'] if lector is None else lector
        if sistema == "piper":
            from TTS.lector import configurar_tts
            self._lector = configurar_tts(sistema)
        elif sistema == "onecore":
            self._lector = PrismBackendWrapper(BackendId.ONE_CORE)
        elif sistema == "sapi5":
            self._lector = PrismBackendWrapper(BackendId.SAPI)
        else:
            self._lector = PrismBackendWrapper(is_best=True)
        
        # Intentar inicializar SAPI5 para alertas y anuncios secundarios del sistema.
        # Si falla (por ejemplo, en sistemas sin SAPI o que no son Windows), se usa OneCore de respaldo.
        # Si OneCore también falla, se recurre al mejor backend disponible en el sistema.
        try:
            self._leer = PrismBackendWrapper(BackendId.SAPI)
        except Exception as e:
            print(f"Advertencia: No se pudo inicializar SAPI5 para anuncios del sistema ({e}). Intentando OneCore...")
            try:
                self._leer = PrismBackendWrapper(BackendId.ONE_CORE)
            except Exception as ex:
                print(f"Advertencia: No se pudo inicializar OneCore para anuncios del sistema ({ex}). Usando el mejor disponible...")
                self._leer = PrismBackendWrapper(is_best=True)


    def set_tts(self, nuevo_tts):
        if nuevo_tts == "piper":
            from TTS.lector import configurar_tts
            self._lector = configurar_tts("piper")
        elif nuevo_tts == "onecore":
            self._lector = PrismBackendWrapper(BackendId.ONE_CORE)
        elif nuevo_tts == "sapi5":
            self._lector = PrismBackendWrapper(BackendId.SAPI)
        else:
            self._lector = PrismBackendWrapper(is_best=True)

    def set_sapi(self, sapi):
        config['sapi'] = sapi

    def leer_mensaje(self, mensaje):
        if config['sapi']:
            self.leer_sapi(mensaje)
        else:
            self.leer_auto(mensaje)

    def leer_sapi(self, mensaje):
        if config['sistemaTTS'] == "piper":
            self.leer_auto(mensaje)
        else:
            self._leer.speak(mensaje)

    def leer_auto(self, mensaje):
        self._lector.speak(mensaje)

    def silence(self):
        # Silencia la voz principal y la voz SAPI secundaria.
        self._lector.silence()
        self._leer.silence()

    def close(self):
        if hasattr(self._lector, 'close'):
            self._lector.close()
