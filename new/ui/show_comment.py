import wx
from utils.translator import TranslatorWrapper
from utils import languageHandler
class ShowCommentDialog(wx.Dialog):
    def __init__(self, parent, text):
        super().__init__(parent, title=_('Mensaje'))
        sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
        label_idioma = wx.StaticText(self, wx.ID_ANY, _('Idioma a traducir'))
        tw = TranslatorWrapper()  # Instancia única
        self.choice_idiomas = wx.Choice(self, wx.ID_ANY, choices=[tw.LANGUAGES[k] for k in tw.LANGUAGES])
        self.choice_idiomas.SetStringSelection(tw.LANGUAGES[languageHandler.curLang[:2]])
        self.label_mensaje_texto = wx.StaticText(self, wx.ID_ANY, label=_('mensaje: '))
        self.text_message = wx.TextCtrl(self, wx.ID_ANY, text, style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        self.text_message.SetFocus()
        self.text_message.Bind(wx.EVT_TEXT_ENTER, lambda event: self.Destroy())
        self.traducir = wx.Button(self, wx.ID_ANY, label=_('&Traducir al idioma del programa'))
        cancelar = wx.Button(self, wx.ID_CANCEL, '&Cerrar')
        sizer_mensaje.Add(self.text_message, 0, 0, 0)
        sizer_mensaje.Add(self.traducir, 0, 0, 0)
        sizer_mensaje.Add(cancelar, 0, 0, 0)
        self.SetSizerAndFit(sizer_mensaje)
        self.Centre()
