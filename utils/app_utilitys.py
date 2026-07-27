# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from TTS.lector import detect_onnx_models
from TTS.list_voices import install_piper_voice, piper_list_voices, obtener_ruta_voz
from setup import reader, player
from ui.dialog_response import response
from globals.data_store import config
from globals.resources import lista_voces_piper
from controller.piper_downloader_controller import PiperDownloaderController
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
def porcentaje_a_escala(porcentaje): return 1.25 + porcentaje * 0.125
def configurar_piper(parent, carpeta_voces):
    onnx_models = detect_onnx_models(carpeta_voces)
    if onnx_models is None:
        if response(_('Necesitas al menos una voz para poder usar el sintetizador Piper. ¿Deseas abrir el descargador de voces ahora para buscar e instalar una?'), _("No hay voces instaladas"), wx.YES_NO | wx.ICON_ASTERISK) == wx.ID_YES:
            downloader = PiperDownloaderController(parent)
            downloader.show()
            nuevas_voces = detect_onnx_models(carpeta_voces)
            if nuevas_voces is not None:
                lista_voces_piper.clear()
                lista_voces_piper.extend(piper_list_voices())
                config['voz'] = 0
                model_path = obtener_ruta_voz(lista_voces_piper[0])
                reader._lector = reader._lector.piperSpeak(model_path)
                nombres_dispositivos = player.devicenames
                dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres_dispositivos)]
                nombre_actual = nombres_dispositivos[config["dispositivo"]-1]
                salida_actual = reader._lector.find_device_id(nombre_actual, known_devices=dispositivos_formateados)
                reader._lector.set_device(salida_actual)
                reader.leer_auto(_("Lector Piper inicializado correctamente."))
    elif isinstance(onnx_models, str) or isinstance(onnx_models, list):
        config['voz'] = 0