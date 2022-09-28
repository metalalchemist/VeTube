#!/usr/bin/python
# -*- coding: <encoding name> -*-
import json,wx,threading,languageHandler,restart,translator
from keyboard_handler.wx_handler import WXKeyboardHandler
from playsound import playsound
from accessible_output2.outputs import auto, sapi5
from youtube_dl import YoutubeDL
from pyperclip import copy
from chat_downloader import ChatDownloader
from update import updater,update
from os import path
voz=0
tono=0
volume=100
speed=0
sapi=True
sonidos=True
reader=True
donations=True
updates=True
idioma="system"
yt=0
favorite=[]
categ=[True,True,False,False,False]
listasonidos=[True,True,True,True,True,True,True,True,True]
rutasonidos=["sounds/chat.mp3","sounds/chatmiembro.mp3","sounds/miembros.mp3","sounds/donar.mp3","sounds/moderators.mp3","sounds/verified.mp3","sounds/abrirchat.wav","sounds/propietario.mp3","sounds/buscar.wav"]
lector=auto.Auto()
leer=sapi5.SAPI5()
lista_voces=leer.list_voices()
def escribirFavorito():
	with open('favoritos.json', 'w+') as file: json.dump(favorite, file)
def leerFavoritos():
	if path.exists("favoritos.json"):
		with open ("favoritos.json") as file:
			global favorite
			favorite=json.load(file)
	else: escribirFavorito()
def asignarConfiguracion():
	global voz,tono,volume,speed,sapi,sonidos,idioma,reader,categ,listasonidos,donations,updates
	voz=0
	tono=0
	volume=100
	speed=0
	sapi=True
	sonidos=True
	idioma="system"
	reader=True
	categ=[True,True,False,False,False]
	listasonidos=[True,True,True,True,True,True,True,True,True]
	donations=True
	updates=True
	leer.set_rate(speed)
	leer.set_pitch(tono)
	leer.set_voice(lista_voces[voz])
	leer.set_volume(volume)
def convertirFavoritos(lista):
	if len(lista)<=0: return[]
	else:
		newlista=[]
		for datos in lista: newlista.append(datos['titulo']+': '+datos['url'])
		return newlista
def escribirConfiguracion():
	data={'voz': voz,
"tono": tono,
"volume": volume,
"speed": speed,
'sapi':sapi,
'sonidos': sonidos,
'idioma': idioma,
'categorias': categ,
'listasonidos': listasonidos,
'reader': reader,
'donations': donations,
'updates': updates}
	with open('data.json', 'w+') as file: json.dump(data, file)
def leerConfiguracion():
	if path.exists("data.json"):
		with open ("data.json") as file: resultado=json.load(file)
		global voz,tono,volume,speed,sapi,sonidos,idioma,reader,categ,listasonidos,donations,updates
		voz=resultado['voz']
		tono=resultado['tono']
		volume=resultado['volume']
		speed=resultado['speed']
		sapi=resultado['sapi']
		sonidos=resultado['sonidos']
		idioma=resultado['idioma']
		reader=resultado['reader']
		categ=resultado['categorias']
		donations=resultado['donations']
		updates=resultado['updates']
		listasonidos=resultado['listasonidos']
	else: escribirConfiguracion()
def escribirTeclas():
	with open('keys.txt', 'w+') as arch: arch.write("""{"control+p": leer.silence,"alt+shift+up": self.elementoAnterior,"alt+shift+down": self.elementoSiguiente,"alt+shift+left": self.retrocederCategorias,"alt+shift+right": self.avanzarCategorias,"alt+shift+home": self.elementoInicial,"alt+shift+end": self.elementoFinal,"alt+shift+f": self.destacarMensaje,"alt+shift+c": self.copiar,"alt+shift+m": self.callar,"alt+shift+s": self.iniciarBusqueda,"alt+shift+v": self.mostrarMensaje,"alt+shift+d": self.borrarBuffer,"alt+shift+p": self.desactivarSonidos}""")
	leerTeclas()
def leerTeclas():
	if path.exists("keys.txt"):
		global mis_teclas
		with open ("keys.txt",'r') as arch:
			mis_teclas=arch.read()
	else: escribirTeclas()
pos=[]
leerConfiguracion()
leerFavoritos()
leer.set_rate(speed)
leer.set_pitch(tono)
leer.set_voice(lista_voces[voz])
leer.set_volume(volume)
favs=convertirFavoritos(favorite)
languageHandler.setLanguage(idioma)
idiomas = languageHandler.getAvailableLanguages()
langs = []
[langs.append(i[1]) for i in idiomas]
codes = []
[codes.append(i[0]) for i in idiomas]
mensaje_teclas=[_('Silencia la voz sapy'),_('Buffer anterior.'),_('Siguiente buffer.'),_('Mensaje anterior'),_('Mensaje siguiente'),_('Ir al comienzo del buffer'),_('Ir al final del buffer'),_('Copia el mensaje actual'),_('Activa o desactiva la lectura automática'),_('Muestra el mensaje actual en un cuadro de texto'),_('Busca una palabra en los mensajes actuales')]
mensajes_categorias=[_('Miembros'),_('Donativos'),_('Moderadores'),_('Usuarios Verificados'),_('Favoritos')]
mensajes_sonidos=[_('Sonido cuando llega un mensaje'),_('Sonido cuando habla un miembro'),_('Sonido cuando se conecta un miembro'),_('Sonido cuando llega un donativo'),_('Sonido cuando habla un moderador'),_('Sonido cuando habla un usuario verificado'),_('Sonido al ingresar al chat'),_('Sonido cuando habla el propietario del canal'),_('sonido al terminar la búsqueda de mensajes')]
codes.reverse()
langs.reverse()
def retornarCategorias():
	lista=[[_('General')]]
	if categ[0]: lista.append([_('Miembros')])
	if categ[1]: lista.append([_('Donativos')])
	if categ[2]: lista.append([_('Moderadores')])
	if categ[3]: lista.append([_('Usuarios Verificados')])
	if categ[4]: lista.append([_('Favoritos')])
	return lista
