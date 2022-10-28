#!/usr/bin/python
# -*- coding: <encoding name> -*-
import json,wx,wx.adv,threading,languageHandler,restart,translator,time,keyboard_handler
from keyboard_handler.wx_handler import WXKeyboardHandler
from playsound import playsound
from accessible_output2.outputs import auto, sapi5
from youtube_dl import YoutubeDL
from pyperclip import copy
from chat_downloader import ChatDownloader
from update import updater,update
from os import path,remove
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
categ=[True,True,False,False,False]
listasonidos=[True,True,True,True,True,True,True,True,True]
rutasonidos=["sounds/chat.mp3","sounds/chatmiembro.mp3","sounds/miembros.mp3","sounds/donar.mp3","sounds/moderators.mp3","sounds/verified.mp3","sounds/abrirchat.wav","sounds/propietario.mp3","sounds/buscar.wav"]
lector=auto.Auto()
leer=sapi5.SAPI5()
lista_voces=leer.list_voices()
def escribirJsonLista(arch,lista=[]):
	with open(arch, 'w+') as file: json.dump(lista, file)
def leerJsonLista(arch):
	if path.exists(arch):
		with open (arch) as file: return json.load(file)
	else: return []
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
def convertirLista(lista, val1, val2):
	if len(lista)<=0: return []
	else:
		newlista=[]
		for datos in lista: newlista.append(datos[val1]+': '+datos[val2])
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
	with open('keys.txt', 'w+') as arch: arch.write("""{"control+p": leer.silence,"alt+shift+up": self.elementoAnterior,"alt+shift+down": self.elementoSiguiente,"alt+shift+left": self.retrocederCategorias,"alt+shift+right": self.avanzarCategorias,"alt+shift+home": self.elementoInicial,"alt+shift+end": self.elementoFinal,"alt+shift+f": self.destacarMensaje,"alt+shift+c": self.copiar,"alt+shift+m": self.callar,"alt+shift+s": self.iniciarBusqueda,"alt+shift+v": self.mostrarMensaje,"alt+shift+d": self.borrarBuffer,"alt+shift+p": self.desactivarSonidos,"alt+shift+k": self.createEditor, "alt+shift+a": self.addRecuerdo}""")
	leerTeclas()
def leerTeclas():
	if path.exists("keys.txt"):
		global mis_teclas
		with open ("keys.txt",'r') as arch:
			mis_teclas=arch.read()
	else: escribirTeclas()
