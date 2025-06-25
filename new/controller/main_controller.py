from globals.data_store import favorite, mensajes_destacados, favs, msjs
from ui.main_window import MyFrame
from utils import funciones
from os import remove
from utils import languageHandler
import wx
from controller.main_menu_controller import MainMenuController

class MainController:
    def __init__(self):
        self.frame = MyFrame(None)
        self.menu_controller = MainMenuController(self.frame)
        self.inicializar_datos()
        self.establecer_eventos()
        # Aquí puedes enlazar eventos futuros

    def inicializar_datos(self):
        # Favoritos
        self.frame.list_favorite.Set(favs)
        self.frame.favoritos_num = self.frame.list_favorite.GetCount()
        self.frame.notebook_1.SetPageText(1, _( "Favoritos(%s)") % self.frame.favoritos_num)
        if not favs or self.frame.list_favorite.GetCount() == 0:
            self.frame.list_favorite.Append(_( "Tus favoritos aparecerán aquí"), 0)
        # Mensajes destacados
        self.frame.list_mensajes.Set(msjs)
        if not self.frame.list_mensajes.GetCount():
            self.frame.list_mensajes.Append(_("Tus mensajes archivados aparecerán aquí"), 0)

    def establecer_eventos(self):
        # Menú y botones principales
        self.frame.menu_1.Bind(wx.EVT_BUTTON, lambda evt: self.menu_controller.menu.mostrar(self.frame.menu_1))
        self.frame.text_ctrl_1.Bind(wx.EVT_TEXT, self.mostrarBoton)
        self.frame.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
        self.frame.button_borrar_favoritos.Bind(wx.EVT_BUTTON, self.borrarFavorito)
        self.frame.borrar_todos_favs.Bind(wx.EVT_CHECKBOX, self.borrarTodosFavoritos)
        self.frame.check_borrar_todos.Bind(wx.EVT_CHECKBOX, self.seleccionarTodos)
        self.frame.button_borrar_mensajes.Bind(wx.EVT_BUTTON, self.borraRecuerdo)
        self.frame.button_1.Bind(wx.EVT_BUTTON, self.abrir_chat_dialog)
        # Bind global key events (CharHook) to the frame
        self.frame.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)

    def mostrarBoton(self, event):
        if self.frame.text_ctrl_1.GetValue() != "":
            self.frame.button_1.Enable()
            self.frame.button_2.Enable()
        else:
            self.frame.button_1.Disable()
            self.frame.button_2.Disable()

    def borrarContenido(self, event):
        self.frame.text_ctrl_1.SetValue("")
        self.frame.text_ctrl_1.SetFocus()

    def borrarFavorito(self, event=None):
        lf = self.frame.list_favorite
        if lf.GetCount() <= 0 or lf.GetStrings()[0] == _( "Tus favoritos aparecerán aquí"):
            wx.MessageBox(_( "No hay favoritos que borrar"), _( "Error"), wx.ICON_ERROR)
            lf.SetFocus()
        else:
            if self.frame.borrar_todos_favs.GetValue():
                if wx.MessageBox(_( "¿Estás seguro de borrar todos los favoritos de la lista?"), _( "¡Atención!"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    lf.Clear()
                    favorite.clear()
                    remove('favoritos.json')
                    lf.SetFocus()
            else:
                sel = lf.GetSelection()
                lf.Delete(sel)
                favorite.pop(sel)
                funciones.escribirJsonLista('favoritos.json', favorite)
                lf.SetFocus()
        if lf.GetCount() <= 0:
            lf.Append(_( "Tus favoritos aparecerán aquí"))

    def seleccionarTodos(self, event):
        if self.frame.check_borrar_todos.GetValue():
            self.frame.button_borrar_mensajes.SetLabel(_("&Borrar mensajes"))
            self.frame.button_borrar_mensajes.SetToolTip(_("Borrar todos los mensajes destacados"))
            self.frame.button_borrar_mensajes.SetFocus()
        else:
            self.frame.button_borrar_mensajes.SetLabel(_("&Borrar mensaje"))
            self.frame.button_borrar_mensajes.SetToolTip(_("Borrar el mensaje destacado seleccionado"))
            self.frame.button_borrar_mensajes.SetFocus()

    def borrarTodosFavoritos(self, event):
        if self.frame.borrar_todos_favs.GetValue():
            self.frame.button_borrar_favoritos.SetLabel(_("&Borrar favoritos"))
            self.frame.button_borrar_favoritos.SetToolTip(_("Borrar todos los favoritos"))
            self.frame.button_borrar_favoritos.SetFocus()
        else:
            self.frame.button_borrar_favoritos.SetLabel(_("&Borrar favorito"))
            self.frame.button_borrar_favoritos.SetToolTip(_("Borrar el favorito seleccionado"))
            self.frame.button_borrar_favoritos.SetFocus()

    def borraRecuerdo(self, event):
        lf = self.frame.list_mensajes
        if not self.frame.check_borrar_todos.GetValue():
            if not lf.GetStrings()[0] == _( "Tus mensajes archivados aparecerán aquí"):
                if len(mensajes_destacados) > 0:
                    sel = lf.GetSelection()
                    lf.Delete(sel)
                    mensajes_destacados.pop(sel)
                    funciones.escribirJsonLista('mensajes_destacados.json', mensajes_destacados)
                    lf.SetFocus()
                else:
                    wx.MessageBox(_( "No hay más elementos que borrar"), "Error.", wx.ICON_ERROR)
            else:
                wx.MessageBox(_( "No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
                lf.SetFocus()
            if lf.GetCount() <= 0:
                lf.Append(_( "Tus mensajes archivados aparecerán aquí"))
        else:
            if len(mensajes_destacados) > 0:
                if wx.MessageBox(_( "¿Estás seguro de que quieres borrar todos los mensajes?"), "Confirmación", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    mensajes_destacados.clear()
                    remove('mensajes_destacados.json')
                    lf.Clear()
                    lf.Append(_( "Tus mensajes archivados aparecerán aquí"))
                    lf.SetFocus()
            elif len(mensajes_destacados) <= 0:
                wx.MessageBox(_( "No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
                lf.SetFocus()

    def abrir_chat_dialog(self, event):
        from ui.chat_ui import ChatDialog
        dlg = ChatDialog(self.frame)
        dlg.ShowModal()

    def OnCharHook(self, event):
        code = event.GetKeyCode()
        # alt + m
        if code == 77 and event.AltDown():
            self.menu_controller.menu.mostrar(self.frame.menu_1)
        elif wx.GetKeyState(wx.WXK_F1):
            wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md')
        else:
            event.Skip()