import wx
from ui.editor.editor import EditorCombinaciones
from utils.key_utilitys import editor
from os import remove
from ui.dialog_response import response
from ui.editor.nueva_combinacion import NuevaCombinacionDialog
from helpers.keyboard_handler.wx_handler import WXKeyboardHandler
from globals.mensajes import mensaje_teclas

class EditorController:
    def __init__(self, frame):
        self.frame = frame  # Guarda el frame principal como atributo
        self.ui = EditorCombinaciones(frame)  # frame como parent visual
        self.handler_keyboard = WXKeyboardHandler(self.frame)  # Usa el frame para hotkeys
        self._bind_events()

    def _bind_events(self):
        self.ui.restaurar.Bind(wx.EVT_BUTTON, self.on_restore_defaults)
        self.ui.editar.Bind(wx.EVT_BUTTON, self.on_editar)
        self.ui.combinaciones.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_editar)

    def on_restore_defaults(self, event):
        if response(_("Está apunto de restaurar las combinaciones a sus valores por defecto, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"))==wx.ID_YES:
            remove("keys.txt")
            editor.leerTeclas()
            c=0
            for valor in editor.teclas:
                self.ui.combinaciones.SetItem(c, 1, valor)
                c+=1
            self.ui.combinaciones.Focus(0)
            self.ui.combinaciones.SetFocus()
            
    def on_editar(self, event):
        dlg = NuevaCombinacionDialog(self.ui.dlg_teclado, self.ui.combinaciones)
        if dlg.ShowModal() == wx.ID_OK:
            indice = self.ui.combinaciones.GetFocusedItem()
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
            if not ctrl and not alt and not win and not shift:
                wx.MessageBox(_("Debe escoger al menos una tecla de las casillas de verificación"), "error.", wx.ICON_ERROR)
                return
            for busc in range(self.ui.combinaciones.GetItemCount()):
                if busc == indice:
                    continue
                if self.nueva_combinacion == self.ui.combinaciones.GetItem(busc, 1).GetText():
                    wx.MessageBox(_("Esta combinación ya está siendo usada en la función %s") % mensaje_teclas[busc], "error.", wx.ICON_ERROR)
                    return
            self.handler_keyboard.register_key(self.nueva_combinacion,print)
        wx.CallAfter(self.correccion)
        dlg.dlg_editar_combinacion.Destroy()

    def correccion(self):
        indice = self.ui.combinaciones.GetFocusedItem()
        combinacion_actual = self.ui.combinaciones.GetItem(indice, 1).GetText()
        if self.nueva_combinacion not in self.handler_keyboard.active_keys:
            wx.MessageBox(_("Esa combinación está siendo usada por el sistema"), "error.", wx.ICON_ERROR)
            return
        else:
            self.handler_keyboard.unregister_key(self.nueva_combinacion,print)
            self.texto = self.nueva_combinacion
            self.nueva_combinacion = ""
            editor.reemplazar(combinacion_actual, self.texto)
            self.ui.combinaciones.SetItem(indice, 1, self.texto)
            self.ui.combinaciones.SetFocus()

    def ShowModal(self):
        return self.ui.ShowModal()
