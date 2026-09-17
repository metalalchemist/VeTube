import asyncio
import hashlib
import os
import shutil
import tarfile
import tempfile
from logging import getLogger

import httpx

from globals.paths import ENGINES_DIR

from .base_downloader import BaseDownloader

logger = getLogger(__name__)


class MotorManager(BaseDownloader):
    """Instalador común de los motores de voz que VeTube se descarga a la carta.

    Los motores viven en la release fija «motores» del repositorio, en .tar.bz2
    y con su firma SHA-256 al lado: etiqueta fija y no «latest» para que la URL
    no cambie nunca, y .tar.bz2 por simetría con el paquete Kokoro de k2-fsa.
    Cada motor concreto (sonata para las voces Piper, sherpa para las Kokoro)
    solo pone sus constantes; lo demás es común: progreso 0-100 (0-90 descarga,
    90-99 extracción, 100 instalado), verificación de la firma, extracción en
    streaming y cancelación en todo momento.

    Lo instalado queda en engines/, junto al ejecutable como voices/: un
    directorio descargado no viaja en el build, así que lib/64/ no existe para
    él, y de paso el actualizador (que copia sin borrar) nunca lo pisa.
    """

    # --- Lo que define a cada motor ---
    # URL del paquete en la release «motores»; la firma es esta misma + .sha256.
    URL_MOTOR = ""
    # El paquete se genera con `tar -C .../64 <carpeta>`, así que sus miembros
    # cuelgan de esta carpeta, y es la que se muda entera a engines/ al final.
    CARPETA_MOTOR = ""
    # Tamaños medidos de esta versión del paquete (la release fija no cambia),
    # para la barra de progreso y el aviso de espacio en disco.
    TAMANO_DESCARGA = 0
    TAMANO_EXTRAIDO = 0
    # Lo mínimo que debe existir tras extraer para dar la instalación por buena:
    # el servidor y sus datos de fonemización (espeak-ng-data va DENTRO del
    # paquete, cada motor lleva la suya).
    FICHERO_CLAVE = ""
    CARPETA_CLAVE = ""

    def __init__(self):
        super().__init__()
        self.cancelado = False

    @property
    def url_firma(self):
        return self.URL_MOTOR + ".sha256"

    def cancelar(self):
        """Puede llamarse desde cualquier hilo: la descarga y la extracción
        comprueban esta bandera y abortan limpiamente."""
        self.cancelado = True

    def destino_final(self):
        return str(ENGINES_DIR / self.CARPETA_MOTOR)

    def hay_espacio_suficiente(self, temp_dir):
        """Comprueba el espacio libre antes de empezar: el paquete y su
        extracción conviven en el temporal antes de mudarse a engines/."""
        try:
            libre_temp = shutil.disk_usage(temp_dir).free
            # El disco del destino real (engines/ vive junto al ejecutable),
            # no el directorio de trabajo: el cwd del proceso puede estar en
            # otro disco (accesos directos, relanzamientos del actualizador).
            libre_destino = shutil.disk_usage(str(ENGINES_DIR.parent)).free
        except Exception:
            return True  # Si no se puede medir, dejamos que lo intente
        return (
            libre_temp > self.TAMANO_DESCARGA + self.TAMANO_EXTRAIDO
            and libre_destino > self.TAMANO_EXTRAIDO
        )

    async def instalar_motor(self, progress_callback=None):
        """Descarga el paquete, lo verifica, lo extrae en un temporal y lo
        mueve a engines/. Devuelve {'success': bool, 'cancelado': bool,
        'data': detalle}.

        La bandera de cancelación NO se reinicia aquí: esta corrutina empieza a
        correr cuando el bucle de red le hace sitio, y quien cancele entre medias
        (el bucle también atiende los chats) se habría quedado sin efecto. La
        reinicia quien lanza la descarga, antes de encolarla."""
        temp_dir = tempfile.mkdtemp(prefix="vetube_%s_" % self.CARPETA_MOTOR)
        tar_path = os.path.join(temp_dir, self.CARPETA_MOTOR + ".tar.bz2")
        try:
            if not self.hay_espacio_suficiente(temp_dir):
                necesario_mb = (self.TAMANO_DESCARGA + self.TAMANO_EXTRAIDO) // (
                    1024 * 1024
                )
                return {
                    "success": False,
                    "cancelado": False,
                    "data": _(
                        "No hay suficiente espacio libre en disco (se necesitan unos %d MB)."
                    )
                    % necesario_mb,
                }

            res = await self._descargar(self.URL_MOTOR, tar_path, progress_callback)
            if not res["success"]:
                return res

            firma = await self._descargar_firma()
            # La firma pudo interrumpirse por cancelación: el contrato es
            # «cancelable en todo momento», también en esta etapa intermedia.
            if self.cancelado:
                return {"success": False, "cancelado": True, "data": ""}

            # La verificación y la extracción tardan: fuera del bucle de red,
            # que mientras tanto sigue atendiendo los chats.
            return await asyncio.to_thread(
                self._verificar_extraer_e_instalar,
                tar_path,
                temp_dir,
                firma,
                progress_callback,
            )
        except Exception as e:
            logger.error(
                "Fallo al instalar el motor %s", self.CARPETA_MOTOR, exc_info=True
            )
            return {"success": False, "cancelado": False, "data": str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _descargar(self, url, dest_path, progress_callback):
        """La descarga en sí la hace BaseDownloader.download_file: aquí solo se
        le pasan las particularidades de este paquete y se traduce su resultado
        al formato con 'cancelado' que espera el resto del instalador."""
        res = await self.download_file(
            url,
            dest_path,
            progress_callback=progress_callback,
            cancel_check=lambda: self.cancelado,
            # El cliente central no tiene timeout: aquí ponemos uno de lectura
            # para que una conexión congelada termine en error visible en vez
            # de dejar la descarga (y al usuario) esperando para siempre.
            timeout=httpx.Timeout(60.0, connect=15.0),
            total_estimado=self.TAMANO_DESCARGA,
            tope_progreso=90,
        )
        if res.get("cancelado"):
            # Sin detalle: al cancelar no se le enseña ningún mensaje al usuario.
            return {"success": False, "cancelado": True, "data": ""}
        if res.get("status_code"):
            # Mensaje propio: el de la clase base lleva la URL cruda dentro y
            # este se le enseña al usuario en un cuadro de diálogo.
            return {
                "success": False,
                "cancelado": False,
                "data": _("el servidor de descargas respondió con el error HTTP %d.")
                % res["status_code"],
            }
        return {"success": res["success"], "cancelado": False, "data": res["data"]}

    async def _descargar_firma(self):
        """La firma SHA-256 publicada junto al paquete (formato «hash *nombre»).
        Devuelve el hash en minúsculas, o None si no se pudo obtener: la firma
        protege de una descarga corrupta, pero su ausencia momentánea no debe
        impedir instalar el motor (mismo criterio que el paquete Kokoro, que no
        tiene firma ninguna)."""
        from utils.network import network_manager as network

        try:
            # Como tarea vigilada y no como await directo: la bandera de
            # cancelación debe seguir mandando también aquí («cancelable en
            # todo momento»); un await directo la ignoraría hasta 30 segundos.
            tarea = asyncio.ensure_future(
                network.client.get(
                    self.url_firma,
                    follow_redirects=True,
                    timeout=httpx.Timeout(30.0, connect=15.0),
                )
            )
            while not tarea.done():
                if self.cancelado:
                    tarea.cancel()
                    return None
                await asyncio.sleep(0.2)
            respuesta = tarea.result()
            if respuesta.status_code != 200:
                logger.warning(
                    "HTTP %s al descargar la firma del motor %s; se instala sin verificar",
                    respuesta.status_code,
                    self.CARPETA_MOTOR,
                )
                return None
            return respuesta.text.split()[0].strip().lower()
        except Exception:
            logger.warning(
                "No se pudo descargar la firma del motor %s; se instala sin verificar",
                self.CARPETA_MOTOR,
                exc_info=True,
            )
            return None

    def _verificar_extraer_e_instalar(
        self, tar_path, temp_dir, firma, progress_callback
    ):
        """Corre en un hilo aparte. Verifica la firma, extrae en el temporal,
        comprueba y mueve la carpeta completa a engines/ (así nunca queda una
        instalación a medias)."""
        if firma:
            sha = hashlib.sha256()
            with open(tar_path, "rb") as f:
                while True:
                    if self.cancelado:
                        return {"success": False, "cancelado": True, "data": ""}
                    bloque = f.read(1024 * 1024)
                    if not bloque:
                        break
                    sha.update(bloque)
            if sha.hexdigest().lower() != firma:
                return {
                    "success": False,
                    "cancelado": False,
                    "data": _(
                        "el paquete descargado no supera la comprobación de integridad. Inténtalo de nuevo."
                    ),
                }

        dir_extraccion = os.path.join(temp_dir, "extraido")
        extraido = 0
        ultimo_avance = -1
        # Iteración en streaming: una sola pasada de descompresión, con los
        # ficheros copiados por bloques para que la barra avance también dentro
        # de los ejecutables grandes y la cancelación siga respondiendo (mismo
        # esquema, y mismas razones, que el instalador de Kokoro).
        with tarfile.open(tar_path, "r:bz2") as tar:
            for miembro in tar:
                if self.cancelado:
                    return {"success": False, "cancelado": True, "data": ""}
                if not self._miembro_seguro(miembro):
                    logger.warning(
                        "Miembro sospechoso ignorado en el paquete %s: %s",
                        self.CARPETA_MOTOR,
                        miembro.name,
                    )
                    continue
                ruta_miembro = os.path.join(
                    dir_extraccion, *miembro.name.replace("\\", "/").split("/")
                )
                if miembro.isdir():
                    os.makedirs(ruta_miembro, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(ruta_miembro), exist_ok=True)
                fuente = tar.extractfile(miembro)
                if fuente is None:
                    continue
                with fuente, open(ruta_miembro, "wb") as destino_f:
                    while True:
                        if self.cancelado:
                            return {"success": False, "cancelado": True, "data": ""}
                        bloque = fuente.read(1024 * 1024)
                        if not bloque:
                            break
                        destino_f.write(bloque)
                        extraido += len(bloque)
                        avance = 90 + min(9, int(extraido / self.TAMANO_EXTRAIDO * 10))
                        if progress_callback and avance != ultimo_avance:
                            ultimo_avance = avance
                            progress_callback(avance)

        origen = os.path.join(dir_extraccion, self.CARPETA_MOTOR)
        if not os.path.isfile(os.path.join(origen, self.FICHERO_CLAVE)):
            return {
                "success": False,
                "cancelado": False,
                "data": _("El paquete descargado está incompleto (falta %s).")
                % self.FICHERO_CLAVE,
            }
        if not os.path.isdir(os.path.join(origen, self.CARPETA_CLAVE)):
            return {
                "success": False,
                "cancelado": False,
                "data": _("El paquete descargado está incompleto (falta %s).")
                % self.CARPETA_CLAVE,
            }

        destino = self.destino_final()
        if os.path.isdir(destino):
            shutil.rmtree(destino)
        self.ensure_dir(str(ENGINES_DIR))
        shutil.move(origen, destino)
        if progress_callback:
            progress_callback(100)
        return {"success": True, "cancelado": False, "data": destino}

    def _miembro_seguro(self, miembro):
        """Solo ficheros y carpetas con rutas relativas sanas (sin .., sin
        absolutas, sin unidad): defensa si el paquete llegara manipulado."""
        if not (miembro.isfile() or miembro.isdir()):
            return False
        nombre = miembro.name.replace("\\", "/")
        # La barra inicial se comprueba aparte: desde Python 3.13, isabs() en
        # Windows ya no considera absoluto «/etc/passwd» (sin unidad).
        if (
            nombre.startswith("/")
            or os.path.isabs(nombre)
            or (len(nombre) > 1 and nombre[1] == ":")
        ):
            return False
        return ".." not in nombre.split("/")
