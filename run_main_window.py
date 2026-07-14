#To resume this session: gemini --resume "44dd7d2c-5663-42a5-9e3b-ab471b033308"
# Configuramos los logs lo antes posible, antes de cualquier otro import del programa,
# para capturar también los errores que ocurran durante el arranque.
from utils.logging_setup import configurar_logs
configurar_logs()
import asyncio,sys,wx,setup
from globals.data_store import config
from globals.resources import carpeta_voces,lista_voces_piper
from controller.main_controller import MainController
from update import updater,update
from TTS.lector import detect_onnx_models
from utils.app_utilitys import configurar_piper
if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def run_app():
    app = wx.App(False)
    if config['sistemaTTS'] == "piper":
        if detect_onnx_models(carpeta_voces) is not None:
            from TTS.list_voices import obtener_ruta_voz
            setup.reader._lector=setup.reader._lector.piperSpeak(obtener_ruta_voz(lista_voces_piper[config['voz']]))
            nombres_dispositivos = setup.player.devicenames
            dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres_dispositivos)]
            nombre_actual = nombres_dispositivos[config["dispositivo"]-1]
            salida_actual = setup.reader._lector.find_device_id(nombre_actual, known_devices=dispositivos_formateados)
            setup.reader._lector.set_device(salida_actual)
    
    # Mostrar donación si es necesario (síncrono al inicio está bien por ser un diálogo de bienvenida)
    if config['donations']: update.donation()
    
    # Iniciar la interfaz principal
    controller = MainController()
    
    name = 'vetube-instance-checker'
    instance = wx.SingleInstanceChecker(name)
    if instance.IsAnotherRunning():
        wx.MessageBox(_('VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta.'), 'Error', wx.ICON_ERROR)
        return
    
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
run_app()
