import wx
from utils.menu_accesible import Accesible

class ChatFilterMenu:
    def __init__(self, parent):
        self.parent = parent
        self.menu = wx.Menu()
        
        self.todos = self.menu.Append(wx.ID_ANY, _("Todos"))
        self.unidos = self.menu.Append(wx.ID_ANY, _("Unidos"))
        self.gustados = self.menu.Append(wx.ID_ANY, _("Gustados"))
        self.compartidas = self.menu.Append(wx.ID_ANY, _("Compartidas"))
        self.seguidores = self.menu.Append(wx.ID_ANY, _("Seguidores"))
        
        self.parent.Bind(wx.EVT_MENU, self.on_todos, self.todos)
        self.parent.Bind(wx.EVT_MENU, self.on_unidos, self.unidos)
        self.parent.Bind(wx.EVT_MENU, self.on_gustados, self.gustados)
        self.parent.Bind(wx.EVT_MENU, self.on_compartidas, self.compartidas)
        self.parent.Bind(wx.EVT_MENU, self.on_seguidores, self.seguidores)

    def on_todos(self, event):
        self.parent.actualizar_filtro_eventos("todos")

    def on_unidos(self, event):
        self.parent.actualizar_filtro_eventos("join")

    def on_gustados(self, event):
        self.parent.actualizar_filtro_eventos("like")

    def on_compartidas(self, event):
        self.parent.actualizar_filtro_eventos("share")

    def on_seguidores(self, event):
        self.parent.actualizar_filtro_eventos("follow")

    def popup(self, control):
        self.parent.PopupMenu(self.menu, control.GetPosition())
