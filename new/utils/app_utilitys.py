# -*- coding: cp1252
from __future__ import unicode_literals
from TTS.lector import detect_onnx_models
from TTS.list_voices import install_piper_voice
from setup import reader
from ui.dialog_response import response
from globals.data_store import config
import sys, os,wx

def restart_program():
    """ Function that restarts the application if is executed."""
    args = sys.argv[:]
    if not hasattr(sys, "frozen"):
        args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]
    pidpath = os.path.join(os.getenv("temp"), "{}.pid".format('VeTube'))
    if os.path.exists(pidpath):
        os.remove(pidpath)
    os.execv(sys.executable, args)
def porcentaje_a_escala(porcentaje): return 2.00 + (1 - ((porcentaje - -10) / (10 - -10))) * (0.50 - 2.00)
def configurar_piper(carpeta_voces):
    global config
    onnx_models = detect_onnx_models(carpeta_voces)
    if onnx_models is None:
        if response(_('Necesitas al menos una voz para poder usar el sintetizador Piper. ¿Quieres abrir nuestra carpeta de Drive para descargar algunos modelos? Si pulsas sí, se abrirá nuestra carpeta seguido de una ventana para instalar una una vez la descargues.'), _("No hay voces instaladas"),wx.YES_NO | wx.ICON_ASTERISK) == wx.ID_YES:
            wx.LaunchDefaultBrowser("https://drive.google.com/drive/folders/1zFJRTI6CpVw9NkrTiNYOKGga0yn4JXzv?usp=drive_link")
            config, reader._lector = install_piper_voice(config, reader._lector)
    elif isinstance(onnx_models, str) or isinstance(onnx_models, list):
        config['voz'] = 0