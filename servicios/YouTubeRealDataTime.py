import pytchat, wx, json, threading, google_currency
from utils.play_mp4 import extract_stream_url
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player, reader
from controller.chat_controller import ChatController
from controller.media_controller import MediaController
from servicios.estadisticas_manager import EstadisticasManager

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
                        if data_store.config['eventos'][3] and data_store.config['categorias'][3] and hasattr(self.chat_controller.ui, 'list_box_donaciones'):
                            amount = c.amountString
                            currency = c.currency
                            if data_store.divisa != "Por defecto" and data_store.divisa != currency:
                                converted = json.loads(google_currency.convert(currency, data_store.divisa, c.amountValue))
                                if converted['converted']:
                                    currency = data_store.divisa
                                    amount = converted['amount']
                            
                            full_message = f"{amount} {currency}, {author_name}: {msg}"
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][3]:
                                player.play(rutasonidos[3])
                            wx.CallAfter(self.chat_controller.agregar_mensaje_donacion, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][3]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                        continue

                    full_message = f"{author_name}: {msg}"

                    if message_type == 'general':
                        if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][0]:
                                player.play(rutasonidos[0])
                            wx.CallAfter(self.chat_controller.agregar_mensaje_general, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][0]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'miembro':
                        if data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][1]:
                                player.play(rutasonidos[1])
                            wx.CallAfter(self.chat_controller.agregar_mensaje_miembro, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][1]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'moderador' or message_type == 'propietario':
                        if data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][4]:
                                if message_type == 'moderador':
                                    player.play(rutasonidos[4])
                                if message_type == 'propietario':
                                    player.play(rutasonidos[7])
                            wx.CallAfter(self.chat_controller.agregar_mensaje_moderador, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][4]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'verificado':
                        if data_store.config['eventos'][5] and data_store.config['categorias'][5] and hasattr(self.chat_controller.ui, 'list_box_verificados'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][5]:
                                player.play(rutasonidos[5])
                            wx.CallAfter(self.chat_controller.agregar_mensaje_verificado, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][5]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
        except Exception as e: print(f"Error en el servicio de YouTube en tiempo real: {e}")
        finally:
            if self.chat: self.chat.terminate()
