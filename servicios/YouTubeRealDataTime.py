from __future__ import annotations

import pytchat, wx, json, threading, google_currency
from typing import TYPE_CHECKING
from utils.play_mp4 import extract_stream_url
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player, reader
from controller.chat_controller import ChatController
from controller.media_controller import MediaController
from servicios.estadisticas_manager import EstadisticasManager
from servicios.message_router import MessageRouter, RoutableMessage

if TYPE_CHECKING:
    from servicios.chat_service_protocol import ChatService


class YouTubeRealTimeService:
    def __init__(self, url, frame, plataforma, title=None, chat_controller=None):
        self.url = url
        self.frame = frame
        self.title = title
        self.chat = None
        self.media_controller = None
        if chat_controller:
            self.chat_controller = chat_controller
            self.chat_controller.servicio = self
        else:
            # If no chat_controller is provided, create a new one with its own EstadisticasManager
            self.chat_controller = ChatController(None, frame, self, plataforma) # main_controller is None here, will be set by ChatController.servicio
        self.estadisticas_manager = self.chat_controller.estadisticas_manager
        self._detener = False
        self.router = MessageRouter(self.chat_controller)

    def iniciar_chat_reutilizando_ui(self):
        self._detener = False
        threading.Thread(target=self.prepare, daemon=True).start()
        self._hilo = threading.Thread(target=self.recibir, daemon=True)
        self._hilo.start()
        wx.CallAfter(reader.leer_sapi, "Cambiando a servicio de tiempo real.")

    def detener(self):
        if self.chat:
            self.chat.terminate()
        if self.media_controller:
            self.media_controller.release()
        self._detener = True

    def prepare(self):
        video_url = extract_stream_url(self.url, format_preference='mp4')
        if video_url:
            self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
            self.chat_controller.set_media_controller(self.media_controller)
            print(video_url)
    def recibir(self):
        if data_store.dst:
            self.translator = translator.translatorWrapper()
        try:
            self.chat = pytchat.create(video_id=self.url, interruptable=False)
            display_title = self.title + " (En tiempo real)"
            wx.CallAfter(self.chat_controller.agregar_titulo, display_title)
            wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, display_title)

            while self.chat.is_alive() and not self._detener:
                for c in self.chat.get().sync_items():
                    if self._detener: break
                    author_name = c.author.name
                    msg = c.message
                    self.estadisticas_manager.agregar_mensaje(author_name)
                    if data_store.dst: msg = self.translator.translate(text=msg, target=data_store.dst)
                    message_type = 'general'
                    if c.author.isChatOwner: message_type = 'propietario'
                    elif c.author.isChatModerator: message_type = 'moderador'
                    elif c.author.isChatSponsor: message_type = 'miembro'
                    elif c.author.isVerified: message_type = 'verificado'
                    if c.type == "superChat" or c.type == "superSticker": message_type = 'donacion'

                    if message_type == 'donacion':
                        amount = c.amountString
                        currency = c.currency
                        if data_store.divisa != "Por defecto" and data_store.divisa != currency:
                            converted = json.loads(google_currency.convert(currency, data_store.divisa, c.amountValue))
                            if converted['converted']:
                                currency = data_store.divisa
                                amount = converted['amount']
                        
                        full_message = f"{amount} {currency}, {author_name}: {msg}"
                        donacion_msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='donation',
                            platform='youtube_realtime'
                        )
                        self.router.route(donacion_msg)
                        continue

                    full_message = f"{author_name}: {msg}"

                    if message_type == 'general':
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='general',
                            platform='youtube_realtime'
                        )
                        self.router.route(msg)
                    elif message_type == 'miembro':
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='member',
                            platform='youtube_realtime'
                        )
                        self.router.route(msg)
                    elif message_type == 'moderador' or message_type == 'propietario':
                        sound_idx = 7 if message_type == 'propietario' else 4
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='moderator',
                            platform='youtube_realtime',
                            sound_index=sound_idx
                        )
                        self.router.route(msg)
                    elif message_type == 'verificado':
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='verified',
                            platform='youtube_realtime'
                        )
                        self.router.route(msg)
        except Exception as e:
            wx.CallAfter(self.chat_controller.notificar_error, str(e))
        finally:
            if self.chat: self.chat.terminate()
