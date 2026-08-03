# -*- coding: utf-8 -*-
import wx
from setup import network, reader
from globals.data_store import config
from servicios.kokoro_manager import KokoroManager, TAMANO_DESCARGA
from ui.kokoro_downloader import KokoroDownloaderDialog
from TTS.sherpa_handler import kokoro_model_instalado, kokoro_voice_config

class KokoroDownloaderController:
    def __init__(self, parent):
        self.manager = KokoroManager()
        self.view = KokoroDownloaderDialog(parent, TAMANO_DESCARGA // (1024 * 1024))
        self.descargando = False
        self.fase_instalacion = False
        self.cancelacion_pedida = False

        self.view.btn_descargar.Bind(wx.EVT_BUTTON, self.on_descargar)
        self.view.btn_cerrar.Bind(wx.EVT_BUTTON, self.on_cerrar)
        self.view.Bind(wx.EVT_CLOSE, self.on_close)

        if kokoro_model_instalado():
            self.view.set_status(_("Las voces Kokoro ya están instaladas en este equipo."))
            self.view.btn_descargar.Disable()
            self.view.btn_cerrar.SetFocus()
        else:
            self.view.set_status(_("Listo para descargar."))

    def on_descargar(self, event):
        self.descargando = True
        self.fase_instalacion = False
        self.cancelacion_pedida = False
        # Aquí y no dentro de instalar_modelo: la corrutina no arranca hasta que
        # el bucle de red le hace sitio, y un Escape pulsado en ese hueco se
        # habría borrado al empezar ella.
        self.manager.cancelado = False
        self.view.btn_descargar.Disable()
        # El foco estaba en el botón recién deshabilitado: sin esto queda en el
        # limbo y un usuario de lector de pantalla ya no sabe dónde está.
        self.view.btn_cerrar.SetFocus()
        self.view.update_progress(0)
        self.view.set_status(_("Descargando el paquete de voces..."))
        network.execute(self.manager.instalar_modelo(self._progreso), self._al_terminar)

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
            exito = resultado.get('success', False)
            cancelado = resultado.get('cancelado', False)
            detalle = resultado.get('data', '')

        if exito:
            self.view.set_status(_("Instalación completada."))
            self._recargar_voz_activa()
            wx.MessageBox(
                _("Las voces Kokoro se han instalado correctamente. Ya puedes seleccionarlas en los Ajustes de Voz."),
                _("Éxito"), parent=self.view)
            self.view.EndModal(wx.ID_OK)
        elif cancelado:
            self.view.EndModal(wx.ID_CANCEL)
        else:
            self.view.update_progress(0)
            self.view.set_status(_("La instalación ha fallado."))
            self.view.btn_descargar.Enable()
            self.view.btn_descargar.SetFocus()
            wx.MessageBox(
                _("No se pudieron instalar las voces Kokoro: %s") % detalle,
                _("Error"), parent=self.view)

    def _recargar_voz_activa(self):
        """Si Kokoro es el sistema activo, carga la voz recién instalada para
        que funcione al momento, sin tener que reabrir los Ajustes."""
        if config.get('sistemaTTS') != "kokoro":
            return
        config_kokoro = kokoro_voice_config(config.get('voz', 0))
        if config_kokoro is not None:
            reader._lector.load_model(config_kokoro)

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
        # Con _leer (voz secundaria) y no leer_auto: la voz principal puede ser
        # justamente el Kokoro aún sin instalar, es decir, muda.
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
