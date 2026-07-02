# -*- coding: utf-8 -*-
import wx
import asyncio
import os
import shutil
from setup import network, player, reader
from servicios.piper_manager import PiperManager
from ui.piper_downloader import PiperDownloaderDialog
from TTS.list_voices import piper_list_voices

class PiperDownloaderController:
    def __init__(self, parent):
        self.parent = parent
        self.manager = PiperManager()
        self.view = PiperDownloaderDialog(parent)
        
        self.idiomas_data = [] # Lista de {'code': ..., 'display': ...}
        self.voces_actuales = [] # Lista de voces filtradas actualmente
        self.voces_locales = [] # Nombres de archivos .onnx locales
        
        self.play_timer = wx.Timer(self.view)
        self.view.Bind(wx.EVT_TIMER, self.on_check_play_status, self.play_timer)
        self.reproduciendo_muestra = False
        
        self._bind_events()
        self._refrescar_instaladas()
        
        # Iniciar carga de catálogo
        network.execute(self.manager.cargar_catalogo(), self.on_catalogo_cargado)

    def _bind_events(self):
        # Eventos de la pestaña Descargar
        self.view.lang_list.Bind(wx.EVT_LIST_ITEM_CHECKED, self.on_lang_checked)
        self.view.lang_list.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.on_lang_checked)
        self.view.btn_reproducir.Bind(wx.EVT_BUTTON, self.on_reproducir)
        self.view.btn_descargar.Bind(wx.EVT_BUTTON, self.on_descargar)
        
        # Eventos de la pestaña Instaladas
        self.view.btn_probar_local.Bind(wx.EVT_BUTTON, self.on_probar_local)
        self.view.btn_eliminar.Bind(wx.EVT_BUTTON, self.on_eliminar)
        
        # Sincronización de visibilidad de botones según pestaña
        self.view.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self._actualizar_botones_visibles()

    def on_page_changed(self, event):
        self._actualizar_botones_visibles()
        event.Skip()

    def _actualizar_botones_visibles(self):
        is_descargar = self.view.notebook.GetSelection() == 1
        self.view.btn_reproducir.Show(is_descargar)
        self.view.btn_descargar.Show(is_descargar)
        self.view.Layout()

    def _refrescar_instaladas(self):
        self.voces_locales = piper_list_voices()
        self.view.list_instaladas.Clear()
        if self.voces_locales:
            self.view.list_instaladas.Set(self.voces_locales)
        else:
            self.view.list_instaladas.Append(_("No hay voces instaladas"))

    def on_probar_local(self, event):
        selection = self.view.list_instaladas.GetSelection()
        if selection == -1 or self.view.list_instaladas.GetString(selection) == _("No hay voces instaladas"):
            return
        
        voz_nombre = self.voces_locales[selection]
        ruta_modelo = os.path.join("voices", f"voice-{voz_nombre[:-5]}", voz_nombre)
        
        self.view.set_status(_("Probando voz local: %s") % voz_nombre)
        
        # Usamos el lector Piper directamente para la prueba
        # Guardamos el modelo actual para restaurarlo después si fuera necesario
        try:
            reader._lector.load_model(ruta_modelo)
            reader._lector.speak(_("Hola, esta es una prueba de la voz %s instalada localmente.") % voz_nombre)
        except Exception as e:
            wx.MessageBox(_("Error al cargar la voz para prueba: %s") % str(e), _("Error"))

    def on_eliminar(self, event):
        selection = self.view.list_instaladas.GetSelection()
        if selection == -1 or self.view.list_instaladas.GetString(selection) == _("No hay voces instaladas"):
            return
        
        voz_nombre = self.voces_locales[selection]
        if wx.MessageBox(_("¿Estás seguro de que deseas eliminar la voz %s? Esta acción no se puede deshacer.") % voz_nombre, 
                         _("Confirmar eliminación"), wx.YES_NO | wx.ICON_WARNING) == wx.ID_YES:
            
            # La carpeta suele ser voice-<nombre_sin_onnx>
            folder_name = f"voice-{voz_nombre[:-5]}"
            path_to_remove = os.path.join("voices", folder_name)
            
            try:
                if os.path.exists(path_to_remove):
                    shutil.rmtree(path_to_remove)
                    self.view.set_status(_("Voz %s eliminada correctamente.") % voz_nombre)
                    self._refrescar_instaladas()
                else:
                    wx.MessageBox(_("No se pudo encontrar la carpeta de la voz."), _("Error"))
            except Exception as e:
                wx.MessageBox(_("No se pudo eliminar la voz: %s. Asegúrate de que no esté en uso.") % str(e), _("Error"))

    def on_catalogo_cargado(self, result):
        if isinstance(result, Exception) or not result.get('success'):
            self.view.set_status(_("Error al cargar el catálogo de voces."))
            wx.MessageBox(_("No se pudo conectar con Hugging Face para obtener las voces."), _("Error"), wx.ICON_ERROR)
            return

        self.idiomas_data = self.manager.get_idiomas_disponibles()
        self.view.lang_list.DeleteAllItems()
        for i, info in enumerate(self.idiomas_data):
            self.view.lang_list.InsertItem(i, info['display'])
        
        self.view.set_status(_("Catálogo cargado. Selecciona idiomas para ver las voces."))

    def on_lang_checked(self, event):
        codigos_seleccionados = []
        for i in range(self.view.lang_list.GetItemCount()):
            if self.view.lang_list.IsItemChecked(i):
                codigos_seleccionados.append(self.idiomas_data[i]['code'])
        
        self.voces_actuales = self.manager.get_voces_por_idiomas(codigos_seleccionados)
        self._actualizar_lista_voces()

    def _actualizar_lista_voces(self):
        self.view.voice_list.DeleteAllItems()
        for i, v in enumerate(self.voces_actuales):
            self.view.voice_list.InsertItem(i, v['name'])
            self.view.voice_list.SetItem(i, 1, v['quality'])
            self.view.voice_list.SetItem(i, 2, v['lang_code'])

    def on_reproducir(self, event):
        if self.reproduciendo_muestra:
            self.play_timer.Stop()
            if player.sound is not None and hasattr(player.sound, 'is_playing') and player.sound.is_playing:
                player.sound.stop()
            self.view.btn_reproducir.SetLabel(_("&Reproducir muestra"))
            self.view.set_status(_("Reproducción de muestra detenida."))
            self.reproduciendo_muestra = False
            return

        item = self.view.voice_list.GetFocusedItem()
        if item == -1:
            wx.MessageBox(_("Por favor, selecciona una voz de la lista para escuchar la muestra."), _("Aviso"))
            return
        
        voice = self.voces_actuales[item]
        url = voice.get('sample_url')
        if url:
            self.view.set_status(_("Reproduciendo muestra de %s...") % voice['name'])
            # Usamos el SoundPlayer global para reproducir la URL directamente
            player.play(url)
            self.view.btn_reproducir.SetLabel(_("&Detener"))
            self.reproduciendo_muestra = True
            self.play_timer.Start(200)
        else:
            wx.MessageBox(_("Esta voz no dispone de muestra de audio."), _("Error"))

    def on_check_play_status(self, event):
        if not player.sound or not getattr(player.sound, 'is_playing', False):
            self.play_timer.Stop()
            self.view.btn_reproducir.SetLabel(_("&Reproducir muestra"))
            self.view.set_status(_("Reproducción de muestra finalizada."))
            self.reproduciendo_muestra = False

    def on_descargar(self, event):
        checked_indices = []
        for i in range(self.view.voice_list.GetItemCount()):
            if self.view.voice_list.IsItemChecked(i):
                checked_indices.append(i)
        
        # Si no hay nada marcado con checkbox, probamos con el elemento enfocado
        if not checked_indices:
            focused = self.view.voice_list.GetFocusedItem()
            if focused != -1:
                checked_indices = [focused]
        
        if not checked_indices:
            wx.MessageBox(_("Por favor, selecciona al menos una voz para descargar."), _("Aviso"))
            return
        
        voces_seleccionadas = [self.voces_actuales[i] for i in checked_indices]
        tiene_rt = any(v.get('has_rt') for v in voces_seleccionadas)
        
        if tiene_rt:
            # Mostrar menú para elegir variante global para el lote
            menu = wx.Menu()
            item_normal = menu.Append(wx.ID_ANY, _("Descargar variantes de Calidad Normal (Alta)"))
            item_rt = menu.Append(wx.ID_ANY, _("Descargar variantes Rápidas (RT) donde estén disponibles"))
            
            self.view.Bind(wx.EVT_MENU, lambda evt: self._iniciar_descarga_multiple(voces_seleccionadas, es_rt=False), item_normal)
            self.view.Bind(wx.EVT_MENU, lambda evt: self._iniciar_descarga_multiple(voces_seleccionadas, es_rt=True), item_rt)
            
            self.view.PopupMenu(menu)
            menu.Destroy()
        else:
            # Ninguna tiene RT, descarga normal para todas
            self._iniciar_descarga_multiple(voces_seleccionadas, es_rt=False)

    def _iniciar_descarga_multiple(self, voces, es_rt):
        self.view.btn_descargar.Disable()
        self.view.lang_list.Disable()
        self.view.voice_list.Disable()
        
        network.execute(self._descargar_lote(voces, es_rt))

    async def _descargar_lote(self, voces, preferir_rt):
        total = len(voces)
        completadas = 0
        
        for voice in voces:
            usar_rt = preferir_rt and voice.get('has_rt')
            tipo_str = "RT" if usar_rt else "Normal"
            
            wx.CallAfter(self.view.set_status, _("Descargando %s (%s) [%d/%d]...") % (voice['name'], tipo_str, completadas + 1, total))
            
            def cb(p):
                wx.CallAfter(self.view.update_progress, p)

            if usar_rt:
                res = await self.manager.instalar_voz_rt(voice['key'], cb)
            else:
                res = await self.manager.instalar_voz(voice['key'], cb)
            
            if res['success']:
                completadas += 1
            else:
                wx.CallAfter(wx.MessageBox, _("Error al descargar %s: %s") % (voice['name'], res['data']), _("Error"))
        
        wx.CallAfter(self._finalizar_descargas, completadas, total)

    def _finalizar_descargas(self, completadas, total):
        self.view.set_status(_("Proceso finalizado. %d de %d voces instaladas.") % (completadas, total))
        self.view.btn_descargar.Enable()
        self.view.lang_list.Enable()
        self.view.voice_list.Enable()
        self.view.update_progress(100)
        
        if completadas > 0:
            wx.MessageBox(_("Las voces se han instalado correctamente. Ya puedes seleccionarlas en los Ajustes de Voz."), _("Éxito"))

    def show(self):
        res = self.view.ShowModal()
        if self.play_timer.IsRunning():
            self.play_timer.Stop()
        if self.reproduciendo_muestra:
            if player.sound is not None and hasattr(player.sound, 'is_playing') and player.sound.is_playing:
                player.sound.stop()
            self.reproduciendo_muestra = False
        return res
