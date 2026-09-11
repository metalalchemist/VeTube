import json

from globals.paths import DATA_FILE

configuraciones = {
    "salir": True,
    "sistemaTTS": "auto",
    "voz": 0,
    # La voz de cada motor con puente propio, para que cambiar de motor no se
    # lleve por delante la voz elegida en el otro. Tienen que estar aquí: son
    # claves que Cancelar revierte, y sin valor por defecto la instantánea de
    # Ajustes las deja en None (ver CLAVES_EN_CALIENTE en ajustes_controller).
    "voz_piper": 0,
    "voz_kokoro": 0,
    "voz_edge": 0,
    # La voz SAPI 5 que lee el chat cuando la casilla «Usar voz sapi» está
    # marcada. Aparte por lo mismo que las otras tres: su lista no tiene nada
    # que ver con la del motor elegido, y sin clave propia marcar la casilla y
    # desmarcarla le cambiaba la voz al motor de debajo.
    "voz_sapi": 0,
    "tono": 0,
    "tono_onecore": 0,
    "volume": 100,
    "speed": 0,
    "sapi": True,
    "dispositivo": 1,
    "sonidos": True,
    "idioma": "system",
    "categorias": [True, True, True, True, False, False, False],
    "listasonidos": [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ],
    "eventos": [True, True, True, True, True, True, True, True, True, True],
    "unread": [True, True, True, True, True, True, True, True, True, True],
    "reader": True,
    "donations": True,
    "updates": True,
    "traducir": False,
    "directorio": "default",
    "reproducir": False,
    "tiempo": 10,
    "volumen": 100,
    "cambiovolumen": 10,
    "interface": False,
    "discord_token": "",
    "leer_historial": True,
    "update_channel": "stable",
    "create_backup_before_update": True,
    # Firmador local del chat de TikTok: en vez de pedirle la firma a un
    # servicio externo, VeTube lee las tramas que el navegador del usuario ya
    # está recibiendo en el directo abierto. Apagado de fábrica porque hace
    # falta la extensión puesta en el navegador para que llegue algo.
    "tiktok_firmador_local": False,
}
actualizar_configuracion = False


def escribirConfiguracion():
    global configuraciones
    with open(DATA_FILE, "w+") as file:
        json.dump(configuraciones, file, indent=4)


def guardarConfiguracion(configs):
    """Guarda en data.json la configuración actual (no los valores por defecto)."""
    with open(DATA_FILE, "w+", encoding="utf-8") as file:
        json.dump(configs, file, indent=4, ensure_ascii=False)


def leerConfiguracion():
    global configuraciones, actualizar_configuracion
    with open(DATA_FILE) as file:
        configs = json.load(file)
    for clave, valor_pred in configuraciones.items():
        if clave not in configs:
            configs[clave] = valor_pred
            actualizar_configuracion = True
        elif (
            isinstance(valor_pred, list)
            and isinstance(configs[clave], list)
            and len(configs[clave]) < len(valor_pred)
        ):
            # Completar listas que crecieron en versiones nuevas, conservando las preferencias existentes (evita IndexError)
            configs[clave] = configs[clave] + valor_pred[len(configs[clave]) :]
            actualizar_configuracion = True
    # La casilla «Usar voz sapi» no se migra: el valor de fábrica ya es el
    # comportamiento bueno. Marcada, el chat sale por la voz SAPI 5 y el
    # programa se lo queda el lector de pantalla, que es lo que hace falta
    # para moverse deprisa por la lista. Desmarcarla al actualizar dejaría a
    # quien eligió piper, kokoro o edge con la navegación leída por su motor,
    # justo lo contrario de lo que se busca.
    # actualizar al archivo en caso de ser necesario:
    if actualizar_configuracion:
        with open(DATA_FILE, "w+") as file:
            json.dump(configs, file, indent=4)
    return configs
