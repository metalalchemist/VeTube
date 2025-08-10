import json, google_currency,threading,re
from chat_downloader import ChatDownloader
from globals.data_store import config, divisa, dst
from globals.resources import rutasonidos
from utils import translator
from setup import player,reader
from controller.chat_controller import ChatController

class ServicioTwich:
    def __init__(self, url, frame, plataforma):
        self.url = url
        self.frame = frame
        self.chat = None
        self.chat_controller = ChatController(frame, self)
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
        if dst: translator=translator.TranslatorWrapper()
        self.chat=ChatDownloader().get_chat(self.url,message_groups=["messages", "bits","subscriptions","upgrades"])
        for message in self.chat:
            if self._detener: break
            if not message: continue
            # Si author existe pero no tiene display_name, asígnalo
            if 'author' in message and isinstance(message['author'], dict) and 'display_name' not in message['author']:
                message['author']['display_name'] = 'Desconocido'
            if message['message'] is None: message['message'] = ''
            if dst: message['message'] = translator.translate(text=message['message'], target=dst)
            if message['message_type']=='resubscription' and config['eventos'][1]:
                self.chat_controller.agregar_mensaje(message['author']['display_name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! '))
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                continue
            if message['message_type']=='subscription' and config['eventos'][1]:
                self.chat_controller.agregar_mensaje(message['author']['display_name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                continue
            if message['message_type']=='mystery_subscription_gift':
                self.chat_controller.agregar_mensaje(message['author']['display_name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                continue
            if message['message_type']=='subscription_gift':
                self.chat_controller.agregar_mensaje(message['author']['display_name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                continue
            if message['message_type']=='resubscription' and config['eventos'][1]:
                mssg=message['message'].split('! ')
                mssg=str(mssg[1:])
                self.chat_controller.agregar_mensaje(message['author']['display_name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][2]: player.playsound(rutasonidos[2],False)
                continue
            if re.search(r'\bCheer\d+\b', message['message']) and config['eventos'][2]:
                divide1=message['message'].split('Cheer')
                if not divide1[0]:
                    if divisa!='Por defecto': divide1[0]=divisa
                    else: divide1[0]='Cheer'
                    final_msj=divide1[1].split()
                    if divisa!='Por defecto':
                        if divisa=='USD':final_msj[0]=int(final_msj[0])/100
                        else:
                            moneda=json.loads(google_currency.convert('USD',divisa,int(final_msj[0])/100) )
                            if moneda['converted']: final_msj[0]=moneda['amount']
                    dinero=divide1[0]+str(final_msj[0])
                    if len(final_msj)==1: divide1=''
                    else: divide1=' '.join(final_msj[1:])
                else:
                    if divisa!='Por defecto':
                        if divisa=='USD': divide1[1]=int(divide1[1])/100
                        else:
                            moneda=json.loads(google_currency.convert('USD',divisa,int(divide1[1])/100) )
                            if moneda['converted']: divide1[1]=moneda['amount']
                    if divisa!='Por defecto': dinero=divisa+str(divide1[1])
                    else: dinero='Cheer '+str(divide1[1])
                    divide1=' '+divide1[0]
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][3]: player.playsound(rutasonidos[3],False)
                self.chat_controller.agregar_mensaje(dinero+', '+message['author']['display_name']+': '+divide1)
                continue
            try:
                if message['author']['is_subscriber'] and config['eventos'][0]:
                    self.chat_controller.agregar_mensaje(message['author']['display_name']+': '+message['message'])
                    if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][1]: player.playsound(rutasonidos[1],False)
                    continue
                elif message['author']['is_moderator'] and config['eventos'][3]:
                    self.chat_controller.agregar_mensaje(message['author']['display_name']+': '+message['message'])
                    if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][4]: player.playsound(rutasonidos[4],False)
                    continue
            except KeyError: pass #these keys not  exists in a past live status.
            if 'badges' in message['author']:
                for t in message['author']['badges']:
                    if 'Subscriber' in t['title'] and config['eventos'][0]:
                        if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][1]: player.playsound(rutasonidos[1],False)
                        self.chat_controller.agregar_mensaje(message['author']['display_name']+': '+message['message'])
                        break
                    elif 'Moderator' in t['title'] and config['eventos'][3]:
                        if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][4]: player.playsound(rutasonidos[4],False)
                        self.chat_controller.agregar_mensaje(message['author']['display_name']+': '+message['message'])
                        break
                    elif 'Verified' in t['title'] and config['eventos'][4]:
                        if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][5]: player.playsound(rutasonidos[5],False)
                        self.chat_controller.agregar_mensaje(message['author']['display_name']+': '+message['message'])
                        break
                else:
                    if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][0]: player.playsound(rutasonidos[0],False)
                    self.chat_controller.agregar_mensaje(message['author']['display_name'] +': ' +message['message'])
                continue
            else:
                if config['sonidos'] and self.chat.status!="past" and config['listasonidos'][0]: player.playsound(rutasonidos[0],False)
                self.chat_controller.agregar_mensaje(message['author']['display_name'] +': ' +message['message'])
                continue