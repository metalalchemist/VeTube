from googletrans import LANGUAGES
from utils.languageHandler import getAvailableLanguages
from google_currency import CODES
from TTS.list_voices import piper_list_voices
from setup import reader
from os import path, getcwd
from globals.data_store import config
rutasonidos = [
    f"sounds/{config['directorio']}/chat.mp3",
    f"sounds/{config['directorio']}/chatmiembro.mp3",
    f"sounds/{config['directorio']}/miembros.mp3",
    f"sounds/{config['directorio']}/donar.mp3",
    f"sounds/{config['directorio']}/moderators.mp3",
    f"sounds/{config['directorio']}/verified.mp3",
    f"sounds/{config['directorio']}/abrirchat.wav",
    f"sounds/{config['directorio']}/propietario.mp3",
    f"sounds/{config['directorio']}/buscar.wav",
    f"sounds/{config['directorio']}/like.wav",
    f"sounds/{config['directorio']}/seguirte.mp3",
    f"sounds/{config['directorio']}/share.mp3",
    f"sounds/{config['directorio']}/chest.mp3"
]
idiomas = getAvailableLanguages()
langs = [i[1] for i in idiomas][::-1]
codes = [i[0] for i in idiomas][::-1]
idiomas_disponibles = [""] + [v for v in LANGUAGES.values()]
monedas = [_('Por defecto')] + [f'{CODES[k]}, ({k})' for k in CODES]
if piper_list_voices() is None:
	lista_voces_piper=[_("No hay voces instaladas")]
else:
	lista_voces_piper=piper_list_voices()
lista_voces=reader._leer.list_voices()
carpeta_voces = path.join(getcwd(), "piper", "voices")