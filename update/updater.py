# -*- coding: utf-8 -*-
from . import update
from builtins import str
import logging
from requests.exceptions import ConnectionError
from .wxUpdater import *
from accessible_output2.outputs import auto
logger = logging.getLogger("updater")
Lector=auto.Auto()
def do_update(endpoint='https://raw.githubusercontent.com/metalalchemist/VeTube/master/updater.json'):
    try: result = update.perform_update(endpoint=endpoint, current_version="2.71", app_name="VeTube", update_available_callback=available_update_dialog, progress_callback=progress_callback, update_complete_callback=update_finished)
    except: Lector.speak(_("Hubo un error al actualizar VeTube."))
    return result
