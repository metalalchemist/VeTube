# -*- coding: UTF-8 -*-

import wx
import utils.languageHandler as languageHandler # Keep this at top for _
_ = languageHandler.language.gettext # Define _ early

# Standard library imports
from os import path # Used for path.exists

# Third-party imports
from google_currency import CODES # Used for currency choices

# Application-specific imports
from utils import fajustes, app_utilitys # app_utilitys might be needed by event handlers if not passed explicitly
from utils.translator import TranslatorWrapper
from TTS.list_voices import piper_list_voices
from helpers.reader_handler import ReaderHandler
from helpers.sound_helper import playsound

# Import the event handler class
from .ajustes_events import ConfiguracionDialogEvents # Relative import

class configuracionDialogUI(wx.Dialog):
	def __init__(self, parent):
		# Initialize language for the dialog title first if possible
		# This requires self.config to be available for languageHandler.setLanguage
		# Temporary config load for initial language setting
		temp_config = fajustes.leerConfiguracion()
		languageHandler.setLanguage(temp_config.get('idioma', 'en'))
		_ = languageHandler.language.gettext # Re-initialize _ with correct language

		super().__init__(parent, title=_("Configuración"))

		# --- Initialize data as instance attributes ---
		if not path.exists("data.json"):
			fajustes.escribirConfiguracion()
		self.config = fajustes.leerConfiguracion() # Main config for the dialog instance

		# Set language again now that self.config is properly loaded, if different from temp_config
		if temp_config.get('idioma') != self.config.get('idioma'):
			languageHandler.setLanguage(self.config.get('idioma', 'en'))
			_ = languageHandler.language.gettext # Re-initialize _ for safety
			# Note: UI elements already created with old _ won't update. This is a known issue with such dynamic lang changes.
			# Best to set language once before any UI. For a dialog, it's tricky if lang comes from its own config.
			self.SetTitle(_("Configuración")) # Update title if language changed

		self.player = playsound()
		try:
			if 'dispositivo' in self.config:
				self.player.setdevice(int(self.config["dispositivo"]))
		except Exception as e:
			print(f"Error setting player device in configuracionDialogUI: {e}")
			# Potentially fall back to a default device or handle error

		# Initialize ReaderHandler (prueba) based on config if possible
		# Assuming ReaderHandler can take the TTS system string
		self.prueba = ReaderHandler(self.config.get('sistemaTTS', 'piper'))

		self.dispositivos_piper = None # This will be updated by event handlers
		self.lista_voces_piper = piper_list_voices()

		# Determine current list of voices based on TTS system
		if self.config.get('sistemaTTS') == "piper":
			self.lista_voces = self.lista_voces_piper if self.lista_voces_piper else [_("No hay voces instaladas")]
		else:
			try:
				self.lista_voces = self.prueba._leer.list_voices() if hasattr(self.prueba, '_leer') else [_("Voz no disponible")]
			except Exception as e:
				print(f"Error getting system voices: {e}")
				self.lista_voces = [_("Error al cargar voces")]


		self.rutasonidos = [
			"sounds/chat.mp3", "sounds/chatmiembro.mp3", "sounds/miembros.mp3",
			"sounds/donar.mp3", "sounds/moderators.mp3", "sounds/verified.mp3",
			"sounds/abrirchat.wav", "sounds/propietario.mp3", "sounds/buscar.wav",
			"sounds/like.wav", "sounds/seguirte.mp3", "sounds/share.mp3",
			"sounds/chest.mp3"
		]
		self.translator = TranslatorWrapper() # For language name list

		# --- UI Construction (largely from original, ensure self. attributes for controls) ---
		# Idioma data for choices (needs self.config, self.translator)
		# This was local in previous version, now ensure it uses/creates self.attributes if needed by global_refs
		self.idiomas = languageHandler.getAvailableLanguages()
		self.langs = [i[1] for i in self.idiomas]
		self.codes = [i[0] for i in self.idiomas]
		# Original code reversed these, check if that's still needed or if direct indexing is better
		# For now, keeping as is:
		_langs_rev = self.langs[:]
		_codes_rev = self.codes[:]
		_langs_rev.reverse()
		_codes_rev.reverse()


		self.idiomas_disponibles = [_('Por defecto')] + [self.translator.LANGUAGES[k] for k in self.translator.LANGUAGES]
		self.monedas = [_('Por defecto')] + [f'{CODES[k]}, ({k})' for k in CODES]

		# This was effective_lista_voces, now it's self.lista_voces
		# Ensure self.choice_2 uses self.lista_voces

		mensajes_categorias=[
			_('Mensajes'),_('Miembros'),_('Donativos'),_('Moderadores'),_('Usuarios Verificados'),_('Favoritos')
		]
		mensajes_sonidos=[
			_('Sonido cuando llega un mensaje'), _('Sonido cuando habla un miembro'),
			_('Sonido cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),
			_('Sonido cuando llega un donativo'), _('Sonido cuando habla un moderador'),
			_('Sonido cuando habla un usuario verificado'), _('Sonido al ingresar al chat'),
			_('Sonido cuando habla el propietario del canal'), _('sonido al terminar la búsqueda de mensajes'),
			_('sonido cuando le dan me gusta al en vivo (solo para tiktok)'),
			_('Sonido cuando alguien empieza a seguirte en tiktok'),
			_('Sonido cuando alguien comparte el enlace de tu envivo en  tiktok'),
			_('Sonido cuando alguien envía un cofre  en tiktok')
		]
		eventos_lista=[
			_('Cuando habla un miembro'), _('Cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),
			_('Cuando llega un donativo'), _('Cuando habla un moderador'),
			_('Cuando habla un usuario verificado'), _('Cuando le dan me gusta al en vivo (solo para tiktok)'),
			_('Cuando alguien empieza a seguirte en tiktok'),
			_('Cuando alguien comparte el enlace de tu envivo en  tiktok'),
			_('Cuando alguien envía un cofre  en tiktok')
		]

		# Main Sizer
		sizer_5 = wx.BoxSizer(wx.VERTICAL)
		labelConfic = wx.StaticText(self, -1, _("Categorías")) # This label seems misplaced, maybe for Treebook itself?
		# sizer_5.Add(labelConfic, 1, wx.EXPAND, 0) # Commenting out, seems odd for main sizer top item
		self.tree_1 = wx.Treebook(self, wx.ID_ANY)
		sizer_5.Add(self.tree_1, 1, wx.EXPAND, 0)

		# Page 1: General
		self.treeItem_1 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_1, _("General"))
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL) # Main sizer for this page
		box_1 = wx.StaticBox(self.treeItem_1, -1, _("Opciones de la app"))
		boxSizer_1 = wx.StaticBoxSizer(box_1,wx.VERTICAL)

		label_language = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("Idioma de VeTube (Requiere reiniciar)"))
		boxSizer_1.Add(label_language)
		self.choice_language = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=_langs_rev) # Use reversed lists
		try:
			self.choice_language.SetSelection(_codes_rev.index(self.config['idioma']))
		except ValueError:
			if _codes_rev: self.choice_language.SetSelection(0) # Default if not found
		boxSizer_1.Add(self.choice_language)

		self.check_donaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Activar diálogo de donaciones al inicio de la app."))
		self.check_donaciones.SetValue(self.config.get('donations', False))
		boxSizer_1.Add(self.check_donaciones)
		self.check_salir = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("preguntar si desea salir de la app al cerrar."))
		self.check_salir.SetValue(self.config.get('salir', False))
		boxSizer_1.Add(self.check_salir)
		self.check_actualizaciones = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Comprobar si hay actualizaciones al iniciar la app"))
		self.check_actualizaciones.SetValue(self.config.get('updates', True))
		boxSizer_1.Add(self.check_actualizaciones)
		self.check_traduccion = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("intentar traducir las novedades cuando salga una actualización."))
		self.check_traduccion.SetValue(self.config.get('traducir', False))
		boxSizer_1.Add(self.check_traduccion)

		label_trans = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("traducción de mensajes: "))
		self.choice_traducir = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=self.idiomas_disponibles)
		# Set selection for choice_traducir based on config if available
		# Assuming config stores 'translate_to_language_name'
		try:
			self.choice_traducir.SetStringSelection(self.config.get('translate_to_language_name', self.idiomas_disponibles[0]))
		except: # wxPython raises if string not found
			if self.idiomas_disponibles: self.choice_traducir.SetSelection(0)
		boxSizer_1.Add(label_trans)
		boxSizer_1.Add(self.choice_traducir)

		label_monedas = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("convertir las donaciones a la divisa: "))
		self.choice_moneditas = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=self.monedas)
		# Set selection for choice_moneditas based on config if available
		# Assuming config stores 'target_currency' (e.g., "USD")
		target_currency_config = self.config.get('target_currency')
		found_currency = False
		if target_currency_config:
			for i, mon_str in enumerate(self.monedas):
				if f"({target_currency_config})" in mon_str:
					self.choice_moneditas.SetSelection(i)
					found_currency = True
					break
		if not found_currency and self.monedas: self.choice_moneditas.SetSelection(0) # Default "Por defecto"

		boxSizer_1.Add(label_monedas)
		boxSizer_1.Add(self.choice_moneditas)
		sizer_4.Add(boxSizer_1, 1, wx.EXPAND, 0)
		self.treeItem_1.SetSizer(sizer_4)

		# Page 2: Voz
		self.treeItem_2 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_2, _("Voz"))
		sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
		box_2 = wx.StaticBox(self.treeItem_2, -1, _("Opciones del habla"))
		boxSizer_2 = wx.StaticBoxSizer(box_2,wx.VERTICAL)

		self.check_1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Usar voz sapi en lugar de lector de pantalla."))
		self.check_1.SetValue(self.config.get('sapi', False))
		boxSizer_2.Add(self.check_1)

		label_tts = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Sistema TTS a usar: "))
		boxSizer_2.Add(label_tts)
		self.seleccionar_TTS= wx.Choice(self.treeItem_2, wx.ID_ANY, choices=["auto", "piper", "sapi5"]) # TODO: Make these constants or dynamic
		self.seleccionar_TTS.SetStringSelection(self.config.get('sistemaTTS', 'auto'))
		self.seleccionar_TTS.Enable(not self.config.get('sapi', False)) # Disable if SAPI checked
		boxSizer_2.Add(self.seleccionar_TTS)

		self.chk1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Activar lectura de mensajes automática"))
		self.chk1.SetValue(self.config.get('reader', False))
		boxSizer_2.Add(self.chk1)

		label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
		boxSizer_2.Add(label_6)
		self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=self.lista_voces) # Uses self.lista_voces
		if self.lista_voces: # Ensure list is not empty
			try:
				self.choice_2.SetSelection(self.config.get('voz', 0))
			except IndexError: # If config['voz'] is out of bounds
				self.choice_2.SetSelection(0)

		boxSizer_2.Add(self.choice_2)

		self.instala_voces = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("Instalar un paquete de voz..."))
		self.instala_voces.Enable(self.config.get('sistemaTTS') == "piper") # Enable only if Piper is selected
		boxSizer_2.Add(self.instala_voces)

		self.label_8_tono = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Tono: ")) # Renamed to avoid clash if used elsewhere
		boxSizer_2.Add(self.label_8_tono)
		self.slider_1 = wx.Slider(self.treeItem_2, wx.ID_ANY, self.config.get('tono',0)+10, 0, 20) # Default tono 0 -> slider 10
		boxSizer_2.Add(self.slider_1)
		self.label_9_vol = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Volumen: ")) # Renamed
		boxSizer_2.Add(self.label_9_vol)
		self.slider_2 = wx.Slider(self.treeItem_2, wx.ID_ANY, self.config.get('volume',100), 0, 100)
		boxSizer_2.Add(self.slider_2)

		if self.config.get('sistemaTTS') == "piper":
			self.label_8_tono.Disable()
			self.slider_1.Disable()
			self.label_9_vol.Disable()
			self.slider_2.Disable()

		label_10 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Velocidad: "))
		boxSizer_2.Add(label_10)
		self.slider_3 = wx.Slider(self.treeItem_2, wx.ID_ANY, self.config.get('speed',0)+10, 0, 20) # Default speed 0 -> slider 10
		boxSizer_2.Add(self.slider_3)
		self.boton_prueva = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("&Reproducir prueba."))
		boxSizer_2.Add(self.boton_prueva)
		sizer_6.Add(boxSizer_2, 1, wx.EXPAND, 0) # Changed proportion to 1 and added EXPAND
		self.treeItem_2.SetSizer(sizer_6)

		# Page 3: Categorias
		self.treeItem_3 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_3, _('Categorías'))
		sizer_categoriza = wx.BoxSizer(wx.VERTICAL) # Changed to VERTICAL
		self.categoriza = wx.ListCtrl(self.treeItem_3, wx.ID_ANY, style=wx.LC_LIST | wx.LC_REPORT) # Added style
		self.categoriza.EnableCheckBoxes()
		# self.categoriza.InsertColumn(0, _("Categoría"), width=200) # Add a column for better appearance

		for i, cat_name in enumerate(mensajes_categorias): # Max 6 from original
			self.categoriza.InsertItem(i, cat_name)
			self.categoriza.CheckItem(i, check=self.config.get('categorias', [True]*6)[i]) # Default to all true
		sizer_categoriza.Add(self.categoriza, 1, wx.EXPAND|wx.ALL, 5)
		self.treeItem_3.SetSizer(sizer_categoriza)

		# Page 4: Sonidos
		self.treeItem_4 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_4, _('Sonidos'))
		sizer_soniditos_page = wx.BoxSizer(wx.VERTICAL)

		self.check_2 = wx.CheckBox(self.treeItem_4, wx.ID_ANY, _("Activar sonidos"))
		self.check_2.SetValue(self.config.get('sonidos', True))
		sizer_soniditos_page.Add(self.check_2, 0, wx.ALL, 5)

		self.soniditos = wx.ListCtrl(self.treeItem_4, wx.ID_ANY, style=wx.LC_LIST | wx.LC_REPORT) # Added style
		self.soniditos.EnableCheckBoxes()
		# self.soniditos.InsertColumn(0, _("Descripción del Sonido"), width=300) # Add a column

		default_listasonidos_config = [True]*len(mensajes_sonidos) # Default all true
		current_listasonidos_config = self.config.get('listasonidos', default_listasonidos_config)
		for i, sound_desc in enumerate(mensajes_sonidos):
			self.soniditos.InsertItem(i, sound_desc)
			try:
				self.soniditos.CheckItem(i, check=current_listasonidos_config[i])
			except IndexError: # If config list is shorter
				self.soniditos.CheckItem(i, check=True)


		self.soniditos.Enable(self.config.get('sonidos', True))
		sizer_soniditos_page.Add(self.soniditos, 1, wx.EXPAND|wx.ALL, 5)

		# Buttons for sounds page
		sound_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.reproducir = wx.Button(self.treeItem_4, wx.ID_ANY, _("&Reproducir"))
		self.reproducir.Enable(self.config.get('sonidos', True))
		sound_buttons_sizer.Add(self.reproducir, 0, wx.ALL, 5)
		# ... (other sound related buttons if any, like browse for sound) ...
		sizer_soniditos_page.Add(sound_buttons_sizer, 0, wx.ALIGN_LEFT, 0)


		# Audio device selection
		self.dispositivos_audio = self.player.devicenames if hasattr(self.player, 'devicenames') else [_("No devices found")]
		label_dispositivo = wx.StaticText(self.treeItem_4, wx.ID_ANY, _("Seleccionar dispositivo de audio"))
		sizer_soniditos_page.Add(label_dispositivo,0, wx.ALL, 5)
		self.lista_dispositivos = wx.Choice(self.treeItem_4, wx.ID_ANY, choices=self.dispositivos_audio)

		current_device_idx = self.config.get('dispositivo', 1) # Default to 1 (first device)
		if self.dispositivos_audio:
			if 1 <= current_device_idx <= len(self.dispositivos_audio):
				self.lista_dispositivos.SetSelection(current_device_idx - 1)
			else:
				self.lista_dispositivos.SetSelection(0)
		sizer_soniditos_page.Add(self.lista_dispositivos, 0, wx.EXPAND|wx.ALL, 5)
		self.establecer_dispositivo = wx.Button(self.treeItem_4, wx.ID_ANY, label=_("&Establecer"))
		sizer_soniditos_page.Add(self.establecer_dispositivo,0, wx.ALL,5)
		self.treeItem_4.SetSizer(sizer_soniditos_page)

		# Page 5: Eventos
		self.treeItem_5 = wx.Panel(self.tree_1, wx.ID_ANY)
		self.tree_1.AddPage(self.treeItem_5, _('Eventos'))
		sizer_eventos_page = wx.BoxSizer(wx.HORIZONTAL) # As original

		lbl_procesados = wx.StaticText(self.treeItem_5, wx.ID_ANY, _("procesados: "))
		sizer_eventos_page.Add(lbl_procesados, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.eventos = wx.ListCtrl(self.treeItem_5, wx.ID_ANY, style=wx.LC_LIST|wx.LC_REPORT)
		self.eventos.EnableCheckBoxes()
		# self.eventos.InsertColumn(0, _("Evento"), width=200)
		default_eventos_config = [True]*len(eventos_lista)
		current_eventos_config = self.config.get('eventos', default_eventos_config)
		for i, evento_desc in enumerate(eventos_lista):
			self.eventos.InsertItem(i, evento_desc)
			try:
				self.eventos.CheckItem(i, check=current_eventos_config[i])
			except IndexError:
				self.eventos.CheckItem(i, check=True)
		sizer_eventos_page.Add(self.eventos, 1, wx.EXPAND|wx.ALL, 5)

		lbl_leidos = wx.StaticText(self.treeItem_5, wx.ID_ANY, _("leídos")) # "unread"
		sizer_eventos_page.Add(lbl_leidos, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.unread = wx.ListCtrl(self.treeItem_5, wx.ID_ANY, style=wx.LC_LIST|wx.LC_REPORT)
		self.unread.EnableCheckBoxes()
		# self.unread.InsertColumn(0, _("Evento no leído"), width=200)
		default_unread_config = [True]*len(eventos_lista)
		current_unread_config = self.config.get('unread', default_unread_config)
		for i, evento_desc in enumerate(eventos_lista): # Assuming same list of descriptions
			self.unread.InsertItem(i, evento_desc)
			try:
				self.unread.CheckItem(i, check=current_unread_config[i])
			except IndexError:
				self.unread.CheckItem(i, check=True)
		sizer_eventos_page.Add(self.unread, 1, wx.EXPAND|wx.ALL, 5)
		self.treeItem_5.SetSizer(sizer_eventos_page)

		# OK and Cancel buttons for the main dialog sizer (sizer_5)
		# Ensure these are attributes for binding if custom logic is needed beyond wx.ID_OK
		self.button_ok = wx.Button(self, wx.ID_OK, _("&Aceptar"))
		self.button_ok.SetDefault()
		self.button_cancel = wx.Button(self, wx.ID_CANCEL, _("&Cancelar"))

		btnsizer = wx.StdDialogButtonSizer()
		btnsizer.AddButton(self.button_ok)
		btnsizer.AddButton(self.button_cancel)
		btnsizer.Realize()
		sizer_5.Add(btnsizer, 0, wx.EXPAND|wx.ALL, 5)

		self.SetSizer(sizer_5)
		self.Fit() # Fit dialog to sizer content
		self.Center()

		# --- Create global_refs dictionary for event handlers ---
		self.global_refs = {
			'lista_voces': self.lista_voces,
			'lista_voces_piper': self.lista_voces_piper,
			'dispositivos_piper': self.dispositivos_piper,
			'rutasonidos': self.rutasonidos,
			'codes': self.codes, # From UI construction part
			'langs': self.langs, # From UI construction part
			# Add any other 'global-like' things needed by handlers
		}

		# --- Instantiate Event Handler Class ---
		self.events = ConfiguracionDialogEvents()

		# --- Bind Events ---
		# Lambdas pass: event, specific_args..., ui_parent, config, global_refs, player, reader_handler (self.prueba)
		# General Page
		self.check_donaciones.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar(event, 'donations', self, self.config, self.global_refs, self.player, self.prueba)))
		self.check_salir.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar(event, 'salir', self, self.config, self.global_refs, self.player, self.prueba)))
		self.check_actualizaciones.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar(event, 'updates', self, self.config, self.global_refs, self.player, self.prueba)))
		self.check_traduccion.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar(event, 'traducir', self, self.config, self.global_refs, self.player, self.prueba)))
		self.choice_language.Bind(wx.EVT_CHOICE, lambda event: self._update_config(self.events.on_choice_language(event, self, self.config, self.global_refs, self.player, self.prueba)))
		self.choice_traducir.Bind(wx.EVT_CHOICE, lambda event: self._update_config(self.events.on_choice_translate_to(event, self, self.config, self.global_refs, self.player, self.prueba)))
		self.choice_moneditas.Bind(wx.EVT_CHOICE, lambda event: self._update_config(self.events.on_choice_currency(event, self, self.config, self.global_refs, self.player, self.prueba)))

		# Voz Page
		self.check_1.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar_sapi(event, self, self.config, self.global_refs, self.player, self.prueba)))
		self.seleccionar_TTS.Bind(wx.EVT_CHOICE, lambda event: self._update_config_and_globals(self.events.cambiar_sintetizador(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.chk1.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.checar(event, 'reader', self, self.config, self.global_refs, self.player, self.prueba)))
		self.choice_2.Bind(wx.EVT_CHOICE, lambda event: self._update_config_globals_reader(self.events.cambiarVoz(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.instala_voces.Bind(wx.EVT_BUTTON, lambda event: self._update_config_globals_reader(self.events.instalar_voz_piper(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.slider_1.Bind(wx.EVT_SLIDER, lambda event: self._update_config(self.events.cambiarTono(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.slider_2.Bind(wx.EVT_SLIDER, lambda event: self._update_config(self.events.cambiarVolumen(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.slider_3.Bind(wx.EVT_SLIDER, lambda event: self._update_config(self.events.cambiarVelocidad(event, self, self.config, self.prueba, self.global_refs, self.player)))
		self.boton_prueva.Bind(wx.EVT_BUTTON, lambda event: self.events.reproducirPrueva(event, self, self.config, self.prueba, self.global_refs)) # No state update from this

		# Categorias Page (specific_args: list_ctrl_name, config_key)
		self.categoriza.Bind(wx.EVT_LIST_ITEM_CHECKED, lambda event: self._update_config(self.events.on_list_item_checked(event, 'categoriza', 'categorias', self, self.config, self.global_refs, self.player, self.prueba)))

		# Sonidos Page
		self.check_2.Bind(wx.EVT_CHECKBOX, lambda event: self._update_config(self.events.mostrarSonidos(event, self, self.config, self.global_refs, self.player, self.prueba)))
		self.soniditos.Bind(wx.EVT_LIST_ITEM_CHECKED, lambda event: self._update_config(self.events.on_list_item_checked(event, 'soniditos', 'listasonidos', self, self.config, self.global_refs, self.player, self.prueba)))
		self.reproducir.Bind(wx.EVT_BUTTON, lambda event: self.events.on_play_sound_button(event, self, self.player, self.global_refs)) # Passes player directly
		self.establecer_dispositivo.Bind(wx.EVT_BUTTON, lambda event: self._update_config(self.events.alternar_dispositivo(event, self, self.config, self.player, self.prueba, self.global_refs)))

		# Eventos Page
		self.eventos.Bind(wx.EVT_LIST_ITEM_CHECKED, lambda event: self._update_config(self.events.on_list_item_checked(event, 'eventos', 'eventos', self, self.config, self.global_refs, self.player, self.prueba)))
		self.unread.Bind(wx.EVT_LIST_ITEM_CHECKED, lambda event: self._update_config(self.events.on_list_item_checked(event, 'unread', 'unread', self, self.config, self.global_refs, self.player, self.prueba)))

		# OK and Cancel buttons
		# The event handlers on_ok/on_cancel in ajustes_events.py expect (self_events, dialog, config)
		self.button_ok.Bind(wx.EVT_BUTTON, lambda event: self.events.on_ok(self, self.config))
		self.button_cancel.Bind(wx.EVT_BUTTON, lambda event: self.events.on_cancel(self))


	# --- Helper methods for updating state from event handlers ---
	def _update_config(self, result_config):
		if result_config is not None:
			self.config = result_config
			# Potentially refresh parts of UI if config change affects it directly
			# For example, if a checkbox state depends on another config value

	def _update_config_and_globals(self, result_tuple):
		if result_tuple:
			new_config, new_global_refs = result_tuple
			if new_config is not None: self.config = new_config
			if new_global_refs is not None:
				self.global_refs = new_global_refs
				# Update instance attributes that are part of global_refs and might have changed identity (e.g. new list)
				self.lista_voces = self.global_refs.get('lista_voces', self.lista_voces)
				self.lista_voces_piper = self.global_refs.get('lista_voces_piper', self.lista_voces_piper)
				self.dispositivos_piper = self.global_refs.get('dispositivos_piper', self.dispositivos_piper)
				# Potentially refresh UI elements that depend on these lists (e.g., self.choice_2)

	def _update_config_globals_reader(self, result_tuple):
		if result_tuple:
			new_config, new_reader_handler, new_global_refs = result_tuple
			if new_config is not None: self.config = new_config
			if new_reader_handler is not None: self.prueba = new_reader_handler # Update reader instance
			if new_global_refs is not None:
				self.global_refs = new_global_refs
				self.lista_voces = self.global_refs.get('lista_voces', self.lista_voces)
				self.lista_voces_piper = self.global_refs.get('lista_voces_piper', self.lista_voces_piper)
				self.dispositivos_piper = self.global_refs.get('dispositivos_piper', self.dispositivos_piper)
				# Potentially refresh UI elements (e.g., self.choice_2)

```
