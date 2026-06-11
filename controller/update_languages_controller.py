import wx
import asyncio
from setup import network
from ui.update_languages_dialog import UpdateLanguagesDialog
from servicios.language_updater import GestorRepositorios
from ui.dialog_response import response
from utils import app_utilitys

class UpdateLanguagesController:
    def __init__(self, parent, gestor, update_data):
        self.parent = parent
        self.gestor = gestor
        self.update_data = update_data
        
        languages_to_display = self._prepare_display_list()
        
        self.view = UpdateLanguagesDialog(parent, languages_to_display)
        self._bind_events()
        self.update_completed = False

    def _bind_events(self):
        self.view.ok_button.Bind(wx.EVT_BUTTON, self.start_update)
        self.view.cancel_button.Bind(wx.EVT_BUTTON, self.close)
        self.view.Bind(wx.EVT_CLOSE, self.close)

    def _prepare_display_list(self):
        nuevos = self.update_data.get('nuevos', {})
        actualizaciones = self.update_data.get('actualizaciones', {})
        
        languages_to_display = []
        for lang_code, version in nuevos.items():
            languages_to_display.append(_("%s (Nuevo - v%s)") % (lang_code, version))
        for lang_code, version in actualizaciones.items():
            languages_to_display.append(_("%s (Actualizar a v%s)") % (lang_code, version))
        return languages_to_display

    def show(self):
        return self.view.ShowModal()

    def start_update(self, event=None):
        selected_languages_text = self.view.GetCheckedLanguages()
        if not selected_languages_text:
            wx.MessageBox(_("Por favor, selecciona al menos un idioma para actualizar."), _("Advertencia"), wx.OK | wx.ICON_WARNING)
            return

        wx.BeginBusyCursor()
        self.view.disable_controls()

        languages_to_process = []
        for display_text in selected_languages_text:
            lang_code = display_text.split(' ')[0]
            version_str = display_text.split('v')[-1].replace(')', '')
            version = int(version_str)
            languages_to_process.append({'code': lang_code, 'version': version})

        self.total_tasks = len(languages_to_process)
        self.completed_tasks = 0
        
        async def do_all_updates():
            tasks = []
            for lang_info in languages_to_process:
                tasks.append(self._download_and_install_language_async(lang_info['code'], lang_info['version']))
            await asyncio.gather(*tasks)

        # Usamos el motor de red global para lanzar todas las descargas a la vez
        network.execute(do_all_updates())
        wx.CallAfter(self.view.set_status, _("Iniciando descarga de idiomas..."))

    async def _download_and_install_language_async(self, lang_code, version):
        try:
            result = await self.gestor.instalar_idioma(lang_code, version)
            if result['success']:
                wx.CallAfter(self.view.set_status, _("Idioma %s actualizado con éxito.") % lang_code)
            else:
                error_msg = result.get('data', 'Error desconocido')
                wx.CallAfter(self.view.set_status, _("Error en %s: %s") % (lang_code, error_msg))
                wx.CallAfter(wx.MessageBox, _("Error al actualizar %s: %s") % (lang_code, error_msg), _("Error"), wx.ICON_ERROR)
        except Exception as exc:
            import traceback
            error_traceback = traceback.format_exc()
            wx.CallAfter(self.view.set_status, _("Error inesperado en %s: %s") % (lang_code, exc))
            wx.CallAfter(wx.MessageBox, _("Error inesperado en %s:\n%s\n\nVer consola para más detalles.") % (lang_code, exc), _("Error"), wx.OK | wx.ICON_ERROR)
        
        self.completed_tasks += 1
        progress = int((self.completed_tasks / self.total_tasks) * 100)
        wx.CallAfter(self.view.update_progress, progress)

        if self.completed_tasks == self.total_tasks:
            self._finalize_update()

    def _finalize_update(self):
        # Esta función interna es necesaria para pasarla a CallAfter y que todo sea seguro para hilos
        def _logic():
            self.update_completed = True
            self.view.set_status(_("Actualización completada."))
            self.view.preparar_interfaz_final()
            self.view.ok_button.Unbind(wx.EVT_BUTTON)
            self.view.ok_button.Bind(wx.EVT_BUTTON, lambda evt: self.view.EndModal(wx.ID_OK))
            wx.EndBusyCursor()
        wx.CallAfter(_logic)

    def close(self, event=None):
        if self.update_completed:
            if response(_("Es necesario reiniciar el programa para aplicar los nuevos idiomas. ¿Desea reiniciarlo ahora?"), _("¡Atención!")) == wx.ID_YES:
                app_utilitys.restart_program()
        self.view.Destroy()
