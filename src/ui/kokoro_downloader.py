import wx


class KokoroDownloaderDialog(wx.Dialog):
    """Instalador del modelo Kokoro: un único paquete con todas las voces.
    La barra es un wx.Gauge nativo para que los lectores de pantalla anuncien
    el avance por sí mismos (los pitidos de progreso de NVDA)."""

    def __init__(self, parent, tamano_mb):
        super().__init__(
            parent, title=_("Instalar las voces Kokoro"), style=wx.DEFAULT_DIALOG_STYLE
        )

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.intro = wx.StaticText(
            self,
            label=_(
                "Las voces Kokoro se instalan con un único paquete para todos los idiomas. "
                "Se descarga una sola vez y ocupa %d MB aproximadamente."
            )
            % tamano_mb,
        )
        self.intro.Wrap(520)
        main_sizer.Add(self.intro, 0, wx.ALL, 10)

        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        main_sizer.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.status_text = wx.StaticText(self, label="")
        main_sizer.Add(self.status_text, 0, wx.ALL, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_descargar = wx.Button(self, label=_("&Descargar e instalar"))
        btn_sizer.Add(self.btn_descargar, 0, wx.RIGHT, 5)
        self.btn_cerrar = wx.Button(self, wx.ID_CANCEL, label=_("&Cerrar"))
        btn_sizer.Add(self.btn_cerrar, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.btn_descargar.SetDefault()
        self.btn_descargar.SetFocus()

        self.SetSizerAndFit(main_sizer)
        self.Centre()

    def update_progress(self, value):
        self.gauge.SetValue(value)

    def set_status(self, text):
        self.status_text.SetLabel(text)
        self.Layout()
