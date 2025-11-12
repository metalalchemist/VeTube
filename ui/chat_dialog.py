import wx
import configparser
from globals import data_store
from helpers.keyboard_handler.wx_handler import WXKeyboardHandler
from setup import reader

class ChatDialog(wx.Dialog):
    def __init__(self, parent, main_controller, id=wx.ID_ANY, title="Chat Sessions", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):
        super().__init__(parent, id=id, title=title, pos=pos, size=size, style=style)

        self.main_controller = main_controller
        self.notebook = wx.Treebook(self, wx.ID_ANY, style=wx.NB_LEFT)
        self.globally_controlled_media_player = None
        self.chat_sessions = {}
        self.active_chat_session = None
        self.keyboard_handler = WXKeyboardHandler(self)
        self.is_programmatic_close = False
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.notebook.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.on_page_changed)
        
        self._initialize_shortcuts()

    def _initialize_shortcuts(self):
        """
        Lee los atajos del archivo de configuración y los registra una sola vez.
        Usa lambdas para que los métodos se llamen en el contexto del chat activo dinámicamente.
        """
        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt")

        command_objects = {
            'main': self.main_controller,
            'reader': reader,
            'chat_dialog': self
        }

        for section in ['atajos_chat', 'atajos_player']:
            if section not in config:
                continue
            for key, command_str in config[section].items():
                try:
                    obj_name, method_name = command_str.split('.', 1)

                    if obj_name == 'chat':
                        # Llama al método en la sesión de chat activa en el momento de la pulsación
                        handler = lambda m=method_name: getattr(self.active_chat_session, m)() if self.active_chat_session else None
                        self.keyboard_handler.register_key(key, handler)
                    elif obj_name == 'media_player':
                        # Llama al método en el reproductor de medios globalmente activo
                        handler = lambda m=method_name: getattr(self.globally_controlled_media_player, m)() if self.globally_controlled_media_player else None
                        self.keyboard_handler.register_key(key, handler)
                    elif obj_name in command_objects:
                        target_obj = command_objects[obj_name]
                        method = getattr(target_obj, method_name, None)
                        if method and callable(method):
                            self.keyboard_handler.register_key(key, method)
                except Exception as e:
                    logging.error(f"Error parsing shortcut {key}={command_str}: {e}")

    def add_chat_page(self, chat_panel, title, chat_controller):
        self.notebook.AddPage(chat_panel, title)
        page_index = self.notebook.GetPageCount() - 1
        self.notebook.SetSelection(page_index)
        self.chat_sessions[chat_controller.servicio.url] = (chat_controller, page_index)
        self.active_chat_session = chat_controller
        return page_index

    def remove_chat_page(self, chat_controller):
        url_to_remove = None
        page_index_to_remove = -1
        for url, (controller, page_index) in self.chat_sessions.items():
            if controller == chat_controller:
                url_to_remove = url
                page_index_to_remove = page_index
                break
        
        if url_to_remove and page_index_to_remove != -1:
            self.notebook.DeletePage(page_index_to_remove)
            del self.chat_sessions[url_to_remove]
            if self.notebook.GetPageCount() == 0:
                self.is_programmatic_close = True
                self.Close() # Llamar a Close() para asegurar que on_close se ejecute
    def update_chat_page_title(self, chat_controller, new_title):
        for url, (controller, page_index) in self.chat_sessions.items():
            if controller == chat_controller:
                self.notebook.SetPageText(page_index, new_title)
                break

    def on_close(self, event):
        # Si el cierre no es programático (es decir, por Alt+F4 o el botón 'X'), pedir confirmación.
        if not self.is_programmatic_close:
            if wx.MessageBox(_("¿Desea cerrar la ventana de lectura de los chats en vivo?"), _("¡Atención!"), wx.YES_NO | wx.ICON_QUESTION) == wx.NO:
                event.Veto() # Cancelar el evento de cierre
                return

        # Si el usuario confirma o el cierre es programático, proceder con la limpieza.
        self.main_controller.frame.menu_1.Enable()
        self.keyboard_handler.unregister_all_keys()
        for url, (controller, page_index) in list(self.chat_sessions.items()):
            if controller.servicio:
                controller.servicio.detener()
        self.Destroy()

    def close_chat_session(self, chat_controller):
        if chat_controller.servicio:
            chat_controller.servicio.detener()
        self.remove_chat_page(chat_controller)
        self.main_controller.frame.plataforma.SetSelection(0)

    def on_page_changed(self, event):
        # Guarda para asegurar que solo procesamos eventos de nuestro propio Treebook (el de sesiones)
        if event.GetEventObject() != self.notebook:
            return

        event.Skip()

        new_page_index = event.GetSelection()
        self.active_chat_session = None
        for url, (controller, page_index) in self.chat_sessions.items():
            if page_index == new_page_index:
                self.active_chat_session = controller
                break

    def next_session(self):
        page_count = self.notebook.GetPageCount()
        if page_count <= 1:
            return
        current_selection = self.notebook.GetSelection()
        next_selection = current_selection + 1
        if next_selection >= page_count:
            next_selection = 0
        self.notebook.SetSelection(next_selection)
        
        if self.active_chat_session and self.active_chat_session.ui:
            self.active_chat_session.ui.treebook.SetFocus()
        
        reader.leer_auto(self.notebook.GetPageText(next_selection))

    def previous_session(self):
        page_count = self.notebook.GetPageCount()
        if page_count <= 1:
            return
        current_selection = self.notebook.GetSelection()
        next_selection = current_selection - 1
        if next_selection < 0:
            next_selection = page_count - 1
        self.notebook.SetSelection(next_selection)

        if self.active_chat_session and self.active_chat_session.ui:
            self.active_chat_session.ui.treebook.SetFocus()

        reader.leer_auto(self.notebook.GetPageText(next_selection))

    def on_media_player_state_change(self, media_controller, state):
        if state == 'playing':
            if self.globally_controlled_media_player and self.globally_controlled_media_player != media_controller:
                if self.globally_controlled_media_player.is_playing():
                    self.globally_controlled_media_player.pause()
            self.globally_controlled_media_player = media_controller
        elif state == 'stopped' or state == 'paused':
            if self.globally_controlled_media_player == media_controller:
                self.globally_controlled_media_player = None

    def toggle_global_media_pause(self):
        if self.globally_controlled_media_player:
            self.globally_controlled_media_player.toggle_pause()
        elif self.active_chat_session and self.active_chat_session.media_controller:
            self.active_chat_session.media_controller.play()

    def toggle_chat_window_visibility(self):
        if self.IsShown():
            self.Hide()
            # Mostrar y configurar la ventana principal
            self.main_controller.frame.Show()
            self.main_controller.frame.Raise()
            self.main_controller.frame.text_ctrl_1.SetFocus()
            self.main_controller.frame.plataforma.SetSelection(0)
        else:
            # Mostrar este diálogo (la ventana principal permanece visible)
            self.Show()
            self.Raise()
