from os import path
import re
class KeyUtils:
	def __init__(self): self.leerTeclas()
	def escribirTeclas(self):
		with open('keys.txt', 'w+') as arch: arch.write("""{
"control+p": reader._leer.silence,
"alt+shift+up": self.elementoAnterior,
"alt+shift+down": self.elementoSiguiente,
"alt+shift+left": self.retrocederCategorias,
"alt+shift+right": self.avanzarCategorias,
"alt+shift+home": self.elementoInicial,
"alt+shift+end": self.elementoFinal,
"alt+shift+f": self.destacarMensaje,
"alt+shift+c": self.copiar,
"alt+shift+m": self.callar,
"alt+shift+s": self.iniciarBusqueda,
"alt+shift+v": self.mostrarMensaje,
"alt+shift+d": self.borrarBuffer,
"alt+shift+p": self.desactivarSonidos,
"alt+shift+k": self.createEditor,
"alt+shift+a": self.addRecuerdo}""")
		self.leerTeclas()
	def leerTeclas(self):
		if path.exists("keys.txt"):
			with open ("keys.txt",'r') as arch:
				contenido = arch.read()
				self.teclas = re.findall(r'"(.*?)"', contenido)
		else: self.escribirTeclas()
	def reemplazar(self, vieja, nueva):
		with open("keys.txt", 'r', encoding='utf-8') as arch:
			contenido = arch.read()
		contenido = contenido.replace(vieja, nueva)
		with open("keys.txt", 'w', encoding='utf-8') as arch:
			arch.write(contenido)
		self.leerTeclas()
editor=KeyUtils()