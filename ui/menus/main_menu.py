import wx

class MainMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu1 = wx.Menu()
        self.opciones = wx.Menu()
        self.ayuda = wx.Menu()
        self.menu1.AppendSubMenu(self.opciones, _("&Opciones"))
        self.opcion_0 = self.opciones.Append(wx.ID_ANY, _("&Editor de combinaciones de teclado para VeTube"))
        self.opcion_1 = self.opciones.Append(wx.ID_ANY, _("&Configuración"))
        self.opcion_3 = self.opciones.Append(wx.ID_ANY, _("&Restablecer los ajustes"))
        self.menu1.AppendSubMenu(self.ayuda, _("&Ayuda"))
        self.manual = self.ayuda.Append(wx.ID_ANY, _("¿Cómo usar &vetube? (documentación en línea)"))
        self.apoyo = self.ayuda.Append(wx.ID_ANY, _("Únete a nuestra &causa"))
        self.itemPageMain = self.ayuda.Append(wx.ID_ANY, _("&Visita nuestra página de github"))
        self.actualizador = self.ayuda.Append(wx.ID_ANY, _("&buscar actualizaciones"))
        self.update_langs = self.ayuda.Append(wx.ID_ANY, _("Actualizar &idiomas"))
        self.acercade = self.menu1.Append(wx.ID_ANY, _("&Acerca de"))
        self.salir = self.menu1.Append(wx.ID_EXIT, _("&Salir...\tAlt+F4"))

    def mostrar(self, boton): self.parent.PopupMenu(self.menu1, boton.GetPosition())
