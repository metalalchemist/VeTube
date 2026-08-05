from logging import getLogger
from globals.data_store import config
from globals.resources import rutasonidos,lista_voces,lista_voces_piper,recargar_rutasonidos
from setup import player,reader
from utils import app_utilitys, languageHandler
from TTS.list_voices import piper_list_voices , install_piper_voice
from TTS.sherpa_handler import (kokoro_list_voices, kokoro_voice_config,
                                kokoro_idiomas_disponibles, kokoro_voces_de_idioma,
                                kokoro_idioma_de_voz)
from TTS.edge_handler import (edge_list_voices, edge_idiomas_disponibles,
                              edge_voces_de_idioma, edge_idioma_de_voz,
                              edge_voz_shortname, edge_iniciar_carga,
                              edge_voces_listas)
from controller.piper_downloader_controller import PiperDownloaderController
from controller.kokoro_downloader_controller import KokoroDownloaderController
from utils.menu_accesible import Accesible
from ui.dialog_response import response
import wx

logger = getLogger(__name__)

def _sin_diacriticos(texto):
    """Texto sin tildes ni diacríticos, para ordenar listas alfabéticamente sin
    depender del locale del sistema."""
    import unicodedata
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()

class AccesibleInstalador(Accesible):
    """El botón de instalar abre un menú con Piper pero un diálogo con Kokoro:
    el rol que anuncia el lector de pantalla debe decir la verdad en ambos
    casos, así que se decide en el momento en que se consulta."""
    def GetRole(self, childId):
        if config['sistemaTTS'] == "kokoro":
            return (wx.ACC_OK, wx.ROLE_SYSTEM_PUSHBUTTON)
        return super().GetRole(childId)

    def GetDefaultAction(self, childId):
        if config['sistemaTTS'] == "kokoro":
            # Sin acción especial: que wx anuncie la de un botón normal
            return (wx.ACC_NOT_IMPLEMENTED, "")
        return super().GetDefaultAction(childId)

