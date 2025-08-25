import wx

class MainMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu1 = wx.Menu()
        self.opciones = wx.Menu()
        self.ayuda = wx.Menu()
        self.menu1.AppendSubMenu(self.opciones, "&Opciones")
        self.opcion_0 = self.opciones.Append(wx.ID_ANY, "&Editor de combinaciones de teclado para VeTube")
        self.opcion_1 = self.opciones.Append(wx.ID_ANY, "&Configuración")
        self.opcion_3 = self.opciones.Append(wx.ID_ANY, "&Restablecer los ajustes")
        self.menu1.AppendSubMenu(self.ayuda, "&Ayuda")
        self.manual = self.ayuda.Append(wx.ID_ANY, "¿Cómo usar &vetube? (documentación en línea)")
        self.apoyo = self.ayuda.Append(wx.ID_ANY, "Únete a nuestra &causa")
        self.itemPageMain = self.ayuda.Append(wx.ID_ANY, "&Visita nuestra página de github")
        self.actualizador = self.ayuda.Append(wx.ID_ANY, "&buscar actualizaciones")
        self.acercade = self.menu1.Append(wx.ID_ANY, "&Acerca de")
        self.salir = self.menu1.Append(wx.ID_EXIT, "&Salir...\tAlt+F4")

    def mostrar(self, boton):
        self.parent.PopupMenu(self.menu1, boton.GetPosition())
        # No destruir el menú aquí, para permitir múltiples usos
        # self.menu1.Destroy()
