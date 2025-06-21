from globals.mensajes import mensaje_teclas
from globals.resources import teclas
import wx

class EditorCombinaciones:
    def __init__(self, parent=None):
        self.dlg_teclado = wx.Dialog(parent, wx.ID_ANY, _("Editor de combinaciones de teclado para Vetube"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        label_editor = wx.StaticText(self.dlg_teclado, wx.ID_ANY, _("&Selecciona la combinación de teclado a editar"))
        self.combinaciones = wx.ListCtrl(self.dlg_teclado, wx.ID_ANY, style=wx.LC_REPORT)
        self.combinaciones.InsertColumn(0, _("acción: "))
        self.combinaciones.InsertColumn(1, _("combinación de teclas: "))
        for i in range(len(mensaje_teclas)): self.combinaciones.InsertItem(i, mensaje_teclas[i])
        c=0
        for valor in teclas:
            self.combinaciones.SetItem(c, 1, valor)
            c+=1
        self.combinaciones.Focus(0)
        self.combinaciones.SetFocus()
        editar = wx.Button(self.dlg_teclado, -1, _(u"&Editar"))
        editar.SetDefault()
        restaurar = wx.Button(self.dlg_teclado, -1, _(u"&restaurar combinaciones por defecto"))
        close = wx.Button(self.dlg_teclado, wx.ID_CANCEL, _(u"&Cerrar"))
        firstSizer = wx.BoxSizer(wx.HORIZONTAL)
        firstSizer.Add(label_editor, 0, wx.ALL, 5)
        firstSizer.Add(self.combinaciones, 0, wx.ALL, 5)
        secondSizer = wx.BoxSizer(wx.HORIZONTAL)
        secondSizer.Add(editar, 0, wx.ALL, 5)
        secondSizer.Add(restaurar, 0, wx.ALL, 5)
        secondSizer.Add(close, 0, wx.ALL, 5)
        sizer.Add(firstSizer, 0, wx.ALL, 5)
        sizer.Add(secondSizer, 0, wx.ALL, 5)
        self.dlg_teclado.SetSizerAndFit(sizer)
        self.dlg_teclado.Centre()

    def ShowModal(self):
        return self.dlg_teclado.ShowModal()
