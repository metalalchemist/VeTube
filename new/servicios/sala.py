from helpers.timer import Timer
from helpers.playroom_helper import PlayroomHelper
from controller.chat_controller import ChatController
from globals.data_store import config, dst
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController

class ServicioSala:
    def __init__(self, url, frame, plataforma):
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = ChatController(frame, self, plataforma)
        self._detener = False

    def iniciar_chat(self):
        self._detener = False
        self.chat = PlayroomHelper()
        self._hilo = Timer(0.5, self.recibir)
        self._hilo.daemon = True
        self._hilo.start()
        player.playsound(rutasonidos[6], False)
        reader.leer_sapi(_("Ingresando al chat."))
        self.chat_controller.mostrar_dialogo()
    def detener(self):
        self._detener = True

    def recibir(self):
        if dst: translator=translator.TranslatorWrapper()
        self.chat.get_new_messages()
        for message in self.chat.new_messages:
            if self._detener: break
            if message['message']==None: message['message']=''
            if dst: message['message'] = translator.translate(text=message['message'], target=dst)
            if config['sonidos'] and config['listasonidos'][0]: player.playsound(rutasonidos[0],False)
            if (message['type'] == 'private'): self.chat_controller.agregar_mensaje(_('privado de ') + message['author'] +': ' +message['message'])
            else: self.chat_controller.agregar_mensaje(message['author'] +': ' +message['message'])
