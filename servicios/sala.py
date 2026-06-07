from __future__ import annotations

import wx
from typing import TYPE_CHECKING
from helpers.timer import Timer
from helpers.playroom_helper import PlayroomHelper
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager
from servicios.message_router import MessageRouter, RoutableMessage

if TYPE_CHECKING:
    from servicios.chat_service_protocol import ChatService


class ServicioSala:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager
        self.media_controller = None
        self._detener = False
        self.router = MessageRouter(chat_controller)

    def iniciar_chat(self):
        try:
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
        except Exception as e:
            wx.CallAfter(self.chat_controller.notificar_error, str(e))

    def detener(self):
        self._detener = True

    def recibir(self):
        try:
            self.chat.get_new_messages()
            for message in self.chat.new_messages:
                self.estadisticas_manager.agregar_mensaje(message['author'])
                if self._detener: break
                if message['message']==None: message['message']=''
                if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)
                if (message['type'] == 'private'):
                    msg = RoutableMessage(
                        text=message['message'],
                        author=message['author'],
                        category='member',
                        platform='sala',
                        sound_index=2
                    )
                    self.router.route(msg)
                else:
                    msg = RoutableMessage(
                        text=message['message'],
                        author=message['author'],
                        category='general',
                        platform='sala'
                    )
                    self.router.route(msg)
        except Exception as e:
            wx.CallAfter(self.chat_controller.notificar_error, str(e))
