#!/usr/bin/python
# -*- coding: <encoding name> -*-
import json,wx,wx.adv,threading,languageHandler,restart,translator,time,funciones,google_currency,fajustes,ajustes
from keyboard_handler.wx_handler import WXKeyboardHandler
from playsound import playsound
from TTS.lector import configurar_tts, detect_onnx_models
from TTS.list_voices import install_piper_voice
from yt_dlp import YoutubeDL
from pyperclip import copy
from chat_downloader import ChatDownloader
from update import updater,update
from os import path,remove,getcwd, makedirs
#from TikTokLive import TikTokLiveClient
#from TikTokLive.types.events import CommentEvent, ConnectEvent
from menu_accesible import Accesible

yt=0
# revisar la configuración primero, ya que necesitamos determinar el sistema TTS a través de ella.
if not path.exists("data.json"): fajustes.escribirConfiguracion()
config=fajustes.leerConfiguracion()
lector=configurar_tts(config['sistemaTTS'])
leer=configurar_tts("sapi5")

def configurar_piper(carpeta_voces):
	global config, lector
	onnx_models = detect_onnx_models(carpeta_voces)
	if onnx_models is None:
		sinvoces = wx.MessageDialog(None, _('Necesitas al menos una voz para poder usar el sintetizador Piper. ¿Quieres abrir nuestra carpeta de Drive para descargar algunos modelos? Si pulsas sí, se abrirá nuestra carpeta seguido de una ventana para instalar una una vez la descargues.'), _("No hay voces instaladas"), wx.YES_NO | wx.ICON_QUESTION)
		abrir_modelos = sinvoces.ShowModal()
		if abrir_modelos == wx.ID_YES:
			wx.LaunchDefaultBrowser("https://drive.google.com/drive/folders/1zFJRTI6CpVw9NkrTiNYOKGga0yn4JXzv?usp=drive_link")
			config, lector = install_piper_voice(config, lector)
		sinvoces.Destroy()
	elif isinstance(onnx_models, str):
		config['voz'] = onnx_models
	else:
		config['voz'] = onnx_models[0]

carpeta_voces = path.join(getcwd(), "piper", "voices")

