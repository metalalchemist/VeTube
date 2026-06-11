# -*- coding: utf-8 -*-
import wx
from . import utils

progress_dialog = None

def available_update_dialog(version, description):
    dialog = wx.MessageDialog(None, _(u"Hay una nueva versión de VeTube. Te gustaría descargarla ahora?\n\n VeTube versión: %s\n\nCambios:\n%s") % (version, description), _(u"Nueva versión de VeTube"), style=wx.YES|wx.NO|wx.ICON_WARNING)
    if dialog.ShowModal() == wx.ID_YES:
        return True
    else:
        return False


def create_progress_dialog():
    return wx.ProgressDialog(_(u"Descarga en progreso"), _(u"Descargando la actualización"),  parent=None, maximum=100)

def progress_callback(total_downloaded, total_size):
    global progress_dialog
    
    def update_ui():
        global progress_dialog
        if progress_dialog == None:
            progress_dialog = create_progress_dialog()
            progress_dialog.Show()
        if total_downloaded == total_size:
            progress_dialog.Destroy()
            progress_dialog = None
        else:
            progress_dialog.Update(int((total_downloaded*100)/total_size), _(u"Actualizando... %s de %s") % (str(utils.convert_bytes(total_downloaded)), str(utils.convert_bytes(total_size))))
    
    wx.CallAfter(update_ui)

def update_finished():
    def show_msg():
        wx.MessageDialog(None, _(u"La actualización se ha descargado e instalado exitosamente. Pulse en aceptar para continuar."), _(u"¡Hecho!")).ShowModal()
    wx.CallAfter(show_msg)
