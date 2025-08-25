import wx
from utils import funciones

class ListUrlsDialog(wx.Dialog):
    def __init__(self, list_box_1, dialog_mensaje):
        urls = funciones.extract_urls(list_box_1.GetString(list_box_1.GetSelection()))
        if urls:
            super().__init__(dialog_mensaje, wx.ID_ANY, _("Lista de URLS"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            list_urls = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
            list_urls.InsertColumn(0, "URLs")
            for i, url in enumerate(urls):
                list_urls.InsertItem(i, url)
            list_urls.SetColumnWidth(0, 350)
            list_urls.Focus(0)
            list_urls.SetFocus()
            list_urls.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda event: (wx.LaunchDefaultBrowser(list_urls.GetItem(list_urls.GetFocusedItem(), 0).GetText()), self.Destroy()))
            main_sizer.Add(list_urls, 1, wx.EXPAND | wx.ALL, 5)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.AddStretchSpacer()
            button_cerrar = wx.Button(self, wx.ID_CANCEL, _("&Cerrar"))
            button_sizer.Add(button_cerrar, 0, wx.ALL, 5)
            main_sizer.Add(button_sizer, 0, wx.EXPAND)
            self.SetSizer(main_sizer)
            self.SetSize((400, 300))
            self.Centre()
            self.ShowModal()
            self.Destroy()
        else:
            wx.MessageBox(_("No hay URLS en este mensaje"), "Error", wx.ICON_ERROR)
