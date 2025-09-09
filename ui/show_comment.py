import wx
from utils.translator import TranslatorWrapper
from utils import languageHandler
class ShowCommentDialog(wx.Dialog):
    def __init__(self, parent, text):
        super().__init__(parent, title=_('Mensaje'), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_message = wx.TextCtrl(self, wx.ID_ANY, text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_PROCESS_ENTER)
        self.text_message.Bind(wx.EVT_TEXT_ENTER, lambda event: self.Destroy())
        main_sizer.Add(self.text_message, 1, wx.EXPAND | wx.ALL, 5)
        translation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tw = TranslatorWrapper()
        self.traducir = wx.Button(self, wx.ID_ANY, label=_('&Traducir'))
        self.traducir.Bind(wx.EVT_BUTTON, self.traducirMensaje)
        translation_sizer.Add(self.traducir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.choice_idiomas = wx.Choice(self, wx.ID_ANY, choices=[self.tw.LANGUAGES[k] for k in self.tw.LANGUAGES])
        current_lang_code = languageHandler.curLang[:2]
        if current_lang_code in self.tw.LANGUAGES: self.choice_idiomas.SetStringSelection(self.tw.LANGUAGES[current_lang_code])
        self.choice_idiomas.Bind(wx.EVT_CHOICE, self.cambiarTraducir)
        self.label_mensaje_texto = wx.StaticText(self, wx.ID_ANY, label=_("mensaje: "))
        translation_sizer.Add(self.choice_idiomas, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(translation_sizer, 0, wx.EXPAND | wx.ALL, 0)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()
        cancelar = wx.Button(self, wx.ID_CANCEL, '&Cerrar')
        button_sizer.Add(cancelar, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(main_sizer)
        self.SetSize((500, 350))
        self.Centre()
    def ShowModal(self):
        self.Raise()
        self.text_message.SetFocus()
        return super(ShowCommentDialog, self).ShowModal()

    def cambiarTraducir(self,event): self.traducir.SetLabel(_("&Traducir mensaje") if self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()) != self.tw.LANGUAGES[languageHandler.curLang[:2]] else _("&Traducir al idioma del programa"))
    def traducirMensaje(self,event):
        for k in self.tw.LANGUAGES:
            if self.tw.LANGUAGES[k] == self.choice_idiomas.GetStringSelection():
                self.text_message.SetValue(self.tw.translate(self.text_message.GetValue(),target=k))
                break
        self.label_mensaje_texto.SetLabel(_("mensaje en ") +self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()))
        self.text_message.SetFocus()