lista=retornarCategorias()
for temporal in lista: pos.append(1)
class MyFrame(wx.Frame):
	def __init__(self, *args, **kwds):
		self.name = 'vetube-%s'.format(wx.GetUserId())
		self.instance = wx.SingleInstanceChecker(self.name)
		if self.instance.IsAnotherRunning():
			wx.MessageBox(_('VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta.'), 'Error', wx.ICON_ERROR)
			return False
		if donations: update.donation()
		self.contador=0
		self.dentro=False
		self.dst =""
		kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		if updates: updater.do_update()
		self.SetSize((800, 600))
		self.SetTitle("VeTube")
		self.SetWindowStyle(wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)
		self.handler_keyboard = WXKeyboardHandler(self)
		self.panel_1 = wx.Panel(self, wx.ID_ANY)
		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		self.menu_1 = wx.Button(self.panel_1, wx.ID_ANY, _("&Más opciones"))
		self.menu_1.Bind(wx.EVT_BUTTON, self.opcionesMenu)
		self.menu_1.SetToolTip(_(u"Pulse alt para abrir el menú"))
		self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
		sizer_1.Add(self.notebook_1, 1, wx.EXPAND, 0)
		self.tap_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
		self.notebook_1.AddPage(self.tap_1, _("Inicio"))
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		self.tap_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
		self.notebook_1.AddPage(self.tap_2, _("Favoritos"))
		sizer_favoritos = wx.BoxSizer(wx.VERTICAL)
		self.label_1 = wx.StaticText(self.tap_1, wx.ID_ANY, _("Escriba o pegue una URL de youtube"), style=wx.ALIGN_CENTER_HORIZONTAL)
		sizer_2.Add(self.label_1, 0, 0, 0)
		self.text_ctrl_1 = wx.TextCtrl(self.tap_1, wx.ID_ANY, "", style=wx.TE_AUTO_URL | wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
		self.text_ctrl_1.SetToolTip(_("Escribe o pega una URL"))
		self.text_ctrl_1.Bind(wx.EVT_TEXT, self.mostrarBoton)
		self.text_ctrl_1.Bind(wx.EVT_TEXT_ENTER, self.acceder)
		self.text_ctrl_1.SetFocus()
		sizer_2.Add(self.text_ctrl_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
		self.button_1 = wx.Button(self.tap_1, wx.ID_ANY, _("&Acceder"))
		self.button_1.Bind(wx.EVT_BUTTON, self.acceder)
		self.button_1.Disable()
		sizer_2.Add(self.button_1, 0, 0, 0)
		self.button_2 = wx.Button(self.tap_1, wx.ID_ANY, _("Borrar"))
		self.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
		self.button_2.Disable()
		sizer_2.Add(self.button_2, 0, 0, 0)
		self.tap_1.SetSizer(sizer_2)
		label_favoritos = wx.StaticText(self.tap_2, wx.ID_ANY, _("Tus favoritos: "))
		sizer_favoritos.Add(label_favoritos)
		self.list_favorite = wx.ListBox(self.tap_2, wx.ID_ANY, choices=favs)
		self.list_favorite.Bind(wx.EVT_KEY_UP, self.favoritoTeclas)
		sizer_favoritos.Add(self.list_favorite)

		self.button_borrar_favoritos = wx.Button(self.tap_2, wx.ID_ANY, _("&Borrar favorito"))
		self.button_borrar_favoritos.Bind(wx.EVT_BUTTON, self.borrarFavorito)
		sizer_favoritos.Add(self.button_borrar_favoritos,0,0,0)
		self.tap_2.SetSizer(sizer_favoritos)
		self.panel_1.SetSizer(sizer_1)
		self.Layout()
		self.Maximize()
		self.Centre()
		self.Show()

	# Evento que hace aparecer las opciones del menú
	def opcionesMenu(self, event):
		menu1 = wx.Menu()
		opciones = wx.Menu()
		ayuda = wx.Menu()
		menu1.AppendSubMenu(opciones, _(u"&Opciones"))
		opcion_1 = opciones.Append(wx.ID_ANY, _("Configuración"))
		self.Bind(wx.EVT_MENU, self.appConfiguracion, opcion_1)
		opcion_2 = opciones.Append(wx.ID_ANY, _("Restablecer los ajustes"))
		self.Bind(wx.EVT_MENU, self.restaurar, opcion_2)
		menu1.AppendSubMenu(ayuda, _("&Ayuda"))
		manual = ayuda.Append(wx.ID_ANY, _("¿Cómo usar vetube? (documentación en línea)"))
		self.Bind(wx.EVT_MENU, self.documentacion, manual)
		apoyo = ayuda.Append(wx.ID_ANY, _("Únete a nuestra &causa"))
		self.Bind(wx.EVT_MENU, self.donativo, apoyo)
		itemPageMain = ayuda.Append(wx.ID_ANY, _("&Visita nuestra página de github"))
		self.Bind(wx.EVT_MENU, self.pageMain, itemPageMain)
		actualizador = ayuda.Append(wx.ID_ANY, _("&buscar actualizaciones"))
		self.Bind(wx.EVT_MENU, self.updater, actualizador)
		acercade = menu1.Append(wx.ID_ANY, _("Acerca de"))
		self.Bind(wx.EVT_MENU, self.infoApp, acercade)
		salir = menu1.Append(wx.ID_EXIT)
		self.Bind(wx.EVT_MENU, self.cerrarVentana, salir)
		self.PopupMenu(menu1, self.menu_1.GetPosition())
		menu1.Destroy
	def documentacion(self, evt): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md')
	def pageMain(self, evt): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube')
	def donativo(self, evt): wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')
	def appConfiguracion(self, event):			
		idiomas_disponibles = [""]
		language_dict = translator.LANGUAGES
		for k in language_dict:
			idiomas_disponibles.append(language_dict[k])
		self.dialogo_2 = wx.Dialog(self, wx.ID_ANY, _("Configuración"))
		sizer_5 = wx.BoxSizer(wx.VERTICAL)
		labelConfic = wx.StaticText(self.dialogo_2, -1, _("Categorías"))
		sizer_5.Add(labelConfic, 1, wx.EXPAND, 0)
		self.tree_1 = wx.Treebook(self.dialogo_2, wx.ID_ANY)
		sizer_5.Add(self.tree_1, 1, wx.EXPAND, 0)
		self.treeItem_1 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_1, _("General"))
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
		box_1 = wx.StaticBox(self.treeItem_1, -1, _("Opciones de la app"))
		boxSizer_1 = wx.StaticBoxSizer(box_1,wx.VERTICAL)
		label_language = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("Idioma de VeTube (Requiere reiniciar)"))
		boxSizer_1.Add(label_language)
		self.choice_language = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=langs)
		self.choice_language.SetSelection(codes.index(idioma))
		boxSizer_1.Add(self.choice_language)
		self.check_donaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Activar diálogo de donaciones al inicio de la app."))
		self.check_donaciones.SetValue(donations)
		self.check_donaciones.Bind(wx.EVT_CHECKBOX, self.checarDonaciones)
		boxSizer_1.Add(self.check_donaciones)
		self.check_actualizaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Comprobar si hay actualizaciones al iniciar la app"))
		self.check_actualizaciones.SetValue(updates)
		self.check_actualizaciones.Bind(wx.EVT_CHECKBOX, self.checarActualizaciones)
		boxSizer_1.Add(self.check_actualizaciones)
		label_trans = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("traducción de mensajes: "))
		self.choice_traducir = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=idiomas_disponibles)
		self.choice_traducir.SetSelection(0)
		boxSizer_1.Add(label_trans)
		boxSizer_1.Add(self.choice_traducir)
		sizer_4.Add(boxSizer_1, 1, wx.EXPAND, 0)
		self.treeItem_2 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_2, _("Voz"))
		sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
		box_2 = wx.StaticBox(self.treeItem_2, -1, _("Opciones del habla"))
		boxSizer_2 = wx.StaticBoxSizer(box_2,wx.VERTICAL)
		self.check_1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Usar voz sapi en lugar de lector de pantalla."))
		self.check_1.SetValue(sapi)
		self.check_1.Bind(wx.EVT_CHECKBOX, self.checar)
		boxSizer_2.Add(self.check_1)
		self.chk1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Activar lectura de mensajes automática"))
		self.chk1.SetValue(reader)
		self.chk1.Bind(wx.EVT_CHECKBOX, self.checar1)
		boxSizer_2.Add(self.chk1)
		label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
		boxSizer_2 .Add(label_6)
		self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=lista_voces)
		self.choice_2.SetSelection(voz)
		self.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
		boxSizer_2 .Add(self.choice_2)
		label_8 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Tono: "))
		boxSizer_2 .Add(label_8)
		self.slider_1 = wx.Slider(self.treeItem_2, wx.ID_ANY, tono+10, 0, 20)
		self.slider_1.Bind(wx.EVT_SLIDER, self.cambiarTono)
		boxSizer_2 .Add(self.slider_1)
		label_9 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Volumen: "))
		boxSizer_2 .Add(label_9)
		self.slider_2 = wx.Slider(self.treeItem_2, wx.ID_ANY, volume, 0, 100)
		self.slider_2.Bind(wx.EVT_SLIDER, self.cambiarVolumen)
		boxSizer_2 .Add(self.slider_2)
		label_10 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Velocidad: "))
		boxSizer_2 .Add(label_10)
		self.slider_3 = wx.Slider(self.treeItem_2, wx.ID_ANY, speed+10, 0, 20)
		self.slider_3.Bind(wx.EVT_SLIDER, self.cambiarVelocidad)
		boxSizer_2 .Add(self.slider_3)
		self.boton_prueva = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("&Reproducir prueba."))
		self.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
		boxSizer_2.Add(self.boton_prueva)
		sizer_6.Add(boxSizer_2, 0, 0, 0)
		self.treeItem_3 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.categoriza=wx.ListCtrl(self.treeItem_3, wx.ID_ANY)
		self.categoriza.EnableCheckBoxes()
		for contador in range(5):
			self.categoriza.InsertItem(contador,mensajes_categorias[contador])
			self.categoriza.CheckItem(contador,check=categ[contador])
		self.categoriza.Focus(0)
		sizer_categoriza = wx.BoxSizer()
		sizer_categoriza.Add(self.categoriza, 1, wx.EXPAND)
		self.treeItem_3.SetSizer(sizer_categoriza)
		self.tree_1.AddPage(self.treeItem_3, _('Categorías'))
		self.treeItem_4 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.check_2 = wx.CheckBox(self.treeItem_4, wx.ID_ANY, _("Reproducir sonidos."))
		self.check_2.SetValue(sonidos)
		self.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
		self.soniditos=wx.ListCtrl(self.treeItem_4, wx.ID_ANY)
		self.soniditos.EnableCheckBoxes()
		for contador in range(len(listasonidos)):
			self.soniditos.InsertItem(contador,mensajes_sonidos[contador])
			self.soniditos.CheckItem(contador,check=listasonidos[contador])
		self.soniditos.Focus(0)
		if sonidos: self.soniditos.Enable()
		else: self.soniditos.Disable()
		sizer_soniditos = wx.BoxSizer()
		sizer_soniditos.Add(self.check_2)
		sizer_soniditos.Add(self.soniditos, 1, wx.EXPAND)
		self.reproducir= wx.Button(self.treeItem_4, wx.ID_ANY, _("&Reproducir"))
		self.reproducir.Bind(wx.EVT_BUTTON, self.reproducirSonidos)
		if sonidos: self.reproducir.Enable()
		else: self.reproducir.Disable()
		sizer_soniditos.Add(self.reproducir)
		self.treeItem_4.SetSizer(sizer_soniditos)
		self.tree_1.AddPage(self.treeItem_4, _('Sonidos'))
		self.button_cansel = wx.Button(self.dialogo_2, wx.ID_CANCEL, _("&Cancelar"))
		sizer_5.Add(self.button_cansel, 0, 0, 0)
		self.button_6 = wx.Button(self.dialogo_2, wx.ID_OK, _("&Aceptar"))
		self.button_6.SetDefault()
		sizer_5.Add(self.button_6, 0, 0, 0)
		self.treeItem_1.SetSizer(sizer_4)
		self.treeItem_2.SetSizer(sizer_6)
		self.dialogo_2.SetSizer(sizer_5)		
		self.dialogo_2.SetEscapeId(self.button_cansel.GetId())
		self.dialogo_2.Center()
		hey=self.dialogo_2.ShowModal()
		if hey==wx.ID_OK: self.guardar()
		else: self.dialogo_2.Destroy()
	def reproducirPrueva(self, event):
		leer.silence()
		leer.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
	def infoApp(self, event): wx.MessageBox(_("Creadores del proyecto:")+"\nCésar Verástegui & Johan G.\n"+_("Descripción:\n Lee en voz alta los mensajes de los directos en youtube y twitch, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."), _("Información"), wx.ICON_INFORMATION)
	def cambiarVelocidad(self, event):
		global speed
		value=self.slider_3.GetValue()-10
		leer.set_rate(value)
		speed=value
	def cambiarTono(self, event):
		global tono
		value=self.slider_1.GetValue()-10
		leer.set_pitch(value)
		tono=value
	def cambiarVolumen(self, event):
		global volume
		leer.set_volume(self.slider_2.GetValue())
		volume=self.slider_2.GetValue()
	def mostrarSonidos(self,event):
		global sonidos
		if event.IsChecked():
			sonidos=True
			self.soniditos.Enable()
			self.reproducir.Enable()
		else:
			sonidos=False
			self.soniditos.Disable()
			self.reproducir.Disable()
	def checar(self, event):
		global sapi
		sapi=True if event.IsChecked() else False
	def checar1(self, event):
		global reader
		reader=True if event.IsChecked() else False
	def acceder(self, event=None,url=""):
		if not url: url=self.text_ctrl_1.GetValue()
		if url:
			if 'studio' in url:
				pag=url
				pag=pag.split("/")
				pag=pag[-2]
				url="https://www.youtube.com/watch?v="+pag
			try:
				if 'yout' in url: self.chat=ChatDownloader().get_chat(url,message_groups=["messages", "superchat"])
				elif 'twitch' in url: self.chat=ChatDownloader().get_chat(url,message_groups=["messages", "bits","subscriptions","upgrades"])
				else:
					wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
					return
				self.text_ctrl_1.SetValue(url)
				self.dentro=True
				self.usuarios = []
				self.mensajes = []
				self.dialog_mensaje = wx.Dialog(self, wx.ID_ANY, _("Chat en vivo"))
				sizer_mensaje_1 = wx.BoxSizer(wx.VERTICAL)
				self.label_dialog = wx.StaticText(self.dialog_mensaje, wx.ID_ANY, _("Lectura del chat en vivo..."))
				sizer_mensaje_1.Add(self.label_dialog, 0, 0, 0)
				sizer_mensaje_2 = wx.StdDialogButtonSizer()
				sizer_mensaje_1.Add(sizer_mensaje_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
				self.label_mensaje = wx.StaticText(self.dialog_mensaje, wx.ID_ANY, _("historial  de mensajes: "))
				sizer_mensaje_2.Add(self.label_mensaje, 20, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
				self.list_box_1 = wx.ListBox(self.dialog_mensaje, wx.ID_ANY, choices=[])
				self.list_box_1.SetFocus()
				self.list_box_1.Bind(wx.EVT_KEY_UP, self.historialItemsTeclas)
				sizer_mensaje_1.Add(self.list_box_1, 1, wx.EXPAND | wx.ALL, 4)
				self.boton_opciones = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("&Opciones"))
				self.boton_opciones.Bind(wx.EVT_BUTTON, self.opcionesChat)
				sizer_mensaje_1.Add(self.boton_opciones, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
				button_mensaje_detener = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("&Detener chat"))
				button_mensaje_detener.Bind(wx.EVT_BUTTON,self.detenerLectura)
				sizer_mensaje_2.Add(button_mensaje_detener, 10, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
				sizer_mensaje_2.Realize()
				self.dialog_mensaje.SetSizer(sizer_mensaje_1)
				sizer_mensaje_1.Fit(self.dialog_mensaje)
				self.dialog_mensaje.Centre()
				self.dialog_mensaje.SetEscapeId(button_mensaje_detener.GetId())
				if sonidos and listasonidos[6]: playsound(rutasonidos[6],False)
				leer.speak(_("Ingresando al chat."))
				self.hilo2 = threading.Thread(target=self.iniciarChat)
				self.hilo2.daemon = True
				self.hilo2.start()
				self.dialog_mensaje.ShowModal()
			except Exception as e:
				wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
				self.text_ctrl_1.SetFocus()
		else:
			wx.MessageBox(_("No se puede  acceder porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
			self.text_ctrl_1.SetFocus()
	def opcionesChat(self, event):
		menu = wx.Menu()
		menu.Append(1, _("&Borrar historial de mensajes"))
		menu.Append(2, _("&Exportar los mensajes en un archivo de texto"))
		if self.chat.status!="upcoming": menu.Append(3, _("&Añadir este canal a favoritos"))
		menu.Append(4, _("&Ver estadísticas del chat"))
		menu.Bind(wx.EVT_MENU, self.borrarHistorial, id=1)
		menu.Bind(wx.EVT_MENU, self.guardarLista, id=2)
		if self.chat.status!="upcoming": menu.Bind(wx.EVT_MENU, self.addFavoritos, id=3)
		menu.Bind(wx.EVT_MENU, self.estadisticas, id=4)
		self.boton_opciones.PopupMenu(menu)
		menu.Destroy()
	def estadisticas(self, event):
		for k in range(len(self.mensajes)-1):
			for x in range(len(self.mensajes)-1-k):
				if self.mensajes[x]<self.mensajes[x+1]:
					aux1=self.mensajes[x]
					self.mensajes[x]=self.mensajes[x+1]
					self.mensajes[x+1]=aux1
					aux2=self.usuarios[x]
					self.usuarios[x]=self.usuarios[x+1]
					self.usuarios[x+1]=aux2
		dlg_estadisticas = wx.Dialog(self.dialog_mensaje, wx.ID_ANY, _("Estadísticas del canal:"))
		sizer_estadisticas = wx.BoxSizer(wx.VERTICAL)
		mayor_menor = wx.ListBox(dlg_estadisticas, wx.ID_ANY, choices=[])
		for r in range(len(self.usuarios)): mayor_menor.Append(str(self.usuarios[r])+": "+str(self.mensajes[r]))
		text_ctrl_estadisticas = wx.TextCtrl(dlg_estadisticas, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY)
		text_ctrl_estadisticas.SetValue(_("Total de usuarios: %s\nTotal de mensajes: %s") % (len(self.usuarios), sum(self.mensajes)))
		sizer_estadisticas.Add(text_ctrl_estadisticas, 1, wx.EXPAND | wx.ALL, 4)
		button_estadisticas_cerrar = wx.Button(dlg_estadisticas, wx.ID_CANCEL, _("&Cerrar"))
		dlg_estadisticas.SetSizer(sizer_estadisticas)
		sizer_estadisticas.Fit(dlg_estadisticas)
		dlg_estadisticas.Centre()
		dlg_estadisticas.ShowModal()
		dlg_estadisticas.Destroy()
	def borrarContenido(self, event):
		self.text_ctrl_1.SetValue("")
		self.text_ctrl_1.SetFocus()

	def detenerLectura(self, event):
		global yt,pos,lista
		dlg_mensaje = wx.MessageDialog(self.dialog_mensaje, _("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		if dlg_mensaje.ShowModal() == wx.ID_YES:
			self.dentro=False
			self.contador=0
			yt=0
			pos=[]
			lista=[]
			lista=retornarCategorias()				
			for temporal in lista: pos.append(1)
			leer.silence()
			leer.speak(_("ha finalizado la lectura del chat."))
			self.dst =""
			self.text_ctrl_1.SetValue("")
			self.dialog_mensaje.Destroy()
			self.text_ctrl_1.SetFocus()
			self.handler_keyboard.unregister_all_keys()
	def guardarLista(self, event):
		if self.list_box_1.GetCount()>0:
			dlg_mensaje = wx.FileDialog(self.dialog_mensaje, _("Guardar lista de mensajes"), "", info_dict.get('title'), "*.txt", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
			if dlg_mensaje.ShowModal() == wx.ID_OK:
				with open(dlg_mensaje.GetPath(), "w") as archivo:
					for escribe in range(self.list_box_1.GetCount()): archivo.write(self.list_box_1.GetString(escribe)+ "\n")
				wx.MessageBox(_("Lista de mensajes guardada correctamente."), "info.", wx.ICON_INFORMATION)
			dlg_mensaje.Destroy()
		else: wx.MessageBox(_("No hay mensajes para guardar."), "info.", wx.ICON_INFORMATION)
	def guardar(self):
		global idioma, rest,categ,lista,listasonidos
		rest=False
		categ=[]
		listasonidos=[]
		for contador in range(len(mensajes_categorias)):
			if self.categoriza.IsItemChecked(contador): categ.append(True)
			else: categ.append(False)
		for contador in range(len(mensajes_sonidos)):
			if self.soniditos.IsItemChecked(contador): listasonidos.append(True)
			else: listasonidos.append(False)
		lista=retornarCategorias()
		if idioma!=codes[self.choice_language.GetSelection()]:
			idioma=codes[self.choice_language.GetSelection()]
			rest=True
		escribirConfiguracion()
		if rest:
			dlg = wx.MessageDialog(None, _("Es necesario reiniciar el programa para aplicar el nuevo idioma. ¿desea reiniciarlo ahora?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
			if dlg.ShowModal()==wx.ID_YES: restart.restart_program()
			else: dlg.Destroy()
		if self.choice_traducir.GetStringSelection()!="":
			self.language_dict = translator.LANGUAGES
			for k in self.language_dict:
				if self.language_dict[k] == self.choice_traducir.GetStringSelection(): self.dst = k
		self.dialogo_2.Destroy()
	def borrarHistorial(self,event):
		dlg_2 = wx.MessageDialog(self.dialog_mensaje, _("Está apunto de eliminar del historial aproximadamente ")+str(self.list_box_1.GetCount())+_(" elementos, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		dlg_2.SetYesNoLabels(_("&Eliminar"), _("&Cancelar"))
		if self.list_box_1.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
		elif dlg_2.ShowModal()==wx.ID_YES:
			self.list_box_1.Clear()
			self.list_box_1.SetFocus()
	def restaurar(self, event):
		global lista
		self.dlg_3 = wx.MessageDialog(self, _("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		if self.dlg_3.ShowModal()==wx.ID_YES:
			lista=[]
			asignarConfiguracion()
			escribirConfiguracion()
			lista=retornarCategorias()
	def mostrarBoton(self, event):
		if self.text_ctrl_1.GetValue() != "":
			self.button_1.Enable()
			self.button_2.Enable()
		else:
			self.button_1.Disable()
			self.button_2.Disable()
	def cambiarVoz(self, event):	
		global voz
		voz=event.GetSelection()
		leer.set_voice(lista_voces[event.GetSelection()])
	def historialItemsTeclas(self, event):
		event.Skip()
		if event.GetKeyCode() == 127: self.list_box_1.Delete(self.list_box_1.GetSelection())
		if event.GetKeyCode() == 32:
			leer.silence()
			leer.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
	def iniciarChat(self):
		global info_dict
		ydlop = {'ignoreerrors': True, 'extract_flat': 'in_playlist', 'dump_single_json': True, 'quiet': True}
		with YoutubeDL(ydlop) as ydl: info_dict = ydl.extract_info(self.text_ctrl_1.GetValue(), download=False)
		try: self.label_dialog.SetLabel(info_dict.get('title')+', '+str(info_dict["view_count"])+_(' reproducciones'))
		except: pass
		self.registrarTeclas()
		if 'yout' in self.text_ctrl_1.GetValue(): self.recibirYT()
		elif 'twitch' in self.text_ctrl_1.GetValue(): self.recibirTwich()
	def elementoAnterior(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					if self.contador>0: self.contador-=1
					lector.speak(self.list_box_1.GetString(self.contador))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					if pos[yt]>1: pos[yt]-=1
					lector.speak(lista[yt][pos[yt]])
		if sonidos: self.reproducirMsg()
	def elementoSiguiente(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					if self.contador<self.list_box_1.GetCount()-1: self.contador+=1
					lector.speak(self.list_box_1.GetString(self.contador))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					if pos[yt]<len(lista[yt])-1: pos[yt]+=1
					lector.speak(lista[yt][pos[yt]])
		if sonidos: self.reproducirMsg()
	def copiar(self):
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					copy(self.list_box_1.GetString(self.contador))
					lector.speak(_("¡Copiado!"))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					copy(lista[yt][pos[yt]])
					lector.speak(_("¡Copiado!"))
	def elementoInicial(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					self.contador=0
					lector.speak(self.list_box_1.GetString(self.contador))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					pos[yt]=1
					lector.speak(lista[yt][pos[yt]])
		if sonidos: self.reproducirMsg()
	def elementoFinal(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					self.contador=self.list_box_1.GetCount()-1
					lector.speak(self.list_box_1.GetString(self.contador))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					pos[yt]=len(lista[yt])-1
					lector.speak(lista[yt][pos[yt]])
		if sonidos: self.reproducirMsg()
	def callar(self):
		global reader
		if reader:
			reader=False
			leer.silence()
		else: reader=True
		lector.speak(_("Lectura automática activada.")if reader else _("Lectura automática  desactivada."))
	def cerrarVentana(self, event):
		dialogo_cerrar = wx.MessageDialog(self, _("¿está seguro que desea salir del programa?"), _("¡atención!:"), wx.YES_NO | wx.ICON_ASTERISK)
		if dialogo_cerrar.ShowModal()==wx.ID_YES: self.Destroy()
	def retornarMensaje(self):
		if self.list_box_1.GetCount()>0 and lista[yt][0]=='General': return self.list_box_1.GetString(self.contador)
		if lista[yt][0]!='General' and len(lista[yt])>0: return lista[yt][pos[yt]]
	def mostrarMensaje(self):
		if self.dentro and self.retornarMensaje():
			my_dialog = wx.Dialog(self, wx.ID_ANY, _("mensaje"))
			sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
			self.text_message = wx.TextCtrl(my_dialog, wx.ID_ANY, self.retornarMensaje(), style=wx.TE_CENTRE)
			traducir = wx.Button(my_dialog, wx.ID_ANY, _("&traducir el mensaje al idioma del programa"))
			traducir.Bind(wx.EVT_BUTTON, self.traducirMensaje)
			cancelar = wx.Button(my_dialog, wx.ID_CLOSE, _("&Cerrar"))
			sizer_mensaje.Add(self.text_message, 0, 0, 0)
			sizer_mensaje.Add(traducir,0,0,0)
			sizer_mensaje.Add(cancelar,0,0,0)
			my_dialog.SetSizer(sizer_mensaje)
			sizer_mensaje.Fit(my_dialog)
			my_dialog.Centre()
			my_dialog.SetEscapeId(cancelar.GetId())
			my_dialog.ShowModal()
	def traducirMensaje(self,event):
		self.text_message.SetValue(translator.translate(self.text_message.GetValue(),target=languageHandler.curLang[:2]))
		self.text_message.SetFocus()
	def reproducirMsg(self):
		if lista[yt][0]=='General':
			if self.contador==0 or self.contador==self.list_box_1.GetCount()-1: playsound("sounds/orilla.mp3",False)
			else: playsound("sounds/msj.mp3",False)
		else:
			if pos[yt]<=1 or pos[yt]==len(lista[yt])-1: playsound("sounds/orilla.mp3",False)
			else: playsound("sounds/msj.mp3",False)
	def addFavoritos(self, event):
		if len(favorite)<=0:
			self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
			favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
			escribirFavorito()
			lector.speak("Se a añadido el elemento a favoritos")
		else:
			encontrado=False
			for dato in favorite:
				if dato['titulo']==info_dict.get('title'):
					encontrado=True
					break
			if encontrado: wx.MessageBox(_("al parecer ya tienes ese enlace en tus favoritos"), "error.", wx.ICON_ERROR)
			else:
				self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
				favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
				escribirFavorito()
				lector.speak(_("Se a añadido el elemento a favoritos"))
	def updater(self,event=None):
		update = updater.do_update()
		if update==False:
			if self.GetTitle(): wx.MessageBox(_("Al parecer tienes la última versión del programa"), _("Información"), wx.ICON_INFORMATION)
	def borrarFavorito(self, event=None):
		if self.list_favorite.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
		else:
			favorite.pop(self.list_favorite.GetSelection())
			self.list_favorite.Delete(self.list_favorite.GetSelection())
			escribirFavorito()
	def favoritoTeclas(self,event):
		event.Skip()
		if event.GetKeyCode() == 32: self.acceder(url=favorite[self.list_favorite.GetSelection()]['url'])
	def recibirYT(self):
		global lista
		for message in self.chat:
			if self.dst: message['message'] = translator.translate(text=message['message'], target=self.dst)
			if not message['author']['name'] in self.usuarios:
				self.usuarios.append(message['author']['name'])
				self.mensajes.append(1)
			else:
				c=0
				for a in self.usuarios:
					if a==message['author']['name']:
						self.mensajes[c]+=1
						break
					c+=1
			if message['message_type']=='paid_message' or message['message_type']=='paid_sticker':
				if message['message']!=None:
					if categ[1]:
						for contador in range(len(lista)):
							if lista[contador][0]=='Donativos':
								lista[contador].append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
								break
						if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
					self.list_box_1.Append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
					if lista[yt][0]=='Donativos':
						if reader:
							if sapi: leer.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
							else: lector.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
				else:
					if categ[1]:
						for contador in range(len(lista)):
							if lista[contador][0]=='Donativos':
								lista[contador].append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
								break
						if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
					self.list_box_1.Append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
					if lista[yt][0]=='Donativos':
						if reader:
							if sapi: leer.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
							else: lector.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
			if 'header_secondary_text' in message:
				for t in message['author']['badges']:
					if categ[0]:
						for contador in range(len(lista)):
							if lista[contador][0]=='Miembros':
								lista[contador].append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
								break
						if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
					self.list_box_1.Append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
				if lista[yt][0]=='Miembros':
					if reader:
						if sapi: leer.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
						else: lector.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
			if 'badges' in message['author']:
				for t in message['author']['badges']:
					if 'Owner' in t['title']:
						if categ[2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[7],False)
						self.list_box_1.Append(_('Propietario ')+message['author']['name'] +': ' +message['message'])
						if lista[yt][0]=='Moderadores':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Moderator' in t['title']:
						if categ[2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[4],False)
						self.list_box_1.Append(_('Moderador ')+message['author']['name'] +': ' +message['message'])
						if lista[yt][0]=='Moderadores':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Member' in t['title']:
						if message['message'] == None: pass
						else:
							if categ[0]:
								for contador in range(len(lista)):
									if lista[contador][0]=='Miembros':
										lista[contador].append(message['author']['name'] +': ' +message['message'])
										break
								if sonidos and self.chat.status!="past" and listasonidos[1]: playsound(rutasonidos[1],False)
							self.list_box_1.Append(_('Miembro ')+message['author']['name'] +': ' +message['message'])
							if lista[yt][0]=='Miembros':
								if reader:
									if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
									else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Verified' in t['title']:
						if categ[3]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Usuarios Verificados':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[5]: playsound(rutasonidos[5],False)
						self.list_box_1.Append(message['author']['name'] +_(' (usuario verificado): ') +message['message'])
						if lista[yt][0]=='Usuarios Verificados':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
			else:
				if message['message_type']=='paid_message' or message['message_type']=='paid_sticker': pass
				else:
					if self.dentro:
						if lista[yt][0]=='General':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
						if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
						self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
					else:
						exit()
						self.hilo2.join()
	def recibirTwich(self):
		for message in self.chat:
			if self.dst: message['message'] = translator.translate(text=message['message'], target=self.dst)
			if not message['author']['name'] in self.usuarios:
				self.usuarios.append(message['author']['name'])
				self.mensajes.append(1)
			else:
				c=0
				for a in self.usuarios:
					if a==message['author']['name']:
						self.mensajes[c]+=1
						break
					c+=1
			if 'Cheer' in message['message']:
				divide=message['message'].split()
				dinero=divide[0]
				divide=" ".join(divide[1:])
				if categ[1]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Donativos':
							lista[contador].append(dinero+', '+message['author']['name']+': '+divide)
							break
					if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
				self.list_box_1.Append(dinero+', '+message['author']['name']+': '+divide)
				if lista[yt][0]=='Donativos':
					if reader:
						if sapi: leer.speak(dinero+', '+message['author']['name']+': '+divide)
						else: lector.speak(dinero+', '+message['author']['name']+': '+divide)
				continue
			if message['message_type']=='subscription':
				if categ[0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
							break
					if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
				if lista[yt][0]=='Miembros':
					if reader:
						if sapi: leer.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
						else: lector.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
				continue
			if message['message_type']=='mystery_subscription_gift':
				if categ[0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
							break
					if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
				if lista[yt][0]=='Miembros':
					if reader:
						if sapi: leer.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
						else: lector.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
				continue
			if message['message_type']=='subscription_gift':
				if categ[0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
							break
					if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
				if lista[yt][0]=='Miembros':
					if reader:
						if sapi: leer.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
						else: lector.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
				continue
			if message['message_type']=='resubscription':
				mssg=message['message'].split('! ')
				mssg=str(mssg[1:])
				if categ[0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
							break
					if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
				if lista[yt][0]=='Miembros':
					if reader:
						if sapi: leer.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
						else: lector.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
				continue
			if 'badges' in message['author']:
				for t in message['author']['badges']:
					if 'Moderator' in t['title']:
						if categ[2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[4],False)
						if lista[yt][0]=='Moderadores':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					elif 'Subscriber' in t['title']:
						if categ[0]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Miembros':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[1]: playsound(rutasonidos[1],False)
						if lista[yt][0]=='Miembros':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					elif 'Verified' in t['title']:
						if categ[3]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Usuarios Verificados':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if sonidos and self.chat.status!="past" and listasonidos[5]: playsound(rutasonidos[5],False)
						if lista[yt][0]=='Usuarios Verificados':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					else:
						if lista[yt][0]=='General':
							if reader:
								if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
							if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
						self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
			else:
				if self.dentro:
					if lista[yt][0]=='General':
						if reader:
							if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
							else: lector.speak(message['author']['name'] +': ' +message['message'])
						if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
					self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
				else:
					exit()
					self.hilo2.join()
	def avanzarCategorias(self):
		global yt
		if yt<len(lista)-1: yt+=1
		else: yt=0
		lector.speak(lista[yt][0])
	def retrocederCategorias(self):
		global yt
		if yt<=0: yt=len(lista)-1
		else: yt-=1
		lector.speak(lista[yt][0])
	def destacarMensaje(self):
		global lista,pos
		encontrado=False
		contador=0
		for coso in lista:
			if coso[0]=='Favoritos': encontrado=True
		if not encontrado: lista.append([_('Favoritos')])
		for contador in range(len(lista)):
			if lista[contador]=='Favoritos': break
		if lista[yt][0]=='General': lista[contador].append(self.list_box_1.GetString(self.contador))
		else: lista[contador].append(lista[yt][pos[yt]])
		lector.speak(_('Se agregó el elemento a la lista de favoritos...'))
	def reproducirSonidos(self,event): playsound(rutasonidos[self.soniditos.GetFocusedItem()], False)
	def iniciarBusqueda(self):
		self.my_dialog = wx.Dialog(self, wx.ID_ANY, _("escriba el término de su búsqueda"))
		sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
		self.text_box = wx.TextCtrl(self.my_dialog, wx.ID_ANY,"", style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
		self.text_box.Bind(wx.EVT_TEXT, self.mostrarBuscar)
		self.text_box.Bind(wx.EVT_TEXT_ENTER, self.buscar)
		sizer_mensaje.Add(self.text_box, 0, 0, 0)
		self.buttonbuscar = wx.Button(self.my_dialog, wx.ID_ANY, _("&Buscar"))
		self.buttonbuscar.Bind(wx.EVT_BUTTON,self.buscar)
		sizer_mensaje.Add(self.buttonbuscar,0,0,0)
		cancelar = wx.Button(self.my_dialog, wx.ID_CLOSE, _("&Cerrar"))
		sizer_mensaje.Add(cancelar,0,0,0)
		self.my_dialog.SetSizer(sizer_mensaje)
		sizer_mensaje.Fit(self.my_dialog)
		self.my_dialog.Centre()
		self.my_dialog.SetEscapeId(cancelar.GetId())
		self.my_dialog.ShowModal()
	def mostrarBuscar(self, event):
		if self.text_box.GetValue() != "": self.buttonbuscar.Enable()
		else: self.buttonbuscar.Disable()
	def buscar(self, event):
		if self.text_box.GetValue():
			lista.append([self.text_box.GetValue()])
			pos.append(1)
			self.my_dialog.Close()
			for busqueda in range(self.list_box_1.GetCount()):
				if self.text_box.GetValue() in self.list_box_1.GetString(busqueda).lower(): lista[-1].append(self.list_box_1.GetString(busqueda))
			if len(lista[-1])==1:
				lista.pop(-1)
				pos.pop()
				wx.MessageBox(_("No hay ningún criterio de búsqueda que coincida con el término ingresado."), _("información"), wx.ICON_INFORMATION)
			else:
				if listasonidos[8]: playsound(rutasonidos[8],False)
				leer.speak(_("se encontraron %s resultados") % str(len(lista[-1])-1))
		else:
			wx.MessageBox(_("No hay nada que buscar porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
			self.text_box.SetFocus()
	def borrarBuffer(self):
		if lista[yt][0]!='General' and lista[yt][0]!='Miembros' and lista[yt][0]!='Donativos' and lista[yt][0]!='Moderadores' and lista[yt][0]!='Usuarios Verificados':
			lista.pop(yt)
			pos.pop()
			lector.speak(_('Se eliminó el buffer'))
		else: lector.speak(_('No es posible borrar este buffer'))
	def desactivarSonidos(self):
		global sonidos
		sonidos=False if sonidos else True
		lector.speak(_("Sonidos activados.") if sonidos else _("Sonidos desactivados"))
	def registrarTeclas(self):
		leerTeclas()
		try: self.handler_keyboard.register_keys(eval(mis_teclas))
		except: lector.speak(_("hubo un error al registrar los atajos de teclado globales."))
	def checarDonaciones(self,event):
		global donations
		donations=True if event.IsChecked() else False
	def checarActualizaciones(self,event):
		global updates
		updates= True if event.IsChecked() else False
class MyApp(wx.App):
	def OnInit(self):
		self.frame = MyFrame(None, wx.ID_ANY, "")
		self.SetTopWindow(self.frame)
		self.frame.Show()
		return True
app = MyApp(0)
app.MainLoop()