def escribirTeclas():
	with open('keys.txt', 'w+') as arch: arch.write("""{
"control+p": leer.silence,
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
	leerTeclas()
def leerTeclas():
	if path.exists("keys.txt"):
		global mis_teclas
		with open ("keys.txt",'r') as arch:
			mis_teclas=arch.read()
	else: escribirTeclas()
pos=[]
favorite=funciones.leerJsonLista('favoritos.json')
mensajes_destacados=funciones.leerJsonLista('mensajes_destacados.json')
leer.set_rate(config['speed'])
leer.set_pitch(config['tono'])
leer.set_voice(leer.list_voices()[0])
leer.set_volume(config['volume'])
favs=funciones.convertirLista(favorite,'titulo','url')
msjs=funciones.convertirLista(mensajes_destacados,'mensaje','titulo')
# establecer la voz del lector en piper:
if config['sistemaTTS'] == "piper":
	lector=lector.piperSpeak(f"piper/voices/voice-{ajustes.lista_voces[config['voz']][:-4]}/{ajustes.lista_voces[config['voz']]}")
# establecer idiomas:
languageHandler.setLanguage(config['idioma'])
idiomas = languageHandler.getAvailableLanguages()
langs = []
[langs.append(i[1]) for i in idiomas]
codes = []
[codes.append(i[0]) for i in idiomas]
codes.reverse()
langs.reverse()
mensaje_teclas=[_('Silencia la voz sapy'),_('Mensaje anterior.'),_('Mensaje siguiente'),_('Buffer anterior'),_('Siguiente Buffer'),_('Ir al comienzo del buffer'),_('Ir al final del buffer'),_('Destaca un mensaje en el buffer de  favoritos'),_('Copia el mensaje actual'),_('Activa o desactiva la lectura automática'),_('Busca una palabra en los mensajes actuales'),_('Muestra el mensaje actual en un cuadro de texto'),_('borra el buffer seleccionado'),_('activa o desactiva los sonidos del programa'),_('Invocar el editor de combinaciones de teclado'),_('Archivar un mensaje')]
def retornarCategorias():
	lista=[[_('General')]]
	if config['categorias'][0]: lista.append([_('Miembros')])
	if config['categorias'][1]: lista.append([_('Donativos')])
	if config['categorias'][2]: lista.append([_('Moderadores')])
	if config['categorias'][3]: lista.append([_('Usuarios Verificados')])
	if config['categorias'][4]: lista.append([_('Favoritos')])
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
		# configurar TTS:
		if config['sistemaTTS'] == "piper":
			configurar_piper(carpeta_voces)
		if config['donations']: update.donation()
		self.dentro=False
		self.dst =""
		self.nueva_combinacion=""
		self.divisa="Por defecto"
		leerTeclas()
		kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		if config['updates']: updater.do_update()
		self.SetSize((800, 600))
		self.SetTitle("VeTube")
		self.SetWindowStyle(wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)
		self.handler_keyboard = WXKeyboardHandler(self)
		self.Bind(wx.EVT_CLOSE, self.cerrarVentana)
		self.panel_1 = wx.Panel(self, wx.ID_ANY)
		self.panel_1.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)
		self.sizer_1 = wx.BoxSizer(wx.VERTICAL)
		self.menu_1 = wx.Button(self.panel_1, wx.ID_ANY, _("&Más opciones"))
		self.menu_1.Bind(wx.EVT_BUTTON, self.opcionesMenu)
		self.sizer_1.Add(self.menu_1, 0, wx.EXPAND, 0)
		# aplicar la accesibilidad
		self.menu_1.SetAccessible(Accesible(self.menu_1))
		self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
		self.sizer_1.Add(self.notebook_1, 1, wx.EXPAND, 0)
		self.tap_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
		self.notebook_1.AddPage(self.tap_1, _("Inicio"))
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		self.tap_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
		self.notebook_1.AddPage(self.tap_2, _("Favoritos"))
		sizer_favoritos = wx.BoxSizer(wx.VERTICAL)
		self.label_1 = wx.StaticText(self.tap_1, wx.ID_ANY, _("Escriba o pegue una URL de youtube"), style=wx.ALIGN_CENTER_HORIZONTAL)
		sizer_2.Add(self.label_1, 0, 0, 0)
		self.text_ctrl_1 = wx.TextCtrl(self.tap_1, wx.ID_ANY, "", style=wx.TE_AUTO_URL | wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
		self.text_ctrl_1.Bind(wx.EVT_TEXT, self.mostrarBoton)
		self.text_ctrl_1.Bind(wx.EVT_TEXT_ENTER, self.acceder)
		self.text_ctrl_1.SetFocus()
		sizer_2.Add(self.text_ctrl_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
		self.button_1 = wx.Button(self.tap_1, wx.ID_ANY, _("&Acceder"))
		self.button_1.Bind(wx.EVT_BUTTON, self.acceder)
		self.button_1.Disable()
		sizer_2.Add(self.button_1, 0, 0, 0)
		self.button_2 = wx.Button(self.tap_1, wx.ID_ANY, _("&Borrar"))
		self.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
		self.button_2.Disable()
		sizer_2.Add(self.button_2, 0, 0, 0)
		self.tap_1.SetSizer(sizer_2)
		label_favoritos = wx.StaticText(self.tap_2, wx.ID_ANY, _("&Tus favoritos: "))
		sizer_favoritos.Add(label_favoritos)
		self.list_favorite = wx.ListBox(self.tap_2, wx.ID_ANY, choices=favs)
		self.list_favorite.Bind(wx.EVT_KEY_UP, self.favoritoTeclas)
		# optener la cantidad de elementos
		self.favoritos_num = self.list_favorite.GetCount()
		# Meter la cantidad de favoritos en la segunda pestaña
		self.notebook_1.SetPageText(1, _("Favoritos (%s)") % self.favoritos_num)
		sizer_favoritos.Add(self.list_favorite)
		if not favs or self.list_favorite.GetCount() == 0: self.list_favorite.Append(_("Tus favoritos aparecerán aquí"), 0)
		self.button_borrar_favoritos = wx.Button(self.tap_2, wx.ID_ANY, _("&Borrar favorito"))
		self.button_borrar_favoritos.Bind(wx.EVT_BUTTON, self.borrarFavorito)
		sizer_favoritos.Add(self.button_borrar_favoritos,0,0,0)
		# poner una casilla de verificación para borrar todos los favoritos
		self.borrar_todos_favs = wx.CheckBox(self.tap_2, wx.ID_ANY, _("&Seleccionar todos los elementos"))
		self.borrar_todos_favs.Bind(wx.EVT_CHECKBOX, self.borrarTodosFavoritos)
		sizer_favoritos.Add(self.borrar_todos_favs,0,0,0)
		self.tap_2.SetSizer(sizer_favoritos)
		self.tap_3 = wx.Panel(self.notebook_1, wx.ID_ANY)
		self.notebook_1.AddPage(self.tap_3, _("mensajes archivados"))
		sizer_mensajes = wx.BoxSizer(wx.VERTICAL)
		label_mensajes = wx.StaticText(self.tap_3, wx.ID_ANY, _("&Mensajes archivados: "))
		self.list_mensajes = wx.ListBox(self.tap_3, wx.ID_ANY,choices=msjs)
		# poner un item cuando la lista esté vacía
		if not self.list_mensajes.GetCount(): self.list_mensajes.Append("Tus mensajes archivados aparecerán aquí", 0)
		sizer_mensajes.Add(label_mensajes)
		sizer_mensajes.Add(self.list_mensajes)
		self.button_borrar_mensajes = wx.Button(self.tap_3, wx.ID_ANY, _("&Borrar mensaje"))
		self.button_borrar_mensajes.Bind(wx.EVT_BUTTON, self.borraRecuerdo)
		sizer_mensajes.Add(self.button_borrar_mensajes,0,0,0)
		# crear una casilla para elegir si se quieren seleccionar todos los elementos para borrarlos
		self.check_borrar_todos = wx.CheckBox(self.tap_3, wx.ID_ANY, _("&Seleccionar todos los elementos"))
		self.check_borrar_todos.Bind(wx.EVT_CHECKBOX, self.seleccionarTodos)
		sizer_mensajes.Add(self.check_borrar_todos,0,0,0)
		self.tap_3.SetSizer(sizer_mensajes)
		self.panel_1.SetSizer(self.sizer_1)
		self.sizer_1.Layout()
		self.SetClientSize(self.sizer_1.CalcMin())
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
		opcion_3 = opciones.Append(wx.ID_ANY, _("Restablecer los ajustes"))
		self.Bind(wx.EVT_MENU, self.restaurar, opcion_3)
		menu1.AppendSubMenu(ayuda, _("&Ayuda"))
		manual = ayuda.Append(wx.ID_ANY, _("¿Cómo usar vetube? (documentación en línea)"))
		self.Bind(wx.EVT_MENU, lambda event: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md'), manual)
		apoyo = ayuda.Append(wx.ID_ANY, _("Únete a nuestra &causa"))
		self.Bind(wx.EVT_MENU, lambda event: wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U'), apoyo)
		itemPageMain = ayuda.Append(wx.ID_ANY, _("&Visita nuestra página de github"))
		self.Bind(wx.EVT_MENU, lambda event: wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube'), itemPageMain)
		actualizador = ayuda.Append(wx.ID_ANY, _("&buscar actualizaciones"))
		self.Bind(wx.EVT_MENU, self.updater, actualizador)
		acercade = menu1.Append(wx.ID_ANY, _("Acerca de"))
		self.Bind(wx.EVT_MENU, self.infoApp, acercade)
		salir = menu1.Append(wx.ID_EXIT, _("&Salir...\tAlt+F4"))
		self.Bind(wx.EVT_MENU, self.cerrarVentana, salir)
		self.PopupMenu(menu1, self.menu_1.GetPosition())
		menu1.Destroy
	# Evento para acer aparecer el menú con la tecla alt
	def OnCharHook(self, event):
		code = event.GetKeyCode()
		# alt mas m
		if code == 77 and event.AltDown(): self.opcionesMenu(event)
		elif wx.GetKeyState(wx.WXK_F1): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md')
		else: event.Skip()
	def createEditor(self,event=None):
		global mis_teclas
		try: mis_teclas=eval(mis_teclas)
		except: pass
		self.dlg_teclado = wx.Dialog(None, wx.ID_ANY, _("Editor de combinaciones de teclado para Vetube"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		label_editor = wx.StaticText(self.dlg_teclado, wx.ID_ANY, _("&Selecciona la combinación de teclado a editar"))
		self.combinaciones= wx.ListCtrl(self.dlg_teclado, wx.ID_ANY, style=wx.LC_REPORT)
		self.combinaciones.InsertColumn(0, _("acción: "))
		self.combinaciones.InsertColumn(1, _("combinación de teclas: "))
		for i in range(len(mensaje_teclas)): self.combinaciones.InsertItem(i, mensaje_teclas[i])
		c=0
		for valor in mis_teclas:
			self.combinaciones.SetItem(c, 1, valor)
			c+=1
		self.combinaciones.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.editarTeclas)
		self.combinaciones.Focus(0)
		self.combinaciones.SetFocus()
		editar= wx.Button(self.dlg_teclado, -1, _(u"&Editar"))
		editar.Bind(wx.EVT_BUTTON, self.editarTeclas)
		editar.SetDefault()
		restaurar=wx.Button(self.dlg_teclado, -1, _(u"&restaurar combinaciones por defecto"))
		restaurar.Bind(wx.EVT_BUTTON, self.restaurarTeclas)
		close = wx.Button(self.dlg_teclado, wx.ID_CANCEL, _(u"&Cerrar"))
		firstSizer = wx.BoxSizer(wx.HORIZONTAL)
		firstSizer.Add(label_editor, 0, wx.ALL, 5)
		firstSizer.Add(self.combinaciones, 0, wx.ALL, 5)
		secondSizer = wx.BoxSizer(wx.HORIZONTAL)
		secondSizer.Add(editar, 0, wx.ALL, 5)
		secondSizer.Add(restaurar, 0, wx.ALL, 5)
		secondSizer.Add(close, 0, wx.ALL, 5)
		sizer.Add(firstSizer, 0, wx.ALL, 5)
		sizer.Add(secondSizer, 0, wx.ALL, 5)
		self.dlg_teclado.SetSizerAndFit(sizer)
		self.dlg_teclado.Centre()
		self.dlg_teclado.ShowModal()
		self.dlg_teclado.Destroy()
		wx.CallLater(100,self.comprobar)
	def comprobar(self):
		if bool(self.dlg_teclado): self.dlg_teclado.Destroy()
	def editarTeclas(self, event):
		indice=self.combinaciones.GetFocusedItem()
		if not self.nueva_combinacion: self.texto=self.combinaciones.GetItem(indice,1).GetText()
		self.dlg_editar_combinacion = wx.Dialog(self.dlg_teclado, wx.ID_ANY, _("Editando la combinación de teclas para %s") % mensaje_teclas[indice])
		sizer = wx.BoxSizer(wx.VERTICAL)
		firstSizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer_check = wx.BoxSizer(wx.HORIZONTAL)
		# el sizer para los botones
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		groupbox = wx.StaticBox(self.dlg_editar_combinacion, wx.ID_ANY, _("Selecciona las teclas que quieres usar"))
		# el sizer para el agrupamiento
		sizer_groupbox = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
		self.check_ctrl = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Control"))
		if 'control' in self.texto: self.check_ctrl.SetValue(True)
		self.check_alt = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Alt"))
		if 'alt' in self.texto: self.check_alt.SetValue(True)
		self.check_shift = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Shift"))
		if 'shift' in self.texto: self.check_shift.SetValue(True)
		self.check_win = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Windows"))
		if 'win' in self.texto: self.check_win.SetValue(True)
		self.teclas = ["return", "tab", "space", "back", "delete", "home", "end", "pageup", "pagedown", "up", "down", "left", "right", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
		label_tecla = wx.StaticText(self.dlg_editar_combinacion, wx.ID_ANY, _("&Selecciona una tecla para la combinación"))
		self.combo_tecla = wx.ComboBox(self.dlg_editar_combinacion, wx.ID_ANY, choices=self.teclas, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		texto=self.texto.split('+')
		self.combo_tecla.SetValue(texto[-1])
		self.editar= wx.Button(self.dlg_editar_combinacion, -1, _(u"&Aplicar nueva combinación de teclado"))
		self.editar.Bind(wx.EVT_BUTTON, self.editarTeclas2)
		self.editar.SetDefault()
		close = wx.Button(self.dlg_editar_combinacion, wx.ID_CANCEL, _(u"&Cerrar"))
		close.Bind(wx.EVT_BUTTON,self.berifica)
		sizer_check.Add(self.check_ctrl, 0, wx.ALL, 5)
		sizer_check.Add(self.check_alt, 0, wx.ALL, 5)
		sizer_check.Add(self.check_shift, 0, wx.ALL, 5)
		sizer_check.Add(self.check_win, 0, wx.ALL, 5)
		sizer_groupbox.Add(sizer_check, 0, wx.ALL, 5)
		sizer.Add(sizer_groupbox, 0, wx.ALL, 5)
		firstSizer.Add(label_tecla, 0, wx.ALL, 5)
		firstSizer.Add(self.combo_tecla, 0, wx.ALL, 5)
		sizer_buttons.Add(self.editar, 0, wx.ALL, 5)
		sizer_buttons.Add(close, 0, wx.ALL, 5)
		sizer.Add(firstSizer, 0, wx.ALL, 5)
		sizer.Add(sizer_buttons, 0, wx.ALL, 5)
		self.dlg_editar_combinacion.SetSizerAndFit(sizer)
		self.dlg_editar_combinacion.Centre()
		self.dlg_editar_combinacion.ShowModal()
		self.dlg_editar_combinacion.Destroy()
	def editarTeclas2(self, event):
		indice=self.combinaciones.GetFocusedItem()
		texto=self.combinaciones.GetItem(indice,1).GetText()
		tecla=self.combo_tecla.GetValue()
		ctrl=self.check_ctrl.GetValue()
		alt=self.check_alt.GetValue()
		shift=self.check_shift.GetValue()
		win=self.check_win.GetValue()
		self.nueva_combinacion=tecla
		if shift: self.nueva_combinacion="shift+"+self.nueva_combinacion
		if alt: self.nueva_combinacion="alt+"+self.nueva_combinacion
		if ctrl: self.nueva_combinacion="control+"+self.nueva_combinacion
		if win: self.nueva_combinacion="win+"+self.nueva_combinacion
		if not ctrl and not alt and not win and not shift:
			wx.MessageBox(_("Debe escoger al menos una tecla de las casillas de berificación"), "error.", wx.ICON_ERROR)
			return
		for busc in range(self.combinaciones.GetItemCount()):
			if busc== indice: continue
			if self.nueva_combinacion == self.combinaciones.GetItem(busc,1).GetText():
				wx.MessageBox(_("esta combinación ya está siendo usada en la función %s") % mensaje_teclas[busc], "error.", wx.ICON_ERROR)
				return
		if self.texto in self.handler_keyboard.active_keys: self.handler_keyboard.unregister_key(self.combinaciones.GetItem(indice,1).GetText(),mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
		self.handler_keyboard.register_key(self.nueva_combinacion,mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
		self.dlg_editar_combinacion.Destroy()
		wx.CallAfter(self.correccion)
	def correccion(self):
		global mis_teclas
		if self.nueva_combinacion not in self.handler_keyboard.active_keys:
			wx.MessageBox(_("esa combinación está siendo usada por el sistema"), "error.", wx.ICON_ERROR)
			self.handler_keyboard.register_key(self.texto,mis_teclas[self.combinaciones.GetItem(self.combinaciones.GetFocusedItem(),1).GetText()])
		else:
			self.texto=self.nueva_combinacion
			self.nueva_combinacion=""
		leerTeclas()
		mis_teclas=mis_teclas.replace(self.combinaciones.GetItem(self.combinaciones.GetFocusedItem(),1).GetText(),self.texto)
		with open("keys.txt", "w") as fichero: fichero.write(mis_teclas)
		mis_teclas=eval(mis_teclas)
		self.combinaciones.SetItem(self.combinaciones.GetFocusedItem(), 1, self.texto)
		self.combinaciones.SetFocus()
	def berifica(self, event):
		self.nueva_combinacion=""
		self.dlg_editar_combinacion.Destroy()
	def restaurarTeclas(self,event):
		dlg_2 = wx.MessageDialog(self.dlg_teclado, _("Está apunto de restaurar las combinaciones a sus valores por defecto, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		if dlg_2.ShowModal()==wx.ID_YES:
			remove("keys.txt")
			leerTeclas()
			global mis_teclas
			mis_teclas=eval(mis_teclas)
			c=0
			for valor in mis_teclas:
				self.combinaciones.SetItem(c, 1, valor)
				c+=1
			self.combinaciones.Focus(0)
			self.combinaciones.SetFocus()
			self.handler_keyboard.unregister_all_keys()
			self.handler_keyboard.register_keys(mis_teclas)
	def appConfiguracion(self, event):			
		self.cf=ajustes.configuracionDialog(self)
		if self.cf.ShowModal()==wx.ID_OK: self.guardar()
	def infoApp(self, event): wx.MessageBox(_("Creadores del proyecto:")+"\nCésar Verástegui & Johan G.\n"+_("Descripción:\n Lee en voz alta los mensajes de los directos en youtube y twitch, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."), _("Información"), wx.ICON_INFORMATION)
	def acceder(self, event=None,url=""):
		if not url: url=self.text_ctrl_1.GetValue()
		if url:
			if 'studio' in url:
				url=url.replace('https://studio.youtube.com/video/','https://www.youtube.com/watch?v=')
				url=url.replace('/livestreaming','/')
			if 'live' in url: url=url.replace('live/','watch?v=')
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
				# poner un menú contextual
				self.list_box_1.Bind(wx.EVT_CONTEXT_MENU, self.historialItemsMenu)
				sizer_mensaje_1.Add(self.list_box_1, 1, wx.EXPAND | wx.ALL, 4)
				self.boton_opciones = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("&Opciones"))
				self.boton_opciones.Bind(wx.EVT_BUTTON, self.opcionesChat)
				self.boton_opciones.SetAccessible(Accesible(self.boton_opciones))
				sizer_mensaje_1.Add(self.boton_opciones, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
				button_mensaje_detener = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("&Detener chat"))
				button_mensaje_detener.Bind(wx.EVT_BUTTON,self.detenerLectura)
				sizer_mensaje_2.Add(button_mensaje_detener, 10, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
				sizer_mensaje_2.Realize()
				self.dialog_mensaje.SetSizerAndFit(sizer_mensaje_1)
				self.dialog_mensaje.Centre()
				self.dialog_mensaje.SetEscapeId(button_mensaje_detener.GetId())
				if config['sonidos'] and config['listasonidos'][6]: playsound(ajustes.rutasonidos[6],False)
				leer.speak(_("Ingresando al chat."))
				self.hilo2 = threading.Thread(target=self.iniciarChat)
				self.hilo2.daemon = True
				self.hilo2.start()
				self.dialog_mensaje.ShowModal()
			except Exception as e:
				wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."+str(e)), "error.", wx.ICON_ERROR)
				self.text_ctrl_1.SetFocus()
		else:
			wx.MessageBox(_("No se puede  acceder porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
			self.text_ctrl_1.SetFocus()
	def historialItemsMenu(self, event):
		menu = wx.Menu()
		menu.Append(5, _("&Traducir"))
		menu.Bind(wx.EVT_MENU, self.traducirMenu, id=5)
		menu.Append(0, _("&Mostrar el mensaje en un cuadro de texto."))
		menu.Bind(wx.EVT_MENU, self.mostrarMensaje, id=0)
		menu.Append(6, _("&Copiar mensaje al portapapeles"))
		menu.Bind(wx.EVT_MENU, self.copiarMensaje,id=6)
		menu.Append(7, _("&Archivar mensaje"))
		menu.Bind(wx.EVT_MENU, self.addRecuerdo,id=7)
		# if para comprobar si un elemento está seleccionado
		if self.list_box_1.GetSelection() != -1: self.list_box_1.PopupMenu(menu)
		else:
			self.list_box_1.SetSelection(0)
			self.list_box_1.PopupMenu(menu)
		menu.Destroy()
	def traducirMenu(self, event):
		noti =wx.adv.NotificationMessage(_("Mensaje traducido"), _("el mensaje se ha traducido al idioma del programa y se  a  copiado en el portapapeles."))
		noti.Show(timeout=10)
		copy(translator.translate(self.list_box_1.GetString(self.list_box_1.GetSelection()),target=languageHandler.curLang[:2]))
	def copiarMensaje(self, event):
		noti =wx.adv.NotificationMessage(_("Mensaje copiado al portapapeles"), _("El mensaje seleccionado ha sido copiado al portapapeles."))
		noti.Show(timeout=10)
		copy(self.list_box_1.GetString(self.list_box_1.GetSelection()))
	def opcionesChat(self, event):
		menu = wx.Menu()
		menu.Append(10, _("&Editor de combinaciones de teclado para VeTube"))
		menu.Append(1, _("&Borrar historial de mensajes"))
		menu.Append(2, _("E&xportar los mensajes en un archivo de texto"))
		if self.chat.status!="upcoming":
			menu.Append(3, _("&Añadir este canal a favoritos"))
			menu.Bind(wx.EVT_MENU, self.addFavoritos, id=3)
		menu.Append(4, _("&Ver estadísticas del chat"))
		menu.Append(8, _("&Copiar enlace del chat al portapapeles"))
		menu.Append(9, _("&Reproducir video en el navegador"))
		menu.Bind(wx.EVT_MENU, self.createEditor, id=10)
		menu.Bind(wx.EVT_MENU, self.borrarHistorial, id=1)
		menu.Bind(wx.EVT_MENU, self.guardarLista, id=2)
		menu.Bind(wx.EVT_MENU, self.estadisticas, id=4)
		menu.Bind(wx.EVT_MENU, self.copiarEnlace, id=8)
		menu.Bind(wx.EVT_MENU, self.reproducirVideo, id=9)
		self.boton_opciones.PopupMenu(menu)
		menu.Destroy()
	def copiarEnlace(self, event):
		noti =	wx.adv.NotificationMessage(_("Enlace copiado al portapapeles"), _("El enlace del chat ha sido copiado al portapapeles."))
		noti.Show(timeout=5)
		if not self.dentro: url=favorite[self.list_favorite.GetSelection()]['url']
		else: url=self.text_ctrl_1.GetValue()
		copy(url)
	def reproducirVideo(self, event):
		if not self.dentro: url=favorite[self.list_favorite.GetSelection()]['url']
		else: url=self.text_ctrl_1.GetValue()
		wx.LaunchDefaultBrowser(url)
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
		self.dlg_estadisticas = wx.Dialog(self.dialog_mensaje, wx.ID_ANY, _("Estadísticas del chat:"))
		sizer_estadisticas = wx.BoxSizer(wx.VERTICAL)
		label_estadisticas = wx.StaticText(self.dlg_estadisticas, wx.ID_ANY, _("&Usuarios y mensajes:"))
		sizer_estadisticas.Add(label_estadisticas, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)
		self.mayor_menor = wx.ListCtrl(self.dlg_estadisticas, wx.ID_ANY, style=wx.LC_REPORT)
		self.mayor_menor.InsertColumn(0, _("Usuario: "))
		self.mayor_menor.InsertColumn(1, _("Cantidad de mensajes: "))
		for i in range(len(self.mensajes)):
			self.mayor_menor.InsertItem(i, self.usuarios[i])
			self.mayor_menor.SetItem(i, 1, str(self.mensajes[i]))
		sizer_estadisticas.Add(self.mayor_menor, 1, wx.EXPAND | wx.ALL, 4)
		label_total = wx.StaticText(self.dlg_estadisticas, wx.ID_ANY, _("&Estadísticas totales:"))
		sizer_estadisticas.Add(label_total, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)
		self.text_ctrl_estadisticas = wx.TextCtrl(self.dlg_estadisticas, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY)
		self.text_ctrl_estadisticas.SetValue(_("Total de usuarios: %s\nTotal de mensajes: %s") % (len(self.usuarios), sum(self.mensajes)))
		sizer_estadisticas.Add(self.text_ctrl_estadisticas, 1, wx.EXPAND | wx.ALL, 4)
		button_estadisticas_descargar = wx.Button(self.dlg_estadisticas, wx.ID_ANY, _("&Guardar las estadísticas en un archivo de texto"))
		button_estadisticas_descargar.Bind(wx.EVT_BUTTON, self.descargarEstadisticas)
		sizer_estadisticas.Add(button_estadisticas_descargar, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
		button_estadisticas_cerrar = wx.Button(self.dlg_estadisticas, wx.ID_CANCEL, _("&Cerrar"))
		self.dlg_estadisticas.SetSizerAndFit(sizer_estadisticas)
		self.dlg_estadisticas.Centre()
		self.dlg_estadisticas.ShowModal()
		self.dlg_estadisticas.Destroy()
	def descargarEstadisticas(self, event):
		dlg_file	= wx.FileDialog(self.dlg_estadisticas, _("Guardar archivo de texto"), "", "", _("Archivos de texto (*.txt)|*.txt"), wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		dlg_file.SetFilename(_("estadísticas %s %s.txt") % (time.strftime("%d-%m-%Y"),self.chat.title))
		if dlg_file.ShowModal() == wx.ID_OK:
			nombre_archivo = dlg_file.GetFilename()
			directorio = dlg_file.GetDirectory()
			with open(path.join(directorio, nombre_archivo), "w") as archivo:
				archivo.write(_("Estadísticas del canal: %s") % self.chat.title+ "\n")
				archivo.write(self.text_ctrl_estadisticas.GetValue()+ "\n")
				archivo.write(_("Usuarios y mensajes:")+ "\n")
				for i in range(self.mayor_menor.GetItemCount()): archivo.write(self.mayor_menor.GetItemText(i, 0) + " " + self.mayor_menor.GetItemText(i, 1)+ "\n")
		dlg_file.Destroy()
	def borrarContenido(self, event):
		self.text_ctrl_1.SetValue("")
		self.text_ctrl_1.SetFocus()
	def detenerLectura(self, event):
		global yt,pos,lista
		dlg_mensaje = wx.MessageDialog(self.dialog_mensaje, _("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		if dlg_mensaje.ShowModal() == wx.ID_YES:
			self.dentro=False
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
		global lista,config,leer
		rest=False
		config=ajustes.config
		config['categorias']=[]
		config['listasonidos']=[]
		for contador in range(self.cf.categoriza.GetItemCount()):
			if self.cf.categoriza.IsItemChecked(contador): config['categorias'].append(True)
			else: config['categorias'].append(False)
		for contador in range(self.cf.soniditos.GetItemCount()):
			if self.cf.soniditos.IsItemChecked(contador): config['listasonidos'].append(True)
			else: config['listasonidos'].append(False)
		lista=retornarCategorias()
		if config['idioma']!=codes[self.cf.choice_language.GetSelection()]:
			config['idioma']=codes[self.cf.choice_language.GetSelection()]
			rest=True
		with open('data.json', 'w+') as file: json.dump(config, file)
		if rest:
			dlg = wx.MessageDialog(None, _("Es necesario reiniciar el programa para aplicar el nuevo idioma. ¿desea reiniciarlo ahora?"), _("¡Atención!"), wx.YES_NO | wx.ICON_ASTERISK)
			if dlg.ShowModal()==wx.ID_YES: restart.restart_program()
			else: dlg.Destroy()
		if self.cf.choice_traducir.GetStringSelection()!="":
			for k in translator.LANGUAGES:
				if translator.LANGUAGES[k] == self.cf.choice_traducir.GetStringSelection():
					self.dst = k
					break
		if self.cf.choice_moneditas.GetStringSelection()!='Por defecto':
			monedita=self.cf.choice_moneditas.GetStringSelection().split(', (')
			for k in google_currency.CODES:
				if google_currency.CODES[k] == monedita[0]:
					self.divisa = k
					break
		leer=ajustes.prueba
	def borrarHistorial(self,event):
		dlg_2 = wx.MessageDialog(self.dialog_mensaje, _("Está apunto de eliminar del historial aproximadamente ")+str(self.list_box_1.GetCount())+_(" elementos, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		dlg_2.SetYesNoLabels(_("&Eliminar"), _("&Cancelar"))
		if self.list_box_1.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
		elif dlg_2.ShowModal()==wx.ID_YES:
			self.list_box_1.Clear()
			self.list_box_1.SetFocus()
	def restaurar(self, event):
		self.dlg_3 = wx.MessageDialog(self, _("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
		if self.dlg_3.ShowModal()==wx.ID_YES:
			fajustes.escribirConfiguracion()
			restart.restart_program()
	def mostrarBoton(self, event):
		if self.text_ctrl_1.GetValue() != "":
			self.button_1.Enable()
			self.button_2.Enable()
		else:
			self.button_1.Disable()
			self.button_2.Disable()
	def historialItemsTeclas(self, event):
		event.Skip()
		if event.GetKeyCode() == 32:
			leer.silence()
			leer.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
	def iniciarChat(self):
		global info_dict
		ydlop = {'ignoreerrors': True, 'extract_flat': 'in_playlist', 'dump_single_json': True, 'quiet': True}
		with YoutubeDL(ydlop) as ydl: info_dict = ydl.extract_info(self.text_ctrl_1.GetValue(), download=False)
		try: self.label_dialog.SetLabel(info_dict.get('title')+', '+str(info_dict["view_count"])+_(' reproducciones'))
		except: pass
		self.handler_keyboard.register_keys(eval(mis_teclas))
		if 'yout' in self.text_ctrl_1.GetValue(): self.recibirYT()
		elif 'twitch' in self.text_ctrl_1.GetValue(): self.recibirTwich()
	def elementoAnterior(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					if self.list_box_1.GetSelection() == wx.NOT_FOUND: self.list_box_1.SetSelection(0)
					if self.list_box_1.GetSelection() >0: self.list_box_1.SetSelection(self.list_box_1.GetSelection()-1)
					lector.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					if pos[yt]>1: pos[yt]-=1
					lector.speak(lista[yt][pos[yt]])
		if config['sonidos']: self.reproducirMsg()
	def elementoSiguiente(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					if self.list_box_1.GetSelection() == wx.NOT_FOUND: self.list_box_1.SetSelection(0)
					if self.list_box_1.GetSelection() <self.list_box_1.GetCount()-1: self.list_box_1.SetSelection(self.list_box_1.GetSelection()+1)
					lector.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					if pos[yt]<len(lista[yt])-1: pos[yt]+=1
					lector.speak(lista[yt][pos[yt]])
		if config['sonidos']: self.reproducirMsg()
	def copiar(self):
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					if self.list_box_1.GetSelection() == wx.NOT_FOUND: self.list_box_1.SetSelection(0)
					copy(self.list_box_1.GetString(self.list_box_1.GetSelection()))
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
					self.list_box_1.SetSelection(0)
					lector.speak(self.list_box_1.GetString(0))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					pos[yt]=1
					lector.speak(lista[yt][pos[yt]])
		if config['sonidos']: self.reproducirMsg()
	def elementoFinal(self):
		global pos
		if self.dentro:
			if lista[yt][0]=='General':
				if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
				else:
					self.list_box_1.SetSelection(self.list_box_1.GetCount()-1)
					lector.speak(self.list_box_1.GetString(self.list_box_1.GetCount()-1))
			else:
				if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
				else:
					pos[yt]=len(lista[yt])-1
					lector.speak(lista[yt][pos[yt]])
		if config['sonidos']: self.reproducirMsg()
	def callar(self):
		if config['reader']:
			config['reader']=False
			leer.silence()
		else: config['reader']=True
		lector.speak(_("Lectura automática activada.")if config['reader'] else _("Lectura automática  desactivada."))
	def cerrarVentana(self, event):
		dialogo_cerrar = wx.MessageDialog(self, _("¿está seguro que desea salir del programa?"), _("¡atención!"), wx.YES_NO | wx.ICON_ASTERISK)
		if dialogo_cerrar.ShowModal()==wx.ID_YES: wx.GetApp().ExitMainLoop()
	def retornarMensaje(self):
		if self.list_box_1.GetCount()>0 and lista[yt][0]=='General': return self.list_box_1.GetString(self.list_box_1.GetSelection())
		if lista[yt][0]!='General' and len(lista[yt])>0: return lista[yt][pos[yt]]
	def mostrarMensaje(self,event=None):
		idiomas_disponibles =[translator.LANGUAGES[k] for k in LANGUAGES]
		if self.dentro and self.retornarMensaje():
			my_dialog = wx.Dialog(self, wx.ID_ANY, _("mensaje"))
			sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
			label_idioma = wx.StaticText(my_dialog, wx.ID_ANY, _("idioma a traducir:"))
			self.choice_idiomas = wx.Choice(my_dialog, wx.ID_ANY, choices=idiomas_disponibles)
			self.choice_idiomas.SetStringSelection(translator.LANGUAGES[languageHandler.curLang[:2]])
			self.choice_idiomas.Bind(wx.EVT_CHOICE, self.cambiarTraducir)
			self.label_mensaje_texto = wx.StaticText(my_dialog, wx.ID_ANY, label=_("Mensaje en ") +self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()) + ":")
			self.text_message = wx.TextCtrl(my_dialog, wx.ID_ANY, self.retornarMensaje(), style=wx.TE_CENTRE)
			self.text_message.SetFocus()
			self.traducir = wx.Button(my_dialog, wx.ID_ANY, label=_("&traducir el mensaje al idioma del programa"))
			self.traducir.Bind(wx.EVT_BUTTON, self.traducirMensaje)
			cancelar = wx.Button(my_dialog, wx.ID_CANCEL, _("&Cerrar"))
			sizer_mensaje.Add(self.text_message, 0, 0, 0)
			sizer_mensaje.Add(self.traducir,0,0,0)
			sizer_mensaje.Add(cancelar,0,0,0)
			my_dialog.SetSizerAndFit(sizer_mensaje)
			my_dialog.Centre()
			my_dialog.ShowModal()
	def cambiarTraducir(self,event): self.traducir.SetLabel(_("&traducir el mensaje") if self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()) != translator.LANGUAGES[languageHandler.curLang[:2]] else _("&Traducir mensaje al idioma del programa"))
	def traducirMensaje(self,event):
		for k in translator.LANGUAGES:
			if translator.LANGUAGES[k] == self.choice_idiomas.GetStringSelection():
				self.text_message.SetValue(translator.translate(self.text_message.GetValue(),target=k))
				break
		self.label_mensaje_texto.SetLabel(_("Mensaje en ") +self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()))
		self.text_message.SetFocus()
	def reproducirMsg(self):
		if lista[yt][0]=='General':
			if self.list_box_1.GetSelection()==0 or self.list_box_1.GetSelection()==self.list_box_1.GetCount()-1: playsound("sounds/orilla.mp3",False)
			else: playsound("sounds/msj.mp3",False)
		else:
			if pos[yt]<=1 or pos[yt]==len(lista[yt])-1: playsound("sounds/orilla.mp3",False)
			else: playsound("sounds/msj.mp3",False)
	def addFavoritos(self, event):
		if self.list_favorite.GetStrings()==[_("Tus favoritos aparecerán aquí")]: self.list_favorite.Delete(0)
		if len(favorite)<=0:
			if 'twitch' in self.text_ctrl_1.GetValue() and not 'videos' in self.text_ctrl_1.GetValue():
				self.list_favorite.Append(info_dict.get('uploader')+': '+self.text_ctrl_1.GetValue())
				favorite.append({'titulo': info_dict.get('uploader'), 'url': self.text_ctrl_1.GetValue()})
			else:
				self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
				favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
		else:
			if self.list_favorite.GetStrings()==[info_dict.get('title')+': '+self.text_ctrl_1.GetValue()] or self.list_favorite.GetStrings()==[info_dict.get('uploader')+': '+self.text_ctrl_1.GetValue()]:
				wx.MessageBox(_("Ya se encuentra en favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
				return
			else:
				if 'twitch' in self.text_ctrl_1.GetValue() and not 'videos' in self.text_ctrl_1.GetValue():
					self.list_favorite.Append(info_dict.get('uploader')+': '+self.text_ctrl_1.GetValue())
					favorite.append({'titulo': info_dict.get('uploader'), 'url': self.text_ctrl_1.GetValue()})
				else:
					self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
					favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
		funciones.escribirJsonLista('favoritos.json',favorite)
		wx.MessageBox(_("Se ha agregado a favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
	def updater(self,event=None):
		update = updater.do_update()
		if update==False:
			if self.GetTitle(): wx.MessageBox(_("Al parecer tienes la última versión del programa"), _("Información"), wx.ICON_INFORMATION)
	def borrarFavorito(self, event=None):
		if self.list_favorite.GetCount()<=0 or self.list_favorite.GetStrings()[0]==_("Tus favoritos aparecerán aquí"):
			wx.MessageBox(_("No hay favoritos que borrar"), _("Error"), wx.ICON_ERROR)
			self.list_favorite.SetFocus()
		else:
			if self.borrar_todos_favs.GetValue():
				# preguntar
				if wx.MessageBox(_("¿Estás seguro de borrar todos los favoritos de la lista?"), _("¡Atención!"), wx.YES_NO|wx.ICON_QUESTION)==wx.YES:
					self.list_favorite.Clear()
					favorite.clear()
					remove('favoritos.json')
					self.list_favorite.SetFocus()
			else:
				self.list_favorite.Delete(self.list_favorite.GetSelection())
				favorite.pop(self.list_favorite.GetSelection())
				funciones.escribirJsonLista('favoritos.json',favorite)
				lector.speak(_("Se a borrado el elemento de favoritos"))
				self.list_favorite.SetFocus()
		if self.list_favorite.GetCount()<=0: self.list_favorite.Append(_("Tus favoritos aparecerán aquí"))
	def favoritoTeclas(self,event):
		event.Skip()
		if event.GetKeyCode() == 32: self.acceder(url=favorite[self.list_favorite.GetSelection()]['url'])
	def recibirYT(self):
		global lista
		for message in self.chat:
			if message['message']==None: message['message']=''
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
			if 'header_secondary_text' in message:
				for t in message['author']['badges']:
					if config['categorías'][0]:
						for contador in range(len(lista)):
							if lista[contador][0]=='Miembros':
								lista[contador].append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
								break
						if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: playsound(ajustes.rutasonidos[2],False)
					self.list_box_1.Append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
				if lista[yt][0]=='Miembros':
					if config['reader']:
						if config['sapi']: leer.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
						else: lector.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
			if 'badges' in message['author']:
				for t in message['author']['badges']:
					if 'Owner' in t['title']:
						if config['categorias'][2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][4]: playsound(ajustes.rutasonidos[7],False)
						self.list_box_1.Append(_('Propietario ')+message['author']['name'] +': ' +message['message'])
						if lista[yt][0]=='Moderadores':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Moderator' in t['title']:
						if config['categorias'][2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][4]: playsound(ajustes.rutasonidos[4],False)
						self.list_box_1.Append(_('Moderador ')+message['author']['name'] +': ' +message['message'])
						if lista[yt][0]=='Moderadores':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Member' in t['title']:
						if config['categorias'][0]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Miembros':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][1]: playsound(ajustes.rutasonidos[1],False)
						self.list_box_1.Append(_('Miembro ')+message['author']['name'] +': ' +message['message'])
						if lista[yt][0]=='Miembros':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					if 'Verified' in t['title']:
						if config['categorias'][3]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Usuarios Verificados':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][5]: playsound(ajustes.rutasonidos[5],False)
						self.list_box_1.Append(message['author']['name'] +_(' (usuario verificado): ') +message['message'])
						if lista[yt][0]=='Usuarios Verificados':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
			if message['message_type']=='paid_message' or message['message_type']=='paid_sticker':
				if self.divisa!="Por defecto" and self.divisa!=message['money']['currency']:
					moneda=json.loads(google_currency.convert(message['money']['currency'],self.divisa,message['money']['amount']) )
					if moneda['converted']:
						message['money']['currency']=self.divisa
						message['money']['amount']=moneda['amount']
				if config['categorias'][1]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Donativos':
							lista[contador].append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][3]: playsound(ajustes.rutasonidos[3],False)
				self.list_box_1.Append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
				if lista[yt][0]=='Donativos':
					if config['reader']:
						if config['sapi']: leer.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
						else: lector.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
			else:
				if self.dentro:
					if lista[yt][0]=='General':
						if config['reader']:
							if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
							else: lector.speak(message['author']['name'] +': ' +message['message'])
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][0]: playsound(ajustes.rutasonidos[0],False)
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
				divide1=message['message'].split('Cheer')
				if not divide1[0]:
					if self.divisa!='Por defecto': divide1[0]=self.divisa
					else: divide1[0]='Cheer'
					final_msj=divide1[1].split()
					if self.divisa!='Por defecto':
						if self.divisa=='USD':final_msj[0]=int(final_msj[0])/100
						else:
							moneda=json.loads(google_currency.convert('USD',self.divisa,int(final_msj[0])/100) )
							if moneda['converted']: final_msj[0]=moneda['amount']
					dinero=divide1[0]+str(final_msj[0])
					if len(final_msj)==1: divide1=''
					else: divide1=' '.join(final_msj[1:])
				else:
					if self.divisa!='Por defecto':
						if self.divisa=='USD': divide1[1]=int(divide1[1])/100
						else:
							moneda=json.loads(google_currency.convert('USD',self.divisa,int(divide1[1])/100) )
							if moneda['converted']: divide1[1]=moneda['amount']
					if self.divisa!='Por defecto': dinero=self.divisa+str(divide1[1])
					else: dinero='Cheer '+str(divide1[1])
					divide1=' '+divide1[0]
				if config['categorias'][1]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Donativos':
							lista[contador].append(dinero+', '+message['author']['name']+': '+divide1)
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][3]: playsound(ajustes.rutasonidos[3],False)
				self.list_box_1.Append(dinero+', '+message['author']['name']+': '+divide1)
				if lista[yt][0]=='Donativos':
					if config['reader']:
						if config['sapi']: leer.speak(dinero+', '+message['author']['name']+': '+divide1)
						else: lector.speak(dinero+', '+message['author']['name']+': '+divide1)
				continue
			if message['message_type']=='subscription':
				if config['categorias'][0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: playsound(ajustes.rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
				if lista[yt][0]=='Miembros':
					if config['reader']:
						if config['sapi']: leer.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
						else: lector.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
				continue
			if message['message_type']=='mystery_subscription_gift':
				if config['categorias'][0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: playsound(ajustes.rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
				if lista[yt][0]=='Miembros':
					if config['reader']:
						if config['sapi']: leer.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
						else: lector.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
				continue
			if message['message_type']=='subscription_gift':
				if config['categorias'][0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: playsound(ajustes.rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
				if lista[yt][0]=='Miembros':
					if config['reader']:
						if sapi: leer.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
						else: lector.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
				continue
			if message['message_type']=='resubscription':
				mssg=message['message'].split('! ')
				mssg=str(mssg[1:])
				if config['categorias'][0]:
					for contador in range(len(lista)):
						if lista[contador][0]=='Miembros':
							lista[contador].append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
							break
					if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: playsound(ajustes.rutasonidos[2],False)
				self.list_box_1.Append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
				if lista[yt][0]=='Miembros':
					if config['reader']:
						if sapi: leer.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
						else: lector.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
				continue
			if 'badges' in message['author']:
				for t in message['author']['badges']:
					if 'Moderator' in t['title']:
						if config['categorias'][2]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Moderadores':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][4]: playsound(ajustes.rutasonidos[4],False)
						if lista[yt][0]=='Moderadores':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					elif 'Subscriber' in t['title']:
						if config['categorias'][0]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Miembros':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][1]: playsound(ajustes.rutasonidos[1],False)
						if lista[yt][0]=='Miembros':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					elif 'Verified' in t['title']:
						if config['categorias'][3]:
							for contador in range(len(lista)):
								if lista[contador][0]=='Usuarios Verificados':
									lista[contador].append(message['author']['name'] +': ' +message['message'])
									break
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][5]: playsound(ajustes.rutasonidos[5],False)
						if lista[yt][0]=='Usuarios Verificados':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
					else:
						if lista[yt][0]=='General':
							if config['reader']:
								if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
								else: lector.speak(message['author']['name'] +': ' +message['message'])
							if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][0]: playsound(ajustes.rutasonidos[0],False)
						self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
			else:
				if self.dentro:
					if lista[yt][0]=='General':
						if config['reader']:
							if config['sapi']: leer.speak(message['author']['name'] +': ' +message['message'])
							else: lector.speak(message['author']['name'] +': ' +message['message'])
						if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][0]: playsound(ajustes.rutasonidos[0],False)
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
		if lista[yt][0]=='Favoritos': lector.speak(_("no puedes agregar un Favorito del bufer de favoritos"))
		encontrado=False
		contador=0
		for coso in lista:
			if coso[0]=='Favoritos': encontrado=True
		if not encontrado: lista.append([_('Favoritos')])
		pos.append(1)
		for contador in range(len(lista)):
			if lista[contador]=='Favoritos': break
		if lista[yt][0]=='General':
			if self.list_box_1.GetString(self.list_box_1.GetSelection()) in [x for x in lista[contador]]:
				lector.speak(_("este mensaje ya se encuentra en el buffer de favoritos."))
				return
			else: lista[contador].append(self.list_box_1.GetString(self.list_box_1.GetSelection()))
		else:
			if lista[yt][pos[yt]] in [x for x in lista[contador]]:
				lector.speak(_("este mensaje ya se encuentra en el buffer de favoritos."))
				return
			else: lista[contador].append(lista[yt][pos[yt]])
		lector.speak(_('Se agregó el elemento a la lista de favoritos...'))
	def reproducirSonidos(self,event): playsound(ajustes.rutasonidos[self.soniditos.GetFocusedItem()], False)
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
		cancelar = wx.Button(self.my_dialog, wx.ID_CANCEL, _("&Cerrar"))
		sizer_mensaje.Add(cancelar,0,0,0)
		self.my_dialog.SetSizerAndFit(sizer_mensaje)
		self.my_dialog.Centre()
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
				if listasonidos[8]: playsound(ajustes.rutasonidos[8],False)
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
		config['sonidos']=False if config['sonidos'] else True
		lector.speak(_("Sonidos activados.") if config['sonidos'] else _("Sonidos desactivados"))
	def addRecuerdo(self, event=None):
		if self.list_mensajes.GetStrings()[0]==_("Tus mensajes archivados aparecerán aquí"): self.list_mensajes.Delete(0)
		if len(mensajes_destacados)<=0:
			# añadir un nuevo archivado
			if lista[yt][0]=='General':
				self.list_mensajes.Append(self.list_box_1.GetString(self.list_box_1.GetSelection())+': '+info_dict.get('title'))
				mensajes_destacados.append({'mensaje': self.list_box_1.GetString(self.list_box_1.GetSelection()), 'titulo': info_dict.get('title')})
			else:
				self.list_mensajes.Append(lista[yt][pos[yt]]+': '+info_dict.get('title'))
				mensajes_destacados.append({'mensaje': lista[yt][pos[yt]], 'titulo': info_dict.get('title')})
		else:
			if lista[yt][0]=='General':
				if self.list_box_1.GetString(self.list_box_1.GetSelection()) in [x['mensaje'] for x in mensajes_destacados]:
					wx.MessageBox(_("El mensaje ya está archivado."), _("error"), wx.ICON_ERROR)
					return
				else:
					self.list_mensajes.Append(self.list_box_1.GetString(self.list_box_1.GetSelection())+': '+info_dict.get('title'))
					mensajes_destacados.append({'mensaje': self.list_box_1.GetString(self.list_box_1.GetSelection()), 'titulo': info_dict.get('title')})
			else:
				if lista[yt][pos[yt]] in [x['mensaje'] for x in mensajes_destacados]:
					wx.MessageBox(_("El mensaje ya está archivado."), _("error"), wx.ICON_ERROR)
					return
				else:
					self.list_mensajes.Append(lista[yt][pos[yt]]+': '+info_dict.get('title'))
					mensajes_destacados.append({'mensaje': lista[yt][pos[yt]], 'titulo': info_dict.get('title')})
		funciones.escribirJsonLista('mensajes_destacados.json',mensajes_destacados)
		lector.speak(_("se archivó el mensaje"))
	def seleccionarTodos(self, event):
		if self.check_borrar_todos.GetValue():
			self.button_borrar_mensajes.SetLabel(_("&Borrar mensajes"))
			self.button_borrar_mensajes.SetToolTip(_("Borrar todos los mensajes destacados"))
			self.button_borrar_mensajes.SetFocus()
		else:
			self.button_borrar_mensajes.SetLabel(_("&Borrar mensaje"))
			self.button_borrar_mensajes.SetToolTip(_("Borrar el mensaje destacado seleccionado"))
			self.button_borrar_mensajes.SetFocus()
	def borrarTodosFavoritos(self, event):
		if self.borrar_todos_favs.GetValue():
			self.button_borrar_favoritos.SetLabel(_("&Borrar favoritos"))
			self.button_borrar_favoritos.SetToolTip(_("Borrar todos los favoritos"))
			self.button_borrar_favoritos.SetFocus()
		else:
			self.button_borrar_favoritos.SetLabel(_("&Borrar favorito"))
			self.button_borrar_favoritos.SetToolTip(_("Borrar el favorito seleccionado"))
			self.button_borrar_favoritos.SetFocus()
	def borraRecuerdo(self, event):
		# si la casilla está desactivada
		if not self.check_borrar_todos.GetValue():
			if not	self.list_mensajes.GetStrings()[0]=='Tus mensajes archivados aparecerán aquí':
				if len(mensajes_destacados)>0:
					self.list_mensajes.Delete(self.list_mensajes.GetSelection())
					mensajes_destacados.pop(self.list_mensajes.GetSelection())
					funciones.escribirJsonLista('mensajes_destacados.json',mensajes_destacados)
					lector.speak(_("se eliminó el mensaje de tus mensajes archivados"))
					self.list_mensajes.SetFocus()
				else: wx.MessageBox(_("No hay más elementos que borrar"), "Error.", wx.ICON_ERROR)
			else:
				wx.MessageBox(_("No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
				self.list_mensajes.SetFocus()
			if self.list_mensajes.GetCount()<=0: self.list_mensajes.Append(_("Tus mensajes archivados aparecerán aquí"))
		else:
			if len(mensajes_destacados)>0:
				# preguntar
				if wx.MessageBox(_("¿Estás seguro de que quieres borrar todos los mensajes?"), "Confirmación", wx.YES_NO|wx.ICON_QUESTION)==wx.YES:
					mensajes_destacados.clear()
					remove('mensajes_destacados.json')
					self.list_mensajes.Clear()
					self.list_mensajes.Append(_("Tus mensajes archivados aparecerán aquí"))
					lector.speak(_("se eliminaron los mensajes archivados"))
					self.list_mensajes.SetFocus()
			elif	len(mensajes_destacados)<=0:
				wx.MessageBox(_("No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
				self.list_mensajes.SetFocus()
class MyApp(wx.App):
	def OnInit(self):
		self.frame = MyFrame(None, wx.ID_ANY, "")
		self.SetTopWindow(self.frame)
		self.frame.Show()
		return True
app = MyApp(0)
app.MainLoop()