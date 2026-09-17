from globals.paths import DATA_FILE, FAVORITOS_FILE, MENSAJES_DESTACADOS_FILE
from utils import fajustes, funciones

# Inicialización global de configuración
if DATA_FILE.exists():
    config = fajustes.leerConfiguracion()
else:
    fajustes.escribirConfiguracion()
    config = fajustes.leerConfiguracion()

# Inicialización global de favoritos y mensajes destacados
favorite = funciones.leerJsonLista(FAVORITOS_FILE)
mensajes_destacados = funciones.leerJsonLista(MENSAJES_DESTACADOS_FILE)
favs = funciones.convertirLista(favorite, "titulo", "url")
msjs = funciones.convertirLista(mensajes_destacados, "mensaje", "titulo")


def motor_de_interfaz(ajustes=None):
    """El motor que lee el programa, que no siempre es config['sistemaTTS'].

    La casilla «Usar voz sapi» aparta el motor elegido: marcada, el chat sale
    por la voz SAPI 5 secundaria y el programa vuelve a leerlo el lector de
    pantalla, que es lo que significa «auto». Así la casilla se basta sola —
    marcarla no obliga a ir antes a la lista a elegir «auto»— y config
    ['sistemaTTS'] guarda mientras tanto el motor al que volver al desmarcarla.

    Quien pregunte qué motor habla, qué modelo cargar o qué enseñar en los
    Ajustes tiene que preguntar aquí; config['sistemaTTS'] a secas solo vale
    para saber qué eligió el usuario en la lista.

    Con `ajustes` se pregunta por otra foto de la configuración en vez de por
    la de ahora: lo usa Cancelar en los Ajustes, que compara el motor que habla
    con el que había al abrir el diálogo. Así la regla vive en un solo sitio.
    """
    if ajustes is None:
        ajustes = config
    return "auto" if ajustes.get("sapi") else ajustes["sistemaTTS"]


divisa = "Por defecto"
# La traducción de mensajes no es persistente: arranca desactivada en cada sesión (se ajusta desde el diálogo)
dst = ""
