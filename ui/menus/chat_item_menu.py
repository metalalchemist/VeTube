import wx

class ChatItemMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu = wx.Menu()
        self.traducir = self.menu.Append(wx.ID_ANY, _(u"&Traducir"))
        self.mostrar = self.menu.Append(wx.ID_ANY, _(u"&Mostrar el mensaje en un cuadro de texto."))
        self.copiar = self.menu.Append(wx.ID_ANY, _(u"&Copiar mensaje al portapapeles"))
        self.listado_urls = self.menu.Append(wx.ID_ANY, _(u"&Listado de Urls."))
        self.archivar = self.menu.Append(wx.ID_ANY, _(u"&Archivar mensaje"))

    def mostrar_menu(self, list_box):
        # Solo muestra el menú si hay selección, si no selecciona el primero
        if list_box.GetSelection() == -1 and list_box.GetCount() > 0:
            list_box.SetSelection(0)
        if list_box.GetCount() > 0:
            list_box.PopupMenu(self.menu)
