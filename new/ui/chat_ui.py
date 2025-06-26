import wx
from utils.menu_accesible import Accesible

class ChatDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, _(u"Chat en vivo"))
        sizer_mensaje_1 = wx.BoxSizer(wx.VERTICAL)
        self.label_dialog = wx.StaticText(self, wx.ID_ANY, _(u"Lectura del chat en vivo..."))
        sizer_mensaje_1.Add(self.label_dialog, 0, 0, 0)
        sizer_mensaje_2 = wx.StdDialogButtonSizer()
        sizer_mensaje_1.Add(sizer_mensaje_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        self.label_mensaje = wx.StaticText(self, wx.ID_ANY, _(u"historial  de mensajes: "))
        sizer_mensaje_2.Add(self.label_mensaje, 20, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
        self.list_box_1 = wx.ListBox(self, wx.ID_ANY,choices=['hola'])
        self.list_box_1.SetFocus()
        sizer_mensaje_1.Add(self.list_box_1, 1, wx.EXPAND | wx.ALL, 4)
        self.boton_opciones = wx.Button(self, wx.ID_ANY, _(u"&Opciones"))
        self.boton_opciones.SetAccessible(Accesible(self.boton_opciones))
        sizer_mensaje_1.Add(self.boton_opciones, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        self.button_mensaje_detener = wx.Button(self, wx.ID_ANY, _(u"&Detener chat"))
        sizer_mensaje_2.Add(self.button_mensaje_detener, 10, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
        sizer_mensaje_2.Realize()
        self.SetSizerAndFit(sizer_mensaje_1)
        self.Centre()
        self.SetEscapeId(self.button_mensaje_detener.GetId())

    def ShowModal(self):
        return super().ShowModal()
