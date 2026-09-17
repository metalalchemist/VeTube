import asyncio
import os
import shutil
import tarfile
import tempfile
import traceback
from logging import getLogger
from pathlib import Path

from globals.paths import VOICES_DIR
from utils.network import network_manager as network

from .base_downloader import BaseDownloader

logger = getLogger(__name__)

PIPER_VOICE_LIST_URL = (
    "https://huggingface.co/rhasspy/piper-voices/raw/v1.0.0/voices.json"
)
PIPER_VOICE_DOWNLOAD_URL_PREFIX = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
)
PIPER_SAMPLES_URL_PREFIX = "https://rhasspy.github.io/piper-samples/samples"
# URLs para variantes rápidas (RT)
RT_VOICE_LIST_URL = (
    "https://huggingface.co/datasets/mush42/piper-rt/raw/main/voices.json"
)
RT_VOICE_DOWNLOAD_URL_PREFIX = (
    "https://huggingface.co/datasets/mush42/piper-rt/resolve/main"
)

# Ficheros propios de cada variante. Las dos se descargan en la MISMA carpeta
# (voices/voice-<clave>), así que al instalar una hay que retirar la otra: si
# conviven, obtener_ruta_voz da siempre prioridad a decoder.onnx y la voz recién
# descargada se queda inalcanzable, sin ningún aviso y sin vuelta atrás desde la
# interfaz.
_FICHEROS_RT = ("encoder.onnx", "decoder.onnx")


def _limpiar_variante(dest_dir, quitar_rt):
    """Borra de la carpeta los ficheros de la variante que no se acaba de
    instalar. Con quitar_rt, los de la RT; si no, el modelo estándar."""
    try:
        for nombre in os.listdir(dest_dir):
            bajo = nombre.lower()
            es_rt = bajo in _FICHEROS_RT or (bajo.endswith(".json") and "+rt" in bajo)
            if not (bajo.endswith(".onnx") or bajo.endswith(".json")):
                continue
            if es_rt == quitar_rt:
                try:
                    os.remove(os.path.join(dest_dir, nombre))
                except OSError:
                    # Que esto falle no es inocuo: si sobrevive el decoder.onnx
                    # de la variante anterior, obtener_ruta_voz le sigue dando
                    # prioridad y la voz recién descargada no se usa nunca,
                    # mientras el diálogo anuncia que todo ha ido bien. No se
                    # ha conseguido provocar (el puente sonata no retiene el
                    # fichero tras LoadVoice), pero un antivirus o un atributo
                    # de solo lectura bastarían. Al menos que quede registrado.
                    logger.exception(
                        "No se ha podido borrar %s de %s", nombre, dest_dir
                    )
    except OSError:
        # print_exc iba a una salida que la aplicación compilada no tiene.
        logger.exception("No se ha podido repasar la carpeta de voz %s", dest_dir)


def _extraer_plano(tar_path, destino):
    """Extrae un tar en 'destino' aplanando las rutas de dentro.

    Los paquetes RT de mush42 no vienen comprimidos pese a llamarse .tar.gz
    (empiezan por «./», no por la firma gzip), así que 'r:gz' falla al abrir y
    el que trabaja de verdad es el repli 'r:'. Entre un intento y el otro se
    vacía el destino: si el primero llegó a escribir algo, no debe quedar
    mezclado con lo del segundo.
    """
    ultimo_error = None
    for modo in ("r:gz", "r:"):
        try:
            with tarfile.open(tar_path, modo) as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        # Solo el nombre del fichero, para aplanar la ruta.
                        member.name = os.path.basename(member.name)
                        tar.extract(member, destino)
            return
        except tarfile.ReadError as e:
            ultimo_error = e
            shutil.rmtree(destino, ignore_errors=True)
            os.makedirs(destino, exist_ok=True)
    raise ultimo_error


