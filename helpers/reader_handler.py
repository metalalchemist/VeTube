from utils import fajustes
from TTS.lector import configurar_tts
class ReaderHandler:
	def __init__(self,lector=None):
		if lector is None: self._config=fajustes.leerConfiguracion()
		self._lector=configurar_tts(self._config['sistemaTTS'] if lector is None else lector)
		self._leer=configurar_tts("sapi5")
	def leer_mensaje(self, mensaje):
		if hasattr(self, '_config'):
			if self._config['sapi']: self.leer_sapi(mensaje)
			else: self.leer_auto(mensaje)
		else: self.leer_auto(mensaje)
	def leer_sapi(self, mensaje): self._leer.speak(mensaje)
	def leer_auto(self,mensaje): self._lector.speak(mensaje)