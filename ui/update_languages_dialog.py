import wx

class UpdateLanguagesDialog(wx.Dialog):
    def __init__(self, parent, languages_to_update, controller):
        super().__init__(parent, title=_("Actualizar idiomas"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.controller = controller
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, label=_("Selecciona los idiomas que deseas actualizar:"))
        main_sizer.Add(label, 0, wx.ALL, 10)

        self.check_list_box = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.check_list_box.InsertColumn(0, _("Idioma"))
        self.check_list_box.EnableCheckBoxes()

        for i, lang_text in enumerate(languages_to_update):
            self.check_list_box.InsertItem(i, lang_text)
            self.check_list_box.CheckItem(i, check=False)
        self.check_list_box.Focus(0)
        self.check_list_box.SetFocus()
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
        self.SetSize((400, 400))
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self._on_update_button, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self._on_cancel_button, self.cancel_button)
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def GetCheckedLanguages(self):
        checked_languages = []
        for i in range(self.check_list_box.GetItemCount()):
            if self.check_list_box.IsItemChecked(i):
                checked_languages.append(self.check_list_box.GetItemText(i))
        return checked_languages

    def _on_update_button(self, event):
        self.controller.start_update()

    def _on_cancel_button(self, event):
        self.controller.close()

    def _on_close(self, event):
        self.controller.close()

    def disable_controls(self):
        self.ok_button.Disable()
        self.cancel_button.Disable()
        self.check_list_box.Disable()

    def update_progress(self, value):
        self.progress_gauge.SetValue(value)

    def set_status(self, text):
        self.status_text.SetLabel(text)

    def finalize_update(self):
        self.status_text.SetLabel(_("Actualización completada."))
        self.ok_button.SetLabel(_("Cerrar"))
        self.ok_button.Enable()
        self.cancel_button.Hide()
        
        # Rebind OK button to close dialog
        self.ok_button.Unbind(wx.EVT_BUTTON)
        self.ok_button.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_OK))