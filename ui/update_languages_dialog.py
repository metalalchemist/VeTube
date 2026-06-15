import wx

class UpdateLanguagesDialog(wx.Dialog):
    def __init__(self, parent, languages_to_update):
        super().__init__(parent, title=_("Actualizar idiomas"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, label=_("Selecciona los idiomas que deseas actualizar:"))
        main_sizer.Add(label, 0, wx.ALL, 10)

        self.check_list_box = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.check_list_box.InsertColumn(0, _("Idioma"), width=350)
        self.check_list_box.EnableCheckBoxes()

        for i, lang_text in enumerate(languages_to_update):
            self.check_list_box.InsertItem(i, lang_text)
            self.check_list_box.CheckItem(i, check=False)
        
        main_sizer.Add(self.check_list_box, 1, wx.EXPAND | wx.ALL, 10)

        self.progress_gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        main_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.ALL, 10)

        self.status_text = wx.StaticText(self, label="")
        main_sizer.Add(self.status_text, 0, wx.ALL, 10)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.ok_button = self.FindWindowById(wx.ID_OK)
        self.ok_button.SetLabel(_("Actualizar"))
        self.cancel_button = self.FindWindowById(wx.ID_CANCEL)

        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(main_sizer)
        self.SetSize((400, 450))
        self.Centre()
        
        # Establecer el foco al final para asegurar que no lo roben otros controles
        if self.check_list_box.GetItemCount() > 0:
            self.check_list_box.Focus(0)
            self.check_list_box.Select(0)
        self.check_list_box.SetFocus()

    def GetCheckedLanguages(self):
        checked_languages = []
        for i in range(self.check_list_box.GetItemCount()):
            if self.check_list_box.IsItemChecked(i):
                checked_languages.append(self.check_list_box.GetItemText(i))
        return checked_languages

    def disable_controls(self):
        self.ok_button.Disable()
        self.cancel_button.Disable()
        self.check_list_box.Disable()

    def update_progress(self, value):
        self.progress_gauge.SetValue(value)

    def set_status(self, text):
        self.status_text.SetLabel(text)

    def preparar_interfaz_final(self):
        self.status_text.SetLabel(_("Actualización completada."))
        self.ok_button.SetLabel(_("Cerrar"))
        self.ok_button.Enable()
        self.cancel_button.Hide()
        self.ok_button.SetFocus()
