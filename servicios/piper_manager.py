import os
import json
import asyncio
import traceback
import tarfile
import tempfile
import shutil
from .base_downloader import BaseDownloader
from setup import network

PIPER_VOICE_LIST_URL = "https://huggingface.co/rhasspy/piper-voices/raw/v1.0.0/voices.json"
PIPER_VOICE_DOWNLOAD_URL_PREFIX = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
PIPER_SAMPLES_URL_PREFIX = "https://rhasspy.github.io/piper-samples/samples"
# URLs para variantes rápidas (RT)
RT_VOICE_LIST_URL = "https://huggingface.co/datasets/mush42/piper-rt/raw/main/voices.json"
RT_VOICE_DOWNLOAD_URL_PREFIX = "https://huggingface.co/datasets/mush42/piper-rt/resolve/main"

class PiperManager(BaseDownloader):
    def __init__(self):
        super().__init__()
        self.voices_data = {}
        self.rt_mapping = {} # Mapeo de { "nombre_base": "clave_rt" }
        self.languages = {} # { "code": { "name_native": "...", "voices": [] } }

    async def cargar_catalogo(self):
        """Descarga y procesa el catálogo de voces estándar y RT."""
        try:
            # Descargamos catálogo estándar
            res_std = await network.client.get(PIPER_VOICE_LIST_URL)
            if res_std.status_code != 200:
                return {'success': False, 'data': f"Error HTTP {res_std.status_code} en catálogo estándar"}
            
            self.voices_data = res_std.json()
            
            # Descargamos catálogo RT para saber qué voces tienen variante rápida
            try:
                res_rt = await network.client.get(RT_VOICE_LIST_URL)
                if res_rt.status_code == 200:
                    rt_data = res_rt.json()
                    # Mapeamos el 'base' (ej: es_ES-carlota-medium) con la clave del JSON RT
                    self.rt_mapping = {v['base']: rt_key for rt_key, v in rt_data.items() if 'base' in v}
            except:
                traceback.print_exc()

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
                'sample_url': self._generar_sample_url(data),
                'has_rt': key in self.rt_mapping
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
        Descarga el .onnx y el .json de una voz específica (Calidad Normal).
        """
        if voice_key not in self.voices_data:
            return {'success': False, 'data': 'Voz no encontrada en el catálogo.'}
        
        data = self.voices_data[voice_key]
        archivos = data.get('files', {})
        dest_dir = os.path.join("voices", f"voice-{voice_key}")
        self.ensure_dir(dest_dir)
        
        tasks = []
        for rel_path in archivos.keys():
            url = f"{PIPER_VOICE_DOWNLOAD_URL_PREFIX}/{rel_path}"
            file_name = os.path.basename(rel_path)
            local_path = os.path.join(dest_dir, file_name)
            tasks.append(self.download_file(url, local_path, progress_callback))
            
        results = await asyncio.gather(*tasks)
        for r in results:
            if not r['success']: return r
                
        return {'success': True, 'data': dest_dir}

    async def instalar_voz_rt(self, voice_key, progress_callback=None):
        """
        Descarga y extrae la variante rápida (RT) de una voz (.tar.gz).
        """
        rt_key = self.rt_mapping.get(voice_key)
        if not rt_key:
            return {'success': False, 'data': 'No existe variante RT para esta voz.'}
            
        url = f"{RT_VOICE_DOWNLOAD_URL_PREFIX}/{rt_key}.tar.gz"
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, f"{rt_key}.tar.gz")
        
        try:
            # Descargar el comprimido
            res = await self.download_file(url, tar_path, progress_callback)
            if not res['success']: return res
            
            # Extraer
            dest_dir = os.path.join("voices", f"voice-{voice_key}")
            self.ensure_dir(dest_dir)
            
            try:
                # Primero intentamos como 'gz' que es lo más común
                with tarfile.open(tar_path, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.isfile():
                            # Extraemos solo el nombre del archivo para aplanarlo
                            member.name = os.path.basename(member.name)
                            tar.extract(member, dest_dir)
            except tarfile.ReadError:
                # Si falla, podría ser un tar no comprimido
                with tarfile.open(tar_path, 'r:') as tar:
                    for member in tar.getmembers():
                        if member.isfile():
                            # Extraemos solo el nombre del archivo para aplanarlo
                            member.name = os.path.basename(member.name)
                            tar.extract(member, dest_dir)
            
            return {'success': True, 'data': dest_dir}
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'data': str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
