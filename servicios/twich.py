from __future__ import annotations

import json, google_currency,threading,re,wx
from typing import TYPE_CHECKING
from chat_downloader import ChatDownloader
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from utils.play_mp4 import extract_stream_url
from setup import player,reader
from controller.chat_controller import ChatController
from controller.media_controller import MediaController
from servicios.estadisticas_manager import EstadisticasManager
from servicios.message_router import MessageRouter, RoutableMessage

if TYPE_CHECKING:
    from servicios.chat_service_protocol import ChatService


class ServicioTwich:
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
        self._detener = False
        self._hilo = threading.Thread(target=self.recibir, daemon=True)
        self._hilo.start()
        player.play(rutasonidos[6])
        reader.leer_sapi(_("Ingresando al chat."))

    def detener(self):
        self._detener = True
        if self.media_controller:
            self.media_controller.release()

    def prepare_player(self, status):
        try:
            format_pref = 'mp4' if status == "past" else 'best'
            video_url = extract_stream_url(self.url, format_preference=format_pref)
            if video_url:
                self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error al iniciar la reproducción de video en Twitch: {e}")

    def recibir(self):
        try:
            if data_store.dst: self.translator=translator.translatorWrapper()
            self.chat=ChatDownloader().get_chat(self.url,message_groups=["messages", "bits","subscriptions","upgrades"])
            threading.Thread(target=self.prepare_player, args=(self.chat.status,), daemon=True).start()
            wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, self.chat.title)
            for message in self.chat:
                if self._detener: break
                if not message: continue

                if message['message'] is None: message['message'] = ''
                if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)

                author_name = message['author'].get('display_name', _('Desconocido'))
                self.estadisticas_manager.agregar_mensaje(author_name)
                msg = message['message']
                full_message = f"{author_name}: {msg}"

                # Subscription events
                if message['message_type'] in ['resubscription', 'subscription', 'mystery_subscription_gift', 'subscription_gift']:
                    sub_message = ""
                    if message['message_type'] == 'resubscription' and data_store.config['eventos'][2]:
                        sub_message = _("{author_name} ha renovado su suscripción en el nivel {subscription_plan_name}. ¡Lleva suscrito por {cumulative_months} meses!").format(author_name=author_name, subscription_plan_name=message.get('subscription_plan_name', ''), cumulative_months=message.get('cumulative_months', ''))
                        if message.get('message'):
                            mssg=message['message'].split('! ')
                            mssg=str(mssg[1:])
                            sub_message +=f": {mssg}"
                    elif message['message_type'] == 'subscription' and data_store.config['eventos'][2]: sub_message = _("{author_name} se ha suscrito en el nivel {subscription_plan_name} por {cumulative_months} meses!").format(author_name=author_name, subscription_plan_name=message.get('subscription_plan_name', ''), cumulative_months=message.get('cumulative_months', ''))
                    elif message['message_type'] == 'mystery_subscription_gift' and data_store.config['eventos'][2]: sub_message = _("{author_name} regaló una suscripción de nivel {subscription_type} a la comunidad, ¡ha regalado un total de {sender_count} suscripciones!").format(author_name=author_name, subscription_type=message.get('subscription_type', ''), sender_count=message.get('sender_count', ''))
                    elif message['message_type'] == 'subscription_gift' and data_store.config['eventos'][2]: sub_message = _("{author_name} ha regalado una suscripción a {gift_recipient_display_name} en el nivel {subscription_plan_name} por {number_of_months_gifted} meses!").format(author_name=author_name, gift_recipient_display_name=message.get('gift_recipient_display_name', ''), subscription_plan_name=message.get('subscription_plan_name', ''), number_of_months_gifted=message.get('number_of_months_gifted', ''))
                    if sub_message:
                        msg = RoutableMessage(
                            text=sub_message,
                            author='',
                            category='event',
                            event_type='subscribe',
                            platform='twitch',
                            is_past=(self.chat.status == 'past'),
                            eventos_index=2,
                            sound_index=2
                        )
                        self.router.route(msg)
                    continue

                # Cheer/Bits event
                if re.search(r'\bCheer\d+\b', msg):
                    divide1=message['message'].split('Cheer')
                    if not divide1[0]:
                        if data_store.divisa!=_('Por defecto'): divide1[0]=data_store.divisa
                        else: divide1[0]='Cheer'
                        final_msj=divide1[1].split()
                        if data_store.divisa!=_('Por defecto'):
                            if data_store.divisa=='USD':final_msj[0]=int(final_msj[0])/100
                            else:
                                moneda=json.loads(google_currency.convert('USD',data_store.divisa,int(final_msj[0])/100) )
                                if moneda['converted']: final_msj[0]=moneda['amount']
                        dinero=divide1[0]+str(final_msj[0])
                        if len(final_msj)==1: divide1=''
                        else: divide1=' '.join(final_msj[1:])
                    else:
                        if data_store.divisa!=_('Por defecto'):
                            if data_store.divisa=='USD': divide1[1]=int(divide1[1])/100
                            else:
                                moneda=json.loads(google_currency.convert('USD',data_store.divisa,int(divide1[1])/100) )
                                if moneda['converted']: divide1[1]=moneda['amount']
                        if data_store.divisa!=_('Por defecto'): dinero=data_store.divisa+str(divide1[1])
                        else: dinero='Cheer '+str(divide1[1])
                        divide1=' '+divide1[0]
                    cheer_msg = RoutableMessage(
                        text=dinero+', '+author_name+': '+divide1,
                        author='',
                        category='donation',
                        platform='twitch',
                        is_past=(self.chat.status == 'past')
                    )
                    self.router.route(cheer_msg)
                    continue

                # Regular messages with badges/roles
                message_sent = False
                try:
                    if message['author'].get('is_moderator'):
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='moderator',
                            platform='twitch',
                            is_past=(self.chat.status == 'past')
                        )
                        self.router.route(msg)
                        message_sent = True
                    elif message['author'].get('is_subscriber'):
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='member',
                            platform='twitch',
                            is_past=(self.chat.status == 'past')
                        )
                        self.router.route(msg)
                        message_sent = True
                except KeyError: pass
                if message_sent: continue
                if 'badges' in message['author']:
                    for badge in message['author']['badges']:
                        title = badge.get('title', '')
                        if 'Subscriber' in title:
                            msg = RoutableMessage(
                                text=full_message,
                                author='',
                                category='member',
                                platform='twitch',
                                is_past=(self.chat.status == 'past')
                            )
                            self.router.route(msg)
                            message_sent = True
                            break
                        elif 'Moderator' in title:
                            msg = RoutableMessage(
                                text=full_message,
                                author='',
                                category='moderator',
                                platform='twitch',
                                is_past=(self.chat.status == 'past')
                            )
                            self.router.route(msg)
                            message_sent = True
                            break
                        elif 'Verified' in title:
                            msg = RoutableMessage(
                                text=full_message,
                                author='',
                                category='verified',
                                platform='twitch',
                                is_past=(self.chat.status == 'past')
                            )
                            self.router.route(msg)
                            message_sent = True
                            break
                    else:
                        msg = RoutableMessage(
                            text=full_message,
                            author='',
                            category='general',
                            platform='twitch',
                            is_past=(self.chat.status == 'past')
                        )
                        self.router.route(msg)
                        message_sent = True
                if message_sent: continue
                # Default to general
                msg = RoutableMessage(
                    text=full_message,
                    author='',
                    category='general',
                    platform='twitch',
                    is_past=(self.chat.status == 'past')
                )
                self.router.route(msg)
        except Exception as e:
            wx.CallAfter(self.chat_controller.notificar_error, str(e))

