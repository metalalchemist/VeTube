from globals.data_store import config
from globals.resources import lista_voces_piper
from servicios.sonata_manager import SonataManager
from setup import reader
from TTS.sonata_handler import sonata_instalado

from .motor_downloader_controller import MotorDownloaderController


class SonataDownloaderController(MotorDownloaderController):
    """El motor sonata: el servidor de las voces Piper, que las instalaciones
    nuevas ya no traen en el build y se baja una sola vez desde la release fija
    «motores»."""

    MANAGER = SonataManager
    MOTOR = "piper"

    def motor_instalado(self):
        return sonata_instalado()

    def titulo(self):
        return _("Instalar el motor de las voces Piper")

    def presentacion(self, tamano_mb):
        return (
            _(
                "Las voces Piper necesitan el motor sonata para poder sonar. "
                "Se descarga una sola vez y ocupa %d MB aproximadamente."
            )
            % tamano_mb
        )

    def texto_ya_instalado(self):
        return _("El motor de las voces Piper ya está instalado en este equipo.")

    def texto_exito(self):
        return _(
            "El motor de las voces Piper se ha instalado correctamente. Los mensajes ya pueden sonar con la voz elegida."
        )

    def texto_error(self, detalle):
        return _("No se pudo instalar el motor de las voces Piper: %s") % detalle

    def cargar_voz_activa(self):
        if lista_voces_piper and lista_voces_piper[0] != _("No hay voces instaladas"):
            if not (0 <= config.get("voz", 0) < len(lista_voces_piper)):
                config["voz"] = 0
            from TTS.list_voices import obtener_ruta_voz

            model_path = obtener_ruta_voz(lista_voces_piper[config["voz"]])
            if model_path:
                reader._lector.load_model(model_path)
            # Import aquí y no en cabecera: app_utilitys importa setup, y este
            # módulo se importa desde los menús antes de que setup termine.
            from utils.app_utilitys import fijar_dispositivo_lector

            fijar_dispositivo_lector()
