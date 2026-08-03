import os
import glob
import asyncio
import traceback
from .base_downloader import BaseDownloader
from setup import network

PIPER_VOICE_LIST_URL = "https://huggingface.co/rhasspy/piper-voices/raw/v1.0.0/voices.json"
PIPER_VOICE_DOWNLOAD_URL_PREFIX = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
PIPER_SAMPLES_URL_PREFIX = "https://rhasspy.github.io/piper-samples/samples"

# Ficheros de las antiguas voces RT. La variante se retiró del catálogo: el
# motor sherpa no puede usar esos modelos partidos, y cada voz RT existe
# también en versión estándar (misma calidad de sonido).
_FICHEROS_RT = ("encoder.onnx", "decoder.onnx")

def _es_json_rt(nombre):
    """Los paquetes RT de mush42 llevan «+RT» en el nombre de su .json
    (por ejemplo fr_FR-mls+RT-medium.json)."""
    return nombre.endswith(".json") and "+RT" in nombre

def voces_rt_instaladas():
    """Recorre voices/ y clasifica las carpetas con restos de la variante RT.

    Devuelve (puras, mixtas): claves de voz cuya carpeta SOLO tiene los
    ficheros RT (hay que descargar la variante estándar para no perder la
    voz) y claves que ya tienen un modelo estándar además de los restos RT
    (basta con limpiarlas).
    """
    puras, mixtas = [], []
    if not os.path.isdir("voices"):
        return puras, mixtas
    for carpeta in os.listdir("voices"):
        ruta = os.path.join("voices", carpeta)
        if not (carpeta.startswith("voice-") and os.path.isdir(ruta)):
            continue
        onnx = [os.path.basename(m).lower() for m in glob.glob(os.path.join(ruta, "*.onnx"))]
        if not any(f in onnx for f in _FICHEROS_RT):
            continue
        clave = carpeta[len("voice-"):]
        if any(f not in _FICHEROS_RT for f in onnx):
            mixtas.append(clave)
        else:
            puras.append(clave)
    return puras, mixtas

def limpiar_ficheros_rt(voice_key):
    """Borra los ficheros de la variante RT de la carpeta de una voz."""
    ruta = os.path.join("voices", f"voice-{voice_key}")
    try:
        for nombre in os.listdir(ruta):
            if nombre.lower() in _FICHEROS_RT or _es_json_rt(nombre):
                os.remove(os.path.join(ruta, nombre))
    except OSError:
        traceback.print_exc()

