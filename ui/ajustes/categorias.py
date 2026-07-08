import wx
from globals.data_store import config
from globals.mensajes import mensajes_categorias

class PanelCategorias(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		sizer_categoriza = wx.BoxSizer(wx.VERTICAL)
		self.categoriza = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
		self.categoriza.InsertColumn(0, _("Categoría"))
		self.categoriza.EnableCheckBoxes()
		sizer_categoriza.Add(self.categoriza, 1, wx.EXPAND | wx.ALL, 5)
		self.SetSizer(sizer_categoriza)
		for contador in range(len(mensajes_categorias)):
			self.categoriza.InsertItem(contador, mensajes_categorias[contador])
			self.categoriza.CheckItem(contador, check=config['categorias'][contador])
		self.categoriza.Focus(0)
