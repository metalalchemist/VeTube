import wx
from utils import languageHandler
from utils.translator import TranslatorWrapper
class showComment(wx.Dialog):
	def __init__(self, parent,text):
		self.translator=TranslatorWrapper()
		super().__init__(parent, title=_("Mensaje"))
		sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
		label_idioma = wx.StaticText(self, wx.ID_ANY, _("Idioma a traducir"))
		self.choice_idiomas = wx.Choice(self, wx.ID_ANY, choices=[self.translator.LANGUAGES[k] for k in self.translator.LANGUAGES])
		self.choice_idiomas.SetStringSelection(self.translator.LANGUAGES[languageHandler.curLang[:2]])
		self.choice_idiomas.Bind(wx.EVT_CHOICE, self.cambiarTraducir)
		self.label_mensaje_texto = wx.StaticText(self, wx.ID_ANY, label=_("mensaje: "))
		self.text_message = wx.TextCtrl(self, wx.ID_ANY, text, style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
		self.text_message.SetFocus()
		self.text_message.Bind(wx.EVT_TEXT_ENTER, lambda event: self.Destroy())
		self.traducir = wx.Button(self, wx.ID_ANY, label=_("&Traducir al idioma del programa"))
		self.traducir.Bind(wx.EVT_BUTTON, self.traducirMensaje)
		cancelar = wx.Button(self, wx.ID_CANCEL, "&Cerrar")
		sizer_mensaje.Add(self.text_message, 0, 0, 0)
		sizer_mensaje.Add(self.traducir,0,0,0)
		sizer_mensaje.Add(cancelar,0,0,0)
		self.SetSizerAndFit(sizer_mensaje)
		self.Centre()
	def cambiarTraducir(self,event): self.traducir.SetLabel(_("&Traducir mensaje") if self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()) != self.translator.LANGUAGES[languageHandler.curLang[:2]] else _("&Traducir al idioma del programa"))
	def traducirMensaje(self,event):
		for k in self.translator.LANGUAGES:
			if self.translator.LANGUAGES[k] == self.choice_idiomas.GetStringSelection():
				self.text_message.SetValue(self.translator.translate(self.text_message.GetValue(),target=k))
				break
		self.label_mensaje_texto.SetLabel(_("mensaje en ") +self.choice_idiomas.GetString(self.choice_idiomas.GetSelection()))
		self.text_message.SetFocus()