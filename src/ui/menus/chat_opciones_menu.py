import wx


class ChatOpcionesMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu = wx.Menu()
        self.editor_combinaciones = self.menu.Append(
            10, _("&Editor de combinaciones de teclado para VeTube")
        )
        self.favoritos = self.menu.Append(3, _("&Añadir este canal a favoritos"))
        self.ver_estadisticas = self.menu.Append(4, _("&Ver estadísticas del chat"))
        self.copiar_enlace = self.menu.Append(
            8, _("&Copiar enlace del chat al portapapeles")
        )
        self.reproducir_navegador = self.menu.Append(
            9, _("&Reproducir video en el navegador")
        )
        self.buscar = self.menu.Append(wx.ID_ANY, _("Buscar mensajes..."))

    def popup(self, btn):
        btn.PopupMenu(self.menu)
