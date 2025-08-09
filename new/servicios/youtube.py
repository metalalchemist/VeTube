import json, google_currency,threading
from chat_downloader import ChatDownloader
from globals.data_store import config, divisa, dst
from globals.resources import rutasonidos
from utils import translator
from setup import player
from controller.chat_controller import ChatController

class ServicioYouTube:
    def __init__(self, url, frame, plataforma):
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = ChatController(frame)

    def iniciar_chat(self):
            threading.Thread(target=self.recibir, daemon=True).start()
            self.chat_controller.mostrar_dialogo()

    def recibir(self):
        self.chat = ChatDownloader().get_chat(self.url, message_groups=["messages", "superchat"], interruptible_retry=False)
        for message in self.chat:
            if message['message'] is None:
                message['message'] = ''
            if dst:
                message['message'] = translator.translate(text=message['message'], target=dst)
            # Comprobación básica para evitar KeyError en 'author'['name']
            if 'header_secondary_text' in message and config['eventos'][1]:
                for t in message['author']['badges']:
                    mensajito = message['author']['display_name'] + _(' se a conectado al chat. ') + t['title']
                    break
                    if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][2]:
                        player.playsound(rutasonidos[2], False)
                    self.chat_controller.agregar_mensaje(mensajito)
                continue
            if 'badges' in message['author']:
                for t in message['author']['badges']:
                    if 'Owner' in t['title']:
                        if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][4]:
                            player.playsound(rutasonidos[7], False)
                        self.chat_controller.agregar_mensaje(_('Propietario ') + message['author']['display_name'] + ': ' + message['message'])
                        break
                    if 'Moderator' in t['title'] and config['eventos'][3]:
                        if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][4]:
                            player.playsound(rutasonidos[4], False)
                        self.chat_controller.agregar_mensaje(_('Moderador ') + message['author']['display_name'] + ': ' + message['message'])
                        break
                    if 'member' in t['title'].lower() and config['eventos'][0]:
                        if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][1]:
                            player.playsound(rutasonidos[1], False)
                        self.chat_controller.agregar_mensaje(_('Miembro ') + message['author']['display_name'] + ': ' + message['message'])
                        break
                    if 'Verified' in t['title'] and config['eventos'][4]:
                        if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][5]:
                            player.playsound(rutasonidos[5], False)
                        self.chat_controller.agregar_mensaje(message['author']['display_name'] + _(' (usuario verificado): ') + message['message'])
                        break
                continue
            if message['message_type'] == 'paid_message' or message['message_type'] == 'paid_sticker':
                if config['eventos'][2]:
                    if divisa != "Por defecto" and divisa != message['money']['currency']:
                        moneda = json.loads(google_currency.convert(message['money']['currency'], divisa, message['money']['amount']))
                        if moneda['converted']:
                            message['money']['currency'] = divisa
                            message['money']['amount'] = moneda['amount']
                    if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][3]:
                        player.playsound(rutasonidos[3], False)
                    self.chat_controller.agregar_mensaje(str(message['money']['amount']) + message['money']['currency'] + ', ' + message['author']['display_name'] + ': ' + message['message'])
                    continue
            else:
                if config['sonidos'] and self.chat.status != "past" and config['listasonidos'][0]:
                    player.playsound(rutasonidos[0], False)
                self.chat_controller.agregar_mensaje(message['author']['display_name'] + ': ' + message['message'])
                continue