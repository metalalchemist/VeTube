import wx
from utils import funciones

class ListUrlsDialog(wx.Dialog):
    def __init__(self, parent, list_box_1, dialog_mensaje):
        urls = funciones.extract_urls(list_box_1.GetString(list_box_1.GetSelection()))
        if urls:
            super().__init__(dialog_mensaje, wx.ID_ANY, _("Lista de URLS"))
            sizer_urls = wx.BoxSizer(wx.VERTICAL)
            list_urls = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
            list_urls.InsertColumn(0, "URLs")
            for i in range(len(urls)):
                list_urls.InsertItem(i, urls[i])
            list_urls.Focus(0)
            list_urls.SetFocus()
            list_urls.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda event: (wx.LaunchDefaultBrowser(list_urls.GetItem(list_urls.GetFocusedItem(), 0).GetText()), self.Destroy()))
            sizer_urls.Add(list_urls)
            button_cerrar = wx.Button(self, wx.ID_CANCEL, _("&Cerrar"))
            sizer_urls.Add(button_cerrar)
            self.SetSizerAndFit(sizer_urls)
            self.Centre()
            self.ShowModal()
            self.Destroy()
        else:
            wx.MessageBox(_("No hay URLS en este  mensaje"), "Error", wx.ICON_ERROR)
