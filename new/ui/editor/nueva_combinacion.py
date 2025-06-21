import wx
from globals.mensajes import mensaje_teclas

class NuevaCombinacionDialog:
    def __init__(self, parent, combinaciones, indice=None, texto=None):
        if indice is None:
            indice = combinaciones.GetFocusedItem()
        if texto is None:
            texto = combinaciones.GetItem(indice, 1).GetText()
        self.dlg_editar_combinacion = wx.Dialog(parent, wx.ID_ANY, _("Editando la combinación de teclas para %s") % mensaje_teclas[indice])
        sizer = wx.BoxSizer(wx.VERTICAL)
        firstSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_check = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        groupbox = wx.StaticBox(self.dlg_editar_combinacion, wx.ID_ANY, _("Selecciona las teclas que quieres usar"))
        sizer_groupbox = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
        self.check_ctrl = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Control"))
        if 'control' in texto: self.check_ctrl.SetValue(True)
        self.check_alt = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Alt"))
        if 'alt' in texto: self.check_alt.SetValue(True)
        self.check_shift = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Shift"))
        if 'shift' in texto: self.check_shift.SetValue(True)
        self.check_win = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Windows"))
        if 'win' in texto: self.check_win.SetValue(True)
        self.teclas = ["return", "tab", "space", "back", "delete", "home", "end", "pageup", "pagedown", "up", "down", "left", "right", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        label_tecla = wx.StaticText(self.dlg_editar_combinacion, wx.ID_ANY, _("&Selecciona una tecla para la combinación"))
        self.combo_tecla = wx.ComboBox(self.dlg_editar_combinacion, wx.ID_ANY, choices=self.teclas, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        texto_split = texto.split('+')
        self.combo_tecla.SetValue(texto_split[-1])
        self.editar = wx.Button(self.dlg_editar_combinacion, -1, _(u"&Aplicar nueva combinación de teclado"))
        self.editar.SetDefault()
        close = wx.Button(self.dlg_editar_combinacion, wx.ID_CANCEL, _(u"&Cerrar"))
        sizer_check.Add(self.check_ctrl, 0, wx.ALL, 5)
        sizer_check.Add(self.check_alt, 0, wx.ALL, 5)
        sizer_check.Add(self.check_shift, 0, wx.ALL, 5)
        sizer_check.Add(self.check_win, 0, wx.ALL, 5)
        sizer_groupbox.Add(sizer_check, 0, wx.ALL, 5)
        sizer.Add(sizer_groupbox, 0, wx.ALL, 5)
        firstSizer.Add(label_tecla, 0, wx.ALL, 5)
        firstSizer.Add(self.combo_tecla, 0, wx.ALL, 5)
        sizer_buttons.Add(self.editar, 0, wx.ALL, 5)
        sizer_buttons.Add(close, 0, wx.ALL, 5)
        sizer.Add(firstSizer, 0, wx.ALL, 5)
        sizer.Add(sizer_buttons, 0, wx.ALL, 5)
        self.dlg_editar_combinacion.SetSizerAndFit(sizer)
        self.dlg_editar_combinacion.Centre()

    def ShowModal(self):
        return self.dlg_editar_combinacion.ShowModal()