pos=[]
leerConfiguracion()
favorite=leerJsonLista('favoritos.json')
mensajes_destacados=leerJsonLista('mensajes_destacados.json')
leer.set_rate(speed)
leer.set_pitch(tono)
leer.set_voice(lista_voces[voz])
leer.set_volume(volume)
favs=convertirLista(favorite,'titulo','url')
msjs=convertirLista(mensajes_destacados,'mensaje','titulo')
languageHandler.setLanguage(idioma)
idiomas = languageHandler.getAvailableLanguages()
langs = []
[langs.append(i[1]) for i in idiomas]
codes = []
[codes.append(i[0]) for i in idiomas]
mensaje_teclas=[_('Silencia la voz sapy'),_('Buffer anterior.'),_('Siguiente buffer.'),_('Mensaje anterior'),_('Mensaje siguiente'),_('Ir al comienzo del buffer'),_('Ir al final del buffer'),_('Destaca un mensaje en el buffer de  favoritos'),_('Copia el mensaje actual'),_('Activa o desactiva la lectura automática'),_('Busca una palabra en los mensajes actuales'),_('Muestra el mensaje actual en un cuadro de texto'),_('borra el buffer seleccionado'),_('activa o desactiva los sonidos del programa'),_('Invocar el editor de combinaciones de teclado')]
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
		self.dentro=False
		self.dst =""
		leerTeclas()
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
		self.button_2 = wx.Button(self.tap_1, wx.ID_ANY, _("&Borrar"))
		self.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
		self.button_2.Disable()
		sizer_2.Add(self.button_2, 0, 0, 0)
		self.tap_1.SetSizer(sizer_2)
		label_favoritos = wx.StaticText(self.tap_2, wx.ID_ANY, _("&Tus favoritos: "))
		sizer_favoritos.Add(label_favoritos)
		self.list_favorite = wx.ListBox(self.tap_2, wx.ID_ANY, choices=favs)
		self.list_favorite.Bind(wx.EVT_KEY_UP, self.favoritoTeclas)
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
		opcion_2 = opciones.Append(wx.ID_ANY, _("Editor de combinaciones de teclado para VeTube"))
		self.Bind(wx.EVT_MENU, self.createEditor, opcion_2)
		opcion_3 = opciones.Append(wx.ID_ANY, _("Restablecer los ajustes"))
		self.Bind(wx.EVT_MENU, self.restaurar, opcion_3)
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
		self.dlg_teclado.SetSizer(sizer)
		sizer.Fit(self.dlg_teclado)
		self.dlg_teclado.Centre()
		self.dlg_teclado.ShowModal()
		self.dlg_teclado.Destroy()
	def editarTeclas(self, event):
		indice=self.combinaciones.GetFocusedItem()
		texto=self.combinaciones.GetItem(indice,1).GetText()
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
		if 'control' in texto: self.check_ctrl.SetValue(True)
		self.check_alt = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Alt"))
		if 'alt' in texto: self.check_alt.SetValue(True)
		self.check_shift = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Shift"))
		if 'shift' in texto: self.check_shift.SetValue(True)
		self.check_win = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Windows"))
		if 'win' in texto: self.check_win.SetValue(True)
		self.teclas = ["enter", "tab", "space", "back", "delete", "home", "end", "pageUp", "pageDown", "up", "down", "left", "right", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
		label_tecla = wx.StaticText(self.dlg_editar_combinacion, wx.ID_ANY, _("&Selecciona una tecla para	la combinación"))
		self.combo_tecla = wx.ComboBox(self.dlg_editar_combinacion, wx.ID_ANY, choices=self.teclas, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		texto=texto.split('+')
		self.combo_tecla.SetValue(texto[-1])
		self.editar= wx.Button(self.dlg_editar_combinacion, -1, _(u"&Aplicar nueva combinación de teclado"))
		self.editar.Bind(wx.EVT_BUTTON, self.editarTeclas2)
		self.editar.SetDefault()
		close = wx.Button(self.dlg_editar_combinacion, wx.ID_CANCEL, _(u"&Cerrar"))
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
		self.dlg_editar_combinacion.SetSizer(sizer)
		sizer.Fit(self.dlg_editar_combinacion)
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
		nueva_combinacion=tecla
		if shift: nueva_combinacion="shift+"+nueva_combinacion
		if alt: nueva_combinacion="alt+"+nueva_combinacion
		if ctrl: nueva_combinacion="control+"+nueva_combinacion
		if win: nueva_combinacion="win+"+nueva_combinacion
		if not ctrl and not alt and not win and not shift:
			wx.MessageBox(_("Debe escoger al menos una tecla de las casillas de berificación"), "error.", wx.ICON_ERROR)
			return
		for busc in range(self.combinaciones.GetItemCount()):
			if busc== indice: continue
			if nueva_combinacion == self.combinaciones.GetItem(busc,1).GetText():
				wx.MessageBox(_("esta combinación ya está siendo usada en la función %s") % mensaje_teclas[busc], "error.", wx.ICON_ERROR)
				return
		global mis_teclas
		if self.dentro:
			self.handler_keyboard.unregister_key(self.combinaciones.GetItem(indice,1).GetText(),mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
			self.handler_keyboard.register_key(nueva_combinacion,mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
		leerTeclas()
		mis_teclas=mis_teclas.replace(self.combinaciones.GetItem(indice,1).GetText(),nueva_combinacion)
		with open("keys.txt", "w") as fichero: fichero.write(mis_teclas)
		self.combinaciones.SetItem(indice, 1, nueva_combinacion)
		self.dlg_editar_combinacion.Close()
		self.combinaciones.SetFocus()
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
			if self.dentro:
				self.handler_keyboard.unregister_all_keys()
				self.handler_keyboard.register_keys(mis_teclas)
	def documentacion(self, evt): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md')
	def pageMain(self, evt): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube')
	def donativo(self, evt): wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')
	def appConfiguracion(self, event):			
		idiomas_disponibles = [""]
		for k in translator.LANGUAGES: idiomas_disponibles.append(translator.LANGUAGES[k])
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
		self.button_6 = wx.Button(self.dialogo_2, wx.ID_OK, _("&Aceptar"))
		self.button_6.SetDefault()
		sizer_5.Add(self.button_6, 0, 0, 0)
		self.button_cansel = wx.Button(self.dialogo_2, wx.ID_CANCEL, _("&Cancelar"))
		sizer_5.Add(self.button_cansel, 0, 0, 0)
		self.treeItem_1.SetSizer(sizer_4)
		self.treeItem_2.SetSizer(sizer_6)
		self.dialogo_2.SetSizer(sizer_5)		
		self.dialogo_2.SetEscapeId(self.button_cansel.GetId())
		self.dialogo_2.Center()
		hey=self.dialogo_2.ShowModal()
		if hey==wx.ID_OK:
			self.guardar()
			leer.silence()
		else:
			self.dialogo_2.Destroy()
			leer.silence()
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
				# poner un menú contextual
				self.list_box_1.Bind(wx.EVT_CONTEXT_MENU, self.historialItemsMenu)
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
		noti =	wx.adv.NotificationMessage(_("Mensaje traducido"), _("el mensaje se ha traducido al idioma del programa y se  a  copiado en el portapapeles."))
		noti.Show(timeout=10)
		copy(translator.translate(self.list_box_1.GetString(self.list_box_1.GetSelection()),target=languageHandler.curLang[:2]))
	def copiarMensaje(self, event):
		noti =	wx.adv.NotificationMessage(_("Mensaje copiado al portapapeles"), _("El mensaje seleccionado ha sido copiado al portapapeles."))
		noti.Show(timeout=10)
		copy(self.list_box_1.GetString(self.list_box_1.GetSelection()))
	def opcionesChat(self, event):
		menu = wx.Menu()
		menu.Append(1, _("&Borrar historial de mensajes"))
		menu.Append(2, _("&Exportar los mensajes en un archivo de texto"))
		if self.chat.status!="upcoming": menu.Append(3, _("&Añadir este canal a favoritos"))
		menu.Append(4, _("&Ver estadísticas del chat"))
		menu.Append(8, _("&Copiar enlace del chat al portapapeles"))
		menu.Append(9, _("&Reproducir video en el navegador"))
		menu.Bind(wx.EVT_MENU, self.borrarHistorial, id=1)
		menu.Bind(wx.EVT_MENU, self.guardarLista, id=2)
		if self.chat.status!="upcoming": menu.Bind(wx.EVT_MENU, self.addFavoritos, id=3)
		menu.Bind(wx.EVT_MENU, self.estadisticas, id=4)
		menu.Bind(wx.EVT_MENU, self.copiarEnlace, id=8)
		menu.Bind(wx.EVT_MENU, self.reproducirVideo, id=9)
		self.boton_opciones.PopupMenu(menu)
		menu.Destroy()

	def copiarEnlace(self, event):
		noti =	wx.adv.NotificationMessage(_("Enlace copiado al portapapeles"), _("El enlace del chat ha sido copiado al portapapeles."))
		noti.Show(timeout=10)
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
		self.dlg_estadisticas = wx.Dialog(self.dialog_mensaje, wx.ID_ANY, _("Estadísticas del canal:"))
		sizer_estadisticas = wx.BoxSizer(wx.VERTICAL)
		label_estadisticas = wx.StaticText(self.dlg_estadisticas, wx.ID_ANY, _("&Usuarios y mensajes:"))
		sizer_estadisticas.Add(label_estadisticas, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)
		self.mayor_menor = wx.ListCtrl(self.dlg_estadisticas, wx.ID_ANY, style=wx.LC_REPORT)
		self.mayor_menor.InsertColumn(0, _("Usuario: "))
		self.mayor_menor.InsertColumn(1, _("Cantidad de mensajes: "))
		for i in range(len(self.mensajes)): self.mayor_menor.InsertItem(i, self.usuarios[i])
		for i in range(len(self.mensajes)): self.mayor_menor.SetItem(i, 1, str(self.mensajes[i]))
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
		self.dlg_estadisticas.SetSizer(sizer_estadisticas)
		sizer_estadisticas.Fit(self.dlg_estadisticas)
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
			for k in translator.LANGUAGES:
				if translator.LANGUAGES[k] == self.choice_traducir.GetStringSelection():
					self.dst = k
					break
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
		if event.GetKeyCode() == 32:
			leer.silence()
			leer.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
	def iniciarChat(self):
		global info_dict
		ydlop = {'ignoreerrors': True, 'extract_flat': 'in_playlist', 'dump_single_json': True, 'quiet': True}
		with YoutubeDL(ydlop) as ydl: info_dict = ydl.extract_info(self.text_ctrl_1.GetValue(), download=False)
		try: self.label_dialog.SetLabel(info_dict.get('title')+', '+str(info_dict["view_count"])+_(' reproducciones'))
		except: pass
		try: self.handler_keyboard.register_keys(eval(mis_teclas))
		except keyboard_handler.KeyboardHandlerError: wx.MessageBox(_("Hubo un error al registrar los atajos de teclado globales."), "Error", wx.ICON_ERROR)
		except: self.handler_keyboard.register_keys(mis_teclas)
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
		if sonidos: self.reproducirMsg()
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
		if sonidos: self.reproducirMsg()
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
		if sonidos: self.reproducirMsg()
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
		if self.list_box_1.GetCount()>0 and lista[yt][0]=='General': return self.list_box_1.GetString(self.list_box_1.GetSelection())
		if lista[yt][0]!='General' and len(lista[yt])>0: return lista[yt][pos[yt]]
	def mostrarMensaje(self,event=None):
		idiomas_disponibles = []
		for k in translator.LANGUAGES: 			idiomas_disponibles.append(translator.LANGUAGES[k])
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
			cancelar = wx.Button(my_dialog, wx.ID_CLOSE, _("&Cerrar"))
			sizer_mensaje.Add(self.text_message, 0, 0, 0)
			sizer_mensaje.Add(self.traducir,0,0,0)
			sizer_mensaje.Add(cancelar,0,0,0)
			my_dialog.SetSizer(sizer_mensaje)
			sizer_mensaje.Fit(my_dialog)
			my_dialog.Centre()
			my_dialog.SetEscapeId(cancelar.GetId())
			my_dialog.ShowModal()
	def cambiarTraducir(self,event): self.traducir.SetLabel(_("&traducir el mensaje" if self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()) != translator.LANGUAGES[languageHandler.curLang[:2]] else "&Traducir mensaje al idioma del programa"))
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
			self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
			favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
		else:
			encontrado=False
			for dato in favorite:
				if dato['titulo']==info_dict.get('title'):
					encontrado=True
					break
			if encontrado or self.list_favorite.GetStrings()==[info_dict.get('title')+': '+self.text_ctrl_1.GetValue()]:
				wx.MessageBox(_("Ya se encuentra en favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
				return
			else:
				self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
				favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
		escribirJsonLista('favoritos.json',favorite)
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
					escribirJsonLista('favoritos.json',favorite)
					self.list_favorite.SetFocus()
			else:
				self.list_favorite.Delete(self.list_favorite.GetSelection())
				favorite.pop(self.list_favorite.GetSelection())
				escribirJsonLista('favoritos.json',favorite)
				lector.speak(_("Se a borrado el elemento de favoritos"))
				self.list_favorite.SetFocus()
		if self.list_favorite.GetCount()<=0: self.list_favorite.Append(_("Tus favoritos aparecerán aquí"))

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
	def checarDonaciones(self,event):
		global donations
		donations=True if event.IsChecked() else False
	def checarActualizaciones(self,event):
		global updates
		updates= True if event.IsChecked() else False

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
		escribirJsonLista('mensajes_destacados.json',mensajes_destacados)
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
					escribirJsonLista('mensajes_destacados.json',mensajes_destacados)
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
					escribirJsonLista('mensajes_destacados.json',mensajes_destacados)
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