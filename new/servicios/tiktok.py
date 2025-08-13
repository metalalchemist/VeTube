import json, google_currency, threading, asyncio
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, DisconnectEvent, ConnectEvent, LikeEvent, JoinEvent, FollowEvent, ShareEvent, RoomUserSeqEvent, EnvelopeEvent, EmoteChatEvent,LiveEndEvent
from globals.data_store import config, divisa, dst
from globals.resources import rutasonidos
from utils import translator,funciones
from setup import player,reader
from controller.chat_controller import ChatController

class ServicioTiktok:
    def __init__(self, url, frame, plataforma):
        self.url = url
        self.frame = frame
        self.chat_controller = ChatController(frame, self, plataforma)
        self.chat = None
        self.loop = None
        self.is_running = False
        self.last_live_status = None
        self.megusta=self.seguidores=self.unidos=self.compartidas=0
        self.gustados=[]

    def iniciar_chat(self):
        self.is_running = True
        thread = threading.Thread(target=self._start_async_loop, daemon=True)
        thread.start()
        self.chat_controller.mostrar_dialogo()

    def _start_async_loop(self):
        try:
            user_id = funciones.extractUser(self.url)
            self.chat = TikTokLiveClient(unique_id=user_id)
            self._add_listeners()
            asyncio.run(self._run_client_async())
        except Exception as e:
            print(f"Error fatal en el hilo de conexión: {e}")

    async def _run_client_async(self):
        self.loop = asyncio.get_running_loop()
        while self.is_running:
            try:
                is_live_now = await self.chat.is_live()
                if is_live_now:
                    if self.last_live_status is not True: reader.leer_sapi(_("El usuario está en vivo. Conectando..."))
                    self.last_live_status = True
                    await self.chat.connect()
                else:
                    if self.last_live_status is not False: reader.leer_sapi(_("El usuario no está en vivo. Reintentando en un minuto."))
                    self.last_live_status = False
                    if self.is_running: await asyncio.sleep(60)
            except Exception as e:
                if self.is_running:
                    print(f"Error en el bucle del cliente: {e}.")
                    self.detener()

    def detener(self):
        if self.is_running and self.loop:
            self.is_running = False
            asyncio.run_coroutine_threadsafe(self.chat.disconnect(), self.loop)
        self.loop = None
        self.chat = None

    def _add_listeners(self):
        self.chat.add_listener(ConnectEvent, self.on_connect)
        self.chat.add_listener(CommentEvent, self.on_comment)
        self.chat.add_listener(LiveEndEvent, self.finalizado)
        self.chat.add_listener(DisconnectEvent, self.on_disconnect)
        if config['eventos'][0]: self.chat.add_listener(EmoteChatEvent, self.on_emote)
        if config['eventos'][8]: self.chat.add_listener(EnvelopeEvent, self.on_chest)
        if config['eventos'][6]: self.chat.add_listener(FollowEvent, self.on_follow)
        if config['eventos'][2]: self.chat.add_listener(GiftEvent, self.on_gift)
        if config['eventos'][1]: self.chat.add_listener(JoinEvent, self.on_join)
        if config['eventos'][5]: self.chat.add_listener(LikeEvent, self.on_like)
        if config['eventos'][7]: self.chat.add_listener(ShareEvent, self.on_share)
        self.chat.add_listener(RoomUserSeqEvent, self.on_view)

    async def finalizado(self, event: LiveEndEvent):
        self.last_live_status = False
        reader.leer_sapi(_("El directo ha finalizado. Se buscará de nuevo en un minuto."))

    async def on_disconnect(self, event: DisconnectEvent):
        if self.is_running:
            self.is_running = False
            reader.leer_sapi(_("Se ha perdido la conexión. El servicio se ha detenido."))

    async def on_connect(self,event: ConnectEvent):
        self.last_live_status = True
        reader.leer_sapi(_("Ingresando al chat"))
        if config['sonidos'] and config['listasonidos'][6]: player.playsound(rutasonidos[6],False)

    async def on_comment(self,event: CommentEvent):
        self.chat_controller.agregar_mensaje_general(event.user.nickname + ": " + event.comment if event.comment is not None else '')
        if config['sonidos'] and config['listasonidos'][0]: player.playsound(rutasonidos[0],False)

    async def on_emote(self,event: EmoteChatEvent):
        self.chat_controller.agregar_mensaje_general(event.user.nickname + _(" envió un emogi."))
        if config['sonidos'] and config['listasonidos'][1]: player.playsound(rutasonidos[1],False)

    async def on_chest(self,event: EnvelopeEvent):
        self.chat_controller.agregar_mensaje_donacion(event.user.nickname + _(" ha enviado un cofre!"))
        if config['sonidos'] and config['listasonidos'][12]: player.playsound(rutasonidos[12],False)

    async def on_follow(self,event: FollowEvent):
        self.seguidores+=1
        self.chat_controller.agregar_mensaje_general(event.user.nickname + _(" comenzó a seguirte!"))
        if config['sonidos'] and config['listasonidos'][10]: player.playsound(rutasonidos[10],False)

    async def on_gift(self,event: GiftEvent):
        if event.gift.streakable and not event.streaking:
            if divisa!="Por defecto":
                if divisa=='USD': total=float((event.gift.diamond_count*event.repeat_count)/100)
                else:
                    moneda = json.loads(google_currency.convert('USD', divisa, int((event.gift.diamond_count * event.repeat_count) / 100)))
                    if moneda['converted']: total=moneda['amount']
                mensajito=_('%s ha enviado %s %s (%s %s)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(total),divisa)
            else: mensajito=_('%s ha enviado %s %s (%s diamante)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(event.gift.diamond_count))
        elif not event.gift.streakable:
            if divisa!="Por defecto":
                if divisa=='USD': total=int((event.gift.diamond_count*event.repeat_count)/100)
                else:
                    moneda = json.loads(google_currency.convert('USD', divisa, int((event.gift.diamond_count * event.repeat_count) / 100)))
                    if moneda['converted']: total=moneda['amount']
                mensajito=_('%s ha enviado %s %s (%s %s)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(total),divisa)
            else: mensajito=_('%s ha enviado %s %s (%s diamante)') % (event.user.nickname,str(event.repeat_count),event.gift.name,str(event.gift.diamond_count))
        try:
            self.chat_controller.agregar_mensaje_donacion(mensajito)
            if config['sonidos'] and config['listasonidos'][3]: player.playsound(rutasonidos[3],False)
        except Exception as e: pass

    async def on_join(self,event: JoinEvent):
        self.unidos+=1
        self.chat_controller.agregar_mensaje_general(event.user.nickname+_(" se ha unido a tu en vivo."))
        if config['sonidos'] and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)

    async def on_like(self,event: LikeEvent):
        self.megusta=event.total
        self.gustados.append(event.user.nickname)
        self.chat_controller.agregar_mensaje_general(event.user.nickname + _(" le ha dado me gusta a tu en vivo."))
        if config['sonidos'] and config['listasonidos'][9]: player.playsound(rutasonidos[9],False)

    async def on_share(self,event: ShareEvent):
        self.compartidas+=1
        self.chat_controller.agregar_mensaje_general(event.user.nickname + _(" ha compartido tu en vivo!"))
        if config['sonidos'] and config['listasonidos'][11]: player.playsound(rutasonidos[11],False)

    async def on_view(self,event: RoomUserSeqEvent): self.chat_controller.agregar_titulo(self.chat.unique_id+_(' en vivo, actualmente ')+str(event.m_total)+_(' viendo ahora'))
