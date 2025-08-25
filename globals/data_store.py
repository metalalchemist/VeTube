import os
from utils import fajustes, funciones

# Inicialización global de configuración
if os.path.exists('data.json'):
    config = fajustes.leerConfiguracion()
else:
    fajustes.escribirConfiguracion()
    config = fajustes.leerConfiguracion()

# Inicialización global de favoritos y mensajes destacados
favorite = funciones.leerJsonLista('favoritos.json')
mensajes_destacados = funciones.leerJsonLista('mensajes_destacados.json')
favs = funciones.convertirLista(favorite, 'titulo', 'url')
msjs = funciones.convertirLista(mensajes_destacados, 'mensaje', 'titulo')
divisa="Por defecto"
dst=""
