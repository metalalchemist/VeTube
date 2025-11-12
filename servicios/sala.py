import wx
from helpers.timer import Timer
from helpers.playroom_helper import PlayroomHelper
from controller.chat_controller import ChatController
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager

class ServicioSala:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager
        self._detener = False

    def iniciar_chat(self):
        self._detener = False
        self.chat = PlayroomHelper()
        if data_store.dst: self.translator=translator.translatorWrapper()
        self._hilo = Timer(0.5, self.recibir)
        self._hilo.daemon = True
        self._hilo.start()
        player.play(rutasonidos[6])
        reader.leer_sapi(_("Ingresando al chat."))
        title = _("Chat de la sala de juegos")
        wx.CallAfter(self.chat_controller.agregar_titulo, title)
        wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, title)
    def detener(self):
        self._detener = True

    def recibir(self):
        self.chat.get_new_messages()
        for message in self.chat.new_messages:
            self.estadisticas_manager.agregar_mensaje(message['author'])
            if self._detener: break
            if message['message']==None: message['message']=''
            if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)
            if (message['type'] == 'private'):
                if data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                    if data_store.config['eventos'][1]:
                        self.chat_controller.agregar_mensaje_miembro(message['author'] +': ' +message['message'])
                        if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(message['author'] +': ' +message['message'])
                        if data_store.config['sonidos'] and data_store.config['listasonidos'][2]: player.play(rutasonidos[2])
            else:
                if data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                    if data_store.config['eventos'][0]:
                        self.chat_controller.agregar_mensaje_general(message['author'] +': ' +message['message'])
                        if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(message['author'] +': ' +message['message'])
                        if data_store.config['sonidos'] and data_store.config['listasonidos'][0]: player.play(rutasonidos[0])