class PiperManager(BaseDownloader):
    def __init__(self):
        super().__init__()
        self.voices_data = {}
        self.rt_mapping = {}  # Mapeo de { "nombre_base": "clave_rt" }
        # False mientras no se haya podido leer el catálogo RT: la interfaz lo
        # dice, para que una columna vacía no se confunda con «no hay variante».
        self.rt_disponible = False
        self.languages = {}  # { "code": { "name_native": "...", "voices": [] } }

    async def cargar_catalogo(self):
        """Descarga y procesa el catálogo de voces estándar y RT."""
        try:
            # Descargamos catálogo estándar
            res_std = await network.client.get(PIPER_VOICE_LIST_URL)
            if res_std.status_code != 200:
                return {
                    "success": False,
                    "data": f"Error HTTP {res_std.status_code} en catálogo estándar",
                }

            self.voices_data = res_std.json()

            # Descargamos catálogo RT para saber qué voces tienen variante rápida.
            # Si falla no abortamos —el catálogo estándar sirve igual—, pero hay
            # que DECIRLO: sin este mapeo ninguna voz sale marcada como rápida y
            # la columna queda vacía, que es exactamente lo que se ve cuando de
            # verdad no hay variante. Callarlo deja al usuario sin forma de
            # distinguir «no hay RT» de «no se pudo consultar».
            try:
                res_rt = await network.client.get(RT_VOICE_LIST_URL)
                if res_rt.status_code == 200:
                    rt_data = res_rt.json()
                    # Mapeamos el 'base' (ej: es_ES-carlota-medium) con la clave del JSON RT
                    self.rt_mapping = {
                        v["base"]: rt_key
                        for rt_key, v in rt_data.items()
                        if "base" in v
                    }
                    self.rt_disponible = True
                else:
                    logger.warning(
                        "El catálogo de voces RT respondió HTTP %s", res_rt.status_code
                    )
            except Exception:
                logger.exception("No se pudo descargar el catálogo de voces RT")

            self._procesar_idiomas()
            return {"success": True}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "data": str(e)}

    def _procesar_idiomas(self):
        """Organiza las voces por idioma para facilitar el filtrado en la UI."""
        self.languages = {}
        for key, data in self.voices_data.items():
            lang_info = data.get("language", {})
            lang_code = lang_info.get("code")
            if not lang_code:
                continue

            if lang_code not in self.languages:
                self.languages[lang_code] = {
                    "name_native": lang_info.get("name_native", lang_code),
                    "name_english": lang_info.get("name_english", ""),
                    "country": lang_info.get("country_english", ""),
                    "voices": [],
                }

            # Añadimos la voz a este idioma
            voice_entry = {
                "key": key,
                "name": data.get("name", ""),
                "quality": data.get("quality", ""),
                "files": data.get("files", {}),
                "num_speakers": data.get("num_speakers", 1),
                "sample_url": self._generar_sample_url(data),
                "has_rt": key in self.rt_mapping,
            }
            self.languages[lang_code]["voices"].append(voice_entry)

    def _generar_sample_url(self, voice_data):
        """Genera la URL de la muestra de audio basándose en la estructura de Piper."""
        try:
            lang_family = voice_data["language"]["family"].lower()
            lang_code = voice_data["language"]["code"]
            voice_name = voice_data["name"]
            quality = voice_data["quality"]
            # Por defecto usamos el speaker 0 para la muestra
            return f"{PIPER_SAMPLES_URL_PREFIX}/{lang_family}/{lang_code}/{voice_name}/{quality}/speaker_0.mp3"
        except:
            return None

    def get_idiomas_disponibles(self):
        """Retorna una lista de idiomas formateada para ser amigable con lectores de pantalla."""
        # Ejemplo: "Español (Argentina)"
        lista = []
        for code, info in self.languages.items():
            nombre = info["name_native"].capitalize()
            pais = info["country"]
            if pais:
                texto = f"{nombre} ({pais})"
            else:
                texto = nombre
            lista.append({"code": code, "display": texto})
        return sorted(lista, key=lambda x: x["display"])

    def get_voces_por_idiomas(self, codigos_idioma):
        """Retorna todas las voces de los idiomas seleccionados."""
        voces = []
        for code in codigos_idioma:
            if code in self.languages:
                for v in self.languages[code]["voices"]:
                    v_info = v.copy()
                    v_info["lang_code"] = code
                    voces.append(v_info)
        return voces

    async def instalar_voz(self, voice_key, progress_callback=None):
        """
        Descarga el .onnx y el .json de una voz específica.
        """
        if voice_key not in self.voices_data:
            return {"success": False, "data": "Voz no encontrada en el catálogo."}

        data = self.voices_data[voice_key]
        archivos = data.get("files", {})
        dest_dir = str(VOICES_DIR / f"voice-{voice_key}")
        self.ensure_dir(dest_dir)

        tasks = []
        partes = []
        for rel_path in archivos.keys():
            url = f"{PIPER_VOICE_DOWNLOAD_URL_PREFIX}/{rel_path}"
            file_name = os.path.basename(rel_path)
            local_path = str(Path(dest_dir) / file_name)
            # Descarga a un nombre temporal: una descarga interrumpida no debe
            # dejar nunca un .onnx truncado que parezca una voz instalada.
            partes.append((local_path + ".part", local_path))
            # Solo el .onnx (el fichero grande) informa del progreso: si el
            # .json diminuto compartiera la barra, esta saltaría a 100 al
            # instante y volvería a bajar (los pitidos de NVDA dirían
            # «terminado» nada más empezar).
            cb = progress_callback if file_name.endswith(".onnx") else None
            tasks.append(self.download_file(url, local_path + ".part", cb))

        results = await asyncio.gather(*tasks)
        if not all(r["success"] for r in results):
            for parte, _final in partes:
                try:
                    os.remove(parte)
                except OSError:
                    pass
            return next(r for r in results if not r["success"])
        # El renombrado va dentro del try: un fallo aquí (fichero retenido por
        # el antivirus, voz que se está reinstalando) reventaba la corrutina y
        # dejaba el descargador congelado sin decir nada.
        try:
            for parte, final in partes:
                os.replace(parte, final)
            # Esta carpeta pudo tener antes la variante RT de la misma voz.
            _limpiar_variante(dest_dir, quitar_rt=True)
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "data": str(e)}

        return {"success": True, "data": dest_dir}

    async def instalar_voz_rt(self, voice_key, progress_callback=None):
        """
        Descarga y extrae la variante rápida (RT) de una voz (.tar.gz).
        """
        rt_key = self.rt_mapping.get(voice_key)
        if not rt_key:
            return {"success": False, "data": "No existe variante RT para esta voz."}

        url = f"{RT_VOICE_DOWNLOAD_URL_PREFIX}/{rt_key}.tar.gz"
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, f"{rt_key}.tar.gz")

        try:
            # Descargar el comprimido
            res = await self.download_file(url, tar_path, progress_callback)
            if not res["success"]:
                return res

            # Se extrae a un directorio de paso, NO a la carpeta de la voz: si
            # la extracción se corta a media faena (apagón, disco lleno, cierre
            # de la aplicación) durante los 63 MB del paquete, la voz que ya
            # estaba instalada no puede quedarse con restos. obtener_ruta_voz da
            # prioridad a decoder.onnx, así que media extracción convierte una
            # voz que funcionaba en una voz muda.
            stage_dir = os.path.join(temp_dir, "extraido")
            os.makedirs(stage_dir, exist_ok=True)
            _extraer_plano(tar_path, stage_dir)

            dest_dir = str(VOICES_DIR / f"voice-{voice_key}")
            self.ensure_dir(dest_dir)

            # El paso al directorio definitivo repite el patrón de instalar_voz:
            # primero se llevan todos los ficheros con el nombre acabado en
            # .part y solo después se renombran, que es lo único instantáneo.
            # shutil.move y no os.replace porque el temporal del sistema puede
            # estar en otra unidad, y ahí os.replace no cruza.
            partes = []
            try:
                for nombre in os.listdir(stage_dir):
                    final = os.path.join(dest_dir, nombre)
                    parte = final + ".part"
                    shutil.move(os.path.join(stage_dir, nombre), parte)
                    partes.append((parte, final))
                for parte, final in partes:
                    os.replace(parte, final)
            except Exception:
                for parte, _final in partes:
                    try:
                        os.remove(parte)
                    except OSError:
                        pass
                raise

            # Esta carpeta pudo tener antes la variante estándar de la misma voz.
            _limpiar_variante(dest_dir, quitar_rt=False)
            return {"success": True, "data": dest_dir}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "data": str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
