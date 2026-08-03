# -*- coding: utf-8 -*-
import os
import asyncio
import tarfile
import tempfile
import shutil
import httpx
from logging import getLogger
from .base_downloader import BaseDownloader

logger = getLogger(__name__)

# Modelo Kokoro empaquetado por k2-fsa (release tts-models de sherpa-onnx).
# Un único paquete con las 53 voces de todos los idiomas: se descarga una vez.
KOKORO_MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2"
CARPETA_MODELO = "kokoro-multi-lang-v1_0"
# Tamaños de esta versión concreta del paquete, para la barra de progreso y el
# aviso de espacio en disco (si el servidor no informa content-length).
TAMANO_DESCARGA = 349418188
TAMANO_EXTRAIDO = 400786089
# Ficheros que deben existir tras extraer para dar la instalación por buena.
FICHEROS_CLAVE = ("model.onnx", "voices.bin", "tokens.txt")

class KokoroManager(BaseDownloader):
    """Descarga e instala el modelo Kokoro en voices/, con progreso 0-100:
    0-90 descarga, 90-99 extracción, 100 instalado. Cancelable en todo momento."""

    def __init__(self):
        super().__init__()
        self.cancelado = False

    def cancelar(self):
        """Puede llamarse desde cualquier hilo: la descarga y la extracción
        comprueban esta bandera y abortan limpiamente."""
        self.cancelado = True

    def destino_final(self):
        return os.path.join("voices", CARPETA_MODELO)

    def hay_espacio_suficiente(self, temp_dir):
        """Comprueba el espacio libre antes de empezar: el paquete y su
        extracción conviven en el temporal antes de mudarse a voices/."""
        try:
            libre_temp = shutil.disk_usage(temp_dir).free
            libre_destino = shutil.disk_usage(os.path.abspath(".")).free
        except Exception:
            return True  # Si no se puede medir, dejamos que lo intente
        return (libre_temp > TAMANO_DESCARGA + TAMANO_EXTRAIDO
                and libre_destino > TAMANO_EXTRAIDO)

    async def instalar_modelo(self, progress_callback=None):
        """Descarga el paquete, lo extrae en un temporal y lo mueve a voices/.
        Devuelve {'success': bool, 'cancelado': bool, 'data': detalle}.

        La bandera de cancelación NO se reinicia aquí: esta corrutina empieza a
        correr cuando el bucle de red le hace sitio, y quien cancele entre medias
        (el bucle también atiende los chats) se habría quedado sin efecto. La
        reinicia quien lanza la descarga, antes de encolarla."""
        temp_dir = tempfile.mkdtemp(prefix="vetube_kokoro_")
        tar_path = os.path.join(temp_dir, CARPETA_MODELO + ".tar.bz2")
        try:
            if not self.hay_espacio_suficiente(temp_dir):
                necesario_mb = (TAMANO_DESCARGA + TAMANO_EXTRAIDO) // (1024 * 1024)
                return {'success': False, 'cancelado': False,
                        'data': _("No hay suficiente espacio libre en disco (se necesitan unos %d MB).") % necesario_mb}

            res = await self._descargar(KOKORO_MODEL_URL, tar_path, progress_callback)
            if not res['success']:
                return res

            # La extracción de un .tar.bz2 grande tarda: fuera del bucle de red,
            # que mientras tanto sigue atendiendo los chats.
            return await asyncio.to_thread(self._extraer_e_instalar, tar_path, temp_dir, progress_callback)
        except Exception as e:
            logger.error("Fallo al instalar el modelo Kokoro", exc_info=True)
            return {'success': False, 'cancelado': False, 'data': str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _descargar(self, url, dest_path, progress_callback):
        """La descarga en sí la hace BaseDownloader.download_file: aquí solo se
        le pasan las particularidades de este paquete y se traduce su resultado
        al formato con 'cancelado' que espera el resto del instalador."""
        res = await self.download_file(
            url, dest_path,
            progress_callback=progress_callback,
            cancel_check=lambda: self.cancelado,
            # El cliente central no tiene timeout: aquí ponemos uno de lectura
            # para que una conexión congelada termine en error visible en vez
            # de dejar la descarga (y al usuario) esperando para siempre.
            timeout=httpx.Timeout(60.0, connect=15.0),
            total_estimado=TAMANO_DESCARGA,
            tope_progreso=90)
        if res.get('cancelado'):
            # Sin detalle: al cancelar no se le enseña ningún mensaje al usuario.
            return {'success': False, 'cancelado': True, 'data': ''}
        if res.get('status_code'):
            # Mensaje propio: el de la clase base lleva la URL cruda dentro y
            # este se le enseña al usuario en un cuadro de diálogo.
            return {'success': False, 'cancelado': False,
                    'data': _("el servidor de descargas respondió con el error HTTP %d.") % res['status_code']}
        return {'success': res['success'], 'cancelado': False, 'data': res['data']}

    def _extraer_e_instalar(self, tar_path, temp_dir, progress_callback):
        """Corre en un hilo aparte. Extrae en el temporal, verifica y mueve la
        carpeta completa a voices/ (así nunca queda una instalación a medias)."""
        dir_extraccion = os.path.join(temp_dir, "extraido")
        extraido = 0
        ultimo_avance = -1
        # Iteración en streaming: una sola pasada de descompresión. Pedir la
        # lista de miembros por adelantado obligaría a descomprimir dos veces.
        # Los ficheros se copian por bloques (no con tar.extract) para que el
        # progreso avance DENTRO del model.onnx de 310 MB: sin esto la barra se
        # congela ~15 segundos, que en un lector de pantalla suena a cuelgue,
        # y la cancelación tampoco respondería durante ese fichero.
        with tarfile.open(tar_path, 'r:bz2') as tar:
            for miembro in tar:
                if self.cancelado:
                    return {'success': False, 'cancelado': True, 'data': ''}
                if not self._miembro_seguro(miembro):
                    logger.warning("Miembro sospechoso ignorado en el paquete Kokoro: %s", miembro.name)
                    continue
                ruta_miembro = os.path.join(dir_extraccion, *miembro.name.replace('\\', '/').split('/'))
                if miembro.isdir():
                    os.makedirs(ruta_miembro, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(ruta_miembro), exist_ok=True)
                fuente = tar.extractfile(miembro)
                if fuente is None:
                    continue
                with fuente, open(ruta_miembro, 'wb') as destino_f:
                    while True:
                        if self.cancelado:
                            return {'success': False, 'cancelado': True, 'data': ''}
                        bloque = fuente.read(1024 * 1024)
                        if not bloque:
                            break
                        destino_f.write(bloque)
                        extraido += len(bloque)
                        avance = 90 + min(9, int(extraido / TAMANO_EXTRAIDO * 10))
                        if progress_callback and avance != ultimo_avance:
                            ultimo_avance = avance
                            progress_callback(avance)

        origen = os.path.join(dir_extraccion, CARPETA_MODELO)
        for fichero in FICHEROS_CLAVE:
            if not os.path.isfile(os.path.join(origen, fichero)):
                return {'success': False, 'cancelado': False,
                        'data': _("El paquete descargado está incompleto (falta %s).") % fichero}
        if not os.path.isdir(os.path.join(origen, "espeak-ng-data")):
            return {'success': False, 'cancelado': False,
                    'data': _("El paquete descargado está incompleto (falta %s).") % "espeak-ng-data"}

        destino = self.destino_final()
        if os.path.isdir(destino):
            shutil.rmtree(destino)
        self.ensure_dir("voices")
        shutil.move(origen, destino)
        if progress_callback:
            progress_callback(100)
        return {'success': True, 'cancelado': False, 'data': destino}

    def _miembro_seguro(self, miembro):
        """Solo ficheros y carpetas con rutas relativas sanas (sin .., sin
        absolutas, sin unidad): defensa si el paquete llegara manipulado."""
        if not (miembro.isfile() or miembro.isdir()):
            return False
        nombre = miembro.name.replace('\\', '/')
        if os.path.isabs(nombre) or (len(nombre) > 1 and nombre[1] == ':'):
            return False
        return '..' not in nombre.split('/')
