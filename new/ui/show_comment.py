import wx
from utils.translator import TranslatorWrapper
from utils import languageHandler
class ShowCommentDialog(wx.Dialog):
    def __init__(self, parent, text):
        super().__init__(parent, title=_('Mensaje'), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_message = wx.TextCtrl(self, wx.ID_ANY, text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text_message.SetFocus()
        main_sizer.Add(self.text_message, 1, wx.EXPAND | wx.ALL, 5)
        translation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tw = TranslatorWrapper()
        self.traducir = wx.Button(self, wx.ID_ANY, label=_('&Traducir'))
        translation_sizer.Add(self.traducir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.choice_idiomas = wx.Choice(self, wx.ID_ANY, choices=[tw.LANGUAGES[k] for k in tw.LANGUAGES])
        current_lang_code = languageHandler.curLang[:2]
        if current_lang_code in tw.LANGUAGES:
            self.choice_idiomas.SetStringSelection(tw.LANGUAGES[current_lang_code])
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
