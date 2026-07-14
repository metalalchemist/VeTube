from globals.data_store import config
from globals.resources import rutasonidos,lista_voces,lista_voces_piper,recargar_rutasonidos
from setup import player,reader
from utils import app_utilitys
from TTS.list_voices import piper_list_voices , install_piper_voice
from controller.piper_downloader_controller import PiperDownloaderController
from utils.menu_accesible import Accesible
import wx
class AjustesController:
    def __init__(self, dialog):
        self.dialog = dialog
        self.dialog.instala_voces.SetAccessible(Accesible(self.dialog.instala_voces))
        
        self.play_timer = wx.Timer(self.dialog)
        self.dialog.Bind(wx.EVT_TIMER, self.on_check_play_status, self.play_timer)
        self.reproduciendo_prueba = False
        self.dialog.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        
        self._bind_events()
        self.actualizar_visibilidad_piper()
        # Cargamos la lista de voces correcta al iniciar
        self.dialog.choice_2.Clear()
        if config['sistemaTTS'] == "piper":
            self.dialog.choice_2.AppendItems(lista_voces_piper)
        else:
            voces = reader._lector.list_voices()
            if not voces:
                voces = [_("Controlado por el lector de pantalla")]
            self.dialog.choice_2.AppendItems(voces)
        self.actualizar_habilitacion_controles()
        try:
            self.dialog.choice_2.SetSelection(config['voz'])
        except:
            self.dialog.choice_2.SetSelection(0)
            config['voz'] = 0
        
        # Sincronización inicial de parámetros
        if config['sistemaTTS'] == "piper":
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            # Aplicamos la velocidad inicial usando la escala correcta
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
        elif config['sistemaTTS'] == "onecore":
            reader._lector.set_volume(config['volume'])
            reader._lector.set_rate(config['speed'])
            # Aplicar el tono guardado para OneCore (posición 0-4, por defecto 0.6 = 0.6)
            reader._lector.set_pitch(config.get('tono_onecore', 0.6))
    def _bind_events(self):
        self.dialog.check_1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar_sapi(event))
        self.dialog.chk1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'reader'))
        self.dialog.check_traduccion.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'traducir'))
        self.dialog.check_interface.Bind(wx.EVT_CHECKBOX, self.on_check_interface)
        self.dialog.check_actualizaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'updates'))
        self.dialog.check_salir.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'salir'))
        self.dialog.check_donaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'donations'))
        self.dialog.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
        self.dialog.lista_temas.Bind(wx.EVT_CHOICE, self.cambiar_tema_sonidos)
        self.dialog.reproducir.Bind(wx.EVT_BUTTON, lambda event: player.play(rutasonidos[self.dialog.soniditos.GetFocusedItem()]))
        self.dialog.seleccionar_TTS.Bind(wx.EVT_CHOICE, self.cambiar_sintetizador)
        self.dialog.establecer_dispositivo.Bind(wx.EVT_BUTTON, self.establecer_dispositivo)
        self.dialog.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
        self.dialog.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
        self.dialog.slider_2.Bind(wx.EVT_SLIDER, self.cambiarVolumen)
        self.dialog.slider_1.Bind(wx.EVT_SLIDER, self.cambiarTono)
        self.dialog.slider_3.Bind(wx.EVT_SLIDER, self.cambiarVelocidad)
        self.dialog.instala_voces.Bind(wx.EVT_BUTTON, self.instalar_voz_piper)
        self.dialog.check_reproducir.Bind(wx.EVT_CHECKBOX, self.on_check_reproducir)
        self.dialog.spin_tiempo.Bind(wx.EVT_SPINCTRL, self.on_spin_tiempo)
        self.dialog.slider_volumen_reproductor.Bind(wx.EVT_SLIDER, self.on_slider_volumen_reproductor)
        self.dialog.slider_cambiovolumen.Bind(wx.EVT_SLIDER, self.on_slider_cambiovolumen)

    def on_slider_cambiovolumen(self, event):
        config['cambiovolumen'] = event.GetEventObject().GetValue()

    def on_check_interface(self, event):
        config['interface'] = event.IsChecked()

    def on_check_reproducir(self, event):
        config['reproducir'] = event.IsChecked()

    def on_spin_tiempo(self, event):
        config['tiempo'] = event.GetEventObject().GetValue()

    def on_slider_volumen_reproductor(self, event):
        config['volumen'] = event.GetEventObject().GetValue()

    def mostrarSonidos(self, event):
        if event.IsChecked():
            config['sonidos'] = True
            self.dialog.soniditos.Enable()
            self.dialog.reproducir.Enable()
        else:
            config['sonidos'] = False
            self.dialog.soniditos.Disable()
            self.dialog.reproducir.Disable()

    def cambiar_tema_sonidos(self, event):
        config['directorio'] = self.dialog.lista_temas.GetStringSelection()
        recargar_rutasonidos()
        if config['sonidos']: player.play(rutasonidos[0])

    def checar(self, event, key):
        config[key] = True if event.IsChecked() else False

    def checar_sapi(self, event):
        config['sapi'] = True if event.IsChecked() else False
        self.dialog.seleccionar_TTS.Enable(not event.IsChecked())
        self.actualizar_visibilidad_piper()

    def cambiar_sintetizador(self, event):
        if self.play_timer.IsRunning():
            self.play_timer.Stop()
        reader._lector.silence()
        self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
        self.reproduciendo_prueba = False

        config['sistemaTTS'] = self.dialog.seleccionar_TTS.GetStringSelection()
        reader.set_tts(config['sistemaTTS'])
        self.dialog.choice_2.Clear()
        if config['sistemaTTS'] == "piper":
            if lista_voces_piper and lista_voces_piper[0] != 'No hay voces instaladas':
                voz_index = config.get('voz', 0)
                if voz_index >= len(lista_voces_piper):
                    voz_index = 0
                    config['voz'] = 0
                from TTS.list_voices import obtener_ruta_voz
                model_path = obtener_ruta_voz(lista_voces_piper[voz_index])
                reader._lector.load_model(model_path)
            self.dialog.choice_2.AppendItems(lista_voces_piper)
            # Sincronizar volumen, tono y velocidad de Piper
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
        else:
            voces = reader._lector.list_voices()
            if not voces:
                voces = [_("Controlado por el lector de pantalla")]
            self.dialog.choice_2.AppendItems(voces)
            
            # Sincronizar volumen, tono y velocidad para SAPI/OneCore
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            reader._lector.set_rate(config['speed'])
            
            # Sincronizar voz para SAPI/OneCore
            if voces and voces[0] != _("Controlado por el lector de pantalla"):
                voz_index = config.get('voz', 0)
                if voz_index >= len(voces):
                    voz_index = 0
                    config['voz'] = 0
                reader._lector.set_voice(voces[voz_index])
                
        self.actualizar_visibilidad_piper()
        self.actualizar_habilitacion_controles()
        try:
            self.dialog.choice_2.SetSelection(config['voz'])
        except:
            self.dialog.choice_2.SetSelection(0)
            config['voz'] = 0

    def actualizar_visibilidad_piper(self):
        show = not config['sapi'] and config['sistemaTTS'] == "piper"
        self.dialog.instala_voces.Show(show)
        # Aseguramos que los controles de tono y volumen estén habilitados siempre
        self.dialog.slider_1.Enable()
        self.dialog.slider_2.Enable()
        self.dialog.treeItem_2.Layout()

    def actualizar_habilitacion_controles(self):
        if config['sistemaTTS'] == "piper":
            # Restaurar slider de tono al rango normal si venía de OneCore
            if self.dialog.slider_1.GetMax() == 4:
                self.dialog.slider_1.SetRange(0, 20)
                self.dialog.slider_1.SetValue(config['tono'] + 10)
            self.dialog.slider_1.Enable(True)
            self.dialog.slider_2.Enable(True)
            self.dialog.slider_3.Enable(True)
            self.dialog.choice_2.Enable(True)
        elif config['sistemaTTS'] == "onecore":
            # OneCore: pitch limitado a 5 valores discretos: 0.6, 0.7, 0.8, 0.9, 1.0
            # Slider rango 0-4 donde cada paso = 0.1 en la escala real de OneCore
            self.dialog.slider_1.SetRange(0, 4)
            # Por defecto posición 0.6 = 0.6, el tono más natural en OneCore
            pos_onecore = config.get('tono_onecore', 0.6)  # 0.6 = 0.6 (tono más natural)
            self.dialog.slider_1.SetValue(pos_onecore)
            # Aplicar el pitch inmediatamente al lector
            reader._lector.set_pitch(pos_onecore)
            self.dialog.slider_1.Enable(True)
            self.dialog.slider_2.Enable(True)
            self.dialog.slider_3.Enable(True)
            self.dialog.choice_2.Enable(True)
        else:
            # Restaurar slider de tono al rango normal si venía de OneCore
            if self.dialog.slider_1.GetMax() == 4:
                self.dialog.slider_1.SetRange(0, 20)
                self.dialog.slider_1.SetValue(config['tono'] + 10)
            has_backend = hasattr(reader._lector, 'backend')
            features = reader._lector.backend.features if has_backend else None
            if features:
                self.dialog.slider_1.Enable(features.supports_set_pitch)
                self.dialog.slider_2.Enable(features.supports_set_volume)
                self.dialog.slider_3.Enable(features.supports_set_rate)
                self.dialog.choice_2.Enable(features.supports_set_voice)
            else:
                self.dialog.slider_1.Enable(True)
                self.dialog.slider_2.Enable(True)
                self.dialog.slider_3.Enable(True)
                self.dialog.choice_2.Enable(True)

    def establecer_dispositivo(self, event):
        valor = self.dialog.lista_dispositivos.GetSelection() + 1
        valor_str = self.dialog.lista_dispositivos.GetStringSelection()
        config['dispositivo'] = valor
        player.setdevice(config["dispositivo"])
        player.play(f"sounds/{config['directorio']}/cambiardispositivo.mp3")
        if config['sistemaTTS'] == "piper":
            if lista_voces_piper and lista_voces_piper[0] != 'No hay voces instaladas':
                # Reutilizamos los nombres que ya tiene el player formateados para Sonata
                nombres = player.devicenames
                dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres)]
                reader._lector.set_device(reader._lector.find_device_id(valor_str, known_devices=dispositivos_formateados))
            reader.leer_auto(_("Hablaré a través de este dispositivo."))

    def reproducirPrueva(self, event):
        if config['sistemaTTS'] == "piper":
            if self.dialog.choice_2.GetStringSelection() != 'No hay voces instaladas':
                reader.leer_auto(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
        else:
            if self.reproduciendo_prueba:
                self.play_timer.Stop()
                reader._lector.silence()
                self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
                self.reproduciendo_prueba = False
                return
            
            reader._lector.silence()
            reader.leer_auto(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
            self.dialog.boton_prueva.SetLabel(_("&Detener prueba."))
            self.reproduciendo_prueba = True
            self.play_timer.Start(200)

    def cambiarVoz(self, event):
        if self.play_timer.IsRunning():
            self.play_timer.Stop()
        reader._lector.silence()
        self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
        self.reproduciendo_prueba = False

        config['voz'] = self.dialog.choice_2.GetSelection()
        if config['sistemaTTS'] == "piper":
            from TTS.list_voices import obtener_ruta_voz
            # Simplemente cargamos el nuevo modelo en el lector existente
            reader._lector.piperSpeak(obtener_ruta_voz(lista_voces_piper[config['voz']]))
            # El dispositivo se mantiene o se actualiza si es necesario, usando dispositivos conocidos
            nombres = player.devicenames
            dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres)]
            salida_piper = reader._lector.find_device_id(nombres[config["dispositivo"]-1], known_devices=dispositivos_formateados)
            reader._lector.set_device(salida_piper)
        else:
            voces_lector = reader._lector.list_voices()
            if voces_lector and config['voz'] < len(voces_lector):
                reader._lector.set_voice(voces_lector[config['voz']])
    def cambiarVolumen(self, event):
        value = self.dialog.slider_2.GetValue()
        reader._leer.set_volume(value)
        reader._lector.set_volume(value)
        config['volume'] = value
    def cambiarTono(self, event):
        if config['sistemaTTS'] == "onecore":
            # OneCore: el slider va de 0 a 4, cada posición = 0.6, 0.7, 0.8, 0.9, 1.0
            pos = self.dialog.slider_1.GetValue()
            config['tono_onecore'] = pos
            reader._lector.set_pitch(pos)  # PrismBackendWrapper recibirá 0-4 para OneCore
        else:
            value = self.dialog.slider_1.GetValue() - 10
            reader._leer.set_pitch(value)
            reader._lector.set_pitch(value)
            config['tono'] = value
    def cambiarVelocidad(self, event):
        value = self.dialog.slider_3.GetValue() - 10
        reader._leer.set_rate(value)
        if config['sistemaTTS'] == "piper":
            voz_actual = lista_voces_piper[self.dialog.choice_2.GetSelection()]
            if voz_actual != 'No hay voces instaladas':
                reader._lector.set_rate(app_utilitys.porcentaje_a_escala(value))
        else:
            reader._lector.set_rate(value)
        config['speed'] = value
    def instalar_voz_piper(self, event):
        menu = wx.Menu()
        item_online = menu.Append(wx.ID_ANY, _("Descargar voces de internet..."))
        item_local = menu.Append(wx.ID_ANY, _("Instalar desde archivo local (.tar.gz)..."))
        
        self.dialog.Bind(wx.EVT_MENU, self.on_descargar_online, item_online)
        self.dialog.Bind(wx.EVT_MENU, self.on_instalar_local, item_local)
        
        self.dialog.PopupMenu(menu)
        menu.Destroy()

    def on_descargar_online(self, event):
        downloader = PiperDownloaderController(self.dialog)
        downloader.show()
        self._refrescar_voces_piper()

    def on_instalar_local(self, event):
        global config
        # Aseguramos que Piper sea el sistema activo para cargar el modelo tras instalar
        reader.set_tts("piper")
        res = install_piper_voice(config, reader._lector)
        if res:
            # install_piper_voice devuelve (config, reader)
            # Aunque no podemos reasignar config global fácilmente aquí sin global config,
            # lo que nos interesa es refrescar la lista.
            self._refrescar_voces_piper()

    def _refrescar_voces_piper(self):
        from TTS.list_voices import piper_list_voices
        import globals.resources as resources
        
        nuevas_voces = piper_list_voices()
        if nuevas_voces:
            # Actualizamos la lista global para que toda la app vea los cambios
            resources.lista_voces_piper.clear()
            resources.lista_voces_piper.extend(nuevas_voces)
            
            # Actualizamos la UI si estamos en modo Piper
            if config['sistemaTTS'] == "piper":
                self.dialog.choice_2.Clear()
                self.dialog.choice_2.AppendItems(resources.lista_voces_piper)
                # Intentamos mantener la selección o poner la primera
                try:
                    self.dialog.choice_2.SetSelection(config.get('voz', 0))
                except:
                    self.dialog.choice_2.SetSelection(0)

    def on_check_play_status(self, event):
        if config['sistemaTTS'] != "piper" and hasattr(reader._lector, 'backend'):
            try:
                if not reader._lector.backend.speaking:
                    self.play_timer.Stop()
                    self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
                    self.reproduciendo_prueba = False
            except Exception:
                self.play_timer.Stop()
                self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
                self.reproduciendo_prueba = False
        else:
            self.play_timer.Stop()

    def on_destroy(self, event):
        if hasattr(self, 'play_timer') and self.play_timer.IsRunning():
            self.play_timer.Stop()
        try:
            reader._lector.silence()
        except Exception:
            pass
        event.Skip()