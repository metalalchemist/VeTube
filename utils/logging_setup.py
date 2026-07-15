# -*- coding: utf-8 -*-
"""Configuración central de logs de VeTube.

Escribe un archivo rotativo en la carpeta ``logs`` junto al programa y captura
las excepciones no controladas (hilo principal e hilos secundarios). Está pensado
para no romper nunca el arranque: si algo falla al configurar los logs, la app
sigue funcionando sin registro.
"""
import logging
import logging.handlers
import os
import sys
import threading

# Bibliotecas de terceros muy verbosas (peticiones HTTP, latidos de websocket...):
# las bajamos a WARNING para que el archivo de log siga siendo legible.
_LIBRERIAS_RUIDOSAS = (
    "httpx", "httpcore", "urllib3", "asyncio", "PIL",
    "comtypes", "websocket", "websockets",
)

# Nuestros propios módulos: los ponemos en DEBUG para tener diagnóstico fino
# (p. ej. los pasos del actualizador), mientras el resto queda en INFO. Se hace
# con lista explícita porque los loggers de VeTube no comparten un prefijo común.
# "servicios" cubre por jerarquía a todos sus submódulos (servicios.kick, etc.).
_LOGGERS_VETUBE = ("vetube", "update", "updater", "keyboard_handler", "servicios")

_configurado = False
_log = logging.getLogger("vetube")


def carpeta_logs():
    """Devuelve la ruta de la carpeta de logs (junto al ejecutable o al proyecto)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    return os.path.join(base, "logs")


def configurar_logs(nivel=logging.INFO):
    """Configura el logger raíz una sola vez. Seguro de llamar varias veces."""
    global _configurado
    if _configurado:
        return

    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    raiz = logging.getLogger()
    raiz.setLevel(nivel)

    # Archivo rotativo: máx. ~1 MB por archivo, 5 copias -> tope de ~6 MB.
    try:
        destino = carpeta_logs()
        os.makedirs(destino, exist_ok=True)
        manejador_archivo = logging.handlers.RotatingFileHandler(
            os.path.join(destino, "vetube.log"),
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        manejador_archivo.setFormatter(formato)
        raiz.addHandler(manejador_archivo)
    except OSError:
        # Si no se puede crear la carpeta o el archivo (permisos, disco lleno...),
        # no rompemos el arranque: seguimos sin log en archivo.
        pass

    # En desarrollo (no congelado) también mostramos por consola.
    if not getattr(sys, "frozen", False):
        manejador_consola = logging.StreamHandler()
        manejador_consola.setFormatter(formato)
        raiz.addHandler(manejador_consola)

    for nombre in _LIBRERIAS_RUIDOSAS:
        logging.getLogger(nombre).setLevel(logging.WARNING)

    for nombre in _LOGGERS_VETUBE:
        logging.getLogger(nombre).setLevel(logging.DEBUG)

    _instalar_captura_excepciones()

    _configurado = True
    _log.info("=== VeTube iniciado (%s, Python %s) ===",
              sys.platform, sys.version.split()[0])


def _instalar_captura_excepciones():
    """Registra en el log cualquier excepción no controlada, incluidos los hilos."""
    excepthook_previo = sys.excepthook

    def manejar_hilo_principal(tipo, valor, traza):
        if issubclass(tipo, KeyboardInterrupt):
            excepthook_previo(tipo, valor, traza)
            return
        _log.critical("Excepción no controlada", exc_info=(tipo, valor, traza))
        excepthook_previo(tipo, valor, traza)

    sys.excepthook = manejar_hilo_principal

    # threading.excepthook existe desde Python 3.8; los servicios de VeTube corren
    # en hilos (Kick, TikTok, Discord, actualizador...), así que capturar aquí es clave.
    threading_previo = threading.excepthook

    def manejar_hilo_secundario(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            threading_previo(args)
            return
        _log.critical(
            "Excepción no controlada en el hilo %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        threading_previo(args)

    threading.excepthook = manejar_hilo_secundario
