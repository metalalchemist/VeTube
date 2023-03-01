import wx,languageHandler,fajustes,translator
from google_currency import CODES
from translator import LANGUAGES
from accessible_output2.outputs import  sapi5
from os import path
from playsound import playsound
prueba=sapi5.SAPI5()
lista_voces=prueba.list_voices()
rutasonidos=["sounds/chat.mp3","sounds/chatmiembro.mp3","sounds/miembros.mp3","sounds/donar.mp3","sounds/moderators.mp3","sounds/verified.mp3","sounds/abrirchat.wav","sounds/propietario.mp3","sounds/buscar.wav"]
class configuracionDialog(wx.Dialog):
	def __init__(self, parent):
		global config
		if not path.exists("data.json"): fajustes.escribirConfiguracion()
		config=fajustes.leerConfiguracion()
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
		for k in LANGUAGES: idiomas_disponibles.append(LANGUAGES[k])
		mensajes_categorias=[_('Miembros'),_('Donativos'),_('Moderadores'),_('Usuarios Verificados'),_('Favoritos')]
		mensajes_sonidos=[_('Sonido cuando llega un mensaje'),_('Sonido cuando habla un miembro'),_('Sonido cuando se conecta un miembro'),_('Sonido cuando llega un donativo'),_('Sonido cuando habla un moderador'),_('Sonido cuando habla un usuario verificado'),_('Sonido al ingresar al chat'),_('Sonido cuando habla el propietario del canal'),_('sonido al terminar la búsqueda de mensajes')]
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
		self.check_donaciones.Bind(wx.EVT_CHECKBOX, self.checarDonaciones)
		boxSizer_1.Add(self.check_donaciones)
		self.check_actualizaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Comprobar si hay actualizaciones al iniciar la app"))
		self.check_actualizaciones.SetValue(config['updates'])
		self.check_actualizaciones.Bind(wx.EVT_CHECKBOX, self.checarActualizaciones)
		boxSizer_1.Add(self.check_actualizaciones)
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
		self.check_1.Bind(wx.EVT_CHECKBOX, self.checar)
		boxSizer_2.Add(self.check_1)
		self.chk1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Activar lectura de mensajes automática"))
		self.chk1.SetValue(config['reader'])
		self.chk1.Bind(wx.EVT_CHECKBOX, self.checar1)
		boxSizer_2.Add(self.chk1)
		label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
		boxSizer_2 .Add(label_6)
		self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=lista_voces)
		self.choice_2.SetSelection(config['voz'])
		self.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
		boxSizer_2 .Add(self.choice_2)
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
		for contador in range(5):
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
		self.reproducir.Bind(wx.EVT_BUTTON, self.reproducirSonidos)
		if config['sonidos']: self.reproducir.Enable()
		else: self.reproducir.Disable()
		sizer_soniditos.Add(self.reproducir)
		self.treeItem_4.SetSizer(sizer_soniditos)
		self.tree_1.AddPage(self.treeItem_4, _('Sonidos'))
		self.button_6 = wx.Button(self, wx.ID_OK, _("&Aceptar"))
		self.button_6.SetDefault()
		sizer_5.Add(self.button_6, 0, 0, 0)
		self.button_cansel = wx.Button(self, wx.ID_CANCEL, _("&Cancelar"))
		sizer_5.Add(self.button_cansel, 0, 0, 0)
		self.treeItem_1.SetSizer(sizer_4)
		self.treeItem_2.SetSizer(sizer_6)
		self.SetSizer(sizer_5)		
		self.SetEscapeId(self.button_cansel.GetId())
		self.Center()
	def reproducirPrueva(self, event):
		prueba.silence()
		prueba.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
	def cambiarVelocidad(self, event):
		value=self.slider_3.GetValue()-10
		prueba.set_rate(value)
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
	def checar(self, event): config['sapi']=True if event.IsChecked() else False
	def checar1(self, event): config['reader']=True if event.IsChecked() else False
	def cambiarVoz(self, event):	
		config['voz']=event.GetSelection()
		prueba.set_voice(lista_voces[event.GetSelection()])
	def checarDonaciones(self,event): config['donations']=True if event.IsChecked() else False
	def checarActualizaciones(self,event): config['updates']= True if event.IsChecked() else False
	def reproducirSonidos(self,event): playsound(rutasonidos[self.soniditos.GetFocusedItem()], False)