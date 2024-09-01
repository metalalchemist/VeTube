import vetube,wx
class MyApp(wx.App):
	def OnInit(self):
		self.frame = vetube.MyFrame(None, wx.ID_ANY, "")
		self.SetTopWindow(self.frame)
		self.frame.Show()
		return True
app = MyApp(0)
app.MainLoop()