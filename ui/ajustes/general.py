import wx
from globals.data_store import config
from globals.resources import langs, codes

class PanelGeneral(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		panel_sizer_1 = wx.BoxSizer(wx.VERTICAL)
		box_1 = wx.StaticBox(self, -1, _("Opciones de la app"))
		boxSizer_1 = wx.StaticBoxSizer(box_1, wx.VERTICAL)
		label_language = wx.StaticText(self, wx.ID_ANY, _("Idioma de VeTube (Requiere reiniciar)"))
		boxSizer_1.Add(label_language, 0, wx.ALL, 5)
		self.choice_language = wx.Choice(self, wx.ID_ANY, choices=langs)
		self.choice_language.SetSelection(codes.index(config['idioma']))
		boxSizer_1.Add(self.choice_language, 0, wx.EXPAND | wx.ALL, 5)
		self.check_donaciones = wx.CheckBox(self, wx.ID_ANY, _("Activar diálogo de donaciones al inicio de la app."))
		self.check_donaciones.SetValue(config['donations'])
		boxSizer_1.Add(self.check_donaciones, 0, wx.ALL, 5)
		self.check_salir = wx.CheckBox(self, wx.ID_ANY, _("preguntar si desea salir de la app al cerrar."))
		self.check_salir.SetValue(config['salir'])
		boxSizer_1.Add(self.check_salir, 0, wx.ALL, 5)
		self.check_actualizaciones = wx.CheckBox(self, wx.ID_ANY, _("Comprobar si hay actualizaciones al iniciar la app"))
		self.check_actualizaciones.SetValue(config['updates'])
		boxSizer_1.Add(self.check_actualizaciones, 0, wx.ALL, 5)
		self.check_traduccion = wx.CheckBox(self, wx.ID_ANY, _("intentar traducir las novedades cuando salga una actualización."))
		self.check_traduccion.SetValue(config['traducir'])
		boxSizer_1.Add(self.check_traduccion, 0, wx.ALL, 5)
		self.check_interface = wx.CheckBox(self, wx.ID_ANY, _("Desactivar la interfaz invisible"))
		self.check_interface.SetValue(config.get('interface', False))
		boxSizer_1.Add(self.check_interface, 0, wx.ALL, 5)
		panel_sizer_1.Add(boxSizer_1, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(panel_sizer_1)
