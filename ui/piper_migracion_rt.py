# -*- coding: utf-8 -*-
import wx

class PiperMigracionRTDialog(wx.Dialog):
    """Reinstalación de las antiguas voces rápidas (RT) en variante estándar.
    La barra es un wx.Gauge nativo para que los lectores de pantalla anuncien
    el avance por sí mismos (los pitidos de progreso de NVDA)."""

    def __init__(self, parent):
        super().__init__(parent, title=_("Actualizar las voces de Piper"), style=wx.DEFAULT_DIALOG_STYLE)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.intro = wx.StaticText(self, label=_(
            "Descargando la versión estándar de tus voces rápidas (RT). "
            "Cada voz quedará instalada en su mismo lugar y conservará su configuración."
        ))
        self.intro.Wrap(520)
        main_sizer.Add(self.intro, 0, wx.ALL, 10)

        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        main_sizer.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.status_text = wx.StaticText(self, label="")
        main_sizer.Add(self.status_text, 0, wx.ALL, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_cancelar = wx.Button(self, wx.ID_CANCEL, label=_("&Cancelar"))
        btn_sizer.Add(self.btn_cancelar, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.btn_cancelar.SetDefault()
        self.btn_cancelar.SetFocus()

        self.SetSizerAndFit(main_sizer)
        self.Centre()

    def update_progress(self, value):
        self.gauge.SetValue(value)

    def set_status(self, text):
        self.status_text.SetLabel(text)
        self.Layout()
