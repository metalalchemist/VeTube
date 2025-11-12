import json, google_currency,threading,wx
from chat_downloader import ChatDownloader
from globals import data_store
from globals.resources import rutasonidos
from utils import translator
from utils.play_mp4 import extract_stream_url
from setup import player,reader
from controller.chat_controller import ChatController
from controller.media_controller import MediaController
from servicios.estadisticas_manager import EstadisticasManager

class ServicioYouTube:
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
        # Primero, liberar el reproductor de medios
        if self.media_controller:
            self.media_controller.release()
            self.media_controller = None # Importante para evitar referencias a objetos liberados

        # Ya no esperamos al hilo de recepción de chat aquí para evitar bloquear la interfaz.
        # Confiamos en que el flag _detener y el break del bucle sean suficientes.

        # Finalmente, limpiar el objeto chat si es necesario
        self.chat = None # Eliminar la referencia al objeto ChatDownloader

    def do_switch(self, title):
        from servicios.YouTubeRealDataTime import YouTubeRealTimeService
        realtime_service = YouTubeRealTimeService(self.url, self.frame, 'youtube_realtime', title=title, chat_controller=self.chat_controller)
        realtime_service.iniciar_chat_reutilizando_ui()
        self.chat_controller.set_active_service(realtime_service)

    def prepare_player(self, status):
        try:
            format_pref = 'mp4' if status == "past" else 'best'
            video_url = extract_stream_url(self.url, format_preference=format_pref)
            if video_url:
                self.media_controller = MediaController(url=video_url, state_callback=self.chat_controller.chat_dialog.on_media_player_state_change)
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error al iniciar la reproducción de video en YouTube: {e}")

    def recibir(self):
        if data_store.dst: self.translator=translator.translatorWrapper()
        self.chat = ChatDownloader().get_chat(self.url, message_groups=["messages", "superchat"], interruptible_retry=False)
        if self.chat.status == 'past':
            dialog = wx.MessageDialog(self.chat_controller.ui, _("Se ha detectado una transmisión pasada. ¿Deseas conectarte con el servicio en tiempo real del chat?"), _("Transmisión pasada"), wx.YES_NO | wx.ICON_QUESTION)
            result = dialog.ShowModal()
            if result == wx.ID_YES:
                self.detener()
                wx.CallAfter(self.do_switch, self.chat.title)
                return
        threading.Thread(target=self.prepare_player, args=(self.chat.status,), daemon=True).start()
        wx.CallAfter(self.chat_controller.chat_dialog.update_chat_page_title, self.chat_controller, self.chat.title)
        for message in self.chat:
            if self._detener: break
            if not message: continue
            if message['message'] is None: message['message'] = ''
            if data_store.dst: message['message'] = self.translator.translate(text=message['message'], target=data_store.dst)

            author_name = message['author']['display_name']
            self.estadisticas_manager.agregar_mensaje(author_name)
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
                if data_store.config['eventos'][2] and data_store.config['categorias'][1] and hasattr(self.chat_controller.ui, 'list_box_eventos'):
                    for t in message['author']['badges']:
                        mensajito=author_name+ _(' se a conectado al chat. ')+t['title']
                        break
                    wx.CallAfter(self.chat_controller.agregar_mensaje_evento, mensajito)
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][2]: player.play(rutasonidos[2])
                    if data_store.config['reader'] and data_store.config['unread'][2]: wx.CallAfter(reader.leer_mensaje, mensajito)
                continue
            # Construct the message string
            if message_type == 'donacion':
                if data_store.config['eventos'][3] and data_store.config['categorias'][3] and hasattr(self.chat_controller.ui, 'list_box_donaciones'):
                    if data_store.divisa != "Por defecto" and data_store.divisa != message['money']['currency']:
                        moneda = json.loads(google_currency.convert(message['money']['currency'], data_store.divisa, message['money']['amount']))
                        if moneda['converted']:
                            message['money']['currency'] = data_store.divisa
                            message['money']['amount'] = moneda['amount']
                    full_message = f"{message['money']['amount']} {message['money']['currency']}, {author_name}: {msg}"
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][3]: player.play(rutasonidos[3])
                    wx.CallAfter(self.chat_controller.agregar_mensaje_donacion, full_message)
                    if data_store.config['reader'] and data_store.config['unread'][3]: wx.CallAfter(reader.leer_mensaje, full_message)
                continue

            full_message = f"{author_name}: {msg}"

            if message_type == 'general':
                if data_store.config['eventos'][0] and data_store.config['categorias'][0] and hasattr(self.chat_controller.ui, 'list_box_general'):
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][0]: player.play(rutasonidos[0])
                    wx.CallAfter(self.chat_controller.agregar_mensaje_general, full_message)
                    if data_store.config['reader'] and data_store.config['unread'][0]: wx.CallAfter(reader.leer_mensaje, full_message)
            elif message_type == 'miembro':
                if data_store.config['eventos'][1] and data_store.config['categorias'][2] and hasattr(self.chat_controller.ui, 'list_box_miembros'):
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][1]: player.play(rutasonidos[1])
                    wx.CallAfter(self.chat_controller.agregar_mensaje_miembro, full_message)
                    if data_store.config['reader'] and data_store.config['unread'][1]: wx.CallAfter(reader.leer_mensaje, full_message)
            elif message_type == 'moderador' or message_type=='propietario':
                if data_store.config['eventos'][4] and data_store.config['categorias'][4] and hasattr(self.chat_controller.ui, 'list_box_moderadores'):
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][4]:
                        if message_type=='moderador': player.play(rutasonidos[4])
                        if message_type=='propietario': player.play(rutasonidos[7])
                    wx.CallAfter(self.chat_controller.agregar_mensaje_moderador, full_message)
                    if data_store.config['reader'] and data_store.config['unread'][4]: wx.CallAfter(reader.leer_mensaje, full_message)
            elif message_type == 'verificado':
                if data_store.config['eventos'][5] and data_store.config['categorias'][5] and hasattr(self.chat_controller.ui, 'list_box_verificados'):
                    if data_store.config['sonidos'] and self.chat.status != "past" and data_store.config['listasonidos'][5]: player.play(rutasonidos[5])
                    wx.CallAfter(self.chat_controller.agregar_mensaje_verificado, f"{author_name}: {msg}")
                    if data_store.config['reader'] and data_store.config['unread'][5]: wx.CallAfter(reader.leer_mensaje, f'{author_name}: {msg}')