import wx
from globals.data_store import config
from globals.mensajes import eventos_lista

class PanelEventos(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		sizer_eventos = wx.BoxSizer(wx.VERTICAL)
		lbl = wx.StaticText(self, wx.ID_ANY, _("procesados: "))
		sizer_eventos.Add(lbl, 0, wx.ALL, 5)
		self.eventos = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
		self.eventos.InsertColumn(0, _("Evento"))
		self.eventos.EnableCheckBoxes()
		sizer_eventos.Add(self.eventos, 1, wx.EXPAND | wx.ALL, 5)
		lbl_1 = wx.StaticText(self, wx.ID_ANY, _("leídos"))
		sizer_eventos.Add(lbl_1, 0, wx.ALL, 5)
		self.unread = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
		self.unread.InsertColumn(0, _("Evento"))
		self.unread.EnableCheckBoxes()
		sizer_eventos.Add(self.unread, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(sizer_eventos)
		for contador in range(len(config['eventos'])):
			self.eventos.InsertItem(contador, eventos_lista[contador])
			self.eventos.CheckItem(contador, check=config['eventos'][contador])
		self.eventos.Focus(0)
		for contador in range(len(config['unread'])):
			self.unread.InsertItem(contador, eventos_lista[contador])
			self.unread.CheckItem(contador, check=config['unread'][contador])
		self.unread.Focus(0)
