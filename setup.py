from utils import languageHandler
from globals.data_store import config
from helpers.sound_helper import playsound
from helpers.reader_handler import ReaderHandler
languageHandler.setLanguage(config['idioma'])
player=playsound()
reader = ReaderHandler()
reader._leer.set_rate(config['speed'])
reader._leer.set_pitch(config['tono'])
reader._leer.set_voice(reader._leer.list_voices()[config['voz']])
reader._leer.set_volume(config['volume'])