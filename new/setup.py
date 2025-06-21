from utils import languageHandler
from globals.data_store import config
from helpers.sound_helper import playsound
from helpers.reader_handler import ReaderHandler
languageHandler.setLanguage(config['idioma'])
player=playsound()
reader = ReaderHandler()