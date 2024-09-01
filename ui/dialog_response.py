import wx
def response(message,title,flags=wx.YES_NO | wx.ICON_ASTERISK): return wx.MessageDialog(None,message,title,flags).ShowModal()