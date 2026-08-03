# -*- coding: utf-8 -*-
import os
import traceback
from setup import network

class BaseDownloader:
    """Clase base para gestionar descargas asíncronas de archivos."""
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir

    async def download_file(self, url, dest_path, progress_callback=None, cancel_check=None):
        """
        Descarga un archivo desde una URL a una ruta local.
        Reporta el progreso a través de un callback. Si se pasa cancel_check,
        se consulta en cada bloque recibido y la descarga se corta en cuanto
        devuelve True (mismo patrón que el instalador de Kokoro).
        """
        try:
            # Asegurar que el directorio de destino existe
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            async with network.client.stream("GET", url, follow_redirects=True) as response:
                if response.status_code != 200:
                    return {'success': False, 'data': f"HTTP {response.status_code} al descargar {url}"}

                total = int(response.headers.get('content-length', 0))
                descargado = 0
                ultimo_avance = -1

                with open(dest_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        if cancel_check and cancel_check():
                            return {'success': False, 'cancelado': True, 'data': 'Descarga cancelada'}
                        f.write(chunk)
                        descargado += len(chunk)
                        if progress_callback and total > 0:
                            # Solo cuando el porcentaje cambia de verdad: cada
                            # aviso cruza al hilo de la interfaz (wx.CallAfter)
                            # y un fichero grande da miles de bloques para cien
                            # valores distintos.
                            progreso_actual = int(descargado / total * 100)
                            if progreso_actual != ultimo_avance:
                                ultimo_avance = progreso_actual
                                progress_callback(progreso_actual)

            return {'success': True, 'data': dest_path}
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'data': str(e)}

    def ensure_dir(self, directory):
        """Utilidad para crear directorios si no existen."""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
