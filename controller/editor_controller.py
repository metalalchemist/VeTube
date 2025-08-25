import wx
from ui.editor.editor import EditorCombinaciones
from utils.key_utilitys import editor
from os import remove
from ui.dialog_response import response
from ui.editor.nueva_combinacion import NuevaCombinacionDialog
from helpers.keyboard_handler.wx_handler import WXKeyboardHandler
from globals.mensajes import mensaje_teclas, comandos_a_descripcion
import configparser

class EditorController:
    def __init__(self, frame, chat_controller=None):
        self.frame = frame
        self.chat_controller = chat_controller
        self.ui = EditorCombinaciones(frame)
        self.handler_keyboard = WXKeyboardHandler(self.frame)
        self._bind_events()
        self._load_combinations()

    def _load_combinations(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt")
        
        if 'atajos_chat' in config:
            self.ui.combinaciones.DeleteAllItems()
            index = 0
            for key, command_str in config['atajos_chat'].items():
                description = comandos_a_descripcion.get(command_str, "")
                
                self.ui.combinaciones.InsertItem(index, description)
                self.ui.combinaciones.SetItem(index, 1, key)
                index += 1
        if self.ui.combinaciones.GetItemCount() > 0:
            self.ui.combinaciones.Focus(0)
            self.ui.combinaciones.SetFocus()

    def _bind_events(self):
        self.ui.restaurar.Bind(wx.EVT_BUTTON, self.on_restore_defaults)
        self.ui.editar.Bind(wx.EVT_BUTTON, self.on_editar)
        self.ui.combinaciones.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_editar)

    def on_restore_defaults(self, event):
        if response(_("Está apunto de restaurar las combinaciones a sus valores por defecto, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"))==wx.ID_YES:
            editor.escribirTeclas() # This writes the default keys.txt
            self._load_combinations() # This reloads the UI from the new keys.txt
            self.ui.combinaciones.Focus(0)
            self.ui.combinaciones.SetFocus()
            # Notify ChatController to reload shortcuts
            if self.chat_controller:
                self.chat_controller.reload_shortcuts()
            
    def on_editar(self, event):
        indice = self.ui.combinaciones.GetFocusedItem()
        selected_key = self.ui.combinaciones.GetItem(indice, 1).GetText()

        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt")
        command_str = config['atajos_chat'].get(selected_key, "")
        description = comandos_a_descripcion.get(command_str, _("Función desconocida"))

        dlg = NuevaCombinacionDialog(self.ui.dlg_teclado, self.ui.combinaciones, texto=selected_key, description=description)
        if dlg.ShowModal() == wx.ID_OK:
            combinacion_actual = self.ui.combinaciones.GetItem(indice, 1).GetText()

            tecla = dlg.combo_tecla.GetValue()
            ctrl = dlg.check_ctrl.GetValue()
            alt = dlg.check_alt.GetValue()
            shift = dlg.check_shift.GetValue()
            win = dlg.check_win.GetValue()
            self.nueva_combinacion = tecla
            if shift: self.nueva_combinacion = "shift+" + self.nueva_combinacion
            if alt: self.nueva_combinacion = "alt+" + self.nueva_combinacion
            if ctrl: self.nueva_combinacion = "control+" + self.nueva_combinacion
            if win: self.nueva_combinacion = "win+" + self.nueva_combinacion

            if self.nueva_combinacion == combinacion_actual:
                dlg.dlg_editar_combinacion.Destroy()
                return

            if not ctrl and not alt and not win and not shift:
                wx.MessageBox(_("Debe escoger al menos una tecla de las casillas de verificación"), "error.", wx.ICON_ERROR)
                return

            for busc in range(self.ui.combinaciones.GetItemCount()):
                if busc == indice:
                    continue
                if self.nueva_combinacion == self.ui.combinaciones.GetItem(busc, 1).GetText():
                    wx.MessageBox(_("Esta combinación ya está siendo usada en la función %s") % comandos_a_descripcion.get(config['atajos_chat'].get(self.ui.combinaciones.GetItem(busc, 1).GetText(), ""), _("Función desconocida")), "error.", wx.ICON_ERROR)
                    return

            self.handler_keyboard.register_key(self.nueva_combinacion, print)
            wx.CallAfter(self.correccion_de_prueba)
        dlg.dlg_editar_combinacion.Destroy()

    def correccion_de_prueba(self):
        # Check if the key was successfully added to the handler's active list
        if self.nueva_combinacion in self.handler_keyboard.active_keys:
            # Success! Immediately unregister the test key.
            self.handler_keyboard.unregister_key(self.nueva_combinacion, print)
            
            # And now save the change permanently
            indice = self.ui.combinaciones.GetFocusedItem()
            combinacion_actual = self.ui.combinaciones.GetItem(indice, 1).GetText()
            editor.reemplazar(combinacion_actual, self.nueva_combinacion)
            self.ui.combinaciones.SetItem(indice, 1, self.nueva_combinacion)
            self.ui.combinaciones.SetFocus()
            # Notify ChatController to reload shortcuts
            if self.chat_controller:
                self.chat_controller.reload_shortcuts()
        else:
            # Failure. The key was not registered, likely because the OS blocked it.
            wx.MessageBox(_("Esa combinación está siendo usada por el sistema operativo"), "error.", wx.ICON_ERROR)

    def ShowModal(self):
        return self.ui.ShowModal()