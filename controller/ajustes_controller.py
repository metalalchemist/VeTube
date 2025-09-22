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
    def _bind_events(self):
        self.dialog.check_1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar_sapi(event))
        self.dialog.chk1.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'reader'))
        self.dialog.check_traduccion.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'traducir'))
        self.dialog.check_actualizaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'updates'))
        self.dialog.check_salir.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'salir'))
        self.dialog.check_donaciones.Bind(wx.EVT_CHECKBOX, lambda event: self.checar(event, 'donations'))
        self.dialog.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
        self.dialog.reproducir.Bind(wx.EVT_BUTTON, lambda event: player.playsound(rutasonidos[self.dialog.soniditos.GetFocusedItem()], False))
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

    def cambiar_sintetizador(self, event):
        config['sistemaTTS'] = self.dialog.seleccionar_TTS.GetStringSelection()
        if config['sistemaTTS'] == "piper":
            if len(lista_voces_piper) == 1 and lista_voces_piper[0]=='No hay voces instaladas':
                reader.set_tts("piper")
                reader._lector=reader._lector.piperSpeak(f"piper/voices/voice-{lista_voces[0][:-5]}/{lista_voces[0]}")
                config['voz'] = 0
            self.dialog.instala_voces.Enable()
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces_piper)
        else:
            reader.set_tts(config['sistemaTTS'])
            self.dialog.instala_voces.Disable()
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces)
        try:
            self.dialog.choice_2.SetSelection(config['voz'])
        except:
            self.dialog.choice_2.SetSelection(0)
    def establecer_dispositivo(self, event):
        valor = self.dialog.lista_dispositivos.GetSelection() + 1
        valor_str = self.dialog.lista_dispositivos.GetStringSelection()
        config['dispositivo'] = valor
        player.setdevice(config["dispositivo"])
        player.playsound("sounds/cambiardispositivo.wav")
        if config['sistemaTTS'] == "piper":
            if reader._lector.get_devices() is not None and lista_voces_piper[0]!='No hay voces instaladas':
                reader._lector.set_device(reader._lector.find_device_id(valor_str))
            reader.leer_auto(_("Hablaré a través  de este dispositivo."))
    def reproducirPrueva(self, event):
        if not ".onnx" in self.dialog.choice_2.GetStringSelection():
            reader._leer.silence()
            reader.leer_sapi(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
        else:
            reader.leer_auto(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
    def cambiarVoz(self, event):
        config['voz'] = self.dialog.choice_2.GetSelection()
        if config['sistemaTTS'] == "piper":
            reader.set_tts("sapi5")
            reader.set_tts("piper")
            reader._lector = reader._lector.piperSpeak(f"piper/voices/voice-{lista_voces[config['voz']][:-5]}/{lista_voces[config['voz']]}")
            dispositivos_piper = reader._lector.get_devices()
            salida_piper = reader._lector.find_device_id(player.devicenames[config["dispositivo"]-1])
            reader._lector.set_device(salida_piper)
        else:
            reader._leer.set_voice(lista_voces[config['voz']])
    def cambiarVolumen(self, event):
        reader._leer.set_volume(self.dialog.slider_2.GetValue())
        config['volume'] = self.dialog.slider_2.GetValue()
    def cambiarTono(self, event):
        value = self.dialog.slider_1.GetValue() - 10
        reader._leer.set_pitch(value)
        config['tono'] = value
    def cambiarVelocidad(self, event):
        value = self.dialog.slider_3.GetValue() - 10
        if not ".onnx" in lista_voces[self.dialog.choice_2.GetSelection()]:
            reader._leer.set_rate(value)
        else:
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(value))
        config['speed'] = value
    def instalar_voz_piper(self, event):
        reader.set_tts("sapi5")
        reader.set_tts("piper")
        config, reader._lector = install_piper_voice(config, reader._lector)
        lista_voces_piper = piper_list_voices()
        if lista_voces_piper:
            self.dialog.choice_2.Clear()
            self.dialog.choice_2.AppendItems(lista_voces_piper)