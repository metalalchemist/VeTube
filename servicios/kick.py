
import asyncio
import threading
import subprocess
import os
import platform
import wx
import traceback
import kick
from globals import data_store
from globals.resources import rutasonidos
from utils import funciones
from setup import reader, player
from controller.media_controller import MediaController
from utils.play_mp4 import extract_stream_url

class ServicioKick:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager
        
        self.is_running = False
        self.loop = None
        self.client = None
        self.bypass_process = None
        self.thread = None
        self.media_controller = None

    def iniciar_chat(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.thread.start()

    def _run_bypass_and_wait(self):
        dir_current_script = os.path.dirname(os.path.abspath(__file__))
        arch = "64" if platform.architecture()[0][:2] == "64" else "32"
        path_to_arch_dir = os.path.join(os.getcwd(), arch)
        bypass_executable = os.path.join(path_to_arch_dir, f"bypass{arch}.exe")

        if not os.path.exists(bypass_executable):
            print(f"Error: No se encuentra el archivo '{bypass_executable}'.")
            wx.CallAfter(reader.leer_sapi, _("error_bypass_no_encontrado"))
            return False

        print("Iniciando bypass.exe en segundo plano...")
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        try:
            self.bypass_process = subprocess.Popen(
                [bypass_executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags
            )
        except Exception as e:
            print(f"Error al intentar ejecutar {bypass_executable}: {e}")
            return False

        print("Esperando el mensaje 'starting' desde bypass.exe...")
        for line in iter(self.bypass_process.stdout.readline, ''):
            if not self.is_running:
                return False
            if "starting" in line.lower():
                print("Mensaje 'starting' detectado. Procediendo a conectar con Kick.")
                return True
        
        print("Error: bypass.exe terminó inesperadamente.")
        return False

    def _start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            wx.CallAfter(reader.leer_sapi, _("Cargando..."))
            if not self._run_bypass_and_wait():
                if self.is_running:
                    wx.CallAfter(reader.leer_sapi, _("error_iniciar_bypass"))
                self.detener()
                return

            self.client = kick.Client()
            self._add_listeners()
            
            # Iniciar el cliente como una tarea para no bloquear
            self.loop.create_task(self.client.run())
            self.loop.run_forever() # Esto se ejecutará hasta que se llame a loop.stop()
        except Exception as e:
            if self.is_running:
                print(f"Error fatal en el hilo de conexión de Kick: {e}")
                traceback.print_exc()
        finally:
            # Limpieza final del bucle
            if self.loop.is_running():
                self.loop.close()
            print("Hilo de Kick finalizado.")

    def _add_listeners(self):
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_follow)

    async def on_ready(self):
        print("Cliente de Kick listo.")
        wx.CallAfter(reader.leer_sapi, _("Ingresando al chat"))
        if data_store.config['sonidos'] and data_store.config['listasonidos'][6]:
            wx.CallAfter(player.play, rutasonidos[6])
        try:
            user = await self.client.fetch_user(self.url)
            title = user.chatroom.streamer.livestream.title
            wx.CallAfter(self.chat_controller.agregar_titulo, title)
            wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, title)
            await user.chatroom.connect()
            
            kick_page_url = f"https://kick.com/{self.url}"
            video_url = extract_stream_url(kick_page_url)
            
            print(f"URL de la página de Kick: {kick_page_url}")
            print(f"URL de stream extraída: {video_url}")

            if video_url and not self.media_controller:
                self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error al conectar al chatroom de Kick: {e}")
            wx.CallAfter(reader.leer_sapi, _("error_conectar_kick_chatroom"))
            self.detener()

    async def on_message(self, message: kick.Message):
        mensaje = f"{message.author.username}: {message.content}"
        wx.CallAfter(self.chat_controller.agregar_mensaje_general, mensaje)
        if data_store.config['sonidos'] and data_store.config['listasonidos'][0]:
            wx.CallAfter(player.play, rutasonidos[0])

    async def on_follow(self, user: kick.User):
        mensaje = f"{user.username} {_('comenzó a seguirte')}"
        if data_store.config['eventos'][7] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
            wx.CallAfter(self.estadisticas_manager.agregar_seguidor)
            wx.CallAfter(self.chat_controller.agregar_mensaje_evento, mensaje, "follow")
            if data_store.config['sonidos'] and data_store.config['listasonidos'][10]:
                wx.CallAfter(player.play, rutasonidos[10])
            if data_store.config['reader'] and data_store.config['unread'][7]:
                wx.CallAfter(reader.leer_mensaje, mensaje)

    def detener(self):
        if not self.is_running:
            return
        self.is_running = False
        print("Deteniendo servicio de Kick...")

        if self.media_controller:
            self.media_controller.release()
            self.media_controller = None

        if self.loop and self.loop.is_running():
            # Cancelar todas las tareas pendientes (principalmente client.run())
            for task in asyncio.all_tasks(loop=self.loop):
                task.cancel()
            # Detener el bucle de eventos
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.bypass_process:
            try:
                print("Terminando proceso de bypass...")
                self.bypass_process.terminate()
                self.bypass_process.wait()
                print("Proceso de bypass terminado.")
            except Exception as e:
                print(f"Error al terminar el proceso de bypass: {e}")
            self.bypass_process = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join()
        
        print("Servicio de Kick detenido completamente.")