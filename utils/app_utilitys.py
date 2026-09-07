import os
import sys

import wx

from controller.piper_downloader_controller import PiperDownloaderController
from globals.data_store import config
from globals.resources import lista_voces_piper
from setup import player, reader
from TTS.lector import detect_onnx_models
from TTS.list_voices import obtener_ruta_voz, piper_list_voices
from ui.dialog_response import response


def restart_program():
    """Function that restarts the application if is executed."""
    args = sys.argv[:]
    if not hasattr(sys, "frozen"):
        args.insert(0, sys.executable)
    if sys.platform == "win32":
        args = ['"%s"' % arg for arg in args]
    pidpath = os.path.join(os.getenv("temp"), "{}.pid".format("VeTube"))
    if os.path.exists(pidpath):
        os.remove(pidpath)
    os.execv(sys.executable, args)


def porcentaje_a_escala(porcentaje):
    return 1.25 + porcentaje * 0.125


def fijar_dispositivo_lector():
    """Fija en el motor de voz activo (sonata o sherpa, según motor_de_interfaz(),
    que no es config['sistemaTTS'] cuando manda la casilla «Usar voz sapi»)
    la salida de audio que marca config['dispositivo'] (1 = el primero de la
    lista, igual que para el player).

    Los nombres que ya tiene el player valen de known_devices: así no hay que
    volver a abrir el subsistema de audio solo para enumerar los dispositivos."""
    nombres_dispositivos = player.devicenames
    if not nombres_dispositivos:
        # Arranque mudo (sin dispositivo de audio): no hay nada que fijar, y la
        # línea de abajo reventaría con IndexError al indexar la lista vacía.
        return
    dispositivos_formateados = [
        {"name": n, "id": i} for i, n in enumerate(nombres_dispositivos)
    ]
    nombre_actual = nombres_dispositivos[config["dispositivo"] - 1]
    reader._lector.set_device(
        reader._lector.find_device_id(
            nombre_actual, known_devices=dispositivos_formateados
        )
    )


def _cargar_voz_piper_actual():
    """Carga en el puente la voz de Piper que marca config['voz'], con el
    dispositivo de salida configurado."""
    model_path = obtener_ruta_voz(lista_voces_piper[config["voz"]])
    if not model_path:
        return
    reader._lector = reader._lector.piperSpeak(model_path)
    fijar_dispositivo_lector()


def _asegurar_motor(parent, esta_instalado, controlador, pregunta, titulo):
    """True si el motor ya está en el equipo; si falta, ofrece descargarlo y
    devuelve si quedó instalado. Común a los dos motores que se bajan a la
    carta (sonata para Piper, sherpa para Kokoro)."""
    if esta_instalado():
        return True
    if response(pregunta, titulo, wx.YES_NO | wx.ICON_ASTERISK) == wx.ID_YES:
        controlador(parent).show()
    return esta_instalado()


def asegurar_motor_sonata(parent):
    """True si el motor sonata (el servidor de las voces Piper) está en el
    equipo, ofreciendo descargarlo si falta. Lo llaman el arranque con Piper
    elegido y la prueba de voz de los Ajustes; el Aceptar de los Ajustes abre
    el descargador directamente, como el de Kokoro. Mientras el motor falte,
    el chat habla por el respaldo SAPI del instante (ver configurar_tts)."""
    # Imports diferidos: este módulo se importa desde setup y el controlador
    # del descargador importa setup a su vez.
    from controller.sonata_downloader_controller import SonataDownloaderController
    from TTS.sonata_handler import sonata_instalado

    return _asegurar_motor(
        parent,
        sonata_instalado,
        SonataDownloaderController,
        _(
            "Las voces Piper necesitan su motor de voz, que aún no está en este equipo. ¿Deseas descargarlo ahora? Mientras tanto te acompañará una voz del sistema."
        ),
        _("Falta el motor de las voces Piper"),
    )


def asegurar_motor_kokoro(parent):
    """Lo mismo para el motor sherpa, el servidor de las voces Kokoro. Es el
    motor, no el paquete de voces de 334 MB: ese se ofrece aparte y después,
    porque sin motor no sonaría igualmente."""
    from controller.sherpa_downloader_controller import SherpaDownloaderController
    from TTS.sherpa_handler import sherpa_instalado

    return _asegurar_motor(
        parent,
        sherpa_instalado,
        SherpaDownloaderController,
        _(
            "Las voces Kokoro necesitan su motor de voz, que aún no está en este equipo. ¿Deseas descargarlo ahora? Mientras tanto te acompañará una voz del sistema."
        ),
        _("Falta el motor de las voces Kokoro"),
    )


def configurar_piper(parent, carpeta_voces):
    onnx_models = detect_onnx_models(carpeta_voces)
    if onnx_models is None:
        if (
            response(
                _(
                    "Necesitas al menos una voz para poder usar el sintetizador Piper. ¿Deseas abrir el descargador de voces ahora para buscar e instalar una?"
                ),
                _("No hay voces instaladas"),
                wx.YES_NO | wx.ICON_ASTERISK,
            )
            == wx.ID_YES
        ):
            downloader = PiperDownloaderController(parent)
            downloader.show()
            nuevas_voces = detect_onnx_models(carpeta_voces)
            if nuevas_voces is not None:
                lista_voces_piper.clear()
                lista_voces_piper.extend(piper_list_voices())
                config["voz"] = 0
                _cargar_voz_piper_actual()
                # Solo si el motor sonata está de verdad: sin él quien habla es
                # el respaldo SAPI, y esta frase mentiría en su boca (regla de
                # leer_motor: quien llama comprueba el motor antes de anunciar).
                from TTS.sonata_handler import sonata_instalado

                if sonata_instalado():
                    reader.leer_motor(_("Lector Piper inicializado correctamente."))
    elif isinstance(onnx_models, str) or isinstance(onnx_models, list):
        # Solo se recoloca la voz si el índice guardado quedó fuera de rango:
        # resetearla siempre hacía perder la voz elegida en cada Aceptar.
        if not (0 <= config["voz"] < len(lista_voces_piper)):
            config["voz"] = 0
