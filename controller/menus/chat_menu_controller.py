import wx, wx.adv
from pyperclip import copy
from ui.menus.chat_opciones_menu import ChatOpcionesMenu
from controller.editor_controller import EditorController
from utils import funciones
from controller.estadisticas_controller import EstadisticasController
from servicios.estadisticas_manager import EstadisticasManager

class ChatMenuController:
    def __init__(self, parent, plataforma, chat_controller):
        self.parent = parent
        self.plataforma = plataforma
        self.chat_controller = chat_controller
        self.menu = ChatOpcionesMenu(parent)
        self._bind_menu_events()
        self._customize_menu()

    def _customize_menu(self):
        # Ocultar opciones si la plataforma es 'La sala de juegos'
        if self.plataforma and self.plataforma.lower() == 'la sala de juegos':
            self.menu.menu.Remove(self.menu.copiar_enlace.GetId())
            self.menu.menu.Remove(self.menu.reproducir_navegador.GetId())
            self.menu.menu.Remove(self.menu.favoritos.GetId())

    def _bind_menu_events(self):
        # Bind all menu items here
        self.parent.Bind(wx.EVT_MENU, self.mostrar_editor_combinaciones, self.menu.editor_combinaciones)
        self.parent.Bind(wx.EVT_MENU, self.addFavoritos, self.menu.favoritos)
        self.parent.Bind(wx.EVT_MENU, self.mostrar_estadisticas, self.menu.ver_estadisticas)
        self.parent.Bind(wx.EVT_MENU, self.copiarEnlace, self.menu.copiar_enlace)
        self.parent.Bind(wx.EVT_MENU, self.reproducirVideo, self.menu.reproducir_navegador)
        self.parent.Bind(wx.EVT_MENU, lambda evt: self.chat_controller.buscar_mensajes(), self.menu.buscar)

    def addFavoritos(self, event):
        from globals.data_store import favorite
        main_frame = self.parent.GetParent()
        list_favorite = main_frame.list_favorite
        text_ctrl_1 = main_frame.text_ctrl_1
        url = text_ctrl_1.GetValue()

        if not url:
            wx.MessageBox(_("No hay una URL para agregar a favoritos."), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
            return

        if self.plataforma == 'TikTok': titulo = funciones.extractUser(url)
        elif self.plataforma == 'Twich' and self.chat_controller.servicio.chat.status != 'past': titulo = funciones.extractUser(url)
        else: titulo = self.parent.label_dialog.GetLabel()

        if any(fav.get('url') == url for fav in favorite):
            wx.MessageBox(_("Ya se encuentra en favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
            return

        if list_favorite.GetCount() > 0 and list_favorite.GetStrings()[0] == _("Tus favoritos aparecerán aquí"): list_favorite.Delete(0)

        list_favorite.Append(f"{titulo}: {url}")
        favorite.append({'titulo': titulo, 'url': url})
        funciones.escribirJsonLista('favoritos.json', favorite)
        wx.MessageBox(_("Se ha agregado a favoritos"), _("Aviso"), wx.OK | wx.ICON_INFORMATION)

    def copiarEnlace(self, event):
        main_frame = self.parent.GetParent()
        url = main_frame.text_ctrl_1.GetValue()
        if url:
            copy(url)
            noti = wx.adv.NotificationMessage(_("Enlace copiado al portapapeles"), _("El enlace del chat ha sido copiado al portapapeles."))
            noti.Show(timeout=5)
        else: wx.adv.NotificationMessage(_("No se pudo copiar el enlace"), _("No se encontró un enlace válido para copiar.")).Show(timeout=5)

    def reproducirVideo(self, event):
        main_frame = self.parent.GetParent()
        url = main_frame.text_ctrl_1.GetValue()
        if url: wx.LaunchDefaultBrowser(url)
        else: wx.adv.NotificationMessage(_("No se pudo abrir el enlace"), _("No se encontró un enlace válido para abrir.")).Show(timeout=5)

    def mostrar_editor_combinaciones(self, event):
        editor_ctrl = EditorController(self.parent, self.chat_controller)
        editor_ctrl.ShowModal()

    def mostrar_estadisticas(self, event):
        estadisticas_manager = EstadisticasManager()
        controller = EstadisticasController(self.parent, estadisticas_manager, self.plataforma)
        controller.show()