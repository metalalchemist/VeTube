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
def fijar_dispositivo_lector():
    """Fija en el puente sherpa la salida de audio que marca config['dispositivo']
    (1 = el primero de la lista, igual que para el player).

    Los nombres que ya tiene el player valen de known_devices: así no hay que
    volver a abrir el subsistema de audio solo para enumerar los dispositivos."""
    nombres_dispositivos = player.devicenames
    dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres_dispositivos)]
    nombre_actual = nombres_dispositivos[config["dispositivo"]-1]
    reader._lector.set_device(reader._lector.find_device_id(nombre_actual, known_devices=dispositivos_formateados))
def limpiar_motor_antiguo():
    """Borra la carpeta del antiguo servidor sonata (64/sonata) si quedó de
    una instalación anterior. El actualizador copia la versión nueva POR
    ENCIMA sin borrar nada (copytree con dirs_exist_ok) y el instalador
    tampoco limpia restos: sin esto, los dos motores convivirían para
    siempre. Ningún sonata-grpc.exe puede seguir vivo (el Job Object de la
    versión anterior lo mata al cerrarse VeTube, incluso tras un cierre
    forzado); si aun así el borrado falla, se reintenta en el próximo
    arranque."""
    antigua = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "64", "sonata")
    if os.path.isdir(antigua):
        import shutil
        try:
            shutil.rmtree(antigua)
        except OSError:
            pass
def proponer_migracion_rt(parent):
    """Detecta restos de las antiguas voces rápidas (RT) y reinstala en
    variante estándar las que se quedarían sin modelo. Llamar antes de cargar
    la voz de Piper (arranque y Aceptar de los Ajustes). Devuelve True si la
    lista de voces pudo cambiar."""
    from servicios.piper_manager import voces_rt_instaladas, limpiar_ficheros_rt
    # config['voz'] es una POSICIÓN en la lista, y la migración la hace crecer
    # (una carpeta RT pura pasa a contar como voz instalada): nos quedamos con
    # el NOMBRE de la voz activa para recolocarla después. Comprobar solo el
    # rango no sirve — un índice desplazado sigue estando dentro.
    voz_activa = (lista_voces_piper[config['voz']]
                  if 0 <= config['voz'] < len(lista_voces_piper) else None)
    puras, mixtas = voces_rt_instaladas()
    # Carpetas que ya tienen el modelo estándar: los restos RT solo ocupan sitio.
    for clave in mixtas:
        limpiar_ficheros_rt(clave)
    if puras:
        nombres = ", ".join(sorted(puras))
        if response(_("Las voces rápidas (RT) ya no existen en VeTube: el nuevo motor de voz no las necesita y la versión estándar suena igual. ¿Quieres descargar ahora la versión estándar de estas voces? %s") % nombres,
                    _("Voces por actualizar")) == wx.ID_YES:
            from controller.piper_migracion_rt_controller import PiperMigracionRTController
            PiperMigracionRTController(parent, sorted(puras)).show()
    if not (puras or mixtas):
        return False
    # La lista visible puede haber cambiado: una carpeta RT pura ya no cuenta
    # como voz instalada hasta que se reinstala su variante estándar.
    lista_voces_piper.clear()
    nuevas = piper_list_voices()
    lista_voces_piper.extend(nuevas if nuevas else [_("No hay voces instaladas")])
    if voz_activa in lista_voces_piper:
        config['voz'] = lista_voces_piper.index(voz_activa)
    elif not (0 <= config['voz'] < len(lista_voces_piper)):
        config['voz'] = 0
    return True
def _cargar_voz_piper_actual():
    """Carga en el puente la voz de Piper que marca config['voz'], con el
    dispositivo de salida configurado."""
    model_path = obtener_ruta_voz(lista_voces_piper[config['voz']])
    if not model_path:
        return
    reader._lector = reader._lector.piperSpeak(model_path)
    fijar_dispositivo_lector()
def configurar_piper(parent, carpeta_voces):
    migrado = proponer_migracion_rt(parent)
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
                _cargar_voz_piper_actual()
                reader.leer_auto(_("Lector Piper inicializado correctamente."))
    elif isinstance(onnx_models, str) or isinstance(onnx_models, list):
        # Solo se recoloca la voz si el índice guardado quedó fuera de rango:
        # resetearla siempre hacía perder la voz elegida en cada Aceptar.
        if not (0 <= config['voz'] < len(lista_voces_piper)):
            config['voz'] = 0
        if migrado:
            # La migración RT acaba de reinstalar modelos: cargar la voz
            # actual aquí mismo (en el arranque ya nadie más lo hará, el
            # bloque de run_main_window pasó antes de la migración).
            _cargar_voz_piper_actual()