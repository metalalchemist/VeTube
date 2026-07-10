import wx
from setup import player
from globals.data_store import config
from globals.mensajes import mensajes_sonidos
from globals.resources import listar_temas_sonidos, recargar_rutasonidos

class PanelSonidos(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent, wx.ID_ANY)
		sizer_soniditos = wx.BoxSizer(wx.VERTICAL)
		self.check_2 = wx.CheckBox(self, wx.ID_ANY, _("Activar sonidos"))
		self.check_2.SetValue(config['sonidos'])
		sizer_soniditos.Add(self.check_2, 0, wx.ALL, 5)
		label_tema = wx.StaticText(self, wx.ID_ANY, _("Tema de sonidos"))
		sizer_soniditos.Add(label_tema, 0, wx.ALL, 5)
		self.lista_temas = wx.Choice(self, wx.ID_ANY, choices=listar_temas_sonidos())
		if not self.lista_temas.SetStringSelection(config['directorio']) and self.lista_temas.GetCount() > 0:
			self.lista_temas.SetSelection(0)
			config['directorio'] = self.lista_temas.GetStringSelection()
			recargar_rutasonidos()
		sizer_soniditos.Add(self.lista_temas, 0, wx.EXPAND | wx.ALL, 5)
		self.soniditos = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
		self.soniditos.InsertColumn(0, _("Sonido"))
		self.soniditos.EnableCheckBoxes()
		sizer_soniditos.Add(self.soniditos, 1, wx.EXPAND | wx.ALL, 5)
		sound_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.reproducir = wx.Button(self, wx.ID_ANY, _("&Reproducir"))
		sound_buttons_sizer.Add(self.reproducir, 0, wx.ALL, 5)
		sizer_soniditos.Add(sound_buttons_sizer, 0, wx.ALL, 5)
		label_dispositivo = wx.StaticText(self, wx.ID_ANY, _("Seleccionar dispositivo de audio"))
		sizer_soniditos.Add(label_dispositivo, 0, wx.ALL, 5)
		self.lista_dispositivos = wx.Choice(self, wx.ID_ANY, choices=player.devicenames)
		self.lista_dispositivos.SetSelection(config['dispositivo'] - 1)
		sizer_soniditos.Add(self.lista_dispositivos, 0, wx.EXPAND | wx.ALL, 5)
		self.establecer_dispositivo = wx.Button(self, wx.ID_ANY, label=_("&Establecer"))
		sizer_soniditos.Add(self.establecer_dispositivo, 0, wx.ALL, 5)
		self.SetSizer(sizer_soniditos)
		for contador in range(len(mensajes_sonidos)):
			self.soniditos.InsertItem(contador, mensajes_sonidos[contador])
			self.soniditos.CheckItem(contador, check=config['listasonidos'][contador])
		self.soniditos.Focus(0)
