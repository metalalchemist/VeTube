# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from builtins import str
from past.utils import old_div
import wx
from . import utils

progress_dialog = None

def available_update_dialog(version, description, date):
    dialog = wx.MessageDialog(None, _(u"Hay una nueva versión de VeTube. Te gustaría descargarla ahora?\n\n VeTube versión: %s\n\nCambios:\n%s") % (version, description), _(u"Nueva versión de VeTube"), style=wx.YES|wx.NO|wx.ICON_WARNING)
    if dialog.ShowModal() == wx.ID_YES:
        return True
    else:
        return False


def create_progress_dialog():
    return wx.ProgressDialog(_(u"Descarga en progreso"), _(u"Descargando la actualización"),  parent=None, maximum=100)

def progress_callback(total_downloaded, total_size):
    global progress_dialog
    if progress_dialog == None:
        progress_dialog = create_progress_dialog()
        progress_dialog.Show()
    if total_downloaded == total_size:
        progress_dialog.Destroy()
    else:
        progress_dialog.Update(old_div((total_downloaded*100),total_size), _(u"Actualizando... %s de %s") % (str(utils.convert_bytes(total_downloaded)), str(utils.convert_bytes(total_size))))

def update_finished():
    ms = wx.MessageDialog(None, _(u"La actualización se a descargado he instalado exitosamente. pulse en aceptar para continuar."), _(u"¡Hecho!")).ShowModal()