class AjustesController:
    # Claves que los controles del diálogo escriben en config apenas cambian (en caliente),
    # sin esperar a Aceptar. Ver revertir_cambios_en_caliente(): con Cancelar/Escape, todas
    # vuelven al valor que tenían al abrir el diálogo.
    CLAVES_EN_CALIENTE = [
        'sapi', 'reader', 'traducir', 'interface', 'updates', 'salir', 'donations',
        'sonidos', 'directorio', 'sistemaTTS', 'dispositivo', 'voz', 'volume',
        'tono', 'tono_onecore', 'speed', 'reproducir', 'tiempo', 'volumen', 'cambiovolumen',
    ]

    def __init__(self, dialog):
        self.dialog = dialog
        self.config_al_abrir = {clave: config.get(clave) for clave in self.CLAVES_EN_CALIENTE}
        # Traducción entre lo que se ve en la lista de voces y lo que se guarda
        # en config['voz'] (ver _mostrar_voces), y códigos del filtro de idioma.
        self.indices_voces = []
        self.codigos_idioma = []
        # Última voz usada en cada idioma: cruzar idiomas con las flechas no
        # debe hacer perder la voz elegida (ver cambiar_idioma_voz).
        self.ultima_voz_por_idioma = {}
        self.dialog.instala_voces.SetAccessible(AccesibleInstalador(self.dialog.instala_voces))
        
        self.play_timer = wx.Timer(self.dialog)
        self.dialog.Bind(wx.EVT_TIMER, self.on_check_play_status, self.play_timer)
        self.reproduciendo_prueba = False
        self.dialog.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        
        self._bind_events()
        self.actualizar_visibilidad_instalador()
        self.actualizar_filtro_idioma()
        # Cargamos la lista de voces correcta al iniciar
        if config['sistemaTTS'] == "piper":
            self._mostrar_voces(lista_voces_piper)
        elif config['sistemaTTS'] == "kokoro":
            self.rellenar_voces()
        elif config['sistemaTTS'] == "edge":
            # Las voces de Edge viven en el CDN: se descargan en segundo plano
            # y se rellenan cuando llegan (ver _poblar_voces_edge).
            if edge_voces_listas():
                self.rellenar_voces()
            else:
                edge_iniciar_carga(self._voces_edge_listas)
        else:
            voces = reader._lector.list_voices()
            if not voces:
                voces = [_("Controlado por el lector de pantalla")]
            self._mostrar_voces(voces)
        self.actualizar_habilitacion_controles()
        # SetSelection fuera de rango no lanza excepción en wx: colocamos la voz
        # a mano para que el lector de pantalla siempre anuncie una.
        self._seleccionar_voz_activa()

        # Sincronización inicial de parámetros
        if config['sistemaTTS'] in ("piper", "kokoro"):
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            # Aplicamos la velocidad inicial usando la escala correcta
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
        elif config['sistemaTTS'] == "edge":
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            # Edge usa la velocidad nativa (-10 a 10) sin reescalar
            reader._lector.set_rate(config['speed'])
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
        self.dialog.reproducir.Bind(wx.EVT_BUTTON, self.reproducir_sonido)
        self.dialog.seleccionar_TTS.Bind(wx.EVT_CHOICE, self.cambiar_sintetizador)
        self.dialog.establecer_dispositivo.Bind(wx.EVT_BUTTON, self.establecer_dispositivo)
        self.dialog.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
        self.dialog.choice_idioma_voz.Bind(wx.EVT_CHOICE, self.cambiar_idioma_voz)
        self.dialog.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
        self.dialog.slider_2.Bind(wx.EVT_SLIDER, self.cambiarVolumen)
        self.dialog.slider_1.Bind(wx.EVT_SLIDER, self.cambiarTono)
        self.dialog.slider_3.Bind(wx.EVT_SLIDER, self.cambiarVelocidad)
        self.dialog.instala_voces.Bind(wx.EVT_BUTTON, self.instalar_paquete_voz)
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

    def reproducir_sonido(self, event):
        idx = self.dialog.soniditos.GetFocusedItem()
        if 0 <= idx < len(rutasonidos):
            player.play(rutasonidos[idx])

    def checar(self, event, key):
        config[key] = True if event.IsChecked() else False

    def checar_sapi(self, event):
        config['sapi'] = True if event.IsChecked() else False
        self.dialog.seleccionar_TTS.Enable(not event.IsChecked())
        self.actualizar_visibilidad_instalador()

    def cambiar_sintetizador(self, event):
        if self.play_timer.IsRunning():
            self.play_timer.Stop()
        reader._lector.silence()
        self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
        self.reproduciendo_prueba = False

        config['sistemaTTS'] = self.dialog.seleccionar_TTS.GetStringSelection()
        reader.set_tts(config['sistemaTTS'])
        self.actualizar_filtro_idioma()
        if config['sistemaTTS'] == "piper":
            if lista_voces_piper and lista_voces_piper[0] != _("No hay voces instaladas"):
                voz_index = config.get('voz', 0)
                if voz_index >= len(lista_voces_piper):
                    voz_index = 0
                    config['voz'] = 0
                from TTS.list_voices import obtener_ruta_voz
                model_path = obtener_ruta_voz(lista_voces_piper[voz_index])
                reader._lector.load_model(model_path)
            else:
                # Sin voces de Piper no hay nada que cargar, y el puente es el
                # mismo proceso: hay que soltar la voz de Kokoro que pudiera
                # quedar cargada, o el chat se leería con ella.
                reader._lector.unload_model()
            self._mostrar_voces(lista_voces_piper)
            # Sincronizar volumen, tono y velocidad de Piper
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
        elif config['sistemaTTS'] == "kokoro":
            voces_kokoro = kokoro_list_voices()
            voz_index = config.get('voz', 0)
            if voz_index >= len(voces_kokoro):
                voz_index = 0
                config['voz'] = 0
            config_kokoro = kokoro_voice_config(voz_index)
            if config_kokoro is not None:
                reader._lector.load_model(config_kokoro)
            else:
                # Mismo caso al revés: sin el paquete de Kokoro hay que soltar
                # la voz de Piper que estuviera cargada en el puente.
                reader._lector.unload_model()
                if event is not None:
                    # Avisar en voz alta en lugar de callar, pero no al
                    # revertir con Cancelar (el diálogo ya se está cerrando).
                    reader._leer.speak(_("No hay voces instaladas"))
            self.rellenar_voces_kokoro()
            # Sincronizar volumen, tono y velocidad (misma escala que Piper)
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(config['speed']))
        elif config['sistemaTTS'] == "edge":
            # Edge no tiene nada local que cargar: solo apuntar el lector a la
            # voz elegida (ShortName) y descargar la lista de voces en segundo
            # plano si aún no está (la necesita el filtro de idioma y la lista).
            voz_index = config.get('voz', 0)
            reader._lector.load_model(edge_voz_shortname(voz_index))
            reader._lector.set_volume(config['volume'])
            reader._lector.set_pitch(config['tono'])
            reader._lector.set_rate(config['speed'])
            self.actualizar_filtro_idioma()
            if edge_voces_listas():
                self.rellenar_voces()
                self._seleccionar_voz_activa()
            else:
                edge_iniciar_carga(self._voces_edge_listas)
        else:
            voces = reader._lector.list_voices()
            if not voces:
                voces = [_("Controlado por el lector de pantalla")]
            self._mostrar_voces(voces)

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
                
        self.actualizar_visibilidad_instalador()
        self.actualizar_habilitacion_controles()
        self._seleccionar_voz_activa()

    def actualizar_visibilidad_instalador(self):
        # El mismo botón instala voces de Piper o el paquete de Kokoro,
        # según el sistema TTS elegido.
        show = not config['sapi'] and config['sistemaTTS'] in ("piper", "kokoro")
        self.dialog.instala_voces.Show(show)
        # Aseguramos que los controles de tono y volumen estén habilitados siempre
        self.dialog.slider_1.Enable()
        self.dialog.slider_2.Enable()
        self.dialog.treeItem_2.Layout()

    def _nombre_idioma(self, codigo):
        """Nombre de un código de idioma, traducido cuando hay traducción. Se
        arma al llamar, no al importar el módulo, para que respete el idioma de
        la interfaz. Vale para los códigos de Kokoro (es, en-us, en-gb…) y para
        los de Edge (2 letras, p.ej. de, ja, zh): los que no están traducidos
        caen en el nombre en inglés de googletrans."""
        traducciones = {
            "es": _("Español"),
            "fr": _("Francés"),
            "en-us": _("Inglés (Estados Unidos)"),
            "en-gb": _("Inglés (Reino Unido)"),
            "it": _("Italiano"),
            "pt-br": _("Portugués (Brasil)"),
            "hi": _("Hindi"),
        }
        if codigo in traducciones:
            return traducciones[codigo]
        from googletrans import LANGUAGES
        nombre = LANGUAGES.get(codigo)
        if nombre:
            return nombre.capitalize()
        return codigo

    def _idiomas_disponibles(self):
        """Códigos de idioma que ofrece el motor elegido, o [] si ninguno."""
        if config['sistemaTTS'] == "kokoro":
            return kokoro_idiomas_disponibles()
        if config['sistemaTTS'] == "edge":
            return edge_idiomas_disponibles()
        return []

    def _idioma_de_voz(self, index):
        """Código de idioma de la voz que ocupa ese índice global, o None."""
        if config['sistemaTTS'] == "kokoro":
            return kokoro_idioma_de_voz(index)
        if config['sistemaTTS'] == "edge":
            return edge_idioma_de_voz(index)
        return None

    def actualizar_filtro_idioma(self):
        """El filtro de idioma solo tiene sentido con motores de voces de varios
        idiomas: Kokoro (siete en un paquete) y Edge (todo el catálogo de
        Microsoft). En ambos se coloca por defecto en el idioma del programa
        (languageHandler.curLang), igual que en el menú principal
        (main_menu_controller, curLang[:2])."""
        es_multi = config['sistemaTTS'] in ("kokoro", "edge")
        self.dialog.label_idioma_voz.Show(es_multi)
        self.dialog.choice_idioma_voz.Show(es_multi)
        if es_multi:
            # Orden alfabético por el nombre traducido: en una lista desplegable
            # se salta a un idioma tecleando su inicial. Se ordena sin tildes ni
            # diacríticos, si no «Španělština» acabaría después de la Z en checo.
            codigos = sorted(self._idiomas_disponibles(),
                             key=lambda codigo: _sin_diacriticos(self._nombre_idioma(codigo)))
            # La primera entrada no filtra nada, de ahí el None.
            self.codigos_idioma = [None] + codigos
            self.dialog.choice_idioma_voz.Clear()
            self.dialog.choice_idioma_voz.AppendItems(
                [_("Todos los idiomas")] + [self._nombre_idioma(c) for c in codigos])
            # Idioma del programa (languageHandler.curLang) como punto de
            # partida del filtro para todos los motores multilingües.
            codigo_usuario = (languageHandler.curLang or "es")[:2].lower()
            seleccion = self.codigos_idioma.index(
                codigo_usuario) if codigo_usuario in self.codigos_idioma else 0
            self.dialog.choice_idioma_voz.SetSelection(seleccion)
        else:
            self.codigos_idioma = []
        self.dialog.treeItem_2.Layout()

    def _idioma_filtrado(self):
        """Código del idioma elegido en el filtro, o None si son todos."""
        seleccion = self.dialog.choice_idioma_voz.GetSelection()
        if 0 <= seleccion < len(self.codigos_idioma):
            return self.codigos_idioma[seleccion]
        return None

    def _mostrar_voces(self, etiquetas, indices=None):
        """Llena la lista de voces. indices traduce cada posición mostrada al
        número que se guarda en config['voz']: con Kokoro filtrado por idioma no
        coinciden, y guardar la posición de la lista cambiaría de voz sola."""
        self.indices_voces = list(indices) if indices is not None else list(range(len(etiquetas)))
        self.dialog.choice_2.Clear()
        self.dialog.choice_2.AppendItems(etiquetas)

    def _seleccionar_voz_activa(self):
        """Deja la lista sobre la voz de config['voz'] y devuelve True. Si esa
        voz no está (índice inservible, o filtrada por idioma), cae en la
        primera de la lista, actualiza config['voz'] y devuelve False."""
        if config['voz'] in self.indices_voces:
            self.dialog.choice_2.SetSelection(self.indices_voces.index(config['voz']))
            return True
        self.dialog.choice_2.SetSelection(0)
        config['voz'] = self.indices_voces[0] if self.indices_voces else 0
        return False

    def _indice_global_seleccionado(self):
        """Índice de la voz elegida en la lista, tal como se guarda en config."""
        seleccion = self.dialog.choice_2.GetSelection()
        if 0 <= seleccion < len(self.indices_voces):
            return self.indices_voces[seleccion]
        return config['voz']

    def rellenar_voces_kokoro(self):
        """Llena la lista con las voces del idioma elegido en el filtro."""
        self.rellenar_voces()

    def rellenar_voces(self):
        """Llena la lista con las voces del idioma elegido en el filtro, para
        Kokoro o Edge según el motor activo."""
        if config['sistemaTTS'] == "kokoro":
            voces = kokoro_voces_de_idioma(self._idioma_filtrado())
        elif config['sistemaTTS'] == "edge":
            voces = edge_voces_de_idioma(self._idioma_filtrado())
        else:
            voces = []
        self._mostrar_voces([etiqueta for indice, etiqueta in voces],
                            [indice for indice, etiqueta in voces])

    def _voces_edge_listas(self):
        """Se llama desde el hilo del loop de edge-tts cuando termina la
        descarga de voces: hay que volver al hilo de la UI antes de tocar wx."""
        wx.CallAfter(self._poblar_voces_edge)

    def _poblar_voces_edge(self):
        if config['sistemaTTS'] != "edge":
            return
        try:
            # El diálogo pudo cerrarse antes de que terminara la descarga: no
            # tocar widgets ya destruidos.
            self.dialog.seleccionar_TTS
        except Exception:
            return
        self.actualizar_filtro_idioma()
        self.rellenar_voces()
        self._seleccionar_voz_activa()
        # Asegurar que el lector apunta a la voz que queda seleccionada: si la
        # lista se llenó después de abrir el diálogo, todavía no está cargada.
        self.cambiarVoz(None)

    def cambiar_idioma_voz(self, event):
        # Para llegar a un idioma se pasa por los de en medio con las flechas, y
        # cada uno cambia de voz: guardamos la voz de cada idioma para
        # devolverla si el usuario vuelve, en vez de dejarlo con la primera.
        voz_anterior = config['voz']
        idioma_anterior = self._idioma_de_voz(voz_anterior)
        if idioma_anterior:
            self.ultima_voz_por_idioma[idioma_anterior] = voz_anterior
        self.rellenar_voces()
        recordada = self.ultima_voz_por_idioma.get(self._idioma_filtrado())
        if voz_anterior not in self.indices_voces and recordada in self.indices_voces:
            config['voz'] = recordada
        if not self._seleccionar_voz_activa() or config['voz'] != voz_anterior:
            # La voz cambia con el idioma: cargarla igual que si el usuario la
            # hubiera elegido en la lista.
            self.cambiarVoz(None)

    def actualizar_habilitacion_controles(self):
        if config['sistemaTTS'] in ("piper", "kokoro", "edge"):
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
        if self.dialog.lista_dispositivos.GetSelection() == wx.NOT_FOUND:
            self.dialog.lista_dispositivos.SetFocus()
            return
        valor = self.dialog.lista_dispositivos.GetSelection() + 1
        config['dispositivo'] = valor
        player.setdevice(config["dispositivo"])
        player.play(f"sounds/{config['directorio']}/cambiardispositivo.mp3")
        if config['sistemaTTS'] in ("piper", "kokoro"):
            hay_voz = config['sistemaTTS'] == "kokoro" or (
                lista_voces_piper and lista_voces_piper[0] != _("No hay voces instaladas"))
            if hay_voz:
                # La lista del diálogo se construye con player.devicenames, así que
                # el nombre elegido y el que saca config['dispositivo'] son el mismo.
                app_utilitys.fijar_dispositivo_lector()
            reader.leer_auto(_("Hablaré a través de este dispositivo."))
        elif config['sistemaTTS'] == "edge":
            app_utilitys.fijar_dispositivo_lector()
            reader.leer_auto(_("Hablaré a través de este dispositivo."))

    def reproducirPrueva(self, event):
        # El botón alterna entre reproducir y detener con cualquier motor:
        # el puente sherpa también sabe decir si sigue hablando (is_playing).
        if self.reproduciendo_prueba:
            self.play_timer.Stop()
            reader._lector.silence()
            self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
            self.reproduciendo_prueba = False
            return

        if config['sistemaTTS'] in ("piper", "kokoro"):
            if config['sistemaTTS'] == "kokoro" and kokoro_voice_config(config['voz']) is None:
                # Sin el modelo instalado la síntesis no arranca nunca: avisar
                # de lo que falta y ofrecer el descargador ahí mismo (pedido
                # de César; mismo patrón que configurar_piper).
                if response(_("Para probar las voces Kokoro hay que descargar antes el paquete de voces. ¿Quieres abrir el descargador ahora?"),
                            _("No hay voces instaladas")) == wx.ID_YES:
                    KokoroDownloaderController(self.dialog).show()
                return
            if config['sistemaTTS'] == "piper" and self.dialog.choice_2.GetStringSelection() == _("No hay voces instaladas"):
                # Mismo aviso hablado que con Kokoro: un botón que no hace
                # nada en silencio desorienta al lector de pantalla.
                reader._leer.speak(_("No hay voces instaladas"))
                return
        elif config['sistemaTTS'] == "edge":
            if not edge_voz_shortname(config['voz']):
                # Sin la lista de voces descargada no hay voz que apuntar: un
                # botón que no hace nada en silencio desorienta. Si aún no ha
                # llegado, se espera a que termine la descarga.
                if not edge_voces_listas():
                    reader._leer.speak(_("Cargando las voces de Edge TTS, espera un momento."))
                    edge_iniciar_carga(self._voces_edge_listas)
                return
            # Apuntar el lector a la voz elegida por si la lista se cargó después
            # de abrir el diálogo (mismo efecto que cambiarVoz).
            reader._lector.load_model(edge_voz_shortname(config['voz']))
        else:
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

        config['voz'] = self._indice_global_seleccionado()
        if config['sistemaTTS'] == "piper":
            from TTS.list_voices import obtener_ruta_voz
            # Simplemente cargamos el nuevo modelo en el lector existente
            reader._lector.load_model(obtener_ruta_voz(lista_voces_piper[config['voz']]))
            app_utilitys.fijar_dispositivo_lector()
        elif config['sistemaTTS'] == "kokoro":
            config_kokoro = kokoro_voice_config(config['voz'])
            if config_kokoro is not None:
                reader._lector.load_model(config_kokoro)
                app_utilitys.fijar_dispositivo_lector()
            elif event is not None:
                # Solo cuando el usuario elige una voz a mano: esta función
                # también se llama sola (filtro de idioma, Cancelar), y ahí el
                # aviso se repetiría en cada flecha, encima de lo que lee NVDA.
                reader._leer.speak(_("No hay voces instaladas"))
        elif config['sistemaTTS'] == "edge":
            shortname = edge_voz_shortname(config['voz'])
            if shortname:
                reader._lector.load_model(shortname)
                app_utilitys.fijar_dispositivo_lector()
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
            if voz_actual != _("No hay voces instaladas"):
                reader._lector.set_rate(app_utilitys.porcentaje_a_escala(value))
        elif config['sistemaTTS'] == "kokoro":
            reader._lector.set_rate(app_utilitys.porcentaje_a_escala(value))
        elif config['sistemaTTS'] == "edge":
            # Edge usa la velocidad nativa (-10 a 10) sin reescalar
            reader._lector.set_rate(value)
        else:
            reader._lector.set_rate(value)
        config['speed'] = value
    def instalar_paquete_voz(self, event):
        if config['sistemaTTS'] == "kokoro":
            KokoroDownloaderController(self.dialog).show()
            return
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
                # Mantiene la selección si la voz sigue en la lista, o cae en la
                # primera; _mostrar_voces deja además al día la equivalencia
                # entre lo que se ve y lo que se guarda en config['voz'].
                self._mostrar_voces(resources.lista_voces_piper)
                self._seleccionar_voz_activa()

    def on_check_play_status(self, event):
        try:
            if config['sistemaTTS'] in ("piper", "kokoro", "edge"):
                sigue_hablando = reader._lector.is_playing()
            else:
                sigue_hablando = reader._lector.backend.speaking
        except Exception:
            sigue_hablando = False
        if not sigue_hablando:
            self.play_timer.Stop()
            self.dialog.boton_prueva.SetLabel(_("&Reproducir prueba."))
            self.reproduciendo_prueba = False

    def on_destroy(self, event):
        if hasattr(self, 'play_timer') and self.play_timer.IsRunning():
            self.play_timer.Stop()
        try:
            reader._lector.silence()
        except Exception:
            pass
        event.Skip()

    def revertir_cambios_en_caliente(self):
        """Cancelar/Escape: deshace en config y en el lector/reproductor real todo lo que
        ya se había aplicado en caliente, para que el diálogo quede como al abrirlo.
        Reutiliza los propios manejadores (cambiar_sintetizador, cambiarVoz, etc.) porque
        leen los valores desde los widgets del diálogo, no desde el event, así que sirve
        con event=None una vez que dejamos los widgets en el valor original. Cada bloque
        va en su propio try/except: si uno falla (un backend de voz que ya no está
        disponible, un dispositivo desconectado...) no debe impedir que se reviertan los
        demás, y no debe fallar en silencio — se registra con logger.exception."""
        original = self.config_al_abrir
        cambio_tts = config.get('sistemaTTS') != original['sistemaTTS']
        cambio_voz = config.get('voz') != original['voz']
        cambio_volumen = config.get('volume') != original['volume']
        cambio_tono = (config.get('tono') != original['tono']) or (config.get('tono_onecore') != original['tono_onecore'])
        cambio_velocidad = config.get('speed') != original['speed']
        cambio_dispositivo = config.get('dispositivo') != original['dispositivo']
        cambio_tema = config.get('directorio') != original['directorio']

        for clave in self.CLAVES_EN_CALIENTE:
            config[clave] = original[clave]

        if cambio_tema:
            try:
                recargar_rutasonidos()
            except Exception:
                logger.exception("No se pudo restaurar el tema de sonidos al cancelar Ajustes (directorio=%s)", config['directorio'])

        if cambio_tts:
            try:
                self.dialog.seleccionar_TTS.SetStringSelection(config['sistemaTTS'])
                self.cambiar_sintetizador(None)
            except Exception:
                logger.exception("No se pudo restaurar el sistema TTS al cancelar Ajustes (sistemaTTS=%s)", config['sistemaTTS'])
        elif cambio_voz:
            try:
                if config['sistemaTTS'] == "piper":
                    lista_voces_actual = lista_voces_piper
                elif config['sistemaTTS'] == "kokoro":
                    lista_voces_actual = kokoro_list_voices()
                elif config['sistemaTTS'] == "edge":
                    lista_voces_actual = edge_list_voices()
                else:
                    lista_voces_actual = reader._lector.list_voices()
                if 0 <= config['voz'] < len(lista_voces_actual):
                    if config['sistemaTTS'] in ("kokoro", "edge"):
                        # La lista puede haber quedado filtrada por otro idioma:
                        # hay que devolverla al idioma de la voz original, si no
                        # esta no aparece y se recargaría cualquier otra.
                        self.actualizar_filtro_idioma()
                        self.rellenar_voces()
                    self._seleccionar_voz_activa()
                    self.cambiarVoz(None)
                else:
                    # SetSelection() con un índice fuera de rango no lanza excepción en wx: no
                    # basta con un try/except acá, hay que descartar el índice inválido a mano
                    # para no terminar cargando una voz cualquiera (indexación negativa de Python).
                    logger.warning(
                        "No se pudo restaurar la voz al cancelar Ajustes: índice %s fuera de rango (%s voces disponibles)",
                        config['voz'], len(lista_voces_actual),
                    )
            except Exception:
                logger.exception("No se pudo restaurar la voz al cancelar Ajustes (voz=%s)", config['voz'])

        if cambio_volumen:
            try:
                self.dialog.slider_2.SetValue(config['volume'])
                self.cambiarVolumen(None)
            except Exception:
                logger.exception("No se pudo restaurar el volumen al cancelar Ajustes (volume=%s)", config['volume'])

        if cambio_tono:
            try:
                if config['sistemaTTS'] == "onecore":
                    self.dialog.slider_1.SetValue(config.get('tono_onecore', 0.6))
                else:
                    self.dialog.slider_1.SetValue(config['tono'] + 10)
                self.cambiarTono(None)
            except Exception:
                logger.exception("No se pudo restaurar el tono al cancelar Ajustes")

        if cambio_velocidad:
            try:
                self.dialog.slider_3.SetValue(config['speed'] + 10)
                self.cambiarVelocidad(None)
            except Exception:
                logger.exception("No se pudo restaurar la velocidad al cancelar Ajustes (speed=%s)", config['speed'])

        if cambio_dispositivo:
            # Sin el sonido de confirmación ni el "Hablaré a través de este dispositivo" de
            # establecer_dispositivo(): un Cancelar silencioso no debe sonar como un cambio aplicado.
            try:
                player.setdevice(config['dispositivo'])
                hay_voz_local = (config['sistemaTTS'] in ("kokoro", "edge") or (
                    config['sistemaTTS'] == "piper" and lista_voces_piper
                    and lista_voces_piper[0] != _("No hay voces instaladas")))
                if hay_voz_local:
                    app_utilitys.fijar_dispositivo_lector()
            except Exception:
                # Puede fallar si el dispositivo guardado desapareció mientras Ajustes estaba
                # abierto (auriculares desconectados, etc. — mismo caso que setup.py al arrancar).
                # No debe tumbar el revert ni impedir que se cierre el diálogo.
                logger.exception("No se pudo restaurar el dispositivo de audio al cancelar Ajustes (dispositivo=%s)", config['dispositivo'])