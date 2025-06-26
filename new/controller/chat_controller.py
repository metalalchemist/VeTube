import wx
from ui.chat_ui import ChatDialog
from ui.menus.chat_item_menu import ChatItemMenu
from controller.menus.chat_item_controller import ChatItemController

class ChatController:
    def __init__(self, frame):
        self.frame = frame
        self.ui = ChatDialog(frame)
        self.menu_controller = ChatItemController(self.ui)  # Solo pasa el dialog como parent
        self._bind_events()

    def _bind_events(self):
        self.ui.list_box_1.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

    def on_context_menu(self, event):
        self.menu_controller.menu.mostrar_menu(self.ui.list_box_1)

    def mostrar_dialogo(self):
        self.ui.ShowModal()
