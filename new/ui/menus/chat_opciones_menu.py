import wx

class ChatOpcionesMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu = wx.Menu()
        self.editor_combinaciones = self.menu.Append(10, _(u"&Editor de combinaciones de teclado para VeTube"))
        self.exportar_mensajes = self.menu.Append(2, _(u"E&xportar los mensajes en un archivo de texto"))
        self.favoritos = self.menu.Append(3, _(u"&Añadir este canal a favoritos"))
        self.ver_estadisticas = self.menu.Append(4, _(u"&Ver estadísticas del chat"))
        self.copiar_enlace = self.menu.Append(8, _(u"&Copiar enlace del chat al portapapeles"))
        self.reproducir_navegador = self.menu.Append(9, _(u"&Reproducir video en el navegador"))

    def popup(self, btn):
        btn.PopupMenu(self.menu)
