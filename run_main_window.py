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
from utils.app_utilitys import configurar_piper, limpiar_motor_antiguo, fijar_dispositivo_lector
if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def run_app():
    # Restos del motor de voz anterior (actualizaciones copian por encima)
    limpiar_motor_antiguo()
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
            fijar_dispositivo_lector()
        elif config['sistemaTTS'] == "kokoro":
            # Modelo Kokoro no disponible: avisar con la voz secundaria en lugar
            # de arrancar con la voz principal muda (revisión de accesibilidad).
            setup.reader._leer.speak(_("No hay voces instaladas"))
    elif config['sistemaTTS'] == "edge":
        # Edge no tiene modelo local: basta con apuntar el lector al nombre
        # corto de la voz elegida y fijar el dispositivo de salida.
        from TTS.edge_handler import edge_voz_shortname, edge_iniciar_carga, edge_list_voices
        if not (0 <= config['voz'] < len(edge_list_voices())):
            config['voz'] = 0
        setup.reader._lector.load_model(edge_voz_shortname(config['voz']))
        fijar_dispositivo_lector()
        # La lista de voces se descarga en segundo plano (para los Ajustes).
        edge_iniciar_carga()
    
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
