import wx
from utils.menu_accesible import Accesible
from globals import data_store

class ChatPanel(wx.Panel):
    def __init__(self, parent, plataforma):
        super().__init__(parent, wx.ID_ANY)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_dialog = wx.StaticText(self, wx.ID_ANY, _(u"Lectura del chat en vivo..."))
        top_sizer.Add(self.label_dialog, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.button_mensaje_detener = wx.Button(self, wx.ID_ANY, _(u"&Cerrar chat"))
        top_sizer.Add(self.button_mensaje_detener, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        main_sizer.Add(top_sizer, 0, wx.EXPAND)

        self.treebook = wx.Treebook(self, wx.ID_ANY)
        
        # Create and add pages
        if plataforma == 'La sala de juegos':
            if data_store.config['categorias'][0]: self.list_box_general, self.page_index_general = self.create_page_with_listbox(self.treebook, _(u"conversaciones"))
            if data_store.config['categorias'][2]: self.list_box_miembros, self.page_index_miembros = self.create_page_with_listbox(self.treebook, _(u"mensajes privados"))
        elif plataforma == 'TikTok':
            if data_store.config['categorias'][0]: self.list_box_general, self.page_index_general = self.create_page_with_listbox(self.treebook, _(u"General"))
            if data_store.config['categorias'][1]: self.list_box_eventos, self.page_index_eventos = self.create_page_with_listbox(self.treebook, _(u"Eventos"), plataforma)
            if data_store.config['categorias'][2]: self.list_box_miembros, self.page_index_miembros = self.create_page_with_listbox(self.treebook, _(u"Miembros"))
            if data_store.config['categorias'][3]: self.list_box_donaciones, self.page_index_donaciones = self.create_page_with_listbox(self.treebook, _(u"regalos"))
        else:
            if data_store.config['categorias'][0]: self.list_box_general, self.page_index_general = self.create_page_with_listbox(self.treebook, _(u"General"))
            if data_store.config['categorias'][1]: self.list_box_eventos, self.page_index_eventos = self.create_page_with_listbox(self.treebook, _(u"Eventos"))
            if data_store.config['categorias'][2]: self.list_box_miembros, self.page_index_miembros = self.create_page_with_listbox(self.treebook, _(u"Miembros"))
            if data_store.config['categorias'][4]: self.list_box_moderadores, self.page_index_moderadores = self.create_page_with_listbox(self.treebook, _(u"Moderadores"))
            if data_store.config['categorias'][3]: self.list_box_donaciones, self.page_index_donaciones = self.create_page_with_listbox(self.treebook, _(u"Donaciones"))
            if data_store.config['categorias'][5]: self.list_box_verificados, self.page_index_verificados = self.create_page_with_listbox(self.treebook, _(u"Verificados"))
        if data_store.config['categorias'][5]: self.list_box_favoritos, self.page_index_favoritos = self.create_page_with_listbox(self.treebook, _(u"Favoritos"))

        self.treebook.SetFocus()
        main_sizer.Add(self.treebook, 1, wx.EXPAND | wx.ALL, 5)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.AddStretchSpacer()
        self.boton_eliminar = wx.Button(self, wx.ID_ANY, _(u"&Eliminar"))
        bottom_sizer.Add(self.boton_eliminar, 0, wx.ALL, 5)
        self.boton_opciones = wx.Button(self, wx.ID_ANY, _(u"&Opciones"))
        self.boton_opciones.SetAccessible(Accesible(self.boton_opciones))
        bottom_sizer.Add(self.boton_opciones, 0, wx.ALL, 5)
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND)
        self.SetSizer(main_sizer)

    def create_page_with_listbox(self, parent, name, plataforma=None):
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        list_box = wx.ListBox(page, wx.ID_ANY)
        sizer.Add(list_box, 1, wx.EXPAND | wx.ALL, 5)
        if plataforma == 'TikTok' and name == _(u"Eventos"):
            self.boton_filtrar = wx.Button(page, wx.ID_ANY, _(u"&Filtrar por"))
            self.boton_filtrar.SetAccessible(Accesible(self.boton_filtrar))
            sizer.Add(self.boton_filtrar, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        page.SetSizer(sizer)
        page_index = parent.AddPage(page, str(name))
        return list_box, page_index