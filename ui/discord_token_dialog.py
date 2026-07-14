import wx
from utils import languageHandler

# Idiomas con guía disponible en doc/<idioma>/discord.md
IDIOMAS_GUIA = ('cs', 'en', 'es', 'fr', 'id', 'pl', 'pt')

def url_guia_discord():
    lang = languageHandler.curLang[:2]
    if lang not in IDIOMAS_GUIA:
        lang = 'en'
    return f'https://github.com/metalalchemist/VeTube/blob/master/doc/{lang}/discord.md'

class DiscordTokenDialog(wx.Dialog):
    """Pequeño diálogo que pide el token del bot cuando no hay uno guardado."""
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, title=_("Se necesita el token del bot de Discord"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(self, wx.ID_ANY, _("Para leer un canal de Discord, VeTube necesita el token de tu bot. Pégalo aquí; quedará guardado y no se te volverá a pedir."))
        intro.Wrap(420)
        sizer.Add(intro, 0, wx.ALL, 10)
        label = wx.StaticText(self, wx.ID_ANY, _("&Token del bot:"))
        sizer.Add(label, 0, wx.LEFT | wx.RIGHT, 10)
        self.token_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_PASSWORD)
        sizer.Add(self.token_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.boton_guia = wx.Button(self, wx.ID_ANY, _("¿No sabes cómo crear el token? Abrir la &guía"))
        self.boton_guia.Bind(wx.EVT_BUTTON, self.abrir_guia)
        sizer.Add(self.boton_guia, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        botones = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(botones, 0, wx.EXPAND | wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.on_aceptar, id=wx.ID_OK)
        self.SetSizerAndFit(sizer)
        self.Centre()
        self.token_ctrl.SetFocus()

    def abrir_guia(self, event):
        wx.LaunchDefaultBrowser(url_guia_discord())

    def on_aceptar(self, event):
        if not self.get_token():
            wx.MessageBox(_("Debes pegar el token del bot para continuar."), _("Error"), wx.ICON_ERROR)
            self.token_ctrl.SetFocus()
            return
        event.Skip()

    def get_token(self):
        return self.token_ctrl.GetValue().strip()