class PiperManager(BaseDownloader):
    def __init__(self):
        super().__init__()
        self.voices_data = {}
        self.languages = {} # { "code": { "name_native": "...", "voices": [] } }
        self.cancelado = False

    def cancelar(self):
        """Corta la descarga en curso en el siguiente bloque recibido."""
        self.cancelado = True

    async def cargar_catalogo(self):
        """Descarga y procesa el catálogo de voces."""
        try:
            res_std = await network.client.get(PIPER_VOICE_LIST_URL)
            if res_std.status_code != 200:
                return {'success': False, 'data': f"Error HTTP {res_std.status_code} en catálogo estándar"}

            self.voices_data = res_std.json()
            self._procesar_idiomas()
            return {'success': True}
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'data': str(e)}

    def _procesar_idiomas(self):
        """Organiza las voces por idioma para facilitar el filtrado en la UI."""
        self.languages = {}
        for key, data in self.voices_data.items():
            lang_info = data.get('language', {})
            lang_code = lang_info.get('code')
            if not lang_code: continue

            if lang_code not in self.languages:
                self.languages[lang_code] = {
                    'name_native': lang_info.get('name_native', lang_code),
                    'name_english': lang_info.get('name_english', ''),
                    'country': lang_info.get('country_english', ''),
                    'voices': []
                }

            # Añadimos la voz a este idioma
            voice_entry = {
                'key': key,
                'name': data.get('name', ''),
                'quality': data.get('quality', ''),
                'files': data.get('files', {}),
                'num_speakers': data.get('num_speakers', 1),
                'sample_url': self._generar_sample_url(data)
            }
            self.languages[lang_code]['voices'].append(voice_entry)

    def _generar_sample_url(self, voice_data):
        """Genera la URL de la muestra de audio basándose en la estructura de Piper."""
        try:
            lang_family = voice_data['language']['family'].lower()
            lang_code = voice_data['language']['code']
            voice_name = voice_data['name']
            quality = voice_data['quality']
            # Por defecto usamos el speaker 0 para la muestra
            return f"{PIPER_SAMPLES_URL_PREFIX}/{lang_family}/{lang_code}/{voice_name}/{quality}/speaker_0.mp3"
        except:
            return None

    def get_idiomas_disponibles(self):
        """Retorna una lista de idiomas formateada para ser amigable con lectores de pantalla."""
        # Ejemplo: "Español (Argentina)"
        lista = []
        for code, info in self.languages.items():
            nombre = info['name_native'].capitalize()
            pais = info['country']
            if pais:
                texto = f"{nombre} ({pais})"
            else:
                texto = nombre
            lista.append({'code': code, 'display': texto})
        return sorted(lista, key=lambda x: x['display'])

    def get_voces_por_idiomas(self, codigos_idioma):
        """Retorna todas las voces de los idiomas seleccionados."""
        voces = []
        for code in codigos_idioma:
            if code in self.languages:
                for v in self.languages[code]['voices']:
                    v_info = v.copy()
                    v_info['lang_code'] = code
                    voces.append(v_info)
        return voces

    async def instalar_voz(self, voice_key, progress_callback=None):
        """
        Descarga el .onnx y el .json de una voz específica.
        """
        if voice_key not in self.voices_data:
            return {'success': False, 'data': 'Voz no encontrada en el catálogo.'}

        data = self.voices_data[voice_key]
        archivos = data.get('files', {})
        dest_dir = os.path.join("voices", f"voice-{voice_key}")
        self.ensure_dir(dest_dir)

        tasks = []
        partes = []
        for rel_path in archivos.keys():
            url = f"{PIPER_VOICE_DOWNLOAD_URL_PREFIX}/{rel_path}"
            file_name = os.path.basename(rel_path)
            local_path = os.path.join(dest_dir, file_name)
            # Descarga a un nombre temporal: una descarga interrumpida no debe
            # dejar nunca un .onnx truncado que parezca una voz instalada.
            partes.append((local_path + ".part", local_path))
            # Solo el .onnx (el fichero grande) informa del progreso: si el
            # .json diminuto compartiera la barra, esta saltaría a 100 al
            # instante y volvería a bajar (los pitidos de NVDA dirían
            # «terminado» nada más empezar).
            cb = progress_callback if file_name.endswith(".onnx") else None
            tasks.append(self.download_file(url, local_path + ".part", cb,
                                            cancel_check=lambda: self.cancelado))

        results = await asyncio.gather(*tasks)
        if not all(r['success'] for r in results):
            for parte, _final in partes:
                try:
                    os.remove(parte)
                except OSError:
                    pass
            return next(r for r in results if not r['success'])
        # Renombrado y preparación van dentro del try: un fallo aquí (fichero
        # retenido por el antivirus, voz que se está reinstalando) reventaba la
        # corrutina y dejaba el descargador congelado sin decir nada.
        try:
            for parte, final in partes:
                os.replace(parte, final)

            # El motor sherpa necesita el tokens.txt y los metadatos del .onnx:
            # se preparan desde el .json recién descargado (equivalente a lo que
            # traen de fábrica los paquetes oficiales k2-fsa). forzar=True
            # porque al reinstalar una voz el tokens.txt anterior sigue ahí y el
            # .onnx nuevo se quedaría sin metadatos.
            from TTS.sherpa_handler import preparar_voz_piper
            for rel_path in archivos.keys():
                if rel_path.endswith(".onnx.json"):
                    preparar_voz_piper(os.path.join(dest_dir, os.path.basename(rel_path)),
                                       forzar=True)
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'data': str(e)}

        return {'success': True, 'data': dest_dir}
