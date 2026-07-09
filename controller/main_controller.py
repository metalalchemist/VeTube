import wx
from globals.data_store import favorite, mensajes_destacados, favs, msjs,config
from ui.main_window import MyFrame, PLATAFORMAS
from os import remove
from utils import languageHandler,canonical_scraper,funciones,fajustes
from controller.menus.main_menu_controller import MainMenuController
from controller.chat_dialog_controller import ChatDialogController
from servicios.youtube import ServicioYouTube
from servicios.twich import ServicioTwich
from servicios.sala import ServicioSala
from servicios.tiktok import ServicioTiktok
from servicios.kick import ServicioKick # Importar ServicioKick
from servicios.discord import ServicioDiscord, extraer_id_canal, validar_token
from ui.dialog_response import response
from setup import reader,network
from controller.chat_controller import ChatController
from controller.editor_controller import EditorController

class MainController:
    def __init__(self):
        self.frame = MyFrame(None)
        self.menu_controller = MainMenuController(self.frame, self)
        self.chat_dialog = None # Initialize ChatDialog instance here
        self.inicializar_datos()
        self.establecer_eventos()
        self.procesando_url = False
        
        # Iniciar la secuencia de comprobaciones al arrancar la app
        wx.CallAfter(self.iniciar_secuencia_arranque)

    def iniciar_secuencia_arranque(self):
        # 1. Verificar e instalar voces si es necesario
        if config.get('sistemaTTS') == "piper":
            self.verificar_piper_inicio()
        
        # 2. Comprobar actualizaciones en segundo plano de forma segura
        if config.get('updates', False):
            from update import updater
            updater.do_update()

    def verificar_piper_inicio(self):
        from TTS.lector import detect_onnx_models
        from globals.resources import carpeta_voces
        onnx_models = detect_onnx_models(carpeta_voces)
        if onnx_models is None:
            if response(_('Necesitas al menos una voz para poder usar el sintetizador Piper. ¿Deseas abrir el descargador de voces ahora para buscar e instalar una?'), _("No hay voces instaladas"), wx.YES_NO | wx.ICON_ASTERISK) == wx.ID_YES:
                from controller.piper_downloader_controller import PiperDownloaderController
                downloader = PiperDownloaderController(self.frame)
                downloader.show()
                
                # Después de cerrar el descargador, verificamos si instaló alguna voz
                nuevas_voces = detect_onnx_models(carpeta_voces)
                if nuevas_voces is not None:
                    from TTS.list_voices import piper_list_voices, obtener_ruta_voz
                    from globals.resources import lista_voces_piper
                    import setup
                    
                    # Refrescamos la lista de voces global
                    lista_voces_piper.clear()
                    lista_voces_piper.extend(piper_list_voices())
                    
                    # Seleccionamos la primera por defecto
                    config['voz'] = 0
                    model_path = obtener_ruta_voz(lista_voces_piper[0])
                    
                    # Inicializamos y cargamos el modelo en el lector
                    setup.reader._lector = setup.reader._lector.piperSpeak(model_path)
                    
                    # Sincronizamos el dispositivo de salida de Piper
                    nombres_dispositivos = setup.player.devicenames
                    dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres_dispositivos)]
                    nombre_actual = nombres_dispositivos[config["dispositivo"]-1]
                    salida_actual = setup.reader._lector.find_device_id(nombre_actual, known_devices=dispositivos_formateados)
                    setup.reader._lector.set_device(salida_actual)
                    
                    # Damos la bienvenida para confirmar que ya funciona
                    setup.reader.leer_auto(_("Lector Piper inicializado correctamente."))
    def inicializar_datos(self):
        self.frame.list_favorite.Set(favs)
        self.frame.favoritos_num = self.frame.list_favorite.GetCount()
        self.frame.notebook_1.SetPageText(1, _( "Favoritos(%s)") % self.frame.favoritos_num)
        if not favs or self.frame.list_favorite.GetCount() == 0:
            self.frame.list_favorite.Append(_( "Tus favoritos aparecerán aquí"), 0)
        self.frame.list_mensajes.Set(msjs)
        if not self.frame.list_mensajes.GetCount():
            self.frame.list_mensajes.Append(_("Tus mensajes archivados aparecerán aquí"), 0)

    def establecer_eventos(self):
        self.frame.menu_1.Bind(wx.EVT_BUTTON, lambda evt: self.menu_controller.menu.mostrar(self.frame.menu_1))
        self.frame.text_ctrl_1.Bind(wx.EVT_TEXT, self.mostrarBoton)
        self.frame.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
        self.frame.button_borrar_favoritos.Bind(wx.EVT_BUTTON, self.borrarFavorito)
        self.frame.borrar_todos_favs.Bind(wx.EVT_CHECKBOX, self.borrarTodosFavoritos)
        self.frame.check_borrar_todos.Bind(wx.EVT_CHECKBOX, self.seleccionarTodos)
        self.frame.button_borrar_mensajes.Bind(wx.EVT_BUTTON, self.borraRecuerdo)
        self.frame.button_1.Bind(wx.EVT_BUTTON, self.abrir_chat_dialog)
        self.frame.plataforma.Bind(wx.EVT_CHOICE, self.habilitarSala)
        self.frame.Bind(wx.EVT_CHAR_HOOK, self.OnCharHook)
        self.frame.list_favorite.Bind(wx.EVT_KEY_UP, self.on_favorite_key_up)
        self.frame.Bind(wx.EVT_CLOSE, self.cerrarVentana)

    def mostrarBoton(self, event):
        if self.frame.text_ctrl_1.GetValue() != "":
            self.frame.button_1.Enable()
            self.frame.button_2.Enable()
        else:
            self.frame.button_1.Disable()
            self.frame.button_2.Disable()

    def borrarContenido(self, event):
        self.frame.text_ctrl_1.SetValue("")
        self.frame.text_ctrl_1.SetFocus()

    def borrarFavorito(self, event=None):
        lf = self.frame.list_favorite
        if lf.GetCount() <= 0 or lf.GetStrings()[0] == _( "Tus favoritos aparecerán aquí"):
            wx.MessageBox(_( "No hay favoritos que borrar"), _( "Error"), wx.ICON_ERROR)
            lf.SetFocus()
        else:
            if self.frame.borrar_todos_favs.GetValue():
                if wx.MessageBox(_( "¿Estás seguro de borrar todos los favoritos de la lista?"), _( "¡Atención!"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    lf.Clear()
                    favorite.clear()
                    remove('favoritos.json')
                    lf.SetFocus()
            else:
                sel = lf.GetSelection()
                lf.Delete(sel)
                favorite.pop(sel)
                funciones.escribirJsonLista('favoritos.json', favorite)
                lf.SetFocus()
        if lf.GetCount() <= 0:
            lf.Append(_( "Tus favoritos aparecerán aquí"))

    def seleccionarTodos(self, event):
        if self.frame.check_borrar_todos.GetValue():
            self.frame.button_borrar_mensajes.SetLabel(_("&Borrar mensajes"))
            self.frame.button_borrar_mensajes.SetToolTip(_("Borrar todos los mensajes destacados"))
            self.frame.button_borrar_mensajes.SetFocus()
        else:
            self.frame.button_borrar_mensajes.SetLabel(_("&Borrar mensaje"))
            self.frame.button_borrar_mensajes.SetToolTip(_("Borrar el mensaje destacado seleccionado"))
            self.frame.button_borrar_mensajes.SetFocus()

    def borrarTodosFavoritos(self, event):
        if self.frame.borrar_todos_favs.GetValue():
            self.frame.button_borrar_favoritos.SetLabel(_("&Borrar favoritos"))
            self.frame.button_borrar_favoritos.SetToolTip(_("Borrar todos los favoritos"))
            self.frame.button_borrar_favoritos.SetFocus()
        else:
            self.frame.button_borrar_favoritos.SetLabel(_("&Borrar favorito"))
            self.frame.button_borrar_favoritos.SetToolTip(_("Borrar el favorito seleccionado"))
            self.frame.button_borrar_favoritos.SetFocus()

    def borraRecuerdo(self, event):
        lf = self.frame.list_mensajes
        if not self.frame.check_borrar_todos.GetValue():
            if not lf.GetStrings()[0] == _( "Tus mensajes archivados aparecerán aquí"):
                if len(mensajes_destacados) > 0:
                    sel = lf.GetSelection()
                    lf.Delete(sel)
                    mensajes_destacados.pop(sel)
                    funciones.escribirJsonLista('mensajes_destacados.json', mensajes_destacados)
                    lf.SetFocus()
                else:
                    wx.MessageBox(_( "No hay más elementos que borrar"), "Error.", wx.ICON_ERROR)
            else:
                wx.MessageBox(_( "No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
                lf.SetFocus()
            if lf.GetCount() <= 0:
                lf.Append(_( "Tus mensajes archivados aparecerán aquí"))
        else:
            if len(mensajes_destacados) > 0:
                if wx.MessageBox(_( "¿Estás seguro de que quieres borrar todos los mensajes?"), "Confirmación", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    mensajes_destacados.clear()
                    remove('mensajes_destacados.json')
                    lf.Clear()
                    lf.Append(_( "Tus mensajes archivados aparecerán aquí"))
                    lf.SetFocus()
            elif len(mensajes_destacados) <= 0:
                wx.MessageBox(_( "No hay mensajes que borrar"), "Error.", wx.ICON_ERROR)
                lf.SetFocus()

    def abrir_chat_dialog(self, event=None, url=""):
        if self.procesando_url:
            return
            
        if not url:
            url = self.frame.text_ctrl_1.GetValue()
        
        if url:
            # Si es TikTok y necesita simplificación, lo manejamos de forma asíncrona
            if 'vm.tiktok' in url or 'vt.tiktok' in url or 'v.tiktok' in url or 'tiktok.com/t/' in url:
                self.procesando_url = True
                wx.BeginBusyCursor()

                def handle_tiktok_result(result):
                    if isinstance(result, Exception):
                        wx.MessageBox(_("Error al simplificar URL de TikTok: {}").format(result), _("Error"), wx.ICON_ERROR)
                    elif result:
                        self._continuar_abriendo_chat(result)
                    else:
                        wx.MessageBox(_("No se pudo obtener la URL real de TikTok."), _("Error"), wx.ICON_ERROR)
                    
                    # Liberamos el cerrojo y restauramos el cursor al final de todo
                    self.procesando_url = False
                    wx.EndBusyCursor()

                network.execute(canonical_scraper.get_simplified_tiktok_live_url(url), callback=handle_tiktok_result)
            else:
                self._continuar_abriendo_chat(url)
        else:
            wx.MessageBox(_("No se puede acceder porque el campo de texto está vacío, debe escribir algo."), _("Error"), wx.ICON_ERROR)
            self.frame.text_ctrl_1.SetFocus()

    def _continuar_abriendo_chat(self, url):
        # Check if chat dialog exists, if not create it
        if not self.chat_dialog:
            self.chat_dialog = ChatDialogController(self.frame, self)

        # Check if session already exists in chat_dialog
        if url in self.chat_dialog.chat_sessions:
            # Find the page index and set selection
            page_index = self.chat_dialog.chat_sessions[url][1]
            self.chat_dialog.view.notebook.SetSelection(page_index)
            self.chat_dialog.view.Show()
            self.chat_dialog.view.Raise()
            self.chat_dialog.active_chat_session = self.chat_dialog.chat_sessions[url][0]
            self.frame.text_ctrl_1.SetValue("")
            return

        plataforma_ids = self.frame.plataforma.GetSelection()
        if plataforma_ids == 4:
            url = "sala"
        
        autodetectar = False if plataforma_ids != 0 else True
        if 'http' in url or 'www' in url:
            autodetectar = True
        
        # Si no autodetecta, construye la URL basada en la plataforma seleccionada y el texto actual
        if not autodetectar:
            # Quita el arroba si el usuario lo escribió con el nombre; el código ya lo añade donde hace falta
            url = url.lstrip('@')
            if plataforma_ids == 1:
                url = "https://www.youtube.com/@" + url + "/live"
            elif plataforma_ids == 2:
                url = "https://www.twitch.tv/" + url
            elif plataforma_ids == 3:
                url = "https://www.tiktok.com/@" + url + "/live"
            elif plataforma_ids == 5: # Nuevo: Kick
                url = "https://www.kick.com/" + url
            elif plataforma_ids == 6: # Discord: no hay URL construible, se necesita el enlace del canal
                wx.MessageBox(_("Para Discord pega el enlace del canal de texto: haz clic derecho sobre el canal y elige «Copiar enlace»."), _("Error"), wx.ICON_ERROR)
                self.frame.text_ctrl_1.SetFocus()
                return
        
        if 'yout' in url:
            if 'studio' in url:
                url = url.replace('https://studio.youtube.com/video/','https://www.youtube.com/watch?v=')
                url = url.replace('/livestreaming','/')
            if 'live' in url:
                url = url.replace('live/','watch?v=')
            self.set_plataforma(1)
        elif 'twitch' in url:
            self.set_plataforma(2)
        elif 'tiktok' in url:
            self.set_plataforma(3)
        elif "sala" in url:
            self.set_plataforma(4)
        elif 'kick' in url: # Nuevo: Detección de URL para Kick
            self.set_plataforma(5)
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            if path_parts:
                url = path_parts[-1]
            else:
                url = self.frame.text_ctrl_1.GetValue()

        elif 'discord' in url: # Detección de URL para Discord
            if not extraer_id_canal(url):
                wx.MessageBox(_("El enlace de Discord no es válido. Copia el enlace del canal de texto (clic derecho sobre el canal, «Copiar enlace») y pégalo en VeTube."), _("Error"), wx.ICON_ERROR)
                self.frame.text_ctrl_1.SetFocus()
                return
            self.set_plataforma(6)
            # El enlace completo identifica la sesión (así favoritos y «copiar
            # enlace» funcionan); el servicio extrae de él el id del canal.
            if not config.get('discord_token', ''):
                self._pedir_token_discord(url)
                return
        else:
            wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), _("Error"), wx.ICON_ERROR)
            self.frame.text_ctrl_1.SetFocus()
            return
        
        self.frame.text_ctrl_1.SetValue(url)
        plataforma_ids = self.frame.plataforma.GetSelection()
        # Identificador interno, no la etiqueta traducida del wx.Choice: con la
        # interfaz en otro idioma la etiqueta no coincide con las comparaciones
        # del código (p. ej. == 'La sala de juegos') y la plataforma se trata
        # como genérica.
        plataforma = PLATAFORMAS[plataforma_ids]
        
        # Create ChatController first
        chat_controller = ChatController(self, self.frame, plataforma=plataforma, chat_dialog=self.chat_dialog)

        servicio = None
        try:
            if plataforma_ids == 1:
                servicio = ServicioYouTube(self, url, self.frame, plataforma, chat_controller)
            elif plataforma_ids == 2:
                servicio = ServicioTwich(self, url, self.frame, plataforma, chat_controller)
            elif plataforma_ids == 3:
                servicio = ServicioTiktok(self, url, self.frame, plataforma, chat_controller)
            elif plataforma_ids == 4:
                servicio = ServicioSala(self, url, self.frame, plataforma, chat_controller)
            elif plataforma_ids == 5: # Nuevo: Instanciar ServicioKick
                servicio = ServicioKick(self, url, self.frame, plataforma, chat_controller)
            elif plataforma_ids == 6: # Discord (el token ya quedó validado en la detección del enlace)
                servicio = ServicioDiscord(self, url, self.frame, plataforma, chat_controller)

            if servicio:
                chat_controller.servicio = servicio # Set the service in chat_controller
                servicio.iniciar_chat()
                chat_controller.create_ui(self.chat_dialog.view.notebook)
                chat_panel = chat_controller.mostrar_dialogo() # This now returns a ChatPanel instance
                self.chat_dialog.add_chat_page(chat_panel, _("Conectando..."), chat_controller) # Add panel to ChatDialog
                self.chat_dialog.view.Show() # Show the chat dialog
                self.chat_dialog.view.Raise() # Bring to front
                self.frame.menu_1.Disable() # Deshabilitar botón
                self.frame.text_ctrl_1.SetValue("")

        except Exception as e:
            wx.MessageBox(f"Error al iniciar el chat: {str(e)}", "error.", wx.ICON_ERROR)
            self.frame.text_ctrl_1.SetFocus()
            return

    def mostrar_editor_combinaciones(self, event=None):
        parent = self.frame  # Padre por defecto es la ventana principal
        if self.chat_dialog and self.chat_dialog.view.IsShown():
            parent = self.chat_dialog.view # Si el chat dialog está visible, él es el padre
        
        editor = EditorController(parent, self)
        editor.ShowModal()

    def reload_shortcuts(self):
        if self.chat_dialog and self.chat_dialog.activo:
            self.chat_dialog.reiniciar_atajos_teclado()

    def OnCharHook(self, event):
        code = event.GetKeyCode()
        if code == 77 and event.AltDown():
            # Solo mostrar el menú si no hay sesiones de chat cargadas
            if not (self.chat_dialog and self.chat_dialog.chat_sessions):
                self.menu_controller.menu.mostrar(self.frame.menu_1)
        elif wx.GetKeyState(wx.WXK_F1):
            wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube/tree/master/doc/'+languageHandler.curLang[:2]+'/readme.md')
        elif code == wx.WXK_RETURN or code == wx.WXK_NUMPAD_ENTER:
            if self.frame.FindFocus()== self.frame.plataforma or self.frame.FindFocus()==self.frame.text_ctrl_1: self.abrir_chat_dialog()
        else:
            event.Skip()

    def set_plataforma(self, idx):
        self.frame.plataforma.SetSelection(idx)

    def _pedir_token_discord(self, url):
        """Pide el token del bot con el diálogo y lo valida contra la API de
        Discord SIN bloquear la interfaz: la comprobación corre en el hilo de
        red (network.execute) y el resultado vuelve al hilo de la UI. Si el
        token es válido se guarda en data.json y se retoma la apertura del
        chat con el mismo enlace."""
        from ui.discord_token_dialog import DiscordTokenDialog
        dlg = DiscordTokenDialog(self.frame)
        resultado = dlg.ShowModal()
        token = dlg.get_token()
        dlg.Destroy()
        if resultado != wx.ID_OK:
            self.set_plataforma(0)
            self.frame.text_ctrl_1.SetFocus()
            return
        wx.BeginBusyCursor()

        def al_validar(valido):
            wx.EndBusyCursor()
            if valido is True:
                config['discord_token'] = token
                fajustes.guardarConfiguracion(config)
                self._continuar_abriendo_chat(url)
                return
            if valido is False:
                wx.MessageBox(_("El token no es válido. Comprueba que lo copiaste completo desde el portal de desarrolladores de Discord."), _("Error"), wx.ICON_ERROR)
            else: # None o excepción: fallo de red
                wx.MessageBox(_("No se pudo comprobar el token por un fallo de red. Revisa tu conexión a internet e inténtalo de nuevo."), _("Error"), wx.ICON_ERROR)
            self._pedir_token_discord(url)

        network.execute(validar_token(token), callback=al_validar)

    def on_favorite_key_up(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            sel = self.frame.list_favorite.GetSelection()
            if sel != -1:
                texto = self.frame.list_favorite.GetString(sel)
                if 'tus favoritos aparecerán aquí' in texto.lower():
                    return
                self.abrir_chat_dialog(url=favorite[sel]['url'])
        else:
            event.Skip()

    def habilitarSala(self, evt):
        if evt.GetSelection() == 4:
            self.frame.button_1.Enable()

    def close(self):
        """Cierre centralizado de recursos (TTS, Chats, Servicios)."""
        # 1. Cerrar el lector (Sonata, etc)
        try:
            reader.close()
        except:
            pass
        
        # 2. Cerrar diálogos de chat y sus servicios (Kick bypass, etc)
        if self.chat_dialog:
            try:
                self.chat_dialog.keyboard_handler.unregister_all_keys()
                for url, (controller, page_index) in list(self.chat_dialog.chat_sessions.items()):
                    if controller.servicio:
                        try:
                            controller.servicio.detener()
                        except:
                            pass
            except:
                pass

    def cerrarVentana(self, event):
        if config['salir']:
            if response(_("¿está seguro que desea salir del programa?"), _("¡atención!"))==wx.ID_YES:
                self.close()
                wx.GetApp().ExitMainLoop()
        else:
            self.close()
            wx.GetApp().ExitMainLoop()
