import wx
from globals import data_store
from globals.data_store import config
from globals.resources import idiomas_disponibles, codigos_traduccion, monedas

class PanelChat(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		panel_sizer_chat = wx.BoxSizer(wx.VERTICAL)
		box_chat = wx.StaticBox(self, -1, _("Opciones del chat"))
		boxSizer_chat = wx.StaticBoxSizer(box_chat, wx.VERTICAL)
		self.check_historial = wx.CheckBox(self, wx.ID_ANY, _("Leer los mensajes anteriores al chat"))
		self.check_historial.SetValue(config.get('leer_historial', True))
		boxSizer_chat.Add(self.check_historial, 0, wx.ALL, 5)
		label_trans = wx.StaticText(self, wx.ID_ANY, _("traducción de mensajes: "))
		boxSizer_chat.Add(label_trans, 0, wx.ALL, 5)
		self.choice_traducir = wx.Choice(self, wx.ID_ANY, choices=idiomas_disponibles)
		try:
			self.choice_traducir.SetSelection(codigos_traduccion.index(data_store.dst))
		except ValueError:
			self.choice_traducir.SetSelection(0)
		boxSizer_chat.Add(self.choice_traducir, 0, wx.EXPAND | wx.ALL, 5)
		self.chk1 = wx.CheckBox(self, wx.ID_ANY, _("Activar lectura de mensajes automática"))
		self.chk1.SetValue(config['reader'])
		boxSizer_chat.Add(self.chk1, 0, wx.ALL, 5)
		label_monedas = wx.StaticText(self, wx.ID_ANY, _("convertir las donaciones a la divisa: "))
		boxSizer_chat.Add(label_monedas, 0, wx.ALL, 5)
		self.choice_moneditas = wx.Choice(self, wx.ID_ANY, choices=monedas)
		self.choice_moneditas.SetSelection(0)
		boxSizer_chat.Add(self.choice_moneditas, 0, wx.EXPAND | wx.ALL, 5)
		panel_sizer_chat.Add(boxSizer_chat, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(panel_sizer_chat)
