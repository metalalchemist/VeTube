import wx
from utils.menu_accesible import Accesible

class ChatDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, _(u"Chat en vivo"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_dialog = wx.StaticText(self, wx.ID_ANY, _(u"Lectura del chat en vivo..."))
        top_sizer.Add(self.label_dialog, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.button_mensaje_detener = wx.Button(self, wx.ID_ANY, _(u"&Detener chat"))
        top_sizer.Add(self.button_mensaje_detener, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        main_sizer.Add(top_sizer, 0, wx.EXPAND)
        self.label_mensaje = wx.StaticText(self, wx.ID_ANY, _(u"Historial de mensajes:"))
        main_sizer.Add(self.label_mensaje, 0, wx.ALL, 5)
        self.list_box_1 = wx.ListBox(self, wx.ID_ANY, choices=[])
        self.list_box_1.SetFocus()
        main_sizer.Add(self.list_box_1, 1, wx.EXPAND | wx.ALL, 5)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.AddStretchSpacer()
        self.boton_opciones = wx.Button(self, wx.ID_ANY, _(u"&Opciones"))
        self.boton_opciones.SetAccessible(Accesible(self.boton_opciones))
        bottom_sizer.Add(self.boton_opciones, 0, wx.ALL, 5)
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.SetSize((400, 500))
        self.Centre()
        self.SetEscapeId(self.button_mensaje_detener.GetId())

    def ShowModal(self):
        return super().ShowModal()
