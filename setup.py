from utils import languageHandler
from globals.data_store import config
from players.sound_helper import SoundPlayer
from helpers.reader_handler import ReaderHandler
languageHandler.setLanguage(config['idioma'])
player=SoundPlayer()
reader = ReaderHandler()
reader._leer.set_rate(config['speed'])
reader._leer.set_pitch(config['tono'])
reader._leer.set_volume(config['volume'])
voices_leer = reader._leer.list_voices()
if voices_leer:
    idx = config['voz']
    if idx >= len(voices_leer): idx = 0
    reader._leer.set_voice(voices_leer[idx])

# Configurar también el lector principal de chat si no es Piper
if config['sistemaTTS'] != "piper":
    reader._lector.set_rate(config['speed'])
    if config['sistemaTTS'] == "onecore":
        reader._lector.set_pitch(config.get('tono_onecore', 0))
    else:
        reader._lector.set_pitch(config['tono'])
    reader._lector.set_volume(config['volume'])
    voices_lector = reader._lector.list_voices()
    if voices_lector:
        idx = config['voz']
        if idx >= len(voices_lector): idx = 0
        reader._lector.set_voice(voices_lector[idx])
from utils.network import network_manager as network