import wx

class EstadisticasDialog(wx.Dialog):
    def __init__(self, parent, title=_("Estadísticas del Chat"), summary_text=""):
        super(EstadisticasDialog, self).__init__(parent, title=title, size=(450, 500))
        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.summary_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, value=summary_text)
        vbox.Add(self.summary_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        self.list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, _('Autor'), width=250)
        self.list_ctrl.InsertColumn(1, _('Cantidad de mensajes'), width=150)

        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        self.btn_guardar = wx.Button(self.panel, label=_('Guardar estadísticas'))
        self.btn_cerrar = wx.Button(self.panel, id=wx.ID_CANCEL, label=_('Cerrar'))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.btn_guardar, 0, wx.ALL, 5)
        hbox.Add(self.btn_cerrar, 0, wx.ALL, 5)

        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.panel.SetSizer(vbox)
        self.CenterOnScreen()