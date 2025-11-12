import json, google_currency, threading, asyncio, wx, traceback
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, DisconnectEvent, ConnectEvent, LikeEvent, JoinEvent, FollowEvent, ShareEvent, RoomUserSeqEvent, EnvelopeEvent, EmoteChatEvent,LiveEndEvent
from globals import data_store
from globals.resources import rutasonidos
from utils import translator,funciones
from setup import player,reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager

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
        if data_store.config['categorias'][2]: self.chat.add_listener(EmoteChatEvent, self.on_emote)
        if data_store.config['categorias'][1]: self.chat.add_listener(EnvelopeEvent, self.on_chest)
        if data_store.config['categorias'][1]: self.chat.add_listener(FollowEvent, self.on_follow)
        if data_store.config['categorias'][3]: self.chat.add_listener(GiftEvent, self.on_gift)
        if data_store.config['categorias'][1]: self.chat.add_listener(JoinEvent, self.on_join)
        if data_store.config['categorias'][1]: self.chat.add_listener(LikeEvent, self.on_like)
        if data_store.config['categorias'][1]: self.chat.add_listener(ShareEvent, self.on_share)
        self.chat.add_listener(RoomUserSeqEvent, self.on_view)

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
        if data_store.config['eventos'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
            wx.CallAfter(self.estadisticas_manager.agregar_mensaje, event.user.nickname)
            cadena = event.comment if event.comment is not None else ''
            if data_store.dst: cadena = self.translator.translate(text=cadena, target=data_store.dst)
            wx.CallAfter(self.chat_controller.agregar_mensaje_general, event.user.nickname + ": " + cadena)
            if data_store.config['sonidos'] and data_store.config['listasonidos'][0]:
                wx.CallAfter(player.play, rutasonidos[0])
            if data_store.config['reader'] and data_store.config['unread'][0]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + ": " + cadena)

    async def on_emote(self,event: EmoteChatEvent):
        if data_store.config['eventos'][1] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
            wx.CallAfter(self.estadisticas_manager.agregar_mensaje, event.user.nickname)
            wx.CallAfter(self.chat_controller.agregar_mensaje_miembro, event.user.nickname + _(" envió un emogi."))
            if data_store.config['sonidos'] and data_store.config['listasonidos'][1]:
                wx.CallAfter(player.play, rutasonidos[1])
            if data_store.config['reader'] and data_store.config['unread'][1]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" envió un emogi."))

    async def on_chest(self,event: EnvelopeEvent):
        if data_store.config['eventos'][9] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, event.user.nickname + _(" ha enviado un cofre!"), "chest")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][12]:
                wx.CallAfter(player.play, rutasonidos[12])
            if data_store.config['reader'] and data_store.config['unread'][9]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" ha enviado un cofre!"))

    async def on_follow(self,event: FollowEvent):
        if data_store.config['eventos'][7] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.estadisticas_manager.agregar_seguidor)
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, event.user.nickname + _(" comenzó a seguirte!"), "follow")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][10]:
                wx.CallAfter(player.play, rutasonidos[10])
            if data_store.config['reader'] and data_store.config['unread'][7]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" comenzó a seguirte!"))

    async def on_gift(self,event: GiftEvent):
        if data_store.config['eventos'][3] and hasattr(self.chat_controller.ui, 'list_box_donaciones'):
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
                wx.CallAfter(self.chat_controller.agregar_mensaje_donacion, mensajito)
                if data_store.config['sonidos'] and data_store.config['listasonidos'][3]:
                    wx.CallAfter(player.play, rutasonidos[3])
                if data_store.config['reader'] and data_store.config['unread'][3]:
                    wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_join(self,event: JoinEvent):
        if data_store.config['eventos'][2] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.estadisticas_manager.agregar_unido)
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, event.user.nickname+_(" se ha unido a tu en vivo."), "join")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][2]:
                wx.CallAfter(player.play, rutasonidos[2])
            if data_store.config['reader'] and data_store.config['unread'][2]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" se ha unido a tu en vivo."))

    async def on_like(self,event: LikeEvent):
        if data_store.config['eventos'][6] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.estadisticas_manager.actualizar_megusta, event.total)
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, event.user.nickname + _(" le ha dado me gusta a tu en vivo."), "like")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][9]:
                wx.CallAfter(player.play, rutasonidos[9])
            if data_store.config['reader'] and data_store.config['unread'][6]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" le ha dado me gusta a tu en vivo."))

    async def on_share(self,event: ShareEvent):
        if data_store.config['eventos'][8] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.estadisticas_manager.agregar_compartida)
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, event.user.nickname + _(" ha compartido tu en vivo!"), "share")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][11]:
                wx.CallAfter(player.play, rutasonidos[11])
            if data_store.config['reader'] and data_store.config['unread'][8]:
                wx.CallAfter(reader.leer_mensaje, event.user.nickname + _(" ha compartido tu en vivo!"))

    async def on_view(self,event: RoomUserSeqEvent):
        title = self.chat.unique_id+_(' en vivo, actualmente ')+str(event.m_total)+_(' viendo ahora')
        wx.CallAfter(self.chat_controller.agregar_titulo, title)
        wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, title)