import wx,languageHandler,fajustes
from google_currency import CODES
from translator import TranslatorWrapper
from accessible_output2.outputs import  sapi5
from TTS.lector import configurar_tts, detect_onnx_models
from TTS.list_voices import piper_list_voices, install_piper_voice
from TTS.Piper import Piper, speaker
from os import path
from playsound import playsound
if not path.exists("data.json"): fajustes.escribirConfiguracion()
config=fajustes.leerConfiguracion()

prueba=configurar_tts("sapi5")
prueba_piper=configurar_tts("piper")
lista_voces=prueba.list_voices()
lista_voces_piper = piper_list_voices()
rutasonidos=["sounds/chat.mp3","sounds/chatmiembro.mp3","sounds/miembros.mp3","sounds/donar.mp3","sounds/moderators.mp3","sounds/verified.mp3","sounds/abrirchat.wav","sounds/propietario.mp3","sounds/buscar.wav","sounds/like.wav","sounds/seguirte.mp3","sounds/share.mp3","sounds/chest.mp3"]
class configuracionDialog(wx.Dialog):
	def __init__(self, parent):
		global config, lista_voces, prueba_piper
		# idioma:
		translator = TranslatorWrapper()
		languageHandler.setLanguage(config['idioma'])
		idiomas = languageHandler.getAvailableLanguages()
		langs = []
		[langs.append(i[1]) for i in idiomas]
		codes = []
		[codes.append(i[0]) for i in idiomas]
		codes.reverse()
		langs.reverse()
		idiomas_disponibles = [""]
		monedas=[_('Por defecto')]
		for k in CODES: monedas.append(f'{CODES[k]}, ({k})')
		for k in translator.LANGUAGES: idiomas_disponibles.append(translator.LANGUAGES[k])
		# voces:
		if config['sistemaTTS'] == "piper":
			if not lista_voces_piper is None:
				lista_voces = lista_voces_piper
			else:
				lista_voces = [_("No hay voces instaladas")]
		mensajes_categorias=[_('Mensajes'),_('Miembros'),_('Donativos'),_('Moderadores'),_('Usuarios Verificados'),_('Favoritos')]
		mensajes_sonidos=[_('Sonido cuando llega un mensaje'),_('Sonido cuando habla un miembro'),_('Sonido cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),_('Sonido cuando llega un donativo'),_('Sonido cuando habla un moderador'),_('Sonido cuando habla un usuario verificado'),_('Sonido al ingresar al chat'),_('Sonido cuando habla el propietario del canal'),_('sonido al terminar la búsqueda de mensajes'),_('sonido cuando le dan me gusta al en vivo (solo para tiktok)'),_('Sonido cuando alguien empieza a seguirte en tiktok'),_('Sonido cuando alguien comparte el enlace de tu envivo en  tiktok'),_('Sonido cuando alguien envía un cofre  en tiktok')]
		eventos_lista=[_('Cuando habla un miembro'),_('Cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),_('Cuando llega un donativo'),_('Cuando habla un moderador'),_('Cuando habla un usuario verificado'),_('Cuando le dan me gusta al en vivo (solo para tiktok)'),_('Cuando alguien empieza a seguirte en tiktok'),_('Cuando alguien comparte el enlace de tu envivo en  tiktok'),_('Cuando alguien envía un cofre  en tiktok')]
		super().__init__(parent, title=_("Configuración"))
		sizer_5 = wx.BoxSizer(wx.VERTICAL)
		labelConfic = wx.StaticText(self, -1, _("Categorías"))
		sizer_5.Add(labelConfic, 1, wx.EXPAND, 0)
		self.tree_1 = wx.Treebook(self, wx.ID_ANY)
		sizer_5.Add(self.tree_1, 1, wx.EXPAND, 0)
		self.treeItem_1 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_1, _("General"))
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
		box_1 = wx.StaticBox(self.treeItem_1, -1, _("Opciones de la app"))
		boxSizer_1 = wx.StaticBoxSizer(box_1,wx.VERTICAL)
		label_language = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("Idioma de VeTube (Requiere reiniciar)"))
		boxSizer_1.Add(label_language)
		self.choice_language = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=langs)
		self.choice_language.SetSelection(codes.index(config['idioma']))
		boxSizer_1.Add(self.choice_language)
		self.check_donaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Activar diálogo de donaciones al inicio de la app."))
		self.check_donaciones.SetValue(config['donations'])
		self.check_donaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event,'donations'))
		boxSizer_1.Add(self.check_donaciones)
		self.check_salir = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("preguntar si desea salir de la app al cerrar."))
		self.check_salir.SetValue(config['salir'])
		self.check_salir.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event,'salir'))
		boxSizer_1.Add(self.check_salir)
		self.check_actualizaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Comprobar si hay actualizaciones al iniciar la app"))
		self.check_actualizaciones.SetValue(config['updates'])
		self.check_actualizaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event,'updates'))
		boxSizer_1.Add(self.check_actualizaciones)
		self.check_traduccion = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("intentar traducir las novedades cuando salga una actualización."))
		self.check_traduccion.SetValue(config['traducir'])
		self.check_traduccion.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event,'traducir'))
		boxSizer_1.Add(self.check_traduccion)
		label_trans = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("traducción de mensajes: "))
		self.choice_traducir = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=idiomas_disponibles)
		self.choice_traducir.SetSelection(0)
		boxSizer_1.Add(label_trans)
		boxSizer_1.Add(self.choice_traducir)
		label_monedas = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("convertir las donaciones a la divisa: "))
		self.choice_moneditas = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=monedas)
		self.choice_moneditas.SetSelection(0)
		boxSizer_1.Add(label_monedas)
		boxSizer_1.Add(self.choice_moneditas)
		sizer_4.Add(boxSizer_1, 1, wx.EXPAND, 0)
		self.treeItem_2 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_2, _("Voz"))
		sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
		box_2 = wx.StaticBox(self.treeItem_2, -1, _("Opciones del habla"))
		boxSizer_2 = wx.StaticBoxSizer(box_2,wx.VERTICAL)
		self.check_1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Usar voz sapi en lugar de lector de pantalla."))
		self.check_1.SetValue(config['sapi'])
		self.check_1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar_sapi(event))
		boxSizer_2.Add(self.check_1)
		label_tts = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Sistema TTS a usar: "))
		boxSizer_2 .Add(label_tts)
		self.seleccionar_TTS= wx.Choice(self.treeItem_2, wx.ID_ANY, choices=["auto", "piper", "sapi5"])
		self.seleccionar_TTS.SetStringSelection(config['sistemaTTS'])
		if config['sapi']:
			self.seleccionar_TTS.Disable()
		else:
			self.seleccionar_TTS.Enable()
		self.seleccionar_TTS.Bind(wx.EVT_CHOICE, self.cambiar_sintetizador)
		boxSizer_2 .Add(self.seleccionar_TTS)
		self.chk1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Activar lectura de mensajes automática"))
		self.chk1.SetValue(config['reader'])
		self.chk1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event,'reader'))
		boxSizer_2.Add(self.chk1)
		label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
		boxSizer_2 .Add(label_6)
		self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=lista_voces)
		self.choice_2.SetSelection(config['voz'])
		self.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
		boxSizer_2 .Add(self.choice_2)
		if config['sistemaTTS'] == "piper":
			if len(lista_voces) == 1:
				prueba_piper = speaker.piperSpeak(f"piper/voices/voice-{lista_voces[0][:-4]}/{lista_voces[0]}")
				config['voz'] = 0
		self.instala_voces = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("Instalar un paquete de voz..."))
		self.instala_voces.Bind(wx.EVT_BUTTON, self.instalar_voz_piper)
		boxSizer_2.Add(self.instala_voces)
		if config['sistemaTTS'] == "piper":
			self.instala_voces.Disable()
		label_8 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Tono: "))
		boxSizer_2 .Add(label_8)
		self.slider_1 = wx.Slider(self.treeItem_2, wx.ID_ANY, config['tono']+10, 0, 20)
		self.slider_1.Bind(wx.EVT_SLIDER, self.cambiarTono)
		boxSizer_2 .Add(self.slider_1)
		label_9 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Volumen: "))
		boxSizer_2 .Add(label_9)
		self.slider_2 = wx.Slider(self.treeItem_2, wx.ID_ANY, config['volume'], 0, 100)
		self.slider_2.Bind(wx.EVT_SLIDER, self.cambiarVolumen)
		boxSizer_2 .Add(self.slider_2)
		# desactivar tono/volumen para piper, por ahora no soportados:
		if config['sistemaTTS'] == "piper":
			label_8.Disable()
			self.slider_1.Disable()
			label_9.Disable()
			self.slider_2.Disable()
		label_10 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Velocidad: "))
		boxSizer_2 .Add(label_10)
		self.slider_3 = wx.Slider(self.treeItem_2, wx.ID_ANY, config['speed']+10, 0, 20)
		self.slider_3.Bind(wx.EVT_SLIDER, self.cambiarVelocidad)
		boxSizer_2 .Add(self.slider_3)
		self.boton_prueva = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("&Reproducir prueba."))
		self.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
		boxSizer_2.Add(self.boton_prueva)
		sizer_6.Add(boxSizer_2, 0, 0, 0)
		self.treeItem_3 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.categoriza=wx.ListCtrl(self.treeItem_3, wx.ID_ANY)
		self.categoriza.EnableCheckBoxes()
		for contador in range(6):
			self.categoriza.InsertItem(contador,mensajes_categorias[contador])
			self.categoriza.CheckItem(contador,check=config['categorias'][contador])
		self.categoriza.Focus(0)
		sizer_categoriza = wx.BoxSizer()
		sizer_categoriza.Add(self.categoriza, 1, wx.EXPAND)
		self.treeItem_3.SetSizer(sizer_categoriza)
		self.tree_1.AddPage(self.treeItem_3, _('Categorías'))
		self.treeItem_4 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.check_2 = wx.CheckBox(self.treeItem_4, wx.ID_ANY, _("Reproducir sonidos."))
		self.check_2.SetValue(config['sonidos'])
		self.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
		self.soniditos=wx.ListCtrl(self.treeItem_4, wx.ID_ANY)
		self.soniditos.EnableCheckBoxes()
		for contador in range(len(config['listasonidos'])):
			self.soniditos.InsertItem(contador,mensajes_sonidos[contador])
			self.soniditos.CheckItem(contador,check=config['listasonidos'][contador])
		self.soniditos.Focus(0)
		if config['sonidos']: self.soniditos.Enable()
		else: self.soniditos.Disable()
		sizer_soniditos = wx.BoxSizer()
		sizer_soniditos.Add(self.check_2)
		sizer_soniditos.Add(self.soniditos, 1, wx.EXPAND)
		self.reproducir= wx.Button(self.treeItem_4, wx.ID_ANY, _("&Reproducir"))
		self.reproducir.Bind(wx.EVT_BUTTON, lambda event: playsound(rutasonidos[self.soniditos.GetFocusedItem()], False))
		if config['sonidos']: self.reproducir.Enable()
		else: self.reproducir.Disable()
		sizer_soniditos.Add(self.reproducir)
		self.treeItem_4.SetSizer(sizer_soniditos)
		self.tree_1.AddPage(self.treeItem_4, _('Sonidos'))
		self.treeItem_5 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.eventos=wx.ListCtrl(self.treeItem_5, wx.ID_ANY)
		self.eventos.EnableCheckBoxes()
		for contador in range(len(config['eventos'])):
			self.eventos.InsertItem(contador,eventos_lista[contador])
			self.eventos.CheckItem(contador,check=config['eventos'][contador])
		self.eventos.Focus(0)
		sizer_eventos = wx.BoxSizer()
		sizer_eventos.Add(self.eventos, 1, wx.EXPAND)
		self.treeItem_5.SetSizer(sizer_eventos)
		self.tree_1.AddPage(self.treeItem_5, _('Eventos del chat.'))
		button_6 = wx.Button(self, wx.ID_OK, _("&Aceptar"))
		button_6.SetDefault()
		sizer_5.Add(button_6, 0, 0, 0)
		button_cansel = wx.Button(self, wx.ID_CANCEL, _("&Cancelar"))
		sizer_5.Add(button_cansel, 0, 0, 0)
		self.treeItem_1.SetSizer(sizer_4)
		self.treeItem_2.SetSizer(sizer_6)
		self.SetSizer(sizer_5)		
		self.Center()
	def cambiar_sintetizador(self, event):
		global lista_voces
		config['sistemaTTS']=self.seleccionar_TTS.GetStringSelection()
		if config['sistemaTTS'] == "piper":
			if not lista_voces_piper is None:
				lista_voces = lista_voces_piper
			else:
				lista_voces = [_("No hay voces instaladas")]
			self.instala_voces.Enable()
		else:
			lista_voces = prueba.list_voices()
			self.instala_voces.Disable()
		self.choice_2.Clear()
		self.choice_2.AppendItems(lista_voces)
	def instalar_voz_piper(self, event):
		global config, prueba_piper,lista_voces
		config, prueba_piper = install_piper_voice(config, prueba_piper)
		lista_voces = piper_list_voices()
		if lista_voces:
			self.choice_2.Clear()
			self.choice_2.AppendItems(lista_voces)
	def reproducirPrueva(self, event):
		if not ".onnx" in self.choice_2.GetStringSelection():
			prueba.silence()
			prueba.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
		else:
			prueba_piper.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
	def porcentaje_a_escala(self, porcentaje):
		scale = 2.00 + (1 - ((porcentaje - -10) / (10 - -10))) * (0.50 - 2.00)
		return scale

	def cambiarVelocidad(self, event):
		value=self.slider_3.GetValue()-10
		if not ".onnx" in lista_voces[self.choice_2.GetSelection()]:
			prueba.set_rate(value)
		else:
			prueba_piper.set_rate(self.porcentaje_a_escala(value))
		config['speed']=value
	def cambiarTono(self, event):
		value=self.slider_1.GetValue()-10
		prueba.set_pitch(value)
		config['tono']=value
	def cambiarVolumen(self, event):
		prueba.set_volume(self.slider_2.GetValue())
		config['volume']=self.slider_2.GetValue()
	def mostrarSonidos(self,event):
		if event.IsChecked():
			config['sonidos']=True
			self.soniditos.Enable()
			self.reproducir.Enable()
		else:
			config['sonidos']=False
			self.soniditos.Disable()
			self.reproducir.Disable()
	def checar(self, event,key): config[key]=True if event.IsChecked() else False
	def checar_sapi(self, event):
		config['sapi']=True if event.IsChecked() else False
		self.seleccionar_TTS.Enable(not event.IsChecked())

	def cambiarVoz(self, event):	
		global prueba_piper, lista_voces
		config['voz']=self.choice_2.GetSelection()
		if config['sistemaTTS'] == "piper":
			prueba_piper = speaker.piperSpeak(f"piper/voices/voice-{lista_voces[config['voz']][:-4]}/{lista_voces[config['voz']]}")
		else:
			prueba.set_voice(lista_voces[config['voz']])