import json, google_currency,threading
from chat_downloader import ChatDownloader
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController
from utils.estadisticas_manager import EstadisticasManager

class ServicioYouTube:
    def __init__(self, url, frame, plataforma):
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = ChatController(frame, self, plataforma)
        self._detener = False

    def iniciar_chat(self):
        self._detener = False
        self._hilo = threading.Thread(target=self.recibir, daemon=True)
        self._hilo.start()
        player.playsound(rutasonidos[6], False)
        reader.leer_sapi(_("Ingresando al chat."))
        self.chat_controller.mostrar_dialogo()
    def detener(self):
        self._detener = True

    def recibir(self):
        if data_store.dst: self.translator=translator.translatorWrapper()
        self.chat = ChatDownloader().get_chat(self.url, message_groups=["messages", "superchat"], interruptible_retry=False)
        self.chat_controller.agregar_titulo(self.chat.title)
        for message in self.chat:
            if self._detener: break
            if not message: continue
            if message['message'] is None: message['message'] = ''
            if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)

            author_name = message['author']['display_name']
            EstadisticasManager().agregar_mensaje(author_name)
            msg = message['message']

            # Default message type
            message_type = 'general'

            if 'badges' in message['author']:
                for badge in message['author']['badges']:
                    title = badge.get('title', '')
                    if 'Owner' in title:
                        message_type = 'propietario'
                        break
                    if 'Moderator' in title:
                        message_type = 'moderador'
                        break
                    if 'member' in title.lower():
                        message_type = 'miembro'
                        break
                    if 'Verified' in title:
                        message_type = 'verificado'
                        break

            if message['message_type'] == 'paid_message' or message['message_type'] == 'paid_sticker': message_type = 'donacion'
            if 'header_secondary_text' in message:
                if data_store.config['eventos'][2] and data_store.config['categorias'][1]:
                    for t in message['author']['badges']:
                        mensajito=author_name+ _(' se a conectado al chat. ')+t['title']
                        break
                    self.chat_controller.agregar_mensaje_evento(mensajito)
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                    if data_store.config['unread'][2]: reader.leer_mensaje(mensajito)
                continue
            # Construct the message string
            if message_type == 'donacion':
                if data_store.config['eventos'][3] and data_store.config['categorias'][3]:
                    if data_store.divisa != "Por defecto" and data_store.divisa != message['money']['currency']:
                        moneda = json.loads(google_currency.convert(message['money']['currency'], data_store.divisa, message['money']['amount']))
                        if moneda['converted']:
                            message['money']['currency'] = data_store.divisa
                            message['money']['amount'] = moneda['amount']
                    full_message = f"{message['money']['amount']} {message['money']['currency']}, {author_name}: {msg}"
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][3]: player.playsound(rutasonidos[3], False)
                    self.chat_controller.agregar_mensaje_donacion(full_message)
                    if data_store.config['reader'] and data_store.config['unread'][3]: reader.leer_mensaje(full_message)
                continue

            full_message = f"{author_name}: {msg}"

            if message_type == 'general':
                if data_store.config['eventos'][0] and data_store.config['categorias'][0]:
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][0]: player.playsound(rutasonidos[0], False)
                    self.chat_controller.agregar_mensaje_general(full_message)
                    if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(full_message)
            elif message_type == 'miembro':
                if data_store.config['eventos'][1] and data_store.config['categorias'][2]:
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][1]: player.playsound(rutasonidos[1], False)
                    self.chat_controller.agregar_mensaje_miembro(full_message)
                    if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(full_message)
            elif message_type == 'moderador' or message_type=='propietario':
                if data_store.config['eventos'][4] and data_store.config['categorias'][4]:
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][4]:
                        if message_type=='moderador': player.playsound(rutasonidos[4], False)
                        if message_type=='propietario': player.playsound(rutasonidos[7], False)
                    self.chat_controller.agregar_mensaje_moderador(full_message)
                    if data_store.config['reader'] and data_store.config['unread'][4]: reader.leer_mensaje(full_message)
            elif message_type == 'verificado':
                if data_store.config['eventos'][5] and data_store.config['categorias'][5]:
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][5]: player.playsound(rutasonidos[5], False)
                    self.chat_controller.agregar_mensaje_verificado(f"{author_name}: {msg}")
                    if data_store.config['reader'] and data_store.config['unread'][5]: reader.leer_mensaje(f'{author_name}: {msg}')