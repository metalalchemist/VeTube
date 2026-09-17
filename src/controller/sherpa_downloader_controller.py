from globals.data_store import config
from servicios.sherpa_manager import SherpaManager
from setup import reader
from TTS.sherpa_handler import (
    kokoro_model_instalado,
    kokoro_voice_config,
    sherpa_instalado,
)

from .motor_downloader_controller import MotorDownloaderController


class SherpaDownloaderController(MotorDownloaderController):
    """El motor sherpa: el servidor de las voces Kokoro, que las instalaciones
    nuevas ya no traen en el build y se baja una sola vez desde la release fija
    «motores», igual que sonata para las voces Piper.

    Es el motor, no el paquete de voces de 334 MB: ese lo instala
    KokoroDownloaderController y se pide aparte. Hacen falta los dos."""

    MANAGER = SherpaManager
    MOTOR = "kokoro"

    def motor_instalado(self):
        return sherpa_instalado()

    def titulo(self):
        return _("Instalar el motor de las voces Kokoro")

    def presentacion(self, tamano_mb):
        return (
            _(
                "Las voces Kokoro necesitan el motor sherpa para poder sonar. "
                "Se descarga una sola vez y ocupa %d MB aproximadamente."
            )
            % tamano_mb
        )

    def texto_ya_instalado(self):
        return _("El motor de las voces Kokoro ya está instalado en este equipo.")

    def texto_exito(self):
        if not kokoro_model_instalado():
            # Aquí no se puede prometer lo mismo que con sonata: las voces
            # Kokoro son otro paquete, de 334 MB, que suele ofrecerse justo
            # después. Decir que ya suena contradiría el diálogo siguiente.
            return _(
                "El motor de las voces Kokoro se ha instalado correctamente. Todavía falta el paquete de voces Kokoro para que puedan sonar."
            )
        return _(
            "El motor de las voces Kokoro se ha instalado correctamente. Los mensajes ya pueden sonar con la voz elegida."
        )

    def texto_error(self, detalle):
        return _("No se pudo instalar el motor de las voces Kokoro: %s") % detalle

    def cargar_voz_activa(self):
        # Sin el paquete de voces instalado no hay nada que cargar todavía: el
        # puente queda levantado y esperando a que lo descarguen aparte.
        config_kokoro = kokoro_voice_config(config.get("voz", 0))
        if config_kokoro is not None:
            reader._lector.load_model(config_kokoro)
        # Import aquí y no en cabecera: app_utilitys importa setup, y este
        # módulo se importa desde los menús antes de que setup termine.
        from utils.app_utilitys import fijar_dispositivo_lector

        fijar_dispositivo_lector()
