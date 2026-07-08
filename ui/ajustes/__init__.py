import wx
from globals import data_store
from globals.data_store import config
from controller.ajustes_controller import AjustesController

from .general import PanelGeneral
from .chat import PanelChat
from .voz import PanelVoz
from .reproduccion import PanelReproduccion
from .categorias import PanelCategorias
from .sonidos import PanelSonidos
from .eventos import PanelEventos

class configuracionDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title=_("Configuración"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		self.tree_1 = wx.Treebook(self, wx.ID_ANY)

		# Instanciar paneles
		self.panel_general = PanelGeneral(self.tree_1)
		self.treeItem_1 = self.panel_general
		self.tree_1.AddPage(self.panel_general, _("General"))

		self.panel_chat = PanelChat(self.tree_1)
		self.treeItem_chat = self.panel_chat
		self.tree_1.AddPage(self.panel_chat, _("Chat"))

		self.panel_voz = PanelVoz(self.tree_1)
		self.treeItem_2 = self.panel_voz
		self.tree_1.AddPage(self.panel_voz, _("Voz"))

		self.panel_reproduccion = PanelReproduccion(self.tree_1)
		self.treeItem_reproduccion = self.panel_reproduccion
		self.tree_1.AddPage(self.panel_reproduccion, _("reproducción"))

		self.panel_categorias = PanelCategorias(self.tree_1)
		self.treeItem_3 = self.panel_categorias
		self.tree_1.AddPage(self.panel_categorias, _("Categorías"))

		self.panel_sonidos = PanelSonidos(self.tree_1)
		self.treeItem_4 = self.panel_sonidos
		self.tree_1.AddPage(self.panel_sonidos, _("Sonidos"))

		self.panel_eventos = PanelEventos(self.tree_1)
		self.treeItem_5 = self.panel_eventos
		self.tree_1.AddPage(self.panel_eventos, _("Eventos"))

		main_sizer.Add(self.tree_1, 1, wx.EXPAND | wx.ALL, 5)

		# Botones de diálogo
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		button_sizer.AddStretchSpacer()
		button_ok = wx.Button(self, wx.ID_OK, _("&Aceptar"))
		button_ok.SetDefault()
		button_cancel = wx.Button(self, wx.ID_CANCEL, _("&Cancelar"))
		button_sizer.Add(button_ok, 0, wx.ALL, 5)
		button_sizer.Add(button_cancel, 0, wx.ALL, 5)
		main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 0)
		self.SetSizer(main_sizer)
		self.SetSize((550, 600))
		self.Center()

		# Atajos/Propiedades fachada para controladores (ajustes_controller y main_menu_controller)
		# Panel General
		self.choice_language = self.panel_general.choice_language
		self.check_donaciones = self.panel_general.check_donaciones
		self.check_salir = self.panel_general.check_salir
		self.check_actualizaciones = self.panel_general.check_actualizaciones
		self.check_traduccion = self.panel_general.check_traduccion
		self.check_interface = self.panel_general.check_interface

		# Panel Chat
		self.check_historial = self.panel_chat.check_historial
		self.choice_traducir = self.panel_chat.choice_traducir
		self.chk1 = self.panel_chat.chk1
		self.choice_moneditas = self.panel_chat.choice_moneditas

		# Panel Voz
		self.check_1 = self.panel_voz.check_1
		self.seleccionar_TTS = self.panel_voz.seleccionar_TTS
		self.choice_2 = self.panel_voz.choice_2
		self.instala_voces = self.panel_voz.instala_voces
		self.slider_1 = self.panel_voz.slider_1
		self.slider_2 = self.panel_voz.slider_2
		self.slider_3 = self.panel_voz.slider_3
		self.boton_prueva = self.panel_voz.boton_prueva

		# Panel Reproducción
		self.check_reproducir = self.panel_reproduccion.check_reproducir
		self.spin_tiempo = self.panel_reproduccion.spin_tiempo
		self.slider_volumen_reproductor = self.panel_reproduccion.slider_volumen_reproductor
		self.slider_cambiovolumen = self.panel_reproduccion.slider_cambiovolumen

		# Panel Categorías
		self.categoriza = self.panel_categorias.categoriza

		# Panel Sonidos
		self.check_2 = self.panel_sonidos.check_2
		self.soniditos = self.panel_sonidos.soniditos
		self.reproducir = self.panel_sonidos.reproducir
		self.lista_dispositivos = self.panel_sonidos.lista_dispositivos
		self.establecer_dispositivo = self.panel_sonidos.establecer_dispositivo

		# Panel Eventos
		self.eventos = self.panel_eventos.eventos
		self.unread = self.panel_eventos.unread

		# Lógica inicial
		if config['sapi']:
			self.seleccionar_TTS.Disable()
		else:
			self.seleccionar_TTS.Enable()
		if config['sonidos']:
			self.soniditos.Enable()
			self.reproducir.Enable()
		else:
			self.soniditos.Disable()
			self.reproducir.Disable()

		self.ajustes_controller = AjustesController(self)
