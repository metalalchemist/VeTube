import wx

from globals.data_store import motor_de_interfaz
from setup import reader
from ui.motor_downloader import MotorDownloaderDialog
from utils.network import network_manager as network


class MotorDownloaderController:
    """Base común de los instaladores de motor de voz: los motores ya no viajan
    en el build y se bajan una sola vez desde la release fija «motores» (sonata
    para las voces Piper, sherpa para las Kokoro). Cada motor concreto pone su
    gestor de descarga, sus textos y cómo recargar su voz; el diálogo, el
    progreso y la cancelación son comunes."""

    # --- Lo que define a cada motor ---
    MANAGER = None  # clase de servicios/*_manager.py
    MOTOR = ""  # nombre del sistema TTS al que sirve (piper, kokoro)

    def __init__(self, parent):
        self.manager = self.MANAGER()
        self.view = MotorDownloaderDialog(
            parent,
            self.titulo(),
            self.presentacion(self.MANAGER.TAMANO_DESCARGA // (1024 * 1024)),
        )
        self.descargando = False
        self.fase_instalacion = False
        self.cancelacion_pedida = False

        self.view.btn_descargar.Bind(wx.EVT_BUTTON, self.on_descargar)
        self.view.btn_cerrar.Bind(wx.EVT_BUTTON, self.on_cerrar)
        self.view.Bind(wx.EVT_CLOSE, self.on_close)

        if self.motor_instalado():
            self.view.set_status(self.texto_ya_instalado())
            self.view.btn_descargar.Disable()
            self.view.btn_cerrar.SetFocus()
        else:
            self.view.set_status(_("Listo para descargar."))

    # ------------------------------------------------ A definir por cada motor
    def motor_instalado(self):
        raise NotImplementedError

    def titulo(self):
        raise NotImplementedError

    def presentacion(self, tamano_mb):
        raise NotImplementedError

    def texto_ya_instalado(self):
        raise NotImplementedError

    def texto_exito(self):
        raise NotImplementedError

    def texto_error(self, detalle):
        raise NotImplementedError

    def cargar_voz_activa(self):
        """Carga en el puente recién levantado la voz que el usuario tenía
        elegida. Cada motor sabe dónde vive su voz."""
        raise NotImplementedError

    # ----------------------------------------------------------------- Común
    def on_descargar(self, event):
        self.descargando = True
        self.fase_instalacion = False
        self.cancelacion_pedida = False
        # Aquí y no dentro de instalar_motor: la corrutina no arranca hasta que
        # el bucle de red le hace sitio, y un Escape pulsado en ese hueco se
        # habría borrado al empezar ella.
        self.manager.cancelado = False
        self.view.btn_descargar.Disable()
        # El foco estaba en el botón recién deshabilitado: sin esto queda en el
        # limbo y un usuario de lector de pantalla ya no sabe dónde está.
        self.view.btn_cerrar.SetFocus()
        self.view.update_progress(0)
        self.view.set_status(_("Descargando el motor de voz..."))
        network.execute(self.manager.instalar_motor(self._progreso), self._al_terminar)

    def _progreso(self, avance):
        # Llega desde el hilo de red o desde el hilo de extracción.
        wx.CallAfter(self._aplicar_progreso, avance)

    def _aplicar_progreso(self, avance):
        if not self.view:
            return
        self.view.update_progress(avance)
        if avance >= 90 and not self.fase_instalacion:
            self.fase_instalacion = True
            self.view.set_status(_("Descarga completada. Instalando el paquete..."))

    def _al_terminar(self, resultado):
        self.descargando = False
        if not self.view:
            return
        if isinstance(resultado, Exception):
            exito, cancelado, detalle = False, False, str(resultado)
        else:
            exito = resultado.get("success", False)
            cancelado = resultado.get("cancelado", False)
            detalle = resultado.get("data", "")

        if exito:
            self.view.set_status(_("Instalación completada."))
            self._recargar_motor()
            wx.MessageBox(
                self.texto_exito(),
                _("Éxito"),
                parent=self.view,
            )
            self.view.EndModal(wx.ID_OK)
        elif cancelado:
            self.view.EndModal(wx.ID_CANCEL)
        else:
            self.view.update_progress(0)
            self.view.set_status(_("La instalación ha fallado."))
            self.view.btn_descargar.Enable()
            self.view.btn_descargar.SetFocus()
            wx.MessageBox(
                self.texto_error(detalle),
                _("Error"),
                parent=self.view,
            )

    def _recargar_motor(self):
        """Si este motor es el sistema activo, sustituye el respaldo SAPI del
        instante por el puente recién instalado y carga la voz elegida, para
        que funcione al momento, sin tener que reiniciar VeTube."""
        if motor_de_interfaz() != self.MOTOR:
            return
        # set_tts pasa por configurar_tts, que ahora sí encuentra el motor y
        # levanta el puente de verdad en lugar del respaldo.
        reader.set_tts(self.MOTOR)
        self.cargar_voz_activa()

    def _pedir_cancelacion(self):
        """Primera petición: anuncia en voz alta y espera a que la tarea suelte
        el bloque en curso (normalmente una fracción de segundo). Segunda
        petición (red congelada que no suelta el control): salida de emergencia
        cerrando el diálogo; los callbacks tardíos ya quedan neutralizados por
        las guardas `if not self.view`. Devuelve True si hay que cerrar ya."""
        if self.cancelacion_pedida:
            return True
        self.cancelacion_pedida = True
        self.manager.cancelar()
        self.view.set_status(_("Cancelando la descarga..."))
        # Con _leer (voz secundaria): el lector principal está justo entre dos
        # puentes (el respaldo momentáneo y el motor que se estaba instalando),
        # y la voz secundaria no depende de ese vaivén. El respaldo sí habla,
        # así que no es cuestión de quedarse mudo, sino de no perder la frase.
        reader._leer.speak(_("Cancelando la descarga..."))
        return False

    def on_cerrar(self, event):
        if self.descargando and not self._pedir_cancelacion():
            return
        self.view.EndModal(wx.ID_CANCEL)

    def on_close(self, event):
        if self.descargando and not self._pedir_cancelacion():
            if event.CanVeto():
                event.Veto()
            return
        self.view.EndModal(wx.ID_CANCEL)

    def show(self):
        resultado = self.view.ShowModal()
        self.view.Destroy()
        return resultado
