import asyncio
import threading
from logging import getLogger

import wx
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import (
    CommentEvent,
    ConnectEvent,
    DisconnectEvent,
    EmoteChatEvent,
    EnvelopeEvent,
    FollowEvent,
    GiftEvent,
    JoinEvent,
    LikeEvent,
    LiveEndEvent,
    RoomUserSeqEvent,
    ShareEvent,
    SuperFanBoxEvent,
    SuperFanEvent,
    SuperFanJoinEvent,
)

from exchange import exchange
from globals import data_store
from globals.resources import rutasonidos
from setup import player, reader
from utils import funciones, translator

logger = getLogger(__name__)


def _nombre_usuario(usuario):
    # event.user es un User "crudo" de TikTok: en TikTokLive 6.6.6 / proto v3 el campo
    # es .nickname (y .display_id para el @-handle). Se mantienen los nombres antiguos
    # (.nick_name/.username) como respaldo por si se instala otra versión.
    if usuario is None:
        return ""
    return (
        getattr(usuario, "nickname", None)
        or getattr(usuario, "nick_name", None)
        or getattr(usuario, "username", None)
        or getattr(usuario, "display_id", None)
        or ""
    )


def _usuario_barrage(event):
    # SuperFanEvent / SuperFanJoinEvent derivan de BarrageEvent, que no trae un
    # campo user directo: el usuario viene en las piezas de texto
    # (TextPiece.user_value.user). Se escanea common_barrage_content y content.
    for texto in (
        getattr(event, "common_barrage_content", None),
        getattr(event, "content", None),
    ):
        for pieza in getattr(texto, "pieces", None) or []:
            user = getattr(getattr(pieza, "user_value", None), "user", None)
            if user is not None:
                return user
    return None


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
        self.translator = None
        self.filtrar_anteriores = False
        # Fallback al navegador: si la conexion normal (firmador remoto) falla,
        # se ofrece leer del navegador una sola vez. _usando_navegador es True
        # desde el arranque solo si ya se eligio el navegador en el desplegable.
        self._usando_navegador = False
        self._navegador_ofrecido = False

    def iniciar_chat(self):
        self.is_running = True
        thread = threading.Thread(target=self._start_async_loop, daemon=True)
        thread.start()

    def _start_async_loop(self):
        # al terminar la corutina principal (desconexión real incluida) hay que parar
        # el bucle: si no, run_forever sigue girando vacío y el hilo queda zombi
        parar_bucle = lambda _tarea: self.loop.stop()
        tarea_principal = None
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            tarea_principal = self.loop.create_task(self._initialize_and_run_client())
            tarea_principal.add_done_callback(parar_bucle)
            self.loop.run_forever()
        except Exception:
            logger.exception("Error fatal en el hilo de conexión")
        finally:
            if tarea_principal is not None:
                tarea_principal.remove_done_callback(parar_bucle)
            pending = asyncio.all_tasks(loop=self.loop)
            for task in pending:
                task.cancel()
            try:
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except RuntimeError:
                pass  # un stop() rezagado de detener() puede vaciar el bucle antes de tiempo
            self.loop.close()
            logger.info("Hilo de TikTok finalizado.")

    async def _initialize_and_run_client(self):
        try:
            user_id = funciones.extractUser(self.url)
            if not user_id:
                raise ValueError(_("No se pudo obtener la URL real de TikTok."))
            self.chat = TikTokLiveClient(unique_id=user_id)
            self._instrumentar_historial()
            self._instalar_firmador_local()
            self._add_listeners()
            await self._run_client_async()
        except Exception as e:
            logger.exception("Error al inicializar el cliente de TikTok")
            wx.CallAfter(self.chat_controller.notificar_error, str(e))
            self.detener()

    async def _run_client_async(self):
        while self.is_running:
            try:
                is_live_now = await self.chat.is_live()
                if is_live_now:
                    if self.last_live_status is not True:
                        wx.CallAfter(
                            reader.leer_aviso,
                            _("El usuario está en vivo. Conectando..."),
                        )
                    self.last_live_status = True
                    if data_store.dst:
                        self.translator = translator.TranslatorWrapper()
                    # Casilla «Leer los mensajes anteriores al chat» desmarcada: se ignoran los
                    # comentarios marcados por TikTok como parte del reenvío de historial
                    # (history_comment_count), ver _instrumentar_historial. Se re-evalúa en
                    # cada (re)conexión del bucle.
                    self.filtrar_anteriores = not data_store.config.get(
                        "leer_historial", True
                    )
                    await self.chat.connect()
                else:
                    if self.last_live_status is not False:
                        wx.CallAfter(
                            reader.leer_aviso,
                            _("El usuario no está en vivo. Reintentando en un minuto."),
                        )
                    self.last_live_status = False
                    if self.is_running:
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self.is_running:
                    break
                # El firmador remoto de TikTok suele caerse. Si la conexion
                # normal falla y todavia no probamos el navegador, ofrecerlo una
                # sola vez: si acepta, se instala el espejo y se reintenta en el
                # mismo bucle; si no, se informa el error como siempre.
                if not self._usando_navegador and not self._navegador_ofrecido:
                    self._navegador_ofrecido = True
                    logger.info(
                        "La conexion normal de TikTok fallo; se ofrece el navegador: %s",
                        e,
                    )
                    acepta = await asyncio.to_thread(self._ofrecer_navegador)
                    if acepta and self.is_running and self._activar_navegador():
                        self.last_live_status = None
                        continue
                logger.exception("Error en el bucle del cliente")
                wx.CallAfter(self.chat_controller.notificar_error, str(e))
                self.detener()

    def detener(self):
        if self.media_controller:
            self.media_controller.release()
        if self.is_running and self.loop and self.loop.is_running():
            self.is_running = False
            logger.info("Deteniendo servicio de TikTok...")
            # Cerrar y frenar en una sola corutina: así el disconnect se espera
            # (await) de verdad antes de parar el bucle. Antes se programaba el
            # disconnect por un lado y el stop por otro; si el bucle paraba
            # primero, la corutina del disconnect quedaba sin await y saltaba un
            # RuntimeWarning ("coroutine was never awaited").
            loop = self.loop
            chat = self.chat

            async def _cerrar_y_frenar():
                try:
                    if chat:
                        await chat.disconnect()
                except Exception:
                    logger.debug("Cierre del cliente con incidencia menor", exc_info=True)
                finally:
                    loop.stop()

            asyncio.run_coroutine_threadsafe(_cerrar_y_frenar(), loop)

    def _instalar_firmador_local(self):
        """Deja el cliente leyendo el chat del navegador, si la opción está marcada.

        TikTok exige que la petición al websocket del chat vaya firmada, y el
        servicio externo que la firmaba está caído. El navegador del usuario, en
        cambio, ya tiene el directo abierto con su websocket firmado y andando: la
        extensión copia esas tramas y las manda a un puerto local. Aquí solo se
        cambia de dónde saca el cliente sus mensajes (ver servicios/tiktok_espejo).

        Apagado de fábrica: sin la extensión puesta no llegaría nada y el chat se
        quedaría esperando en silencio, que es peor que fallar.
        """
        if not data_store.config.get("tiktok_firmador_local", False):
            return
        try:
            from servicios import tiktok_espejo, tiktok_interceptor

            servidor = tiktok_interceptor.servidor_compartido()
            tiktok_espejo.instalar_espejo(
                self.chat, servidor.sesiones, avisar=self._avisar_firmador
            )
            self._usando_navegador = True
            self._navegador_ofrecido = True  # ya esta en el navegador: no ofrecerlo
        except OSError:
            # El puerto ocupado casi siempre significa otra copia de VeTube abierta;
            # decirlo es más útil que un traceback en el log.
            logger.exception("No se pudo abrir el puerto del firmador local")
            wx.CallAfter(
                self.chat_controller.notificar_error,
                _(
                    "No se pudo abrir el puerto del firmador local. "
                    "¿Hay otra copia de VeTube abierta?"
                ),
            )
        except Exception:
            # Que falle el firmador no debe tumbar el chat: sin él, el cliente sigue
            # intentando la conexión normal y el error queda en el log.
            logger.exception("No se pudo instalar el firmador local")

    def _avisar_firmador(self, texto):
        # El espejo corre en el hilo de asyncio; los avisos tienen que volver al
        # hilo de wx para que el lector de pantalla los anuncie.
        wx.CallAfter(reader.leer_aviso, _(texto))

    def _ofrecer_navegador(self):
        """Muestra el cartel y espera la respuesta. Corre fuera del bucle asyncio
        (con asyncio.to_thread) para no congelarlo mientras el dialogo esta abierto."""
        import threading

        evento = threading.Event()
        resultado = {"aceptado": False}

        def mostrar():
            try:
                dlg = wx.MessageDialog(
                    self.frame,
                    _(
                        "No se pudo conectar al chat de TikTok por el servicio "
                        "habitual (suele estar caido).\n\n"
                        "Se puede leer desde el navegador. Asegurate de tener la "
                        "extension de VeTube instalada y este directo abierto en "
                        "el navegador, y pulsa Aceptar cuando este listo."
                    ),
                    _("Leer TikTok desde el navegador"),
                    wx.OK | wx.CANCEL | wx.ICON_INFORMATION,
                )
                resultado["aceptado"] = dlg.ShowModal() == wx.ID_OK
                dlg.Destroy()
            finally:
                evento.set()

        wx.CallAfter(mostrar)
        evento.wait()
        return resultado["aceptado"]

    def _activar_navegador(self):
        """Instala el espejo sobre el cliente ya creado para reintentar leyendo
        del navegador. Devuelve True si quedo listo."""
        try:
            from servicios import tiktok_espejo, tiktok_interceptor

            servidor = tiktok_interceptor.servidor_compartido()
            tiktok_espejo.instalar_espejo(
                self.chat, servidor.sesiones, avisar=self._avisar_firmador
            )
            self._usando_navegador = True
            return True
        except OSError:
            logger.exception("No se pudo abrir el puerto del firmador local")
            wx.CallAfter(
                self.chat_controller.notificar_error,
                _(
                    "No se pudo abrir el puerto del firmador local. "
                    "¿Hay otra copia de VeTube abierta?"
                ),
            )
        except Exception:
            logger.exception("No se pudo instalar el firmador local")
        return False

    def _instrumentar_historial(self):
        # TikTokLiveClient recibe de TikTok un indicador fiable (is_history) que dice si un
        # mensaje formaba parte del reenvío de historial al conectar, pero lo descarta al
        # construir el evento de alto nivel (CommentEvent, etc.) en _parse_webcast_response_message.
        # Antes filtrábamos por marca de tiempo con un margen de tolerancia fijo, pero en un chat
        # activo los últimos mensajes del historial caen casi siempre dentro de ese margen y se
        # colaban como si fueran nuevos. Se engancha aquí para recuperar el indicador real de TikTok.
        parse_original = self.chat._parse_webcast_response_message

        async def parse_instrumentado(
            webcast_response=None, webcast_response_message=None, **kwargs
        ):
            # TikTokLive 6.6.6 llama con argumentos por palabra clave
            # (webcast_response, webcast_response_message); versiones anteriores
            # usaban un único argumento posicional. Aceptar ambos mantiene la
            # compatibilidad.
            eventos = await parse_original(
                webcast_response=webcast_response,
                webcast_response_message=webcast_response_message,
                **kwargs,
            )
            es_historico = getattr(webcast_response_message, "is_history", False)
            for evento in eventos or []:
                if evento is not None:
                    evento._vt_es_historico = es_historico
            return eventos

        self.chat._parse_webcast_response_message = parse_instrumentado

    def prepare_player(self):
        try:
            from utils.play_mp4 import extract_stream_url

            video_url = extract_stream_url(self.url, format_preference="best")
            if video_url:
                from controller.media_controller import MediaController

                self.media_controller = MediaController(
                    url=video_url,
                    state_callback=self.chat_controller.chat_dialog.on_media_player_state_change,
                )
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception:
            logger.exception("Error al iniciar la reproducción de video en TikTok")

    def _add_listeners(self):
        self.chat.add_listener(ConnectEvent, self.on_connect)
        if data_store.config["categorias"][0]:
            self.chat.add_listener(CommentEvent, self.on_comment)
        self.chat.add_listener(LiveEndEvent, self.finalizado)
        self.chat.add_listener(DisconnectEvent, self.on_disconnect)
        if data_store.config["categorias"][2]:
            self.chat.add_listener(EmoteChatEvent, self.on_emote)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(EnvelopeEvent, self.on_chest)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(FollowEvent, self.on_follow)
        if data_store.config["categorias"][3]:
            self.chat.add_listener(GiftEvent, self.on_gift)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(JoinEvent, self.on_join)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(LikeEvent, self.on_like)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(ShareEvent, self.on_share)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(SuperFanJoinEvent, self.on_superfan_join)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(SuperFanEvent, self.on_superfan)
        if data_store.config["categorias"][1]:
            self.chat.add_listener(SuperFanBoxEvent, self.on_superfan_box)
        self.chat.add_listener(RoomUserSeqEvent, self.on_view)

    async def finalizado(self, event: LiveEndEvent):
        self.last_live_status = False
        wx.CallAfter(
            reader.leer_aviso,
            _("El directo ha finalizado. Se buscará de nuevo en un minuto."),
        )

    async def on_disconnect(self, event: DisconnectEvent):
        # TikTokLive emite DisconnectEvent en cada cierre del websocket, incluido el fin
        # normal del directo: en ese caso finalizado() ya anunció que se buscará de nuevo,
        # así que dejamos que el bucle de _run_client_async siga sondeando cada minuto.
        if self.is_running and self.last_live_status is not False:
            self.is_running = False
            wx.CallAfter(
                reader.leer_aviso,
                _("Se ha perdido la conexión. El servicio se ha detenido."),
            )

    async def on_connect(self, event: ConnectEvent):
        self.last_live_status = True
        wx.CallAfter(reader.leer_aviso, _("Ingresando al chat"))
        if not self.media_controller:
            threading.Thread(target=self.prepare_player, daemon=True).start()
        if data_store.config["sonidos"] and data_store.config["listasonidos"][6]:
            wx.CallAfter(player.play, rutasonidos[6])

    def _es_mensaje_anterior(self, event):
        # True si TikTok marcó el mensaje como parte del reenvío de historial al conectar
        # (ver _instrumentar_historial), para respetar la casilla «leer mensajes anteriores»
        # desmarcada.
        return self.filtrar_anteriores and bool(
            getattr(event, "_vt_es_historico", False)
        )

    async def on_comment(self, event: CommentEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][0] and hasattr(
            self.chat_controller.ui, "list_box_general"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.agregar_mensaje, nombre)
            cadena = event.comment if event.comment is not None else ""
            if data_store.dst and self.translator:
                cadena = self.translator.translate(text=cadena, target=data_store.dst)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_general, nombre + ": " + cadena
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][0]:
                wx.CallAfter(player.play, rutasonidos[0])
            if data_store.config["reader"] and data_store.config["unread"][0]:
                wx.CallAfter(reader.leer_mensaje, nombre + ": " + cadena)

    async def on_emote(self, event: EmoteChatEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][1] and hasattr(
            self.chat_controller.ui, "list_box_miembros"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.agregar_mensaje, nombre)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_miembro,
                nombre + _(" envió un emogi."),
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][1]:
                wx.CallAfter(player.play, rutasonidos[1])
            if data_store.config["reader"] and data_store.config["unread"][1]:
                wx.CallAfter(reader.leer_mensaje, nombre + _(" envió un emogi."))

    async def on_chest(self, event: EnvelopeEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][9] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            # EnvelopeEvent no tiene campo 'user': el remitente viene en envelope_info
            mensajito = event.envelope_info.send_user_name + _(" ha enviado un cofre!")
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento, mensajito, "chest"
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][12]:
                wx.CallAfter(player.play, rutasonidos[12])
            if data_store.config["reader"] and data_store.config["unread"][9]:
                wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_follow(self, event: FollowEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][7] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.agregar_seguidor)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento,
                nombre + _(" comenzó a seguirte!"),
                "follow",
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][10]:
                wx.CallAfter(player.play, rutasonidos[10])
            if data_store.config["reader"] and data_store.config["unread"][7]:
                wx.CallAfter(reader.leer_mensaje, nombre + _(" comenzó a seguirte!"))

    async def on_gift(self, event: GiftEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][3] and hasattr(
            self.chat_controller.ui, "list_box_donaciones"
        ):
            gift = event.gift
            if gift is None:
                return
            # Los regalos "streakable" (type == 1) emiten un GiftEvent por cada
            # incremento con repeat_count acumulado; los intermedios tienen
            # event.streaking == True. Se filtran y solo se anuncia el último
            # (repeat_end == 1, con el total de la racha).
            if event.streaking:
                return
            mensajito = ""
            nombre = _nombre_usuario(event.user)
            if data_store.divisa != "Por defecto":
                total = exchange.from_diamonds(gift.diamond_count * event.repeat_count)
                mensajito = _("%s ha enviado %s %s (%s %s)") % (
                    nombre,
                    str(event.repeat_count),
                    gift.name,
                    str(total),
                    data_store.divisa,
                )
            else:
                mensajito = _("%s ha enviado %s %s (%s diamante)") % (
                    nombre,
                    str(event.repeat_count),
                    gift.name,
                    str(gift.diamond_count),
                )

            if mensajito:
                wx.CallAfter(self.chat_controller.agregar_mensaje_donacion, mensajito)
                if (
                    data_store.config["sonidos"]
                    and data_store.config["listasonidos"][3]
                ):
                    wx.CallAfter(player.play, rutasonidos[3])
                if data_store.config["reader"] and data_store.config["unread"][3]:
                    wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_join(self, event: JoinEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][2] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.agregar_unido)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento,
                nombre + _(" se ha unido a tu en vivo."),
                "join",
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][2]:
                wx.CallAfter(player.play, rutasonidos[2])
            if data_store.config["reader"] and data_store.config["unread"][2]:
                wx.CallAfter(
                    reader.leer_mensaje, nombre + _(" se ha unido a tu en vivo.")
                )

    async def on_like(self, event: LikeEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][6] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.actualizar_megusta, event.total)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento,
                nombre + _(" le ha dado me gusta a tu en vivo."),
                "like",
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][9]:
                wx.CallAfter(player.play, rutasonidos[9])
            if data_store.config["reader"] and data_store.config["unread"][6]:
                wx.CallAfter(
                    reader.leer_mensaje,
                    nombre + _(" le ha dado me gusta a tu en vivo."),
                )

    async def on_share(self, event: ShareEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][8] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(event.user)
            wx.CallAfter(self.estadisticas_manager.agregar_compartida)
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento,
                nombre + _(" ha compartido tu en vivo!"),
                "share",
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][11]:
                wx.CallAfter(player.play, rutasonidos[11])
            if data_store.config["reader"] and data_store.config["unread"][8]:
                wx.CallAfter(
                    reader.leer_mensaje, nombre + _(" ha compartido tu en vivo!")
                )

    async def on_superfan_join(self, event: SuperFanJoinEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][2] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(_usuario_barrage(event))
            mensajito = "super fan " + nombre + _(" se ha unido a tu en vivo.")
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, mensajito, "join")
            if data_store.config["sonidos"] and data_store.config["listasonidos"][2]:
                wx.CallAfter(player.play, rutasonidos[2])
            if data_store.config["reader"] and data_store.config["unread"][2]:
                wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_superfan(self, event: SuperFanEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][2] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = _nombre_usuario(_usuario_barrage(event))
            mensajito = nombre + _(" ¡se ha convertido en super fan!")
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, mensajito, "join")
            if data_store.config["sonidos"] and data_store.config["listasonidos"][2]:
                wx.CallAfter(player.play, rutasonidos[2])
            if data_store.config["reader"] and data_store.config["unread"][2]:
                wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_superfan_box(self, event: SuperFanBoxEvent):
        if self._es_mensaje_anterior(event):
            return
        if data_store.config["eventos"][9] and hasattr(
            self.chat_controller.ui, "list_box_eventos"
        ):
            nombre = (
                getattr(getattr(event, "envelope_info", None), "send_user_name", None)
                or ""
            )
            mensajito = nombre + _(" ha enviado un cofre de super fan!")
            wx.CallAfter(
                self.chat_controller.agregar_mensaje_evento, mensajito, "chest"
            )
            if data_store.config["sonidos"] and data_store.config["listasonidos"][12]:
                wx.CallAfter(player.play, rutasonidos[12])
            if data_store.config["reader"] and data_store.config["unread"][9]:
                wx.CallAfter(reader.leer_mensaje, mensajito)

    async def on_view(self, event: RoomUserSeqEvent):
        title = (
            self.chat.unique_id
            + _(" en vivo, actualmente ")
            + str(event.total)
            + _(" viendo ahora")
        )
        wx.CallAfter(self.chat_controller.agregar_titulo, title)
        wx.CallAfter(
            self.chat_controller.chat_dialog.update_chat_page_title,
            self.chat_controller,
            title,
        )
