from globals.data_store import config
from globals.resources import rutasonidos,lista_voces,lista_voces_piper
from setup import player,reader
from utils import app_utilitys
from TTS.list_voices import piper_list_voices , install_piper_voice
import wx
class AjustesController:
    def __init__(self, dialog):
        self.dialog = dialog
        self._bind_events()
        self.actualizar_visibilidad_piper()
        # Cargamos la lista de voces correcta al iniciar
        self.dialog.choice_2.Clear()
        if config['sistemaTTS'] == "piper":
            self.dialog.choice_2.AppendItems(lista_voces_piper)
        else:
            self.dialog.choice_2.AppendItems(lista_voces)
        try:
            self.dialog.choice_2.SetSelection(config['voz'])
        except:
            self.dialog.choice_2.SetSelection(0)
        
        # Sincronización inicial de parámetros para Piper
        if config['sistemaTTS'] == "piper":
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            # Aplicamos la velocidad inicial usando la escala correcta
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
    def _bind_events(self):
        self.dialog.check_1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar_sapi(event))
        self.dialog.chk1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'reader'))
        self.dialog.check_traduccion.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'traducir'))
        self.dialog.check_interface.Bind(wx.EVT_CHECKBOX, self.on_check_interface)
        self.dialog.check_actualizaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'updates'))
        self.dialog.check_salir.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'salir'))
        self.dialog.check_donaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'donations'))
        self.dialog.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
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

    def checar(self, event, key):
        config[key] = True if event.IsChecked() else False

    def checar_sapi(self, event):
        config['sapi'] = True if event.IsChecked() else False
        self.dialog.seleccionar_TTS.Enable(not event.IsChecked())
        self.actualizar_visibilidad_piper()

    def cambiar_sintetizador(self, event):
        config['sistemaTTS'] = self.dialog.seleccionar_TTS.GetStringSelection()
        reader.set_tts(config['sistemaTTS'])
        if config['sistemaTTS'] == "piper":
            if lista_voces_piper and lista_voces_piper[0] != 'No hay voces instaladas':
                voz_index = config.get('voz', 0)
                if voz_index >= len(lista_voces_piper): voz_index = 0
                model_path = f"voices/voice-{lista_voces_piper[voz_index][:-5]}/{lista_voces_piper[voz_index]}"
                reader._lector.load_model(model_path)
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces_piper)
        else:
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces)
        self.actualizar_visibilidad_piper()
        try:
            self.dialog.choice_2.SetSelection(config['voz'])
        except:
            self.dialog.choice_2.SetSelection(0)

    def actualizar_visibilidad_piper(self):
        show = not config['sapi'] and config['sistemaTTS'] == "piper"
        self.dialog.instala_voces.Show(show)
        # Aseguramos que los controles de tono y volumen estén habilitados siempre
        self.dialog.slider_1.Enable()
        self.dialog.slider_2.Enable()
        self.dialog.treeItem_2.Layout()

    def establecer_dispositivo(self, event):
        valor = self.dialog.lista_dispositivos.GetSelection() + 1
        valor_str = self.dialog.lista_dispositivos.GetStringSelection()
        config['dispositivo'] = valor
        player.setdevice(config["dispositivo"])
        player.play("sounds/cambiardispositivo.mp3")
        if config['sistemaTTS'] == "piper":
            if lista_voces_piper and lista_voces_piper[0] != 'No hay voces instaladas':
                # Reutilizamos los nombres que ya tiene el player formateados para Sonata
                nombres = player.devicenames
                dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres)]
                reader._lector.set_device(reader._lector.find_device_id(valor_str, known_devices=dispositivos_formateados))
            reader.leer_auto(_("Hablaré a través de este dispositivo."))

    def reproducirPrueva(self, event):
        if not ".onnx" in self.dialog.choice_2.GetStringSelection():
            reader._leer.silence()
            reader.leer_sapi(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
        else:
            reader.leer_auto(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))

    def cambiarVoz(self, event):
        config['voz'] = self.dialog.choice_2.GetSelection()
        if config['sistemaTTS'] == "piper":
            # Simplemente cargamos el nuevo modelo en el lector existente
            reader._lector.piperSpeak(f"voices/voice-{lista_voces_piper[config['voz']][:-5]}/{lista_voces_piper[config['voz']]}")
            # El dispositivo se mantiene o se actualiza si es necesario, usando dispositivos conocidos
            nombres = player.devicenames
            dispositivos_formateados = [{'name': n, 'id': i} for i, n in enumerate(nombres)]
            salida_piper = reader._lector.find_device_id(nombres[config["dispositivo"]-1], known_devices=dispositivos_formateados)
            reader._lector.set_device(salida_piper)
        else:
            reader._leer.set_voice(lista_voces[config['voz']])
    def cambiarVolumen(self, event):
        value = self.dialog.slider_2.GetValue()
        reader._leer.set_volume(value)
        if config['sistemaTTS'] == "piper":
            reader._lector.set_volume(value)
        config['volume'] = value
    def cambiarTono(self, event):
        value = self.dialog.slider_1.GetValue() - 10
        reader._leer.set_pitch(value)
        if config['sistemaTTS'] == "piper":
            reader._lector.set_pitch(value)
        config['tono'] = value
    def cambiarVelocidad(self, event):
        value = self.dialog.slider_3.GetValue() - 10
        if config['sistemaTTS'] == "piper":
            voz_actual = lista_voces_piper[self.dialog.choice_2.GetSelection()]
            if ".onnx" in voz_actual:
                reader._lector.set_rate(app_utilitys.porcentaje_a_escala(value))
            else:
                reader._leer.set_rate(value)
        else:
            reader._leer.set_rate(value)
        config['speed'] = value
    def instalar_voz_piper(self, event):
        global config
        reader.set_tts("sapi5")
        reader.set_tts("piper")
        config, reader._lector = install_piper_voice(config, reader._lector)
        print(config,'hola')
        lista_voces_piper = piper_list_voices()
        if lista_voces_piper:
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces_piper)