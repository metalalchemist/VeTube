# -*- coding: utf-8 -*-
import os
import traceback
from setup import network

class BaseDownloader:
    """Clase base para gestionar descargas asíncronas de archivos."""
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir

    async def download_file(self, url, dest_path, progress_callback=None):
        """
        Descarga un archivo desde una URL a una ruta local.
        Reporta el progreso a través de un callback.
        """
        try:
            # Asegurar que el directorio de destino existe
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            async with network.client.stream("GET", url, follow_redirects=True) as response:
                if response.status_code != 200:
                    return {'success': False, 'data': f"HTTP {response.status_code} al descargar {url}"}
                
                total = int(response.headers.get('content-length', 0))
                descargado = 0
                
                with open(dest_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        descargado += len(chunk)
                        if progress_callback and total > 0:
                            # Calculamos el progreso porcentual
                            progreso_actual = int(descargado / total * 100)
                            progress_callback(progreso_actual)
                            
            return {'success': True, 'data': dest_path}
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'data': str(e)}

    def ensure_dir(self, directory):
        """Utilidad para crear directorios si no existen."""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
