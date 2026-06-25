# -*- coding: utf-8 -*-
import wx

class PiperDownloaderDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Gestor de voces Piper"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self)
        
        # --- PESTAÑA 1: VOCES INSTALADAS ---
        self.panel_instaladas = wx.Panel(self.notebook)
        instaladas_sizer = wx.BoxSizer(wx.VERTICAL)
        
        inst_label = wx.StaticText(self.panel_instaladas, label=_("Voces que ya tienes en tu equipo:"))
        instaladas_sizer.Add(inst_label, 0, wx.ALL, 10)
        
        self.list_instaladas = wx.ListBox(self.panel_instaladas, style=wx.LB_SINGLE)
        instaladas_sizer.Add(self.list_instaladas, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        inst_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_probar_local = wx.Button(self.panel_instaladas, label=_("&Probar voz"))
        inst_btn_sizer.Add(self.btn_probar_local, 0, wx.RIGHT, 5)
        self.btn_eliminar = wx.Button(self.panel_instaladas, label=_("&Eliminar voz"))
        inst_btn_sizer.Add(self.btn_eliminar, 0)
        instaladas_sizer.Add(inst_btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.panel_instaladas.SetSizer(instaladas_sizer)
        self.notebook.AddPage(self.panel_instaladas, _("Voces instaladas"))

        # --- PESTAÑA 2: DESCARGAR VOCES ---
        self.panel_descargar = wx.Panel(self.notebook)
        descargar_sizer = wx.BoxSizer(wx.VERTICAL)

        lang_label = wx.StaticText(self.panel_descargar, label=_("Selecciona los idiomas para filtrar las voces:"))
        descargar_sizer.Add(lang_label, 0, wx.ALL, 10)
        
        self.lang_list = wx.ListCtrl(self.panel_descargar, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        self.lang_list.InsertColumn(0, _("Idioma"), width=400)
        self.lang_list.EnableCheckBoxes()
        descargar_sizer.Add(self.lang_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        voice_label = wx.StaticText(self.panel_descargar, label=_("Selecciona la voz que deseas descargar:"))
        descargar_sizer.Add(voice_label, 0, wx.ALL, 10)

        self.voice_list = wx.ListCtrl(self.panel_descargar, style=wx.LC_REPORT)
        self.voice_list.InsertColumn(0, _("Voz"), width=200)
        self.voice_list.InsertColumn(1, _("Calidad"), width=100)
        self.voice_list.InsertColumn(2, _("Idioma"), width=80)
        self.voice_list.EnableCheckBoxes()
        descargar_sizer.Add(self.voice_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        self.panel_descargar.SetSizer(descargar_sizer)
        self.notebook.AddPage(self.panel_descargar, _("Descargar voces"))

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        # Feedback de progreso y botones comunes
        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        main_sizer.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.status_text = wx.StaticText(self, label=_("Cargando..."))
        main_sizer.Add(self.status_text, 0, wx.ALL, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_reproducir = wx.Button(self, label=_("&Reproducir muestra"))
        btn_sizer.Add(self.btn_reproducir, 0, wx.RIGHT, 5)
        self.btn_descargar = wx.Button(self, label=_("&Descargar e instalar"))
        btn_sizer.Add(self.btn_descargar, 0, wx.RIGHT, 5)
        self.btn_cerrar = wx.Button(self, wx.ID_CANCEL, label=_("&Cerrar"))
        btn_sizer.Add(self.btn_cerrar, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(main_sizer)
        self.SetSize((650, 600))
        self.Centre()

    def update_progress(self, value):
        self.gauge.SetValue(value)

    def set_status(self, text):
        self.status_text.SetLabel(text)
