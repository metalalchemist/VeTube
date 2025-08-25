import wx
import concurrent.futures
import tempfile
from ui.update_languages_dialog import UpdateLanguagesDialog
from utils.language_updater import GestorRepositorios
from ui.dialog_response import response
from utils import app_utilitys

class UpdateLanguagesController:
    def __init__(self, parent, gestor, update_data):
        self.parent = parent
        self.gestor = gestor
        self.update_data = update_data
        
        languages_to_display = self._prepare_display_list()
        
        self.view = UpdateLanguagesDialog(parent, languages_to_display, self)
        self.executor = None
        self.update_completed = False

    def _prepare_display_list(self):
        nuevos = self.update_data.get('nuevos', {})
        actualizaciones = self.update_data.get('actualizaciones', {})
        
        languages_to_display = []
        for lang_code, version in nuevos.items():
            languages_to_display.append(f"{lang_code} (Nuevo - v{version})")
        for lang_code, version in actualizaciones.items():
            languages_to_display.append(f"{lang_code} (Actualizar a v{version})")
        return languages_to_display

    def show(self):
        return self.view.ShowModal()

    def start_update(self):
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
        
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        
        self.futures = []
        for lang_info in languages_to_process:
            lang_code = lang_info['code']
            version = lang_info['version']
            future = self.executor.submit(self._download_and_install_language, lang_code, version)
            self.futures.append(future)
            future.add_done_callback(lambda f, lc=lang_code: wx.CallAfter(self._on_task_done, f, lc))

        wx.CallAfter(self.view.set_status, _("Iniciando descarga de idiomas..."))

    def _on_task_done(self, future, lang_code):
        self.completed_tasks += 1
        progress = int((self.completed_tasks / self.total_tasks) * 100)
        wx.CallAfter(self.view.update_progress, progress)

        try:
            result = future.result()
            if result['success']:
                wx.CallAfter(self.view.set_status, _(f"Idioma {result['data']} actualizado con éxito."))
            else:
                wx.CallAfter(self.view.set_status, _(f"Error al actualizar idioma {result['data']}: {result['error_msg']}"))
        except Exception as exc:
            import traceback
            error_traceback = traceback.format_exc()
            wx.CallAfter(self.view.set_status, _(f"Error inesperado en {lang_code}: {exc}"))
            print(f"[ERROR] Excepción en hilo de {lang_code}:\n{error_traceback}")
            wx.CallAfter(wx.MessageBox, _(f"Error inesperado en {lang_code}:\n{exc}\n\nVer consola para más detalles."), _("Error"), wx.OK | wx.ICON_ERROR)

        if self.completed_tasks == self.total_tasks:
            self.update_completed = True
            wx.CallAfter(self.view.set_status, _("Actualización completada."))
            wx.CallAfter(self.view.finalize_update)
            wx.EndBusyCursor()
            if self.executor:
                self.executor.shutdown(wait=False)

    def prompt_for_restart(self):
        if response(_("Es necesario reiniciar el programa para aplicar los nuevos idiomas. ¿Desea reiniciarlo ahora?"), _("¡Atención!")) == wx.ID_YES:
            app_utilitys.restart_program()

    def _download_and_install_language(self, lang_code, version):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                download_result = self.gestor.descargar_zip(lang_code, download_dir=temp_dir)
                if not download_result['success']:
                    return {'success': False, 'data': lang_code, 'error_msg': download_result['data']}
                
                unzip_result = self.gestor.descomprimir_zip(lang_code, zip_source_dir=temp_dir, ruta_destino="locales")
                if not unzip_result['success']:
                    return {'success': False, 'data': lang_code, 'error_msg': unzip_result['data']}
                
                self.gestor.actualizar_idioma_local(lang_code, version)
                
                return {'success': True, 'data': lang_code}
        except Exception as e:
            return {'success': False, 'data': lang_code, 'error_msg': str(e)}

    def close(self):
        if self.update_completed:
            self.prompt_for_restart()
        if self.executor:
            self.executor.shutdown(wait=False)
        self.view.Destroy()
