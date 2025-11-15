import wx, wx.adv
from pyperclip import copy
from ui.menus.chat_opciones_menu import ChatOpcionesMenu
from controller.editor_controller import EditorController
from utils import funciones
from controller.estadisticas_controller import EstadisticasController
from servicios.estadisticas_manager import EstadisticasManager

class ChatMenuController:
    def __init__(self, parent, plataforma, chat_controller, estadisticas_manager):
        self.parent = parent
        self.plataforma = plataforma
        self.chat_controller = chat_controller
        self.estadisticas_manager = estadisticas_manager
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
        self.parent.Bind(wx.EVT_MENU, lambda evt: self.chat_controller.main_controller.mostrar_editor_combinaciones(), self.menu.editor_combinaciones)
        self.parent.Bind(wx.EVT_MENU, self.addFavoritos, self.menu.favoritos)
        self.parent.Bind(wx.EVT_MENU, self.mostrar_estadisticas, self.menu.ver_estadisticas)
        self.parent.Bind(wx.EVT_MENU, self.copiarEnlace, self.menu.copiar_enlace)
        self.parent.Bind(wx.EVT_MENU, self.reproducirVideo, self.menu.reproducir_navegador)
        self.parent.Bind(wx.EVT_MENU, lambda evt: self.chat_controller.buscar_mensajes(), self.menu.buscar)

    def addFavoritos(self, event):
        from globals.data_store import favorite
        main_frame = self.parent.GetParent()
        list_favorite = main_frame.list_favorite
        url = self.chat_controller.servicio.url

        if not url:
            wx.MessageBox(_("No hay una URL para agregar a favoritos."), _("Aviso"), wx.OK | wx.ICON_INFORMATION)
            return

        if self.plataforma == 'TikTok': titulo = funciones.extractUser(url)
        elif self.plataforma == 'Twich' and self.chat_controller.servicio.chat.status != 'past': titulo = funciones.extractUser(url)
        elif self.plataforma == 'Kick':
            titulo = url
            url = "https://www.kick.com/" + titulo
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
        url = self.chat_controller.servicio.url
        if url:
            if self.plataforma == 'Kick':
                url = "https://www.kick.com/" + url
            copy(url)
            noti = wx.adv.NotificationMessage(_("Enlace copiado al portapapeles"), _("El enlace del chat ha sido copiado al portapapeles."))
            noti.Show(timeout=5)
        else: wx.adv.NotificationMessage(_("No se pudo copiar el enlace"), _("No se encontró un enlace válido para copiar.")).Show(timeout=5)

    def reproducirVideo(self, event):
        url = self.chat_controller.servicio.url
        if url:
            if self.plataforma == 'Kick':
                url = "https://www.kick.com/" + url
            wx.LaunchDefaultBrowser(url)
        else: wx.adv.NotificationMessage(_("No se pudo abrir el enlace"), _("No se encontró un enlace válido para abrir.")).Show(timeout=5)



    def mostrar_estadisticas(self, event):
        controller = EstadisticasController(self.parent, self.estadisticas_manager, self.plataforma)
        controller.show()