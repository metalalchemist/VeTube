import wx,wx.adv
from ui.menus.chat_item_menu import ChatItemMenu
from ui.show_comment import ShowCommentDialog
from pyperclip import copy
from utils.translator import TranslatorWrapper
from utils.languageHandler import curLang
from ui.list_urls import ListUrlsDialog
from utils import funciones
class ChatItemController:
    def __init__(self, parent):
        self.parent = parent
        self.menu = ChatItemMenu(parent)
        self._bind_menu_events()

    def _bind_menu_events(self):
        self.parent.list_box_1.Bind(wx.EVT_MENU, self.mostrar_mensaje, self.menu.mostrar)
        self.parent.list_box_1.Bind(wx.EVT_MENU, self.traducirMenu, self.menu.traducir)
        self.parent.list_box_1.Bind(wx.EVT_MENU, self.copiarMensaje, self.menu.copiar)
        self.parent.list_box_1.Bind(wx.EVT_MENU, self.listaUrls, self.menu.listado_urls)

    def mostrar_mensaje(self, event):
        sel = self.parent.list_box_1.GetSelection()
        text = self.parent.list_box_1.GetString(sel)
        dlg = ShowCommentDialog(self.parent, text)
        dlg.ShowModal()

    def traducirMenu(self, event):
        translator = TranslatorWrapper()
        noti = wx.adv.NotificationMessage(_("Mensaje traducido"), _("el mensaje se ha traducido al idioma del programa y se  a  copiado en el portapapeles."))
        noti.Show(timeout=10)
        copy(translator.translate(self.parent.list_box_1.GetString(self.parent.list_box_1.GetSelection()), target=curLang[:2]))

    def copiarMensaje(self, event):
        noti = wx.adv.NotificationMessage(_("Mensaje copiado al portapapeles"), _("El mensaje seleccionado ha sido copiado al portapapeles."))
        noti.Show(timeout=10)
        copy(self.parent.list_box_1.GetString(self.parent.list_box_1.GetSelection()))

    def listaUrls(self, event):
        ListUrlsDialog(self.parent, self.parent.list_box_1, self.parent)
