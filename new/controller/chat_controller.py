import wx
from setup import reader
from ui.chat_ui import ChatDialog
from ui.menus.chat_item_menu import ChatItemMenu
from ui.menus.chat_opciones_menu import ChatOpcionesMenu
from controller.menus.chat_item_controller import ChatItemController
from controller.menus.chat_menu_controller import ChatMenuController
from ui.dialog_response import response

class ChatController:
    def __init__(self, frame, servicio=None):
        self.frame = frame
        self.servicio = servicio
        self.ui = ChatDialog(frame)
        self.menu_controller = ChatItemController(self.ui)  # Solo pasa el dialog como parent
        self.opciones_menu = ChatOpcionesMenu(self.ui)
        self._bind_events()

    def _bind_events(self):
        self.ui.button_mensaje_detener.Bind(wx.EVT_BUTTON, self.on_close_dialog)
        self.ui.list_box_1.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.ui.list_box_1.Bind(wx.EVT_KEY_UP, self.on_listbox_keyup)
        self.ui.boton_opciones.Bind(wx.EVT_BUTTON, self.on_opciones_btn)

    def on_context_menu(self, event):
        self.menu_controller.menu.mostrar_menu(self.ui.list_box_1)

    def on_opciones_btn(self, event):
        self.opciones_menu.popup(self.ui.boton_opciones)

    def on_listbox_keyup(self, event):
        event.Skip()
        if event.GetKeyCode() == 32:
            reader._leer.silence()
            reader.leer_sapi(self.ui.list_box_1.GetString(self.ui.list_box_1.GetSelection()))
    def on_close_dialog(self, event):
        if response(_("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:")) == wx.ID_YES:
            self.servicio.detener()
            main_frame = self.ui.GetParent()
            self.ui.Destroy()
            reader._leer.silence()
            reader.leer_sapi(_("ha finalizado la lectura del chat."))
            main_frame.text_ctrl_1.SetValue("")
            main_frame.text_ctrl_1.SetFocus()
            main_frame.plataforma.SetSelection(0)
    def agregar_mensaje(self, mensaje):
        self.ui.list_box_1.Append(mensaje)

    def mostrar_dialogo(self):
        self.ui.ShowModal()
