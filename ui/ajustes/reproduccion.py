import wx
from globals.data_store import config

class PanelReproduccion(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		panel_sizer_reproduccion = wx.BoxSizer(wx.VERTICAL)
		box_reproduccion = wx.StaticBox(self, -1, _("ajustes de reproducción"))
		boxSizer_reproduccion = wx.StaticBoxSizer(box_reproduccion, wx.VERTICAL)
		self.check_reproducir = wx.CheckBox(self, wx.ID_ANY, _("activar reproducción automática al iniciar un en vivo."))
		self.check_reproducir.SetValue(config.get('reproducir', True))
		boxSizer_reproduccion.Add(self.check_reproducir, 0, wx.ALL, 5)
		label_tiempo = wx.StaticText(self, wx.ID_ANY, _("tiempo para adelantar y atrazar el en vivo en segundos"))
		boxSizer_reproduccion.Add(label_tiempo, 0, wx.ALL, 5)
		self.spin_tiempo = wx.SpinCtrl(self, wx.ID_ANY, value=str(config.get('tiempo', 10)), min=1, max=60)
		boxSizer_reproduccion.Add(self.spin_tiempo, 0, wx.EXPAND | wx.ALL, 5)
		label_volumen_reproductor = wx.StaticText(self, wx.ID_ANY, _("volumen del reproductor"))
		boxSizer_reproduccion.Add(label_volumen_reproductor, 0, wx.ALL, 5)
		self.slider_volumen_reproductor = wx.Slider(self, wx.ID_ANY, config.get('volumen', 100), 0, 100)
		boxSizer_reproduccion.Add(self.slider_volumen_reproductor, 0, wx.EXPAND | wx.ALL, 5)
		label_cambiovolumen = wx.StaticText(self, wx.ID_ANY, _("cambio de volumen con las teclas de volumen (1-25)"))
		boxSizer_reproduccion.Add(label_cambiovolumen, 0, wx.ALL, 5)
		self.slider_cambiovolumen = wx.Slider(self, wx.ID_ANY, config.get('cambiovolumen', 10), 1, 25)
		boxSizer_reproduccion.Add(self.slider_cambiovolumen, 0, wx.EXPAND | wx.ALL, 5)
		panel_sizer_reproduccion.Add(boxSizer_reproduccion, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(panel_sizer_reproduccion)
