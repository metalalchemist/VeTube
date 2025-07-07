from globals.mensajes import mensaje_teclas
from utils.key_utilitys import editor
import wx

class EditorCombinaciones:
    def __init__(self, parent=None):
        self.dlg_teclado = wx.Dialog(parent, wx.ID_ANY, _("Editor de combinaciones de teclado para Vetube"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        label_editor = wx.StaticText(self.dlg_teclado, wx.ID_ANY, _("&Selecciona la combinación de teclado a editar"))
        self.combinaciones = wx.ListCtrl(self.dlg_teclado, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.combinaciones.InsertColumn(0, _("acción: "), width=200)
        self.combinaciones.InsertColumn(1, _("combinación de teclas: "), width=200)
        for i in range(len(mensaje_teclas)):
            self.combinaciones.InsertItem(i, mensaje_teclas[i])
        c = 0
        for valor in editor.teclas:
            self.combinaciones.SetItem(c, 1, valor)
            c += 1
        self.combinaciones.Focus(0)
        self.combinaciones.SetFocus()

        self.editar = wx.Button(self.dlg_teclado, -1, _(u"&Editar"))
        self.editar.SetDefault()
        self.restaurar = wx.Button(self.dlg_teclado, -1, _(u"&restaurar combinaciones por defecto"))
        self.close = wx.Button(self.dlg_teclado, wx.ID_CANCEL, _(u"&Cerrar"))

        sizer.Add(label_editor, 0, wx.ALL, 5)
        sizer.Add(self.combinaciones, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.editar, 0, wx.ALL, 5)
        button_sizer.Add(self.restaurar, 0, wx.ALL, 5)
        button_sizer.Add(self.close, 0, wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.dlg_teclado.SetSizerAndFit(sizer)
        self.dlg_teclado.SetSize((500, 400))
        self.dlg_teclado.Centre()

    def ShowModal(self):
        return self.dlg_teclado.ShowModal()
