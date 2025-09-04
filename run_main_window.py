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
            setup.reader._lector=setup.reader._lector.piperSpeak(f"piper/voices/voice-{lista_voces_piper[config['voz']][:-5]}/{lista_voces_piper[config['voz']]}")
            lector_Salidas = setup.reader._lector.get_devices()
            salida_actual = setup.reader._lector.find_device_id(setup.player.devicenames[config["dispositivo"]-1])
            setup.reader._lector.set_device(salida_actual)
        configurar_piper(carpeta_voces)
    if config['donations']: update.donation()
    if config.get('updates', False): updater.do_update()
    name = 'vetube-instance-checker'
    instance = wx.SingleInstanceChecker(name)
    if instance.IsAnotherRunning():
        wx.MessageBox(_('VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta.'), 'Error', wx.ICON_ERROR)
        return
    MainController()
    app.MainLoop()
run_app()
