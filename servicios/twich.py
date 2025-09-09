import json, google_currency,threading,re
from chat_downloader import ChatDownloader
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController
from servicios.estadisticas_manager import EstadisticasManager

class ServicioTwich:
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
        self.chat_controller.show()
    def detener(self):
        self._detener = True

    def recibir(self):
        if data_store.dst: self.translator=translator.translatorWrapper()
        self.chat=ChatDownloader().get_chat(self.url,message_groups=["messages", "bits","subscriptions","upgrades"])
        self.chat_controller.agregar_titulo(self.chat.title)
        for message in self.chat:
            if self._detener: break
            if not message: continue

            if message['message'] is None: message['message'] = ''
            if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)

            author_name = message['author'].get('display_name', _('Desconocido'))
            EstadisticasManager().agregar_mensaje(author_name)
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
                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                if data_store.config['reader'] and data_store.config['unread'][2]: reader.leer_mensaje(sub_message)
                continue

            # Cheer/Bits event
            if re.search(r'\bCheer\d+\b', msg) and data_store.config['categorias'][3] and data_store.config['eventos'][3] and hasattr(self.chat_controller.ui, 'list_box_donaciones'):
                divide1=message['message'].split('Cheer')
                if not divide1[0]:
                    if data_store.divisa!=_('Por defecto'): divide1[0]=data_store.divisa
                    else: divide1[0]='Cheer'
                    final_msj=divide1[1].split()
                    if data_store.divisa!=_('Por defecto'):
                        if data_store.divisa=='USD':final_msj[0]=int(final_msj[0])/100
                        else:
                            moneda=json.loads(google_currency.convert('USD',data_store.divisa,int(final_msj[0])/100) )
                            if moneda['converted']: final_msj[0]=moneda['amount']
                    dinero=divide1[0]+str(final_msj[0])
                    if len(final_msj)==1: divide1=''
                    else: divide1=' '.join(final_msj[1:])
                else:
                    if data_store.divisa!=_('Por defecto'):
                        if data_store.divisa=='USD': divide1[1]=int(divide1[1])/100
                        else:
                            moneda=json.loads(google_currency.convert('USD',data_store.divisa,int(divide1[1])/100) )
                            if moneda['converted']: divide1[1]=moneda['amount']
                    if data_store.divisa!=_('Por defecto'): dinero=data_store.divisa+str(divide1[1])
                    else: dinero='Cheer '+str(divide1[1])
                    divide1=' '+divide1[0]
                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][3]: player.playsound(rutasonidos[3],False)
                self.chat_controller.agregar_mensaje_donacion(dinero+', '+author_name+': '+divide1)
                if data_store.config['reader'] and data_store.config['unread'][3]: reader.leer_mensaje(dinero+', '+author_name+': '+divide1)
                continue

            # Regular messages with badges/roles
            message_sent = False
            try:
                if message['author'].get('is_moderator') and data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                    self.chat_controller.agregar_mensaje_moderador(full_message)
                    if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][4]: player.playsound(rutasonidos[4],False)
                    if data_store.config['reader'] and data_store.config['unread'][4]: reader.leer_mensaje(full_message)
                    message_sent = True
                elif message['author'].get('is_subscriber') and data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                    self.chat_controller.agregar_mensaje_miembro(full_message)
                    if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][1]: player.playsound(rutasonidos[1],False)
                    if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(full_message)
                    message_sent = True
            except KeyError: pass
            if message_sent: continue
            if 'badges' in message['author']:
                for badge in message['author']['badges']:
                    title = badge.get('title', '')
                    if 'Subscriber' in title:
                        if data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                            if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][1]: player.playsound(rutasonidos[1],False)
                            self.chat_controller.agregar_mensaje_miembro(full_message)
                            if data_store.config['reader'] and data_store.config['unread'][1]: reader.leer_mensaje(full_message)
                        message_sent = True
                        break
                    elif 'Moderator' in title:
                        if data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                            if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][4]: player.playsound(rutasonidos[4],False)
                            self.chat_controller.agregar_mensaje_moderador(full_message)
                            if data_store.config['reader'] and data_store.config['unread'][4]: reader.leer_mensaje(full_message)
                        message_sent = True
                        break
                    elif 'Verified' in title:
                        if data_store.config['eventos'][5] and data_store.config['categorias'][5] and hasattr(self.chat_controller.ui, 'list_box_verificados'):
                            self.chat_controller.agregar_mensaje_verificado(full_message)
                            if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][5]: player.playsound(rutasonidos[5],False)
                            if data_store.config['reader'] and data_store.config['unread'][5]: reader.leer_mensaje(full_message)
                        message_sent = True
                        break
                else:
                    if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                        if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][0]: player.playsound(rutasonidos[0],False)
                        self.chat_controller.agregar_mensaje_general(full_message)
                        if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(full_message)
                        message_sent = True
            if message_sent: continue
            # Default to general
            if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                self.chat_controller.agregar_mensaje_general(full_message)
                if data_store.config['sonidos'] and self.chat.status!="past" and data_store.config['listasonidos'][0]: player.playsound(rutasonidos[0],False)
                if data_store.config['reader'] and data_store.config['unread'][0]: reader.leer_mensaje(full_message)
