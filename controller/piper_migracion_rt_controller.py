# -*- coding: utf-8 -*-
import wx
from setup import network, reader
from servicios.piper_manager import PiperManager, limpiar_ficheros_rt
from ui.piper_migracion_rt import PiperMigracionRTDialog

class PiperMigracionRTController:
    """Reinstala en variante estándar las voces que solo existían en RT.

    Mismo patrón de cancelación que el instalador de Kokoro: la primera
    petición se anuncia en voz alta y deja terminar la voz en curso; la
    segunda es la salida de emergencia si la red se quedó congelada (los
    callbacks tardíos quedan neutralizados por las guardas de self.view).
    """

    def __init__(self, parent, claves):
        self.claves = claves
        self.manager = PiperManager()
        self.view = PiperMigracionRTDialog(parent)
        self.trabajando = False
        self.cancelado = False
        self.cancelacion_pedida = False

        self.view.btn_cancelar.Bind(wx.EVT_BUTTON, self.on_cancelar)
        self.view.Bind(wx.EVT_CLOSE, self.on_close)

    def show(self):
        self.trabajando = True
        self.view.set_status(_("Conectando con el catálogo de voces..."))
        network.execute(self._migrar(), self._al_terminar)
        resultado = self.view.ShowModal()
        self.view.Destroy()
        self.view = None
        return resultado

    async def _migrar(self):
        res = await self.manager.cargar_catalogo()
        if not res.get('success'):
            return {'completadas': 0, 'total': len(self.claves),
                    'errores': [res.get('data', '')], 'cancelado': False}
        completadas, errores = 0, []
        total = len(self.claves)
        for i, clave in enumerate(self.claves):
            if self.cancelado:
                break
            wx.CallAfter(self._estado, _("Descargando %s [%d/%d]...") % (clave, i + 1, total))

            def cb(avance, indice=i):
                # Barra global monótona sobre el conjunto de voces: sin esto
                # los pitidos de NVDA volverían a cero con cada voz.
                wx.CallAfter(self._progreso, int((indice + avance / 100.0) * 100 / total))

            res = await self.manager.instalar_voz(clave, cb)
            if res.get('cancelado'):
                break
            if res.get('success'):
                # Ya hay modelo estándar completo: los ficheros RT sobran.
                limpiar_ficheros_rt(clave)
                completadas += 1
            else:
                errores.append("%s: %s" % (clave, res.get('data', '')))
        return {'completadas': completadas, 'total': total, 'errores': errores,
                'cancelado': self.cancelado or self.manager.cancelado}

    def _estado(self, texto):
        if self.view:
            self.view.set_status(texto)

    def _progreso(self, avance):
        if self.view:
            self.view.update_progress(avance)

    def _al_terminar(self, resultado):
        self.trabajando = False
        if not self.view:
            return
        if isinstance(resultado, Exception):
            resultado = {'completadas': 0, 'total': len(self.claves),
                         'errores': [str(resultado)], 'cancelado': False}
        completadas = resultado.get('completadas', 0)
        total = resultado.get('total', len(self.claves))
        errores = resultado.get('errores', [])
        if resultado.get('cancelado'):
            # Cancelación pedida por el usuario: cerrar sin anunciar éxito ni
            # completar la barra. Las voces que quedaron sin migrar se
            # volverán a ofrecer en el próximo arranque.
            self.view.EndModal(wx.ID_CANCEL)
            return
        if errores:
            self.view.set_status(_("Proceso finalizado. %d de %d voces actualizadas.") % (completadas, total))
            wx.MessageBox(
                _("No se pudieron actualizar todas las voces: %s\nVeTube lo volverá a intentar en el próximo inicio.") % "; ".join(errores),
                _("Error"), parent=self.view)
        else:
            self.view.update_progress(100)
            # Voz secundaria: la principal aún no tiene modelo cargado.
            reader._leer.speak(_("Voces actualizadas correctamente."))
        self.view.EndModal(wx.ID_OK if completadas == total else wx.ID_CANCEL)

    def _pedir_cancelacion(self):
        if self.cancelacion_pedida:
            return True
        self.cancelacion_pedida = True
        self.cancelado = True
        # El flag del manager corta la transferencia en el siguiente bloque
        # recibido; el flag local corta el bucle entre voces.
        self.manager.cancelar()
        self.view.set_status(_("Cancelando la descarga..."))
        reader._leer.speak(_("Cancelando la descarga..."))
        return False

    def on_cancelar(self, event):
        if self.trabajando and not self._pedir_cancelacion():
            return
        self.view.EndModal(wx.ID_CANCEL)

    def on_close(self, event):
        if self.trabajando and not self._pedir_cancelacion():
            if event.CanVeto():
                event.Veto()
            return
        self.view.EndModal(wx.ID_CANCEL)
