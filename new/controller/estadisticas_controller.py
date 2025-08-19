import wx
from ui.estadisticas_dialog import EstadisticasDialog

class EstadisticasController:
    def __init__(self, parent, estadisticas_manager):
        self.parent = parent
        self.estadisticas_manager = estadisticas_manager
        self.dialog = EstadisticasDialog(self.parent)

        self.populate_stats()

        self.dialog.btn_guardar.Bind(wx.EVT_BUTTON, self.on_save)

    def show(self):
        # ShowModal bloquea hasta que el usuario cierra el diálogo.
        # Devuelve el ID del botón presionado (ej. wx.ID_OK, wx.ID_CANCEL)
        self.dialog.ShowModal()
        # Es crucial destruir el diálogo después de que se cierra para liberar recursos.
        self.dialog.Destroy()


    def populate_stats(self):
        stats = self.estadisticas_manager.obtener_estadisticas_ordenadas()
        self.dialog.list_ctrl.DeleteAllItems()
        for i, (autor, num_mensajes) in enumerate(stats):
            index = self.dialog.list_ctrl.InsertItem(i, autor)
            self.dialog.list_ctrl.SetItem(index, 1, str(num_mensajes))

    def on_save(self, event):
        with wx.FileDialog(self.dialog, "Guardar estadísticas en JSON", wildcard="Archivos JSON (*.json)|*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.estadisticas_manager.guardar_en_archivo(pathname)
                wx.MessageBox(f"Estadísticas guardadas en {pathname}", "Éxito", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error al guardar el archivo: {e}", "Error", wx.OK | wx.ICON_ERROR)

    
