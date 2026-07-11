from googletrans import LANGUAGES
from utils.languageHandler import getAvailableLanguages
from exchange.codes import CODES
from TTS.list_voices import piper_list_voices
from setup import reader
from os import path, getcwd, listdir
from globals.data_store import config
nombres_sonidos = [
    "chat.mp3",
    "chatmiembro.mp3",
    "miembros.mp3",
    "donar.mp3",
    "moderators.mp3",
    "verified.mp3",
    "abrirchat.mp3",
    "propietario.mp3",
    "buscar.mp3",
    "like.mp3",
    "seguirte.mp3",
    "share.mp3",
    "chest.mp3"
]
# msj.mp3, orilla.mp3 y cambiardispositivo.mp3 no están en la lista: se reproducen directamente
sonidos_requeridos = nombres_sonidos + ["msj.mp3", "orilla.mp3", "cambiardispositivo.mp3"]
rutasonidos = []

def listar_temas_sonidos():
    if not path.isdir("sounds"):
        return []
    return sorted(
        d for d in listdir("sounds")
        if all(path.isfile(path.join("sounds", d, nombre)) for nombre in sonidos_requeridos)
    )

def recargar_rutasonidos():
    # Mutación in place: los módulos que importaron rutasonidos ven el cambio sin reiniciar
    rutasonidos[:] = [f"sounds/{config['directorio']}/{nombre}" for nombre in nombres_sonidos]

recargar_rutasonidos()
idiomas = getAvailableLanguages()
langs = [i[1] for i in idiomas][::-1]
codes = [i[0] for i in idiomas][::-1]
idiomas_disponibles = [""] + [v for v in LANGUAGES.values()]
codigos_traduccion = [""] + [k for k in LANGUAGES.keys()]  # mismo orden que idiomas_disponibles: los índices deben coincidir
monedas = [_('Por defecto')] + [f'{CODES[k]}, ({k})' for k in CODES]
voces_p = piper_list_voices()
if not voces_p:
	lista_voces_piper = [_("No hay voces instaladas")]
else:
	lista_voces_piper = voces_p
lista_voces=reader._leer.list_voices()
carpeta_voces = path.join(getcwd(), "voices")