# -*- coding: utf-8 -*-
import os
import json
import asyncio
import tempfile
import shutil
import zipfile
import httpx
import traceback

class GestorRepositorios:
    def __init__(self, frame, github_repo, rama='master', local_dir='.', json_file='languages.json'):
        self.frame = frame
        self.github_repo = github_repo
        self.rama = rama
        self.local_dir = local_dir
        self.json_file = json_file
        if not os.path.exists(self.json_file):
            with open(self.json_file, 'w', encoding='utf-8') as file:
                json.dump({}, file, indent='\t')

    def cargar_idiomas_locales(self):
        try:
            if not os.path.exists(self.json_file): return {'success': True, 'data': {}}
            with open(self.json_file, 'r', encoding='utf-8') as file:
                return {'success': True, 'data': json.load(file)}
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error al cargar el archivo de idiomas local.')}

    def guardar_idiomas_locales(self, idiomas):
        try:
            with open(self.json_file, 'w', encoding='utf-8') as file:
                json.dump(idiomas, file, indent='\t', ensure_ascii=False)
            return {'success': True, 'data': 'OK'}
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error al guardar el archivo de idiomas local.')}

    async def obtener_idiomas_remotos(self):
        try:
            url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.rama}/translates/languages.json"
            async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return {'success': True, 'data': response.json()}
                return {'success': False, 'data': f"HTTP {response.status_code}"}
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error de conexión con el servidor.')}

    async def comprobar_nuevos_y_actualizaciones(self):
        res_loc = self.cargar_idiomas_locales()
        if not res_loc['success']: return res_loc
        res_rem = await self.obtener_idiomas_remotos()
        if not res_rem['success']: return res_rem

        locales = res_loc['data']
        remotos = res_rem['data']
        nuevos = {k: v for k, v in remotos.items() if k not in locales}
        actualizaciones = {k: v for k, v in remotos.items() if k in locales and locales[k] < v}
        
        if nuevos or actualizaciones:
            return {'success': True, 'data': {'nuevos': nuevos, 'actualizaciones': actualizaciones}}
        return {'success': False, 'data': _('No hay actualizaciones ni nuevos idiomas disponibles.'), 'error': False}

    async def descargar_zip(self, idioma, download_dir, progress_callback=None):
        try:
            url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.rama}/translates/{idioma}.zip"
            ruta_zip = os.path.join(download_dir, f"{idioma}.zip")
            async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}, follow_redirects=True, timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    total = int(response.headers.get('content-length', 0))
                    descargado = 0
                    with open(ruta_zip, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                            descargado += len(chunk)
                            if progress_callback and total > 0:
                                progress_callback(int(descargado / total * 100))
            return {'success': True, 'data': ruta_zip}
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error al descargar el archivo del idioma %s.') % idioma}

    def descomprimir_zip(self, ruta_zip, destino):
        try:
            if not os.path.exists(destino): os.makedirs(destino)
            with zipfile.ZipFile(ruta_zip, 'r') as z:
                z.extractall(destino)
            return {'success': True}
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error al extraer los archivos del idioma.')}

    async def instalar_idioma(self, idioma, version, progress_callback=None):
        temp = tempfile.mkdtemp()
        try:
            res = await self.descargar_zip(idioma, temp, progress_callback)
            if not res['success']: return res
            
            # Extraer en la carpeta locales
            ruta_destino = os.path.join(self.local_dir, "locales")
            res = self.descomprimir_zip(res['data'], ruta_destino)
            if not res['success']: return res
            
            return self.actualizar_idioma_local(idioma, version)
        except Exception:
            traceback.print_exc()
            return {'success': False, 'data': _('Error inesperado durante la instalación.')}
        finally:
            if os.path.exists(temp):
                shutil.rmtree(temp, ignore_errors=True)

    def actualizar_idioma_local(self, idioma, version):
        res = self.cargar_idiomas_locales()
        if not res['success']: return res
        idiomas = res['data']
        idiomas[idioma] = version
        return self.guardar_idiomas_locales(idiomas)
