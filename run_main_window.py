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
    if config['sistemaTTS'] in ("piper", "kokoro"):
        # Ambos motores viven en el mismo puente sherpa: localizar la voz
        # configurada y cargarla en el proceso residente.
        modelo = None
        if config['sistemaTTS'] == "piper":
            # Si solo quedan restos de las antiguas voces RT, aquí no habrá
            # voz que cargar: la migración se ofrece justo después, en
            # configurar_piper (secuencia de arranque del MainController).
            if detect_onnx_models(carpeta_voces) is not None:
                from TTS.list_voices import obtener_ruta_voz
                if not (0 <= config['voz'] < len(lista_voces_piper)):
                    config['voz'] = 0
                modelo = obtener_ruta_voz(lista_voces_piper[config['voz']])
        else:
            from TTS.sherpa_handler import kokoro_voice_config
            modelo = kokoro_voice_config(config['voz'])
        if modelo is not None:
            setup.reader._lector.load_model(modelo)
            nombres_dispositivos = setup.player.devicenames
            dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres_dispositivos)]
            nombre_actual = nombres_dispositivos[config["dispositivo"]-1]
            salida_actual = setup.reader._lector.find_device_id(nombre_actual, known_devices=dispositivos_formateados)
            setup.reader._lector.set_device(salida_actual)
        elif config['sistemaTTS'] == "kokoro":
            # Modelo Kokoro no disponible: avisar con la voz secundaria en lugar
            # de arrancar con la voz principal muda (revisión de accesibilidad).
            setup.reader._leer.speak(_("No hay voces instaladas"))
    
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
