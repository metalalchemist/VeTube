# -*- coding: utf-8 -*-
from . import update
from builtins import str
import logging
from .wxUpdater import *
from setup import network
logger = logging.getLogger("updater")

# Versión global del programa
VERSION = "3.8"

# Cerrojo global para evitar múltiples búsquedas simultáneas
buscando = False

def do_update(endpoint='https://raw.githubusercontent.com/metalalchemist/VeTube/master/updater.json', is_manual=False):
    global buscando
    if buscando:
        return
    buscando = True
    
    def handle_check_result(update_data):
        global buscando
        try:
            if isinstance(update_data, Exception):
                if is_manual:
                    wx.CallAfter(wx.MessageBox, _("Error al comprobar actualizaciones: ") + str(update_data), _("Error"), wx.ICON_ERROR)
                return

            if not update_data:
                if is_manual:
                    wx.CallAfter(wx.MessageBox, _("Al parecer tienes la última versión del programa"), _("Información"), wx.ICON_INFORMATION)
                return
            
            # Si hay actualización, mostrar diálogo
            if available_update_dialog(update_data['available_version'], update_data['available_description']):
                import threading
                # La descarga e instalación sigue siendo síncrona en un hilo aparte
                threading.Thread(
                    target=update.perform_update,
                    kwargs={
                        'update_url': update_data['update_url'],
                        'donations': update_data['donations'],
                        'progress_callback': progress_callback,
                        'update_complete_callback': update_finished
                    },
                    daemon=True
                ).start()
        finally:
            buscando = False

    # Lanzamos la comprobación asíncrona usando el motor global
    network.execute(update.async_check_update(endpoint, VERSION), callback=handle_check_result)
