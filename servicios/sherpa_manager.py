from .motor_manager import MotorManager


class SherpaManager(MotorManager):
    """Descarga e instala el motor sherpa en engines/, con progreso 0-100:
    0-90 descarga, 90-99 extracción, 100 instalado. Cancelable en todo momento.
    Gemelo de SonataManager: el trabajo lo hace MotorManager y aquí solo van las
    constantes de este paquete.

    Ojo con los dos «Kokoro»: esto es el MOTOR (el servidor que sintetiza, unos
    15 MB comprimidos), no el paquete de voces de 334 MB que instala
    kokoro_manager.py en voices/. Hacen falta los dos, y se piden por separado."""

    # Motor sherpa (servidor gRPC del modelo Kokoro) empaquetado en la misma
    # release fija «motores» que sonata, con su firma SHA-256 al lado.
    URL_MOTOR = "https://github.com/metalalchemist/VeTube/releases/download/motores/sherpa-x64.tar.bz2"
    CARPETA_MOTOR = "sherpa"
    # Tamaños medidos de esta versión del paquete (la release fija no cambia),
    # para la barra de progreso y el aviso de espacio en disco.
    TAMANO_DESCARGA = 15288727
    TAMANO_EXTRAIDO = 41316351
    # Lo mínimo que debe existir tras extraer para dar la instalación por buena:
    # el servidor y sus datos de fonemización (sherpa lleva su propia
    # espeak-ng-data dentro del paquete, distinta de la de sonata).
    FICHERO_CLAVE = "vetube-sherpa-grpc.exe"
    CARPETA_CLAVE = "espeak-ng-data"
