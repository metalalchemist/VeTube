import asyncio, threading, re, wx, httpx
import discord
from globals import data_store
from globals.resources import rutasonidos
from setup import reader, player
from utils import translator

def extraer_id_canal(url):
    """Devuelve el id del canal si la URL es un enlace de canal de Discord
    (https://discord.com/channels/<servidor>/<canal>), o None si no lo es."""
    match = re.search(r'discord(?:app)?\.com/channels/(\d+)/(\d+)', url)
    if match:
        return match.group(2)
    return None

def validar_token(token):
    """Comprueba el token contra la API de Discord.
    Devuelve True si es válido, False si no lo es y None si no se pudo comprobar (fallo de red)."""
    try:
        respuesta = httpx.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bot {token}"},
            timeout=8,
        )
        return respuesta.status_code == 200
    except Exception:
        return None

class ServicioDiscord:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url  # id del canal, extraído del enlace en main_controller
        self.frame = frame
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager

        self.channel_id = int(url)
        self.is_running = False
        self.loop = None
        self.client = None
        self.thread = None
        self.client_task = None
        self.translator = None

    def iniciar_chat(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.thread.start()

    def _start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            wx.CallAfter(reader.leer_sapi, _("Cargando..."))
            if data_store.dst: self.translator = translator.TranslatorWrapper()

            intents = discord.Intents.default()
            intents.message_content = True
            self.client = discord.Client(intents=intents)
            self._add_listeners()

            self.client_task = self.loop.create_task(self._conectar())
            self.loop.run_forever()
        except Exception as e:
            if self.is_running:
                print(f"Error fatal en el hilo de conexión de Discord: {e}")
                wx.CallAfter(self.chat_controller.notificar_error, str(e))
        finally:
            try:
                self.loop.close()
            except Exception:
                pass
            print("Hilo de Discord finalizado.")

    async def _conectar(self):
        try:
            await self.client.start(data_store.config.get('discord_token', ''))
        except discord.LoginFailure:
            if self.is_running:
                # El token guardado ya no sirve: se borra para que el diálogo
                # vuelva a pedirlo en el siguiente intento.
                wx.CallAfter(self._borrar_token_guardado)
                wx.CallAfter(self.chat_controller.notificar_error, _("El token del bot de Discord no es válido o fue revocado. Pega de nuevo el enlace del canal para introducir un token nuevo."))
                self.detener()
        except discord.PrivilegedIntentsRequired:
            if self.is_running:
                wx.CallAfter(self.chat_controller.notificar_error, _("Al bot le falta activar «Message Content Intent» en el portal de desarrolladores de Discord. Actívalo y vuelve a intentarlo."))
                self.detener()
        except Exception as e:
            if self.is_running:
                print(f"Error de conexión con Discord: {e}")
                wx.CallAfter(self.chat_controller.notificar_error, str(e))
                self.detener()

    def _borrar_token_guardado(self):
        from utils import fajustes
        data_store.config['discord_token'] = ""
        fajustes.guardarConfiguracion(data_store.config)

    def _add_listeners(self):
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    async def on_ready(self):
        wx.CallAfter(reader.leer_sapi, _("Ingresando al chat"))
        if data_store.config['sonidos'] and data_store.config['listasonidos'][6]:
            wx.CallAfter(player.play, rutasonidos[6])
        try:
            channel = self.client.get_channel(self.channel_id)
            if channel is None:
                channel = await self.client.fetch_channel(self.channel_id)
            title = f"#{channel.name} ({channel.guild.name})"
            wx.CallAfter(self.chat_controller.agregar_titulo, title)
            wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, title)
        except Exception as e:
            print(f"Error al acceder al canal de Discord: {e}")
            wx.CallAfter(reader.leer_sapi, _("No se encontró el canal de Discord. Comprueba que el bot está invitado al servidor y que el enlace del canal es correcto."))
            self.detener()

    async def on_message(self, message):
        if not self.is_running:
            return
        if message.channel.id != self.channel_id:
            return
        cadena = message.content
        if not cadena:
            return
        wx.CallAfter(self.estadisticas_manager.agregar_mensaje, message.author.display_name)
        if data_store.dst and self.translator: cadena = self.translator.translate(text=cadena, target=data_store.dst)

        full_message = f"{message.author.display_name}: {cadena}"

        # Moderadores: el dueño del servidor o quien puede gestionar mensajes
        # (equivalente a los badges de moderador/propietario de Kick)
        es_moderador = False
        if message.guild:
            permisos = getattr(message.author, 'guild_permissions', None)
            es_moderador = message.guild.owner_id == message.author.id or (permisos is not None and (permisos.administrator or permisos.manage_messages))

        if es_moderador and data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
            wx.CallAfter(self.chat_controller.agregar_mensaje_moderador, full_message)
            if data_store.config['sonidos'] and data_store.config['listasonidos'][4]: wx.CallAfter(player.play, rutasonidos[4])
            if data_store.config['reader'] and data_store.config['unread'][4]: wx.CallAfter(reader.leer_mensaje, full_message)
            return

        # Fallback: General
        if data_store.config['eventos'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
            wx.CallAfter(self.chat_controller.agregar_mensaje_general, full_message)
            if data_store.config['sonidos'] and data_store.config['listasonidos'][0]: wx.CallAfter(player.play, rutasonidos[0])
            if data_store.config['reader'] and data_store.config['unread'][0]: wx.CallAfter(reader.leer_mensaje, full_message)

    def detener(self):
        if not self.is_running:
            return
        self.is_running = False
        print("Deteniendo servicio de Discord...")

        if self.loop and self.loop.is_running():
            if self.client:
                asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

        print("Servicio de Discord detenido completamente.")
