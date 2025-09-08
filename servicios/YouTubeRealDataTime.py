import pytchat, wx, json, threading, google_currency
from utils.play_mp4 import play_video_url
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player, reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager
from helpers.sound_helper import playsound

class YouTubeRealTimeService:
    def __init__(self, url, frame, plataforma, title=None, chat_controller=None):
        self.url = url
        self.player = playsound()
        threading.Thread(target=play_video_url, args=(url, self.player,), daemon=True).start()
        self.frame = frame
        self.title = title
        self.chat = None
        if chat_controller:
            self.chat_controller = chat_controller
            self.chat_controller.servicio = self
        else:
            self.chat_controller = ChatController(frame, self, plataforma)
        self._detener = False

    def iniciar_chat_reutilizando_ui(self):
        self._detener = False
        self._hilo = threading.Thread(target=self.recibir, daemon=True)
        self._hilo.start()
        wx.CallAfter(reader.leer_sapi, "Cambiando a servicio de tiempo real.")

    def detener(self):
        self._detener = True
        if self.chat:
            self.chat.terminate()
        if hasattr(self, 'player') and self.player and self.player.sound:
            self.player.sound.stop()

    def recibir(self):
        if data_store.dst:
            self.translator = translator.translatorWrapper()
        try:
            self.chat = pytchat.create(video_id=self.url, interruptable=False)
            display_title = self.title + " (En tiempo real)"
            wx.CallAfter(self.chat_controller.agregar_titulo, display_title)

            while self.chat.is_alive() and not self._detener:
                for c in self.chat.get().sync_items():
                    if self._detener:
                        break
                    author_name = c.author.name
                    msg = c.message
                    EstadisticasManager().agregar_mensaje(author_name)
                    if data_store.dst:
                        msg = self.translator.translate(text=msg, target=data_store.dst)

                    message_type = 'general'
                    if c.author.isChatOwner:
                        message_type = 'propietario'
                    elif c.author.isChatModerator:
                        message_type = 'moderador'
                    elif c.author.isChatSponsor:
                        message_type = 'miembro'
                    elif c.author.isVerified:
                        message_type = 'verificado'

                    if c.type == "superChat" or c.type == "superSticker":
                        message_type = 'donacion'

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
                                player.playsound(rutasonidos[3], False)
                            wx.CallAfter(self.chat_controller.agregar_mensaje_donacion, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][3]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                        continue

                    full_message = f"{author_name}: {msg}"

                    if message_type == 'general':
                        if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][0]:
                                player.playsound(rutasonidos[0], False)
                            wx.CallAfter(self.chat_controller.agregar_mensaje_general, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][0]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'miembro':
                        if data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][1]:
                                player.playsound(rutasonidos[1], False)
                            wx.CallAfter(self.chat_controller.agregar_mensaje_miembro, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][1]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'moderador' or message_type == 'propietario':
                        if data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][4]:
                                if message_type == 'moderador':
                                    player.playsound(rutasonidos[4], False)
                                if message_type == 'propietario':
                                    player.playsound(rutasonidos[7], False)
                            wx.CallAfter(self.chat_controller.agregar_mensaje_moderador, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][4]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
                    elif message_type == 'verificado':
                        if data_store.config['eventos'][5] and data_store.config['categorias'][5] and hasattr(self.chat_controller.ui, 'list_box_verificados'):
                            if data_store.config['sonidos'] and data_store.config['listasonidos'][5]:
                                player.playsound(rutasonidos[5], False)
                            wx.CallAfter(self.chat_controller.agregar_mensaje_verificado, full_message)
                            if data_store.config['reader'] and data_store.config['unread'][5]:
                                wx.CallAfter(reader.leer_mensaje, full_message)
        except Exception as e:
            print(f"Error en el servicio de YouTube en tiempo real: {e}")
        finally:
            if self.chat:
                self.chat.terminate()
