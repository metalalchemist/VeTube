import wx
from ui.menus.chat_filter_menu import ChatFilterMenu

class ChatFilterController:
    def __init__(self, parent_controller):
        self.parent_controller = parent_controller
        self.menu = ChatFilterMenu(parent_controller.ui)

    def show_menu(self, control):
        self.menu.popup(control)
