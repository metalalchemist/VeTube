import wx
from setup import reader
from ui.chat_ui import ChatDialog
from ui.menus.chat_item_menu import ChatItemMenu
from ui.menus.chat_opciones_menu import ChatOpcionesMenu
from controller.menus.chat_item_controller import ChatItemController
from controller.menus.chat_menu_controller import ChatMenuController

class ChatController:
    def __init__(self, frame, plataforma):
        self.frame = frame
        self.plataforma = plataforma
        self.ui = ChatDialog(frame)
        self.menu_controller = ChatItemController(self.ui)  # Solo pasa el dialog como parent
        self.menu_opciones_controller = ChatMenuController(self.ui, self.plataforma)
        self._bind_events()

    def _bind_events(self):
        self.ui.list_box_1.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.ui.list_box_1.Bind(wx.EVT_KEY_UP, self.on_listbox_keyup)
        self.ui.boton_opciones.Bind(wx.EVT_BUTTON, self.on_opciones_btn)

    def on_context_menu(self, event):
        self.menu_controller.menu.mostrar_menu(self.ui.list_box_1)

    def on_opciones_btn(self, event):
        self.menu_opciones_controller.menu.popup(self.ui.boton_opciones)

    def on_listbox_keyup(self, event):
        event.Skip()
        if event.GetKeyCode() == 32:
            reader._leer.silence()
            reader.leer_sapi(self.ui.list_box_1.GetString(self.ui.list_box_1.GetSelection()))

    def mostrar_dialogo(self):
        self.ui.ShowModal()
