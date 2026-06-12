import json, threading, re, wx
from exchange import exchange
from chat_downloader import ChatDownloader
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from utils.play_mp4 import extract_stream_url
from setup import player,reader
from controller.chat_controller import ChatController
from controller.media_controller import MediaController
from servicios.estadisticas_manager import EstadisticasManager

class ServicioTwich:
    def __init__(self, main_controller, url, frame, plataforma, chat_controller):
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = chat_controller
        self.estadisticas_manager = chat_controller.estadisticas_manager
        self.media_controller = None
        self._detener = False

    def iniciar_chat(self):
        self._detener = False
        self._hilo = threading.Thread(target=self.recibir, daemon=True)
        self._hilo.start()
        player.play(rutasonidos[6])
        reader.leer_sapi(_("Ingresando al chat."))

    def detener(self):
        self._detener = True
        if self.media_controller:
            self.media_controller.release()

    def prepare_player(self, status):
        try:
            format_pref = 'mp4' if status == "past" else 'best'
            video_url = extract_stream_url(self.url, format_preference=format_pref)
            if video_url:
                self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error al iniciar la reproducción de video en Twitch: {e}")

    def recibir(self):
        try:
            if data_store.dst: self.translator=translator.translatorWrapper()
            self.chat=ChatDownloader().get_chat(self.url,message_groups=["messages", "bits","subscriptions","upgrades"])
            threading.Thread(target=self.prepare_player, args=(self.chat.status,), daemon=True).start()
            wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, self.chat.title)
            for message in self.chat:
                if self._detener: break
                if not message: continue

                if message['message'] is None: message['message'] = ''
                if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)

                author_name = message['author'].get('display_name', _('Desconocido'))
                self.estadisticas_manager.agregar_mensaje(author_name)
                msg = message['message']
                full_message = f"{author_name}: {msg}"

                # Subscription events
                if message['message_type'] in ['resubscription', 'subscription', 'mystery_subscription_gift', 'subscription_gift'] and data_store.config['categorias'][1] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
                    sub_message = ""
                    if message['message_type'] == 'resubscription' and data_store.config['eventos'][2]:
                        sub_message = _("{author_name} ha renovado su suscripción en el nivel {subscription_plan_name}. ¡Lleva suscrito por {cumulative_months} meses!").format(author_name=author_name, subscription_plan_name=message.get('subscription_plan_name', ''), cumulative_months=message.get('cumulative_months', ''))
                        if message.get('message'):
                            mssg=message['message'].split('! ')
                            mssg=str(mssg[1:])
                            sub_message +=f": {mssg}"
                    elif message['message_type'] == 'subscription' and data_store.config['eventos'][2]: sub_message = _("{author_name} se ha suscrito en el nivel {subscription_plan_name} por {cumulative_months} meses!").format(author_name=author_name, subscription_plan_name=message.get('subscription_plan_name', ''), cumulative_months=message.get('cumulative_months', ''))
                    elif message['message_type'] == 'mystery_subscription_gift' and data_store.config['eventos'][2]: sub_message = _("{author_name} regaló una suscripción de nivel {subscription_type} a la comunidad, ¡ha regalado un total de {sender_count} suscripciones!").format(author_name=author_name, subscription_type=message.get('subscription_type', ''), sender_count=message.get('sender_count', ''))
                    elif message['message_type'] == 'subscription_gift' and data_store.config['eventos'][2]: sub_message = _("{author_name} ha regalado una suscripción a {gift_recipient_display_name} en el nivel {subscription_plan_name} por {number_of_months_gifted} meses!").format(author_name=author_name, gift_recipient_display_name=message.get('gift_recipient_display_name', ''), subscription_plan_name=message.get('subscription_plan_name', ''), number_of_months_gifted=message.get('number_of_months_gifted', ''))
                    self.chat_controller.agregar_mensaje_evento(sub_message)
                    if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][2]: player.play(rutasonidos[2])
                    if data_store.config['reader'] and data_store.config['unread'][2]: reader.leer_mensaje(sub_message)
                    continue

                # Cheer/Bits event
                cheer_matches = re.findall(r'cheer(\d+)', msg, re.IGNORECASE)
                if cheer_matches and data_store.config['categorias'][3] and data_store.config['eventos'][3] and hasattr(self.chat_controller.ui, 'list_box_donaciones'):
                    # Sumamos todos los bits encontrados en el mensaje
                    bits_total = sum(int(b) for b in cheer_matches)
                    
                    if data_store.divisa != _('Por defecto'):
                        total_local = exchange.from_bits(bits_total)
                        dinero = f"{total_local} {data_store.divisa}"
                    else:
                        dinero = f"{bits_total} Bits"
                    
                    # Limpiar el mensaje de TODOS los códigos Cheer (insensible a mayúsculas)
                    clean_msg = re.sub(r'cheer\d+', '', msg, flags=re.IGNORECASE).strip()
                    # Si el mensaje queda vacío después de quitar los Cheers, no poner los dos puntos
                    full_donacion = f"{dinero}, {author_name}" + (f": {clean_msg}" if clean_msg else "")
                    
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][3]: 
                        player.play(rutasonidos[3])
                    self.chat_controller.agregar_mensaje_donacion(full_donacion)
                    if data_store.config['reader'] and data_store.config['unread'][3]: 
                        reader.leer_mensaje(full_donacion)
                    continue

                # Regular messages with badges/roles
                message_sent = False
                try:
                    if message['author'].get('is_moderator') and data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                        self.chat_controller.agregar_mensaje_moderador(full_message)
                        if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][4]: player.play(rutasonidos[4])
                        if data_store.config['reader'] and data_store.config['unread'][4]: reader.leer_mensaje(full_message)
                        message_sent = True
                    elif message['author'].get('is_subscriber') and data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                        self.chat_controller.agregar_mensaje_miembro(full_message)
                        if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][1]: player.play(rutasonidos[1])
                        if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(full_message)
                        message_sent = True
                except KeyError: pass
                if message_sent: continue
                if 'badges' in message['author']:
                    for badge in message['author']['badges']:
                        title = badge.get('title', '')
                        if 'Subscriber' in title:
                            if data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][1]: player.play(rutasonidos[1])
                                self.chat_controller.agregar_mensaje_miembro(full_message)
                                if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(full_message)
                            message_sent = True
                            break
                        elif 'Moderator' in title:
                            if data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][4]: player.play(rutasonidos[4])
                                self.chat_controller.agregar_mensaje_moderador(full_message)
                                if data_store.config['reader'] and data_store.config['unread'][4]: reader.leer_mensaje(full_message)
                            message_sent = True
                            break
                        elif 'Verified' in title:
                            if data_store.config['eventos'][5] and data_store.config['categorias'][5] and hasattr(self.chat_controller.ui, 'list_box_verificados'):
                                self.chat_controller.agregar_mensaje_verificado(full_message)
                                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][5]: player.play(rutasonidos[5])
                                if data_store.config['reader'] and data_store.config['unread'][5]: reader.leer_mensaje(full_message)
                            message_sent = True
                            break
                    else:
                        if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                            if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][0]: player.play(rutasonidos[0])
                            self.chat_controller.agregar_mensaje_general(full_message)
                            if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(full_message)
                            message_sent = True
                if message_sent: continue
                # Default to general
                if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                    self.chat_controller.agregar_mensaje_general(full_message)
                    if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][0]: player.play(rutasonidos[0])
                    if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(full_message)
        except Exception as e:
            wx.CallAfter(self.chat_controller.notificar_error, str(e))

