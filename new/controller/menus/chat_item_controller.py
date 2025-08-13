import wx
import wx.adv
from pyperclip import copy
from setup import reader
from utils.translator import TranslatorWrapper
from ui.show_comment import ShowCommentDialog
from ui.list_urls import ListUrlsDialog
from globals.data_store import mensajes_destacados
from utils.funciones import escribirJsonLista

class ChatItemController:
    def __init__(self, menu, list_box):
        self.menu = menu
        self.list_box = list_box
        self.selected_index = self.list_box.GetSelection()
        self.selected_text = self.list_box.GetString(self.selected_index)
        
        # Bind events
        self.menu.menu.Bind(wx.EVT_MENU, self.on_copy, id=self.menu.copiar.GetId())
        self.menu.menu.Bind(wx.EVT_MENU, self.on_show, id=self.menu.mostrar.GetId())
        self.menu.menu.Bind(wx.EVT_MENU, self.on_translate, id=self.menu.traducir.GetId())
        self.menu.menu.Bind(wx.EVT_MENU, self.on_list_urls, id=self.menu.listado_urls.GetId())
        self.menu.menu.Bind(wx.EVT_MENU, self.on_archive, id=self.menu.archivar.GetId())

    def on_copy(self, event):
        copy(self.selected_text)
        noti = wx.adv.NotificationMessage(_("Mensaje copiado al portapapeles"), _("El mensaje seleccionado ha sido copiado al portapapeles."))
        noti.Show(timeout=10)

    def on_show(self, event):
        dlg = ShowCommentDialog(self.menu.parent, self.selected_text)
        dlg.ShowModal()
        dlg.Destroy()

    def on_translate(self, event):
        translator = TranslatorWrapper()
        from utils.languageHandler import curLang
        copy(translator.translate(self.selected_text, target=curLang[:2]))
        noti = wx.adv.NotificationMessage(_("Mensaje traducido"), _("el mensaje se ha traducido al idioma del programa y se  a  copiado en el portapapeles."), parent=self.menu.parent)
        noti.Show(timeout=10)

    def on_list_urls(self, event):
        ListUrlsDialog(self.list_box, self.menu.parent)

    def on_archive(self, event):
        main_frame = self.menu.parent.GetParent()
        list_mensajes = main_frame.list_mensajes
        
        if list_mensajes.GetCount() > 0 and list_mensajes.GetStrings()[0] == _( "Tus mensajes archivados aparecerán aquí"):
            list_mensajes.Delete(0)
        
        mensaje = self.selected_text
        ya_archivado = any(mensaje == d.get('mensaje', '') for d in mensajes_destacados)
        if not ya_archivado:
            list_mensajes.Append(mensaje + ': . ')
            mensajes_destacados.append({'mensaje': mensaje, 'titulo': '. '})
            escribirJsonLista('mensajes_destacados.json', mensajes_destacados)
            reader.leer_sapi(_("El mensaje ha sido archivado correctamente."))
        else:
            reader.leer_sapi(_("Este mensaje ya está en la lista de archivados."))
