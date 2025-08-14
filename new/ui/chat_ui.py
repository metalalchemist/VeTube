import wx
from utils.menu_accesible import Accesible

class ChatDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, _(u"Chat en vivo"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_dialog = wx.StaticText(self, wx.ID_ANY, _(u"Lectura del chat en vivo..."))
        top_sizer.Add(self.label_dialog, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.button_mensaje_detener = wx.Button(self, wx.ID_ANY, _(u"&Detener chat"))
        top_sizer.Add(self.button_mensaje_detener, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        main_sizer.Add(top_sizer, 0, wx.EXPAND)

        self.treebook = wx.Treebook(self, wx.ID_ANY)
        
        # Create and add pages
        self.list_box_general, self.page_index_general = self.create_page_with_listbox(self.treebook, _(u"General"))
        self.list_box_eventos, self.page_index_eventos = self.create_page_with_listbox(self.treebook, _(u"Eventos"))
        self.list_box_miembros, self.page_index_miembros = self.create_page_with_listbox(self.treebook, _(u"Miembros"))
        self.list_box_moderadores, self.page_index_moderadores = self.create_page_with_listbox(self.treebook, _(u"Moderadores"))
        self.list_box_donaciones, self.page_index_donaciones = self.create_page_with_listbox(self.treebook, _(u"Donaciones"))
        self.list_box_verificados, self.page_index_verificados = self.create_page_with_listbox(self.treebook, _(u"Verificados"))

        self.treebook.SetFocus()
        main_sizer.Add(self.treebook, 1, wx.EXPAND | wx.ALL, 5)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.AddStretchSpacer()
        self.boton_opciones = wx.Button(self, wx.ID_ANY, _(u"&Opciones"))
        self.boton_opciones.SetAccessible(Accesible(self.boton_opciones))
        bottom_sizer.Add(self.boton_opciones, 0, wx.ALL, 5)
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.SetSize((400, 500))
        self.Centre()
        self.SetEscapeId(self.button_mensaje_detener.GetId())

    def create_page_with_listbox(self, parent, name):
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        list_box = wx.ListBox(page, wx.ID_ANY)
        sizer.Add(list_box, 1, wx.EXPAND | wx.ALL, 5)
        page.SetSizer(sizer)
        page_index = parent.AddPage(page, str(name))
        return list_box, page_index

    def ShowModal(self):
        return super().ShowModal()
