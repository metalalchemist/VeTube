import wx
from ui.estadisticas_dialog import EstadisticasDialog

class EstadisticasController:
    def __init__(self, parent, estadisticas_manager, plataforma):
        self.parent = parent
        self.estadisticas_manager = estadisticas_manager
        self.plataforma = plataforma
        summary_text = _("Total de mensajes recibidos: {}").format(self.estadisticas_manager.total_mensajes()) + "\n"
        summary_text += _("Total de usuarios que hablaron: {}").format(self.estadisticas_manager.total_usuarios()) + "\n"

        if self.plataforma and self.plataforma.lower() == 'tiktok':
            tiktok_stats = self.estadisticas_manager.obtener_estadisticas_tiktok()
            summary_text += _("Total de usuarios que se unieron al en vivo: {}").format(tiktok_stats['unidos']) + "\n"
            summary_text += _("Total de usuarios que siguieron al moderador: {}").format(tiktok_stats['seguidores']) + "\n"
            summary_text += _("Total de me gustan en el en vivo: {}").format(tiktok_stats['megusta']) + "\n"
            summary_text += _("Total de usuarios que compartieron en el en vivo: {}").format(tiktok_stats['compartidas'])
        
        self.dialog = EstadisticasDialog(self.parent, title=_("Estadísticas del Chat"), summary_text=summary_text)
        self.populate_stats()
        self.dialog.btn_guardar.Bind(wx.EVT_BUTTON, self.on_save)

    def show(self):
        self.dialog.ShowModal()
        self.dialog.Destroy()

    def populate_stats(self):
        stats = self.estadisticas_manager.obtener_estadisticas_ordenadas()
        self.dialog.list_ctrl.DeleteAllItems()
        for i, (autor, num_mensajes) in enumerate(stats):
            index = self.dialog.list_ctrl.InsertItem(i, autor)
            self.dialog.list_ctrl.SetItem(index, 1, str(num_mensajes))

    def on_save(self, event):
        with wx.FileDialog(self.dialog, _("Guardar estadísticas"), wildcard=_("Archivos JSON (*.json)|*.json"),
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.estadisticas_manager.guardar_en_archivo(pathname)
                wx.MessageBox(_("Estadísticas guardadas en {}").format(pathname), _("Éxito"), wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(_("Error al guardar el archivo: {}").format(e), _("Error"), wx.OK | wx.ICON_ERROR)
