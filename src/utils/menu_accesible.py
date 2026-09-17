import wx


# crear una clase de accesibilidad
class Accesible(wx.Accessible):
    def __init__(self, window):
        wx.Accessible.__init__(self)
        self.window = window
        self.tooltip = wx.ToolTip("Menú de opciones")
        self.tooltip.SetDelay(0)
        self.window.SetToolTip(self.tooltip)

    def GetRole(self, childId):
        return (wx.ACC_OK, wx.ROLE_SYSTEM_BUTTONMENU)

    def GetState(self, childId):
        return (wx.ACC_OK, wx.ACC_STATE_SYSTEM_FOCUSABLE | wx.ACC_STATE_SYSTEM_FOCUSED)

    def GetDefaultAction(self, childId):
        return (wx.ACC_OK, "Abrir menú")


class AccesibleConNombre(wx.Accessible):
    """Da un nombre accesible a un control que no puede tomarlo de un
    wx.StaticText anterior. wx.Window.SetName() no sirve para esto: solo
    alimenta FindWindowByName(), los lectores de pantalla lo ignoran."""

    def __init__(self, nombre):
        wx.Accessible.__init__(self)
        self.nombre = nombre

    def GetName(self, childId):
        if childId == 0:
            return (wx.ACC_OK, self.nombre)
        return (wx.ACC_NOT_IMPLEMENTED, "")
