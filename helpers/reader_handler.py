from globals.data_store import config
from TTS.lector import configurar_tts
class ReaderHandler:
	def __init__(self,lector=None):
		self._lector=configurar_tts(config['sistemaTTS'] if lector is None else lector)
		self._leer=configurar_tts("sapi5")
	def set_tts(self, nuevo_tts): self._lector = configurar_tts(nuevo_tts)
	def set_sapi(self, sapi): config['sapi']=sapi
	def leer_mensaje(self, mensaje):
		if config['sapi']: self.leer_sapi(mensaje)
		else: self.leer_auto(mensaje)
	def leer_sapi(self, mensaje): self._leer.speak(mensaje)
	def leer_auto(self,mensaje): self._lector.speak(mensaje)