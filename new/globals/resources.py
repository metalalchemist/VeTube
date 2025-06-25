from googletrans import LANGUAGES
from utils.languageHandler import getAvailableLanguages
from google_currency import CODES
from TTS.list_voices import piper_list_voices
from setup import reader
from os import path, getcwd
rutasonidos = [
    "sounds/chat.mp3",
    "sounds/chatmiembro.mp3",
    "sounds/miembros.mp3",
    "sounds/donar.mp3",
    "sounds/moderators.mp3",
    "sounds/verified.mp3",
    "sounds/abrirchat.wav",
    "sounds/propietario.mp3",
    "sounds/buscar.wav",
    "sounds/like.wav",
    "sounds/seguirte.mp3",
    "sounds/share.mp3",
    "sounds/chest.mp3"
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