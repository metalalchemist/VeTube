# -*- coding: utf-8 -*-
import os
from logging import getLogger
from setup import network

logger = getLogger(__name__)

class BaseDownloader:
    """Clase base para gestionar descargas asíncronas de archivos."""
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir

    async def download_file(self, url, dest_path, progress_callback=None, cancel_check=None,
                            timeout=None, total_estimado=0, tope_progreso=100):
        """
        Descarga un archivo desde una URL a una ruta local.
        Reporta el progreso a través de un callback. Si se pasa cancel_check,
        se consulta en cada bloque recibido y la descarga se corta en cuanto
        devuelve True.

        Los tres últimos parámetros son para descargas con necesidades propias:
        timeout, un límite de httpx solo para esta descarga; total_estimado, el
        tamaño conocido de antemano por si el servidor no informa del
        content-length; tope_progreso, el valor máximo que recibe el callback
        cuando la descarga solo ocupa un tramo de la barra y el resto se
        reserva para lo que venga después.
        """
        try:
            # Asegurar que el directorio de destino existe
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Sin timeout propio se deja el del cliente central: pasarle None a
            # httpx no significa "el de siempre", significa "sin límite".
            opciones = {'timeout': timeout} if timeout is not None else {}
            async with network.client.stream("GET", url, follow_redirects=True, **opciones) as response:
                if response.status_code != 200:
                    logger.error("HTTP %s al descargar %s", response.status_code, url)
                    return {'success': False, 'status_code': response.status_code,
                            'data': f"HTTP {response.status_code} al descargar {url}"}

                total = int(response.headers.get('content-length', 0)) or total_estimado
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
                            progreso_actual = min(tope_progreso, int(descargado / total * tope_progreso))
                            if progreso_actual != ultimo_avance:
                                ultimo_avance = progreso_actual
                                progress_callback(progreso_actual)

            return {'success': True, 'data': dest_path}
        except Exception as e:
            logger.error("Fallo al descargar %s", url, exc_info=True)
            return {'success': False, 'data': str(e)}

    def ensure_dir(self, directory):
        """Utilidad para crear directorios si no existen."""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
