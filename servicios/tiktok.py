from __future__ import annotations

import json, google_currency, threading, asyncio, wx, traceback
from typing import TYPE_CHECKING
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.types.events import CommentEvent, GiftEvent, DisconnectEvent, ConnectEvent, LikeEvent, JoinEvent, FollowEvent, ShareEvent, ViewerUpdateEvent, EnvelopeEvent, EmoteEvent, LiveEndEvent
from globals import data_store
from globals.resources import rutasonidos
from utils import translator,funciones
from setup import player,reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager
from servicios.message_router import MessageRouter, RoutableMessage

if TYPE_CHECKING:
    from servicios.chat_service_protocol import ChatService


class ServicioTiktok:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager
        self.is_running = False
        self.last_live_status = None
        self.loop = None
        self.media_controller = None
        self.router = MessageRouter(chat_controller)

    def iniciar_chat(self):
        self.is_running = True
        thread = threading.Thread(target=self._start_async_loop, daemon=True)
        thread.start()

    def _start_async_loop(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.create_task(self._initialize_and_run_client())
            self.loop.run_forever()
        except Exception as e:
            print(f"Error fatal en el hilo de conexión: {e}")
            traceback.print_exc()
        finally:
            if self.loop.is_running():
                pending = asyncio.all_tasks(loop=self.loop)
                for task in pending:
                    task.cancel()
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def _initialize_and_run_client(self):
        try:
            user_id = funciones.extractUser(self.url)
            self.chat = TikTokLiveClient(unique_id=user_id)
            self._add_listeners()
            await self._run_client_async()
        except Exception as e:
            print(f"Error during client initialization: {e}")
            traceback.print_exc()
            wx.CallAfter(self.chat_controller.notificar_error, str(e))
            self.detener()

    async def _run_client_async(self):
        while self.is_running:
            try:
                is_live_now = await self.chat.is_live()
                if is_live_now:
                    if self.last_live_status is not True:
                        wx.CallAfter(reader.leer_sapi, _("El usuario está en vivo. Conectando..."))
                    self.last_live_status = True
                    if data_store.dst: self.translator = translator.TranslatorWrapper()
                    await self.chat.connect()
                else:
                    if self.last_live_status is not False:
                        wx.CallAfter(reader.leer_sapi, _("El usuario no está en vivo. Reintentando en un minuto."))
                    self.last_live_status = False
                    if self.is_running: await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.is_running:
                    print(f"Error en el bucle del cliente: {e}.")
                    traceback.print_exc()
                    wx.CallAfter(self.chat_controller.notificar_error, str(e))
                    self.detener()

    def detener(self):
        if self.media_controller:
            self.media_controller.release()
        if self.is_running and self.loop and self.loop.is_running():
            self.is_running = False
            asyncio.run_coroutine_threadsafe(self.chat.disconnect(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

    def prepare_player(self):
        try:
            from utils.play_mp4 import extract_stream_url
            video_url = extract_stream_url(self.url, format_preference='best')
            if video_url:
                from controller.media_controller import MediaController
                self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error al iniciar la reproducción de video en TikTok: {e}")

    def _add_listeners(self):
        self.chat.add_listener(ConnectEvent, self.on_connect)
        if data_store.config['categorias'][0]: self.chat.add_listener(CommentEvent, self.on_comment)
        self.chat.add_listener(LiveEndEvent, self.finalizado)
        self.chat.add_listener(DisconnectEvent, self.on_disconnect)
        if data_store.config['categorias'][2]: self.chat.add_listener(EmoteEvent, self.on_emote)
        if data_store.config['categorias'][1]: self.chat.add_listener(EnvelopeEvent, self.on_chest)
        if data_store.config['categorias'][1]: self.chat.add_listener(FollowEvent, self.on_follow)
        if data_store.config['categorias'][3]: self.chat.add_listener(GiftEvent, self.on_gift)
        if data_store.config['categorias'][1]: self.chat.add_listener(JoinEvent, self.on_join)
        if data_store.config['categorias'][1]: self.chat.add_listener(LikeEvent, self.on_like)
        if data_store.config['categorias'][1]: self.chat.add_listener(ShareEvent, self.on_share)
        self.chat.add_listener(ViewerUpdateEvent, self.on_view)

    async def finalizado(self, event: LiveEndEvent):
        self.last_live_status = False
        wx.CallAfter(reader.leer_sapi, _("El directo ha finalizado. Se buscará de nuevo en un minuto."))

    async def on_disconnect(self, event: DisconnectEvent):
        if self.is_running:
            self.is_running = False
            wx.CallAfter(reader.leer_sapi, _("Se ha perdido la conexión. El servicio se ha detenido."))

    async def on_connect(self,event: ConnectEvent):
        self.last_live_status = True
        wx.CallAfter(reader.leer_sapi, _("Ingresando al chat"))
        if not self.media_controller:
            threading.Thread(target=self.prepare_player, daemon=True).start()
        if data_store.config['sonidos'] and data_store.config['listasonidos'][6]:
            wx.CallAfter(player.play, rutasonidos[6])

    async def on_comment(self,event: CommentEvent):
        wx.CallAfter(self.estadisticas_manager.agregar_mensaje, event.user.nickname)
        cadena = event.comment if event.comment is not None else ''
        if data_store.dst: cadena = self.translator.translate(text=cadena, target=data_store.dst)
        msg = RoutableMessage(
            text=cadena,
            author=event.user.nickname,
            category='general',
            platform='tiktok'
        )
        self.router.route(msg)

    async def on_emote(self,event: EmoteEvent):
        wx.CallAfter(self.estadisticas_manager.agregar_mensaje, event.user.nickname)
        msg = RoutableMessage(
            text=_(" envió un emogi."),
            author=event.user.nickname,
            category='member',
            event_type='emote',
            platform='tiktok'
        )
        self.router.route(msg)

    async def on_chest(self,event: EnvelopeEvent):
        msg = RoutableMessage(
            text=_(" ha enviado un cofre!"),
            author=event.user.nickname,
            category='event',
            event_type='chest',
            platform='tiktok',
            eventos_index=9,
            sound_index=12
        )
        self.router.route(msg)

    async def on_follow(self,event: FollowEvent):
        wx.CallAfter(self.estadisticas_manager.agregar_seguidor)
        msg = RoutableMessage(
            text=_(" comenzó a seguirte!"),
            author=event.user.nickname,
            category='event',
            event_type='follow',
            platform='tiktok',
            eventos_index=7,
            sound_index=10
        )
        self.router.route(msg)

    async def on_gift(self,event: GiftEvent):
        mensajito = ""
        if event.gift.streakable and not event.streaking:
            if data_store.divisa!="Por defecto":
                if data_store.divisa=='USD': total=float((event.gift.diamond_count*event.repeat_count)/100)
                else:
                    moneda = json.loads(google_currency.convert('USD', data_store.divisa, int((event.gift.diamond_count * event.repeat_count) / 100)))
                    if moneda['converted']: total=moneda['amount']
                mensajito=_('%s ha enviado %s %s (%s %s)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(total),data_store.divisa)
            else: mensajito=_('%s ha enviado %s %s (%s diamante)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(event.gift.diamond_count))
        elif not event.gift.streakable:
            if data_store.divisa!="Por defecto":
                if data_store.divisa=='USD': total=int((event.gift.diamond_count*event.repeat_count)/100)
                else:
                    moneda = json.loads(google_currency.convert('USD', data_store.divisa, int((event.gift.diamond_count * event.repeat_count) / 100)))
                    if moneda['converted']: total=moneda['amount']
                mensajito=_('%s ha enviado %s %s (%s %s)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(total),data_store.divisa)
            else: mensajito=_('%s ha enviado %s %s (%s diamante)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(event.gift.diamond_count))
        
        if mensajito:
            msg = RoutableMessage(
                text=mensajito,
                author='',
                category='donation',
                platform='tiktok'
            )
            self.router.route(msg)

    async def on_join(self,event: JoinEvent):
        wx.CallAfter(self.estadisticas_manager.agregar_unido)
        msg = RoutableMessage(
            text=_(" se ha unido a tu en vivo."),
            author=event.user.nickname,
            category='event',
            event_type='join',
            platform='tiktok',
            eventos_index=2,
            sound_index=2
        )
        self.router.route(msg)

    async def on_like(self,event: LikeEvent):
        wx.CallAfter(self.estadisticas_manager.actualizar_megusta, event.total)
        msg = RoutableMessage(
            text=_(" le ha dado me gusta a tu en vivo."),
            author=event.user.nickname,
            category='event',
            event_type='like',
            platform='tiktok',
            eventos_index=6,
            sound_index=9
        )
        self.router.route(msg)

    async def on_share(self,event: ShareEvent):
        wx.CallAfter(self.estadisticas_manager.agregar_compartida)
        msg = RoutableMessage(
            text=_(" ha compartido tu en vivo!"),
            author=event.user.nickname,
            category='event',
            event_type='share',
            platform='tiktok',
            eventos_index=8,
            sound_index=11
        )
        self.router.route(msg)

    async def on_view(self,event: ViewerUpdateEvent):
        title = self.chat.unique_id+_(' en vivo, actualmente ')+str(getattr(event, 'viewer_count', 0))+_(' viendo ahora')
        wx.CallAfter(self.chat_controller.agregar_titulo, title)
        wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, title)