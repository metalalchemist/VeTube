import wx,wx.adv
from ui.menus.chat_item_menu import ChatItemMenu
from ui.show_comment import ShowCommentDialog
from pyperclip import copy
from utils.translator import TranslatorWrapper
from utils.languageHandler import curLang
from ui.list_urls import ListUrlsDialog
from globals.data_store import mensajes_destacados
from utils.funciones import escribirJsonLista
from setup import reader
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
        self.parent.list_box_1.Bind(wx.EVT_MENU, self.archivarMensaje, self.menu.archivar)
    def archivarMensaje(self, event):
        # Obtener el frame principal
        main_frame = self.parent.GetParent()
        list_mensajes = main_frame.list_mensajes
        list_box = self.parent.list_box_1
        if list_mensajes.GetCount() > 0 and list_mensajes.GetStrings()[0] == _( "Tus mensajes archivados aparecerán aquí"):
            list_mensajes.Delete(0)
        mensaje = list_box.GetString(list_box.GetSelection())
        # Evitar duplicados exactos
        ya_archivado = any(mensaje == d.get('mensaje', '') for d in mensajes_destacados)
        if not ya_archivado:
            list_mensajes.Append(mensaje + ': . ')
            mensajes_destacados.append({'mensaje': mensaje, 'titulo': '. '})
            escribirJsonLista('mensajes_destacados.json', mensajes_destacados)
            reader.leer_auto(_("El mensaje ha sido archivado correctamente."))
            # Leer el mensaje archivado usando reader
        else:
            reader.leer_auto(_("Este mensaje ya está en la lista de archivados."))

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
