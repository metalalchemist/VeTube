import wx, wx.adv
from pyperclip import copy
from ui.menus.chat_opciones_menu import ChatOpcionesMenu
from controller.editor_controller import EditorController
from utils import funciones
class ChatMenuController:
    def __init__(self, parent, plataforma=None):
        self.parent = parent
        self.plataforma = plataforma
        self.menu = ChatOpcionesMenu(parent)
        self._customize_menu()
        self._bind_menu_events()

    def _customize_menu(self):
        # Ocultar opciones si la plataforma es 'La sala de juegos'
        if self.plataforma and self.plataforma.lower() == 'la sala de juegos':
            self.menu.menu.Remove(self.menu.copiar_enlace.GetId())
            self.menu.menu.Remove(self.menu.reproducir_navegador.GetId())
            self.menu.menu.Remove(self.menu.favoritos.GetId())

    def _bind_menu_events(self):
        self.parent.Bind(wx.EVT_MENU, self.mostrar_editor_combinaciones, self.menu.editor_combinaciones)
        self.parent.Bind(wx.EVT_MENU, self.copiarEnlace, self.menu.copiar_enlace)
        self.parent.Bind(wx.EVT_MENU, self.reproducirVideo, self.menu.reproducir_navegador)
        self.parent.Bind(wx.EVT_MENU, self.addFavoritos, self.menu.favoritos)
    def addFavoritos(self, event):
        from globals.data_store import favorite
        main_frame = self.parent.GetParent()
        list_favorite = main_frame.list_favorite
        text_ctrl_1 = main_frame.text_ctrl_1
        if list_favorite.GetStrings() == [_("Tus favoritos aparecerán aquí")]:
            list_favorite.Delete(0)
        if len(favorite) <= 0:
            list_favorite.Append(funciones.extractUser(text_ctrl_1.GetValue())+': '+text_ctrl_1.GetValue())
            favorite.append({'titulo': funciones.extractUser(text_ctrl_1.GetValue()), 'url': text_ctrl_1.GetValue()})
        else:
            if any(funciones.extractUser(text_ctrl_1.GetValue())+': '+text_ctrl_1.GetValue() == item for item in list_favorite.GetStrings()):
                wx.MessageBox(_("Ya se encuentra en favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
                return
            else:
                list_favorite.Append(funciones.extractUser(text_ctrl_1.GetValue())+': '+text_ctrl_1.GetValue())
                favorite.append({'titulo': funciones.extractUser(text_ctrl_1.GetValue()), 'url': text_ctrl_1.GetValue()})
        funciones.escribirJsonLista('favoritos.json', favorite)
        wx.MessageBox(_("Se ha agregado a favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
    def copiarEnlace(self, event):
        main_frame = self.parent.GetParent()
        url = main_frame.text_ctrl_1.GetValue()
        if url:
            copy(url)
            noti = wx.adv.NotificationMessage(_("Enlace copiado al portapapeles"), _("El enlace del chat ha sido copiado al portapapeles."))
            noti.Show(timeout=5)
        else:
            wx.adv.NotificationMessage(_("No se pudo copiar el enlace"), _("No se encontró un enlace válido para copiar.")).Show(timeout=5)
    def reproducirVideo(self, event):
        main_frame = self.parent.GetParent()
        url = main_frame.text_ctrl_1.GetValue()
        if url:
            wx.LaunchDefaultBrowser(url)
        else:
            wx.adv.NotificationMessage(_("No se pudo abrir el enlace"), _("No se encontró un enlace válido para abrir.")).Show(timeout=5)
    def mostrar_editor_combinaciones(self, event):
        editor_ctrl = EditorController(self.parent)
        editor_ctrl.ShowModal()
