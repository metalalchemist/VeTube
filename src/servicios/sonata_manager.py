from .motor_manager import MotorManager


class SonataManager(MotorManager):
    """Descarga e instala el motor sonata en engines/, con progreso 0-100:
    0-90 descarga, 90-99 extracción, 100 instalado. Cancelable en todo momento.
    El trabajo lo hace MotorManager, que comparte con su gemelo sherpa (el motor
    de las voces Kokoro); aquí solo van las constantes de este paquete."""

    # Motor sonata (servidor gRPC de las voces Piper) empaquetado en la release
    # fija «motores» de VeTube: mismo esquema que el modelo Kokoro con la
    # release tts-models de k2-fsa. Etiqueta fija y no «latest» para que la URL
    # no cambie nunca, y en .tar.bz2 por simetría con el paquete Kokoro.
    URL_MOTOR = "https://github.com/metalalchemist/VeTube/releases/download/motores/sonata-x64.tar.bz2"
    CARPETA_MOTOR = "sonata"
    # Tamaños medidos de esta versión del paquete (la release fija no cambia),
    # para la barra de progreso y el aviso de espacio en disco.
    TAMANO_DESCARGA = 20539335
    TAMANO_EXTRAIDO = 49331043
    # Lo mínimo que debe existir tras extraer para dar la instalación por buena:
    # el servidor y sus datos de fonemización (espeak-ng-data va DENTRO del
    # paquete).
    FICHERO_CLAVE = "sonata-grpc.exe"
    CARPETA_CLAVE = "espeak-ng-data"
